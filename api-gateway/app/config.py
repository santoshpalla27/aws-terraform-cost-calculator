"""
Configuration management for API Gateway.
All configuration loaded from environment variables.
"""
from pydantic_settings import BaseSettings
from pydantic import Field, field_validator
from typing import List, Union


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
    # CRITICAL: Cannot use wildcard (*) with credentials=true
    # Must use explicit origin from environment variable
    cors_origins: Union[List[str], str] = "http://localhost:3000"
    cors_allow_credentials: bool = True
    
    @field_validator('cors_origins', mode='before')
    @classmethod
    def parse_cors_origins(cls, v):
        """Parse CORS origins from comma-separated string or list."""
        if isinstance(v, str):
            # Split by comma and strip whitespace
            return [origin.strip() for origin in v.split(',')]
        return v
    
    # Logging
    log_level: str = "INFO"
    log_format: str = "json"
    
    # Database
    database_url: str = Field(..., env="DATABASE_URL")
    
    # Downstream Services (MUST be set via environment variables)
    job_orchestrator_url: str = Field(..., env="JOB_ORCHESTRATOR_URL")
    usage_engine_url: str = Field(..., env="USAGE_ENGINE_URL")
    results_service_url: str = Field(default="http://results-service:8008", env="RESULTS_SERVICE_URL")
    
    # Service-to-service authentication (optional)
    service_auth_token: str = Field(default="", env="SERVICE_AUTH_TOKEN")
    
    class Config:
        env_file = ".env"
        case_sensitive = False


# Global settings instance
settings = Settings()
