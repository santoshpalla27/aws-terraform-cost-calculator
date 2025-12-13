"""Upload endpoints."""

from fastapi import APIRouter, UploadFile, File, Form, HTTPException, status, Depends

from ..models.responses import UploadResponse, ErrorResponse
from ..services.upload_service import get_upload_service
from ..middleware.rate_limit import rate_limit_middleware
from ..middleware.auth import get_current_user
from ..utils.logger import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/api/v1/uploads", tags=["Uploads"])


@router.post(
    "",
    response_model=UploadResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Upload Terraform files",
    description="Upload Terraform files as ZIP or individual files",
    responses={
        400: {"model": ErrorResponse, "description": "Invalid upload"},
        413: {"model": ErrorResponse, "description": "File too large"},
        429: {"model": ErrorResponse, "description": "Rate limit exceeded"},
    }
)
async def upload_terraform_files(
    file: UploadFile = File(..., description="Terraform files (ZIP or .tf files)"),
    project_name: str = Form(..., description="Project name", min_length=1, max_length=100),
    description: str = Form(None, description="Optional project description", max_length=500),
    _rate_limit: None = Depends(rate_limit_middleware),
    _current_user: dict = Depends(get_current_user),
) -> UploadResponse:
    """Upload Terraform files for cost estimation.
    
    Accepts:
    - ZIP files containing Terraform configurations
    - Individual .tf or .tfvars files
    
    The uploaded files will be validated for:
    - File size limits
    - Allowed file extensions
    - Valid Terraform structure
    """
    upload_service = get_upload_service()
    
    try:
        uploaded_file = await upload_service.handle_upload(
            file=file,
            project_name=project_name
        )
        
        logger.info(
            "Upload successful",
            upload_id=uploaded_file.upload_id,
            project_name=project_name
        )
        
        return UploadResponse(
            upload_id=uploaded_file.upload_id,
            project_name=uploaded_file.project_name,
            file_count=uploaded_file.file_count,
            total_size_bytes=uploaded_file.total_size_bytes,
            message="Files uploaded successfully"
        )
        
    except ValueError as e:
        logger.warning("Upload validation failed", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error("Upload failed", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to process upload"
        )
