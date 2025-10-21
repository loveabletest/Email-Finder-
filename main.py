import os
import uuid
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv


load_dotenv()


app = FastAPI(title="Email Verifier Backend")


# CORS - allow from env or default to * (for quick deploy). In production, lock this down.
origins = os.getenv("CORS_ORIGINS", "*")
if origins == "*":
allow_origins = ["*"]
else:
allow_origins = [o.strip() for o in origins.split(",")]


app.add_middleware(
CORSMiddleware,
allow_origins=allow_origins,
allow_credentials=True,
allow_methods=["*"],
allow_headers=["*"],
)


# simple in-memory store for runs (for logs/downloads). For prod use a persistent store like S3/DB.
app.state.runs = {}


# include routes
from app.routes import verifier # noqa: E402, F401
app.include_router(verifier.router)




@app.get("/health")
async def health():
"""Basic health check."""
return {"status": "ok", "run_id": str(uuid.uuid4())}
