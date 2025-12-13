"""Validation utilities."""

import os
import zipfile
from typing import List, Tuple
from pathlib import Path

from ..config import settings


def validate_file_extension(filename: str) -> bool:
    """Validate if file has an allowed extension.
    
    Args:
        filename: Name of the file to validate
        
    Returns:
        True if extension is allowed, False otherwise
    """
    ext = os.path.splitext(filename)[1].lower()
    return ext in settings.allowed_extensions_list


def validate_file_size(size_bytes: int) -> bool:
    """Validate if file size is within limits.
    
    Args:
        size_bytes: File size in bytes
        
    Returns:
        True if size is acceptable, False otherwise
    """
    return size_bytes <= settings.max_upload_size_bytes


def validate_terraform_structure(directory: Path) -> Tuple[bool, str]:
    """Validate that directory contains valid Terraform files.
    
    Args:
        directory: Path to directory to validate
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    # Check if directory exists
    if not directory.exists() or not directory.is_dir():
        return False, "Invalid directory path"
    
    # Find all .tf files
    tf_files = list(directory.rglob("*.tf"))
    
    if not tf_files:
        return False, "No Terraform (.tf) files found"
    
    # Basic validation: at least one .tf file should have some content
    has_content = False
    for tf_file in tf_files:
        if tf_file.stat().st_size > 0:
            has_content = True
            break
    
    if not has_content:
        return False, "All Terraform files are empty"
    
    return True, ""


def validate_zip_file(zip_path: Path) -> Tuple[bool, str]:
    """Validate ZIP file structure.
    
    Args:
        zip_path: Path to ZIP file
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    try:
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            # Check if ZIP is valid
            if zip_ref.testzip() is not None:
                return False, "Corrupted ZIP file"
            
            # Check for .tf files
            tf_files = [f for f in zip_ref.namelist() if f.endswith('.tf')]
            if not tf_files:
                return False, "No Terraform (.tf) files found in ZIP"
            
            return True, ""
    except zipfile.BadZipFile:
        return False, "Invalid ZIP file format"
    except Exception as e:
        return False, f"Error validating ZIP: {str(e)}"


def sanitize_filename(filename: str) -> str:
    """Sanitize filename to prevent path traversal attacks.
    
    Args:
        filename: Original filename
        
    Returns:
        Sanitized filename
    """
    # Remove path components
    filename = os.path.basename(filename)
    
    # Remove potentially dangerous characters
    dangerous_chars = ['..', '/', '\\', '\x00']
    for char in dangerous_chars:
        filename = filename.replace(char, '')
    
    return filename
