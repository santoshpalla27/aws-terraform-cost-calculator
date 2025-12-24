"""
Job service with database persistence.
Simplified implementation using dependency injection.
"""
import uuid
import httpx
from typing import List, Optional
from fastapi import HTTPException, status, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.config import settings
from app.models.domain import Job, JobStatus
from app.models.requests import CreateJobRequest
from app.repositories.job_repo import JobRepository
from app.repositories.upload_repo import upload_repository
from app.database.connection import get_db
from app.utils.logger import get_logger

logger = get_logger(__name__)


async def create_job(
    request: CreateJobRequest,
    user_id: str,
    db: AsyncSession = Depends(get_db)
) -> Job:
    """
    Create a new cost estimation job.
    
    Args:
        request: Job creation request
        user_id: User identifier
        db: Database session
        
    Returns:
        Created job
    """
    job_repo = JobRepository(db)
    
    # Verify upload exists
    upload = await upload_repository.get_by_id(request.upload_id)
    if not upload:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Upload {request.upload_id} not found"
        )
    
    # Verify user owns the upload
    if upload.user_id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to create a job for this upload"
        )
    
    # Create job
    job_id = str(uuid.uuid4())
    job = Job(
        job_id=job_id,
        upload_id=request.upload_id,
        user_id=user_id,
        name=request.name,
        current_state=JobStatus.CREATED
    )
    
    await job_repo.create(job)
    
    logger.info(
        f"Job created: {job_id}",
        extra={'job_id': job_id, 'upload_id': request.upload_id}
    )
    
    # Trigger job orchestrator
    try:
        await _trigger_orchestrator(job)
    except Exception as e:
        logger.error(f"Failed to trigger orchestrator for job {job_id}: {e}")
        # Don't fail job creation if orchestrator trigger fails
    
    return job


async def _trigger_orchestrator(job: Job, correlation_id: str = None) -> None:
    """Trigger job orchestrator to start processing."""
    headers = {}
    
    if settings.service_auth_token:
        headers["Authorization"] = f"Bearer {settings.service_auth_token}"
    
    if correlation_id:
        headers["X-Correlation-ID"] = correlation_id
    
    async with httpx.AsyncClient(timeout=10.0) as client:
        response = await client.post(
            f"{settings.job_orchestrator_url}/internal/jobs/{job.job_id}/start",
            headers=headers
        )
        response.raise_for_status()


async def get_job(
    job_id: str,
    user_id: str,
    db: AsyncSession = Depends(get_db)
) -> Job:
    """Get job by ID."""
    job_repo = JobRepository(db)
    job = await job_repo.get_by_id(job_id)
    
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Job {job_id} not found"
        )
    
    if job.user_id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to access this job"
        )
    
    return job


async def list_jobs(
    user_id: str,
    status: Optional[JobStatus] = None,
    page: int = 1,
    page_size: int = 10,
    db: AsyncSession = Depends(get_db)
) -> tuple[List[Job], int]:
    """List jobs for a user."""
    job_repo = JobRepository(db)
    return await job_repo.list_jobs(
        user_id=user_id,
        status=status,
        page=page,
        page_size=page_size
    )


async def delete_job(
    job_id: str,
    user_id: str,
    db: AsyncSession = Depends(get_db)
) -> bool:
    """Delete a job."""
    # Verify job exists and user owns it
    job = await get_job(job_id, user_id, db)
    
    job_repo = JobRepository(db)
    deleted = await job_repo.delete(job_id)
    
    if deleted:
        logger.info(f"Job deleted: {job_id}", extra={'job_id': job_id})
    
    return deleted
