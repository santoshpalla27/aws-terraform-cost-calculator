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
    """
    List available usage profiles with metadata.
    
    Returns:
        profiles: List of profile metadata (name, description, version)
        default: Default profile name from configuration
        
    Raises:
        HTTPException: 500 if profiles directory missing or no profiles found
    """
    try:
        from app.config import settings
        
        profile_names = service.profile_loader.list_profiles()
        
        # Return error if no profiles found
        if not profile_names:
            logger.error("No usage profiles found")
            raise HTTPException(
                status_code=500,
                detail="No usage profiles available"
            )
        
        # Build profile metadata list
        profiles = []
        for name in profile_names:
            try:
                profile_data = service.profile_loader.get_profile(name)
                profiles.append({
                    "name": profile_data.get("name", name),
                    "description": profile_data.get("description", ""),
                    "version": profile_data.get("version", "v1")
                })
            except Exception as e:
                logger.warning(f"Failed to load metadata for profile '{name}': {e}")
                # Include profile with minimal data if metadata load fails
                profiles.append({
                    "name": name,
                    "description": f"Usage profile: {name}",
                    "version": "v1"
                })
        
        logger.info(f"Returning {len(profiles)} usage profiles, default={settings.default_usage_profile}")
        
        return {
            "profiles": profiles,
            "default": settings.default_usage_profile
        }
        
    except HTTPException:
        raise
    except FileNotFoundError as e:
        logger.error(f"Profiles directory not found: {e}")
        raise HTTPException(
            status_code=500,
            detail="Profiles directory not found"
        )
    except Exception as e:
        logger.error(f"Failed to list profiles: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail="Failed to retrieve usage profiles"
        )


@router.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "service": "usage-modeling-engine"
    }
