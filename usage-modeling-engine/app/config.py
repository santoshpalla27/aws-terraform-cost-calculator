"""
Configuration management for Usage Modeling Engine.
"""
from pydantic_settings import BaseSettings
from pathlib import Path


class Settings(BaseSettings):
    """Application settings."""
    
    # Environment
    environment: str = "development"
    
    # Usage Profiles
    default_usage_profile: str = "dev"
    profiles_path: str = "./profiles"
    enable_profile_reload: bool = False
    
    # Logging
    log_level: str = "INFO"
    log_format: str = "json"
    
    # API
    api_port: int = 8006
    
    class Config:
        env_file = ".env"
        case_sensitive = False
    
    def get_profiles_directory(self) -> Path:
        """Get profiles directory path."""
        return Path(self.profiles_path)


# Global settings instance
settings = Settings()
