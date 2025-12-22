"""
Terraform Execution Service - Main Application
FastAPI application for sandboxed Terraform execution (INTERNAL ONLY).
"""
from fastapi import FastAPI
from app.config import settings
from app.routers import internal
from app.utils.logger import setup_logging, get_logger

# Setup logging
setup_logging(settings.log_level, settings.log_format)
logger = get_logger(__name__)

# Create FastAPI application (INTERNAL ONLY)
app = FastAPI(
    title="Terraform Execution Service",
    description="Internal sandboxed Terraform executor for Cost Calculator",
    version="1.0.0",
    docs_url="/internal/docs",
    redoc_url="/internal/redoc",
    openapi_url="/internal/openapi.json"
)

# Include routers
app.include_router(internal.router)


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "service": "terraform-executor"}


@app.on_event("startup")
async def startup_event():
    """Application startup event."""
    logger.info("Terraform Executor starting up...")
    logger.info(f"Terraform version: {settings.terraform_version}")
    logger.info(f"Max execution time: {settings.max_execution_time}s")
    logger.info(f"Allowed providers: {settings.allowed_providers}")


@app.on_event("shutdown")
async def shutdown_event():
    """Application shutdown event."""
    logger.info("Terraform Executor shutting down...")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host=settings.host,
        port=settings.port,
        reload=True,
        log_level=settings.log_level.lower()
    )
