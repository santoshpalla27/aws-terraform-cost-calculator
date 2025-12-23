"""
Internal usage API router.
"""
from fastapi import APIRouter, HTTPException, Depends
from app.schemas.usage import ApplyUsageRequest, ApplyUsageResponse
from app.utils.logger import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/internal/usage", tags=["usage"])

# Global usage service (initialized in main.py)
usage_service = None


def get_usage_service():
    """Dependency to get usage service."""
    if usage_service is None:
        raise HTTPException(status_code=503, detail="Usage service not initialized")
    return usage_service


@router.post("/apply", response_model=ApplyUsageResponse)
async def apply_usage(
    request: ApplyUsageRequest,
    service = Depends(get_usage_service)
):
    """
    Apply usage assumptions to resources.
    
    Args:
        request: Usage application request
        
    Returns:
        Usage-annotated resource graph (UARG)
        
    Raises:
        HTTPException: 400 for invalid input, 503 for service unavailable
    """
    logger.info(f"Applying usage: profile={request.profile}, resources={len(request.resources)}, overrides={len(request.overrides)}")
    
    try:
        response = await service.apply_usage(request)
        
        logger.info(f"Applied usage to {len(response.uarg.resources)} resources")
        
        return response
        
    except ValueError as e:
        logger.error(f"Invalid request: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Usage application failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=503,
            detail="Usage service temporarily unavailable"
        )


@router.get("/profiles")
async def list_profiles(service = Depends(get_usage_service)):
    """List available usage profiles."""
    try:
        profiles = service.profile_loader.list_profiles()
        return {
            "profiles": profiles,
            "count": len(profiles)
        }
    except Exception as e:
        logger.error(f"Failed to list profiles: {e}")
        raise HTTPException(status_code=503, detail="Failed to list profiles")


@router.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "service": "usage-modeling-engine"
    }
