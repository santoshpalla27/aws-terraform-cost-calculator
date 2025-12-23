"""
Job service.
Handles job creation and orchestration initiation.
"""
import uuid
import httpx
from typing import List, Optional
from fastapi import HTTPException, status
from app.config import settings
from app.models.domain import Job, JobStatus
from app.models.requests import CreateJobRequest
from app.repositories.job_repo import job_repository
from app.repositories.upload_repo import upload_repository
from app.utils.logger import get_logger

logger = get_logger(__name__)


class JobService:
    """Service for job management."""
    
    async def create_job(
        self,
        request: CreateJobRequest,
        user_id: str
    ) -> Job:
        """
        Create a new cost estimation job.
        
        Args:
            request: Job creation request
            user_id: User identifier
            
        Returns:
            Created job
            
        Raises:
            HTTPException: If validation fails
        """
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
            status=JobStatus.PENDING
        )
        
        await job_repository.create(job)
        
        logger.info(
            f"Job created: {job_id}",
            extra={'job_id': job_id, 'upload_id': request.upload_id}
        )
        
        # Trigger job orchestrator
        try:
            await self._trigger_orchestrator(job)
        except Exception as e:
            logger.error(f"Failed to trigger orchestrator for job {job_id}: {e}")
            # Don't fail job creation if orchestrator trigger fails
            # Job can be retried later
        
        return job
    
    async def _trigger_orchestrator(self, job: Job, correlation_id: str = None) -> None:
        """
        Trigger job orchestrator to start processing.
        
        Args:
            job: Job to start
            correlation_id: Optional correlation ID for tracing
        """
        headers = {}
        
        # Add auth header only if service_auth_token is configured
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
            logger.info(f"Triggered orchestrator for job {job.job_id}")
    
    async def get_job(self, job_id: str, user_id: str) -> Job:
        """
        Get job by ID.
        
        Args:
            job_id: Job identifier
            user_id: User identifier
            
        Returns:
            Job object
            
        Raises:
            HTTPException: If job not found or access denied
        """
        job = await job_repository.get_by_id(job_id)
        if not job:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Job {job_id} not found"
            )
        
        # Verify user owns the job
        if job.user_id != user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have permission to access this job"
            )
        
        return job
    
    async def list_jobs(
        self,
        user_id: str,
        status: Optional[JobStatus] = None,
        page: int = 1,
        page_size: int = 10
    ) -> tuple[List[Job], int]:
        """
        List jobs for a user.
        
        Args:
            user_id: User identifier
            status: Filter by status
            page: Page number
            page_size: Items per page
            
        Returns:
            Tuple of (jobs, total_count)
        """
        return await job_repository.list_jobs(
            user_id=user_id,
            status=status,
            page=page,
            page_size=page_size
        )
    
    async def delete_job(self, job_id: str, user_id: str) -> None:
        """
        Delete a job.
        
        Args:
            job_id: Job identifier
            user_id: User identifier
            
        Raises:
            HTTPException: If job not found or access denied
        """
        # Verify job exists and user owns it
        job = await self.get_job(job_id, user_id)
        
        # Delete job
        deleted = await job_repository.delete(job_id)
        if not deleted:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Job {job_id} not found"
            )
        
        logger.info(f"Job deleted: {job_id}")


# Global service instance
job_service = JobService()
