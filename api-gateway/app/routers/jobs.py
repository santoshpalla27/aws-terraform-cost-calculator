"""
Job endpoints.
"""
from typing import Optional
from fastapi import APIRouter, Depends, Query, status, Request
from app.models.domain import JobStatus
from app.models.requests import CreateJobRequest
from app.models.responses import JobResponse, PaginatedResponse
from app.models.domain import Job
from app.services.job_service import job_service
from app.middleware.auth import get_current_user
import math

router = APIRouter(prefix="/api/jobs", tags=["jobs"])


@router.post("", status_code=status.HTTP_201_CREATED)
async def create_job(
    request_obj: Request,
    request: CreateJobRequest,
    user_id: str = Depends(get_current_user)
):
    """
    Create a new cost estimation job.
    
    The job will be created in CREATED status and queued for processing.
    """
    from datetime import datetime
    correlation_id = getattr(request_obj.state, 'correlation_id', 'unknown')
    job = await job_service.create_job(request, user_id)
    
    return {
        "success": True,
        "data": job,
        "error": None,
        "correlation_id": correlation_id
    }


@router.get("/{job_id}")
async def get_job(
    request: Request,
    job_id: str,
    user_id: str = Depends(get_current_user)
):
    """Get job details by ID."""
    from datetime import datetime
    correlation_id = getattr(request.state, 'correlation_id', 'unknown')
    job = await job_service.get_job(job_id, user_id)
    
    return {
        "success": True,
        "data": job,
        "error": None,
        "correlation_id": correlation_id
    }


@router.get("")
async def list_jobs(
    request: Request,
    status: Optional[JobStatus] = Query(None, description="Filter by job status"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(10, ge=1, le=100, description="Items per page"),
    user_id: str = Depends(get_current_user)
):
    """
    List jobs with pagination and filtering.
    
    Query Parameters:
    - status: Filter by job status (PENDING, RUNNING, COMPLETED, FAILED)
    - page: Page number (default: 1)
    - page_size: Items per page (default: 10, max: 100)
    """
    correlation_id = getattr(request.state, 'correlation_id', 'unknown')
    
    jobs, total = await job_service.list_jobs(
        user_id=user_id,
        status=status,
        page=page,
        page_size=page_size
    )
    
    total_pages = math.ceil(total / page_size) if total > 0 else 0
    
    # Return in canonical ApiResponse format
    return {
        "success": True,
        "data": jobs,
        "error": None,
        "correlation_id": correlation_id
    }


@router.get("/{job_id}/status")
async def get_job_status(
    request: Request,
    job_id: str,
    user_id: str = Depends(get_current_user)
):
    """
    Get lightweight job status for polling.
    
    Returns minimal status information for efficient real-time updates.
    Use this endpoint instead of GET /api/jobs/{job_id} for polling.
    """
    from datetime import datetime
    correlation_id = getattr(request.state, 'correlation_id', 'unknown')
    status_data = await job_service.get_job_status(job_id, user_id)
    
    return {
        "success": True,
        "data": status_data,
        "error": None,
        "correlation_id": correlation_id
    }


@router.get("/{job_id}/results")
async def get_job_results(
    request: Request,
    job_id: str,
    user_id: str = Depends(get_current_user)
):
    """
    Get cost estimation results for completed job.
    
    Returns 400 if job is not in COMPLETED status.
    Proxies request to results-governance-service.
    """
    from datetime import datetime
    correlation_id = getattr(request.state, 'correlation_id', 'unknown')
    
    # Verify job exists and belongs to user
    job = await job_service.get_job(job_id, user_id)
    
    # Check if job is completed
    if job.status != JobStatus.COMPLETED:
        from fastapi import HTTPException
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Job is not completed (current status: {job.status.value})"
        )
    
    # Fetch results from results service
    results = await job_service.get_job_results(job_id)
    
    return {
        "success": True,
        "data": results,
        "error": None,
        "correlation_id": correlation_id
    }


@router.delete("/{job_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_job(
    job_id: str,
    user_id: str = Depends(get_current_user)
):
    """Delete a job."""
    await job_service.delete_job(job_id, user_id)
    return None
