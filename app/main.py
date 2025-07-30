"""
FastAPI Ana Uygulama
AI-Powered DevOps Testing Platform
"""

from fastapi import FastAPI, HTTPException, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse
from fastapi.exceptions import RequestValidationError
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field, validator
import uvicorn
from typing import Dict, Any, Optional, List
import os
from dotenv import load_dotenv
import logging
import time
import json
from datetime import datetime
from json import JSONEncoder
import aiofiles

# Import AI components
from app.integrations.openai_client import OpenAIClient
from app.core.ai_engine import AIEngine
from app.modules.web_automation import WebAutomation, TestResult

# Import API routers
from app.api.v1.analytics import router as analytics_router
from app.api.v1.multi_ai import router as multi_ai_router
from app.api.v1.auth import router as auth_router
from app.api.v1.performance import router as performance_router

# Import performance monitoring
from app.core.performance import performance_monitor, monitor_endpoint
from app.core.cache import cache_manager

# Load environment variables
load_dotenv()

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="AI DevOps Platform",
    description="AI-powered DevOps testing and automation platform",
    version="1.0.0"
)

# CORS middleware with secure configuration
from app.core.config import get_cors_config

cors_config = get_cors_config()
app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_config["allow_origins"],
    allow_credentials=cors_config["allow_credentials"],
    allow_methods=cors_config["allow_methods"],
    allow_headers=cors_config["allow_headers"],
)

# Performance monitoring middleware
@app.middleware("http")
async def performance_monitoring_middleware(request: Request, call_next):
    """Middleware to monitor API performance"""
    start_time = time.time()
    
    response = await call_next(request)
    
    # Record performance metrics
    response_time = time.time() - start_time
    endpoint = f"{request.method} {request.url.path}"
    
    performance_monitor.record_request(
        endpoint=endpoint,
        response_time=response_time,
        status_code=response.status_code
    )
    
    # Add performance headers
    response.headers["X-Response-Time"] = f"{response_time:.4f}"
    response.headers["X-Process-Time"] = str(int(response_time * 1000))
    
    return response

# Custom JSON Encoder for datetime objects
class DateTimeEncoder(JSONEncoder):
    def default(self, obj):
        if isinstance(obj, datetime):
            return obj.isoformat()
        return super().default(obj)

# Include API routers
app.include_router(analytics_router)
app.include_router(multi_ai_router)
app.include_router(auth_router)
app.include_router(performance_router)

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")

# Initialize AI components
openai_client = OpenAIClient()
ai_engine = AIEngine(openai_client)
web_automation = WebAutomation(headless=False)  # Default GUI mode for high quality

class AICommand(BaseModel):
    """AI Command model - Gelişmiş validation"""
    command: str = Field(..., min_length=1, max_length=1000, description="Doğal dil komutu")
    context: Dict[str, Any] = Field(default_factory=dict, description="Ek bağlam bilgileri")
    platform: Optional[str] = Field(None, description="Hedef platform")
    test_type: Optional[str] = Field(None, description="Test türü")
    priority: Optional[str] = Field(None, description="Test önceliği")
    headless: bool = Field(default=False, description="Headless browser modu")
    
    @validator('command')
    def validate_command(cls, v):
        if not v or not v.strip():
            raise ValueError('Komut boş olamaz')
        return v.strip()
    
    @validator('platform')
    def validate_platform(cls, v):
        if v and v.lower() not in ['instagram', 'facebook', 'twitter', 'linkedin', 'youtube', 'tiktok', 'web']:
            raise ValueError(f'Desteklenmeyen platform: {v}')
        return v.lower() if v else v
    
    @validator('test_type')
    def validate_test_type(cls, v):
        if v and v.lower() not in ['ui', 'functional', 'performance', 'security', 'accessibility', 'e2e']:
            raise ValueError(f'Desteklenmeyen test türü: {v}')
        return v.lower() if v else v
    
    @validator('priority')
    def validate_priority(cls, v):
        if v and v.lower() not in ['low', 'medium', 'high', 'critical']:
            raise ValueError(f'Desteklenmeyen öncelik: {v}')
        return v.lower() if v else v

class AutomationStrategy(BaseModel):
    """Automation Strategy model"""
    platform: str = Field(..., description="Hedef platform")
    test_type: str = Field(default="functional", description="Test türü")
    steps: List[str] = Field(default_factory=list, description="Test adımları")
    priority: str = Field(default="medium", description="Test önceliği")
    estimated_time: int = Field(default=60, description="Tahmini süre (saniye)")
    test_scenarios: List[Dict[str, Any]] = Field(default_factory=list, description="Test senaryoları")

class AICommandResponse(BaseModel):
    """AI Command Response model - Gelişmiş format"""
    status: str = Field(..., description="İşlem durumu")
    command: str = Field(..., description="Orijinal komut")
    parsed_intent: str = Field(..., description="AI tarafından anlaşılan niyet")
    platform: Optional[str] = Field(None, description="Hedef platform")
    test_type: Optional[str] = Field(None, description="Test türü")
    confidence: float = Field(default=0.0, ge=0.0, le=1.0, description="AI güven skoru")
    test_strategy: Dict[str, Any] = Field(default_factory=dict, description="Test stratejisi")
    automation_results: Dict[str, Any] = Field(default_factory=dict, description="Otomasyon sonuçları")
    test_report_path: Optional[str] = Field(None, description="Test raporu dosya yolu")
    processing_time: float = Field(..., ge=0.0, description="İşlem süresi")
    message: str = Field(..., description="İşlem mesajı")
    timestamp: str = Field(default_factory=lambda: datetime.now().isoformat(), description="İşlem zamanı")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }

class ErrorResponse(BaseModel):
    """Error Response model"""
    status: str = Field(default="error", description="Hata durumu")
    error_code: str = Field(..., description="Hata kodu")
    error_message: str = Field(..., description="Hata mesajı")
    details: Optional[Dict[str, Any]] = Field(None, description="Hata detayları")
    timestamp: str = Field(default_factory=lambda: datetime.now().isoformat(), description="Hata zamanı")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }

# Global exception handlers
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Request validation error handler"""
    logger.error(f"Validation error: {exc.errors()}")
    
    error_details = []
    for error in exc.errors():
        error_details.append({
            "field": " -> ".join(str(loc) for loc in error["loc"]),
            "message": error["msg"],
            "type": error["type"]
        })
    
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content=ErrorResponse(
            error_code="VALIDATION_ERROR",
            error_message="Request validation failed",
            details={"validation_errors": error_details}
        ).dict()
    )

@app.exception_handler(json.JSONDecodeError)
async def json_decode_exception_handler(request: Request, exc: json.JSONDecodeError):
    """JSON decode error handler"""
    logger.error(f"JSON decode error: {exc}")
    
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content=ErrorResponse(
            error_code="JSON_DECODE_ERROR",
            error_message="Invalid JSON format",
            details={"json_error": str(exc), "position": exc.pos, "line": exc.lineno}
        ).dict()
    )

@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """General exception handler"""
    logger.error(f"Unexpected error: {exc}")
    
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=ErrorResponse(
            error_code="INTERNAL_ERROR",
            error_message="Internal server error",
            details={"error_type": type(exc).__name__, "error_message": str(exc)}
        ).dict()
    )

@app.get("/health")
async def health_check():
    """Sistem sağlık kontrolü"""
    try:
        openai_health = await openai_client.health_check()
        
        return {
            "status": "healthy", 
            "message": "AI DevOps Platform is running",
            "openai_health": openai_health,
            "timestamp": datetime.now().isoformat(),
            "version": "1.0.0"
        }
    except Exception as e:
        logger.error(f"Health check error: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Service health check failed: {str(e)}"
        )

@app.post("/api/v1/ai/command", response_model=AICommandResponse)
async def process_ai_command(command: AICommand):
    """Process natural language commands for testing automation - Gelişmiş error handling"""
    start_time = time.time()
    
    try:
        logger.info(f"AI command received: {command.command}")
        logger.info(f"Command context: {command.context}")
        
        # Input validation
        if not command.command or len(command.command.strip()) == 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Command cannot be empty"
            )
        
        # 1. AI ile komut analizi
        try:
            ai_command = await ai_engine.process_command(command.command, command.context)
        except Exception as e:
            logger.error(f"AI command processing error: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"AI command processing failed: {str(e)}"
            )
        
        # 2. Test stratejisi oluştur
        try:
            test_strategy = await ai_engine.generate_test_strategy(ai_command)
        except Exception as e:
            logger.error(f"Test strategy generation error: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Test strategy generation failed: {str(e)}"
            )
        
        # 3. AI stratejisini Selenium ile çalıştır
        automation_results = {}
        test_report_path = None
        
        if ai_command.platform:
            logger.info(f"AI stratejisi çalıştırılıyor: {ai_command.platform} (Headless: {command.headless})")
            
            try:
                # Headless mode kontrolü
                if command.headless:
                    # Headless mode için yeni automation instance oluştur
                    headless_automation = WebAutomation(headless=True)
                else:
                    headless_automation = web_automation
                
                # Test stratejisini dictionary'e çevir
                strategy_dict = {
                    "platform": test_strategy.platform,
                    "test_type": test_strategy.test_type,
                    "steps": test_strategy.steps,
                    "priority": test_strategy.priority,
                    "estimated_time": test_strategy.estimated_time,
                    "test_scenarios": test_strategy.test_scenarios
                }
                
                # AI stratejisini çalıştır
                test_result: TestResult = await headless_automation.execute_ai_strategy(
                    ai_command.platform, 
                    strategy_dict
                )
                
                # Test sonuçlarını dictionary'e çevir
                automation_results = web_automation.test_result_to_dict(test_result)
                
                # Test raporunu kaydet
                test_report_path = await headless_automation.save_test_report(
                    test_result, 
                    f"{ai_command.platform}_ai_test_report.json"
                )
                
                logger.info(f"AI stratejisi tamamlandı: {test_result.success}")
                
            except Exception as e:
                logger.error(f"Automation execution error: {e}")
                automation_results = {
                    "error": str(e),
                    "status": "failed",
                    "platform": ai_command.platform
                }
        
        # 4. İşlem süresini hesapla
        processing_time = time.time() - start_time
        
        # 5. Yanıt oluştur
        response = AICommandResponse(
            status="success",
            command=command.command,
            parsed_intent=ai_command.parsed_intent,
            platform=ai_command.platform,
            test_type=ai_command.test_type,
            confidence=ai_command.confidence,
            test_strategy={
                "platform": test_strategy.platform,
                "test_type": test_strategy.test_type,
                "steps": test_strategy.steps,
                "priority": test_strategy.priority,
                "estimated_time": test_strategy.estimated_time,
                "automation_script": test_strategy.automation_script,
                "test_scenarios": test_strategy.test_scenarios,
                "headless": command.headless
            },
            automation_results=automation_results,
            test_report_path=test_report_path,
            processing_time=processing_time,
            message=f"'{command.command}' komutu başarıyla işlendi. {ai_command.platform or 'Web'} platformu için AI stratejisi oluşturuldu ve Selenium otomasyonu çalıştırıldı. Headless: {command.headless}"
        )
        
        logger.info(f"AI command processed successfully: {response}")
        return response
        
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        logger.error(f"AI command processing error: {e}")
        
        processing_time = time.time() - start_time
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"AI command processing failed: {str(e)}"
        )

@app.get("/api/v1/ai/config")
async def get_ai_config():
    """AI konfigürasyon bilgilerini döndür"""
    try:
        return {
            "openai_config": openai_client.get_config(),
            "supported_platforms": ai_engine.supported_platforms,
            "test_types": ai_engine.test_types,
            "platform_keywords": ai_engine.platform_keywords,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Config error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Configuration retrieval failed: {str(e)}"
        )

@app.get("/api/v1/ai/test/{platform}")
async def run_platform_test(platform: str):
    """Belirli bir platform için hızlı test çalıştır"""
    try:
        # Platform validation
        if not platform or platform.strip() == "":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Platform parameter is required"
            )
        
        platform = platform.lower().strip()
        
        if platform not in ai_engine.supported_platforms:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Platform '{platform}' desteklenmiyor. Desteklenen platformlar: {ai_engine.supported_platforms}"
            )
        
        # Test komutu oluştur
        test_command = f"{platform} test et"
        
        # AI komut işleme
        try:
            ai_command = await ai_engine.process_command(test_command, {})
            test_strategy = await ai_engine.generate_test_strategy(ai_command)
        except Exception as e:
            logger.error(f"AI processing error: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"AI processing failed: {str(e)}"
            )
        
        # Test stratejisini dictionary'e çevir
        strategy_dict = {
            "platform": test_strategy.platform,
            "test_type": test_strategy.test_type,
            "steps": test_strategy.steps,
            "priority": test_strategy.priority,
            "estimated_time": test_strategy.estimated_time,
            "test_scenarios": test_strategy.test_scenarios
        }
        
        # AI stratejisini çalıştır
        try:
            test_result: TestResult = await web_automation.execute_ai_strategy(
                platform, 
                strategy_dict
            )
            
            # Test raporunu kaydet
            test_report_path = await web_automation.save_test_report(
                test_result, 
                f"{platform}_quick_test_report.json"
            )
            
        except Exception as e:
            logger.error(f"Automation error: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Automation execution failed: {str(e)}"
            )
        
        return {
            "status": "success",
            "platform": platform,
            "test_strategy": {
                "steps": test_strategy.steps,
                "priority": test_strategy.priority,
                "estimated_time": test_strategy.estimated_time
            },
            "automation_results": web_automation.test_result_to_dict(test_result),
            "test_report_path": test_report_path,
            "message": f"{platform} platformu için AI test tamamlandı",
            "timestamp": datetime.now().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Platform test error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

@app.post("/api/v1/automation/execute")
async def execute_automation_strategy(strategy: AutomationStrategy):
    """Manuel olarak automation stratejisi çalıştır"""
    try:
        logger.info(f"Manuel automation stratejisi çalıştırılıyor: {strategy.platform}")
        
        # Strategy validation
        if not strategy.platform or strategy.platform.strip() == "":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Platform is required"
            )
        
        # AI stratejisini çalıştır
        try:
            test_result: TestResult = await web_automation.execute_ai_strategy(
                strategy.platform, 
                strategy.dict()
            )
            
            # Test raporunu kaydet
            test_report_path = await web_automation.save_test_report(
                test_result, 
                f"{strategy.platform}_manual_test_report.json"
            )
            
        except Exception as e:
            logger.error(f"Automation execution error: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Automation execution failed: {str(e)}"
            )
        
        return {
            "status": "success",
            "platform": strategy.platform,
            "test_result": web_automation.test_result_to_dict(test_result),
            "test_report_path": test_report_path,
            "message": f"{strategy.platform} için manuel automation tamamlandı",
            "timestamp": datetime.now().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Manuel automation error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

@app.get("/api/v1/reports")
async def list_test_reports():
    """Test raporlarını listele"""
    try:
        reports_dir = "test_results"
        if not os.path.exists(reports_dir):
            return {
                "reports": [], 
                "total_count": 0,
                "message": "Henüz test raporu yok",
                "timestamp": datetime.now().isoformat()
            }
        
        reports = []
        for filename in os.listdir(reports_dir):
            if filename.endswith('.json'):
                file_path = os.path.join(reports_dir, filename)
                file_stats = os.stat(file_path)
                reports.append({
                    "filename": filename,
                    "path": file_path,
                    "size": file_stats.st_size,
                    "created": datetime.fromtimestamp(file_stats.st_ctime).isoformat(),
                    "modified": datetime.fromtimestamp(file_stats.st_mtime).isoformat()
                })
        
        # Tarihe göre sırala (en yeni önce)
        reports.sort(key=lambda x: x["modified"], reverse=True)
        
        return {
            "reports": reports,
            "total_count": len(reports),
            "message": f"{len(reports)} test raporu bulundu",
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"List reports error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

@app.get("/api/v1/reports/{filename}")
async def get_test_report(filename: str):
    """Belirli bir test raporunu getir"""
    try:
        import json
        
        # Filename validation
        if not filename or filename.strip() == "":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Filename is required"
            )
        
        # Security check - prevent directory traversal
        safe_path = os.path.abspath(os.path.join("test_results", filename))
        allowed_path = os.path.abspath("test_results")
        if not safe_path.startswith(allowed_path):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid filename - directory traversal not allowed"
            )
        
        report_path = os.path.join("test_results", filename)
        if not os.path.exists(report_path):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Test raporu bulunamadı"
            )
        
        # Use async file operations for better performance
        try:
            async with aiofiles.open(safe_path, 'r', encoding='utf-8') as f:
                content = await f.read()
                report_data = json.loads(content)
        except FileNotFoundError:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Test raporu bulunamadı"
            )
        
        return {
            "filename": filename,
            "data": report_data,
            "message": "Test raporu başarıyla getirildi",
            "timestamp": datetime.now().isoformat()
        }
        
    except HTTPException:
        raise
    except json.JSONDecodeError as e:
        logger.error(f"JSON decode error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Invalid JSON format in report file"
        )
    except Exception as e:
        logger.error(f"Get report error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

@app.get("/api/v1/automation/status")
async def get_automation_status():
    """Automation sistem durumunu kontrol et"""
    try:
        # WebDriver test
        web_automation_status = "unknown"
        try:
            if await web_automation.setup_driver():
                web_automation_status = "available"
                await web_automation.close_driver()
            else:
                web_automation_status = "unavailable"
        except Exception as e:
            web_automation_status = f"error: {str(e)}"
        
        return {
            "web_automation": {
                "status": web_automation_status,
                "headless": web_automation.headless,
                "timeout": web_automation.wait_timeout
            },
            "supported_platforms": list(web_automation.platform_selectors.keys()),
            "test_results_dir": web_automation.test_results_dir,
            "message": "Automation sistem durumu kontrol edildi",
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Automation status error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

@app.get("/dashboard")
async def serve_dashboard():
    """Serve the analytics dashboard"""
    return FileResponse("static/dashboard.html")

@app.get("/hello")
async def hello_world():
    return {"message": "Hello World!"}

@app.get("/")
async def root():
    return {
        "message": "Welcome to AI DevOps Platform",
        "version": "1.0.0",
        "endpoints": {
            "dashboard": "/dashboard",
            "health": "/health",
            "hello": "/hello",
            "ai_command": "/api/v1/ai/command",
            "ai_config": "/api/v1/ai/config",
            "platform_test": "/api/v1/ai/test/{platform}",
            "automation_execute": "/api/v1/automation/execute",
            "automation_status": "/api/v1/automation/status",
            "reports": "/api/v1/reports",
            "report_detail": "/api/v1/reports/{filename}",
            "analytics": "/api/v1/analytics/dashboard",
            "multi_ai": "/api/v1/multi-ai/models",
            "ai_generation": "/api/v1/multi-ai/generate",
            "auth_register": "/api/v1/auth/register",
            "auth_login": "/api/v1/auth/login",
            "auth_oauth": "/api/v1/auth/oauth/{provider}",
            "auth_profile": "/api/v1/auth/me",
            "performance_metrics": "/api/v1/performance/metrics",
            "performance_health": "/api/v1/performance/health",
            "performance_benchmark": "/api/v1/performance/benchmark",
            "docs": "/docs"
        },
        "features": [
            "Natural Language Command Processing",
            "Multi-Model AI Support (OpenAI, Claude, Gemini)",
            "OAuth2 Authentication & User Management",
            "Advanced Analytics Dashboard",
            "AI-Powered Test Strategy Generation", 
            "Selenium Web Automation",
            "Instagram and Social Media Testing",
            "Structured Test Reports",
            "Real-time Test Execution",
            "AI Insights and Optimization",
            "Cost-Optimized AI Usage",
            "Screenshot and Performance Monitoring",
            "JWT Token Authentication",
            "Role-Based Access Control (RBAC)",
            "Redis Caching System",
            "Real-time Performance Metrics",
            "Database Connection Pooling",
            "Automated Performance Benchmarking"
        ],
        "timestamp": datetime.now().isoformat()
    }

# Startup and shutdown events
@app.on_event("startup")
async def startup_event():
    """Initialize services on startup"""
    try:
        # Initialize cache
        await cache_manager.init_redis()
        logger.info("Cache system initialized")
        
        # Log startup metrics
        performance_monitor.record_metric(
            name="application_startup",
            value=1,
            unit="event",
            tags={"event": "startup"}
        )
        
        logger.info("Application startup completed")
        
    except Exception as e:
        logger.error(f"Startup error: {e}")
        raise

@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    try:
        # Log shutdown metrics
        performance_monitor.record_metric(
            name="application_shutdown",
            value=1,
            unit="event",
            tags={"event": "shutdown"}
        )
        
        logger.info("Application shutdown completed")
        
    except Exception as e:
        logger.error(f"Shutdown error: {e}")

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000) 