"""FastAPI application for Plan Parser."""

import logging
from fastapi import FastAPI, HTTPException, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import Dict, Any

from .config import settings
from .parser import TerraformPlanParser
from .schema import NRG

# Setup logging
logging.basicConfig(
    level=getattr(logging, settings.log_level.upper()),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


# Request/Response models
class ParseRequest(BaseModel):
    """Request to parse Terraform plan."""
    plan_json: Dict[str, Any]
    
    class Config:
        json_schema_extra = {
            "example": {
                "plan_json": {
                    "format_version": "1.2",
                    "terraform_version": "1.6.6",
                    "resource_changes": []
                }
            }
        }


class HealthResponse(BaseModel):
    """Health check response."""
    status: str
    version: str


# Create FastAPI app
app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="""
    Terraform Plan Parser - Converts Terraform plan JSON into Normalized Resource Graph (NRG).
    
    ## Features
    
    - **Cloud-Agnostic**: Works with AWS, Azure, GCP, and other providers
    - **Count/For_each Resolution**: Fully resolves count and for_each meta-arguments
    - **Module Flattening**: Flattens module hierarchy while preserving relationships
    - **Confidence Scoring**: Calculates confidence based on known vs. computed attributes
    - **Deterministic Output**: Consistent NRG schema for downstream processing
    """,
    docs_url="/docs",
    redoc_url="/redoc"
)


# Global parser instance
_parser: TerraformPlanParser | None = None


def get_parser() -> TerraformPlanParser:
    """Get the global parser instance."""
    global _parser
    if _parser is None:
        _parser = TerraformPlanParser()
    return _parser


@app.get(
    "/health",
    response_model=HealthResponse,
    status_code=status.HTTP_200_OK,
    summary="Health check"
)
async def health_check() -> HealthResponse:
    """Health check endpoint."""
    return HealthResponse(
        status="healthy",
        version=settings.app_version
    )


@app.post(
    "/api/v1/parse",
    response_model=NRG,
    status_code=status.HTTP_200_OK,
    summary="Parse Terraform plan JSON",
    description="Converts Terraform plan JSON into Normalized Resource Graph"
)
async def parse_plan(request: ParseRequest) -> NRG:
    """Parse Terraform plan JSON into NRG.
    
    This endpoint:
    1. Extracts resources from plan JSON
    2. Resolves count and for_each meta-arguments
    3. Flattens module hierarchy
    4. Calculates confidence scores
    5. Returns normalized resource graph
    """
    parser = get_parser()
    
    try:
        # Parse plan
        nrg = parser.parse(request.plan_json)
        
        # Track relationships (optional)
        nrg = parser.track_relationships(nrg)
        
        logger.info(f"Successfully parsed plan with {len(nrg.resources)} resources")
        
        return nrg
        
    except Exception as e:
        logger.error(f"Failed to parse plan: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to parse plan: {str(e)}"
        )


@app.get("/", include_in_schema=False)
async def root():
    """Root endpoint."""
    return {
        "message": "Terraform Plan Parser",
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
