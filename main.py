# main.py
import csv, re, time, random, smtplib, os, tempfile
from typing import Optional
import pandas as pd
from fastapi import FastAPI, UploadFile, File, Form
from fastapi.responses import FileResponse, JSONResponse

# Optional packages detection
try:
    import dns.resolver
    DNSPY_AVAILABLE = True
except:
    DNSPY_AVAILABLE = False

try:
    from email_validator import validate_email
    EMAIL_VALIDATOR_AVAILABLE = True
except:
    EMAIL_VALIDATOR_AVAILABLE = False

# ----------------- Helpers -----------------

def pip_install_hints():
    hints = []
    if not DNSPY_AVAILABLE:
        hints.append("pip install dnspython")
    if not EMAIL_VALIDATOR_AVAILABLE:
        hints.append("pip install email-validator")
    return hints

def clean_domain(domain: str) -> str:
    d = (domain or "").lower().strip()
    d = re.sub(r'^https?://', '', d)
    d = re.sub(r'^www\.', '', d)
    return d.strip().rstrip('/')

def has_mx(domain: str) -> bool:
    if not DNSPY_AVAILABLE:
        return False
    try:
        answers = dns.resolver.resolve(domain, 'MX')
        return len(answers) > 0
    except:
        return False

def smtp_verify(email: str, timeout: float = 10.0) -> Optional[bool]:
    if not DNSPY_AVAILABLE:
        return None
    try:
        domain = email.split('@')[1]
        answers = dns.resolver.resolve(domain, 'MX')
        mx_record = str(answers[0].exchange).rstrip('.')
        server = smtplib.SMTP(mx_record, timeout=timeout)
        server.set_debuglevel(0)
        server.helo("example.com")
        server.mail("test@example.com")
        code, _ = server.rcpt(email)
        try:
            server.quit()
        except:
            server.close()
        return code == 250
    except smtplib.SMTPRecipientsRefused:
        return False
    except:
        return None

def is_catch_all(domain: str) -> bool:
    if not DNSPY_AVAILABLE:
        return False
    try:
        rand = random.randint(10000, 99999)
        random_email = f"random{rand}@{domain}"
        return smtp_verify(random_email) is True
    except:
        return False

def simple_syntax_check(email: str) -> bool:
    pattern = r"^[^@\s]+@[^@\s]+\.[^@\s]+$"
    return re.match(pattern, email) is not None

def verify_email_status(email: str) -> str:
    if EMAIL_VALIDATOR_AVAILABLE:
        try:
            validate_email(email)
        except:
            return "invalid_syntax"
    else:
        if not simple_syntax_check(email):
            return "invalid_syntax"
    domain = email.split('@')[-1]
    if not has_mx(domain):
        return "no_mx" if DNSPY_AVAILABLE else "inconclusive"
    try:
        if is_catch_all(domain):
            return "catch_all"
    except:
        pass
    smtp_status = smtp_verify(email)
    if smtp_status is True:
        return "deliverable"
    elif smtp_status is False:
        return "undeliverable"
    else:
        return "inconclusive"

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

def _normalize_headers(fieldnames):
    return [str(h) for h in (fieldnames or [])]

def process_dataframe(df: pd.DataFrame, only_verified: bool, sleep_min: float, sleep_max: float,
                      max_candidates_per_row: int) -> (pd.DataFrame, list):
    logs = []
    rows_out = []
    headers = list(df.columns)
    lower_headers = _normalize_headers(headers)
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
                time.sleep(random.uniform(sleep_min, sleep_max))
                status = verify_email_status(c)
                logs.append(f"[{i}/{total}] {c} -> {status}")
                if status == 'deliverable':
                    verified_email = c
                    verification_status = status
                    break
                if status == 'catch_all' and not verification_status:
                    verification_status = status
                if status in ('undeliverable', 'inconclusive') and not verification_status:
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
    return out_df, logs

# ----------------- FastAPI -----------------

app = FastAPI(title="Bulk Email Verifier API")

@app.post("/verify-emails/")
async def verify_emails(
    file: UploadFile = File(...),
    only_verified: bool = Form(False),
    sleep_min: float = Form(0.4),
    sleep_max: float = Form(1.2),
    max_candidates_per_row: int = Form(10),
):
    if not file.filename.endswith(".csv"):
        return JSONResponse({"error": "Please upload a CSV file."}, status_code=400)

    try:
        df = pd.read_csv(file.file)
    except Exception as e:
        return JSONResponse({"error": f"Failed to read CSV: {e}"}, status_code=400)

    try:
        out_df, logs = process_dataframe(
            df,
            only_verified=only_verified,
            sleep_min=sleep_min,
            sleep_max=sleep_max,
            max_candidates_per_row=max_candidates_per_row,
        )
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
