"""
Uygulama Konfigürasyonu
Pydantic Settings ile environment değişkenlerini yönetme
"""

from pydantic_settings import BaseSettings
from typing import List, Optional
import os


class Settings(BaseSettings):
    # Uygulama ayarları
    APP_NAME: str = "AI DevOps Testing Platform"
    VERSION: str = "1.0.0"
    DEBUG: bool = False
    ENVIRONMENT: str = "development"
    LOG_LEVEL: str = "INFO"
    
    # Server ayarları
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    ALLOWED_HOSTS: List[str] = ["*"]
    
    # Database ayarları
    DATABASE_URL: str = "postgresql://postgres:password@localhost:5432/ai_devops_testing"
    TEST_DATABASE_URL: str = "postgresql://postgres:password@localhost:5432/ai_devops_testing_test"
    
    # Redis ayarları
    REDIS_URL: str = "redis://localhost:6379/0"
    
    # Security ayarları
    SECRET_KEY: str = "your-secret-key-change-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    # OpenAI ayarları
    OPENAI_API_KEY: Optional[str] = None
    OPENAI_MODEL: str = "gpt-4"
    OPENAI_MAX_TOKENS: int = 2000
    OPENAI_TEMPERATURE: float = 0.7
    
    # Jira ayarları
    JIRA_SERVER_URL: Optional[str] = None
    JIRA_USERNAME: Optional[str] = None
    JIRA_API_TOKEN: Optional[str] = None
    JIRA_PROJECT_KEY: str = "TEST"
    
    # Celery ayarları
    CELERY_BROKER_URL: str = "redis://localhost:6379/0"
    CELERY_RESULT_BACKEND: str = "redis://localhost:6379/0"
    
    # Rate limiting
    RATE_LIMIT_PER_MINUTE: int = 60
    
    class Config:
        env_file = ".env"
        case_sensitive = True


# Settings instance
settings = Settings()

# Environment değişkenlerini kontrol et
def validate_settings():
    """Kritik ayarları doğrula"""
    if settings.ENVIRONMENT == "production":
        if not settings.SECRET_KEY or settings.SECRET_KEY == "your-secret-key-change-in-production":
            raise ValueError("Production ortamında SECRET_KEY ayarlanmalıdır")
        
        if not settings.OPENAI_API_KEY:
            raise ValueError("Production ortamında OPENAI_API_KEY ayarlanmalıdır")
        
        if not settings.JIRA_SERVER_URL:
            raise ValueError("Production ortamında JIRA_SERVER_URL ayarlanmalıdır")

# Ayarları doğrula
validate_settings() 