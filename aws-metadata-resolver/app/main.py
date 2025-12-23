"""
Main FastAPI application for AWS Metadata Resolver.
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routers import internal
from app.config import settings
from app.utils.logger import setup_logging, get_logger
from app.enrichment.orchestrator import EnrichmentOrchestrator
from app.aws.client_manager import AWSClientManager
from app.aws.retry_handler import RetryHandler
from app.cache.redis_cache import RedisCache
from app.cache.memory_cache import MemoryCache

# Setup logging
setup_logging(
    log_level=settings.log_level,
    log_format=settings.log_format
)

logger = get_logger(__name__)

# Create FastAPI app
app = FastAPI(
    title="AWS Metadata Resolver",
    description="Enrich Normalized Resource Graph with AWS-specific metadata",
    version="1.0.0",
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


@app.on_event("startup")
async def startup_event():
    """Application startup."""
    logger.info(
        "AWS Metadata Resolver starting",
        extra={
            'environment': settings.environment,
            'log_level': settings.log_level,
            'enabled_adapters': settings.enabled_adapters
        }
    )
    
    # Initialize cache
    if settings.enable_cache:
        try:
            cache = RedisCache(settings.redis_url)
            await cache.connect()
            logger.info("Redis cache initialized")
        except Exception as e:
            logger.warning(f"Redis cache failed, using memory cache: {e}")
            cache = MemoryCache(max_size=1000)
    else:
        cache = MemoryCache(max_size=1000)
        logger.info("Memory cache initialized")
    
    # Initialize AWS client manager
    aws_client_manager = AWSClientManager(
        role_arn=settings.aws_role_arn,
        region=settings.aws_region
    )
    
    # Initialize retry handler
    retry_handler = RetryHandler(
        max_retries=settings.max_api_retries,
        backoff_factor=settings.api_retry_backoff
    )
    
    # Initialize enrichment orchestrator
    orchestrator = EnrichmentOrchestrator(
        aws_client_manager=aws_client_manager,
        cache=cache,
        retry_handler=retry_handler,
        enabled_adapters=settings.enabled_adapters
    )
    
    # Store in router module for dependency injection
    internal.orchestrator = orchestrator
    
    logger.info("AWS Metadata Resolver started successfully")


@app.on_event("shutdown")
async def shutdown_event():
    """Application shutdown."""
    logger.info("AWS Metadata Resolver shutting down")
    
    # Disconnect cache if Redis
    if internal.orchestrator and hasattr(internal.orchestrator.cache, 'disconnect'):
        await internal.orchestrator.cache.disconnect()


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "service": "aws-metadata-resolver",
        "version": "1.0.0",
        "status": "operational"
    }
