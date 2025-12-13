"""FastAPI application for Pricing Engine."""

import logging
from fastapi import FastAPI, HTTPException, BackgroundTasks, status
from pydantic import BaseModel
from typing import Dict, Any, Optional

from .config import settings
from .database import init_db
from .ingestion import PricingIngestion
from .lookup import PricingLookup

# Setup logging
logging.basicConfig(
    level=getattr(logging, settings.log_level.upper()),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


# Request/Response models
class LookupRequest(BaseModel):
    """Pricing lookup request."""
    service_code: str
    region: str
    attributes: Dict[str, Any]
    term_type: str = "OnDemand"


class HealthResponse(BaseModel):
    """Health check response."""
    status: str
    version: str
    database: str


# Create FastAPI app
app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="""
    AWS Pricing Engine - Retrieves and normalizes AWS pricing data.
    
    ## Features
    
    - **Price List API**: Single source of truth for pricing
    - **PostgreSQL Storage**: Normalized pricing tables
    - **Version Snapshots**: Historical pricing data
    - **Deterministic Lookups**: SKU-based pricing resolution
    - **Unit Conversion**: Hourly, GB-month, requests
    """,
    docs_url="/docs",
    redoc_url="/redoc"
)


# Global instances
_lookup: Optional[PricingLookup] = None
_ingestion: Optional[PricingIngestion] = None


def get_lookup() -> PricingLookup:
    """Get pricing lookup instance."""
    global _lookup
    if _lookup is None:
        _lookup = PricingLookup()
    return _lookup


def get_ingestion() -> PricingIngestion:
    """Get pricing ingestion instance."""
    global _ingestion
    if _ingestion is None:
        _ingestion = PricingIngestion()
    return _ingestion


@app.on_event("startup")
async def startup_event():
    """Initialize database on startup."""
    try:
        init_db()
        logger.info("Database initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize database: {e}")


@app.get(
    "/health",
    response_model=HealthResponse,
    status_code=status.HTTP_200_OK
)
async def health_check() -> HealthResponse:
    """Health check endpoint."""
    return HealthResponse(
        status="healthy",
        version=settings.app_version,
        database="connected"
    )


@app.post(
    "/api/v1/lookup",
    response_model=Dict[str, Any],
    status_code=status.HTTP_200_OK
)
async def lookup_pricing(request: LookupRequest) -> Dict[str, Any]:
    """Lookup pricing for a resource."""
    lookup = get_lookup()
    
    result = lookup.lookup_price(
        service_code=request.service_code,
        region=request.region,
        attributes=request.attributes,
        term_type=request.term_type
    )
    
    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Pricing not found"
        )
    
    return result


@app.post(
    "/api/v1/ingest",
    status_code=status.HTTP_202_ACCEPTED
)
async def trigger_ingestion(background_tasks: BackgroundTasks):
    """Trigger pricing ingestion (background task)."""
    ingestion = get_ingestion()
    background_tasks.add_task(ingestion.ingest_all_services)
    
    return {"message": "Ingestion started"}


@app.get("/", include_in_schema=False)
async def root():
    """Root endpoint."""
    return {
        "message": "AWS Pricing Engine",
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
