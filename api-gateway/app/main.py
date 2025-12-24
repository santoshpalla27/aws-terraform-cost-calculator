"""
API Gateway - Main Application
FastAPI application for Terraform Cost Calculator platform.
"""
from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError, HTTPException
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
    from datetime import datetime
    correlation_id = get_correlation_id()
    errors = exc.errors()
    
    # Sanitize error details to avoid JSON serialization issues with bytes
    sanitized_errors = []
    for error in errors:
        sanitized_error = error.copy()
        # Convert bytes to string representation in input field
        if 'input' in sanitized_error and isinstance(sanitized_error['input'], dict):
            sanitized_input = {}
            for key, value in sanitized_error['input'].items():
                if isinstance(value, bytes):
                    sanitized_input[key] = f"<bytes: {len(value)} bytes>"
                else:
                    sanitized_input[key] = value
            sanitized_error['input'] = sanitized_input
        sanitized_errors.append(sanitized_error)
    
    logger.warning(f"Validation error: {sanitized_errors}", extra={"correlation_id": correlation_id})
    
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "success": False,
            "data": None,
            "error": {
                "code": "VALIDATION_ERROR",
                "message": "Request validation failed",
                "details": sanitized_errors
            },
            "correlation_id": correlation_id
        }
    )


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """Handle HTTP exceptions."""
    from datetime import datetime
    correlation_id = get_correlation_id()
    logger.warning(
        f"HTTP exception: {exc.status_code} - {exc.detail}",
        extra={"correlation_id": correlation_id, "status_code": exc.status_code}
    )
    
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "success": False,
            "data": None,
            "error": {
                "code": f"HTTP_{exc.status_code}",
                "message": exc.detail if isinstance(exc.detail, str) else str(exc.detail)
            },
            "correlation_id": correlation_id
        }
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Handle unexpected errors."""
    from datetime import datetime
    correlation_id = get_correlation_id()
    logger.error(f"Unexpected error: {str(exc)}", exc_info=True, extra={"correlation_id": correlation_id})
    
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "success": False,
            "data": None,
            "error": {
                "code": "INTERNAL_ERROR",
                "message": "An unexpected error occurred"
            },
            "correlation_id": correlation_id
        }
    )


@app.on_event("startup")
async def startup_event():
    """Application startup event."""
    logger.info("API Gateway starting up...")
    logger.info(f"Auth enabled: {settings.auth_enabled}")
    logger.info(f"Rate limiting enabled: {settings.rate_limit_enabled}")
    
    # Initialize database
    from app.database.connection import init_db
    await init_db()
    logger.info("Database initialized")


@app.on_event("shutdown")
async def shutdown_event():
    """Application shutdown event."""
    logger.info("API Gateway shutting down...")
    
    # Close database connections
    from app.database.connection import close_db
    await close_db()
    logger.info("Database connections closed")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host=settings.host,
        port=settings.port,
        reload=True,
        log_level=settings.log_level.lower()
    )
