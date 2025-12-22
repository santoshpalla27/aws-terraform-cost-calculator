"""
Planning stage executor.
Calls Terraform Execution Service to generate plan.json.
"""
from typing import Dict, Any
import httpx
from app.stages.base import BaseStageExecutor
from app.models.job import Job
from app.config import settings
from app.utils.logger import get_logger

logger = get_logger(__name__)


class PlanningStageExecutor(BaseStageExecutor):
    """Planning stage - execute Terraform plan."""
    
    def __init__(self):
        super().__init__("PLANNING")
        self.terraform_url = settings.terraform_execution_url
    
    async def validate_input(self, job: Job) -> None:
        """Validate that upload_id exists."""
        if not job.upload_id:
            raise ValueError("Missing upload_id")
    
    async def execute(self, job: Job) -> Dict[str, Any]:
        """
        Execute Terraform plan.
        
        Returns:
            Dict with plan_reference
        """
        logger.info(f"Executing planning stage for job {job.job_id}")
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.terraform_url}/internal/plan",
                json={
                    "job_id": job.job_id,
                    "upload_id": job.upload_id
                },
                headers={"Authorization": f"Bearer {settings.service_auth_token}"},
                timeout=settings.planning_timeout
            )
            response.raise_for_status()
            result = response.json()
        
        return result
    
    async def validate_output(self, result: Dict[str, Any]) -> None:
        """Validate plan output."""
        if "plan_reference" not in result:
            raise ValueError("Missing plan_reference in result")
