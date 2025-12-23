"""
Planning stage executor.
Calls Terraform Execution Service to generate plan.json.
Uses async execution contract with polling.
"""
from typing import Dict, Any
import httpx
import asyncio
from app.stages.base import BaseStageExecutor
from app.models.job import Job
from app.config import settings
from app.utils.logger import get_logger

logger = get_logger(__name__)


class PlanningStageExecutor(BaseStageExecutor):
    """Planning stage - execute Terraform plan asynchronously."""
    
    def __init__(self):
        super().__init__("PLANNING")
        self.terraform_url = settings.terraform_executor_url
        self.poll_interval = 2  # seconds
        self.max_poll_attempts = settings.planning_timeout // self.poll_interval
    
    async def validate_input(self, job: Job) -> None:
        """Validate that upload_id exists."""
        if not job.upload_id:
            raise ValueError("Missing upload_id")
    
    async def execute(self, job: Job) -> Dict[str, Any]:
        """
        Execute Terraform plan asynchronously with polling.
        
        Returns:
            Dict with plan_reference
        """
        logger.info(f"Executing planning stage for job {job.job_id}")
        
        # Step 1: Submit execution request
        execution_id = await self._submit_execution(job)
        logger.info(f"Terraform execution submitted: {execution_id}")
        
        # Step 2: Poll for completion
        result = await self._poll_execution(execution_id, job.job_id)
        
        return result
    
    async def _submit_execution(self, job: Job) -> str:
        """Submit Terraform execution and get execution_id."""
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                f"{self.terraform_url}/internal/terraform/execute",
                json={
                    "job_id": job.job_id,
                    "terraform_source": f"upload://{job.upload_id}",  # Reference to uploaded files
                    "variables": job.metadata.get("terraform_variables", {}) if job.metadata else {}
                },
                headers={"Authorization": f"Bearer {settings.service_auth_token}"}
            )
            response.raise_for_status()
            data = response.json()
            return data["execution_id"]
    
    async def _poll_execution(self, execution_id: str, job_id: str) -> Dict[str, Any]:
        """
        Poll execution status until completion or timeout.
        
        Returns:
            Execution result with plan_json
        """
        async with httpx.AsyncClient(timeout=10.0) as client:
            for attempt in range(self.max_poll_attempts):
                # Check status
                status_response = await client.get(
                    f"{self.terraform_url}/internal/terraform/status/{execution_id}",
                    headers={"Authorization": f"Bearer {settings.service_auth_token}"}
                )
                status_response.raise_for_status()
                status_data = status_response.json()
                
                status = status_data["status"]
                logger.debug(f"Execution {execution_id} status: {status} (attempt {attempt + 1}/{self.max_poll_attempts})")
                
                if status == "COMPLETED":
                    # Fetch result
                    result_response = await client.get(
                        f"{self.terraform_url}/internal/terraform/result/{execution_id}",
                        headers={"Authorization": f"Bearer {settings.service_auth_token}"}
                    )
                    result_response.raise_for_status()
                    result_data = result_response.json()
                    
                    return {
                        "plan_reference": f"execution:{execution_id}",
                        "plan_json": result_data.get("plan_json"),
                        "execution_id": execution_id
                    }
                
                elif status == "FAILED":
                    error_msg = status_data.get("error_message", "Unknown error")
                    raise RuntimeError(f"Terraform execution failed: {error_msg}")
                
                elif status in ["TIMEOUT", "KILLED"]:
                    raise RuntimeError(f"Terraform execution {status.lower()}")
                
                # Still running, wait before next poll
                await asyncio.sleep(self.poll_interval)
            
            # Timeout reached - kill execution
            logger.error(f"Execution {execution_id} timed out after {settings.planning_timeout}s")
            try:
                await client.delete(
                    f"{self.terraform_url}/internal/terraform/execution/{execution_id}",
                    headers={"Authorization": f"Bearer {settings.service_auth_token}"}
                )
            except Exception as e:
                logger.warning(f"Failed to kill execution {execution_id}: {e}")
            
            raise TimeoutError(f"Terraform execution timed out after {settings.planning_timeout}s")
    
    async def validate_output(self, result: Dict[str, Any]) -> None:
        """Validate plan output."""
        if "plan_reference" not in result:
            raise ValueError("Missing plan_reference in result")
