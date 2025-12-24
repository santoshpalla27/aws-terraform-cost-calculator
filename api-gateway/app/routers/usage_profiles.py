"""
Usage Profiles API router.
Proxies requests to usage-modeling-engine.
"""
import httpx
from datetime import datetime
from fastapi import APIRouter, HTTPException, Request, Depends
from app.config import settings
from app.middleware.auth import get_current_user
from app.utils.logger import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/api/usage-profiles", tags=["usage-profiles"])


@router.get("")
async def get_usage_profiles(request: Request, user_id: str = Depends(get_current_user)):
    """
    Get available usage profiles.
    
    Proxies request to usage-modeling-engine and transforms response
    to match frontend ApiResponse contract.
    
    Returns:
        ApiResponse with profiles array
        
    Raises:
        HTTPException: 502 for downstream errors, 503 for service unavailable
    """
    correlation_id = getattr(request.state, 'correlation_id', 'unknown')
    
    logger.info(f"Fetching usage profiles for user={user_id}, correlation_id={correlation_id}")
    
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(
                f"{settings.usage_engine_url}/internal/usage/profiles",
                headers={"X-Correlation-ID": correlation_id}
            )
            
            # Handle downstream errors
            if response.status_code >= 500:
                logger.error(
                    f"Usage engine error: status={response.status_code}, "
                    f"correlation_id={correlation_id}"
                )
                raise HTTPException(
                    status_code=502,
                    detail="Usage service temporarily unavailable"
                )
            
            if response.status_code >= 400:
                logger.warning(
                    f"Usage engine client error: status={response.status_code}, "
                    f"correlation_id={correlation_id}"
                )
                raise HTTPException(
                    status_code=response.status_code,
                    detail=response.json().get("detail", "Bad request")
                )
            
            # Get raw response from usage engine
            raw_data = response.json()
            profiles_list = raw_data.get('profiles', [])
            default_profile = raw_data.get('default', '')
            
            # Transform to frontend format
            # Frontend expects: ApiResponse<UsageProfile[]>
            # where UsageProfile has: id, name, description, isDefault, assumptions
            transformed_profiles = []
            for profile in profiles_list:
                transformed_profiles.append({
                    "id": profile.get("name", ""),  # Use name as id
                    "name": profile.get("name", ""),
                    "description": profile.get("description", ""),
                    "isDefault": profile.get("name") == default_profile,
                    "assumptions": {}  # Empty for now, can be populated if needed
                })
            
            logger.info(
                f"Retrieved {len(transformed_profiles)} usage profiles, "
                f"default={default_profile}, correlation_id={correlation_id}"
            )
            
            # Return in canonical ApiResponse format
            return {
                "success": True,
                "data": transformed_profiles,
                "error": None,
                "correlation_id": correlation_id
            }
            
    except httpx.TimeoutException:
        logger.error(f"Usage engine timeout, correlation_id={correlation_id}")
        raise HTTPException(
            status_code=504,
            detail="Usage service request timeout"
        )
    except httpx.ConnectError:
        logger.error(f"Cannot connect to usage engine, correlation_id={correlation_id}")
        raise HTTPException(
            status_code=503,
            detail="Usage service unavailable"
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            f"Unexpected error fetching usage profiles: {e}, "
            f"correlation_id={correlation_id}",
            exc_info=True
        )
        raise HTTPException(
            status_code=500,
            detail="Internal server error"
        )


@router.post("/validate")
async def validate_usage_profile(
    request: Request,
    body: dict,
    user_id: str = Depends(get_current_user)
):
    """
    Validate usage profile configuration.
    
    Verifies that a profile ID exists and is valid.
    
    Args:
        request: FastAPI request object
        body: Request body with profile_id
        user_id: Authenticated user ID
        
    Returns:
        ApiResponse with validation result
        
    Raises:
        HTTPException: 400 if profile is invalid
    """
    correlation_id = getattr(request.state, 'correlation_id', 'unknown')
    profile_id = body.get("profile_id")
    
    if not profile_id:
        raise HTTPException(
            status_code=400,
            detail="profile_id is required"
        )
    
    logger.info(f"Validating usage profile: {profile_id}, correlation_id={correlation_id}")
    
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            # Check if profile exists by fetching all profiles
            response = await client.get(
                f"{settings.usage_engine_url}/internal/usage/profiles",
                headers={"X-Correlation-ID": correlation_id}
            )
            
            if response.status_code >= 500:
                raise HTTPException(
                    status_code=502,
                    detail="Usage service temporarily unavailable"
                )
            
            response.raise_for_status()
            profiles_data = response.json()
            profiles_list = profiles_data.get('profiles', [])
            
            # Check if profile_id exists
            valid = any(p.get('name') == profile_id for p in profiles_list)
            
            if not valid:
                return {
                    "success": False,
                    "data": {"valid": False},
                    "error": {
                        "code": "INVALID_PROFILE",
                        "message": f"Profile '{profile_id}' not found"
                    },
                    "correlation_id": correlation_id
                }
            
            
            return {
                "success": True,
                "data": {"valid": True},
                "error": None,
                "correlation_id": correlation_id
            }
            
    except httpx.TimeoutException:
        logger.error(f"Usage engine timeout, correlation_id={correlation_id}")
        raise HTTPException(
            status_code=504,
            detail="Usage service request timeout"
        )
    except httpx.ConnectError:
        logger.error(f"Cannot connect to usage engine, correlation_id={correlation_id}")
        raise HTTPException(
            status_code=503,
            detail="Usage service unavailable"
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            f"Unexpected error validating profile: {e}, "
            f"correlation_id={correlation_id}",
            exc_info=True
        )
        raise HTTPException(
            status_code=500,
            detail="Internal server error"
        )
