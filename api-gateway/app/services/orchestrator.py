"""Orchestrator for communicating with downstream services."""

from typing import Dict, Any, Optional
import httpx

from ..config import settings
from ..models.domain import Job
from ..utils.logger import get_logger

logger = get_logger(__name__)


class ServiceOrchestrator:
    """Orchestrates communication with downstream services."""
    
    def __init__(self):
        """Initialize orchestrator."""
        self.terraform_executor_url = settings.terraform_executor_url
        self.http_client = httpx.AsyncClient(timeout=30.0)
        logger.info(
            "Initialized service orchestrator",
            terraform_executor_url=self.terraform_executor_url
        )
    
    async def submit_job_to_executor(self, job: Job) -> Dict[str, Any]:
        """Submit job to Terraform Execution Engine.
        
        Args:
            job: Job to submit
            
        Returns:
            Response from executor
            
        Raises:
            httpx.HTTPError: If request fails
        """
        payload = {
            "job_id": job.job_id,
            "upload_id": job.upload_id,
            "region": job.region,
        }
        
        logger.info(
            "Submitting job to executor",
            job_id=job.job_id,
            executor_url=self.terraform_executor_url
        )
        
        try:
            response = await self.http_client.post(
                f"{self.terraform_executor_url}/api/v1/execute",
                json=payload
            )
            response.raise_for_status()
            
            result = response.json()
            logger.info("Job submitted successfully", job_id=job.job_id)
            return result
            
        except httpx.HTTPError as e:
            logger.error(
                "Failed to submit job to executor",
                job_id=job.job_id,
                error=str(e)
            )
            raise
    
    async def check_executor_health(self) -> bool:
        """Check if Terraform Execution Engine is healthy.
        
        Returns:
            True if healthy, False otherwise
        """
        try:
            response = await self.http_client.get(
                f"{self.terraform_executor_url}/health",
                timeout=5.0
            )
            is_healthy = response.status_code == 200
            
            logger.info(
                "Executor health check",
                is_healthy=is_healthy,
                status_code=response.status_code
            )
            
            return is_healthy
            
        except Exception as e:
            logger.warning("Executor health check failed", error=str(e))
            return False
    
    async def close(self):
        """Close HTTP client."""
        await self.http_client.aclose()
        logger.info("Closed orchestrator HTTP client")


# Global orchestrator instance
_orchestrator: Optional[ServiceOrchestrator] = None


def get_orchestrator() -> ServiceOrchestrator:
    """Get the global orchestrator instance.
    
    Returns:
        ServiceOrchestrator instance
    """
    global _orchestrator
    if _orchestrator is None:
        _orchestrator = ServiceOrchestrator()
    return _orchestrator
