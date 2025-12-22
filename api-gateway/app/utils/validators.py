"""
File validation utilities.
Prevents path traversal, zip bombs, and validates file types.
"""
import os
import zipfile
from pathlib import Path
from typing import List, Tuple
from fastapi import UploadFile, HTTPException, status


class FileValidator:
    """Validates uploaded files for security and compliance."""
    
    def __init__(
        self,
        allowed_extensions: List[str],
        max_file_size: int,
        max_zip_ratio: float = 10.0,
        max_zip_files: int = 1000
    ):
        self.allowed_extensions = [ext.lower() for ext in allowed_extensions]
        self.max_file_size = max_file_size
        self.max_zip_ratio = max_zip_ratio
        self.max_zip_files = max_zip_files
    
    def validate_filename(self, filename: str) -> str:
        """
        Validate and sanitize filename.
        Prevents path traversal attacks.
        
        Args:
            filename: Original filename
            
        Returns:
            Sanitized filename
            
        Raises:
            HTTPException: If filename is invalid
        """
        if not filename:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Filename cannot be empty"
            )
        
        # Remove any path components
        filename = os.path.basename(filename)
        
        # Check for path traversal attempts
        if '..' in filename or filename.startswith('/') or filename.startswith('\\'):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid filename: path traversal detected"
            )
        
        # Check for null bytes
        if '\x00' in filename:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid filename: null byte detected"
            )
        
        return filename
    
    def validate_extension(self, filename: str) -> None:
        """
        Validate file extension.
        
        Args:
            filename: Filename to validate
            
        Raises:
            HTTPException: If extension is not allowed
        """
        ext = Path(filename).suffix.lower()
        
        if ext not in self.allowed_extensions:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"File extension '{ext}' not allowed. Allowed: {', '.join(self.allowed_extensions)}"
            )
    
    def validate_file_size(self, file_size: int) -> None:
        """
        Validate file size.
        
        Args:
            file_size: Size in bytes
            
        Raises:
            HTTPException: If file is too large
        """
        if file_size > self.max_file_size:
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail=f"File size {file_size} exceeds maximum {self.max_file_size} bytes"
            )
    
    async def validate_upload_file(self, file: UploadFile) -> Tuple[str, bytes]:
        """
        Validate an uploaded file.
        
        Args:
            file: FastAPI UploadFile object
            
        Returns:
            Tuple of (sanitized_filename, file_content)
            
        Raises:
            HTTPException: If validation fails
        """
        # Validate filename
        filename = self.validate_filename(file.filename or "")
        
        # Validate extension
        self.validate_extension(filename)
        
        # Read file content
        content = await file.read()
        
        # Validate size
        self.validate_file_size(len(content))
        
        # If it's a ZIP file, check for zip bombs
        if filename.lower().endswith('.zip'):
            self.validate_zip_file(content)
        
        return filename, content
    
    def validate_zip_file(self, content: bytes) -> None:
        """
        Validate ZIP file to prevent zip bombs.
        
        Args:
            content: ZIP file content
            
        Raises:
            HTTPException: If ZIP file is malicious
        """
        try:
            import io
            zip_file = zipfile.ZipFile(io.BytesIO(content))
            
            # Check number of files
            if len(zip_file.namelist()) > self.max_zip_files:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"ZIP contains too many files (max: {self.max_zip_files})"
                )
            
            # Check compression ratio
            compressed_size = len(content)
            uncompressed_size = sum(info.file_size for info in zip_file.infolist())
            
            if uncompressed_size > compressed_size * self.max_zip_ratio:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="ZIP file has suspicious compression ratio (possible zip bomb)"
                )
            
            # Validate each file in the ZIP
            for info in zip_file.infolist():
                # Check for path traversal in ZIP entries
                if info.filename.startswith('/') or '..' in info.filename:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=f"ZIP contains invalid path: {info.filename}"
                    )
                
                # Validate extension of files in ZIP
                if not info.is_dir():
                    self.validate_extension(info.filename)
        
        except zipfile.BadZipFile:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid ZIP file"
            )
