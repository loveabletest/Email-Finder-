import os
import csv
import re
import time
import random
import smtplib
import tempfile
from typing import Optional
import pandas as pd
from fastapi import FastAPI, UploadFile, File, Form
from fastapi.responses import FileResponse, JSONResponse

# Import your existing functions (clean_domain, has_mx, smtp_verify, etc.)
# If needed, put them in a separate utils.py and import them here

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

    # Process dataframe using your existing function
    from your_utils import process_dataframe  # move your existing logic to utils

    out_df, logs = process_dataframe(
        df,
        only_verified=only_verified,
        sleep_min=sleep_min,
        sleep_max=sleep_max,
        max_candidates_per_row=max_candidates_per_row,
    )

    tmp_dir = tempfile.mkdtemp()
    out_csv_path = os.path.join(tmp_dir, "output_verified.csv")
    out_df.to_csv(out_csv_path, index=False)

    return FileResponse(out_csv_path, filename="output_verified.csv")
