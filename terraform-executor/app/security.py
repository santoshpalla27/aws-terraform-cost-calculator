"""Security controls for Terraform execution."""

import re
from pathlib import Path
from typing import Tuple, List

from .utils.logger import get_logger
from .config import settings

logger = get_logger(__name__)


class SecurityValidator:
    """Validates Terraform configurations for security issues."""
    
    def __init__(self):
        """Initialize security validator."""
        self.blocked_providers = settings.blocked_providers_list
        logger.info("Initialized security validator", blocked_providers=self.blocked_providers)
    
    def validate_configuration(self, workspace_path: Path) -> Tuple[bool, str]:
        """Validate Terraform configuration for security issues.
        
        Args:
            workspace_path: Path to workspace containing Terraform files
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        # Check for dangerous providers
        is_valid, error = self._check_dangerous_providers(workspace_path)
        if not is_valid:
            return False, error
        
        # Check for backend configuration
        is_valid, error = self._check_backend_config(workspace_path)
        if not is_valid:
            return False, error
        
        # Check for provisioners
        is_valid, error = self._check_provisioners(workspace_path)
        if not is_valid:
            return False, error
        
        return True, ""
    
    def _check_dangerous_providers(self, workspace_path: Path) -> Tuple[bool, str]:
        """Check for dangerous providers.
        
        Args:
            workspace_path: Path to workspace
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        tf_files = list(workspace_path.rglob("*.tf"))
        
        for tf_file in tf_files:
            content = tf_file.read_text()
            
            # Check for blocked providers
            for provider in self.blocked_providers:
                # Pattern to match provider blocks
                pattern = rf'provider\s+"{provider}"'
                if re.search(pattern, content, re.IGNORECASE):
                    logger.warning(
                        "Blocked provider detected",
                        provider=provider,
                        file=str(tf_file)
                    )
                    return False, f"Blocked provider detected: {provider}"
                
                # Check for provider usage in resources
                resource_pattern = rf'resource\s+"{provider}_'
                if re.search(resource_pattern, content, re.IGNORECASE):
                    logger.warning(
                        "Blocked provider resource detected",
                        provider=provider,
                        file=str(tf_file)
                    )
                    return False, f"Blocked provider resource detected: {provider}"
        
        return True, ""
    
    def _check_backend_config(self, workspace_path: Path) -> Tuple[bool, str]:
        """Check for backend configuration.
        
        Args:
            workspace_path: Path to workspace
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        tf_files = list(workspace_path.rglob("*.tf"))
        
        for tf_file in tf_files:
            content = tf_file.read_text()
            
            # Pattern to match backend blocks
            pattern = r'backend\s+"[^"]+"'
            if re.search(pattern, content):
                logger.warning("Backend configuration detected", file=str(tf_file))
                return False, "Backend configuration is not allowed. Terraform must run with -backend=false"
        
        return True, ""
    
    def _check_provisioners(self, workspace_path: Path) -> Tuple[bool, str]:
        """Check for dangerous provisioners.
        
        Args:
            workspace_path: Path to workspace
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        tf_files = list(workspace_path.rglob("*.tf"))
        
        dangerous_provisioners = ["local-exec", "remote-exec"]
        
        for tf_file in tf_files:
            content = tf_file.read_text()
            
            for provisioner in dangerous_provisioners:
                pattern = rf'provisioner\s+"{provisioner}"'
                if re.search(pattern, content):
                    logger.warning(
                        "Dangerous provisioner detected",
                        provisioner=provisioner,
                        file=str(tf_file)
                    )
                    return False, f"Dangerous provisioner detected: {provisioner}"
        
        return True, ""
    
    def sanitize_path(self, path: str) -> str:
        """Sanitize file path to prevent traversal attacks.
        
        Args:
            path: Path to sanitize
            
        Returns:
            Sanitized path
        """
        # Remove dangerous characters
        dangerous_chars = ['..', '\x00']
        sanitized = path
        for char in dangerous_chars:
            sanitized = sanitized.replace(char, '')
        
        return sanitized
