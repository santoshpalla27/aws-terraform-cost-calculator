"""
Job repository.
In-memory storage (database-ready architecture).
"""
from typing import Dict, List, Optional
from datetime import datetime
from app.models.domain import Job, JobStatus


class JobRepository:
    """Repository for job persistence."""
    
    def __init__(self):
        # In-memory storage (replace with database in production)
        self._jobs: Dict[str, Job] = {}
    
    async def create(self, job: Job) -> Job:
        """
        Create a new job record.
        
        Args:
            job: Job object to store
            
        Returns:
            Created job
        """
        self._jobs[job.job_id] = job
        return job
    
    async def get_by_id(self, job_id: str) -> Optional[Job]:
        """
        Get job by ID.
        
        Args:
            job_id: Job identifier
            
        Returns:
            Job object or None if not found
        """
        return self._jobs.get(job_id)
    
    async def list_jobs(
        self,
        user_id: Optional[str] = None,
        status: Optional[JobStatus] = None,
        page: int = 1,
        page_size: int = 10
    ) -> tuple[List[Job], int]:
        """
        List jobs with filtering and pagination.
        
        Args:
            user_id: Filter by user ID
            status: Filter by job status
            page: Page number (1-indexed)
            page_size: Items per page
            
        Returns:
            Tuple of (jobs_list, total_count)
        """
        # Filter jobs
        jobs = list(self._jobs.values())
        
        if user_id:
            jobs = [j for j in jobs if j.user_id == user_id]
        
        if status:
            jobs = [j for j in jobs if j.status == status]
        
        # Sort by created_at descending
        jobs.sort(key=lambda x: x.created_at, reverse=True)
        
        total = len(jobs)
        
        # Paginate
        start = (page - 1) * page_size
        end = start + page_size
        paginated_jobs = jobs[start:end]
        
        return paginated_jobs, total
    
    async def update_status(
        self,
        job_id: str,
        status: JobStatus,
        error_message: Optional[str] = None
    ) -> Optional[Job]:
        """
        Update job status.
        
        Args:
            job_id: Job identifier
            status: New status
            error_message: Error message if failed
            
        Returns:
            Updated job or None if not found
        """
        job = self._jobs.get(job_id)
        if not job:
            return None
        
        job.status = status
        job.updated_at = datetime.utcnow()
        
        if status == JobStatus.COMPLETED or status == JobStatus.FAILED:
            job.completed_at = datetime.utcnow()
        
        if error_message:
            job.error_message = error_message
        
        return job
    
    async def delete(self, job_id: str) -> bool:
        """
        Delete a job.
        
        Args:
            job_id: Job identifier
            
        Returns:
            True if deleted, False if not found
        """
        if job_id in self._jobs:
            del self._jobs[job_id]
            return True
        return False


# Global repository instance
job_repository = JobRepository()
