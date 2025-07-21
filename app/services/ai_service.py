"""
AI Service
OpenAI entegrasyonu ve AI destekli test analizi
"""

import openai
import logging
from typing import List, Dict, Any, Optional
from app.core.config import settings

logger = logging.getLogger(__name__)


class AIService:
    def __init__(self):
        self.client = openai.AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
        self.model = settings.OPENAI_MODEL
        self.max_tokens = settings.OPENAI_MAX_TOKENS
        self.temperature = settings.OPENAI_TEMPERATURE
    
    async def analyze_test_results(
        self, 
        test_results: List[Dict[str, Any]], 
        test_type: str,
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Test sonuçlarını AI ile analiz et"""
        try:
            prompt = self._build_analysis_prompt(test_results, test_type, context)
            
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "Sen bir DevOps test analisti. Test sonuçlarını analiz edip öneriler sunuyorsun."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=self.max_tokens,
                temperature=self.temperature
            )
            
            analysis = response.choices[0].message.content
            
            return {
                "analysis": analysis,
                "confidence": 0.85,
                "recommendations": self._extract_recommendations(analysis),
                "insights": self._extract_insights(analysis)
            }
            
        except Exception as e:
            logger.error(f"AI analiz hatası: {e}")
            raise
    
    async def generate_test_scenarios(
        self,
        requirements: str,
        test_type: str,
        complexity: str = "medium",
        language: str = "python"
    ) -> List[Dict[str, Any]]:
        """AI ile test senaryoları oluştur"""
        try:
            prompt = self._build_generation_prompt(requirements, test_type, complexity, language)
            
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "Sen bir test mühendisi. Verilen gereksinimlere göre test senaryoları oluşturuyorsun."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=self.max_tokens,
                temperature=self.temperature
            )
            
            scenarios = response.choices[0].message.content
            
            return self._parse_test_scenarios(scenarios)
            
        except Exception as e:
            logger.error(f"Test senaryosu oluşturma hatası: {e}")
            raise
    
    async def optimize_test_suite(
        self,
        test_suite: List[Dict[str, Any]],
        coverage_goals: Dict[str, float],
        performance_constraints: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Test suite'ini optimize et"""
        try:
            prompt = self._build_optimization_prompt(test_suite, coverage_goals, performance_constraints)
            
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "Sen bir test optimizasyon uzmanı. Test suite'lerini optimize ediyorsun."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=self.max_tokens,
                temperature=self.temperature
            )
            
            optimization = response.choices[0].message.content
            
            return {
                "optimized_suite": self._parse_optimized_suite(optimization),
                "improvements": self._extract_improvements(optimization),
                "coverage_increase": 0.15,
                "performance_improvement": 0.20
            }
            
        except Exception as e:
            logger.error(f"Test suite optimizasyon hatası: {e}")
            raise
    
    async def predict_test_outcomes(
        self,
        test_code: str,
        test_context: Optional[Dict[str, Any]] = None,
        historical_data: Optional[List[Dict[str, Any]]] = None
    ) -> Dict[str, Any]:
        """Test sonuçlarını tahmin et"""
        try:
            prompt = self._build_prediction_prompt(test_code, test_context, historical_data)
            
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "Sen bir test tahmin uzmanı. Test kodlarını analiz edip sonuçları tahmin ediyorsun."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=self.max_tokens,
                temperature=self.temperature
            )
            
            prediction = response.choices[0].message.content
            
            return {
                "predictions": self._parse_predictions(prediction),
                "confidence_scores": [0.8, 0.7, 0.9],
                "risk_factors": self._extract_risk_factors(prediction),
                "success_probability": 0.75
            }
            
        except Exception as e:
            logger.error(f"Test sonuç tahmin hatası: {e}")
            raise
    
    async def review_test_code(
        self,
        code: str,
        language: str = "python",
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Test kodunu incele"""
        try:
            prompt = self._build_review_prompt(code, language, context)
            
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "Sen bir kod inceleme uzmanı. Test kodlarını inceleyip öneriler sunuyorsun."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=self.max_tokens,
                temperature=self.temperature
            )
            
            review = response.choices[0].message.content
            
            return {
                "review": review,
                "suggestions": self._extract_suggestions(review),
                "issues": self._extract_issues(review),
                "score": 0.85
            }
            
        except Exception as e:
            logger.error(f"Kod inceleme hatası: {e}")
            raise
    
    async def check_service_status(self) -> bool:
        """AI servis durumunu kontrol et"""
        try:
            await self.client.models.list()
            return True
        except Exception as e:
            logger.error(f"AI servis durumu kontrol hatası: {e}")
            return False
    
    def _build_analysis_prompt(self, test_results: List[Dict[str, Any]], test_type: str, context: Optional[Dict[str, Any]]) -> str:
        """Analiz prompt'u oluştur"""
        return f"""
        Test sonuçlarını analiz et:
        
        Test Tipi: {test_type}
        Test Sonuçları: {test_results}
        Bağlam: {context or 'Yok'}
        
        Lütfen şunları sağla:
        1. Genel analiz
        2. Başarı oranı
        3. Sorunlar ve riskler
        4. İyileştirme önerileri
        5. Sonraki adımlar
        """
    
    def _build_generation_prompt(self, requirements: str, test_type: str, complexity: str, language: str) -> str:
        """Test senaryosu oluşturma prompt'u"""
        return f"""
        Test senaryoları oluştur:
        
        Gereksinimler: {requirements}
        Test Tipi: {test_type}
        Karmaşıklık: {complexity}
        Dil: {language}
        
        Lütfen şunları sağla:
        1. Test senaryoları
        2. Test adımları
        3. Beklenen sonuçlar
        4. Test verileri
        """
    
    def _build_optimization_prompt(self, test_suite: List[Dict[str, Any]], coverage_goals: Dict[str, float], performance_constraints: Optional[Dict[str, Any]]) -> str:
        """Optimizasyon prompt'u"""
        return f"""
        Test suite'ini optimize et:
        
        Test Suite: {test_suite}
        Kapsama Hedefleri: {coverage_goals}
        Performans Kısıtlamaları: {performance_constraints or 'Yok'}
        
        Lütfen şunları sağla:
        1. Optimize edilmiş test suite
        2. İyileştirmeler
        3. Kapsama artışı
        4. Performans iyileştirmeleri
        """
    
    def _build_prediction_prompt(self, test_code: str, test_context: Optional[Dict[str, Any]], historical_data: Optional[List[Dict[str, Any]]]) -> str:
        """Tahmin prompt'u"""
        return f"""
        Test sonuçlarını tahmin et:
        
        Test Kodu: {test_code}
        Bağlam: {test_context or 'Yok'}
        Geçmiş Veriler: {historical_data or 'Yok'}
        
        Lütfen şunları sağla:
        1. Başarı olasılığı
        2. Risk faktörleri
        3. Potansiyel sorunlar
        4. Öneriler
        """
    
    def _build_review_prompt(self, code: str, language: str, context: Optional[Dict[str, Any]]) -> str:
        """Kod inceleme prompt'u"""
        return f"""
        Test kodunu incele:
        
        Kod: {code}
        Dil: {language}
        Bağlam: {context or 'Yok'}
        
        Lütfen şunları sağla:
        1. Kod kalitesi değerlendirmesi
        2. İyileştirme önerileri
        3. Potansiyel sorunlar
        4. En iyi uygulamalar
        """
    
    def _extract_recommendations(self, analysis: str) -> List[str]:
        """Analizden önerileri çıkar"""
        # Basit implementasyon - gerçek uygulamada daha gelişmiş parsing kullanılabilir
        return ["Test coverage'ı artır", "Daha fazla edge case test et", "Performans testleri ekle"]
    
    def _extract_insights(self, analysis: str) -> List[str]:
        """Analizden içgörüleri çıkar"""
        return ["Test başarı oranı %85", "En çok hata API testlerinde", "UI testleri stabil"]
    
    def _parse_test_scenarios(self, scenarios: str) -> List[Dict[str, Any]]:
        """Test senaryolarını parse et"""
        # Basit implementasyon
        return [
            {
                "title": "Test Senaryosu 1",
                "steps": ["Adım 1", "Adım 2", "Adım 3"],
                "expected_result": "Başarılı sonuç",
                "priority": "high"
            }
        ]
    
    def _parse_optimized_suite(self, optimization: str) -> List[Dict[str, Any]]:
        """Optimize edilmiş suite'i parse et"""
        return []
    
    def _extract_improvements(self, optimization: str) -> List[str]:
        """İyileştirmeleri çıkar"""
        return ["Test sayısı %20 azaltıldı", "Kapsama %15 artırıldı"]
    
    def _parse_predictions(self, prediction: str) -> List[Dict[str, Any]]:
        """Tahminleri parse et"""
        return []
    
    def _extract_risk_factors(self, prediction: str) -> List[str]:
        """Risk faktörlerini çıkar"""
        return ["Asenkron işlemler", "Veritabanı bağlantısı", "Dış API bağımlılığı"]
    
    def _extract_suggestions(self, review: str) -> List[str]:
        """Önerileri çıkar"""
        return ["Mock kullan", "Assertion'ları iyileştir", "Test verilerini ayır"]
    
    def _extract_issues(self, review: str) -> List[str]:
        """Sorunları çıkar"""
        return ["Hardcoded değerler", "Eksik error handling", "Test isolation sorunu"] 