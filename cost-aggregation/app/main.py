"""FastAPI application for Cost Aggregation Engine."""

import logging
from fastapi import FastAPI, HTTPException, status
from pydantic import BaseModel
from typing import Dict, Any, List

from .config import settings
from .schema import CostEstimate, CostDiff
from .calculator import CostCalculator
from .aggregator import CostAggregator
from .diff import DiffEngine

# Setup logging
logging.basicConfig(
    level=getattr(logging, settings.log_level.upper()),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


# Request models
class EstimateRequest(BaseModel):
    """Request to generate cost estimate."""
    resources: List[Dict[str, Any]]
    pricing_data: List[Dict[str, Any]]
    usage_data: List[Dict[str, Any]]
    profile: str = "prod"


class DiffRequest(BaseModel):
    """Request to calculate cost diff."""
    before: EstimateRequest
    after: EstimateRequest


class HealthResponse(BaseModel):
    """Health check response."""
    status: str
    version: str


# Create FastAPI app
app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="""
    Cost Aggregation Engine - Pure computation engine for cost estimation.
    
    ## Features
    
    - **Pure Computation**: cost = usage × pricing
    - **Aggregations**: Per-resource, per-service, per-region
    - **Terraform Diff**: Before vs after comparison
    - **Cost Drivers**: Top cost contributors
    - **Confidence Scoring**: Based on metadata quality
    """,
    docs_url="/docs",
    redoc_url="/redoc"
)


# Global instances
calculator = CostCalculator()
aggregator = CostAggregator()
diff_engine = DiffEngine()


@app.get(
    "/health",
    response_model=HealthResponse,
    status_code=status.HTTP_200_OK
)
async def health_check() -> HealthResponse:
    """Health check endpoint."""
    return HealthResponse(
        status="healthy",
        version=settings.app_version
    )


@app.post(
    "/api/v1/estimate",
    response_model=CostEstimate,
    status_code=status.HTTP_200_OK
)
async def generate_estimate(request: EstimateRequest) -> CostEstimate:
    """Generate cost estimate.
    
    Computes costs for all resources and aggregates by service/region.
    """
    try:
        # Create pricing and usage maps
        pricing_map = {p["sku"]: p for p in request.pricing_data}
        usage_map = {u["resource_id"]: u for u in request.usage_data}
        
        # Calculate costs for each resource
        resource_costs = []
        for resource in request.resources:
            resource_id = resource.get("resource_id")
            
            # Get pricing and usage
            pricing = pricing_map.get(resource.get("sku", ""), {})
            usage = usage_map.get(resource_id, {})
            
            if not pricing or not usage:
                logger.warning(f"Missing pricing or usage for {resource_id}")
                continue
            
            # Calculate cost
            resource_cost = calculator.calculate_resource_cost(
                resource=resource,
                pricing=pricing,
                usage=usage,
                profile=request.profile
            )
            resource_costs.append(resource_cost)
        
        # Aggregate
        estimate = aggregator.aggregate(resource_costs, request.profile)
        
        return estimate
        
    except Exception as e:
        logger.error(f"Failed to generate estimate: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate estimate: {str(e)}"
        )


@app.post(
    "/api/v1/diff",
    response_model=CostDiff,
    status_code=status.HTTP_200_OK
)
async def calculate_diff(request: DiffRequest) -> CostDiff:
    """Calculate cost diff between before and after states.
    
    Useful for Terraform plan cost analysis.
    """
    try:
        # Generate before estimate
        before_estimate = await generate_estimate(request.before)
        
        # Generate after estimate
        after_estimate = await generate_estimate(request.after)
        
        # Calculate diff
        diff = diff_engine.calculate_diff(before_estimate, after_estimate)
        
        return diff
        
    except Exception as e:
        logger.error(f"Failed to calculate diff: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to calculate diff: {str(e)}"
        )


@app.get("/", include_in_schema=False)
async def root():
    """Root endpoint."""
    return {
        "message": "Cost Aggregation Engine",
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
