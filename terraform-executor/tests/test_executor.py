"""Tests for Terraform executor."""

import pytest
from pathlib import Path

from app.executor import TerraformExecutor
from app.models import ExecutionStatus


def test_executor_initialization():
    """Test executor initialization."""
    executor = TerraformExecutor()
    
    assert executor is not None
    assert executor.timeout > 0


def test_terraform_version():
    """Test getting Terraform version."""
    executor = TerraformExecutor()
    version = executor.get_terraform_version()
    
    assert version is not None
    assert isinstance(version, str)
    assert len(version) > 0


def test_security_validation_blocks_dangerous_config(dangerous_terraform_config):
    """Test that dangerous configurations are blocked."""
    executor = TerraformExecutor()
    
    status, plan_json, error, output = executor.execute(dangerous_terraform_config)
    
    assert status == ExecutionStatus.FAILED
    assert plan_json is None
    assert error is not None
    assert "local-exec" in error.lower() or "provisioner" in error.lower()


def test_backend_blocking(backend_terraform_config):
    """Test that backend configurations are blocked."""
    executor = TerraformExecutor()
    
    status, plan_json, error, output = executor.execute(backend_terraform_config)
    
    assert status == ExecutionStatus.FAILED
    assert plan_json is None
    assert error is not None
    assert "backend" in error.lower()


# Note: Full execution test requires valid Terraform configuration
# and proper provider setup, which may not be available in test environment
