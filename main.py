# main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routes.verifier import router as verifier_router
import uvicorn

app = FastAPI(title="Email Verifier API", version="1.0")

# Enable CORS for frontend clients
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # adjust for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routers
app.include_router(verifier_router, prefix="/api")

@app.get("/health")
def health_check():
    """Health check endpoint."""
    return {"status": "ok", "message": "Server running"}

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
