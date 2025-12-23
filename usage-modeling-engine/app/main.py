"""
Usage Modeling Engine - Main FastAPI application.
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from app.config import settings
from app.routers import internal
from app.utils.logger import setup_logging, get_logger

# Setup logging
setup_logging(settings.log_level, settings.log_format)
logger = get_logger(__name__)

# Global state
profile_loader = None
usage_service = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events."""
    # Startup
    logger.info("Starting Usage Modeling Engine...")
    
    global profile_loader, usage_service
    
    # Initialize profile loader
    from app.usage.profile_loader import ProfileLoader
    
    profile_loader = ProfileLoader(settings.get_profiles_directory())
    profile_loader.load_profiles()
    logger.info(f"Loaded {len(profile_loader.list_profiles())} usage profiles")
    
    # Initialize usage service
    from app.usage.usage_service import UsageService
    
    usage_service = UsageService(profile_loader)
    internal.usage_service = usage_service
    logger.info("Initialized Usage Service")
    
    logger.info("Usage Modeling Engine started successfully")
    
    yield
    
    # Shutdown
    logger.info("Shutting down Usage Modeling Engine...")
    logger.info("Usage Modeling Engine shut down")


# Create FastAPI app
app = FastAPI(
    title="Usage Modeling Engine",
    description="AWS Usage Assumptions Service",
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
        "service": "usage-modeling-engine",
        "version": "1.0.0",
        "status": "running"
    }
