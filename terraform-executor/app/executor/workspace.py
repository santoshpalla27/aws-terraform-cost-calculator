"""
Workspace manager for isolated Terraform execution.
"""
import shutil
from pathlib import Path
from typing import List
from app.config import settings
from app.utils.logger import get_logger

logger = get_logger(__name__)


class WorkspaceManager:
    """Manages isolated workspaces for Terraform execution."""
    
    def __init__(self):
        self.base_dir = Path(settings.workspace_base_dir)
        self.base_dir.mkdir(parents=True, exist_ok=True)
    
    def create_workspace(self, job_id: str) -> Path:
        """
        Create isolated workspace for job.
        
        Args:
            job_id: Unique job identifier
            
        Returns:
            Path to workspace directory
            
        Raises:
            FileExistsError: If workspace already exists
        """
        workspace_path = self.base_dir / job_id
        
        if workspace_path.exists():
            raise FileExistsError(f"Workspace {job_id} already exists")
        
        workspace_path.mkdir(parents=True)
        logger.info(f"Created workspace: {workspace_path}")
        
        return workspace_path
    
    def copy_files(self, workspace_path: Path, files: List[tuple]) -> None:
        """
        Copy Terraform files into workspace.
        
        Args:
            workspace_path: Path to workspace
            files: List of (filename, content) tuples
        """
        for filename, content in files:
            # Sanitize filename (prevent path traversal)
            safe_filename = Path(filename).name
            file_path = workspace_path / safe_filename
            
            # Write file
            if isinstance(content, bytes):
                file_path.write_bytes(content)
            else:
                file_path.write_text(content)
        
        logger.info(f"Copied {len(files)} files to workspace")
    
    def get_workspace_size(self, workspace_path: Path) -> int:
        """
        Get total size of workspace in bytes.
        
        Args:
            workspace_path: Path to workspace
            
        Returns:
            Total size in bytes
        """
        total_size = sum(
            f.stat().st_size
            for f in workspace_path.rglob('*')
            if f.is_file()
        )
        return total_size
    
    def destroy_workspace(self, job_id: str) -> None:
        """
        Destroy workspace immediately.
        
        Args:
            job_id: Job identifier
        """
        workspace_path = self.base_dir / job_id
        
        if workspace_path.exists():
            shutil.rmtree(workspace_path, ignore_errors=True)
            logger.info(f"Destroyed workspace: {workspace_path}")
        else:
            logger.warning(f"Workspace {job_id} does not exist")


# Global workspace manager instance
workspace_manager = WorkspaceManager()
