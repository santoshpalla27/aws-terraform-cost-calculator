"""
Terraform configuration validator.
Blocks malicious patterns and enforces security policies.
"""
import re
from pathlib import Path
from typing import List
from app.config import settings
from app.utils.logger import get_logger

logger = get_logger(__name__)


class SecurityViolation(Exception):
    """Raised when a security violation is detected."""
    pass


class TerraformValidator:
    """Validates Terraform configurations for security violations."""
    
    def __init__(self):
        self.allowed_providers = settings.allowed_providers
        self.block_local_exec = settings.block_local_exec
        self.block_external_data = settings.block_external_data
    
    def validate_workspace(self, workspace_path: Path) -> None:
        """
        Validate all Terraform files in workspace.
        
        Args:
            workspace_path: Path to workspace directory
            
        Raises:
            SecurityViolation: If security violation detected
        """
        tf_files = list(workspace_path.glob("*.tf"))
        
        for tf_file in tf_files:
            content = tf_file.read_text()
            
            # Check for local-exec provisioners
            if self.block_local_exec:
                self._check_local_exec(content, tf_file.name)
            
            # Check for external data sources
            if self.block_external_data:
                self._check_external_data(content, tf_file.name)
        
        logger.info(f"Validated {len(tf_files)} Terraform files")
    
    def _check_local_exec(self, content: str, filename: str) -> None:
        """Check for local-exec provisioners."""
        pattern = r'provisioner\s+"local-exec"'
        if re.search(pattern, content):
            raise SecurityViolation(
                f"local-exec provisioner not allowed in {filename}"
            )
    
    def _check_external_data(self, content: str, filename: str) -> None:
        """Check for external data sources."""
        pattern = r'data\s+"external"'
        if re.search(pattern, content):
            raise SecurityViolation(
                f"external data source not allowed in {filename}"
            )
    
    def validate_providers(self, workspace_path: Path) -> None:
        """
        Validate provider configurations.
        
        Args:
            workspace_path: Path to workspace directory
            
        Raises:
            SecurityViolation: If unauthorized provider detected
        """
        # Check .terraform.lock.hcl if it exists
        lock_file = workspace_path / ".terraform.lock.hcl"
        if lock_file.exists():
            content = lock_file.read_text()
            
            # Extract provider names
            provider_pattern = r'provider\s+"registry\.terraform\.io/[^/]+/([^"]+)"'
            providers = re.findall(provider_pattern, content)
            
            for provider in providers:
                if provider not in self.allowed_providers:
                    raise SecurityViolation(
                        f"Provider '{provider}' not in allowlist: {self.allowed_providers}"
                    )
        
        logger.info("Provider validation passed")


# Global validator instance
validator = TerraformValidator()
