"""
Authentication Service
OAuth2, JWT, and user management service
"""

import secrets
import hashlib
import logging
from datetime import datetime, timedelta, timezone
from typing import Dict, Optional, List, Any, Union
from urllib.parse import urlencode, urlparse
import aiohttp
import jwt
from passlib.context import CryptContext
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, and_, or_
from sqlalchemy.orm import selectinload

from app.core.database import get_db_session
from app.core.config import settings
from app.models.user import (
    User, UserSession, OAuthState, UserRole, AuthProvider,
    UserCreate, UserUpdate, LoginRequest, OAuthCallback,
    APIKeyRequest, UserStats
)

logger = logging.getLogger(__name__)

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# JWT settings
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30
REFRESH_TOKEN_EXPIRE_DAYS = 7

class AuthService:
    """Comprehensive authentication service"""
    
    def __init__(self):
        self.oauth_configs = {
            AuthProvider.GOOGLE: {
                "client_id": getattr(settings, 'GOOGLE_CLIENT_ID', ''),
                "client_secret": getattr(settings, 'GOOGLE_CLIENT_SECRET', ''),
                "auth_url": "https://accounts.google.com/o/oauth2/v2/auth",
                "token_url": "https://oauth2.googleapis.com/token",
                "user_info_url": "https://www.googleapis.com/oauth2/v2/userinfo",
                "scopes": ["openid", "email", "profile"]
            },
            AuthProvider.GITHUB: {
                "client_id": getattr(settings, 'GITHUB_CLIENT_ID', ''),
                "client_secret": getattr(settings, 'GITHUB_CLIENT_SECRET', ''),
                "auth_url": "https://github.com/login/oauth/authorize",
                "token_url": "https://github.com/login/oauth/access_token",
                "user_info_url": "https://api.github.com/user",
                "scopes": ["user:email"]
            },
            AuthProvider.MICROSOFT: {
                "client_id": getattr(settings, 'MICROSOFT_CLIENT_ID', ''),
                "client_secret": getattr(settings, 'MICROSOFT_CLIENT_SECRET', ''),
                "auth_url": "https://login.microsoftonline.com/common/oauth2/v2.0/authorize",
                "token_url": "https://login.microsoftonline.com/common/oauth2/v2.0/token",
                "user_info_url": "https://graph.microsoft.com/v1.0/me",
                "scopes": ["openid", "profile", "email"]
            }
        }
    
    # Password utilities
    def hash_password(self, password: str) -> str:
        """Hash password using bcrypt"""
        return pwd_context.hash(password)
    
    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """Verify password against hash"""
        return pwd_context.verify(plain_password, hashed_password)
    
    def generate_api_key(self) -> str:
        """Generate secure API key"""
        return f"aip_{secrets.token_urlsafe(32)}"
    
    # JWT utilities
    def create_access_token(self, data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
        """Create JWT access token"""
        to_encode = data.copy()
        
        if expires_delta:
            expire = datetime.now(timezone.utc) + expires_delta
        else:
            expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        
        to_encode.update({"exp": expire, "type": "access"})
        encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=ALGORITHM)
        return encoded_jwt
    
    def create_refresh_token(self, data: Dict[str, Any]) -> str:
        """Create JWT refresh token"""
        to_encode = data.copy()
        expire = datetime.now(timezone.utc) + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
        to_encode.update({"exp": expire, "type": "refresh"})
        encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=ALGORITHM)
        return encoded_jwt
    
    def verify_token(self, token: str, token_type: str = "access") -> Optional[Dict[str, Any]]:
        """Verify and decode JWT token"""
        try:
            payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[ALGORITHM])
            
            if payload.get("type") != token_type:
                return None
            
            return payload
            
        except jwt.ExpiredSignatureError:
            logger.warning("Token has expired")
            return None
        except jwt.JWTError as e:
            logger.warning(f"JWT error: {e}")
            return None
    
    # User management
    async def create_user(self, user_data: UserCreate, request_info: Dict[str, Any] = None) -> User:
        """Create new user"""
        async with get_db_session() as session:
            # Check if user already exists
            existing_user = await session.execute(
                select(User).where(User.email == user_data.email)
            )
            if existing_user.scalar_one_or_none():
                raise ValueError("User with this email already exists")
            
            # Hash password if provided
            hashed_password = None
            if user_data.password:
                hashed_password = self.hash_password(user_data.password)
            
            # Create user
            user = User(
                email=user_data.email,
                username=user_data.username,
                full_name=user_data.full_name,
                hashed_password=hashed_password,
                role=user_data.role,
                auth_provider=user_data.auth_provider,
                is_verified=user_data.auth_provider != AuthProvider.LOCAL  # OAuth users are auto-verified
            )
            
            session.add(user)
            await session.commit()
            await session.refresh(user)
            
            logger.info(f"User created: {user.email} (ID: {user.id})")
            return user
    
    async def authenticate_user(self, email: str, password: str) -> Optional[User]:
        """Authenticate user with email and password"""
        async with get_db_session() as session:
            result = await session.execute(
                select(User).where(
                    and_(
                        User.email == email,
                        User.is_active == True,
                        User.auth_provider == AuthProvider.LOCAL
                    )
                )
            )
            user = result.scalar_one_or_none()
            
            if user and user.hashed_password and self.verify_password(password, user.hashed_password):
                # Update login stats
                await self.update_login_stats(user.id)
                return user
            
            return None
    
    async def get_user_by_id(self, user_id: int) -> Optional[User]:
        """Get user by ID"""
        async with get_db_session() as session:
            result = await session.execute(
                select(User).where(User.id == user_id)
            )
            return result.scalar_one_or_none()
    
    async def get_user_by_email(self, email: str) -> Optional[User]:
        """Get user by email"""
        async with get_db_session() as session:
            result = await session.execute(
                select(User).where(User.email == email)
            )
            return result.scalar_one_or_none()
    
    async def get_user_by_api_key(self, api_key: str) -> Optional[User]:
        """Get user by API key"""
        async with get_db_session() as session:
            result = await session.execute(
                select(User).where(
                    and_(
                        User.api_key == api_key,
                        User.is_active == True,
                        or_(
                            User.api_key_expires_at.is_(None),
                            User.api_key_expires_at > datetime.now(timezone.utc)
                        )
                    )
                )
            )
            return result.scalar_one_or_none()
    
    async def update_user(self, user_id: int, user_data: UserUpdate) -> Optional[User]:
        """Update user information"""
        async with get_db_session() as session:
            result = await session.execute(
                select(User).where(User.id == user_id)
            )
            user = result.scalar_one_or_none()
            
            if not user:
                return None
            
            # Update fields
            update_data = user_data.dict(exclude_unset=True)
            for field, value in update_data.items():
                setattr(user, field, value)
            
            user.updated_at = datetime.now(timezone.utc)
            await session.commit()
            await session.refresh(user)
            
            return user
    
    async def update_login_stats(self, user_id: int):
        """Update user login statistics"""
        async with get_db_session() as session:
            await session.execute(
                update(User)
                .where(User.id == user_id)
                .values(
                    last_login=datetime.now(timezone.utc),
                    login_count=User.login_count + 1
                )
            )
            await session.commit()
    
    # Session management
    async def create_session(self, user_id: int, request_info: Dict[str, Any]) -> UserSession:
        """Create user session"""
        async with get_db_session() as session:
            # Generate tokens
            session_token = secrets.token_urlsafe(32)
            refresh_token = secrets.token_urlsafe(32)
            
            # Create session
            user_session = UserSession(
                user_id=user_id,
                session_token=session_token,
                refresh_token=refresh_token,
                ip_address=request_info.get("ip_address"),
                user_agent=request_info.get("user_agent"),
                device_info=request_info.get("device_info"),
                expires_at=datetime.now(timezone.utc) + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
            )
            
            session.add(user_session)
            await session.commit()
            await session.refresh(user_session)
            
            return user_session
    
    async def get_active_session(self, session_token: str) -> Optional[UserSession]:
        """Get active session by token"""
        async with get_db_session() as session:
            result = await session.execute(
                select(UserSession).where(
                    and_(
                        UserSession.session_token == session_token,
                        UserSession.is_active == True,
                        UserSession.expires_at > datetime.now(timezone.utc)
                    )
                )
            )
            return result.scalar_one_or_none()
    
    async def revoke_session(self, session_token: str):
        """Revoke user session"""
        async with get_db_session() as session:
            await session.execute(
                update(UserSession)
                .where(UserSession.session_token == session_token)
                .values(is_active=False)
            )
            await session.commit()
    
    async def revoke_all_user_sessions(self, user_id: int):
        """Revoke all sessions for a user"""
        async with get_db_session() as session:
            await session.execute(
                update(UserSession)
                .where(UserSession.user_id == user_id)
                .values(is_active=False)
            )
            await session.commit()
    
    # OAuth flows
    def get_oauth_url(self, provider: AuthProvider, redirect_uri: str = None, scopes: List[str] = None) -> Dict[str, str]:
        """Generate OAuth authorization URL"""
        if provider not in self.oauth_configs:
            raise ValueError(f"Unsupported OAuth provider: {provider}")
        
        config = self.oauth_configs[provider]
        
        if not config["client_id"]:
            raise ValueError(f"OAuth not configured for {provider}")
        
        # Generate state for security
        state = secrets.token_urlsafe(32)
        
        # Build authorization URL
        params = {
            "client_id": config["client_id"],
            "response_type": "code",
            "state": state,
            "scope": " ".join(scopes or config["scopes"])
        }
        
        if redirect_uri:
            params["redirect_uri"] = redirect_uri
        
        auth_url = f"{config['auth_url']}?{urlencode(params)}"
        
        return {
            "auth_url": auth_url,
            "state": state
        }
    
    async def store_oauth_state(self, state: str, provider: AuthProvider, request_info: Dict[str, Any]):
        """Store OAuth state for security verification"""
        async with get_db_session() as session:
            oauth_state = OAuthState(
                state=state,
                provider=provider,
                ip_address=request_info.get("ip_address"),
                user_agent=request_info.get("user_agent"),
                expires_at=datetime.now(timezone.utc) + timedelta(minutes=10)  # 10 minute expiry
            )
            
            session.add(oauth_state)
            await session.commit()
    
    async def verify_oauth_state(self, state: str, provider: AuthProvider) -> bool:
        """Verify OAuth state"""
        async with get_db_session() as session:
            result = await session.execute(
                select(OAuthState).where(
                    and_(
                        OAuthState.state == state,
                        OAuthState.provider == provider,
                        OAuthState.used == False,
                        OAuthState.expires_at > datetime.now(timezone.utc)
                    )
                )
            )
            oauth_state = result.scalar_one_or_none()
            
            if oauth_state:
                # Mark as used
                await session.execute(
                    update(OAuthState)
                    .where(OAuthState.id == oauth_state.id)
                    .values(used=True)
                )
                await session.commit()
                return True
            
            return False
    
    async def process_oauth_callback(self, callback: OAuthCallback, redirect_uri: str = None) -> Dict[str, Any]:
        """Process OAuth callback and exchange code for tokens"""
        if callback.provider not in self.oauth_configs:
            raise ValueError(f"Unsupported OAuth provider: {callback.provider}")
        
        # Verify state
        if not await self.verify_oauth_state(callback.state, callback.provider):
            raise ValueError("Invalid or expired OAuth state")
        
        config = self.oauth_configs[callback.provider]
        
        # Exchange code for access token
        token_data = {
            "client_id": config["client_id"],
            "client_secret": config["client_secret"],
            "code": callback.code,
            "grant_type": "authorization_code"
        }
        
        if redirect_uri:
            token_data["redirect_uri"] = redirect_uri
        
        async with aiohttp.ClientSession() as session:
            # Get access token
            async with session.post(config["token_url"], data=token_data) as response:
                if response.status != 200:
                    raise ValueError("Failed to exchange OAuth code for token")
                
                token_response = await response.json()
                access_token = token_response.get("access_token")
                
                if not access_token:
                    raise ValueError("No access token received from OAuth provider")
            
            # Get user info
            headers = {"Authorization": f"Bearer {access_token}"}
            async with session.get(config["user_info_url"], headers=headers) as response:
                if response.status != 200:
                    raise ValueError("Failed to fetch user info from OAuth provider")
                
                user_info = await response.json()
        
        return {
            "access_token": access_token,
            "user_info": user_info,
            "provider": callback.provider
        }
    
    async def create_or_update_oauth_user(self, oauth_data: Dict[str, Any]) -> User:
        """Create or update user from OAuth data"""
        provider = oauth_data["provider"]
        user_info = oauth_data["user_info"]
        
        # Extract user data based on provider
        if provider == AuthProvider.GOOGLE:
            email = user_info.get("email")
            full_name = user_info.get("name")
            avatar_url = user_info.get("picture")
            provider_id = user_info.get("id")
        elif provider == AuthProvider.GITHUB:
            email = user_info.get("email")
            full_name = user_info.get("name")
            avatar_url = user_info.get("avatar_url")
            provider_id = str(user_info.get("id"))
        elif provider == AuthProvider.MICROSOFT:
            email = user_info.get("mail") or user_info.get("userPrincipalName")
            full_name = user_info.get("displayName")
            avatar_url = None  # Microsoft Graph doesn't provide avatar in basic profile
            provider_id = user_info.get("id")
        else:
            raise ValueError(f"Unsupported provider: {provider}")
        
        if not email:
            raise ValueError("Email not provided by OAuth provider")
        
        async with get_db_session() as session:
            # Check if user exists
            result = await session.execute(
                select(User).where(
                    or_(
                        User.email == email,
                        and_(
                            User.auth_provider == provider,
                            User.provider_id == provider_id
                        )
                    )
                )
            )
            user = result.scalar_one_or_none()
            
            if user:
                # Update existing user
                user.full_name = full_name or user.full_name
                user.avatar_url = avatar_url or user.avatar_url
                user.provider_data = user_info
                user.is_verified = True
                user.last_login = datetime.now(timezone.utc)
                user.login_count += 1
                user.updated_at = datetime.now(timezone.utc)
            else:
                # Create new user
                user = User(
                    email=email,
                    full_name=full_name,
                    avatar_url=avatar_url,
                    auth_provider=provider,
                    provider_id=provider_id,
                    provider_data=user_info,
                    is_verified=True,
                    role=UserRole.VIEWER,
                    login_count=1,
                    last_login=datetime.now(timezone.utc)
                )
                session.add(user)
            
            await session.commit()
            await session.refresh(user)
            
            return user
    
    # API Key management
    async def generate_api_key_for_user(self, user_id: int, request: APIKeyRequest) -> str:
        """Generate API key for user"""
        api_key = self.generate_api_key()
        expires_at = datetime.now(timezone.utc) + timedelta(days=request.expires_in_days)
        
        async with get_db_session() as session:
            await session.execute(
                update(User)
                .where(User.id == user_id)
                .values(
                    api_key=api_key,
                    api_key_expires_at=expires_at,
                    updated_at=datetime.now(timezone.utc)
                )
            )
            await session.commit()
        
        return api_key
    
    async def revoke_api_key(self, user_id: int):
        """Revoke user's API key"""
        async with get_db_session() as session:
            await session.execute(
                update(User)
                .where(User.id == user_id)
                .values(
                    api_key=None,
                    api_key_expires_at=None,
                    updated_at=datetime.now(timezone.utc)
                )
            )
            await session.commit()
    
    # User statistics
    async def get_user_stats(self, user_id: int) -> UserStats:
        """Get user statistics"""
        # This would integrate with analytics service
        # For now, return empty stats
        return UserStats()
    
    # Authorization helpers
    def check_permission(self, user: User, required_permission: str) -> bool:
        """Check if user has required permission"""
        if user.is_superuser:
            return True
        
        # Role-based permissions
        role_permissions = {
            UserRole.ADMIN: ["*"],  # All permissions
            UserRole.MANAGER: ["view", "create", "update", "analytics"],
            UserRole.DEVELOPER: ["view", "create", "update"],
            UserRole.VIEWER: ["view"],
            UserRole.GUEST: ["view_public"]
        }
        
        user_permissions = role_permissions.get(user.role, [])
        
        # Check wildcard permission
        if "*" in user_permissions:
            return True
        
        # Check specific permission
        if required_permission in user_permissions:
            return True
        
        # Check custom permissions
        if user.permissions and required_permission in user.permissions:
            return True
        
        return False
    
    async def health_check(self) -> Dict[str, Any]:
        """Authentication service health check"""
        try:
            # Test database connection
            async with get_db_session() as session:
                await session.execute(select(User).limit(1))
            
            # Test OAuth configurations
            configured_providers = []
            for provider, config in self.oauth_configs.items():
                if config["client_id"] and config["client_secret"]:
                    configured_providers.append(provider.value)
            
            return {
                "status": "healthy",
                "database_connection": "ok",
                "configured_oauth_providers": configured_providers,
                "jwt_algorithm": ALGORITHM,
                "access_token_expire_minutes": ACCESS_TOKEN_EXPIRE_MINUTES,
                "refresh_token_expire_days": REFRESH_TOKEN_EXPIRE_DAYS
            }
            
        except Exception as e:
            return {
                "status": "unhealthy",
                "error": str(e)
            }

# Global auth service instance
auth_service = AuthService()