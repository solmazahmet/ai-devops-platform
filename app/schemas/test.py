"""
Test Pydantic Schemas
Test veri doğrulama ve serileştirme
"""

from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from datetime import datetime


class TestBase(BaseModel):
    title: str
    description: Optional[str] = None
    test_type: str  # unit, integration, e2e, performance
    priority: Optional[str] = "medium"
    test_code: Optional[str] = None
    test_data: Optional[Dict[str, Any]] = None
    expected_result: Optional[str] = None
    tags: Optional[List[str]] = None


class TestCreate(TestBase):
    pass


class TestUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    test_type: Optional[str] = None
    status: Optional[str] = None
    priority: Optional[str] = None
    test_code: Optional[str] = None
    test_data: Optional[Dict[str, Any]] = None
    expected_result: Optional[str] = None
    tags: Optional[List[str]] = None


class TestResponse(TestBase):
    id: int
    status: str
    created_by: str
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True


class TestList(BaseModel):
    tests: List[TestResponse]
    total: int
    page: int
    size: int


class TestResultBase(BaseModel):
    status: str  # passed, failed, skipped, error
    execution_time: Optional[float] = None
    output: Optional[str] = None
    error_message: Optional[str] = None
    environment: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


class TestResultCreate(TestResultBase):
    test_id: int


class TestResultResponse(TestResultBase):
    id: int
    test_id: int
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    created_by: str
    created_at: datetime
    
    class Config:
        from_attributes = True 