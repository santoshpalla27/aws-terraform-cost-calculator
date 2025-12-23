"""
Configuration management for AWS Metadata Resolver.
"""
from pydantic_settings import BaseSettings
from pydantic import Field
from typing import List


class Settings(BaseSettings):
    """Application settings."""
    
    # Environment
    environment: str = "development"
    
    # AWS Configuration
    aws_region: str = "us-east-1"
    aws_role_arn: str = ""
    
    # Cache Configuration (MUST be set via environment variables)
    redis_url: str = Field(..., env="REDIS_URL")
    metadata_cache_ttl: int = 3600  # 1 hour
    enable_cache: bool = True
    
    # API Configuration
    max_api_retries: int = 3
    api_retry_backoff: int = 2
    api_timeout: int = 30
    
    # Service Adapters
    enable_service_adapters: str = "ec2,ebs,elb,rds,eks,s3"
    
    # Logging
    log_level: str = "INFO"
    log_format: str = "json"
    
    # Service Authentication
    service_auth_token: str = "change-me-in-production"
    
    @property
    def enabled_adapters(self) -> List[str]:
        """Get list of enabled service adapters."""
        return [s.strip() for s in self.enable_service_adapters.split(',')]
    
    class Config:
        env_file = ".env"
        case_sensitive = False


settings = Settings()
