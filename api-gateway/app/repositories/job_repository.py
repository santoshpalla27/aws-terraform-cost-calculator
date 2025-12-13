"""Job repository for storage abstraction."""

from typing import Dict, List, Optional
from datetime import datetime
import threading

from ..models.domain import Job, JobStatus
from ..utils.logger import get_logger

logger = get_logger(__name__)


class JobRepository:
    """Abstract repository interface for job storage."""
    
    def create(self, job: Job) -> Job:
        """Create a new job."""
        raise NotImplementedError
    
    def get(self, job_id: str) -> Optional[Job]:
        """Get job by ID."""
        raise NotImplementedError
    
    def get_by_idempotency_key(self, key: str) -> Optional[Job]:
        """Get job by idempotency key."""
        raise NotImplementedError
    
    def update(self, job: Job) -> Job:
        """Update existing job."""
        raise NotImplementedError
    
    def list(self, skip: int = 0, limit: int = 10) -> List[Job]:
        """List jobs with pagination."""
        raise NotImplementedError
    
    def count(self) -> int:
        """Count total jobs."""
        raise NotImplementedError
    
    def delete(self, job_id: str) -> bool:
        """Delete job by ID."""
        raise NotImplementedError


class InMemoryJobRepository(JobRepository):
    """In-memory implementation for MVP (thread-safe)."""
    
    def __init__(self):
        """Initialize in-memory storage."""
        self._jobs: Dict[str, Job] = {}
        self._idempotency_index: Dict[str, str] = {}  # key -> job_id
        self._lock = threading.RLock()
        logger.info("Initialized in-memory job repository")
    
    def create(self, job: Job) -> Job:
        """Create a new job."""
        with self._lock:
            if job.job_id in self._jobs:
                raise ValueError(f"Job {job.job_id} already exists")
            
            # Check idempotency key
            if job.idempotency_key:
                if job.idempotency_key in self._idempotency_index:
                    existing_job_id = self._idempotency_index[job.idempotency_key]
                    logger.info(
                        "Idempotent job creation",
                        job_id=existing_job_id,
                        idempotency_key=job.idempotency_key
                    )
                    return self._jobs[existing_job_id]
                
                self._idempotency_index[job.idempotency_key] = job.job_id
            
            self._jobs[job.job_id] = job
            logger.info("Created job", job_id=job.job_id, upload_id=job.upload_id)
            return job
    
    def get(self, job_id: str) -> Optional[Job]:
        """Get job by ID."""
        with self._lock:
            return self._jobs.get(job_id)
    
    def get_by_idempotency_key(self, key: str) -> Optional[Job]:
        """Get job by idempotency key."""
        with self._lock:
            job_id = self._idempotency_index.get(key)
            if job_id:
                return self._jobs.get(job_id)
            return None
    
    def update(self, job: Job) -> Job:
        """Update existing job."""
        with self._lock:
            if job.job_id not in self._jobs:
                raise ValueError(f"Job {job.job_id} not found")
            
            job.updated_at = datetime.utcnow()
            self._jobs[job.job_id] = job
            logger.info("Updated job", job_id=job.job_id, status=job.status)
            return job
    
    def list(self, skip: int = 0, limit: int = 10) -> List[Job]:
        """List jobs with pagination."""
        with self._lock:
            jobs = list(self._jobs.values())
            # Sort by created_at descending
            jobs.sort(key=lambda x: x.created_at, reverse=True)
            return jobs[skip:skip + limit]
    
    def count(self) -> int:
        """Count total jobs."""
        with self._lock:
            return len(self._jobs)
    
    def delete(self, job_id: str) -> bool:
        """Delete job by ID."""
        with self._lock:
            if job_id in self._jobs:
                job = self._jobs[job_id]
                
                # Remove from idempotency index
                if job.idempotency_key and job.idempotency_key in self._idempotency_index:
                    del self._idempotency_index[job.idempotency_key]
                
                del self._jobs[job_id]
                logger.info("Deleted job", job_id=job_id)
                return True
            return False


# Global repository instance
_job_repository: Optional[JobRepository] = None


def get_job_repository() -> JobRepository:
    """Get the global job repository instance.
    
    Returns:
        JobRepository instance
    """
    global _job_repository
    if _job_repository is None:
        _job_repository = InMemoryJobRepository()
    return _job_repository
