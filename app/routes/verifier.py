import io
df,
only_verified=only_verified,
sleep_min=sleep_min,
sleep_max=sleep_max,
max_candidates_per_row=max_candidates,
)


# save to temp file
run_id = str(uuid.uuid4())
tmp_dir = tempfile.mkdtemp(prefix=f"email_verifier_{run_id}_")
out_path = os.path.join(tmp_dir, "output_verified.csv")
out_df.to_csv(out_path, index=False)


# base64 encode
with open(out_path, 'rb') as f:
b64 = base64.b64encode(f.read()).decode('utf-8')


# store minimal run info in app state -- ephemeral
# NOTE: In production use external storage (S3, DB) and do not store large data in memory.
router_state = getattr(router, "state", None)
# store in FastAPI app state through a global import of current_app is possible; here we rely on uvicorn single-process default
# Instead we return run_id and file path; users may download via /download/{run_id}


# Return preview (first N rows) as list of dicts
preview_df = out_df.head(preview_rows)
preview = preview_df.fillna("").to_dict(orient="records")


return {
"run_id": run_id,
"preview": preview,
"rows_processed": len(out_df),
"verification_file_base64": b64,
"download_path": out_path,
}




@router.get("/download")
async def download_file(path: str):
"""Download a generated CSV by providing the path returned in /verify response.
This is a convenience endpoint for deployments where returning a base64 blob is not convenient.
In production you'd return a signed URL from S3 or similar instead of exposing local paths.
"""
if not os.path.exists(path):
raise HTTPException(status_code=404, detail="File not found")
return FileResponse(path, filename=os.path.basename(path), media_type='text/csv')




# Optional endpoint to fetch logs - in this implementation we return logs collected during processing if provided.
@router.post("/logs")
async def get_logs(dummy: Optional[bool] = Form(False)):
# Placeholder - process_dataframe returns logs but we currently return them in verify JSON if you wish.
return {"logs": "Logs are included in the verify response (if needed). For persistent logs add a DB or logging sink."}
