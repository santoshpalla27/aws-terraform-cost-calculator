"""Upload service for handling Terraform file uploads."""

import os
import uuid
import shutil
import zipfile
from pathlib import Path
from typing import Tuple
from datetime import datetime

import aiofiles
from fastapi import UploadFile

from ..config import settings
from ..models.domain import UploadedFile
from ..utils.logger import get_logger
from ..utils.validators import (
    validate_file_extension,
    validate_file_size,
    validate_terraform_structure,
    validate_zip_file,
    sanitize_filename,
)

logger = get_logger(__name__)


class UploadService:
    """Service for handling file uploads."""
    
    def __init__(self):
        """Initialize upload service."""
        self.upload_dir = Path(settings.upload_dir)
        self.upload_dir.mkdir(parents=True, exist_ok=True)
        logger.info("Initialized upload service", upload_dir=str(self.upload_dir))
    
    async def handle_upload(
        self,
        file: UploadFile,
        project_name: str
    ) -> UploadedFile:
        """Handle file upload (ZIP or individual Terraform files).
        
        Args:
            file: Uploaded file
            project_name: Project name
            
        Returns:
            UploadedFile metadata
            
        Raises:
            ValueError: If validation fails
        """
        # Generate unique upload ID
        upload_id = f"upload_{uuid.uuid4().hex[:12]}"
        upload_path = self.upload_dir / upload_id
        upload_path.mkdir(parents=True, exist_ok=True)
        
        logger.info(
            "Processing upload",
            upload_id=upload_id,
            filename=file.filename,
            project_name=project_name
        )
        
        try:
            # Sanitize filename
            safe_filename = sanitize_filename(file.filename or "upload.zip")
            
            # Validate extension
            if not validate_file_extension(safe_filename):
                raise ValueError(
                    f"Invalid file extension. Allowed: {settings.allowed_extensions}"
                )
            
            # Save uploaded file temporarily
            temp_file_path = upload_path / safe_filename
            file_size = await self._save_upload_file(file, temp_file_path)
            
            # Validate size
            if not validate_file_size(file_size):
                raise ValueError(
                    f"File too large. Maximum size: {settings.max_upload_size_mb}MB"
                )
            
            # Extract if ZIP
            if safe_filename.endswith('.zip'):
                is_valid, error_msg = validate_zip_file(temp_file_path)
                if not is_valid:
                    raise ValueError(error_msg)
                
                await self._extract_zip(temp_file_path, upload_path)
                # Remove ZIP after extraction
                temp_file_path.unlink()
            
            # Validate Terraform structure
            is_valid, error_msg = validate_terraform_structure(upload_path)
            if not is_valid:
                raise ValueError(error_msg)
            
            # Count files and calculate total size
            file_count, total_size = self._calculate_stats(upload_path)
            
            uploaded_file = UploadedFile(
                upload_id=upload_id,
                project_name=project_name,
                file_count=file_count,
                total_size_bytes=total_size,
                upload_path=str(upload_path),
                created_at=datetime.utcnow()
            )
            
            logger.info(
                "Upload completed",
                upload_id=upload_id,
                file_count=file_count,
                total_size_bytes=total_size
            )
            
            return uploaded_file
            
        except Exception as e:
            # Clean up on error
            if upload_path.exists():
                shutil.rmtree(upload_path)
            logger.error("Upload failed", upload_id=upload_id, error=str(e))
            raise
    
    async def _save_upload_file(self, file: UploadFile, destination: Path) -> int:
        """Save uploaded file to destination.
        
        Args:
            file: Uploaded file
            destination: Destination path
            
        Returns:
            File size in bytes
        """
        total_size = 0
        async with aiofiles.open(destination, 'wb') as f:
            while chunk := await file.read(8192):  # 8KB chunks
                await f.write(chunk)
                total_size += len(chunk)
        return total_size
    
    async def _extract_zip(self, zip_path: Path, extract_to: Path) -> None:
        """Extract ZIP file.
        
        Args:
            zip_path: Path to ZIP file
            extract_to: Extraction destination
        """
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            zip_ref.extractall(extract_to)
        logger.info("Extracted ZIP", zip_path=str(zip_path), extract_to=str(extract_to))
    
    def _calculate_stats(self, directory: Path) -> Tuple[int, int]:
        """Calculate file count and total size.
        
        Args:
            directory: Directory to analyze
            
        Returns:
            Tuple of (file_count, total_size_bytes)
        """
        file_count = 0
        total_size = 0
        
        for file_path in directory.rglob('*'):
            if file_path.is_file():
                file_count += 1
                total_size += file_path.stat().st_size
        
        return file_count, total_size
    
    def cleanup_upload(self, upload_id: str) -> bool:
        """Clean up uploaded files.
        
        Args:
            upload_id: Upload identifier
            
        Returns:
            True if cleaned up, False otherwise
        """
        upload_path = self.upload_dir / upload_id
        if upload_path.exists():
            shutil.rmtree(upload_path)
            logger.info("Cleaned up upload", upload_id=upload_id)
            return True
        return False


# Global service instance
_upload_service: UploadService | None = None


def get_upload_service() -> UploadService:
    """Get the global upload service instance.
    
    Returns:
        UploadService instance
    """
    global _upload_service
    if _upload_service is None:
        _upload_service = UploadService()
    return _upload_service
