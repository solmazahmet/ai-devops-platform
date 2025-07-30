"""
Test Database Models
Test ve test sonuçları modelleri
"""

from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, JSON, ForeignKey, Float
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.core.database import Base


class Test(Base):
    __tablename__ = "tests"
    
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    test_type = Column(String(50), nullable=False)  # unit, integration, e2e, performance
    status = Column(String(20), default="draft")  # draft, active, inactive, archived
    priority = Column(String(20), default="medium")  # low, medium, high, critical
    test_code = Column(Text, nullable=True)
    test_data = Column(JSON, nullable=True)
    expected_result = Column(Text, nullable=True)
    tags = Column(JSON, nullable=True)
    created_by = Column(String(255), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    results = relationship("TestResult", back_populates="test", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Test(id={self.id}, title='{self.title}', type='{self.test_type}')>"


class TestResult(Base):
    __tablename__ = "test_results"
    
    id = Column(Integer, primary_key=True, index=True)
    test_id = Column(Integer, ForeignKey("tests.id"), nullable=False)
    status = Column(String(20), nullable=False)  # passed, failed, skipped, error
    execution_time = Column(Float, nullable=True)  # seconds
    start_time = Column(DateTime(timezone=True), nullable=True)
    end_time = Column(DateTime(timezone=True), nullable=True)
    output = Column(Text, nullable=True)
    error_message = Column(Text, nullable=True)
    stack_trace = Column(Text, nullable=True)
    environment = Column(String(100), nullable=True)
    browser = Column(String(100), nullable=True)
    os = Column(String(100), nullable=True)
    test_metadata = Column(JSON, nullable=True)
    created_by = Column(String(255), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    test = relationship("Test", back_populates="results")
    
    def __repr__(self):
        return f"<TestResult(id={self.id}, test_id={self.test_id}, status='{self.status}')>" 