from pydantic_settings import BaseSettings
from pydantic import field_validator
from typing import List, Optional
import os

class Settings(BaseSettings):
    # API Configuration
    API_V1_STR: str = "/api/v1"
    PROJECT_NAME: str = "Business Systems Integration Platform"
    
    # Server Configuration
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    DEBUG: bool = True
    
    # Environment
    ENVIRONMENT: str = "development"
    LOG_LEVEL: str = "INFO"
    
    # Database Configuration
    DATABASE_URL: str = "sqlite:///./business_platform.db"
    SUPABASE_URL: Optional[str] = None
    SUPABASE_ANON_KEY: Optional[str] = None
    SUPABASE_SERVICE_ROLE_KEY: Optional[str] = None
    
    # AI Configuration
    OPENAI_API_KEY: Optional[str] = None
    ANTHROPIC_API_KEY: Optional[str] = None
    
    # Kafka Configuration
    KAFKA_BOOTSTRAP_SERVERS: str = "localhost:9092"
    KAFKA_TOPIC_PREFIX: str = "business_platform"
    
    # Redis Configuration
    REDIS_URL: str = "redis://localhost:6380"
    
    # Security
    SECRET_KEY: str = "change-this-in-production-use-env-file"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    # CORS
    CORS_ORIGINS: List[str] = ["http://localhost:3000", "http://localhost:3001"]
    ALLOWED_HOSTS: List[str] = ["*"]
    
    # Integration Templates
    INTEGRATION_TEMPLATES_PATH: str = "./templates"
    
    # Rate Limiting
    RATE_LIMIT_PER_MINUTE: int = 100
    
    @field_validator("CORS_ORIGINS", mode='before')
    @classmethod
    def assemble_cors_origins(cls, v):
        if isinstance(v, str):
            return [i.strip() for i in v.split(",")]
        return v
    
    @field_validator("ALLOWED_HOSTS", mode='before')
    @classmethod
    def assemble_allowed_hosts(cls, v):
        if isinstance(v, str):
            return [i.strip() for i in v.split(",")]
        return v
    
    model_config = {
        "env_file": ".env",
        "case_sensitive": True
    }

# Create settings instance
settings = Settings()

# Validate required settings in production
if settings.ENVIRONMENT == "production":
    required_keys = ["SECRET_KEY", "SUPABASE_URL", "SUPABASE_SERVICE_ROLE_KEY"]
    for key in required_keys:
        if not getattr(settings, key) or getattr(settings, key).startswith("your-"):
            raise ValueError(f"Missing required production setting: {key}")
