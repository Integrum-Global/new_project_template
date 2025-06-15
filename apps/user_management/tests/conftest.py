"""
Shared fixtures for User Management tests

This module provides common fixtures and utilities for all test types.
"""

import asyncio
import uuid
from datetime import datetime
from typing import Any, AsyncGenerator, Dict

import pytest
from fastapi.testclient import TestClient
from httpx import AsyncClient

# App imports
from apps.user_management.config import Settings
from apps.user_management.core.repositories import (
    audit_repository,
    permission_repository,
    role_repository,
    session_repository,
    user_repository,
)

# Kailash imports
from kailash.middleware import AgentUIMiddleware, create_gateway
from kailash.runtime.local import LocalRuntime
from kailash.workflow import WorkflowBuilder


# Test settings
@pytest.fixture
def test_settings():
    """Test-specific settings."""
    return Settings(
        DATABASE_URL="postgresql://kailash:kailash@localhost:5433/kailash_test",
        JWT_SECRET_KEY="test-secret-key",
        SESSION_TIMEOUT_MINUTES=30,
        ENABLE_METRICS=False,
        ENABLE_AUDIT_LOGGING=True,
    )


# Database fixtures
@pytest.fixture
async def setup_database():
    """Setup test database."""
    # Mock database setup for tests
    yield
    # Cleanup handled by test teardown


# Runtime fixtures
@pytest.fixture
async def test_runtime():
    """Test runtime instance."""
    return LocalRuntime(enable_async=True, enable_monitoring=False, debug=True)


@pytest.fixture
async def test_agent_ui():
    """Test Agent UI middleware instance."""
    return AgentUIMiddleware(
        max_sessions=100,
        session_timeout_minutes=30,
        enable_persistence=False,
        enable_metrics=False,
    )


# API client fixtures
@pytest.fixture
async def test_app(test_settings):
    """Test FastAPI application."""
    app = create_gateway(
        title="Test User Management API", version="1.0.0", enable_docs=False
    )

    return app


@pytest.fixture
async def test_client(test_app) -> AsyncGenerator[AsyncClient, None]:
    """Async test client."""
    async with AsyncClient(app=test_app, base_url="http://test") as client:
        yield client


@pytest.fixture
def sync_test_client(test_app) -> TestClient:
    """Synchronous test client for simple tests."""
    return TestClient(test_app)


# Test data fixtures
@pytest.fixture
def sample_user_data():
    """Sample user data for testing."""
    return {
        "email": f"test_{uuid.uuid4().hex[:8]}@example.com",
        "first_name": "Test",
        "last_name": "User",
        "department": "Engineering",
        "title": "Software Engineer",
        "phone": "+1-555-0123",
        "enable_sso": True,
        "enable_mfa": True,
    }


@pytest.fixture
def sample_role_data():
    """Sample role data for testing."""
    return {
        "name": f"test_role_{uuid.uuid4().hex[:8]}",
        "description": "Test role for unit tests",
        "permissions": ["users:read", "users:write", "roles:read"],
        "is_system_role": False,
    }


@pytest.fixture
async def auth_token():
    """Generate auth token for testing."""
    from datetime import timedelta

    import jwt

    payload = {
        "sub": str(uuid.uuid4()),
        "email": "test@example.com",
        "exp": datetime.utcnow() + timedelta(hours=1),
    }

    token = jwt.encode(payload, "test-secret-key", algorithm="HS256")
    return token


# Performance testing fixtures
@pytest.fixture
def performance_timer():
    """Timer for performance tests."""
    import time

    class Timer:
        def __init__(self):
            self.start_time = None
            self.end_time = None

        def start(self):
            self.start_time = time.perf_counter()

        def stop(self):
            self.end_time = time.perf_counter()
            return self.elapsed_ms

        @property
        def elapsed_ms(self):
            if self.start_time and self.end_time:
                return (self.end_time - self.start_time) * 1000
            return 0

    return Timer()


# Event loop configuration
@pytest.fixture(scope="session")
def event_loop():
    """Create an event loop for async tests."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()
