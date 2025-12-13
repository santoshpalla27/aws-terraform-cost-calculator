"""Configuration management."""

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
    app_name: str = Field(default="AWS Metadata Resolver", description="Application name")
    app_version: str = Field(default="1.0.0", description="Application version")
    debug: bool = Field(default=False, description="Debug mode")
    
    # Server
    host: str = Field(default="0.0.0.0", description="Server host")
    port: int = Field(default=8003, description="Server port")
    
    # AWS
    aws_region: str = Field(default="us-east-1", description="Default AWS region")
    aws_profile: str = Field(default=None, description="AWS profile name")
    
    # Cache
    cache_ttl_ami: int = Field(default=3600, description="AMI cache TTL in seconds (1 hour)")
    cache_ttl_instance_type: int = Field(default=86400, description="Instance type cache TTL (24 hours)")
    cache_ttl_elb: int = Field(default=300, description="ELB cache TTL (5 minutes)")
    cache_ttl_eks: int = Field(default=900, description="EKS cache TTL (15 minutes)")
    cache_max_size: int = Field(default=1000, description="Maximum cache entries")
    
    # Graceful degradation
    enable_graceful_degradation: bool = Field(default=True, description="Enable graceful degradation")
    aws_timeout: int = Field(default=10, description="AWS API timeout in seconds")
    
    # Logging
    log_level: str = Field(default="INFO", description="Logging level")


# Global settings instance
settings = Settings()
