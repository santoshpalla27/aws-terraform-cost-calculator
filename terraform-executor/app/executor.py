"""Terraform executor engine."""

import subprocess
import time
from pathlib import Path
from typing import Tuple, Optional, Dict, Any

from .config import settings
from .models import ExecutionStatus
from .security import SecurityValidator
from .parser import PlanParser
from .utils.logger import get_logger
from .utils.workspace import Workspace

logger = get_logger(__name__)


class TerraformExecutor:
    """Executes Terraform commands in isolated environment."""
    
    def __init__(self):
        """Initialize Terraform executor."""
        self.security_validator = SecurityValidator()
        self.plan_parser = PlanParser()
        self.timeout = settings.execution_timeout
        logger.info("Initialized Terraform executor", timeout=self.timeout)
    
    def execute(self, upload_path: Path) -> Tuple[ExecutionStatus, Optional[Dict[str, Any]], Optional[str], Optional[str]]:
        """Execute Terraform and return plan JSON.
        
        Args:
            upload_path: Path to uploaded Terraform files
            
        Returns:
            Tuple of (status, plan_json, error_message, terraform_output)
        """
        start_time = time.time()
        
        # Create isolated workspace
        with Workspace(settings.workspace_dir) as workspace:
            try:
                # Copy files to workspace
                workspace.copy_files(upload_path)
                
                # Security validation
                is_valid, error_msg = self.security_validator.validate_configuration(workspace.workspace_path)
                if not is_valid:
                    logger.error("Security validation failed", error=error_msg)
                    return ExecutionStatus.FAILED, None, f"Security validation failed: {error_msg}", None
                
                # Execute Terraform commands
                status, plan_json, error_msg, tf_output = self._execute_terraform(workspace.workspace_path)
                
                execution_time = time.time() - start_time
                logger.info(
                    "Terraform execution completed",
                    status=status,
                    execution_time=execution_time
                )
                
                return status, plan_json, error_msg, tf_output
                
            except Exception as e:
                logger.error("Terraform execution failed", error=str(e), exc_info=True)
                return ExecutionStatus.FAILED, None, f"Execution error: {str(e)}", None
    
    def _execute_terraform(self, workspace_path: Path) -> Tuple[ExecutionStatus, Optional[Dict[str, Any]], Optional[str], Optional[str]]:
        """Execute Terraform commands.
        
        Args:
            workspace_path: Path to workspace
            
        Returns:
            Tuple of (status, plan_json, error_message, terraform_output)
        """
        all_output = []
        
        try:
            # Step 1: terraform init
            logger.info("Running terraform init")
            success, output = self._run_command(
                ["terraform", "init", "-backend=false", "-no-color"],
                workspace_path
            )
            all_output.append(f"=== INIT ===\n{output}")
            
            if not success:
                return ExecutionStatus.FAILED, None, "Terraform init failed", "\n".join(all_output)
            
            # Step 2: terraform validate
            logger.info("Running terraform validate")
            success, output = self._run_command(
                ["terraform", "validate", "-no-color"],
                workspace_path
            )
            all_output.append(f"=== VALIDATE ===\n{output}")
            
            if not success:
                return ExecutionStatus.FAILED, None, "Terraform validation failed", "\n".join(all_output)
            
            # Step 3: terraform plan
            logger.info("Running terraform plan")
            plan_file = workspace_path / "tfplan"
            success, output = self._run_command(
                ["terraform", "plan", "-out=tfplan", "-no-color"],
                workspace_path
            )
            all_output.append(f"=== PLAN ===\n{output}")
            
            if not success:
                return ExecutionStatus.FAILED, None, "Terraform plan failed", "\n".join(all_output)
            
            # Step 4: terraform show -json
            logger.info("Running terraform show -json")
            success, json_output = self._run_command(
                ["terraform", "show", "-json", "tfplan"],
                workspace_path
            )
            all_output.append(f"=== SHOW JSON ===\n{json_output[:500]}...")  # Truncate for logs
            
            if not success:
                return ExecutionStatus.FAILED, None, "Terraform show failed", "\n".join(all_output)
            
            # Parse JSON
            plan_json = self.plan_parser.parse_plan_json(json_output)
            if not plan_json:
                return ExecutionStatus.FAILED, None, "Failed to parse plan JSON", "\n".join(all_output)
            
            return ExecutionStatus.SUCCESS, plan_json, None, "\n".join(all_output)
            
        except subprocess.TimeoutExpired:
            logger.error("Terraform execution timed out")
            return ExecutionStatus.TIMEOUT, None, f"Execution timed out after {self.timeout} seconds", "\n".join(all_output)
        except Exception as e:
            logger.error("Terraform execution error", error=str(e))
            return ExecutionStatus.FAILED, None, str(e), "\n".join(all_output)
    
    def _run_command(self, cmd: list, cwd: Path) -> Tuple[bool, str]:
        """Run a command with timeout.
        
        Args:
            cmd: Command and arguments
            cwd: Working directory
            
        Returns:
            Tuple of (success, output)
        """
        try:
            result = subprocess.run(
                cmd,
                cwd=cwd,
                capture_output=True,
                text=True,
                timeout=self.timeout,
                check=False
            )
            
            output = result.stdout + result.stderr
            success = result.returncode == 0
            
            if not success:
                logger.warning(
                    "Command failed",
                    cmd=" ".join(cmd),
                    returncode=result.returncode,
                    output=output[:500]
                )
            
            return success, output
            
        except subprocess.TimeoutExpired as e:
            logger.error("Command timed out", cmd=" ".join(cmd))
            raise
        except Exception as e:
            logger.error("Command execution error", cmd=" ".join(cmd), error=str(e))
            return False, str(e)
    
    def get_terraform_version(self) -> Optional[str]:
        """Get Terraform version.
        
        Returns:
            Terraform version string or None
        """
        try:
            result = subprocess.run(
                ["terraform", "version", "-json"],
                capture_output=True,
                text=True,
                timeout=5,
                check=False
            )
            
            if result.returncode == 0:
                import json
                version_data = json.loads(result.stdout)
                return version_data.get("terraform_version")
            
            return None
            
        except Exception as e:
            logger.error("Failed to get Terraform version", error=str(e))
            return None
