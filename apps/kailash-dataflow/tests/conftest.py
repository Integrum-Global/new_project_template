"""
DataFlow Test Configuration - Standalone Version

Provides fixtures and utilities for DataFlow testing without external dependencies.
"""

import asyncio
import os
import sys
from pathlib import Path

import pytest

# Add parent directories to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))  # kailash-dataflow/src
sys.path.insert(0, str(Path(__file__).parent.parent))  # apps/kailash-dataflow
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))  # project root

from dataflow import DataFlow, DataFlowConfig

from kailash.runtime.local import LocalRuntime
from kailash.workflow.builder import WorkflowBuilder


@pytest.fixture(scope="session")
def event_loop():
    """Create an event loop for async tests."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def dataflow():
    """Create a DataFlow instance for testing."""
    # Use in-memory SQLite for tests
    return DataFlow(database_url="sqlite:///:memory:")


@pytest.fixture
def workflow_builder():
    """Create a WorkflowBuilder instance."""
    return WorkflowBuilder()


@pytest.fixture
def runtime():
    """Create a LocalRuntime instance."""
    return LocalRuntime()


@pytest.fixture
def sample_user_model():
    """Create a sample User model."""
    db = DataFlow(database_url="sqlite:///:memory:")

    @db.model
    class User:
        name: str
        email: str
        active: bool = True

    return User, db


@pytest.fixture
def sample_product_model():
    """Create a sample Product model."""
    db = DataFlow(database_url="sqlite:///:memory:")

    @db.model
    class Product:
        name: str
        price: float
        category: str = "general"

    return Product, db


# Test data fixtures
@pytest.fixture
def sample_users():
    """Sample user data for testing."""
    return [
        {"name": "Alice", "email": "alice@example.com", "active": True},
        {"name": "Bob", "email": "bob@example.com", "active": True},
        {"name": "Charlie", "email": "charlie@example.com", "active": False},
    ]


@pytest.fixture
def sample_products():
    """Sample product data for testing."""
    return [
        {"name": "Laptop", "price": 999.99, "category": "electronics"},
        {"name": "Mouse", "price": 29.99, "category": "electronics"},
        {"name": "Coffee", "price": 12.99, "category": "food"},
    ]


# Database configuration for integration tests (if needed)
TEST_DATABASE_CONFIG = {
    "postgresql": {
        "database_url": os.getenv(
            "TEST_POSTGRES_URL",
            "postgresql://test_user:test_password@localhost:5434/kailash_test",
        ),
    },
    "mysql": {
        "database_url": os.getenv(
            "TEST_MYSQL_URL",
            "mysql+pymysql://test_user:test_password@localhost:3307/kailash_test",
        ),
    },
    "sqlite": {
        "database_url": "sqlite:///:memory:",
    },
}


@pytest.fixture
def test_database_url(request):
    """Get database URL based on test parameter."""
    db_type = getattr(request, "param", "sqlite")
    return TEST_DATABASE_CONFIG[db_type]["database_url"]


@pytest.fixture
def dataflow_config():
    """Create a DataFlowConfig for integration tests."""
    from dataflow.core.config import DatabaseConfig, DataFlowConfig, Environment

    # Use test database configuration
    database_config = DatabaseConfig(
        url="postgresql://test_user:test_password@localhost:5434/kailash_test",
        pool_size=10,
        max_overflow=20,
        pool_recycle=3600,
        echo=False,
    )

    config = DataFlowConfig(environment=Environment.TESTING, database=database_config)

    return config
