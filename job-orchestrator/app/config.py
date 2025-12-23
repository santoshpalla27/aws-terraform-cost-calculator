"""
Configuration management for Job Orchestrator.
All configuration loaded from environment variables.
"""
from pydantic_settings import BaseSettings
from pydantic import Field
from typing import Dict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # Database
    database_url: str = "postgresql+asyncpg://postgres:postgres@postgres:5432/cost_governance"
    
    # Redis
    redis_url: str = "redis://redis:6379/0"
    
    # Stage Timeouts (seconds)
    planning_timeout: int = 300
    parsing_timeout: int = 120
    enriching_timeout: int = 180
    costing_timeout: int = 60
    
    # Stage Retry Configuration
    planning_max_retries: int = 2
    parsing_max_retries: int = 2
    enriching_max_retries: int = 1
    costing_max_retries: int = 2
    
    # Job Configuration
    job_ttl: int = 3600  # 1 hour
    lock_ttl: int = 300  # 5 minutes
    worker_id: str = "orchestrator-1"
    
    # Downstream Services (MUST be set via environment variables)
    terraform_execution_url: str = Field(..., env="TERRAFORM_EXECUTOR_URL")
    plan_interpreter_url: str = Field(..., env="PLAN_INTERPRETER_URL")
    metadata_resolver_url: str = Field(..., env="METADATA_RESOLVER_URL")
    pricing_engine_url: str = Field(..., env="PRICING_ENGINE_URL")
    usage_modeling_url: str = Field(..., env="USAGE_ENGINE_URL")
    cost_aggregation_url: str = Field(..., env="COST_ENGINE_URL")
    
    # Service Authentication
    service_auth_token: str = "internal-service-token"
    
    # Logging
    log_level: str = "INFO"
    log_format: str = "json"
    
    # Server
    host: str = "0.0.0.0"
    port: int = 8001
    
    @property
    def stage_config(self) -> Dict[str, Dict[str, int]]:
        """Get stage configuration."""
        return {
            "PLANNING": {
                "timeout": self.planning_timeout,
                "max_retries": self.planning_max_retries,
                "backoff_base": 2,
            },
            "PARSING": {
                "timeout": self.parsing_timeout,
                "max_retries": self.parsing_max_retries,
                "backoff_base": 2,
            },
            "ENRICHING": {
                "timeout": self.enriching_timeout,
                "max_retries": self.enriching_max_retries,
                "backoff_base": 2,
            },
            "COSTING": {
                "timeout": self.costing_timeout,
                "max_retries": self.costing_max_retries,
                "backoff_base": 2,
            },
        }
    
    class Config:
        env_file = ".env"
        case_sensitive = False


# Global settings instance
settings = Settings()
