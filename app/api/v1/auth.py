"""
Authentication API Endpoints
OAuth2, JWT, and user management endpoints
"""

from fastapi import APIRouter, Depends, HTTPException, status, Request, Response
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.responses import RedirectResponse
from typing import Dict, Any, Optional, List
import logging
from datetime import datetime

from app.services.auth_service import auth_service
from app.models.user import (
    LoginRequest, LoginResponse, UserCreate, UserResponse, UserUpdate,
    OAuthLoginRequest, OAuthCallback, TokenResponse, APIKeyRequest, APIKeyResponse,
    UserProfile, UserStats, PasswordResetRequest, PasswordReset, ChangePasswordRequest,
    AuthProvider, UserRole, User
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/auth", tags=["Authentication"])
security = HTTPBearer(auto_error=False)

# Dependencies
async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> User:
    """Get current authenticated user from JWT token"""
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Verify JWT token
    payload = auth_service.verify_token(credentials.credentials, "access")
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Get user from database
    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload"
        )
    
    user = await auth_service.get_user_by_id(int(user_id))
    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or inactive"
        )
    
    return user

async def get_current_active_user(current_user: User = Depends(get_current_user)) -> User:
    """Get current active user"""
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Inactive user"
        )
    return current_user

async def get_current_admin_user(current_user: User = Depends(get_current_active_user)) -> User:
    """Get current admin user"""
    if current_user.role not in [UserRole.ADMIN] and not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    return current_user

def get_request_info(request: Request) -> Dict[str, Any]:
    """Extract request information for logging/security"""
    return {
        "ip_address": request.client.host,
        "user_agent": request.headers.get("user-agent"),
        "device_info": {
            "method": request.method,
            "url": str(request.url),
            "headers": dict(request.headers)
        }
    }

# Authentication endpoints
@router.post("/register", response_model=UserResponse)
async def register(user_data: UserCreate, request: Request):
    """
    Register new user with email and password
    
    Features:
    - Email validation
    - Password hashing
    - Role assignment
    - Account verification (for local accounts)
    """
    try:
        request_info = get_request_info(request)
        
        # Create user
        user = await auth_service.create_user(user_data, request_info)
        
        logger.info(f"User registered: {user.email} (ID: {user.id})")
        
        return UserResponse.from_orm(user)
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Registration error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Registration failed"
        )

@router.post("/login", response_model=LoginResponse)
async def login(login_data: LoginRequest, request: Request):
    """
    Login with email and password
    
    Returns:
    - JWT access token
    - JWT refresh token
    - User profile information
    """
    try:
        request_info = get_request_info(request)
        
        # Authenticate user
        user = await auth_service.authenticate_user(login_data.email, login_data.password)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password"
            )
        
        # Create session
        session = await auth_service.create_session(user.id, request_info)
        
        # Generate JWT tokens
        access_token = auth_service.create_access_token({"sub": str(user.id), "email": user.email})
        refresh_token = auth_service.create_refresh_token({"sub": str(user.id), "session": session.session_token})
        
        # Create user profile
        user_profile = UserProfile(
            id=user.id,
            email=user.email,
            username=user.username,
            full_name=user.full_name,
            role=user.role,
            avatar_url=user.avatar_url,
            bio=user.bio,
            company=user.company,
            location=user.location,
            website=user.website,
            is_verified=user.is_verified,
            auth_provider=user.auth_provider,
            created_at=user.created_at
        )
        
        logger.info(f"User logged in: {user.email} (ID: {user.id})")
        
        return LoginResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            token_type="bearer",
            expires_in=1800,  # 30 minutes
            user=user_profile
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Login error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Login failed"
        )

@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(refresh_token: str, request: Request):
    """
    Refresh access token using refresh token
    
    Provides seamless token renewal without re-authentication
    """
    try:
        # Verify refresh token
        payload = auth_service.verify_token(refresh_token, "refresh")
        if not payload:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired refresh token"
            )
        
        user_id = payload.get("sub")
        session_token = payload.get("session")
        
        if not user_id or not session_token:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid refresh token payload"
            )
        
        # Verify session is still active
        session = await auth_service.get_active_session(session_token)
        if not session or session.user_id != int(user_id):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Session not found or expired"
            )
        
        # Get user
        user = await auth_service.get_user_by_id(int(user_id))
        if not user or not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found or inactive"
            )
        
        # Generate new access token
        new_access_token = auth_service.create_access_token({"sub": user_id, "email": user.email})
        
        return TokenResponse(
            access_token=new_access_token,
            token_type="bearer",
            expires_in=1800
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Token refresh error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Token refresh failed"
        )

@router.post("/logout")
async def logout(current_user: User = Depends(get_current_active_user), request: Request = None):
    """
    Logout current user
    
    Revokes current session and invalidates tokens
    """
    try:
        # This would require session token from the request
        # For now, we'll revoke all user sessions
        await auth_service.revoke_all_user_sessions(current_user.id)
        
        logger.info(f"User logged out: {current_user.email} (ID: {current_user.id})")
        
        return {"message": "Successfully logged out"}
        
    except Exception as e:
        logger.error(f"Logout error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Logout failed"
        )

# OAuth endpoints
@router.get("/oauth/{provider}")
async def oauth_login(provider: AuthProvider, request: Request, redirect_uri: Optional[str] = None):
    """
    Initiate OAuth login flow
    
    Supported providers:
    - Google
    - GitHub  
    - Microsoft
    
    Returns authorization URL for redirect
    """
    try:
        request_info = get_request_info(request)
        
        # Generate OAuth URL
        oauth_data = auth_service.get_oauth_url(provider, redirect_uri)
        
        # Store state for security
        await auth_service.store_oauth_state(oauth_data["state"], provider, request_info)
        
        logger.info(f"OAuth login initiated: {provider}")
        
        return {
            "auth_url": oauth_data["auth_url"],
            "state": oauth_data["state"],
            "provider": provider
        }
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"OAuth initiation error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="OAuth initiation failed"
        )

@router.post("/oauth/callback", response_model=LoginResponse)
async def oauth_callback(callback: OAuthCallback, request: Request, redirect_uri: Optional[str] = None):
    """
    Handle OAuth callback and complete authentication
    
    Processes authorization code and creates/updates user account
    """
    try:
        request_info = get_request_info(request)
        
        # Process OAuth callback
        oauth_data = await auth_service.process_oauth_callback(callback, redirect_uri)
        
        # Create or update user
        user = await auth_service.create_or_update_oauth_user(oauth_data)
        
        # Create session
        session = await auth_service.create_session(user.id, request_info)
        
        # Generate JWT tokens
        access_token = auth_service.create_access_token({"sub": str(user.id), "email": user.email})
        refresh_token = auth_service.create_refresh_token({"sub": str(user.id), "session": session.session_token})
        
        # Create user profile
        user_profile = UserProfile(
            id=user.id,
            email=user.email,
            username=user.username,
            full_name=user.full_name,
            role=user.role,
            avatar_url=user.avatar_url,
            bio=user.bio,
            company=user.company,
            location=user.location,
            website=user.website,
            is_verified=user.is_verified,
            auth_provider=user.auth_provider,
            created_at=user.created_at
        )
        
        logger.info(f"OAuth login successful: {user.email} via {callback.provider}")
        
        return LoginResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            token_type="bearer",
            expires_in=1800,
            user=user_profile
        )
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"OAuth callback error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="OAuth authentication failed"
        )

# User profile endpoints
@router.get("/me", response_model=UserResponse)
async def get_current_user_profile(current_user: User = Depends(get_current_active_user)):
    """
    Get current user profile
    
    Returns complete user information including preferences and stats
    """
    return UserResponse.from_orm(current_user)

@router.put("/me", response_model=UserResponse)
async def update_current_user_profile(
    user_update: UserUpdate,
    current_user: User = Depends(get_current_active_user)
):
    """
    Update current user profile
    
    Allows users to update their profile information, preferences, and settings
    """
    try:
        updated_user = await auth_service.update_user(current_user.id, user_update)
        if not updated_user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        logger.info(f"User profile updated: {updated_user.email} (ID: {updated_user.id})")
        
        return UserResponse.from_orm(updated_user)
        
    except Exception as e:
        logger.error(f"Profile update error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Profile update failed"
        )

@router.get("/me/stats", response_model=UserStats)
async def get_user_stats(current_user: User = Depends(get_current_active_user)):
    """
    Get user statistics and activity metrics
    
    Returns:
    - Test execution statistics
    - Performance metrics
    - Activity history
    - Achievements
    """
    try:
        stats = await auth_service.get_user_stats(current_user.id)
        return stats
        
    except Exception as e:
        logger.error(f"User stats error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get user statistics"
        )

# API Key endpoints
@router.post("/api-key", response_model=Dict[str, str])
async def generate_api_key(
    api_key_request: APIKeyRequest,
    current_user: User = Depends(get_current_active_user)
):
    """
    Generate API key for programmatic access
    
    Features:
    - Custom expiration dates
    - Permission scoping
    - Usage tracking
    """
    try:
        api_key = await auth_service.generate_api_key_for_user(current_user.id, api_key_request)
        
        logger.info(f"API key generated for user: {current_user.email} (ID: {current_user.id})")
        
        return {
            "api_key": api_key,
            "message": "API key generated successfully",
            "expires_in_days": api_key_request.expires_in_days
        }
        
    except Exception as e:
        logger.error(f"API key generation error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="API key generation failed"
        )

@router.delete("/api-key")
async def revoke_api_key(current_user: User = Depends(get_current_active_user)):
    """
    Revoke current API key
    
    Immediately invalidates the user's API key
    """
    try:
        await auth_service.revoke_api_key(current_user.id)
        
        logger.info(f"API key revoked for user: {current_user.email} (ID: {current_user.id})")
        
        return {"message": "API key revoked successfully"}
        
    except Exception as e:
        logger.error(f"API key revocation error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="API key revocation failed"
        )

# Admin endpoints
@router.get("/users", response_model=List[UserResponse])
async def list_users(
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(get_current_admin_user)
):
    """
    List all users (Admin only)
    
    Paginated list of all registered users with filtering options
    """
    try:
        # This would implement user listing with pagination
        # For now, return empty list
        return []
        
    except Exception as e:
        logger.error(f"User listing error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to list users"
        )

@router.get("/users/{user_id}", response_model=UserResponse)
async def get_user(
    user_id: int,
    current_user: User = Depends(get_current_admin_user)
):
    """
    Get specific user by ID (Admin only)
    """
    try:
        user = await auth_service.get_user_by_id(user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        return UserResponse.from_orm(user)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get user error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get user"
        )

@router.put("/users/{user_id}", response_model=UserResponse)
async def update_user(
    user_id: int,
    user_update: UserUpdate,
    current_user: User = Depends(get_current_admin_user)
):
    """
    Update specific user (Admin only)
    """
    try:
        updated_user = await auth_service.update_user(user_id, user_update)
        if not updated_user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        logger.info(f"User updated by admin: {updated_user.email} (ID: {updated_user.id})")
        
        return UserResponse.from_orm(updated_user)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Admin user update error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update user"
        )

# Health check
@router.get("/health")
async def auth_health_check():
    """
    Authentication service health check
    
    Returns status of authentication components:
    - Database connectivity
    - OAuth provider configurations
    - JWT functionality
    """
    try:
        health_status = await auth_service.health_check()
        
        if health_status["status"] == "healthy":
            return health_status
        else:
            return Response(
                content=health_status,
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE
            )
            
    except Exception as e:
        logger.error(f"Auth health check error: {e}")
        return Response(
            content={"status": "error", "error": str(e)},
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE
        )