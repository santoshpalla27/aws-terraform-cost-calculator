"""
Job Orchestrator - Main Application
FastAPI application for job state machine orchestration (INTERNAL ONLY).
"""
from fastapi import FastAPI
from contextlib import asynccontextmanager
from app.config import settings
from app.routers import internal
from app.database.connection import init_db, close_db
from app.services.lock_manager import lock_manager
from app.utils.logger import setup_logging, get_logger

# Setup logging
setup_logging(settings.log_level, settings.log_format)
logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events."""
    # Startup
    logger.info("Job Orchestrator starting up...")
    await init_db()
    await lock_manager.connect()
    logger.info("Job Orchestrator ready")
    
    yield
    
    # Shutdown
    logger.info("Job Orchestrator shutting down...")
    await lock_manager.disconnect()
    await close_db()
    logger.info("Job Orchestrator stopped")


# Create FastAPI application (INTERNAL ONLY)
app = FastAPI(
    title="Job Orchestrator",
    description="Internal job state machine orchestrator for Terraform Cost Calculator",
    version="1.0.0",
    docs_url="/internal/docs",
    redoc_url="/internal/redoc",
    openapi_url="/internal/openapi.json",
    lifespan=lifespan
)

# Include routers
app.include_router(internal.router)


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "service": "job-orchestrator"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host=settings.host,
        port=settings.port,
        reload=True,
        log_level=settings.log_level.lower()
    )
