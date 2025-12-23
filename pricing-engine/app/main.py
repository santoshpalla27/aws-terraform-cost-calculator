"""
Pricing Engine - Main FastAPI application.
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
pricing_client = None
cache = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events."""
    # Startup
    logger.info("Starting Pricing Engine...")
    
    global pricing_client, cache
    
    # Initialize pricing client
    from app.pricing.aws_pricing_client import AWSPricingClient
    pricing_client = AWSPricingClient()
    logger.info("Initialized AWS Pricing Client")
    
    # Initialize cache
    if settings.enable_cache:
        try:
            from app.cache.redis_cache import RedisCache
            cache = RedisCache(settings.redis_url)
            await cache.connect()
            logger.info("Initialized Redis cache")
        except Exception as e:
            logger.warning(f"Failed to initialize Redis cache: {e}, using in-memory cache")
            from app.cache.memory_cache import MemoryCache
            cache = MemoryCache()
    else:
        from app.cache.memory_cache import MemoryCache
        cache = MemoryCache()
        logger.info("Initialized in-memory cache")
    
    # Initialize pricing service
    from app.pricing.pricing_service import PricingService
    from app.routers import internal
    
    pricing_service = PricingService(pricing_client, cache)
    internal.pricing_service = pricing_service
    logger.info("Initialized Pricing Service")
    
    logger.info("Pricing Engine started successfully")
    
    yield
    
    # Shutdown
    logger.info("Shutting down Pricing Engine...")
    
    if pricing_client:
        await pricing_client.close()
    
    if cache:
        await cache.disconnect()
    
    logger.info("Pricing Engine shut down")


# Create FastAPI app
app = FastAPI(
    title="Pricing Engine",
    description="AWS Pricing Data Service",
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
        "service": "pricing-engine",
        "version": "1.0.0",
        "status": "running"
    }
