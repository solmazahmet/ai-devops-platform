"""
Pytest Configuration ve Test Fixtures
Test ortamı için gerekli ayarlar ve fixtures
"""

import pytest
import asyncio
from typing import Generator, Dict, Any
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.main import app
from app.core.database import get_db, Base
from app.core.config import settings
from app.models.user import User
from app.models.test import Test, TestResult
from app.core.security import get_password_hash


# Test database engine
test_engine = create_engine(
    settings.TEST_DATABASE_URL,
    poolclass=StaticPool,
    connect_args={"check_same_thread": False}
)

TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)


@pytest.fixture(scope="session")
def event_loop():
    """Event loop fixture"""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="function")
def db_session():
    """Test database session"""
    # Create tables
    Base.metadata.create_all(bind=test_engine)
    
    # Create session
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()
        # Drop tables
        Base.metadata.drop_all(bind=test_engine)


@pytest.fixture
def client(db_session) -> Generator:
    """Test client"""
    def override_get_db():
        try:
            yield db_session
        finally:
            pass
    
    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


@pytest.fixture
def test_user(db_session) -> Dict[str, Any]:
    """Test kullanıcısı oluştur"""
    user_data = {
        "email": "test@example.com",
        "username": "testuser",
        "full_name": "Test User",
        "hashed_password": get_password_hash("testpassword"),
        "is_active": True
    }
    
    user = User(**user_data)
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    
    return {
        "id": user.id,
        "email": user.email,
        "username": user.username,
        "full_name": user.full_name,
        "password": "testpassword"
    }


@pytest.fixture
def test_user_token(client, test_user) -> str:
    """Test kullanıcısı için token al"""
    response = client.post(
        "/api/v1/auth/login",
        data={
            "username": test_user["email"],
            "password": test_user["password"]
        }
    )
    return response.json()["access_token"]


@pytest.fixture
def test_test(db_session, test_user) -> Dict[str, Any]:
    """Test verisi oluştur"""
    test_data = {
        "title": "Test Test",
        "description": "Test açıklaması",
        "test_type": "unit",
        "priority": "medium",
        "test_code": "def test_function(): pass",
        "created_by": test_user["email"]
    }
    
    test = Test(**test_data)
    db_session.add(test)
    db_session.commit()
    db_session.refresh(test)
    
    return {
        "id": test.id,
        "title": test.title,
        "description": test.description,
        "test_type": test.test_type,
        "priority": test.priority,
        "created_by": test.created_by
    }


@pytest.fixture
def test_result(db_session, test_test) -> Dict[str, Any]:
    """Test sonucu oluştur"""
    result_data = {
        "test_id": test_test["id"],
        "status": "passed",
        "execution_time": 1.5,
        "output": "Test başarılı",
        "created_by": test_test["created_by"]
    }
    
    result = TestResult(**result_data)
    db_session.add(result)
    db_session.commit()
    db_session.refresh(result)
    
    return {
        "id": result.id,
        "test_id": result.test_id,
        "status": result.status,
        "execution_time": result.execution_time,
        "output": result.output
    }


@pytest.fixture
def auth_headers(test_user_token) -> Dict[str, str]:
    """Authorization headers"""
    return {"Authorization": f"Bearer {test_user_token}"}


@pytest.fixture
def sample_test_data() -> Dict[str, Any]:
    """Örnek test verisi"""
    return {
        "title": "API Test",
        "description": "API endpoint testi",
        "test_type": "integration",
        "priority": "high",
        "test_code": """
import requests

def test_api_endpoint():
    response = requests.get("http://localhost:8000/health")
    assert response.status_code == 200
        """,
        "expected_result": "Status code 200",
        "tags": ["api", "health-check"]
    }


@pytest.fixture
def sample_ai_analysis_data() -> Dict[str, Any]:
    """Örnek AI analiz verisi"""
    return {
        "test_results": [
            {
                "status": "passed",
                "execution_time": 1.2,
                "environment": "test"
            },
            {
                "status": "failed",
                "execution_time": 2.1,
                "error_message": "Assertion failed",
                "environment": "test"
            }
        ],
        "test_type": "unit",
        "context": {
            "test_suite": "user_tests",
            "coverage": 85.5
        }
    }


@pytest.fixture
def sample_jira_issue_data() -> Dict[str, Any]:
    """Örnek Jira issue verisi"""
    return {
        "summary": "Test Hatası: API Endpoint",
        "description": "API endpoint testi başarısız oldu",
        "issue_type": "Bug",
        "priority": "High",
        "assignee": "testuser",
        "labels": ["test-failure", "api"],
        "project_key": "TEST"
    } 