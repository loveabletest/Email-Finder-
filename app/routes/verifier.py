# app/routes/verifier.py
from fastapi import APIRouter, UploadFile, File, Form
from fastapi.responses import JSONResponse
from app.services.verify_logic import run_verification_service
import tempfile
import os
import base64

router = APIRouter(prefix="/verify", tags=["Email Verification"])

@router.post("/")
async def verify_csv(
    uploaded_file: UploadFile = File(...),
    only_verified: bool = Form(False),
    sleep_min: float = Form(0.4),
    sleep_max: float = Form(1.2),
    max_candidates: int = Form(10),
    preview_rows: int = Form(10)
):
    """
    Upload a CSV and run bulk email verification.
    Returns JSON results + downloadable base64 CSV.
    """
    try:
        # Save uploaded CSV temporarily
        tmp_dir = tempfile.mkdtemp()
        tmp_input_path = os.path.join(tmp_dir, uploaded_file.filename)
        with open(tmp_input_path, "wb") as f:
            f.write(await uploaded_file.read())

        # Run verification logic
        out_df, logs, out_csv_path = run_verification_service(
            tmp_input_path,
            only_verified,
            sleep_min,
            sleep_max,
            max_candidates,
            preview_rows
        )

        # Encode output CSV in base64 for API download
        with open(out_csv_path, "rb") as f:
            csv_base64 = base64.b64encode(f.read()).decode("utf-8")

        return JSONResponse({
            "status": "success",
            "rows_processed": len(out_df),
            "sample_preview": out_df.head(preview_rows).to_dict(orient="records"),
            "download_base64": csv_base64,
            "logs": logs[-10:]  # last few logs
        })

    except Exception as e:
        return JSONResponse({
            "status": "error",
            "message": str(e)
        }, status_code=500)
