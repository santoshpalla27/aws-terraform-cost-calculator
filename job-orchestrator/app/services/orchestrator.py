"""
Job Orchestrator Service - Core Pipeline Execution Engine.

Executes jobs through the complete pipeline:
CREATED → PLANNING → PARSING → ENRICHING → COSTING → COMPLETED

CRITICAL: This is the heart of the platform. All stages must execute atomically.
"""
import asyncio
import httpx
from typing import Dict, Any, Optional
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.models.job import Job
from app.models.stage import StageExecution, StageStatus
from app.state_machine.states import JobState
from app.repositories.job_repo import JobRepository
from app.services.step_executor import step_executor
from app.services.lock_manager import lock_manager
from app.utils.logger import get_logger, set_job_id

logger = get_logger(__name__)


class JobOrchestrator:
    """
    Orchestrates job execution through all pipeline stages.
    
    Responsibilities:
    1. Execute stages in order: PLANNING → PARSING → ENRICHING → COSTING
    2. Update job state after each stage
    3. Handle errors and mark jobs as FAILED
    4. Track stage executions in database
    5. Propagate correlation_id through all stages
    """
    
    async def execute_job(self, job_id: str, db: AsyncSession) -> None:
        """
        Execute job through complete pipeline.
        
        This is the main entry point for job execution.
        Called as a background task from the /start endpoint.
        
        Args:
            job_id: Job identifier
            db: Database session
        """
        set_job_id(job_id)
        repo = JobRepository(db)
        
        try:
            # Get job
            job = await repo.get(job_id)
            if not job:
                logger.error(f"Job {job_id} not found")
                return
            
            logger.info(
                f"Starting orchestration for job {job_id}",
                extra={"job_id": job_id, "correlation_id": job.correlation_id}
            )
            
            # Acquire distributed lock
            async with lock_manager.acquire_lock(f"job:{job_id}"):
                # Execute pipeline stages
                await self._execute_pipeline(job, repo)
                
        except Exception as e:
            logger.error(
                f"Orchestration failed for job {job_id}: {str(e)}",
                extra={"job_id": job_id},
                exc_info=True
            )
            await repo.update_state(
                job_id,
                JobState.FAILED,
                error_message=f"Orchestration error: {str(e)}"
            )
    
    async def _execute_pipeline(self, job: Job, repo: JobRepository) -> None:
        """
        Execute all pipeline stages in sequence.
        
        Args:
            job: Job to execute
            repo: Job repository
        """
        try:
            # Stage 1: PLANNING (terraform plan)
            plan_data = await self._execute_stage(
                job=job,
                repo=repo,
                stage_name="PLANNING",
                next_state=JobState.PARSING,
                executor_func=lambda: self._call_terraform_executor(job)
            )
            
            if not plan_data:
                return  # Failed, already marked as FAILED
            
            # Stage 2: PARSING (parse terraform plan)
            parsed_data = await self._execute_stage(
                job=job,
                repo=repo,
                stage_name="PARSING",
                next_state=JobState.ENRICHING,
                executor_func=lambda: self._call_plan_interpreter(job, plan_data)
            )
            
            if not parsed_data:
                return
            
            # Stage 3: ENRICHING (resolve AWS metadata)
            enriched_data = await self._execute_stage(
                job=job,
                repo=repo,
                stage_name="ENRICHING",
                next_state=JobState.COSTING,
                executor_func=lambda: self._call_metadata_resolver(job, parsed_data)
            )
            
            if not enriched_data:
                return
            
            # Stage 4: COSTING (calculate costs)
            cost_data = await self._execute_stage(
                job=job,
                repo=repo,
                stage_name="COSTING",
                next_state=JobState.COMPLETED,
                executor_func=lambda: self._call_cost_engines(job, enriched_data)
            )
            
            if not cost_data:
                return
            
            # Mark job as completed
            await repo.update_state(job.job_id, JobState.COMPLETED)
            
            logger.info(
                f"Job {job.job_id} completed successfully",
                extra={"job_id": job.job_id, "correlation_id": job.correlation_id}
            )
            
        except Exception as e:
            logger.error(
                f"Pipeline execution failed: {str(e)}",
                extra={"job_id": job.job_id},
                exc_info=True
            )
            await repo.update_state(
                job.job_id,
                JobState.FAILED,
                error_message=str(e)
            )
    
    async def _execute_stage(
        self,
        job: Job,
        repo: JobRepository,
        stage_name: str,
        next_state: JobState,
        executor_func: callable
    ) -> Optional[Dict[str, Any]]:
        """
        Execute a single pipeline stage.
        
        Args:
            job: Job being executed
            repo: Job repository
            stage_name: Name of stage (PLANNING, PARSING, etc.)
            next_state: State to transition to on success
            executor_func: Function that executes the stage
            
        Returns:
            Stage output data, or None if failed
        """
        logger.info(
            f"Executing stage: {stage_name}",
            extra={"job_id": job.job_id, "stage": stage_name}
        )
        
        # Create stage execution record
        execution = StageExecution(
            job_id=job.job_id,
            stage_name=stage_name,
            attempt_number=1,
            started_at=datetime.utcnow(),
            status=StageStatus.RUNNING,
            input_data={},
            output_data={}
        )
        execution = await repo.create_stage_execution(execution)
        
        # Execute stage with timeout
        stage_config = settings.stage_config[stage_name]
        result = await step_executor.execute_step(
            step_name=stage_name.lower(),
            func=executor_func,
            job_id=job.job_id,
            correlation_id=job.correlation_id,
            timeout=stage_config["timeout"]
        )
        
        # Update stage execution
        if result.success:
            await repo.update_stage_execution(
                execution_id=execution.id,
                status=StageStatus.SUCCESS,
                duration_ms=int(result.execution_time * 1000),
                output_data=result.data
            )
            
            # Transition to next state
            await repo.update_state(job.job_id, next_state)
            
            logger.info(
                f"Stage {stage_name} completed successfully",
                extra={"job_id": job.job_id, "duration_ms": int(result.execution_time * 1000)}
            )
            
            return result.data
        else:
            await repo.update_stage_execution(
                execution_id=execution.id,
                status=StageStatus.FAILED,
                duration_ms=int(result.execution_time * 1000),
                error_message=result.error_message
            )
            
            # Mark job as failed
            await repo.update_state(
                job.job_id,
                JobState.FAILED,
                error_message=f"{stage_name} failed: {result.error_message}"
            )
            
            logger.error(
                f"Stage {stage_name} failed: {result.error_message}",
                extra={"job_id": job.job_id, "error_code": result.error_code}
            )
            
            return None
    
    async def _call_terraform_executor(self, job: Job) -> Dict[str, Any]:
        """
        Call terraform-executor to run terraform plan.
        
        Args:
            job: Job being executed
            
        Returns:
            Terraform plan output
        """
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{settings.terraform_executor_url}/execute",
                json={
                    "job_id": job.job_id,
                    "upload_id": job.upload_id,
                    "correlation_id": job.correlation_id
                },
                headers={"X-Correlation-ID": job.correlation_id},
                timeout=settings.planning_timeout
            )
            response.raise_for_status()
            return response.json()
    
    async def _call_plan_interpreter(self, job: Job, plan_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Call plan-interpreter to parse terraform plan.
        
        Args:
            job: Job being executed
            plan_data: Output from terraform executor
            
        Returns:
            Parsed resource list
        """
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{settings.plan_interpreter_url}/parse",
                json={
                    "job_id": job.job_id,
                    "plan_data": plan_data,
                    "correlation_id": job.correlation_id
                },
                headers={"X-Correlation-ID": job.correlation_id},
                timeout=settings.parsing_timeout
            )
            response.raise_for_status()
            return response.json()
    
    async def _call_metadata_resolver(self, job: Job, parsed_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Call metadata-resolver to enrich resources with AWS metadata.
        
        Args:
            job: Job being executed
            parsed_data: Output from plan interpreter
            
        Returns:
            Enriched resource list
        """
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{settings.metadata_resolver_url}/enrich",
                json={
                    "job_id": job.job_id,
                    "resources": parsed_data.get("resources", []),
                    "correlation_id": job.correlation_id
                },
                headers={"X-Correlation-ID": job.correlation_id},
                timeout=settings.enriching_timeout
            )
            response.raise_for_status()
            return response.json()
    
    async def _call_cost_engines(self, job: Job, enriched_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Call pricing/usage/cost engines to calculate costs.
        
        Args:
            job: Job being executed
            enriched_data: Output from metadata resolver
            
        Returns:
            Cost calculation results
        """
        # This is a simplified version - in reality, you'd call:
        # 1. pricing-engine to get base prices
        # 2. usage-engine to apply usage profiles
        # 3. cost-engine to aggregate final costs
        
        async with httpx.AsyncClient() as client:
            # Call cost engine (which internally calls pricing and usage engines)
            response = await client.post(
                f"{settings.cost_engine_url}/calculate",
                json={
                    "job_id": job.job_id,
                    "resources": enriched_data.get("resources", []),
                    "correlation_id": job.correlation_id
                },
                headers={"X-Correlation-ID": job.correlation_id},
                timeout=settings.costing_timeout
            )
            response.raise_for_status()
            return response.json()


# Singleton instance
job_orchestrator = JobOrchestrator()
