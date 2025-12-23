"""
Configuration management for API Gateway.
All configuration loaded from environment variables.
"""
from pydantic_settings import BaseSettings
from pydantic import Field
from typing import List


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # Server
    host: str = "0.0.0.0"
    port: int = 8000
    workers: int = 4
    
    # Authentication
    auth_enabled: bool = False
    jwt_secret: str = "change-me-in-production"
    jwt_algorithm: str = "HS256"
    jwt_expiration_minutes: int = 60
    
    # OIDC
    oidc_enabled: bool = False
    oidc_issuer: str = ""
    oidc_audience: str = ""
    oidc_client_id: str = ""
    
    # File Uploads
    max_upload_size: int = 52428800  # 50MB
    upload_dir: str = "/tmp/uploads"
    allowed_extensions: List[str] = [".tf", ".tfvars", ".zip"]
    
    # Rate Limiting
    rate_limit_enabled: bool = True
    rate_limit_requests: int = 100
    rate_limit_window: int = 60  # seconds
    
    # CORS
    cors_origins: List[str] = ["http://localhost:3000"]
    cors_allow_credentials: bool = True
    
    # Logging
    log_level: str = "INFO"
    log_format: str = "json"
    
    # Downstream Services (MUST be set via environment variables)
    job_orchestrator_url: str = Field(..., env="JOB_ORCHESTRATOR_URL")
    
    class Config:
        env_file = ".env"
        case_sensitive = False


# Global settings instance
settings = Settings()
