"""
Configuration management for Pricing Engine.
"""
from pydantic_settings import BaseSettings
from typing import List


class Settings(BaseSettings):
    """Application settings."""
    
    # Environment
    environment: str = "development"
    
    # Pricing API
    pricing_api_base_url: str = "https://pricing.us-east-1.amazonaws.com"
    pricing_cache_ttl: int = 86400  # 24 hours
    max_price_api_retries: int = 3
    
    # Supported Services (ONLY implemented normalizers)
    supported_services: str = "ec2,ebs,elb,rds"
    
    # Cache
    redis_url: str = "redis://localhost:6379/1"
    enable_cache: bool = True
    
    # Logging
    log_level: str = "INFO"
    log_format: str = "json"
    
    # API
    api_port: int = 8005
    
    class Config:
        env_file = ".env"
        case_sensitive = False
    
    def get_supported_services_list(self) -> List[str]:
        """Get list of supported services."""
        return [s.strip() for s in self.supported_services.split(',')]


# Global settings instance
settings = Settings()
