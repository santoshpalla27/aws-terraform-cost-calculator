"""Main FastAPI application."""

import time
from pathlib import Path
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, status
from fastapi.responses import JSONResponse

from .config import settings
from .models import ExecutionRequest, ExecutionResponse, HealthCheckResponse, ExecutionStatus
from .executor import TerraformExecutor
from .utils.logger import setup_logging, get_logger

# Setup logging
setup_logging()
logger = get_logger(__name__)


# Global executor instance
_executor: TerraformExecutor | None = None


def get_executor() -> TerraformExecutor:
    """Get the global executor instance."""
    global _executor
    if _executor is None:
        _executor = TerraformExecutor()
    return _executor


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events."""
    # Startup
    logger.info(
        "Starting Terraform Executor",
        app_name=settings.app_name,
        version=settings.app_version
    )
    
    # Initialize executor
    executor = get_executor()
    tf_version = executor.get_terraform_version()
    logger.info("Terraform version", version=tf_version)
    
    yield
    
    # Shutdown
    logger.info("Shutting down Terraform Executor")


# Create FastAPI application
app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="""
    Secure, sandboxed Terraform execution service.
    
    ## Features
    
    - **Isolated Execution**: Runs Terraform in isolated workspaces
    - **Security Controls**: Blocks dangerous providers and provisioners
    - **No State Persistence**: Executes with -backend=false
    - **Resource Limits**: Enforces CPU, memory, and timeout limits
    - **Deterministic Output**: Returns plan JSON for cost estimation
    
    ## Security
    
    - Read-only filesystem
    - Non-root user execution
    - Provider filtering
    - Backend blocking
    - Timeout enforcement
    """,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    lifespan=lifespan,
)


@app.get(
    "/health",
    response_model=HealthCheckResponse,
    status_code=status.HTTP_200_OK,
    summary="Health check",
    description="Returns service health status and Terraform version"
)
async def health_check() -> HealthCheckResponse:
    """Health check endpoint."""
    executor = get_executor()
    tf_version = executor.get_terraform_version()
    
    return HealthCheckResponse(
        status="healthy",
        terraform_version=tf_version
    )


@app.post(
    "/api/v1/execute",
    response_model=ExecutionResponse,
    status_code=status.HTTP_200_OK,
    summary="Execute Terraform",
    description="Execute Terraform and return plan JSON",
    responses={
        400: {"description": "Invalid request"},
        500: {"description": "Execution failed"},
    }
)
async def execute_terraform(request: ExecutionRequest) -> ExecutionResponse:
    """Execute Terraform and return plan JSON.
    
    This endpoint:
    1. Creates an isolated workspace
    2. Validates configuration for security issues
    3. Runs terraform init, validate, plan, and show
    4. Returns deterministic plan JSON
    5. Cleans up workspace
    """
    executor = get_executor()
    
    # Construct upload path
    upload_path = Path(settings.upload_base_dir) / request.upload_id
    
    # Validate upload path exists
    if not upload_path.exists():
        logger.error("Upload path not found", upload_id=request.upload_id, path=str(upload_path))
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Upload {request.upload_id} not found"
        )
    
    logger.info(
        "Executing Terraform",
        job_id=request.job_id,
        upload_id=request.upload_id
    )
    
    start_time = time.time()
    
    # Execute Terraform
    exec_status, plan_json, error_msg, tf_output = executor.execute(upload_path)
    
    execution_time = time.time() - start_time
    
    logger.info(
        "Terraform execution completed",
        job_id=request.job_id,
        status=exec_status,
        execution_time=execution_time
    )
    
    return ExecutionResponse(
        job_id=request.job_id,
        status=exec_status,
        plan_json=plan_json,
        error_type="ExecutionError" if exec_status != ExecutionStatus.SUCCESS else None,
        error_message=error_msg,
        terraform_output=tf_output if settings.debug else None,  # Only include in debug mode
        execution_time_seconds=execution_time
    )


@app.get("/", include_in_schema=False)
async def root():
    """Root endpoint."""
    return {
        "message": "Terraform Executor Service",
        "version": settings.app_version,
        "docs": "/docs",
        "health": "/health"
    }


if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "app.main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug,
        log_level=settings.log_level.lower()
    )
