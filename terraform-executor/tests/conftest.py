"""Pytest configuration and fixtures."""

import pytest
from pathlib import Path
from fastapi.testclient import TestClient

from app.main import app


@pytest.fixture
def client():
    """Test client fixture."""
    return TestClient(app)


@pytest.fixture
def valid_terraform_config(tmp_path):
    """Create a valid Terraform configuration."""
    tf_file = tmp_path / "main.tf"
    tf_file.write_text("""
terraform {
  required_version = ">= 1.0"
}

resource "aws_instance" "example" {
  ami           = "ami-0c55b159cbfafe1f0"
  instance_type = "t3.medium"
  
  tags = {
    Name = "Example"
  }
}

resource "aws_s3_bucket" "data" {
  bucket = "my-data-bucket"
}
""")
    return tmp_path


@pytest.fixture
def dangerous_terraform_config(tmp_path):
    """Create a Terraform configuration with blocked provider."""
    tf_file = tmp_path / "main.tf"
    tf_file.write_text("""
resource "null_resource" "dangerous" {
  provisioner "local-exec" {
    command = "echo 'This should be blocked'"
  }
}
""")
    return tmp_path


@pytest.fixture
def backend_terraform_config(tmp_path):
    """Create a Terraform configuration with backend."""
    tf_file = tmp_path / "main.tf"
    tf_file.write_text("""
terraform {
  backend "s3" {
    bucket = "my-terraform-state"
    key    = "state.tfstate"
    region = "us-east-1"
  }
}

resource "aws_instance" "example" {
  ami           = "ami-0c55b159cbfafe1f0"
  instance_type = "t3.medium"
}
""")
    return tmp_path
