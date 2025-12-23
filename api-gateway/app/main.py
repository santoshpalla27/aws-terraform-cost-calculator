"""
API Gateway - Main Application
FastAPI application for Terraform Cost Calculator platform.
"""
from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from app.config import settings
from app.middleware.correlation import CorrelationIDMiddleware
from app.middleware.logging import RequestLoggingMiddleware
from app.middleware.rate_limit import RateLimitMiddleware, InMemoryRateLimiter
from app.routers import health, uploads, jobs, usage_profiles
from app.utils.logger import setup_logging, get_logger, get_correlation_id

# Setup logging
setup_logging(settings.log_level, settings.log_format)
logger = get_logger(__name__)

# Create FastAPI application
app = FastAPI(
    title="AWS Cost Calculator API Gateway",
    description="API Gateway for Terraform-based AWS infrastructure cost estimation",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=settings.cors_allow_credentials,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Custom middleware
app.add_middleware(CorrelationIDMiddleware)
app.add_middleware(RequestLoggingMiddleware)

# Rate limiting middleware
rate_limiter = InMemoryRateLimiter(
    requests=settings.rate_limit_requests,
    window=settings.rate_limit_window
)
app.add_middleware(RateLimitMiddleware, limiter=rate_limiter)

# Include routers
app.include_router(health.router)
app.include_router(uploads.router)
app.include_router(jobs.router)
app.include_router(usage_profiles.router)


# Global exception handlers
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Handle validation errors."""
    logger.warning(f"Validation error: {exc.errors()}")
    
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "error": {
                "code": "VALIDATION_ERROR",
                "message": "Request validation failed",
                "details": exc.errors()
            },
            "correlation_id": get_correlation_id()
        }
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Handle unexpected errors."""
    logger.error(f"Unexpected error: {str(exc)}", exc_info=True)
    
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": {
                "code": "INTERNAL_ERROR",
                "message": "An unexpected error occurred",
                "details": str(exc) if settings.log_level == "DEBUG" else None
            },
            "correlation_id": get_correlation_id()
        }
    )


@app.on_event("startup")
async def startup_event():
    """Application startup event."""
    logger.info("API Gateway starting up...")
    logger.info(f"Auth enabled: {settings.auth_enabled}")
    logger.info(f"Rate limiting enabled: {settings.rate_limit_enabled}")


@app.on_event("shutdown")
async def shutdown_event():
    """Application shutdown event."""
    logger.info("API Gateway shutting down...")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host=settings.host,
        port=settings.port,
        reload=True,
        log_level=settings.log_level.lower()
    )
