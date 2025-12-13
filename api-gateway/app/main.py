"""Main FastAPI application."""

from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException

from .config import settings
from .utils.logger import setup_logging, get_logger
from .middleware.logging import LoggingMiddleware
from .routers import health_router, uploads_router, jobs_router
from .services.orchestrator import get_orchestrator

# Setup logging
setup_logging()
logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events."""
    # Startup
    logger.info(
        "Starting API Gateway",
        app_name=settings.app_name,
        version=settings.app_version,
        debug=settings.debug
    )
    
    yield
    
    # Shutdown
    logger.info("Shutting down API Gateway")
    
    # Close orchestrator HTTP client
    orchestrator = get_orchestrator()
    await orchestrator.close()


# Create FastAPI application
app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="""
    Production-grade API Gateway for AWS Terraform Cost Estimation Platform.
    
    ## Features
    
    - **Upload Terraform Files**: Upload ZIP or individual Terraform files
    - **Job Management**: Create, track, and manage cost estimation jobs
    - **Status Tracking**: Monitor job progress with real-time status updates
    - **Rate Limiting**: Built-in rate limiting to prevent abuse
    - **Authentication**: Optional JWT-based authentication
    - **Structured Logging**: JSON-formatted logs with correlation IDs
    
    ## Workflow
    
    1. Upload Terraform files using `/api/v1/uploads`
    2. Create a cost estimation job using `/api/v1/jobs` with the upload ID
    3. Poll job status using `/api/v1/jobs/{job_id}`
    4. Retrieve results when job status is `COMPLETED`
    """,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    lifespan=lifespan,
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add logging middleware
app.add_middleware(LoggingMiddleware)

# Register routers
app.include_router(health_router)
app.include_router(uploads_router)
app.include_router(jobs_router)


# Exception handlers
@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    """Handle HTTP exceptions."""
    logger.warning(
        "HTTP exception",
        status_code=exc.status_code,
        detail=exc.detail,
        path=request.url.path
    )
    
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": "HTTPException",
            "message": exc.detail,
        }
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Handle validation errors."""
    logger.warning(
        "Validation error",
        errors=exc.errors(),
        path=request.url.path
    )
    
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "error": "ValidationError",
            "message": "Invalid request parameters",
            "detail": exc.errors()
        }
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Handle unexpected exceptions."""
    logger.error(
        "Unhandled exception",
        error=str(exc),
        error_type=type(exc).__name__,
        path=request.url.path,
        exc_info=True
    )
    
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": "InternalServerError",
            "message": "An unexpected error occurred",
        }
    )


# Root endpoint
@app.get("/", include_in_schema=False)
async def root():
    """Root endpoint redirect to docs."""
    return {
        "message": "Terraform Cost Estimator API Gateway",
        "version": settings.app_version,
        "docs": "/docs",
        "health": "/health"
    }


if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "app.main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug,
        log_level=settings.log_level.lower()
    )
