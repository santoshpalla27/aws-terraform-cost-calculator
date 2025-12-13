"""Configuration management."""

from typing import List
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings."""
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )
    
    # Application
    app_name: str = Field(default="Terraform Executor", description="Application name")
    app_version: str = Field(default="1.0.0", description="Application version")
    debug: bool = Field(default=False, description="Debug mode")
    
    # Server
    host: str = Field(default="0.0.0.0", description="Server host")
    port: int = Field(default=8001, description="Server port")
    
    # Execution Settings
    execution_timeout: int = Field(default=300, description="Execution timeout in seconds")
    workspace_dir: str = Field(default="/tmp/workspace", description="Workspace directory")
    max_plan_size_mb: int = Field(default=50, description="Maximum plan size in MB")
    
    @property
    def max_plan_size_bytes(self) -> int:
        """Convert MB to bytes."""
        return self.max_plan_size_mb * 1024 * 1024
    
    # Security Settings
    allow_network: bool = Field(default=True, description="Allow network access during execution")
    blocked_providers: str = Field(
        default="local-exec,external,null",
        description="Comma-separated list of blocked providers"
    )
    
    @property
    def blocked_providers_list(self) -> List[str]:
        """Parse blocked providers into a list."""
        return [p.strip() for p in self.blocked_providers.split(",")]
    
    # Upload Settings
    upload_base_dir: str = Field(default="/uploads", description="Base directory for uploads")
    
    # Logging
    log_level: str = Field(default="INFO", description="Logging level")
    log_format: str = Field(default="json", description="Log format: json or text")


# Global settings instance
settings = Settings()
