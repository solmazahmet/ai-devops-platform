"""
AI Servisleri API Endpoints
OpenAI entegrasyonu ve AI destekli test analizi
"""

from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List, Optional
import logging

from app.core.database import get_db
from app.core.security import get_current_user
from app.schemas.ai import AIAnalysisRequest, AIAnalysisResponse, TestGenerationRequest
from app.services.ai_service import AIService
from app.tasks.ai_tasks import analyze_test_with_ai, generate_test_scenarios

logger = logging.getLogger(__name__)

router = APIRouter()

@router.post("/analyze", response_model=AIAnalysisResponse)
async def analyze_test(
    analysis_request: AIAnalysisRequest,
    current_user: str = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Test sonuçlarını AI ile analiz et"""
    try:
        ai_service = AIService()
        
        # AI analizi yap
        analysis_result = await ai_service.analyze_test_results(
            test_results=analysis_request.test_results,
            test_type=analysis_request.test_type,
            context=analysis_request.context
        )
        
        logger.info(f"AI analizi tamamlandı: {analysis_request.test_type}")
        
        return AIAnalysisResponse(
            analysis=analysis_result,
            confidence_score=analysis_result.get("confidence", 0.0),
            recommendations=analysis_result.get("recommendations", []),
            insights=analysis_result.get("insights", [])
        )
        
    except Exception as e:
        logger.error(f"AI analiz hatası: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="AI analizi yapılırken hata oluştu"
        )

@router.post("/generate-test-scenarios")
async def generate_test_scenarios_async(
    generation_request: TestGenerationRequest,
    background_tasks: BackgroundTasks,
    current_user: str = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """AI ile test senaryoları oluştur (background task)"""
    try:
        # Background task olarak çalıştır
        background_tasks.add_task(
            generate_test_scenarios,
            user_email=current_user,
            requirements=generation_request.requirements,
            test_type=generation_request.test_type,
            complexity=generation_request.complexity
        )
        
        logger.info(f"Test senaryosu oluşturma başlatıldı: {generation_request.test_type}")
        
        return {
            "message": "Test senaryoları oluşturma başlatıldı",
            "task_status": "started",
            "test_type": generation_request.test_type
        }
        
    except Exception as e:
        logger.error(f"Test senaryosu oluşturma hatası: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Test senaryosu oluşturulurken hata oluştu"
        )

@router.post("/optimize-test-suite")
async def optimize_test_suite(
    test_suite_data: dict,
    current_user: str = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Test suite'ini AI ile optimize et"""
    try:
        ai_service = AIService()
        
        optimization_result = await ai_service.optimize_test_suite(
            test_suite=test_suite_data.get("tests", []),
            coverage_goals=test_suite_data.get("coverage_goals", {}),
            performance_constraints=test_suite_data.get("performance_constraints", {})
        )
        
        logger.info(f"Test suite optimizasyonu tamamlandı")
        
        return {
            "message": "Test suite başarıyla optimize edildi",
            "optimization_result": optimization_result,
            "improvements": optimization_result.get("improvements", []),
            "coverage_increase": optimization_result.get("coverage_increase", 0.0)
        }
        
    except Exception as e:
        logger.error(f"Test suite optimizasyon hatası: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Test suite optimize edilirken hata oluştu"
        )

@router.post("/predict-test-outcomes")
async def predict_test_outcomes(
    test_data: dict,
    current_user: str = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Test sonuçlarını AI ile tahmin et"""
    try:
        ai_service = AIService()
        
        prediction_result = await ai_service.predict_test_outcomes(
            test_code=test_data.get("test_code", ""),
            test_context=test_data.get("context", {}),
            historical_data=test_data.get("historical_data", [])
        )
        
        logger.info(f"Test sonuç tahmini tamamlandı")
        
        return {
            "message": "Test sonuç tahmini tamamlandı",
            "predictions": prediction_result.get("predictions", []),
            "confidence_scores": prediction_result.get("confidence_scores", []),
            "risk_factors": prediction_result.get("risk_factors", [])
        }
        
    except Exception as e:
        logger.error(f"Test sonuç tahmin hatası: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Test sonuç tahmini yapılırken hata oluştu"
        )

@router.get("/ai-status")
async def get_ai_service_status(
    current_user: str = Depends(get_current_user)
):
    """AI servis durumunu kontrol et"""
    try:
        ai_service = AIService()
        status = await ai_service.check_service_status()
        
        return {
            "status": "healthy" if status else "unhealthy",
            "service": "OpenAI",
            "model": ai_service.model,
            "available": status
        }
        
    except Exception as e:
        logger.error(f"AI servis durumu kontrol hatası: {e}")
        return {
            "status": "unhealthy",
            "service": "OpenAI",
            "error": str(e)
        }

@router.post("/code-review")
async def ai_code_review(
    code_data: dict,
    current_user: str = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """AI ile kod incelemesi yap"""
    try:
        ai_service = AIService()
        
        review_result = await ai_service.review_test_code(
            code=code_data.get("code", ""),
            language=code_data.get("language", "python"),
            context=code_data.get("context", {})
        )
        
        logger.info(f"AI kod incelemesi tamamlandı")
        
        return {
            "message": "Kod incelemesi tamamlandı",
            "review": review_result.get("review", ""),
            "suggestions": review_result.get("suggestions", []),
            "issues": review_result.get("issues", []),
            "score": review_result.get("score", 0.0)
        }
        
    except Exception as e:
        logger.error(f"AI kod inceleme hatası: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Kod incelemesi yapılırken hata oluştu"
        ) 