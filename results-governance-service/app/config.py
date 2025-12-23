"""
Configuration management for Results & Governance Service.
"""
from pydantic_settings import BaseSettings
from pydantic import Field
from pathlib import Path


class Settings(BaseSettings):
    """Application settings."""
    
    # Environment
    environment: str = "development"
    
    # Database (MUST be set via environment variables)
    database_url: str = Field(..., env="DATABASE_URL")
    
    # Audit
    enable_audit_log: bool = True
    
    # Policies
    policy_path: str = "./policies"
    
    # Retention
    retention_days: int = 365
    
    # Logging
    log_level: str = "INFO"
    log_format: str = "json"
    
    # API
    api_port: int = 8008
    
    class Config:
        env_file = ".env"
        case_sensitive = False
    
    def get_policies_directory(self) -> Path:
        """Get policies directory path."""
        return Path(self.policy_path)


# Global settings instance
settings = Settings()
