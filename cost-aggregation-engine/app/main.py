"""
Cost Aggregation Engine - Main FastAPI application.
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
cost_service = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events."""
    # Startup
    logger.info("Starting Cost Aggregation Engine...")
    
    global cost_service
    
    # Initialize cost service
    from app.cost_service import CostService
    
    cost_service = CostService(
        default_currency=settings.default_currency,
        enable_determinism_hash=settings.enable_determinism_hash
    )
    internal.cost_service = cost_service
    logger.info("Initialized Cost Service")
    
    logger.info(f"Decimal precision: {settings.decimal_precision}")
    logger.info(f"Default currency: {settings.default_currency}")
    logger.info("Cost Aggregation Engine started successfully")
    
    yield
    
    # Shutdown
    logger.info("Shutting down Cost Aggregation Engine...")
    logger.info("Cost Aggregation Engine shut down")


# Create FastAPI app
app = FastAPI(
    title="Cost Aggregation Engine",
    description="AWS Cost Computation Service",
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
        "service": "cost-aggregation-engine",
        "version": "1.0.0",
        "status": "running",
        "decimal_precision": settings.decimal_precision,
        "currency": settings.default_currency
    }
