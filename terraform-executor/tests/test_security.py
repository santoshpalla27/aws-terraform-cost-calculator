"""Tests for security validator."""

import pytest
from pathlib import Path

from app.security import SecurityValidator


def test_valid_configuration(valid_terraform_config):
    """Test validation of valid configuration."""
    validator = SecurityValidator()
    is_valid, error = validator.validate_configuration(valid_terraform_config)
    
    assert is_valid is True
    assert error == ""


def test_blocked_provider_detection(dangerous_terraform_config):
    """Test detection of blocked providers."""
    validator = SecurityValidator()
    is_valid, error = validator.validate_configuration(dangerous_terraform_config)
    
    assert is_valid is False
    assert "local-exec" in error.lower() or "provisioner" in error.lower()


def test_backend_detection(backend_terraform_config):
    """Test detection of backend configuration."""
    validator = SecurityValidator()
    is_valid, error = validator.validate_configuration(backend_terraform_config)
    
    assert is_valid is False
    assert "backend" in error.lower()


def test_path_sanitization():
    """Test path sanitization."""
    validator = SecurityValidator()
    
    # Test path traversal
    dangerous_path = "../../../etc/passwd"
    sanitized = validator.sanitize_path(dangerous_path)
    assert ".." not in sanitized
    
    # Test null bytes
    dangerous_path = "file\x00.txt"
    sanitized = validator.sanitize_path(dangerous_path)
    assert "\x00" not in sanitized
