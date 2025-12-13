"""Pytest configuration and fixtures."""

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.repositories.job_repository import InMemoryJobRepository


@pytest.fixture
def client():
    """Test client fixture."""
    return TestClient(app)


@pytest.fixture
def job_repository():
    """Job repository fixture."""
    return InMemoryJobRepository()


@pytest.fixture
def sample_terraform_file(tmp_path):
    """Create a sample Terraform file."""
    tf_file = tmp_path / "main.tf"
    tf_file.write_text("""
resource "aws_instance" "example" {
  ami           = "ami-0c55b159cbfafe1f0"
  instance_type = "t3.medium"
}
""")
    return tf_file


@pytest.fixture
def sample_terraform_zip(tmp_path, sample_terraform_file):
    """Create a sample Terraform ZIP file."""
    import zipfile
    
    zip_path = tmp_path / "terraform.zip"
    with zipfile.ZipFile(zip_path, 'w') as zf:
        zf.write(sample_terraform_file, arcname="main.tf")
    
    return zip_path
