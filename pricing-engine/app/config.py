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
    app_name: str = Field(default="AWS Pricing Engine", description="Application name")
    app_version: str = Field(default="1.0.0", description="Application version")
    debug: bool = Field(default=False, description="Debug mode")
    
    # Server
    host: str = Field(default="0.0.0.0", description="Server host")
    port: int = Field(default=8004, description="Server port")
    
    # Database
    database_url: str = Field(
        default="postgresql://postgres:postgres@localhost:5432/pricing",
        description="PostgreSQL connection URL"
    )
    
    # AWS Price List API
    price_list_base_url: str = Field(
        default="https://pricing.us-east-1.amazonaws.com",
        description="AWS Price List API base URL"
    )
    
    # Ingestion
    target_services: list = Field(
        default=["AmazonEC2", "AmazonS3", "AmazonRDS", "AmazonEKS", "AWSELB"],
        description="Services to ingest"
    )
    batch_size: int = Field(default=1000, description="Batch insert size")
    
    # Logging
    log_level: str = Field(default="INFO", description="Logging level")


# Global settings instance
settings = Settings()
