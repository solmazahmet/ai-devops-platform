"""
Test Yönetimi API Endpoints
Test oluşturma, listeleme ve yönetimi
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional
import logging

from app.core.database import get_db
from app.core.security import get_current_user
from app.schemas.test import TestCreate, TestUpdate, TestResponse, TestList
from app.models.test import Test
from app.services.test_service import TestService

logger = logging.getLogger(__name__)

router = APIRouter()

@router.post("/", response_model=TestResponse)
async def create_test(
    test_data: TestCreate,
    current_user: str = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Yeni test oluştur"""
    try:
        test_service = TestService(db)
        test = await test_service.create_test(test_data, current_user)
        
        logger.info(f"Yeni test oluşturuldu: {test.id} - {test.title}")
        
        return test
        
    except Exception as e:
        logger.error(f"Test oluşturma hatası: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Test oluşturulurken hata oluştu"
        )

@router.get("/", response_model=List[TestResponse])
async def get_tests(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    status_filter: Optional[str] = Query(None),
    current_user: str = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Test listesini al"""
    try:
        test_service = TestService(db)
        tests = await test_service.get_tests(
            skip=skip,
            limit=limit,
            status_filter=status_filter,
            user_email=current_user
        )
        
        return tests
        
    except Exception as e:
        logger.error(f"Test listesi alma hatası: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Test listesi alınırken hata oluştu"
        )

@router.get("/{test_id}", response_model=TestResponse)
async def get_test(
    test_id: int,
    current_user: str = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Belirli bir testi al"""
    try:
        test_service = TestService(db)
        test = await test_service.get_test_by_id(test_id, current_user)
        
        if not test:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Test bulunamadı"
            )
        
        return test
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Test alma hatası: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Test alınırken hata oluştu"
        )

@router.put("/{test_id}", response_model=TestResponse)
async def update_test(
    test_id: int,
    test_data: TestUpdate,
    current_user: str = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Test güncelle"""
    try:
        test_service = TestService(db)
        test = await test_service.update_test(test_id, test_data, current_user)
        
        if not test:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Test bulunamadı"
            )
        
        logger.info(f"Test güncellendi: {test_id}")
        
        return test
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Test güncelleme hatası: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Test güncellenirken hata oluştu"
        )

@router.delete("/{test_id}")
async def delete_test(
    test_id: int,
    current_user: str = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Test sil"""
    try:
        test_service = TestService(db)
        success = await test_service.delete_test(test_id, current_user)
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Test bulunamadı"
            )
        
        logger.info(f"Test silindi: {test_id}")
        
        return {"message": "Test başarıyla silindi"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Test silme hatası: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Test silinirken hata oluştu"
        )

@router.post("/{test_id}/run")
async def run_test(
    test_id: int,
    current_user: str = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Test çalıştır"""
    try:
        test_service = TestService(db)
        result = await test_service.run_test(test_id, current_user)
        
        if not result:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Test bulunamadı"
            )
        
        logger.info(f"Test çalıştırıldı: {test_id}")
        
        return {
            "message": "Test başarıyla çalıştırıldı",
            "test_id": test_id,
            "status": "running"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Test çalıştırma hatası: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Test çalıştırılırken hata oluştu"
        )

@router.get("/{test_id}/results")
async def get_test_results(
    test_id: int,
    current_user: str = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Test sonuçlarını al"""
    try:
        test_service = TestService(db)
        results = await test_service.get_test_results(test_id, current_user)
        
        if not results:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Test sonuçları bulunamadı"
            )
        
        return results
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Test sonuçları alma hatası: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Test sonuçları alınırken hata oluştu"
        ) 