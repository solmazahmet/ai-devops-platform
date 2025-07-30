"""
Multi-AI API Endpoints
Enhanced AI functionality with multiple model support
"""

from fastapi import APIRouter, HTTPException, status, Query
from fastapi.responses import JSONResponse
from typing import Dict, List, Any, Optional
from pydantic import BaseModel, Field
import logging
from datetime import datetime

from app.integrations.multi_ai_client import multi_ai_manager, AIModel, AIProvider
from app.core.ai_engine import AIEngine
from app.integrations.openai_client import OpenAIClient

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/multi-ai", tags=["Multi-AI"])

class AIGenerationRequest(BaseModel):
    """AI generation request model"""
    prompt: str = Field(..., min_length=1, max_length=5000, description="Input prompt")
    model: Optional[str] = Field(None, description="Specific AI model to use")
    max_tokens: int = Field(2000, ge=1, le=4000, description="Maximum tokens to generate")
    temperature: float = Field(0.7, ge=0.0, le=2.0, description="Generation temperature")
    use_fallback: bool = Field(True, description="Use fallback models if primary fails")
    context: Dict[str, Any] = Field(default_factory=dict, description="Additional context")

class AIGenerationResponse(BaseModel):
    """AI generation response model"""
    content: str
    model: str
    provider: str
    tokens_used: int
    cost: float
    confidence: float
    processing_time: float
    timestamp: str
    metadata: Dict[str, Any] = Field(default_factory=dict)

class ModelComparisonRequest(BaseModel):
    """Model comparison request"""
    prompt: str = Field(..., min_length=1, max_length=2000)
    models: List[str] = Field(..., min_items=2, max_items=5, description="Models to compare")
    criteria: List[str] = Field(default=["accuracy", "creativity", "coherence"], description="Comparison criteria")

@router.get("/models", response_model=Dict[str, Any])
async def get_available_models():
    """
    Get list of available AI models and their status
    
    Returns:
    - List of available models
    - Provider information
    - Health status of each model
    - Fallback order and configuration
    """
    try:
        # Get available models
        models = multi_ai_manager.get_available_models()
        
        # Get health status
        health_status = await multi_ai_manager.health_check_all()
        
        # Enhance model information with health data
        enhanced_models = []
        for model in models:
            model_name = model["name"]
            health_info = health_status.get(model_name, {"status": "unknown", "available": False})
            
            enhanced_models.append({
                **model,
                "health": health_info,
                "last_checked": datetime.now().isoformat()
            })
        
        return {
            "models": enhanced_models,
            "total_models": len(enhanced_models),
            "healthy_models": len([m for m in enhanced_models if m["health"].get("available", False)]),
            "providers": list(set(model["provider"] for model in enhanced_models)),
            "configuration": {
                "fallback_order": multi_ai_manager.fallback_order,
                "load_balancing_enabled": multi_ai_manager.load_balancing
            },
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error getting available models: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get available models: {str(e)}"
        )

@router.post("/generate", response_model=AIGenerationResponse)
async def generate_with_ai(request: AIGenerationRequest):
    """
    Generate content using specified AI model with fallback support
    
    Features:
    - Multi-model support (OpenAI, Anthropic, Google)
    - Automatic fallback if primary model fails
    - Cost tracking and token usage
    - Performance metrics
    """
    start_time = datetime.now()
    
    try:
        logger.info(f"AI generation request: model={request.model}, tokens={request.max_tokens}")
        
        # Generate response using multi-AI manager
        ai_response = await multi_ai_manager.generate_response(
            prompt=request.prompt,
            model=request.model,
            use_fallback=request.use_fallback,
            max_tokens=request.max_tokens,
            temperature=request.temperature,
            **request.context
        )
        
        # Calculate processing time
        processing_time = (datetime.now() - start_time).total_seconds()
        
        response = AIGenerationResponse(
            content=ai_response.content,
            model=ai_response.model,
            provider=ai_response.provider,
            tokens_used=ai_response.tokens_used,
            cost=ai_response.cost,
            confidence=ai_response.confidence,
            processing_time=processing_time,
            timestamp=ai_response.timestamp.isoformat(),
            metadata=ai_response.metadata
        )
        
        logger.info(f"AI generation successful: {ai_response.model}, tokens: {ai_response.tokens_used}, cost: ${ai_response.cost:.4f}")
        
        return response
        
    except Exception as e:
        logger.error(f"AI generation failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"AI generation failed: {str(e)}"
        )

@router.post("/compare-models")
async def compare_models(request: ModelComparisonRequest):
    """
    Compare responses from multiple AI models for the same prompt
    
    Useful for:
    - A/B testing different models
    - Quality comparison
    - Cost-benefit analysis
    - Model selection optimization
    """
    try:
        logger.info(f"Model comparison request: {request.models}")
        
        # Generate responses from each model
        results = {}
        total_cost = 0.0
        
        for model_name in request.models:
            try:
                start_time = datetime.now()
                
                ai_response = await multi_ai_manager.generate_response(
                    prompt=request.prompt,
                    model=model_name,
                    use_fallback=False,  # Don't use fallback for comparison
                    max_tokens=1000,
                    temperature=0.7
                )
                
                processing_time = (datetime.now() - start_time).total_seconds()
                total_cost += ai_response.cost
                
                results[model_name] = {
                    "content": ai_response.content,
                    "model": ai_response.model,
                    "provider": ai_response.provider,
                    "tokens_used": ai_response.tokens_used,
                    "cost": ai_response.cost,
                    "processing_time": processing_time,
                    "success": True,
                    "error": None
                }
                
            except Exception as e:
                logger.warning(f"Model {model_name} failed: {e}")
                results[model_name] = {
                    "content": None,
                    "success": False,
                    "error": str(e),
                    "cost": 0.0,
                    "processing_time": 0.0
                }
        
        # Generate comparison analysis
        successful_models = [name for name, result in results.items() if result["success"]]
        
        analysis = {
            "summary": {
                "total_models_tested": len(request.models),
                "successful_models": len(successful_models),
                "total_cost": round(total_cost, 4),
                "average_cost": round(total_cost / len(successful_models), 4) if successful_models else 0
            },
            "results": results,
            "recommendations": _generate_model_recommendations(results, request.criteria),
            "timestamp": datetime.now().isoformat()
        }
        
        return analysis
        
    except Exception as e:
        logger.error(f"Model comparison failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Model comparison failed: {str(e)}"
        )

class EnhancedCommandRequest(BaseModel):
    """Enhanced command request model"""
    command: str = Field(..., description="Natural language command")
    preferred_model: Optional[str] = Field(None, description="Preferred AI model")
    include_insights: bool = Field(True, description="Include AI insights")
    generate_alternatives: bool = Field(False, description="Generate alternative strategies")

@router.post("/enhanced-command")
async def process_enhanced_command(request: EnhancedCommandRequest):
    """
    Enhanced command processing with multi-AI support
    
    Features:
    - Multi-model command analysis
    - AI-powered insights generation
    - Alternative strategy suggestions
    - Cost-optimized model selection
    """
    try:
        # Initialize AI engine
        openai_client = OpenAIClient()
        ai_engine = AIEngine(openai_client)
        
        # Process command with specified model
        ai_command = await ai_engine.process_command(
            command=request.command,
            model=request.preferred_model
        )
        
        # Generate test strategy
        test_strategy = await ai_engine.generate_test_strategy(
            ai_command=ai_command,
            model=request.preferred_model
        )
        
        response_data = {
            "command_analysis": {
                "original_command": ai_command.original_command,
                "parsed_intent": ai_command.parsed_intent,
                "platform": ai_command.platform,
                "test_type": ai_command.test_type,
                "confidence": ai_command.confidence,
                "parameters": ai_command.parameters
            },
            "test_strategy": {
                "platform": test_strategy.platform,
                "test_type": test_strategy.test_type,
                "steps": test_strategy.steps,
                "priority": test_strategy.priority,
                "estimated_time": test_strategy.estimated_time,
                "test_scenarios": test_strategy.test_scenarios
            },
            "ai_metadata": {
                "model_used": request.preferred_model or "auto-selected",
                "processing_timestamp": datetime.now().isoformat()
            }
        }
        
        # Add AI insights if requested
        if request.include_insights:
            try:
                insights = await ai_engine.generate_ai_insights(
                    test_results={"command": request.command, "strategy": test_strategy.dict()},
                    model=request.preferred_model
                )
                response_data["ai_insights"] = insights
            except Exception as e:
                logger.warning(f"Failed to generate insights: {e}")
                response_data["ai_insights"] = {"error": "Insights generation failed"}
        
        # Generate alternatives if requested
        if request.generate_alternatives:
            try:
                alternatives = []
                alternative_models = ["openai_gpt4", "claude_sonnet", "gemini_pro"]
                
                for alt_model in alternative_models:
                    if alt_model != request.preferred_model:
                        try:
                            alt_strategy = await ai_engine.generate_test_strategy(
                                ai_command=ai_command,
                                model=alt_model
                            )
                            alternatives.append({
                                "model": alt_model,
                                "strategy": alt_strategy.dict()
                            })
                        except:
                            continue
                
                response_data["alternatives"] = alternatives[:2]  # Limit to 2 alternatives
                
            except Exception as e:
                logger.warning(f"Failed to generate alternatives: {e}")
        
        return response_data
        
    except Exception as e:
        logger.error(f"Enhanced command processing failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Enhanced command processing failed: {str(e)}"
        )

@router.get("/health")
async def multi_ai_health_check():
    """
    Comprehensive health check for all AI providers
    
    Returns detailed status for each model and provider
    """
    try:
        health_status = await multi_ai_manager.health_check_all()
        
        # Calculate overall health metrics
        total_models = len(health_status)
        healthy_models = len([status for status in health_status.values() if status.get("available", False)])
        health_percentage = (healthy_models / total_models * 100) if total_models > 0 else 0
        
        overall_status = "healthy" if health_percentage >= 80 else "degraded" if health_percentage >= 50 else "unhealthy"
        
        return {
            "overall_status": overall_status,
            "health_percentage": round(health_percentage, 1),
            "total_models": total_models,
            "healthy_models": healthy_models,
            "model_status": health_status,
            "configuration": {
                "fallback_enabled": len(multi_ai_manager.fallback_order) > 1,
                "load_balancing": multi_ai_manager.load_balancing
            },
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Multi-AI health check failed: {e}")
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={
                "overall_status": "error",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
        )

class CostOptimizationRequest(BaseModel):
    """Cost optimization request model"""
    usage_data: Dict[str, Any]
    target_cost_reduction: float = Field(0.2, description="Target cost reduction (0.1 = 10%)")

@router.post("/optimize-costs")
async def optimize_ai_costs(request: CostOptimizationRequest):
    """
    AI cost optimization recommendations
    
    Analyzes usage patterns and suggests cost optimization strategies
    """
    try:
        # Simple cost optimization logic
        recommendations = []
        
        # Analyze model usage
        if "model_usage" in request.usage_data:
            expensive_models = ["gpt-4", "claude-3-opus"]
            cheaper_alternatives = {
                "gpt-4": "gpt-3.5-turbo",
                "claude-3-opus": "claude-3-haiku"
            }
            
            for model, usage in request.usage_data["model_usage"].items():
                if model in expensive_models and usage > 1000:  # High usage
                    alternative = cheaper_alternatives.get(model)
                    if alternative:
                        recommendations.append({
                            "type": "model_substitution",
                            "current_model": model,
                            "suggested_model": alternative,
                            "potential_savings": "60-80%",
                            "trade_offs": "Slightly lower quality for significant cost savings"
                        })
        
        # Load balancing recommendation
        if not multi_ai_manager.load_balancing:
            recommendations.append({
                "type": "load_balancing",
                "suggestion": "Enable load balancing to distribute requests across cheaper models",
                "potential_savings": "20-40%",
                "implementation": "Enable load balancing in AI configuration"
            })
        
        # Caching recommendation
        recommendations.append({
            "type": "response_caching",
            "suggestion": "Implement response caching for repeated queries",
            "potential_savings": "30-50%",
            "implementation": "Cache responses for common test commands"
        })
        
        return {
            "current_cost_analysis": request.usage_data,
            "target_reduction": f"{request.target_cost_reduction * 100}%",
            "recommendations": recommendations,
            "estimated_savings": f"{request.target_cost_reduction * 100}% - {(request.target_cost_reduction + 0.2) * 100}%",
            "implementation_priority": [
                "Enable load balancing",
                "Implement response caching", 
                "Consider model alternatives for high-volume requests"
            ],
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Cost optimization analysis failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Cost optimization failed: {str(e)}"
        )

def _generate_model_recommendations(results: Dict[str, Any], criteria: List[str]) -> List[Dict[str, Any]]:
    """Generate model recommendations based on comparison results"""
    recommendations = []
    
    # Find the most cost-effective model
    successful_results = {k: v for k, v in results.items() if v.get("success", False)}
    
    if successful_results:
        # Cost efficiency
        cheapest_model = min(successful_results.items(), key=lambda x: x[1]["cost"])
        recommendations.append({
            "category": "cost_efficiency",
            "model": cheapest_model[0],
            "reasoning": f"Lowest cost at ${cheapest_model[1]['cost']:.4f}",
            "use_case": "High-volume, budget-conscious applications"
        })
        
        # Speed
        fastest_model = min(successful_results.items(), key=lambda x: x[1]["processing_time"])
        recommendations.append({
            "category": "performance",
            "model": fastest_model[0],
            "reasoning": f"Fastest response at {fastest_model[1]['processing_time']:.2f}s",
            "use_case": "Real-time applications requiring quick responses"
        })
        
        # Overall balance (cost vs speed)
        balanced_scores = {}
        for model, result in successful_results.items():
            # Normalize scores (lower is better for both cost and time)
            cost_score = result["cost"] / max(r["cost"] for r in successful_results.values())
            time_score = result["processing_time"] / max(r["processing_time"] for r in successful_results.values())
            balanced_scores[model] = (cost_score + time_score) / 2
        
        best_balanced = min(balanced_scores.items(), key=lambda x: x[1])
        recommendations.append({
            "category": "balanced",
            "model": best_balanced[0],
            "reasoning": "Best balance of cost and performance",
            "use_case": "General-purpose applications"
        })
    
    return recommendations