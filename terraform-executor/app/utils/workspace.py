"""Workspace management for isolated Terraform execution."""

import os
import shutil
import uuid
from pathlib import Path
from typing import Optional

from .logger import get_logger

logger = get_logger(__name__)


class Workspace:
    """Manages isolated workspace for Terraform execution."""
    
    def __init__(self, workspace_base: str = "/tmp/workspace"):
        """Initialize workspace manager.
        
        Args:
            workspace_base: Base directory for workspaces
        """
        self.workspace_base = Path(workspace_base)
        self.workspace_id: Optional[str] = None
        self.workspace_path: Optional[Path] = None
    
    def create(self) -> Path:
        """Create a new isolated workspace.
        
        Returns:
            Path to workspace directory
        """
        self.workspace_id = f"ws_{uuid.uuid4().hex[:12]}"
        self.workspace_path = self.workspace_base / self.workspace_id
        
        # Create workspace directory
        self.workspace_path.mkdir(parents=True, exist_ok=True)
        
        logger.info("Created workspace", workspace_id=self.workspace_id, path=str(self.workspace_path))
        
        return self.workspace_path
    
    def copy_files(self, source_dir: Path) -> None:
        """Copy Terraform files to workspace.
        
        Args:
            source_dir: Source directory containing Terraform files
            
        Raises:
            ValueError: If source directory doesn't exist
        """
        if not source_dir.exists():
            raise ValueError(f"Source directory does not exist: {source_dir}")
        
        if not self.workspace_path:
            raise ValueError("Workspace not created")
        
        # Copy all files
        for item in source_dir.rglob('*'):
            if item.is_file():
                # Calculate relative path
                rel_path = item.relative_to(source_dir)
                dest_path = self.workspace_path / rel_path
                
                # Create parent directories
                dest_path.parent.mkdir(parents=True, exist_ok=True)
                
                # Copy file
                shutil.copy2(item, dest_path)
        
        logger.info("Copied files to workspace", workspace_id=self.workspace_id, source=str(source_dir))
    
    def cleanup(self) -> None:
        """Clean up workspace directory."""
        if self.workspace_path and self.workspace_path.exists():
            try:
                shutil.rmtree(self.workspace_path)
                logger.info("Cleaned up workspace", workspace_id=self.workspace_id)
            except Exception as e:
                logger.error("Failed to cleanup workspace", workspace_id=self.workspace_id, error=str(e))
    
    def __enter__(self):
        """Context manager entry."""
        self.create()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.cleanup()
