"""
FastAPI application entry point for the Journal Assistant.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pathlib import Path

from backend.api.chat import router as chat_router
from backend.api.whoop_oauth import router as whoop_router
from backend.api.whoop_data import router as whoop_data_router

app = FastAPI(
    title="JournaLLM",
    description="A privacy-focused AI journal assistant",
    version="1.0.0",
)

# Allow CORS for local development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routes
app.include_router(chat_router)
app.include_router(whoop_router)
app.include_router(whoop_data_router)

# Serve static frontend files
FRONTEND_DIR = Path(__file__).resolve().parent.parent / "frontend"

if FRONTEND_DIR.exists():
    app.mount("/static", StaticFiles(directory=FRONTEND_DIR), name="static")

    @app.get("/")
    async def serve_frontend():
        return FileResponse(FRONTEND_DIR / "index.html")


@app.get("/health")
async def health_check():
    return {"status": "healthy"}

