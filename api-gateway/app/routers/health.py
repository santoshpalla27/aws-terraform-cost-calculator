"""
Health check endpoints.
"""
from datetime import datetime
from fastapi import APIRouter
from app.models.responses import HealthResponse

router = APIRouter(tags=["health"])


@router.get("/health", response_model=HealthResponse)
async def health_check():
    """Basic health check endpoint."""
    return HealthResponse(
        status="healthy",
        timestamp=datetime.utcnow().isoformat() + 'Z'
    )


@router.get("/health/ready", response_model=HealthResponse)
async def readiness_check():
    """Readiness probe for Kubernetes."""
    # TODO: Check dependencies (database, etc.)
    return HealthResponse(
        status="ready",
        timestamp=datetime.utcnow().isoformat() + 'Z'
    )


@router.get("/health/live", response_model=HealthResponse)
async def liveness_check():
    """Liveness probe for Kubernetes."""
    return HealthResponse(
        status="alive",
        timestamp=datetime.utcnow().isoformat() + 'Z'
    )
