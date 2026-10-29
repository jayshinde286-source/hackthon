"""FastAPI main application entry point for DBGuard."""

import os
from pathlib import Path
from fastapi import FastAPI, Request
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware

from backend.app.api import (
    routes_analysis,
    routes_benchmarks,
    routes_comparison,
    routes_demo,
    routes_health,
    routes_manifest,
    routes_reports,
)
from backend.app.database.connection import Base, engine
from backend.app.database.tables import DBAnalysis, DBIntegrityCheck, DBAnomaly, DBComparison, DBBenchmark

# Create database tables automatically
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="DBGuard API",
    description="Intelligent Integrity Assessment of Compressed Database Exports Without Full Database Restoration",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS configuration for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include Routers under /api
app.include_router(routes_health.router, prefix="/api")
app.include_router(routes_analysis.router, prefix="/api")
app.include_router(routes_reports.router, prefix="/api")
app.include_router(routes_comparison.router, prefix="/api")
app.include_router(routes_manifest.router, prefix="/api")
app.include_router(routes_benchmarks.router, prefix="/api")
app.include_router(routes_demo.router, prefix="/api")

# Serve built frontend if available
frontend_dist = Path(__file__).resolve().parent.parent.parent / "frontend" / "dist"
if frontend_dist.exists():
    app.mount("/assets", StaticFiles(directory=str(frontend_dist / "assets")), name="assets")

    @app.get("/{full_path:path}")
    async def serve_spa(request: Request, full_path: str):
        # Do not intercept /api or docs
        if full_path.startswith("api") or full_path.startswith("docs") or full_path.startswith("redoc") or full_path.startswith("openapi.json"):
            return None
        file_path = frontend_dist / full_path
        if file_path.exists() and file_path.is_file():
            return FileResponse(file_path)
        return FileResponse(frontend_dist / "index.html")
else:
    @app.get("/")
    def root():
        return {
            "app": "DBGuard API",
            "version": "1.0.0",
            "docs": "/docs",
            "status": "ONLINE"
        }
