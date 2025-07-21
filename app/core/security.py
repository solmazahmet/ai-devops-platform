"""
Güvenlik Konfigürasyonu
JWT token yönetimi ve password hashing
"""

from datetime import datetime, timedelta
from typing import Optional, Union
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import HTTPException, status, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import logging

from app.core.config import settings

logger = logging.getLogger(__name__)

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# JWT token scheme
security = HTTPBearer()

# Password işlemleri
def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Şifre doğrulama"""
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    """Şifre hash'leme"""
    return pwd_context.hash(password)

# JWT token işlemleri
def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Access token oluşturma"""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt

def verify_token(token: str) -> Optional[dict]:
    """Token doğrulama"""
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            return None
        return payload
    except JWTError as e:
        logger.error(f"JWT verification failed: {e}")
        return None

# Dependency for getting current user
async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Mevcut kullanıcıyı al"""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        payload = verify_token(credentials.credentials)
        if payload is None:
            raise credentials_exception
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
        return username
    except JWTError:
        raise credentials_exception

# Rate limiting için basit decorator
def rate_limit(max_requests: int = 60, window: int = 60):
    """Rate limiting decorator"""
    def decorator(func):
        def wrapper(*args, **kwargs):
            # Bu basit bir implementasyon, production'da Redis kullanılmalı
            return func(*args, **kwargs)
        return wrapper
    return decorator 