"""
Job repository for PostgreSQL persistence.
"""
from typing import Optional, List
from datetime import datetime
from sqlalchemy import select, update, and_
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.job import Job
from app.models.stage import StageExecution, StageStatus
from app.state_machine.states import JobState
from app.utils.logger import get_logger

logger = get_logger(__name__)


class JobRepository:
    """Repository for job persistence."""
    
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def create(self, job: Job) -> Job:
        """
        Create a new job.
        
        Args:
            job: Job to create
            
        Returns:
            Created job
        """
        # Execute raw SQL insert
        query = """
            INSERT INTO jobs (
                job_id, upload_id, user_id, name, current_state,
                created_at, updated_at, metadata
            ) VALUES (
                :job_id, :upload_id, :user_id, :name, :current_state,
                :created_at, :updated_at, :metadata::jsonb
            )
        """
        
        await self.session.execute(
            query,
            {
                "job_id": job.job_id,
                "upload_id": job.upload_id,
                "user_id": job.user_id,
                "name": job.name,
                "current_state": job.current_state.value,
                "created_at": job.created_at,
                "updated_at": job.updated_at,
                "metadata": job.metadata or {}
            }
        )
        await self.session.commit()
        
        logger.info(f"Created job {job.job_id}", extra={'job_id': job.job_id})
        return job
    
    async def get(self, job_id: str) -> Optional[Job]:
        """
        Get job by ID.
        
        Args:
            job_id: Job identifier
            
        Returns:
            Job or None if not found
        """
        query = "SELECT * FROM jobs WHERE job_id = :job_id"
        result = await self.session.execute(query, {"job_id": job_id})
        row = result.fetchone()
        
        if not row:
            return None
        
        return Job(
            job_id=row.job_id,
            upload_id=row.upload_id,
            user_id=row.user_id,
            name=row.name,
            current_state=JobState(row.current_state),
            previous_state=JobState(row.previous_state) if row.previous_state else None,
            created_at=row.created_at,
            updated_at=row.updated_at,
            started_at=row.started_at,
            completed_at=row.completed_at,
            retry_count=row.retry_count,
            error_message=row.error_message,
            plan_reference=row.plan_reference,
            result_reference=row.result_reference,
            metadata=row.metadata or {}
        )
    
    async def update_state(
        self,
        job_id: str,
        new_state: JobState,
        error_message: Optional[str] = None
    ) -> None:
        """
        Update job state.
        
        Args:
            job_id: Job identifier
            new_state: New state
            error_message: Error message if transitioning to FAILED
        """
        # Get current state for logging
        job = await self.get(job_id)
        if not job:
            raise ValueError(f"Job {job_id} not found")
        
        # Build update query
        updates = {
            "current_state": new_state.value,
            "previous_state": job.current_state.value,
            "updated_at": datetime.utcnow()
        }
        
        if new_state == JobState.PLANNING and not job.started_at:
            updates["started_at"] = datetime.utcnow()
        
        if JobState.is_terminal(new_state):
            updates["completed_at"] = datetime.utcnow()
        
        if error_message:
            updates["error_message"] = error_message
        
        # Execute update
        query = """
            UPDATE jobs SET
                current_state = :current_state,
                previous_state = :previous_state,
                updated_at = :updated_at
        """
        
        if "started_at" in updates:
            query += ", started_at = :started_at"
        if "completed_at" in updates:
            query += ", completed_at = :completed_at"
        if "error_message" in updates:
            query += ", error_message = :error_message"
        
        query += " WHERE job_id = :job_id"
        updates["job_id"] = job_id
        
        await self.session.execute(query, updates)
        await self.session.commit()
        
        logger.info(
            f"Updated job {job_id} state: {job.current_state} → {new_state}",
            extra={'job_id': job_id, 'from_state': job.current_state.value, 'to_state': new_state.value}
        )
    
    async def increment_retry_count(self, job_id: str) -> None:
        """Increment retry count for a job."""
        query = """
            UPDATE jobs SET
                retry_count = retry_count + 1,
                updated_at = :updated_at
            WHERE job_id = :job_id
        """
        
        await self.session.execute(
            query,
            {"job_id": job_id, "updated_at": datetime.utcnow()}
        )
        await self.session.commit()
    
    async def set_plan_reference(self, job_id: str, plan_reference: str) -> None:
        """Set plan reference for a job."""
        query = """
            UPDATE jobs SET
                plan_reference = :plan_reference,
                updated_at = :updated_at
            WHERE job_id = :job_id
        """
        
        await self.session.execute(
            query,
            {
                "job_id": job_id,
                "plan_reference": plan_reference,
                "updated_at": datetime.utcnow()
            }
        )
        await self.session.commit()
    
    async def set_result_reference(self, job_id: str, result_reference: str) -> None:
        """Set result reference for a job."""
        query = """
            UPDATE jobs SET
                result_reference = :result_reference,
                updated_at = :updated_at
            WHERE job_id = :job_id
        """
        
        await self.session.execute(
            query,
            {
                "job_id": job_id,
                "result_reference": result_reference,
                "updated_at": datetime.utcnow()
            }
        )
        await self.session.commit()
    
    async def create_stage_execution(self, execution: StageExecution) -> StageExecution:
        """Create a stage execution record."""
        query = """
            INSERT INTO stage_executions (
                job_id, stage_name, attempt_number, started_at,
                status, input_data, output_data
            ) VALUES (
                :job_id, :stage_name, :attempt_number, :started_at,
                :status, :input_data::jsonb, :output_data::jsonb
            )
            RETURNING id
        """
        
        result = await self.session.execute(
            query,
            {
                "job_id": execution.job_id,
                "stage_name": execution.stage_name,
                "attempt_number": execution.attempt_number,
                "started_at": execution.started_at,
                "status": execution.status.value,
                "input_data": execution.input_data,
                "output_data": execution.output_data
            }
        )
        
        row = result.fetchone()
        execution.id = row.id
        
        await self.session.commit()
        return execution
    
    async def update_stage_execution(
        self,
        execution_id: int,
        status: StageStatus,
        duration_ms: Optional[int] = None,
        error_message: Optional[str] = None,
        output_data: Optional[dict] = None
    ) -> None:
        """Update a stage execution record."""
        updates = {
            "status": status.value,
            "completed_at": datetime.utcnow()
        }
        
        if duration_ms is not None:
            updates["duration_ms"] = duration_ms
        if error_message:
            updates["error_message"] = error_message
        if output_data:
            updates["output_data"] = output_data
        
        query = """
            UPDATE stage_executions SET
                status = :status,
                completed_at = :completed_at
        """
        
        if "duration_ms" in updates:
            query += ", duration_ms = :duration_ms"
        if "error_message" in updates:
            query += ", error_message = :error_message"
        if "output_data" in updates:
            query += ", output_data = :output_data::jsonb"
        
        query += " WHERE id = :id"
        updates["id"] = execution_id
        
        await self.session.execute(query, updates)
        await self.session.commit()
