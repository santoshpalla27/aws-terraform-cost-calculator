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
    
    # Accept CREATED (from API Gateway), PENDING, and UPLOADED states
    # CREATED is the initial state when job is created by API Gateway
    # We treat CREATED/PENDING as equivalent to UPLOADED for orchestration purposes
    valid_state_values = ["CREATED", "PENDING", "UPLOADED"]
    
    # Check if job is in a valid initial state
    if job.current_state.value not in valid_state_values:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Job must be in CREATED, PENDING, or UPLOADED state, currently {job.current_state.value}"
        )
    
    logger.info(f"Job {job_id} in {job.current_state.value} state, starting orchestration")
    
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
