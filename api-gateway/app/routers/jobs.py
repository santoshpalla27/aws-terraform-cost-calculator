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
    
    The job will be created in PENDING status and queued for processing.
    """
    correlation_id = getattr(request_obj.state, 'correlation_id', 'unknown')
    job = await job_service.create_job(request, user_id)
    
    return {
        "success": True,
        "data": {"job": job, "message": "Job created successfully"},
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
    correlation_id = getattr(request.state, 'correlation_id', 'unknown')
    job = await job_service.get_job(job_id, user_id)
    
    return {
        "success": True,
        "data": {"job": job, "message": "Job retrieved successfully"},
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
    
    # Return in standard ApiResponse format
    return {
        "success": True,
        "data": {
            "data": jobs,
            "total": total,
            "page": page,
            "page_size": page_size,
            "total_pages": total_pages
        },
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
