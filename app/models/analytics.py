"""
Analytics Models
Test execution analytics and metrics models
"""

from sqlalchemy import Column, Integer, String, DateTime, Float, Boolean, Text, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql import func
from datetime import datetime
from enum import Enum
from typing import Dict, Any, List, Optional
from pydantic import BaseModel

from app.core.database import Base

class TestStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    PASSED = "passed"
    FAILED = "failed"
    SKIPPED = "skipped"
    ERROR = "error"

class TestExecution(Base):
    """Test execution tracking model"""
    __tablename__ = "test_executions"
    
    id = Column(Integer, primary_key=True, index=True)
    test_id = Column(String, index=True, nullable=False)
    test_name = Column(String, nullable=False)
    test_type = Column(String, nullable=False)  # ui, api, functional, performance
    platform = Column(String, nullable=True)  # instagram, facebook, web, mobile
    
    # Execution details
    status = Column(String, default=TestStatus.PENDING)
    start_time = Column(DateTime, default=func.now())
    end_time = Column(DateTime, nullable=True)
    duration = Column(Float, nullable=True)  # seconds
    
    # Results
    success_rate = Column(Float, default=0.0)
    steps_total = Column(Integer, default=0)
    steps_passed = Column(Integer, default=0)
    steps_failed = Column(Integer, default=0)
    
    # AI Analysis
    ai_confidence = Column(Float, nullable=True)
    ai_suggestions = Column(JSON, nullable=True)
    error_category = Column(String, nullable=True)
    
    # Resources
    cpu_usage = Column(Float, nullable=True)
    memory_usage = Column(Float, nullable=True)
    network_requests = Column(Integer, default=0)
    
    # Files
    screenshot_paths = Column(JSON, nullable=True)
    log_file_path = Column(String, nullable=True)
    report_path = Column(String, nullable=True)
    
    # Metadata
    tags = Column(JSON, nullable=True)
    environment = Column(String, default="development")
    browser = Column(String, nullable=True)
    browser_version = Column(String, nullable=True)
    
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

class TestSuite(Base):
    """Test suite model"""
    __tablename__ = "test_suites"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False, index=True)
    description = Column(Text, nullable=True)
    
    # Suite configuration
    total_tests = Column(Integer, default=0)
    parallel_execution = Column(Boolean, default=False)
    max_workers = Column(Integer, default=1)
    timeout = Column(Integer, default=300)  # seconds
    
    # Results summary
    last_execution_time = Column(DateTime, nullable=True)
    last_duration = Column(Float, nullable=True)
    last_success_rate = Column(Float, nullable=True)
    
    # Statistics
    total_executions = Column(Integer, default=0)
    average_duration = Column(Float, nullable=True)
    average_success_rate = Column(Float, nullable=True)
    
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

class Analytics(Base):
    """Analytics aggregation model"""
    __tablename__ = "analytics"
    
    id = Column(Integer, primary_key=True, index=True)
    date = Column(DateTime, default=func.now(), index=True)
    metric_type = Column(String, nullable=False, index=True)  # daily, weekly, monthly
    
    # Test metrics
    total_tests = Column(Integer, default=0)
    passed_tests = Column(Integer, default=0)
    failed_tests = Column(Integer, default=0)
    skipped_tests = Column(Integer, default=0)
    success_rate = Column(Float, default=0.0)
    
    # Performance metrics
    average_duration = Column(Float, nullable=True)
    total_duration = Column(Float, nullable=True)
    cpu_usage_avg = Column(Float, nullable=True)
    memory_usage_avg = Column(Float, nullable=True)
    
    # Platform breakdown
    platform_stats = Column(JSON, nullable=True)  # {"instagram": 50, "facebook": 30}
    test_type_stats = Column(JSON, nullable=True)  # {"ui": 60, "api": 40}
    error_categories = Column(JSON, nullable=True)  # {"timeout": 5, "element_not_found": 3}
    
    # AI metrics
    ai_confidence_avg = Column(Float, nullable=True)
    ai_suggestions_count = Column(Integer, default=0)
    
    created_at = Column(DateTime, default=func.now())

# Pydantic schemas for API
class TestExecutionResponse(BaseModel):
    id: int
    test_id: str
    test_name: str
    test_type: str
    platform: Optional[str]
    status: str
    start_time: datetime
    end_time: Optional[datetime]
    duration: Optional[float]
    success_rate: float
    steps_total: int
    steps_passed: int
    steps_failed: int
    ai_confidence: Optional[float]
    environment: str
    
    class Config:
        from_attributes = True

class AnalyticsResponse(BaseModel):
    date: datetime
    metric_type: str
    total_tests: int
    passed_tests: int
    failed_tests: int
    success_rate: float
    average_duration: Optional[float]
    platform_stats: Optional[Dict[str, Any]]
    test_type_stats: Optional[Dict[str, Any]]
    error_categories: Optional[Dict[str, Any]]
    
    class Config:
        from_attributes = True

class DashboardMetrics(BaseModel):
    """Dashboard overview metrics"""
    # Overview
    total_tests_today: int = 0
    total_tests_week: int = 0
    success_rate_today: float = 0.0
    success_rate_week: float = 0.0
    
    # Performance
    average_duration_today: Optional[float] = None
    fastest_test_today: Optional[float] = None
    slowest_test_today: Optional[float] = None
    
    # Platform breakdown
    platform_distribution: Dict[str, int] = {}
    test_type_distribution: Dict[str, int] = {}
    
    # Trends
    daily_trend: List[Dict[str, Any]] = []  # Last 7 days
    hourly_trend: List[Dict[str, Any]] = []  # Last 24 hours
    
    # Recent activities
    recent_executions: List[TestExecutionResponse] = []
    recent_failures: List[TestExecutionResponse] = []
    
    # AI insights
    ai_insights: List[Dict[str, Any]] = []
    improvement_suggestions: List[str] = []