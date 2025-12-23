"""
Configuration management for Cost Aggregation Engine.
"""
from pydantic_settings import BaseSettings
from decimal import Decimal, getcontext


class Settings(BaseSettings):
    """Application settings."""
    
    # Environment
    environment: str = "development"
    
    # Currency
    default_currency: str = "USD"
    
    # Decimal Precision
    decimal_precision: int = 28
    
    # Determinism
    enable_determinism_hash: bool = True
    
    # Logging
    log_level: str = "INFO"
    log_format: str = "json"
    
    # API
    api_port: int = 8007
    
    class Config:
        env_file = ".env"
        case_sensitive = False
    
    def configure_decimal_context(self):
        """Configure decimal context for financial calculations."""
        getcontext().prec = self.decimal_precision


# Global settings instance
settings = Settings()

# Configure decimal context on import
settings.configure_decimal_context()
