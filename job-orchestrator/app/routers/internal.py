"""
Internal API endpoints for job orchestration.
NO public APIs - internal network only.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.database.connection import get_db
from app.repositories.job_repo import JobRepository
from app.models.job import JobStateResponse
from app.state_machine.states import JobState
from app.utils.logger import get_logger, set_job_id

logger = get_logger(__name__)
router = APIRouter(prefix="/internal/jobs", tags=["internal"])


@router.post("/{job_id}/start", status_code=status.HTTP_202_ACCEPTED)
async def start_job(
    job_id: str,
    db: AsyncSession = Depends(get_db)
):
    """
    Start job execution.
    Accepts jobs in PENDING state (from API Gateway) or UPLOADED state.
    Transitions to PLANNING.
    """
    set_job_id(job_id)
    
    repo = JobRepository(db)
    job = await repo.get(job_id)
    
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Job {job_id} not found"
        )
    
    # Accept both PENDING (from API Gateway) and UPLOADED states
    # PENDING is the initial state when job is created by API Gateway
    # We treat PENDING as equivalent to UPLOADED for orchestration purposes
    valid_states = [JobState.UPLOADED]
    
    # Check if job is in a state name that matches "PENDING" (from API Gateway)
    # The job might have been created with a different state enum
    if job.current_state.value == "PENDING":
        # Treat PENDING as UPLOADED - this is the initial state from API Gateway
        logger.info(f"Job {job_id} in PENDING state, treating as UPLOADED")
    elif job.current_state not in valid_states:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Job must be in PENDING or UPLOADED state, currently {job.current_state}"
        )
    
    # Transition to PLANNING
    await repo.update_state(job_id, JobState.PLANNING)
    
    logger.info(f"Started job {job_id}")
    
    # TODO: Trigger async orchestration
    # await orchestrator.execute_job(job_id)
    
    return {"message": "Job started", "job_id": job_id}


@router.post("/{job_id}/fail")
async def fail_job(
    job_id: str,
    error_message: str,
    db: AsyncSession = Depends(get_db)
):
    """Transition job to FAILED state."""
    set_job_id(job_id)
    
    repo = JobRepository(db)
    job = await repo.get(job_id)
    
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Job {job_id} not found"
        )
    
    await repo.update_state(job_id, JobState.FAILED, error_message)
    
    logger.error(f"Job {job_id} failed: {error_message}")
    
    return {"message": "Job marked as failed", "job_id": job_id}


@router.get("/{job_id}/state", response_model=JobStateResponse)
async def get_job_state(
    job_id: str,
    db: AsyncSession = Depends(get_db)
):
    """Get current job state."""
    repo = JobRepository(db)
    job = await repo.get(job_id)
    
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Job {job_id} not found"
        )
    
    return JobStateResponse(
        job_id=job.job_id,
        current_state=job.current_state,
        previous_state=job.previous_state,
        created_at=job.created_at,
        updated_at=job.updated_at,
        error_message=job.error_message
    )
