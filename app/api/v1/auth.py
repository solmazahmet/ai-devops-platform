"""
Kimlik Doğrulama API Endpoints
Login, register ve token yönetimi
"""

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from datetime import timedelta
import logging

from app.core.database import get_db
from app.core.security import verify_password, create_access_token, get_password_hash
from app.core.config import settings
from app.schemas.user import UserCreate, UserLogin, Token
from app.models.user import User

logger = logging.getLogger(__name__)

router = APIRouter()

@router.post("/register", response_model=dict)
async def register(user_data: UserCreate, db: Session = Depends(get_db)):
    """Yeni kullanıcı kaydı"""
    try:
        # Kullanıcının var olup olmadığını kontrol et
        existing_user = db.query(User).filter(User.email == user_data.email).first()
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Bu email adresi zaten kayıtlı"
            )
        
        # Yeni kullanıcı oluştur
        hashed_password = get_password_hash(user_data.password)
        new_user = User(
            email=user_data.email,
            username=user_data.username,
            hashed_password=hashed_password,
            full_name=user_data.full_name
        )
        
        db.add(new_user)
        db.commit()
        db.refresh(new_user)
        
        logger.info(f"Yeni kullanıcı kaydı: {user_data.email}")
        
        return {
            "message": "Kullanıcı başarıyla oluşturuldu",
            "user_id": new_user.id
        }
        
    except Exception as e:
        logger.error(f"Kullanıcı kaydı hatası: {e}")
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Kullanıcı oluşturulurken hata oluştu"
        )

@router.post("/login", response_model=Token)
async def login(user_credentials: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    """Kullanıcı girişi"""
    try:
        # Kullanıcıyı bul
        user = db.query(User).filter(User.email == user_credentials.username).first()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Geçersiz email veya şifre",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        # Şifreyi doğrula
        if not verify_password(user_credentials.password, user.hashed_password):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Geçersiz email veya şifre",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        # Token oluştur
        access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = create_access_token(
            data={"sub": user.email}, expires_delta=access_token_expires
        )
        
        logger.info(f"Kullanıcı girişi: {user.email}")
        
        return {
            "access_token": access_token,
            "token_type": "bearer",
            "user_id": user.id,
            "email": user.email
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Giriş hatası: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Giriş yapılırken hata oluştu"
        )

@router.get("/me", response_model=dict)
async def get_current_user_info(current_user: str = Depends(get_current_user), db: Session = Depends(get_db)):
    """Mevcut kullanıcı bilgilerini al"""
    try:
        user = db.query(User).filter(User.email == current_user).first()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Kullanıcı bulunamadı"
            )
        
        return {
            "id": user.id,
            "email": user.email,
            "username": user.username,
            "full_name": user.full_name,
            "is_active": user.is_active,
            "created_at": user.created_at
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Kullanıcı bilgisi alma hatası: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Kullanıcı bilgileri alınırken hata oluştu"
        ) 