"""
Main FastAPI application for Terraform Plan Interpreter.
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routers import internal
from app.config import settings
from app.utils.logger import setup_logging, get_logger

# Setup logging
setup_logging(
    log_level=settings.log_level,
    log_format=settings.log_format
)

logger = get_logger(__name__)

# Create FastAPI app
app = FastAPI(
    title="Terraform Plan Interpreter",
    description="Parse Terraform plan JSON and produce Normalized Resource Graph",
    version="1.0.0",
    docs_url="/docs" if settings.environment == "development" else None,
    redoc_url="/redoc" if settings.environment == "development" else None
)

# Add CORS middleware (internal service, but useful for development)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(internal.router)


@app.on_event("startup")
async def startup_event():
    """Application startup."""
    logger.info(
        "Terraform Plan Interpreter starting",
        extra={
            'environment': settings.environment,
            'log_level': settings.log_level
        }
    )


@app.on_event("shutdown")
async def shutdown_event():
    """Application shutdown."""
    logger.info("Terraform Plan Interpreter shutting down")


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "service": "terraform-plan-interpreter",
        "version": "1.0.0",
        "status": "operational"
    }
