"""
User Models
Authentication and user management models
"""

from sqlalchemy import Column, Integer, String, DateTime, Boolean, JSON, Text, Enum as SQLEnum
from sqlalchemy.sql import func
from datetime import datetime, timezone
from enum import Enum
from typing import Dict, Any, Optional, List
from pydantic import BaseModel, EmailStr, Field

from app.core.database import Base

class UserRole(str, Enum):
    """User roles enum"""
    ADMIN = "admin"
    MANAGER = "manager" 
    DEVELOPER = "developer"
    VIEWER = "viewer"
    GUEST = "guest"

class AuthProvider(str, Enum):
    """Authentication providers"""
    LOCAL = "local"
    GOOGLE = "google"
    GITHUB = "github"
    MICROSOFT = "microsoft"
    AZURE = "azure"

class User(Base):
    """User model for authentication and authorization"""
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    username = Column(String(100), unique=True, index=True, nullable=True)
    full_name = Column(String(255), nullable=True)
    
    # Authentication
    hashed_password = Column(String(255), nullable=True)  # For local auth
    is_active = Column(Boolean, default=True)
    is_verified = Column(Boolean, default=False)
    is_superuser = Column(Boolean, default=False)
    
    # OAuth providers
    auth_provider = Column(SQLEnum(AuthProvider), default=AuthProvider.LOCAL)
    provider_id = Column(String(255), nullable=True)  # Provider-specific user ID
    provider_data = Column(JSON, nullable=True)  # Additional provider data
    
    # Role and permissions
    role = Column(SQLEnum(UserRole), default=UserRole.VIEWER)
    permissions = Column(JSON, nullable=True)  # Custom permissions
    
    # Profile information
    avatar_url = Column(String(500), nullable=True)
    bio = Column(Text, nullable=True)
    company = Column(String(255), nullable=True)
    location = Column(String(255), nullable=True)
    website = Column(String(500), nullable=True)
    
    # Activity tracking
    last_login = Column(DateTime(timezone=True), nullable=True)
    login_count = Column(Integer, default=0)
    
    # API access
    api_key = Column(String(255), unique=True, nullable=True, index=True)
    api_key_expires_at = Column(DateTime(timezone=True), nullable=True)
    rate_limit_tier = Column(String(50), default="standard")  # basic, standard, premium
    
    # Preferences
    preferences = Column(JSON, nullable=True)  # User preferences
    timezone = Column(String(50), default="UTC")
    language = Column(String(10), default="en")
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    deleted_at = Column(DateTime(timezone=True), nullable=True)  # Soft delete

class UserSession(Base):
    """User session tracking"""
    __tablename__ = "user_sessions"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, nullable=False, index=True)
    session_token = Column(String(255), unique=True, nullable=False, index=True)
    refresh_token = Column(String(255), unique=True, nullable=True, index=True)
    
    # Session details
    ip_address = Column(String(45), nullable=True)
    user_agent = Column(Text, nullable=True)
    device_info = Column(JSON, nullable=True)
    location_info = Column(JSON, nullable=True)
    
    # Session status
    is_active = Column(Boolean, default=True)
    expires_at = Column(DateTime(timezone=True), nullable=False)
    last_activity = Column(DateTime(timezone=True), server_default=func.now())
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

class OAuthState(Base):
    """OAuth state tracking for security"""
    __tablename__ = "oauth_states"
    
    id = Column(Integer, primary_key=True, index=True)
    state = Column(String(255), unique=True, nullable=False, index=True)
    provider = Column(SQLEnum(AuthProvider), nullable=False)
    
    # Request details
    redirect_uri = Column(String(500), nullable=True)
    scopes = Column(JSON, nullable=True)
    
    # Security
    ip_address = Column(String(45), nullable=True)
    user_agent = Column(Text, nullable=True)
    
    # Status
    used = Column(Boolean, default=False)
    expires_at = Column(DateTime(timezone=True), nullable=False)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())

# Pydantic schemas for API

class UserBase(BaseModel):
    """Base user schema"""
    email: EmailStr
    username: Optional[str] = None
    full_name: Optional[str] = None
    role: UserRole = UserRole.VIEWER
    is_active: bool = True

class UserCreate(UserBase):
    """User creation schema"""
    password: Optional[str] = Field(None, min_length=8, max_length=100)
    auth_provider: AuthProvider = AuthProvider.LOCAL
    
class UserUpdate(BaseModel):
    """User update schema"""
    email: Optional[EmailStr] = None
    username: Optional[str] = None
    full_name: Optional[str] = None
    bio: Optional[str] = None
    company: Optional[str] = None
    location: Optional[str] = None
    website: Optional[str] = None
    avatar_url: Optional[str] = None
    timezone: Optional[str] = None
    language: Optional[str] = None
    preferences: Optional[Dict[str, Any]] = None

class UserResponse(UserBase):
    """User response schema"""
    id: int
    is_verified: bool
    is_superuser: bool
    auth_provider: AuthProvider
    avatar_url: Optional[str]
    bio: Optional[str]
    company: Optional[str]
    location: Optional[str]
    website: Optional[str]
    last_login: Optional[datetime]
    login_count: int
    rate_limit_tier: str
    timezone: str
    language: str
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

class UserProfile(BaseModel):
    """User profile schema"""
    id: int
    email: str
    username: Optional[str]
    full_name: Optional[str]
    role: UserRole
    avatar_url: Optional[str]
    bio: Optional[str]
    company: Optional[str]
    location: Optional[str]
    website: Optional[str]
    is_verified: bool
    auth_provider: AuthProvider
    created_at: datetime

class LoginRequest(BaseModel):
    """Login request schema"""
    email: EmailStr
    password: str = Field(..., min_length=1)
    remember_me: bool = False

class LoginResponse(BaseModel):
    """Login response schema"""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int
    user: UserProfile

class TokenResponse(BaseModel):
    """Token response schema"""
    access_token: str
    refresh_token: Optional[str] = None
    token_type: str = "bearer"
    expires_in: int

class OAuthLoginRequest(BaseModel):
    """OAuth login request schema"""
    provider: AuthProvider
    redirect_uri: Optional[str] = None
    scopes: Optional[List[str]] = None

class OAuthCallback(BaseModel):
    """OAuth callback schema"""
    code: str
    state: str
    provider: AuthProvider

class APIKeyRequest(BaseModel):
    """API key generation request"""
    name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = None
    expires_in_days: int = Field(365, ge=1, le=3650)  # 1 day to 10 years
    permissions: Optional[List[str]] = None

class APIKeyResponse(BaseModel):
    """API key response"""
    key: str
    name: str
    description: Optional[str]
    expires_at: datetime
    permissions: Optional[List[str]]
    created_at: datetime

class UserStats(BaseModel):
    """User statistics"""
    total_tests: int = 0
    tests_passed: int = 0
    tests_failed: int = 0
    success_rate: float = 0.0
    total_test_time: float = 0.0
    avg_test_time: float = 0.0
    favorite_platforms: List[Dict[str, Any]] = []
    recent_activity: List[Dict[str, Any]] = []
    achievements: List[Dict[str, Any]] = []

class TeamInvite(BaseModel):
    """Team invite schema"""
    email: EmailStr
    role: UserRole = UserRole.VIEWER
    message: Optional[str] = None
    expires_in_days: int = Field(7, ge=1, le=30)

class PasswordResetRequest(BaseModel):
    """Password reset request"""
    email: EmailStr

class PasswordReset(BaseModel):
    """Password reset confirmation"""
    token: str
    new_password: str = Field(..., min_length=8, max_length=100)

class ChangePasswordRequest(BaseModel):
    """Change password request"""
    current_password: str
    new_password: str = Field(..., min_length=8, max_length=100)