"""
Configuration management for Plan Interpreter.
NO runtime configuration - behavior must be deterministic.
"""
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings (minimal)."""
    
    # Server
    host: str = "0.0.0.0"
    port: int = 8003
    
    # Logging
    log_level: str = "INFO"
    log_format: str = "json"
    
    class Config:
        env_file = ".env"
        case_sensitive = False


# Global settings instance
settings = Settings()
