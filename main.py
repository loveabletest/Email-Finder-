# main.py
import csv, re, tempfile, os
from typing import Optional
import pandas as pd
from fastapi import FastAPI, UploadFile, File, Form
from fastapi.responses import FileResponse, JSONResponse

# Optional package detection
try:
    from email_validator import validate_email
    EMAIL_VALIDATOR_AVAILABLE = True
except:
    EMAIL_VALIDATOR_AVAILABLE = False

# ----------------- Helpers -----------------
def simple_syntax_check(email: str) -> bool:
    pattern = r"^[^@\s]+@[^@\s]+\.[^@\s]+$"
    return re.match(pattern, email) is not None

def verify_email_status(email: str) -> str:
    """Quick verification: only syntax check for Railway-friendly deployment"""
    if EMAIL_VALIDATOR_AVAILABLE:
        try:
            validate_email(email)
            return "syntax_ok"
        except:
            return "invalid_syntax"
    else:
        return "syntax_ok" if simple_syntax_check(email) else "invalid_syntax"

def clean_domain(domain: str) -> str:
    d = (domain or "").lower().strip()
    d = re.sub(r'^https?://', '', d)
    d = re.sub(r'^www\.', '', d)
    return d.strip().rstrip('/')

def generate_candidate_emails(first: str, last: str, domain: str):
    f = (first or "").lower().strip()
    l = (last or "").lower().strip()
    f0 = f[:1] if f else ''
    l0 = l[:1] if l else ''
    domain = clean_domain(domain)
    patterns = [
        f"{f0}{l}@{domain}", f"{f}.{l}@{domain}", f"{f}@{domain}", f"{f}_{l}@{domain}",
        f"{f}{l}@{domain}", f"{l}@{domain}", f"{l}{f0}@{domain}", f"{f0}.{l}@{domain}",
        f"{f}{l0}@{domain}", f"{f0}{l0}@{domain}"
    ]
    seen = set()
    out = []
    for p in patterns:
        if p and p not in seen and "@" in p and not p.startswith("@"):
            seen.add(p)
            out.append(p)
    return out

# ----------------- Processing -----------------
def process_dataframe(df: pd.DataFrame, only_verified: bool, max_candidates_per_row: int):
    rows_out = []
    headers = list(df.columns)
    lower_headers = [str(h) for h in headers]
    expected = {'first', 'last', 'company_website'}
    if not expected.issubset(set(lower_headers)):
        raise ValueError("Input CSV must contain headers: first,last,company_website")
    total = len(df)

    for i, r in enumerate(df.itertuples(index=False), start=1):
        row = {str(h): getattr(r, h) if hasattr(r, h) else r[idx] for idx, h in enumerate(headers)}
        first = str(row.get('first', '') or '').strip()
        last = str(row.get('last', '') or '').strip()
        domain = str(row.get('company_website', '') or '').strip()

        verified_email = ''
        verification_status = ''

        if domain:
            candidates = generate_candidate_emails(first, last, domain)[:max_candidates_per_row]
            for c in candidates:
                status = verify_email_status(c)
                if status == 'syntax_ok':
                    verified_email = c
                    verification_status = status
                    break
                if status == 'invalid_syntax' and not verification_status:
                    verification_status = status

        out_row = {str(h): getattr(r, h) if hasattr(r, h) else r[idx] for idx, h in enumerate(headers)}
        out_row['verified_email'] = verified_email
        out_row['verification_status'] = verification_status or ('no_domain' if not domain else 'none_found')

        if only_verified:
            if verified_email:
                rows_out.append(out_row)
        else:
            rows_out.append(out_row)

    out_df = pd.DataFrame(rows_out)
    return out_df

# ----------------- FastAPI -----------------
app = FastAPI(title="Bulk Email Verifier API")

# Health check route for Railway
@app.get("/")
def health():
    return {"status": "ok", "message": "FastAPI Email Verifier is running!"}

@app.post("/verify-emails/")
async def verify_emails(
    file: UploadFile = File(...),
    only_verified: bool = Form(False),
    max_candidates_per_row: int = Form(10),
):
    if not file.filename.endswith(".csv"):
        return JSONResponse({"error": "Please upload a CSV file."}, status_code=400)

    try:
        df = pd.read_csv(file.file)
    except Exception as e:
        return JSONResponse({"error": f"Failed to read CSV: {e}"}, status_code=400)

    try:
        out_df = process_dataframe(df, only_verified=only_verified, max_candidates_per_row=max_candidates_per_row)
    except Exception as e:
        return JSONResponse({"error": f"Processing error: {e}"}, status_code=500)

    tmp_dir = tempfile.mkdtemp()
    out_csv_path = os.path.join(tmp_dir, "output_verified.csv")
    out_df.to_csv(out_csv_path, index=False)

    return FileResponse(out_csv_path, filename="output_verified.csv")

# ----------------- Run App (Railway compatible) -----------------
if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=False)
