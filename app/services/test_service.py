"""
Test Service
Test yönetimi ve iş mantığı
"""

import logging
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_
from datetime import datetime

from app.models.test import Test, TestResult
from app.schemas.test import TestCreate, TestUpdate, TestResponse

logger = logging.getLogger(__name__)


class TestService:
    def __init__(self, db: Session):
        self.db = db
    
    async def create_test(self, test_data: TestCreate, user_email: str) -> TestResponse:
        """Yeni test oluştur"""
        try:
            db_test = Test(
                title=test_data.title,
                description=test_data.description,
                test_type=test_data.test_type,
                priority=test_data.priority,
                test_code=test_data.test_code,
                test_data=test_data.test_data,
                expected_result=test_data.expected_result,
                tags=test_data.tags,
                created_by=user_email
            )
            
            self.db.add(db_test)
            self.db.commit()
            self.db.refresh(db_test)
            
            return TestResponse.from_orm(db_test)
            
        except Exception as e:
            logger.error(f"Test oluşturma hatası: {e}")
            self.db.rollback()
            raise
    
    async def get_tests(
        self,
        skip: int = 0,
        limit: int = 100,
        status_filter: Optional[str] = None,
        user_email: Optional[str] = None
    ) -> List[TestResponse]:
        """Test listesini al"""
        try:
            query = self.db.query(Test)
            
            if status_filter:
                query = query.filter(Test.status == status_filter)
            
            if user_email:
                query = query.filter(Test.created_by == user_email)
            
            tests = query.offset(skip).limit(limit).all()
            
            return [TestResponse.from_orm(test) for test in tests]
            
        except Exception as e:
            logger.error(f"Test listesi alma hatası: {e}")
            raise
    
    async def get_test_by_id(self, test_id: int, user_email: str) -> Optional[TestResponse]:
        """ID'ye göre test al"""
        try:
            test = self.db.query(Test).filter(
                and_(
                    Test.id == test_id,
                    Test.created_by == user_email
                )
            ).first()
            
            if test:
                return TestResponse.from_orm(test)
            return None
            
        except Exception as e:
            logger.error(f"Test alma hatası: {e}")
            raise
    
    async def update_test(
        self,
        test_id: int,
        test_data: TestUpdate,
        user_email: str
    ) -> Optional[TestResponse]:
        """Test güncelle"""
        try:
            test = self.db.query(Test).filter(
                and_(
                    Test.id == test_id,
                    Test.created_by == user_email
                )
            ).first()
            
            if not test:
                return None
            
            # Güncelleme alanları
            update_data = test_data.dict(exclude_unset=True)
            for field, value in update_data.items():
                setattr(test, field, value)
            
            test.updated_at = datetime.utcnow()
            
            self.db.commit()
            self.db.refresh(test)
            
            return TestResponse.from_orm(test)
            
        except Exception as e:
            logger.error(f"Test güncelleme hatası: {e}")
            self.db.rollback()
            raise
    
    async def delete_test(self, test_id: int, user_email: str) -> bool:
        """Test sil"""
        try:
            test = self.db.query(Test).filter(
                and_(
                    Test.id == test_id,
                    Test.created_by == user_email
                )
            ).first()
            
            if not test:
                return False
            
            self.db.delete(test)
            self.db.commit()
            
            return True
            
        except Exception as e:
            logger.error(f"Test silme hatası: {e}")
            self.db.rollback()
            raise
    
    async def run_test(self, test_id: int, user_email: str) -> bool:
        """Test çalıştır"""
        try:
            test = self.db.query(Test).filter(
                and_(
                    Test.id == test_id,
                    Test.created_by == user_email
                )
            ).first()
            
            if not test:
                return False
            
            # Test çalıştırma simülasyonu
            # Gerçek uygulamada burada test runner çağrılır
            test_result = TestResult(
                test_id=test_id,
                status="running",
                start_time=datetime.utcnow(),
                created_by=user_email
            )
            
            self.db.add(test_result)
            self.db.commit()
            
            # Background task olarak test çalıştırılabilir
            # await run_test_async.delay(test_id, test_result.id)
            
            return True
            
        except Exception as e:
            logger.error(f"Test çalıştırma hatası: {e}")
            self.db.rollback()
            raise
    
    async def get_test_results(self, test_id: int, user_email: str) -> Optional[List[Dict[str, Any]]]:
        """Test sonuçlarını al"""
        try:
            test = self.db.query(Test).filter(
                and_(
                    Test.id == test_id,
                    Test.created_by == user_email
                )
            ).first()
            
            if not test:
                return None
            
            results = self.db.query(TestResult).filter(
                TestResult.test_id == test_id
            ).order_by(TestResult.created_at.desc()).all()
            
            return [
                {
                    "id": result.id,
                    "status": result.status,
                    "execution_time": result.execution_time,
                    "start_time": result.start_time,
                    "end_time": result.end_time,
                    "output": result.output,
                    "error_message": result.error_message,
                    "environment": result.environment,
                    "created_at": result.created_at
                }
                for result in results
            ]
            
        except Exception as e:
            logger.error(f"Test sonuçları alma hatası: {e}")
            raise
    
    async def search_tests(
        self,
        query: str,
        user_email: Optional[str] = None,
        test_type: Optional[str] = None
    ) -> List[TestResponse]:
        """Test ara"""
        try:
            db_query = self.db.query(Test)
            
            # Arama filtresi
            search_filter = or_(
                Test.title.ilike(f"%{query}%"),
                Test.description.ilike(f"%{query}%"),
                Test.test_code.ilike(f"%{query}%")
            )
            db_query = db_query.filter(search_filter)
            
            # Kullanıcı filtresi
            if user_email:
                db_query = db_query.filter(Test.created_by == user_email)
            
            # Test tipi filtresi
            if test_type:
                db_query = db_query.filter(Test.test_type == test_type)
            
            tests = db_query.all()
            
            return [TestResponse.from_orm(test) for test in tests]
            
        except Exception as e:
            logger.error(f"Test arama hatası: {e}")
            raise
    
    async def get_test_statistics(self, user_email: str) -> Dict[str, Any]:
        """Test istatistiklerini al"""
        try:
            total_tests = self.db.query(Test).filter(
                Test.created_by == user_email
            ).count()
            
            active_tests = self.db.query(Test).filter(
                and_(
                    Test.created_by == user_email,
                    Test.status == "active"
                )
            ).count()
            
            # Test tipi dağılımı
            test_types = self.db.query(Test.test_type).filter(
                Test.created_by == user_email
            ).all()
            
            type_distribution = {}
            for test_type in test_types:
                type_distribution[test_type[0]] = type_distribution.get(test_type[0], 0) + 1
            
            return {
                "total_tests": total_tests,
                "active_tests": active_tests,
                "type_distribution": type_distribution,
                "success_rate": 0.85  # Bu değer gerçek verilerden hesaplanmalı
            }
            
        except Exception as e:
            logger.error(f"Test istatistikleri alma hatası: {e}")
            raise 