"""
Upload endpoints.
"""
from typing import List
from fastapi import APIRouter, UploadFile, File, Depends, Request
from app.models.responses import UploadResponse
from app.services.upload_service import upload_service
from app.middleware.auth import get_current_user

router = APIRouter(prefix="/api/uploads", tags=["uploads"])


@router.post("", response_model=UploadResponse)
async def create_upload(
    files: List[UploadFile] = File(..., description="Terraform files to upload"),
    user_id: str = Depends(get_current_user)
):
    """
    Upload Terraform configuration files.
    
    Accepts:
    - Individual .tf or .tfvars files
    - ZIP archives containing Terraform files
    
    Security:
    - File extension validation
    - Size limit enforcement
    - Path traversal prevention
    - Zip bomb detection
    """
    upload = await upload_service.process_upload(files, user_id)
    return UploadResponse(upload=upload)


@router.get("/{upload_id}", response_model=UploadResponse)
async def get_upload(
    upload_id: str,
    user_id: str = Depends(get_current_user)
):
    """Get upload metadata by ID."""
    upload = await upload_service.get_upload(upload_id)
    
    # Verify user owns the upload
    if upload.user_id != user_id:
        from fastapi import HTTPException, status
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to access this upload"
        )
    
    return UploadResponse(upload=upload, message="Upload retrieved successfully")
