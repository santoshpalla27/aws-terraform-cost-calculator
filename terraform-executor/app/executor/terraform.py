"""
Terraform CLI wrapper.
Executes Terraform commands via subprocess (NO SHELL).
"""
import subprocess
import time
from pathlib import Path
from typing import Optional, Dict
from app.config import settings
from app.utils.logger import get_logger

logger = get_logger(__name__)


class TerraformExecutor:
    """Executes Terraform CLI commands."""
    
    def __init__(self):
        self.terraform_bin = "/usr/local/bin/terraform"
        self.max_execution_time = settings.max_execution_time
        self.plugin_dir = "/opt/terraform/plugins"  # Pre-baked providers
    
    def init_sync(self, workspace_path: Path, env: Optional[Dict[str, str]] = None) -> subprocess.CompletedProcess:
        """
        Run terraform init (synchronous).
        
        Uses pre-baked providers from plugin directory.
        NO network access during init.
        """
        start_time = time.time()
        
        result = subprocess.run(
            [
                self.terraform_bin,
                "init",
                "-backend=false",
                "-input=false",
                f"-plugin-dir={self.plugin_dir}",  # Use pre-baked providers
                "-get-plugins=false"  # Disable plugin downloads
            ],
            cwd=workspace_path,
            capture_output=True,
            text=True,
            timeout=60,
            env=env,
            check=False
        )
        
        duration_ms = int((time.time() - start_time) * 1000)
        logger.info(
            f"terraform init completed",
            extra={'duration_ms': duration_ms, 'returncode': result.returncode}
        )
        
        return result
    
    def validate_sync(self, workspace_path: Path, env: Optional[Dict[str, str]] = None) -> subprocess.CompletedProcess:
        """Run terraform validate (synchronous)."""
        start_time = time.time()
        
        result = subprocess.run(
            [self.terraform_bin, "validate"],
            cwd=workspace_path,
            capture_output=True,
            text=True,
            timeout=30,
            env=env,
            check=False
        )
        
        duration_ms = int((time.time() - start_time) * 1000)
        logger.info(
            f"terraform validate completed",
            extra={'duration_ms': duration_ms, 'returncode': result.returncode}
        )
        
        return result
    
    def plan_sync(self, workspace_path: Path, env: Optional[Dict[str, str]] = None) -> subprocess.CompletedProcess:
        """Run terraform plan (synchronous)."""
        start_time = time.time()
        
        result = subprocess.run(
            [self.terraform_bin, "plan", "-out=tfplan", "-input=false"],
            cwd=workspace_path,
            capture_output=True,
            text=True,
            timeout=self.max_execution_time,
            env=env,
            check=False
        )
        
        duration_ms = int((time.time() - start_time) * 1000)
        logger.info(
            f"terraform plan completed",
            extra={'duration_ms': duration_ms, 'returncode': result.returncode}
        )
        
        return result
    
    def show_json_sync(self, workspace_path: Path, env: Optional[Dict[str, str]] = None) -> subprocess.CompletedProcess:
        """Convert plan to JSON (synchronous)."""
        start_time = time.time()
        
        result = subprocess.run(
            [self.terraform_bin, "show", "-json", "tfplan"],
            cwd=workspace_path,
            capture_output=True,
            text=True,
            timeout=30,
            env=env,
            check=False
        )
        
        duration_ms = int((time.time() - start_time) * 1000)
        logger.info(
            f"terraform show -json completed",
            extra={'duration_ms': duration_ms, 'returncode': result.returncode}
        )
        
        return result


# Global executor instance
terraform_executor = TerraformExecutor()
