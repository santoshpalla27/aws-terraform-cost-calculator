"""
Internal API endpoints for metadata enrichment.
"""
from fastapi import APIRouter, HTTPException, status, Depends
from app.schemas.api import EnrichRequest, EnrichResponse
from app.enrichment.orchestrator import EnrichmentOrchestrator
from app.aws.client_manager import AWSClientManager
from app.aws.retry_handler import RetryHandler
from app.cache.redis_cache import RedisCache
from app.cache.memory_cache import MemoryCache
from app.config import settings
from app.utils.logger import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/internal", tags=["internal"])

# Global instances (initialized in main.py)
orchestrator: EnrichmentOrchestrator | None = None


def get_orchestrator() -> EnrichmentOrchestrator:
    """Dependency to get enrichment orchestrator."""
    if orchestrator is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Enrichment orchestrator not initialized"
        )
    return orchestrator


@router.post(
    "/enrich",
    response_model=EnrichResponse,
    status_code=status.HTTP_200_OK,
    summary="Enrich NRG with AWS metadata",
    description="Enrich Normalized Resource Graph with AWS-specific metadata"
)
async def enrich_resources(
    request: EnrichRequest,
    orch: EnrichmentOrchestrator = Depends(get_orchestrator)
) -> EnrichResponse:
    """
    Enrich NRG to produce ERG.
    
    This is a read-only operation that calls AWS APIs.
    """
    logger.info(
        f"Received enrichment request for {len(request.normalized_resource_graph)} resources"
    )
    
    try:
        # Enrich resources
        erg_nodes, metadata = await orch.enrich(
            request.normalized_resource_graph,
            request.aws_account_id or "unknown"
        )
        
        logger.info(
            f"Enrichment complete: {metadata.total_resources} total resources",
            extra={
                'terraform_resources': metadata.terraform_resources,
                'implicit_resources': metadata.implicit_resources,
                'cache_hit_rate': metadata.cache_hit_rate,
                'duration_ms': metadata.enrichment_duration_ms
            }
        )
        
        return EnrichResponse(
            enriched_resource_graph=[node.model_dump() for node in erg_nodes],
            enrichment_metadata=metadata.model_dump()
        )
    
    except Exception as e:
        logger.error(f"Enrichment failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Enrichment failed: {str(e)}"
        )


@router.get(
    "/health",
    status_code=status.HTTP_200_OK,
    summary="Health check"
)
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "service": "aws-metadata-resolver",
        "cache_enabled": settings.enable_cache
    }
