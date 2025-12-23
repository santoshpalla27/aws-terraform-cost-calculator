"""
Usage Profiles API router.
Proxies requests to usage-modeling-engine.
"""
import httpx
from fastapi import APIRouter, HTTPException, Request
from app.config import settings
from app.middleware.auth import get_current_user
from app.utils.logger import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/api/usage-profiles", tags=["usage-profiles"])


@router.get("")
async def get_usage_profiles(request: Request, user_id: str = get_current_user):
    """
    Get available usage profiles.
    
    Proxies request to usage-modeling-engine.
    
    Returns:
        profiles: List of available usage profiles with metadata
        default: Default profile name
        
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
            
            # Proxy response as-is
            data = response.json()
            
            logger.info(
                f"Retrieved {len(data.get('profiles', []))} usage profiles, "
                f"default={data.get('default')}, correlation_id={correlation_id}"
            )
            
            return data
            
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
