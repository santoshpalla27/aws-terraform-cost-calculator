"""
Worker process for executing Terraform jobs.
Runs SEPARATELY from FastAPI API process.
"""
import os
import sys
import time
import json
import signal
from pathlib import Path
import redis

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.config import settings
from app.executor.workspace import workspace_manager
from app.executor.terraform import terraform_executor
from app.security.validator import validator, SecurityViolation
from app.security.credentials import credential_resolver
from app.utils.logger import setup_logging, get_logger, set_job_id

# Setup logging
setup_logging(settings.log_level, settings.log_format)
logger = get_logger(__name__)

# Global flag for graceful shutdown
shutdown_requested = False


def signal_handler(signum, frame):
    """Handle shutdown signals."""
    global shutdown_requested
    logger.info(f"Received signal {signum}, initiating graceful shutdown")
    shutdown_requested = True


def execute_job(job_data: dict) -> dict:
    """
    Execute a single Terraform job.
    
    Args:
        job_data: Job data from queue
        
    Returns:
        Execution result
    """
    job_id = job_data.get('job_id')
    workspace_reference = job_data.get('workspace_reference')
    credential_reference = job_data.get('credential_reference')
    
    set_job_id(job_id)
    start_time = time.time()
    workspace_path = None
    
    try:
        logger.info(f"Starting execution for job {job_id}")
        
        # 1. Create isolated workspace
        workspace_path = workspace_manager.create_workspace(job_id)
        
        # 2. Download and copy Terraform files
        # TODO: Download from workspace_reference (S3/storage)
        
        # 3. Enforce workspace size BEFORE execution
        workspace_size = workspace_manager.get_workspace_size(workspace_path)
        max_size_bytes = settings.max_workspace_size * 1024 * 1024  # Convert MB to bytes
        
        if workspace_size > max_size_bytes:
            raise Exception(
                f"Workspace size {workspace_size} bytes exceeds limit {max_size_bytes} bytes"
            )
        
        logger.info(f"Workspace size: {workspace_size} bytes (limit: {max_size_bytes} bytes)")
        
        # 4. Validate Terraform configuration
        validator.validate_workspace(workspace_path)
        logger.info("Security validation passed")
        
        # 5. Resolve credentials (NO raw credentials in request)
        env = os.environ.copy()
        if credential_reference:
            creds = credential_resolver.resolve(credential_reference)
            env.update(creds)
            logger.info("Credentials resolved and injected")
        
        # 6. Execute Terraform commands with HARD timeout
        # Set alarm for hard kill
        signal.signal(signal.SIGALRM, lambda s, f: sys.exit(1))
        signal.alarm(settings.max_execution_time)
        
        try:
            # terraform init
            init_result = terraform_executor.init_sync(workspace_path, env)
            if init_result.returncode != 0:
                raise Exception(f"terraform init failed: {init_result.stderr}")
            
            # terraform validate
            validate_result = terraform_executor.validate_sync(workspace_path, env)
            if validate_result.returncode != 0:
                raise Exception(f"terraform validate failed: {validate_result.stderr}")
            
            # terraform plan
            plan_result = terraform_executor.plan_sync(workspace_path, env)
            if plan_result.returncode != 0:
                raise Exception(f"terraform plan failed: {plan_result.stderr}")
            
            # terraform show -json
            show_result = terraform_executor.show_json_sync(workspace_path, env)
            if show_result.returncode != 0:
                raise Exception(f"terraform show failed: {show_result.stderr}")
            
            # Cancel alarm
            signal.alarm(0)
        
        except Exception as e:
            signal.alarm(0)  # Cancel alarm
            raise
        
        # 7. Save plan.json
        plan_json_path = workspace_path / "plan.json"
        plan_json_path.write_text(show_result.stdout)
        
        # 8. Upload plan.json to storage
        # TODO: Upload to S3/storage
        plan_reference = f"s3://bucket/plans/{job_id}.json"
        
        # 9. Calculate metadata
        duration_ms = int((time.time() - start_time) * 1000)
        
        logger.info(f"Job {job_id} completed successfully in {duration_ms}ms")
        
        return {
            "success": True,
            "job_id": job_id,
            "plan_reference": plan_reference,
            "duration_ms": duration_ms
        }
    
    except SecurityViolation as e:
        logger.error(f"Security violation: {str(e)}")
        return {
            "success": False,
            "job_id": job_id,
            "error_type": "security_violation",
            "error_message": str(e)
        }
    
    except Exception as e:
        logger.error(f"Execution failed: {str(e)}")
        return {
            "success": False,
            "job_id": job_id,
            "error_type": "unknown_error",
            "error_message": str(e)
        }
    
    finally:
        # GUARANTEED cleanup
        if workspace_path:
            try:
                workspace_manager.destroy_workspace(job_id)
            except Exception as e:
                logger.error(f"Failed to cleanup workspace: {str(e)}")


def main():
    """Main worker loop."""
    global shutdown_requested
    
    # Register signal handlers
    signal.signal(signal.SIGTERM, signal_handler)
    signal.signal(signal.SIGINT, signal_handler)
    
    logger.info("Terraform Executor Worker starting...")
    logger.info(f"Terraform version: {settings.terraform_version}")
    logger.info(f"Max execution time: {settings.max_execution_time}s")
    
    # Connect to Redis
    redis_client = redis.from_url(
        os.environ.get("REDIS_URL", "redis://localhost:6379/0"),
        decode_responses=True
    )
    
    queue_name = "terraform:jobs"
    
    logger.info(f"Listening on queue: {queue_name}")
    
    while not shutdown_requested:
        try:
            # Block for 1 second waiting for jobs
            result = redis_client.brpop(queue_name, timeout=1)
            
            if result is None:
                continue
            
            _, job_json = result
            job_data = json.loads(job_json)
            
            logger.info(f"Received job: {job_data.get('job_id')}")
            
            # Execute job
            result = execute_job(job_data)
            
            # Store result in Redis
            result_key = f"terraform:result:{job_data.get('job_id')}"
            redis_client.setex(result_key, 3600, json.dumps(result))  # 1 hour TTL
            
        except Exception as e:
            logger.error(f"Worker error: {str(e)}")
            time.sleep(1)
    
    logger.info("Worker shutting down gracefully")


if __name__ == "__main__":
    main()
