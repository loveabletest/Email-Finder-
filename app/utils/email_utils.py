# app/services/verify_logic.py
import pandas as pd
import tempfile
import os
import time
import random
from typing import Tuple, List
from app.utils.email_utils import (
    pip_install_hints,
    generate_candidate_emails,
    verify_email_status,
    clean_domain
)

def process_dataframe(
    df: pd.DataFrame,
    only_verified: bool,
    sleep_min: float,
    sleep_max: float,
    max_candidates_per_row: int,
    progress_callback=None
) -> Tuple[pd.DataFrame, List[str]]:
    logs = []
    rows_out = []
    headers = list(df.columns)
    lower_headers = [h.lower() for h in headers]
    expected = {'first', 'last', 'company_website'}
    if not expected.issubset(set(lower_headers)):
        raise ValueError("CSV must have headers: first,last,company_website")

    total = len(df)

    for i, r in enumerate(df.itertuples(index=False), start=1):
        row = {str(h).lower(): getattr(r, h) if hasattr(r, h) else r[idx] for idx, h in enumerate(headers)}
        first = str(row.get('first', '')).strip()
        last = str(row.get('last', '')).strip()
        domain = str(row.get('company_website', '')).strip()

        verified_email = ''
        verification_status = ''

        if domain:
            candidates = generate_candidate_emails(first, last, domain)[:max_candidates_per_row]
            for c in candidates:
                time.sleep(random.uniform(sleep_min, sleep_max))
                status = verify_email_status(c)
                logs.append(f"[{i}/{total}] {c} -> {status}")
                if progress_callback:
                    progress_callback(f"[{i}/{total}] {c} -> {status}")
                if status == 'deliverable':
                    verified_email = c
                    verification_status = status
                    break
                if status == 'catch_all' and not verification_status:
                    verification_status = status
                if status in ('undeliverable', 'inconclusive') and not verification_status:
                    verification_status = status

        out_row = dict(row)
        out_row['verified_email'] = verified_email
        out_row['verification_status'] = verification_status or ('no_domain' if not domain else 'none_found')

        if only_verified:
            if verified_email:
                rows_out.append(out_row)
        else:
            rows_out.append(out_row)

    out_df = pd.DataFrame(rows_out)
    return out_df, logs


def run_verification_service(
    uploaded_csv_path: str,
    only_verified: bool,
    sleep_min: float,
    sleep_max: float,
    max_candidates: int,
    preview_rows: int
) -> Tuple[pd.DataFrame, List[str], str]:
    """
    Core service: reads CSV, runs verification, outputs dataframe + logs + CSV path.
    """
    hints = pip_install_hints()
    logs = []
    try:
        df = pd.read_csv(uploaded_csv_path)
    except Exception as e:
        raise ValueError(f"Failed to read CSV: {e}")

    def progress_callback(msg):
        logs.append(msg)

    out_df, process_logs = process_dataframe(
        df, only_verified, sleep_min, sleep_max, max_candidates, progress_callback
    )
    logs.extend(process_logs)

    tmp_dir = tempfile.mkdtemp()
    out_csv_path = os.path.join(tmp_dir, "verified_output.csv")
    out_df.to_csv(out_csv_path, index=False)

    return out_df, logs, out_csv_path
