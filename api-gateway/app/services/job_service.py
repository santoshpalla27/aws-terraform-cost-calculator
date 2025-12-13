"""Job service for orchestrating cost estimation jobs."""

import uuid
from typing import List, Optional
from datetime import datetime

from ..models.domain import Job, JobStatus
from ..models.requests import CreateJobRequest
from ..repositories.job_repository import get_job_repository
from ..utils.logger import get_logger

logger = get_logger(__name__)


class JobService:
    """Service for managing cost estimation jobs."""
    
    def __init__(self):
        """Initialize job service."""
        self.repository = get_job_repository()
        logger.info("Initialized job service")
    
    def create_job(self, request: CreateJobRequest) -> Job:
        """Create a new cost estimation job.
        
        Args:
            request: Job creation request
            
        Returns:
            Created job
        """
        # Generate unique job ID
        job_id = f"job_{uuid.uuid4().hex[:12]}"
        
        # Create job
        job = Job(
            job_id=job_id,
            upload_id=request.upload_id,
            region=request.region,
            status=JobStatus.PENDING,
            idempotency_key=request.idempotency_key,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        
        # Save to repository (handles idempotency)
        created_job = self.repository.create(job)
        
        logger.info(
            "Created job",
            job_id=created_job.job_id,
            upload_id=request.upload_id,
            region=request.region,
            is_duplicate=created_job.job_id != job_id
        )
        
        return created_job
    
    def get_job(self, job_id: str) -> Optional[Job]:
        """Get job by ID.
        
        Args:
            job_id: Job identifier
            
        Returns:
            Job if found, None otherwise
        """
        return self.repository.get(job_id)
    
    def update_job_status(
        self,
        job_id: str,
        status: JobStatus,
        error_message: Optional[str] = None,
        result_data: Optional[dict] = None
    ) -> Job:
        """Update job status.
        
        Args:
            job_id: Job identifier
            status: New status
            error_message: Optional error message
            result_data: Optional result data
            
        Returns:
            Updated job
            
        Raises:
            ValueError: If job not found
        """
        job = self.repository.get(job_id)
        if not job:
            raise ValueError(f"Job {job_id} not found")
        
        job.status = status
        if error_message:
            job.error_message = error_message
        if result_data:
            job.result_data = result_data
        
        updated_job = self.repository.update(job)
        
        logger.info(
            "Updated job status",
            job_id=job_id,
            status=status,
            has_error=error_message is not None
        )
        
        return updated_job
    
    def list_jobs(self, page: int = 1, page_size: int = 10) -> tuple[List[Job], int]:
        """List jobs with pagination.
        
        Args:
            page: Page number (1-indexed)
            page_size: Number of items per page
            
        Returns:
            Tuple of (jobs, total_count)
        """
        skip = (page - 1) * page_size
        jobs = self.repository.list(skip=skip, limit=page_size)
        total = self.repository.count()
        
        logger.info("Listed jobs", page=page, page_size=page_size, total=total)
        
        return jobs, total
    
    def delete_job(self, job_id: str) -> bool:
        """Delete job.
        
        Args:
            job_id: Job identifier
            
        Returns:
            True if deleted, False if not found
        """
        deleted = self.repository.delete(job_id)
        
        if deleted:
            logger.info("Deleted job", job_id=job_id)
        else:
            logger.warning("Job not found for deletion", job_id=job_id)
        
        return deleted


# Global service instance
_job_service: JobService | None = None


def get_job_service() -> JobService:
    """Get the global job service instance.
    
    Returns:
        JobService instance
    """
    global _job_service
    if _job_service is None:
        _job_service = JobService()
    return _job_service
