"""
Internal pricing API router.
"""
from fastapi import APIRouter, HTTPException, Depends
from app.schemas.pricing import PriceLookupRequest, PriceLookupResponse
from app.utils.logger import get_logger
from app.utils.region_mapper import RegionMapper
from app.config import settings

logger = get_logger(__name__)

router = APIRouter(prefix="/internal/pricing", tags=["pricing"])

# Global pricing service (initialized in main.py)
pricing_service = None


def get_pricing_service():
    """Dependency to get pricing service."""
    if pricing_service is None:
        raise HTTPException(status_code=503, detail="Pricing service not initialized")
    return pricing_service


@router.post("/lookup", response_model=PriceLookupResponse)
async def lookup_pricing(
    request: PriceLookupRequest,
    service = Depends(get_pricing_service)
):
    """
    Lookup pricing for a resource.
    
    Args:
        request: Pricing lookup request
        
    Returns:
        Pricing lookup response with unit prices
        
    Raises:
        HTTPException: 400 for invalid input, 404 for no prices found, 503 for service unavailable
    """
    logger.info(f"Pricing lookup: service={request.service}, region={request.region}, resource_type={request.resource_type}")
    
    # Validate service
    supported_services = settings.get_supported_services_list()
    if request.service not in supported_services:
        logger.error(f"Unsupported service: {request.service}")
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported service: {request.service}. Supported: {', '.join(supported_services)}"
        )
    
    # Validate region
    if not RegionMapper.is_supported_region(request.region):
        logger.error(f"Unsupported region: {request.region}")
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported region: {request.region}"
        )
    
    try:
        # Perform pricing lookup
        response = await service.lookup_pricing(request)
        
        # Check if prices were found
        if not response.prices:
            logger.warning(f"No prices found for {request.service}/{request.resource_type} in {request.region}")
            raise HTTPException(
                status_code=404,
                detail=f"No pricing found for {request.service}/{request.resource_type} in {request.region}"
            )
        
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Pricing lookup failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=503,
            detail="Pricing service temporarily unavailable"
        )


@router.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "service": "pricing-engine"
    }


@router.get("/metadata")
async def get_metadata():
    """Get pricing metadata."""
    return {
        "supported_services": settings.get_supported_services_list(),
        "supported_regions": list(RegionMapper.get_all_regions().keys()),
        "cache_enabled": settings.enable_cache
    }
