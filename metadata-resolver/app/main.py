"""FastAPI application for Metadata Resolver."""

import logging
from fastapi import FastAPI, HTTPException, status
from pydantic import BaseModel
from typing import Dict, Any

from .config import settings
from .enricher import MetadataEnricher
from .cache import get_cache

# Setup logging
logging.basicConfig(
    level=getattr(logging, settings.log_level.upper()),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


# Request/Response models
class EnrichRequest(BaseModel):
    """Request to enrich NRG."""
    nrg: Dict[str, Any]
    
    class Config:
        json_schema_extra = {
            "example": {
                "nrg": {
                    "resources": [],
                    "metadata": {},
                    "terraform_version": "1.6.6",
                    "format_version": "1.2"
                }
            }
        }


class HealthResponse(BaseModel):
    """Health check response."""
    status: str
    version: str
    cache_stats: Dict[str, Any]


# Create FastAPI app
app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="""
    AWS Metadata Resolver - Enriches Terraform resources with AWS-derived metadata.
    
    ## Features
    
    - **EC2 Metadata**: Default EBS volumes, instance specs, networking
    - **ALB/NLB Metadata**: LCU factors, cross-zone behavior
    - **NAT Gateway Metadata**: Bandwidth, data processing characteristics
    - **EKS Metadata**: Control plane costs, configuration
    - **Aggressive Caching**: Minimizes AWS API calls
    - **Graceful Degradation**: Returns original resource if metadata unavailable
    """,
    docs_url="/docs",
    redoc_url="/redoc"
)


# Global enricher instance
_enricher: MetadataEnricher | None = None


def get_enricher() -> MetadataEnricher:
    """Get the global enricher instance."""
    global _enricher
    if _enricher is None:
        _enricher = MetadataEnricher()
    return _enricher


@app.get(
    "/health",
    response_model=HealthResponse,
    status_code=status.HTTP_200_OK,
    summary="Health check"
)
async def health_check() -> HealthResponse:
    """Health check endpoint."""
    cache = get_cache()
    cache_stats = cache.get_stats()
    
    return HealthResponse(
        status="healthy",
        version=settings.app_version,
        cache_stats=cache_stats
    )


@app.post(
    "/api/v1/enrich",
    response_model=Dict[str, Any],
    status_code=status.HTTP_200_OK,
    summary="Enrich NRG with AWS metadata",
    description="Enriches Normalized Resource Graph with AWS-derived metadata"
)
async def enrich_nrg(request: EnrichRequest) -> Dict[str, Any]:
    """Enrich NRG with AWS metadata.
    
    This endpoint:
    1. Routes resources to appropriate resolvers
    2. Fetches metadata from AWS (with caching)
    3. Merges metadata into resource attributes
    4. Returns enriched NRG
    """
    enricher = get_enricher()
    
    try:
        # Enrich NRG
        enriched_nrg = enricher.enrich(request.nrg)
        
        logger.info(f"Successfully enriched NRG with {len(enriched_nrg.get('resources', []))} resources")
        
        return enriched_nrg
        
    except Exception as e:
        logger.error(f"Failed to enrich NRG: {str(e)}", exc_info=True)
        
        if settings.enable_graceful_degradation:
            # Return original NRG with degradation flag
            logger.warning("Returning original NRG due to enrichment failure")
            return request.nrg
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to enrich NRG: {str(e)}"
            )


@app.post(
    "/api/v1/cache/clear",
    status_code=status.HTTP_200_OK,
    summary="Clear cache"
)
async def clear_cache(cache_type: str = None):
    """Clear metadata cache."""
    cache = get_cache()
    cache.clear(cache_type)
    
    return {"message": f"Cache cleared: {cache_type or 'all'}"}


@app.get("/", include_in_schema=False)
async def root():
    """Root endpoint."""
    return {
        "message": "AWS Metadata Resolver",
        "version": settings.app_version,
        "docs": "/docs"
    }


if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "app.main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug
    )
