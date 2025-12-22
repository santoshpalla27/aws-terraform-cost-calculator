"""
Upload service.
Handles file upload processing and storage.
"""
import os
import uuid
import zipfile
from pathlib import Path
from typing import List, Tuple
from fastapi import UploadFile, HTTPException, status
from app.config import settings
from app.models.domain import Upload
from app.repositories.upload_repo import upload_repository
from app.utils.validators import FileValidator
from app.utils.logger import get_logger

logger = get_logger(__name__)


class UploadService:
    """Service for handling file uploads."""
    
    def __init__(self):
        self.upload_dir = Path(settings.upload_dir)
        self.validator = FileValidator(
            allowed_extensions=settings.allowed_extensions,
            max_file_size=settings.max_upload_size
        )
        
        # Ensure upload directory exists
        self.upload_dir.mkdir(parents=True, exist_ok=True)
    
    async def process_upload(
        self,
        files: List[UploadFile],
        user_id: str
    ) -> Upload:
        """
        Process uploaded files.
        
        Args:
            files: List of uploaded files
            user_id: User identifier
            
        Returns:
            Upload object
            
        Raises:
            HTTPException: If validation fails
        """
        if not files:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No files provided"
            )
        
        # Generate unique upload ID
        upload_id = str(uuid.uuid4())
        upload_path = self.upload_dir / upload_id
        upload_path.mkdir(parents=True, exist_ok=True)
        
        total_size = 0
        file_count = 0
        original_filename = ""
        
        try:
            for file in files:
                # Validate and save file
                filename, content = await self.validator.validate_upload_file(file)
                
                if not original_filename:
                    original_filename = filename
                
                # Save file
                file_path = upload_path / filename
                with open(file_path, 'wb') as f:
                    f.write(content)
                
                total_size += len(content)
                file_count += 1
                
                # If it's a ZIP file, extract it
                if filename.lower().endswith('.zip'):
                    await self._extract_zip(file_path, upload_path)
                    file_count = len(list(upload_path.glob('**/*.tf'))) + len(list(upload_path.glob('**/*.tfvars')))
            
            # Create upload record
            upload = Upload(
                upload_id=upload_id,
                user_id=user_id,
                filename=original_filename,
                file_count=file_count,
                total_size=total_size
            )
            
            await upload_repository.create(upload)
            
            logger.info(
                f"Upload processed successfully: {upload_id}",
                extra={'upload_id': upload_id, 'file_count': file_count}
            )
            
            return upload
        
        except Exception as e:
            # Clean up on failure
            await self._cleanup_upload(upload_id)
            logger.error(f"Upload processing failed: {str(e)}")
            raise
    
    async def _extract_zip(self, zip_path: Path, extract_to: Path) -> None:
        """
        Extract ZIP file contents.
        
        Args:
            zip_path: Path to ZIP file
            extract_to: Directory to extract to
        """
        try:
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                zip_ref.extractall(extract_to)
            
            # Remove the ZIP file after extraction
            zip_path.unlink()
        
        except Exception as e:
            logger.error(f"ZIP extraction failed: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Failed to extract ZIP file: {str(e)}"
            )
    
    async def _cleanup_upload(self, upload_id: str) -> None:
        """
        Clean up upload directory on failure.
        
        Args:
            upload_id: Upload identifier
        """
        upload_path = self.upload_dir / upload_id
        if upload_path.exists():
            import shutil
            shutil.rmtree(upload_path, ignore_errors=True)
    
    async def get_upload(self, upload_id: str) -> Upload:
        """
        Get upload by ID.
        
        Args:
            upload_id: Upload identifier
            
        Returns:
            Upload object
            
        Raises:
            HTTPException: If upload not found
        """
        upload = await upload_repository.get_by_id(upload_id)
        if not upload:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Upload {upload_id} not found"
            )
        return upload


# Global service instance
upload_service = UploadService()
