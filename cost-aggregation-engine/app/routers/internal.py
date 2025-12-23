"""
Internal cost API router.
"""
from fastapi import APIRouter, HTTPException, Depends
from app.schemas.cost import AggregateRequest, AggregateResponse
from app.utils.logger import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/internal/cost", tags=["cost"])

# Global cost service (initialized in main.py)
cost_service = None


def get_cost_service():
    """Dependency to get cost service."""
    if cost_service is None:
        raise HTTPException(status_code=503, detail="Cost service not initialized")
    return cost_service


@router.post("/aggregate", response_model=AggregateResponse)
async def aggregate_costs(
    request: AggregateRequest,
    service = Depends(get_cost_service)
):
    """
    Aggregate costs from ERG, pricing, and usage.
    
    Args:
        request: Aggregation request
        
    Returns:
        Final Cost Model (FCM)
        
    Raises:
        HTTPException: 400 for invalid input, 503 for service unavailable
    """
    logger.info(
        f"Cost aggregation: {len(request.resources)} resources, "
        f"{len(request.pricing_records)} pricing records, "
        f"{len(request.usage_records)} usage records"
    )
    
    try:
        response = await service.aggregate_costs(request)
        
        logger.info(
            f"Aggregation complete: total expected cost: ${response.fcm.total_cost.expected}, "
            f"confidence: {response.fcm.overall_confidence}"
        )
        
        return response
        
    except ValueError as e:
        logger.error(f"Invalid request: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Cost aggregation failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=503,
            detail="Cost service temporarily unavailable"
        )


@router.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "service": "cost-aggregation-engine"
    }
