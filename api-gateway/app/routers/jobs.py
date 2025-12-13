"""Job management endpoints."""

from typing import Optional
from fastapi import APIRouter, HTTPException, status, Depends, Query

from ..models.requests import CreateJobRequest
from ..models.responses import JobResponse, JobListResponse, ErrorResponse
from ..models.domain import JobStatus
from ..services.job_service import get_job_service
from ..services.orchestrator import get_orchestrator
from ..middleware.rate_limit import rate_limit_middleware
from ..middleware.auth import get_current_user
from ..utils.logger import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/api/v1/jobs", tags=["Jobs"])


@router.post(
    "",
    response_model=JobResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create cost estimation job",
    description="Create a new job to estimate costs for uploaded Terraform files",
    responses={
        400: {"model": ErrorResponse, "description": "Invalid request"},
        404: {"model": ErrorResponse, "description": "Upload not found"},
        429: {"model": ErrorResponse, "description": "Rate limit exceeded"},
    }
)
async def create_job(
    request: CreateJobRequest,
    _rate_limit: None = Depends(rate_limit_middleware),
    _current_user: dict = Depends(get_current_user),
) -> JobResponse:
    """Create a new cost estimation job.
    
    The job will be queued for processing by the Terraform Execution Engine.
    Use the job_id to track the status and retrieve results.
    
    Supports idempotency via the optional idempotency_key field.
    """
    job_service = get_job_service()
    orchestrator = get_orchestrator()
    
    try:
        # Create job
        job = job_service.create_job(request)
        
        # Submit to executor (async, don't wait for completion)
        try:
            await orchestrator.submit_job_to_executor(job)
            # Update status to RUNNING
            job = job_service.update_job_status(job.job_id, JobStatus.RUNNING)
        except Exception as e:
            logger.error("Failed to submit job to executor", job_id=job.job_id, error=str(e))
            # Update status to FAILED
            job = job_service.update_job_status(
                job.job_id,
                JobStatus.FAILED,
                error_message=f"Failed to submit job: {str(e)}"
            )
        
        return JobResponse(
            job_id=job.job_id,
            upload_id=job.upload_id,
            status=job.status,
            region=job.region,
            created_at=job.created_at,
            updated_at=job.updated_at,
            error_message=job.error_message,
            result_data=job.result_data
        )
        
    except ValueError as e:
        logger.warning("Job creation failed", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error("Job creation failed", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create job"
        )


@router.get(
    "/{job_id}",
    response_model=JobResponse,
    status_code=status.HTTP_200_OK,
    summary="Get job status",
    description="Retrieve the status and details of a cost estimation job",
    responses={
        404: {"model": ErrorResponse, "description": "Job not found"},
    }
)
async def get_job(
    job_id: str,
    _current_user: dict = Depends(get_current_user),
) -> JobResponse:
    """Get job status and details.
    
    Returns the current status of the job along with any results or error messages.
    """
    job_service = get_job_service()
    
    job = job_service.get_job(job_id)
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Job {job_id} not found"
        )
    
    return JobResponse(
        job_id=job.job_id,
        upload_id=job.upload_id,
        status=job.status,
        region=job.region,
        created_at=job.created_at,
        updated_at=job.updated_at,
        error_message=job.error_message,
        result_data=job.result_data
    )


@router.get(
    "",
    response_model=JobListResponse,
    status_code=status.HTTP_200_OK,
    summary="List jobs",
    description="List all cost estimation jobs with pagination",
)
async def list_jobs(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(10, ge=1, le=100, description="Items per page"),
    _current_user: dict = Depends(get_current_user),
) -> JobListResponse:
    """List all jobs with pagination.
    
    Returns a paginated list of jobs sorted by creation time (newest first).
    """
    job_service = get_job_service()
    
    jobs, total = job_service.list_jobs(page=page, page_size=page_size)
    
    job_responses = [
        JobResponse(
            job_id=job.job_id,
            upload_id=job.upload_id,
            status=job.status,
            region=job.region,
            created_at=job.created_at,
            updated_at=job.updated_at,
            error_message=job.error_message,
            result_data=job.result_data
        )
        for job in jobs
    ]
    
    return JobListResponse(
        jobs=job_responses,
        total=total,
        page=page,
        page_size=page_size
    )


@router.delete(
    "/{job_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete job",
    description="Cancel and delete a cost estimation job",
    responses={
        404: {"model": ErrorResponse, "description": "Job not found"},
    }
)
async def delete_job(
    job_id: str,
    _current_user: dict = Depends(get_current_user),
):
    """Delete a job.
    
    Cancels the job if it's running and removes it from the system.
    """
    job_service = get_job_service()
    
    deleted = job_service.delete_job(job_id)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Job {job_id} not found"
        )
    
    return None
