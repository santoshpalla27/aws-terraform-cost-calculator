"""Health check endpoints."""

from datetime import datetime
from fastapi import APIRouter, status

from ..models.responses import HealthCheckResponse
from ..config import settings
from ..services.orchestrator import get_orchestrator
from ..utils.logger import get_logger

logger = get_logger(__name__)

router = APIRouter(tags=["Health"])


@router.get(
    "/health",
    response_model=HealthCheckResponse,
    status_code=status.HTTP_200_OK,
    summary="Basic health check",
    description="Returns basic service health status"
)
async def health_check() -> HealthCheckResponse:
    """Basic health check endpoint."""
    return HealthCheckResponse(
        status="healthy",
        version=settings.app_version,
        timestamp=datetime.utcnow()
    )


@router.get(
    "/health/ready",
    response_model=HealthCheckResponse,
    status_code=status.HTTP_200_OK,
    summary="Readiness probe",
    description="Checks if service is ready to accept traffic"
)
async def readiness_check() -> HealthCheckResponse:
    """Readiness probe for Kubernetes/container orchestration."""
    # Could add checks for dependencies here
    return HealthCheckResponse(
        status="ready",
        version=settings.app_version,
        timestamp=datetime.utcnow()
    )


@router.get(
    "/health/live",
    response_model=HealthCheckResponse,
    status_code=status.HTTP_200_OK,
    summary="Liveness probe",
    description="Checks if service is alive"
)
async def liveness_check() -> HealthCheckResponse:
    """Liveness probe for Kubernetes/container orchestration."""
    return HealthCheckResponse(
        status="alive",
        version=settings.app_version,
        timestamp=datetime.utcnow()
    )
