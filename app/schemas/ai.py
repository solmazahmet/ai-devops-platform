"""
AI Services Pydantic Schemas
AI analizi ve test üretimi için veri doğrulama
"""

from pydantic import BaseModel
from typing import Optional, List, Dict, Any


class AIAnalysisRequest(BaseModel):
    test_results: List[Dict[str, Any]]
    test_type: str
    context: Optional[Dict[str, Any]] = None


class AIAnalysisResponse(BaseModel):
    analysis: Dict[str, Any]
    confidence_score: float
    recommendations: List[str]
    insights: List[str]


class TestGenerationRequest(BaseModel):
    requirements: str
    test_type: str  # unit, integration, e2e, performance
    complexity: Optional[str] = "medium"  # low, medium, high
    language: Optional[str] = "python"
    framework: Optional[str] = None


class TestGenerationResponse(BaseModel):
    test_scenarios: List[Dict[str, Any]]
    total_scenarios: int
    estimated_time: Optional[str] = None
    coverage_estimate: Optional[float] = None


class CodeReviewRequest(BaseModel):
    code: str
    language: str = "python"
    context: Optional[Dict[str, Any]] = None


class CodeReviewResponse(BaseModel):
    review: str
    suggestions: List[str]
    issues: List[str]
    score: float


class TestOptimizationRequest(BaseModel):
    test_suite: List[Dict[str, Any]]
    coverage_goals: Dict[str, float]
    performance_constraints: Optional[Dict[str, Any]] = None


class TestOptimizationResponse(BaseModel):
    optimized_suite: List[Dict[str, Any]]
    improvements: List[str]
    coverage_increase: float
    performance_improvement: Optional[float] = None


class TestPredictionRequest(BaseModel):
    test_code: str
    context: Optional[Dict[str, Any]] = None
    historical_data: Optional[List[Dict[str, Any]]] = None


class TestPredictionResponse(BaseModel):
    predictions: List[Dict[str, Any]]
    confidence_scores: List[float]
    risk_factors: List[str]
    success_probability: float 