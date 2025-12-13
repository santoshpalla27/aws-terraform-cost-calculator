"""FastAPI application for Results Storage & Reporting."""

import logging
from fastapi import FastAPI, HTTPException, status, Depends
from pydantic import BaseModel
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import desc

from .config import settings
from .database import init_db, get_db_session
from .models import Job, CostResult, ServiceCost, RegionCost
from .storage import ResultsStorage

# Setup logging
logging.basicConfig(
    level=getattr(logging, settings.log_level.upper()),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


# Request/Response models
class StoreRequest(BaseModel):
    """Request to store cost estimate."""
    estimate: Dict[str, Any]
    user_id: Optional[str] = None
    terraform_plan_hash: Optional[str] = None


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
    Results Storage & Reporting Service - Persistent storage for cost estimates.
    
    ## Features
    
    - **Immutable Records**: INSERT-only, no updates/deletes
    - **Read-Only APIs**: Fast retrieval for dashboards
    - **Historical Comparisons**: Compare jobs over time
    - **Denormalized Aggregations**: Fast service/region queries
    """,
    docs_url="/docs",
    redoc_url="/redoc"
)


# Global instances
storage = ResultsStorage()


def get_db():
    """Dependency for database session."""
    db = get_db_session()
    try:
        yield db
    finally:
        db.close()


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
    "/api/v1/store",
    status_code=status.HTTP_201_CREATED
)
async def store_estimate(request: StoreRequest) -> Dict[str, str]:
    """Store cost estimate (immutable)."""
    try:
        job_id = storage.store_estimate(
            estimate=request.estimate,
            user_id=request.user_id,
            terraform_plan_hash=request.terraform_plan_hash
        )
        
        return {"job_id": job_id}
        
    except Exception as e:
        logger.error(f"Failed to store estimate: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to store estimate: {str(e)}"
        )


@app.get("/api/v1/jobs/{job_id}")
async def get_job(job_id: str, db: Session = Depends(get_db)) -> Dict[str, Any]:
    """Get job by ID with full results."""
    job = db.query(Job).filter(Job.job_id == job_id).first()
    
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Job not found: {job_id}"
        )
    
    return {
        "job_id": str(job.job_id),
        "created_at": job.created_at.isoformat(),
        "profile": job.profile,
        "total_monthly_cost": float(job.total_monthly_cost) if job.total_monthly_cost else 0,
        "confidence_score": float(job.confidence_score) if job.confidence_score else 0,
        "resource_count": job.resource_count,
        "status": job.status
    }


@app.get("/api/v1/jobs")
async def list_jobs(
    user_id: Optional[str] = None,
    limit: int = 10,
    db: Session = Depends(get_db)
) -> List[Dict[str, Any]]:
    """List recent jobs."""
    query = db.query(Job)
    
    if user_id:
        query = query.filter(Job.user_id == user_id)
    
    jobs = query.order_by(desc(Job.created_at)).limit(limit).all()
    
    return [
        {
            "job_id": str(job.job_id),
            "created_at": job.created_at.isoformat(),
            "profile": job.profile,
            "total_monthly_cost": float(job.total_monthly_cost) if job.total_monthly_cost else 0,
            "resource_count": job.resource_count
        }
        for job in jobs
    ]


@app.get("/api/v1/jobs/{job_id}/resources")
async def get_resources(job_id: str, db: Session = Depends(get_db)) -> List[Dict[str, Any]]:
    """Get resource costs for a job."""
    resources = db.query(CostResult).filter(CostResult.job_id == job_id).order_by(
        desc(CostResult.total_monthly_cost)
    ).all()
    
    if not resources:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No resources found for job: {job_id}"
        )
    
    return [
        {
            "resource_id": r.resource_id,
            "resource_type": r.resource_type,
            "service": r.service,
            "region": r.region,
            "total_monthly_cost": float(r.total_monthly_cost),
            "confidence_score": float(r.confidence_score) if r.confidence_score else 0
        }
        for r in resources
    ]


@app.get("/api/v1/jobs/{job_id}/services")
async def get_services(job_id: str, db: Session = Depends(get_db)) -> List[Dict[str, Any]]:
    """Get service aggregation for a job."""
    services = db.query(ServiceCost).filter(ServiceCost.job_id == job_id).order_by(
        desc(ServiceCost.total_cost)
    ).all()
    
    return [
        {
            "service": s.service,
            "total_cost": float(s.total_cost),
            "resource_count": s.resource_count
        }
        for s in services
    ]


@app.get("/api/v1/jobs/{job_id}/regions")
async def get_regions(job_id: str, db: Session = Depends(get_db)) -> List[Dict[str, Any]]:
    """Get region aggregation for a job."""
    regions = db.query(RegionCost).filter(RegionCost.job_id == job_id).order_by(
        desc(RegionCost.total_cost)
    ).all()
    
    return [
        {
            "region": r.region,
            "total_cost": float(r.total_cost),
            "resource_count": r.resource_count,
            "services": r.services
        }
        for r in regions
    ]


@app.get("/api/v1/compare")
async def compare_jobs(
    job_id_1: str,
    job_id_2: str,
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """Compare two jobs."""
    job1 = db.query(Job).filter(Job.job_id == job_id_1).first()
    job2 = db.query(Job).filter(Job.job_id == job_id_2).first()
    
    if not job1 or not job2:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="One or both jobs not found"
        )
    
    delta = float(job2.total_monthly_cost - job1.total_monthly_cost)
    percentage = (delta / float(job1.total_monthly_cost) * 100) if job1.total_monthly_cost else 0
    
    return {
        "job_1": {
            "job_id": str(job1.job_id),
            "total_cost": float(job1.total_monthly_cost),
            "created_at": job1.created_at.isoformat()
        },
        "job_2": {
            "job_id": str(job2.job_id),
            "total_cost": float(job2.total_monthly_cost),
            "created_at": job2.created_at.isoformat()
        },
        "delta": delta,
        "percentage_change": round(percentage, 2)
    }


@app.get("/", include_in_schema=False)
async def root():
    """Root endpoint."""
    return {
        "message": "Results Storage & Reporting Service",
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
