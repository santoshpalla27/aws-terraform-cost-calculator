"""
Configuration management for Terraform Executor.
All configuration loaded from environment variables.
"""
from pydantic_settings import BaseSettings
from typing import List


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # Terraform
    terraform_version: str = "1.6.0"
    
    # Resource Limits
    max_execution_time: int = 300  # seconds
    cpu_limit: int = 2  # cores
    memory_limit: int = 2048  # MB
    max_workspace_size: int = 100  # MB
    
    # Security
    allowed_providers: List[str] = ["aws", "random", "null"]
    block_local_exec: bool = True
    block_external_data: bool = True
    
    # Workspace
    workspace_base_dir: str = "/tmp/terraform-workspaces"
    
    # Logging
    log_level: str = "INFO"
    log_format: str = "json"
    
    # Server
    host: str = "0.0.0.0"
    port: int = 8002
    
    class Config:
        env_file = ".env"
        case_sensitive = False


# Global settings instance
settings = Settings()
