"""FastAPI application entrypoint.

Serves the JSON API under /api/* and the built React frontend from /dist at
the root.  The scheduler starts on startup and shuts down on exit.
"""

from __future__ import annotations

import logging
import os
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware

from . import scheduler, crud
from .config import env
from .database import init_db, get_db
from .routers import patient, admin, auth_router, settings, backup_router, export

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DIST_DIR = PROJECT_ROOT / "dist"


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Application starting")
    init_db()
    with get_db() as db:
        crud.log_event(db, "startup", "Application started")
    scheduler.start_scheduler()
    yield
    scheduler.shutdown_scheduler()
    logger.info("Application stopped")


app = FastAPI(title="Medication Reminder", lifespan=lifespan)


@app.middleware("http")
async def security_headers(request, call_next):
    response = await call_next(request)
    response.headers.setdefault("X-Content-Type-Options", "nosniff")
    response.headers.setdefault("X-Frame-Options", "DENY")
    response.headers.setdefault("Referrer-Policy", "no-referrer")
    response.headers.setdefault("Permissions-Policy", "camera=(), microphone=(), geolocation=()")
    if request.url.path.startswith("/api/"):
        response.headers["Cache-Control"] = "no-store"
    return response

app.add_middleware(
    CORSMiddleware,
    allow_origins=[env.website_url.rstrip("/")],
    allow_methods=["GET", "POST", "PUT", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type", "X-Patient-Token"],
)

# API routers
app.include_router(patient.router)
app.include_router(auth_router.router)
app.include_router(admin.router)
app.include_router(settings.router)
app.include_router(backup_router.router)
app.include_router(export.router)


@app.get("/api/health")
def health():
    return {"status": "ok"}


# Serve frontend
if DIST_DIR.exists():
    app.mount("/assets", StaticFiles(directory=DIST_DIR / "assets"), name="assets")
    DIST_ROOT = DIST_DIR.resolve()

    @app.get("/{full_path:path}")
    def serve_spa(full_path: str):
        file_path = (DIST_ROOT / full_path).resolve()
        if file_path.is_relative_to(DIST_ROOT) and file_path.is_file():
            return FileResponse(file_path)
        index = DIST_DIR / "index.html"
        if index.exists():
            return FileResponse(index)
        return FileResponse(DIST_DIR / "index.html")
else:
    @app.get("/")
    def no_frontend():
        return {
            "message": "Frontend not built yet. Run `npm run build` in the project root.",
            "api_docs": "/docs",
        }
