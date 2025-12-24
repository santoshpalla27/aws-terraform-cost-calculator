"""
Job repository with PostgreSQL persistence.
"""
from typing import List, Optional
from datetime import datetime
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.domain import Job, JobStatus
from app.utils.logger import get_logger

logger = get_logger(__name__)


class JobRepository:
    """Repository for job persistence using PostgreSQL."""
    
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def create(self, job: Job) -> Job:
        """
        Create a new job record in database.
        
        Args:
            job: Job object to store
            
        Returns:
            Created job
        """
        query = text("""
            INSERT INTO jobs (
                job_id, upload_id, user_id, name, current_state,
                created_at, updated_at
            ) VALUES (
                :job_id, :upload_id, :user_id, :name, :current_state,
                :created_at, :updated_at
            )
        """)
        
        await self.session.execute(
            query,
            {
                "job_id": job.job_id,
                "upload_id": job.upload_id,
                "user_id": job.user_id,
                "name": job.name,
                "current_state": job.current_state.value,
                "created_at": job.created_at,
                "updated_at": job.updated_at
            }
        )
        await self.session.commit()
        
        logger.info(f"Created job {job.job_id} in database")
        return job
    
    async def get_by_id(self, job_id: str) -> Optional[Job]:
        """
        Get job by ID from database.
        
        Args:
            job_id: Job identifier
            
        Returns:
            Job object or None if not found
        """
        query = text("SELECT * FROM jobs WHERE job_id = :job_id")
        result = await self.session.execute(query, {"job_id": job_id})
        row = result.fetchone()
        
        if not row:
            return None
        
        return Job(
            job_id=row.job_id,
            upload_id=row.upload_id,
            user_id=row.user_id,
            name=row.name,
            current_state=JobStatus(row.current_state),
            progress=0,
            created_at=row.created_at,
            updated_at=row.updated_at,
            completed_at=row.completed_at,
            error_message=row.error_message
        )
    
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
        # Build query
        where_clauses = []
        params = {}
        
        if user_id:
            where_clauses.append("user_id = :user_id")
            params["user_id"] = user_id
        
        if status:
            where_clauses.append("current_state = :status")
            params["status"] = status.value
        
        where_sql = " WHERE " + " AND ".join(where_clauses) if where_clauses else ""
        
        # Get total count
        count_query = text(f"SELECT COUNT(*) FROM jobs{where_sql}")
        count_result = await self.session.execute(count_query, params)
        total = count_result.scalar()
        
        # Get paginated jobs
        offset = (page - 1) * page_size
        params["limit"] = page_size
        params["offset"] = offset
        
        jobs_query = text(f"""
            SELECT * FROM jobs{where_sql}
            ORDER BY created_at DESC
            LIMIT :limit OFFSET :offset
        """)
        
        result = await self.session.execute(jobs_query, params)
        rows = result.fetchall()
        
        jobs = [
            Job(
                job_id=row.job_id,
                upload_id=row.upload_id,
                user_id=row.user_id,
                name=row.name,
                current_state=JobStatus(row.current_state),
                progress=0,
                created_at=row.created_at,
                updated_at=row.updated_at,
                completed_at=row.completed_at,
                error_message=row.error_message
            )
            for row in rows
        ]
        
        return jobs, total
    
    async def update_status(
        self,
        job_id: str,
        status: JobStatus,
        error_message: Optional[str] = None
    ) -> Optional[Job]:
        """
        Update job status in database.
        
        Args:
            job_id: Job identifier
            status: New status
            error_message: Error message if failed
            
        Returns:
            Updated job or None if not found
        """
        updates = {
            "current_state": status.value,
            "updated_at": datetime.utcnow(),
            "job_id": job_id
        }
        
        query_str = """
            UPDATE jobs SET
                current_state = :current_state,
                updated_at = :updated_at
        """
        
        if status in [JobStatus.COMPLETED, JobStatus.FAILED]:
            query_str += ", completed_at = :completed_at"
            updates["completed_at"] = datetime.utcnow()
        
        if error_message:
            query_str += ", error_message = :error_message"
            updates["error_message"] = error_message
        
        query_str += " WHERE job_id = :job_id"
        
        await self.session.execute(text(query_str), updates)
        await self.session.commit()
        
        return await self.get_by_id(job_id)
    
    async def delete(self, job_id: str) -> bool:
        """
        Delete a job from database.
        
        Args:
            job_id: Job identifier
            
        Returns:
            True if deleted, False if not found
        """
        query = text("DELETE FROM jobs WHERE job_id = :job_id")
        result = await self.session.execute(query, {"job_id": job_id})
        await self.session.commit()
        
        return result.rowcount > 0

