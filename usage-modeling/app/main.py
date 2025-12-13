"""FastAPI application for Usage Modeling Engine."""

import logging
from fastapi import FastAPI, HTTPException, status
from pydantic import BaseModel
from typing import Dict, Any, Optional, List

from .config import settings
from .scenarios import ScenarioGenerator
from .profiles import ProfileLoader

# Setup logging
logging.basicConfig(
    level=getattr(logging, settings.log_level.upper()),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


# Request/Response models
class ScenarioRequest(BaseModel):
    """Request to generate usage scenarios."""
    resource: Dict[str, Any]
    profile: str = "prod"
    overrides: Optional[Dict[str, Any]] = None


class HealthResponse(BaseModel):
    """Health check response."""
    status: str
    version: str
    profiles: List[str]


# Create FastAPI app
app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="""
    Usage Modeling Engine - Generates cost scenarios with explicit assumptions.
    
    ## Features
    
    - **Default Profiles**: Dev, Staging, Production
    - **Resource Models**: EC2, S3, RDS, ELB
    - **Scenarios**: Min (50%), Expected (100%), Max (150%)
    - **Overrides**: API and config file support
    - **Assumption Tracking**: Every parameter documented
    """,
    docs_url="/docs",
    redoc_url="/redoc"
)


# Global instances
_generator: Optional[ScenarioGenerator] = None
_profile_loader: Optional[ProfileLoader] = None


def get_generator() -> ScenarioGenerator:
    """Get scenario generator instance."""
    global _generator
    if _generator is None:
        _generator = ScenarioGenerator()
    return _generator


def get_profile_loader() -> ProfileLoader:
    """Get profile loader instance."""
    global _profile_loader
    if _profile_loader is None:
        _profile_loader = ProfileLoader()
    return _profile_loader


@app.get(
    "/health",
    response_model=HealthResponse,
    status_code=status.HTTP_200_OK
)
async def health_check() -> HealthResponse:
    """Health check endpoint."""
    loader = get_profile_loader()
    
    return HealthResponse(
        status="healthy",
        version=settings.app_version,
        profiles=loader.list_profiles()
    )


@app.post(
    "/api/v1/scenarios",
    response_model=Dict[str, Any],
    status_code=status.HTTP_200_OK
)
async def generate_scenarios(request: ScenarioRequest) -> Dict[str, Any]:
    """Generate usage scenarios for a resource."""
    generator = get_generator()
    
    try:
        scenarios = generator.generate_scenarios(
            resource=request.resource,
            profile_name=request.profile,
            overrides=request.overrides
        )
        
        return scenarios
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Failed to generate scenarios: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate scenarios: {str(e)}"
        )


@app.get("/api/v1/profiles", response_model=List[str])
async def list_profiles() -> List[str]:
    """List available profiles."""
    loader = get_profile_loader()
    return loader.list_profiles()


@app.get("/", include_in_schema=False)
async def root():
    """Root endpoint."""
    return {
        "message": "Usage Modeling Engine",
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
