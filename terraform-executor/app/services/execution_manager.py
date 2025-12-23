"""
Execution manager for tracking async Terraform executions.
Uses Redis for state storage.
"""
import json
import uuid
from datetime import datetime
from typing import Optional, Dict, Any
import redis
from app.models.execution import ExecutionStatus, ExecutionStatusResponse, ExecutionResultResponse
from app.utils.logger import get_logger

logger = get_logger(__name__)


class ExecutionManager:
    """Manages execution state in Redis."""
    
    def __init__(self, redis_url: str):
        self.redis_client = redis.from_url(redis_url, decode_responses=True)
        self.execution_prefix = "terraform:execution:"
        self.queue_name = "terraform:jobs"
    
    def create_execution(self, job_id: str, terraform_source: str, variables: Optional[Dict[str, Any]] = None) -> str:
        """
        Create a new execution and enqueue it.
        
        Returns:
            execution_id: Unique execution identifier
        """
        execution_id = f"exec_{uuid.uuid4().hex[:12]}"
        
        execution_data = {
            "execution_id": execution_id,
            "job_id": job_id,
            "status": ExecutionStatus.PENDING.value,
            "terraform_source": terraform_source,
            "variables": variables or {},
            "created_at": datetime.utcnow().isoformat(),
            "started_at": None,
            "completed_at": None,
            "plan_json": None,
            "error_message": None,
            "metadata": {}
        }
        
        # Store execution state
        key = f"{self.execution_prefix}{execution_id}"
        self.redis_client.setex(key, 3600, json.dumps(execution_data))  # 1 hour TTL
        
        # Enqueue for worker processing
        job_data = {
            "execution_id": execution_id,
            "job_id": job_id,
            "terraform_source": terraform_source,
            "variables": variables
        }
        self.redis_client.lpush(self.queue_name, json.dumps(job_data))
        
        logger.info(f"Created execution {execution_id} for job {job_id}")
        return execution_id
    
    def get_status(self, execution_id: str) -> Optional[ExecutionStatusResponse]:
        """Get execution status."""
        key = f"{self.execution_prefix}{execution_id}"
        data_json = self.redis_client.get(key)
        
        if not data_json:
            return None
        
        data = json.loads(data_json)
        return ExecutionStatusResponse(
            execution_id=data["execution_id"],
            job_id=data["job_id"],
            status=ExecutionStatus(data["status"]),
            started_at=datetime.fromisoformat(data["started_at"]) if data.get("started_at") else None,
            completed_at=datetime.fromisoformat(data["completed_at"]) if data.get("completed_at") else None,
            duration_ms=data.get("duration_ms"),
            error_message=data.get("error_message")
        )
    
    def get_result(self, execution_id: str) -> Optional[ExecutionResultResponse]:
        """Get execution result."""
        key = f"{self.execution_prefix}{execution_id}"
        data_json = self.redis_client.get(key)
        
        if not data_json:
            return None
        
        data = json.loads(data_json)
        return ExecutionResultResponse(
            execution_id=data["execution_id"],
            job_id=data["job_id"],
            status=ExecutionStatus(data["status"]),
            plan_json=data.get("plan_json"),
            error_message=data.get("error_message"),
            metadata=data.get("metadata")
        )
    
    def update_status(self, execution_id: str, status: ExecutionStatus, **kwargs):
        """Update execution status."""
        key = f"{self.execution_prefix}{execution_id}"
        data_json = self.redis_client.get(key)
        
        if not data_json:
            logger.error(f"Execution {execution_id} not found")
            return
        
        data = json.loads(data_json)
        data["status"] = status.value
        
        # Update additional fields
        for k, v in kwargs.items():
            if k in data:
                data[k] = v.isoformat() if isinstance(v, datetime) else v
        
        self.redis_client.setex(key, 3600, json.dumps(data))
        logger.info(f"Updated execution {execution_id} status to {status.value}")
    
    def kill_execution(self, execution_id: str):
        """Mark execution as killed."""
        self.update_status(
            execution_id,
            ExecutionStatus.KILLED,
            completed_at=datetime.utcnow(),
            error_message="Execution killed by timeout or manual intervention"
        )
