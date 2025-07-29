"""
Uygulama Konfigürasyonu
Pydantic Settings ile environment değişkenlerini yönetme
"""

from pydantic_settings import BaseSettings
from typing import List, Optional, Dict, Any, Union
from datetime import datetime, timezone
import json
import os
import secrets
from pathlib import Path


class DateTimeEncoder(json.JSONEncoder):
    """Custom JSON encoder for datetime objects"""
    def default(self, obj):
        if isinstance(obj, datetime):
            if obj.tzinfo is None:
                obj = obj.replace(tzinfo=timezone.utc)
            return obj.isoformat()
        elif isinstance(obj, Path):
            return str(obj)
        elif hasattr(obj, 'dict'):  # Pydantic models
            return obj.dict()
        elif hasattr(obj, '__dict__'):  # Custom objects
            return obj.__dict__
        return super().default(obj)


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
    CORS_ORIGINS: List[str] = ["*"]
    CORS_ALLOW_CREDENTIALS: bool = True
    CORS_ALLOW_METHODS: List[str] = ["*"]
    CORS_ALLOW_HEADERS: List[str] = ["*"]
    
    # Database ayarları
    DATABASE_URL: str = "postgresql://postgres:password@localhost:5432/ai_devops_testing"
    TEST_DATABASE_URL: str = "postgresql://postgres:password@localhost:5432/ai_devops_testing_test"
    DATABASE_POOL_SIZE: int = 20
    DATABASE_MAX_OVERFLOW: int = 30
    DATABASE_POOL_TIMEOUT: int = 30
    DATABASE_POOL_RECYCLE: int = 3600
    
    # Redis ayarları
    REDIS_URL: str = "redis://localhost:6379/0"
    REDIS_MAX_CONNECTIONS: int = 10
    REDIS_SOCKET_TIMEOUT: int = 5
    REDIS_SOCKET_CONNECT_TIMEOUT: int = 5
    
    # Security ayarları
    SECRET_KEY: str = "your-secret-key-change-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    PASSWORD_MIN_LENGTH: int = 8
    PASSWORD_REQUIRE_UPPERCASE: bool = True
    PASSWORD_REQUIRE_LOWERCASE: bool = True
    PASSWORD_REQUIRE_DIGITS: bool = True
    PASSWORD_REQUIRE_SPECIAL_CHARS: bool = True
    
    # OpenAI ayarları
    OPENAI_API_KEY: Optional[str] = None
    OPENAI_API_BASE: str = "https://api.openai.com/v1"
    OPENAI_MODEL: str = "gpt-3.5-turbo"
    OPENAI_MAX_TOKENS: int = 2000
    OPENAI_TEMPERATURE: float = 0.7
    OPENAI_MAX_RETRIES: int = 3
    OPENAI_RETRY_DELAY: float = 1.0
    OPENAI_TIMEOUT: int = 30
    
    # Jira ayarları
    JIRA_SERVER_URL: Optional[str] = None
    JIRA_USERNAME: Optional[str] = None
    JIRA_API_TOKEN: Optional[str] = None
    JIRA_PROJECT_KEY: str = "TEST"
    JIRA_TIMEOUT: int = 30
    JIRA_MAX_RETRIES: int = 3
    
    # Celery ayarları
    CELERY_BROKER_URL: str = "redis://localhost:6379/0"
    CELERY_RESULT_BACKEND: str = "redis://localhost:6379/0"
    CELERY_TASK_SERIALIZER: str = "json"
    CELERY_RESULT_SERIALIZER: str = "json"
    CELERY_ACCEPT_CONTENT: List[str] = ["json"]
    CELERY_TIMEZONE: str = "UTC"
    CELERY_ENABLE_UTC: bool = True
    CELERY_TASK_TRACK_STARTED: bool = True
    CELERY_TASK_TIME_LIMIT: int = 30 * 60  # 30 minutes
    CELERY_TASK_SOFT_TIME_LIMIT: int = 25 * 60  # 25 minutes
    
    # Rate limiting
    RATE_LIMIT_PER_MINUTE: int = 60
    RATE_LIMIT_PER_HOUR: int = 1000
    RATE_LIMIT_PER_DAY: int = 10000
    
    # File upload ayarları
    MAX_FILE_SIZE: int = 10 * 1024 * 1024  # 10MB
    ALLOWED_FILE_TYPES: List[str] = ["jpg", "jpeg", "png", "gif", "pdf", "txt", "json"]
    UPLOAD_DIR: str = "uploads"
    
    # Logging ayarları
    LOG_FORMAT: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    LOG_FILE: Optional[str] = None
    LOG_MAX_SIZE: int = 10 * 1024 * 1024  # 10MB
    LOG_BACKUP_COUNT: int = 5
    
    # Monitoring ayarları
    ENABLE_METRICS: bool = True
    METRICS_PORT: int = 9090
    HEALTH_CHECK_INTERVAL: int = 30
    
    # Cache ayarları
    CACHE_TTL: int = 300  # 5 minutes
    CACHE_MAX_SIZE: int = 1000
    CACHE_ENABLE: bool = True
    
    # Test ayarları
    TEST_TIMEOUT: int = 300  # 5 minutes
    TEST_SCREENSHOT_DIR: str = "test_results/screenshots"
    TEST_REPORT_DIR: str = "test_results"
    TEST_PARALLEL_WORKERS: int = 4
    
    class Config:
        env_file = ".env"
        case_sensitive = True
        env_file_encoding = "utf-8"
        
        @classmethod
        def customise_sources(cls, init_settings, env_settings, file_secret_settings):
            return (
                init_settings,
                env_settings,
                file_secret_settings,
            )


# Settings instance
settings = Settings()

# Custom JSON encoder instance
json_encoder = DateTimeEncoder()


def generate_secret_key() -> str:
    """Güvenli secret key oluştur"""
    return secrets.token_urlsafe(32)


def validate_settings() -> None:
    """Kritik ayarları doğrula ve güvenlik kontrollerini yap"""
    errors = []
    
    # Production güvenlik kontrolleri
    if settings.ENVIRONMENT == "production":
        if not settings.SECRET_KEY or settings.SECRET_KEY == "your-secret-key-change-in-production":
            errors.append("Production ortamında SECRET_KEY ayarlanmalıdır")
        
        if len(settings.SECRET_KEY) < 32:
            errors.append("SECRET_KEY en az 32 karakter olmalıdır")
        
        if not settings.OPENAI_API_KEY:
            errors.append("Production ortamında OPENAI_API_KEY ayarlanmalıdır")
        
        if not settings.JIRA_SERVER_URL:
            errors.append("Production ortamında JIRA_SERVER_URL ayarlanmalıdır")
        
        if settings.DEBUG:
            errors.append("Production ortamında DEBUG=False olmalıdır")
        
        if "*" in settings.CORS_ORIGINS:
            errors.append("Production ortamında CORS_ORIGINS wildcard kullanılmamalıdır")
    
    # OpenAI API Key kontrolü (kritik)
    if not settings.OPENAI_API_KEY:
        errors.append("OPENAI_API_KEY gereklidir")
    
    # Database URL kontrolü
    if not settings.DATABASE_URL:
        errors.append("DATABASE_URL ayarlanmalıdır")
    
    # Redis URL kontrolü
    if not settings.REDIS_URL:
        errors.append("REDIS_URL ayarlanmalıdır")
    
    # Port kontrolü
    if not (1024 <= settings.PORT <= 65535):
        errors.append("PORT 1024-65535 arasında olmalıdır")
    
    # Timeout kontrolü
    if settings.OPENAI_TIMEOUT <= 0:
        errors.append("OPENAI_TIMEOUT pozitif olmalıdır")
    
    if settings.JIRA_TIMEOUT <= 0:
        errors.append("JIRA_TIMEOUT pozitif olmalıdır")
    
    # Rate limit kontrolü
    if settings.RATE_LIMIT_PER_MINUTE <= 0:
        errors.append("RATE_LIMIT_PER_MINUTE pozitif olmalıdır")
    
    # File size kontrolü
    if settings.MAX_FILE_SIZE <= 0:
        errors.append("MAX_FILE_SIZE pozitif olmalıdır")
    
    if errors:
        raise ValueError(f"Konfigürasyon hataları: {'; '.join(errors)}")


def get_database_config() -> Dict[str, Any]:
    """Database konfigürasyonunu döndür"""
    return {
        "url": settings.DATABASE_URL,
        "pool_size": settings.DATABASE_POOL_SIZE,
        "max_overflow": settings.DATABASE_MAX_OVERFLOW,
        "pool_timeout": settings.DATABASE_POOL_TIMEOUT,
        "pool_recycle": settings.DATABASE_POOL_RECYCLE,
        "echo": settings.DEBUG
    }


def get_redis_config() -> Dict[str, Any]:
    """Redis konfigürasyonunu döndür"""
    return {
        "url": settings.REDIS_URL,
        "max_connections": settings.REDIS_MAX_CONNECTIONS,
        "socket_timeout": settings.REDIS_SOCKET_TIMEOUT,
        "socket_connect_timeout": settings.REDIS_SOCKET_CONNECT_TIMEOUT
    }


def get_celery_config() -> Dict[str, Any]:
    """Celery konfigürasyonunu döndür"""
    return {
        "broker_url": settings.CELERY_BROKER_URL,
        "result_backend": settings.CELERY_RESULT_BACKEND,
        "task_serializer": settings.CELERY_TASK_SERIALIZER,
        "result_serializer": settings.CELERY_RESULT_SERIALIZER,
        "accept_content": settings.CELERY_ACCEPT_CONTENT,
        "timezone": settings.CELERY_TIMEZONE,
        "enable_utc": settings.CELERY_ENABLE_UTC,
        "task_track_started": settings.CELERY_TASK_TRACK_STARTED,
        "task_time_limit": settings.CELERY_TASK_TIME_LIMIT,
        "task_soft_time_limit": settings.CELERY_TASK_SOFT_TIME_LIMIT
    }


def get_openai_config() -> Dict[str, Any]:
    """OpenAI konfigürasyonunu döndür"""
    return {
        "api_key": settings.OPENAI_API_KEY,
        "api_base": settings.OPENAI_API_BASE,
        "model": settings.OPENAI_MODEL,
        "max_tokens": settings.OPENAI_MAX_TOKENS,
        "temperature": settings.OPENAI_TEMPERATURE,
        "max_retries": settings.OPENAI_MAX_RETRIES,
        "retry_delay": settings.OPENAI_RETRY_DELAY,
        "timeout": settings.OPENAI_TIMEOUT
    }


def get_jira_config() -> Dict[str, Any]:
    """Jira konfigürasyonunu döndür"""
    return {
        "server_url": settings.JIRA_SERVER_URL,
        "username": settings.JIRA_USERNAME,
        "api_token": settings.JIRA_API_TOKEN,
        "project_key": settings.JIRA_PROJECT_KEY,
        "timeout": settings.JIRA_TIMEOUT,
        "max_retries": settings.JIRA_MAX_RETRIES
    }


def get_security_config() -> Dict[str, Any]:
    """Security konfigürasyonunu döndür"""
    return {
        "secret_key": settings.SECRET_KEY,
        "algorithm": settings.ALGORITHM,
        "access_token_expire_minutes": settings.ACCESS_TOKEN_EXPIRE_MINUTES,
        "refresh_token_expire_days": settings.REFRESH_TOKEN_EXPIRE_DAYS,
        "password_min_length": settings.PASSWORD_MIN_LENGTH,
        "password_require_uppercase": settings.PASSWORD_REQUIRE_UPPERCASE,
        "password_require_lowercase": settings.PASSWORD_REQUIRE_LOWERCASE,
        "password_require_digits": settings.PASSWORD_REQUIRE_DIGITS,
        "password_require_special_chars": settings.PASSWORD_REQUIRE_SPECIAL_CHARS
    }


def get_cors_config() -> Dict[str, Any]:
    """CORS konfigürasyonunu döndür"""
    return {
        "allow_origins": settings.CORS_ORIGINS,
        "allow_credentials": settings.CORS_ALLOW_CREDENTIALS,
        "allow_methods": settings.CORS_ALLOW_METHODS,
        "allow_headers": settings.CORS_ALLOW_HEADERS
    }


def get_rate_limit_config() -> Dict[str, Any]:
    """Rate limiting konfigürasyonunu döndür"""
    return {
        "per_minute": settings.RATE_LIMIT_PER_MINUTE,
        "per_hour": settings.RATE_LIMIT_PER_HOUR,
        "per_day": settings.RATE_LIMIT_PER_DAY
    }


# Ayarları doğrula
validate_settings() 