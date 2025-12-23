"""
Results & Governance Service - Main FastAPI application.
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from app.config import settings
from app.routers import internal
from app.persistence.database import init_db
from app.utils.logger import setup_logging, get_logger

# Setup logging
setup_logging(settings.log_level, settings.log_format)
logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events."""
    # Startup
    logger.info("Starting Results & Governance Service...")
    
    # Initialize database
    try:
        init_db()
        logger.info("Database initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize database: {e}")
        raise
    
    logger.info(f"Database URL: {settings.database_url}")
    logger.info(f"Audit logging: {'enabled' if settings.enable_audit_log else 'disabled'}")
    logger.info(f"Retention days: {settings.retention_days}")
    logger.info("Results & Governance Service started successfully")
    
    yield
    
    # Shutdown
    logger.info("Shutting down Results & Governance Service...")
    logger.info("Results & Governance Service shut down")


# Create FastAPI app
app = FastAPI(
    title="Results & Governance Service",
    description="AWS Cost Results System of Record",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs" if settings.environment == "development" else None,
    redoc_url="/redoc" if settings.environment == "development" else None
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(internal.router)


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "service": "results-governance-service",
        "version": "1.0.0",
        "status": "running",
        "audit_enabled": settings.enable_audit_log
    }
