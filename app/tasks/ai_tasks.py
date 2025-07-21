"""
AI Background Tasks
Celery ile asenkron AI işlemleri
"""

import logging
from celery import shared_task
from typing import Dict, Any, List
from app.services.ai_service import AIService
from app.core.database import SessionLocal
from app.models.test import Test, TestResult

logger = logging.getLogger(__name__)


@shared_task(bind=True, name="analyze_test_with_ai")
def analyze_test_with_ai(self, test_id: int, user_email: str):
    """Test sonuçlarını AI ile analiz et (background task)"""
    try:
        db = SessionLocal()
        ai_service = AIService()
        
        # Test ve sonuçlarını al
        test = db.query(Test).filter(Test.id == test_id).first()
        if not test:
            logger.error(f"Test bulunamadı: {test_id}")
            return {"error": "Test bulunamadı"}
        
        results = db.query(TestResult).filter(TestResult.test_id == test_id).all()
        
        # Test sonuçlarını formatla
        test_results = [
            {
                "status": result.status,
                "execution_time": result.execution_time,
                "error_message": result.error_message,
                "environment": result.environment,
                "created_at": result.created_at.isoformat() if result.created_at else None
            }
            for result in results
        ]
        
        # AI analizi yap
        analysis_result = await ai_service.analyze_test_results(
            test_results=test_results,
            test_type=test.test_type,
            context={"test_title": test.title, "test_description": test.description}
        )
        
        logger.info(f"AI analizi tamamlandı: {test_id}")
        
        return {
            "test_id": test_id,
            "analysis": analysis_result,
            "status": "completed"
        }
        
    except Exception as e:
        logger.error(f"AI analiz task hatası: {e}")
        return {"error": str(e), "status": "failed"}
    finally:
        db.close()


@shared_task(bind=True, name="generate_test_scenarios")
def generate_test_scenarios(
    self,
    user_email: str,
    requirements: str,
    test_type: str,
    complexity: str = "medium"
):
    """AI ile test senaryoları oluştur (background task)"""
    try:
        ai_service = AIService()
        
        # Test senaryoları oluştur
        scenarios = await ai_service.generate_test_scenarios(
            requirements=requirements,
            test_type=test_type,
            complexity=complexity
        )
        
        logger.info(f"Test senaryoları oluşturuldu: {test_type}")
        
        return {
            "user_email": user_email,
            "test_type": test_type,
            "scenarios": scenarios,
            "total_scenarios": len(scenarios),
            "status": "completed"
        }
        
    except Exception as e:
        logger.error(f"Test senaryosu oluşturma task hatası: {e}")
        return {"error": str(e), "status": "failed"}


@shared_task(bind=True, name="optimize_test_suite_ai")
def optimize_test_suite_ai(
    self,
    test_suite_data: List[Dict[str, Any]],
    coverage_goals: Dict[str, float],
    user_email: str
):
    """Test suite'ini AI ile optimize et (background task)"""
    try:
        ai_service = AIService()
        
        # Test suite optimizasyonu
        optimization_result = await ai_service.optimize_test_suite(
            test_suite=test_suite_data,
            coverage_goals=coverage_goals
        )
        
        logger.info(f"Test suite optimizasyonu tamamlandı")
        
        return {
            "user_email": user_email,
            "optimization_result": optimization_result,
            "status": "completed"
        }
        
    except Exception as e:
        logger.error(f"Test suite optimizasyon task hatası: {e}")
        return {"error": str(e), "status": "failed"}


@shared_task(bind=True, name="predict_test_outcomes_ai")
def predict_test_outcomes_ai(
    self,
    test_code: str,
    test_context: Dict[str, Any],
    user_email: str
):
    """Test sonuçlarını AI ile tahmin et (background task)"""
    try:
        ai_service = AIService()
        
        # Test sonuç tahmini
        prediction_result = await ai_service.predict_test_outcomes(
            test_code=test_code,
            test_context=test_context
        )
        
        logger.info(f"Test sonuç tahmini tamamlandı")
        
        return {
            "user_email": user_email,
            "prediction_result": prediction_result,
            "status": "completed"
        }
        
    except Exception as e:
        logger.error(f"Test sonuç tahmin task hatası: {e}")
        return {"error": str(e), "status": "failed"}


@shared_task(bind=True, name="review_test_code_ai")
def review_test_code_ai(
    self,
    code: str,
    language: str,
    user_email: str
):
    """Test kodunu AI ile incele (background task)"""
    try:
        ai_service = AIService()
        
        # Kod incelemesi
        review_result = await ai_service.review_test_code(
            code=code,
            language=language
        )
        
        logger.info(f"Kod incelemesi tamamlandı")
        
        return {
            "user_email": user_email,
            "review_result": review_result,
            "status": "completed"
        }
        
    except Exception as e:
        logger.error(f"Kod inceleme task hatası: {e}")
        return {"error": str(e), "status": "failed"}


@shared_task(bind=True, name="batch_ai_analysis")
def batch_ai_analysis(
    self,
    test_ids: List[int],
    user_email: str
):
    """Toplu AI analizi (background task)"""
    try:
        db = SessionLocal()
        ai_service = AIService()
        
        results = []
        
        for test_id in test_ids:
            try:
                # Her test için analiz yap
                test = db.query(Test).filter(Test.id == test_id).first()
                if not test:
                    continue
                
                test_results = db.query(TestResult).filter(TestResult.test_id == test_id).all()
                
                analysis_result = await ai_service.analyze_test_results(
                    test_results=[
                        {
                            "status": result.status,
                            "execution_time": result.execution_time,
                            "error_message": result.error_message
                        }
                        for result in test_results
                    ],
                    test_type=test.test_type
                )
                
                results.append({
                    "test_id": test_id,
                    "analysis": analysis_result
                })
                
            except Exception as e:
                logger.error(f"Test {test_id} analiz hatası: {e}")
                results.append({
                    "test_id": test_id,
                    "error": str(e)
                })
        
        logger.info(f"Toplu AI analizi tamamlandı: {len(results)} test")
        
        return {
            "user_email": user_email,
            "results": results,
            "total_tests": len(test_ids),
            "successful_analyses": len([r for r in results if "error" not in r]),
            "status": "completed"
        }
        
    except Exception as e:
        logger.error(f"Toplu AI analiz task hatası: {e}")
        return {"error": str(e), "status": "failed"}
    finally:
        db.close()


@shared_task(bind=True, name="cleanup_ai_tasks")
def cleanup_ai_tasks(self):
    """Eski AI task'larını temizle (scheduled task)"""
    try:
        # Bu task Celery beat tarafından düzenli olarak çalıştırılır
        # Eski task sonuçlarını ve log'ları temizler
        
        logger.info("AI task temizleme işlemi başlatıldı")
        
        # Temizleme işlemleri burada yapılır
        # Örnek: 30 günden eski task sonuçlarını sil
        
        return {
            "message": "AI task temizleme tamamlandı",
            "status": "completed"
        }
        
    except Exception as e:
        logger.error(f"AI task temizleme hatası: {e}")
        return {"error": str(e), "status": "failed"} 