"""
DataFlow Test Configuration

Provides fixtures and utilities for DataFlow testing.
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

from kailash_dataflow import DataFlow, DataFlowConfig, Environment

from kailash.runtime.local import LocalRuntime
from kailash.workflow.builder import WorkflowBuilder

# Import shared test utilities from main test suite
from tests.utils.docker_config import (
    DATABASE_CONFIG,
    check_postgres_ready,
    check_redis_ready,
    ensure_docker_services,
    get_mysql_connection_string,
    get_postgres_connection_string,
    get_redis_url,
)


@pytest.fixture(scope="session")
def event_loop():
    """Create an event loop for async tests."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session", autouse=True)
async def ensure_test_services():
    """Ensure Docker services are running for integration/e2e tests."""
    # Skip for unit tests
    if "unit" in str(Path.cwd()):
        return

    # Ensure services are up
    await ensure_docker_services()

    # Wait for services to be ready
    await check_postgres_ready()
    await check_redis_ready()


@pytest.fixture
def dataflow_config():
    """Provide test DataFlow configuration."""
    return DataFlowConfig(
        environment=Environment.TESTING,
        database=DataFlowConfig.database_class(
            url=get_postgres_connection_string("dataflow_test"),
        ),
        monitoring=DataFlowConfig.monitoring_class(
            enabled=True,
            slow_query_threshold=0.5,
        ),
        security=DataFlowConfig.security_class(
            multi_tenant=False,  # Disabled by default for tests
        ),
    )


@pytest.fixture
def dataflow_config_multitenant():
    """Provide multi-tenant test configuration."""
    config = DataFlowConfig(
        environment=Environment.TESTING,
        database=DataFlowConfig.database_class(
            url=get_postgres_connection_string("dataflow_mt_test"),
        ),
        security=DataFlowConfig.security_class(
            multi_tenant=True,
            tenant_isolation_strategy="schema",
        ),
    )
    return config


@pytest.fixture
async def dataflow(dataflow_config):
    """Provide initialized DataFlow instance."""
    db = DataFlow(dataflow_config)
    yield db
    # Cleanup
    if hasattr(db, "__aexit__"):
        await db.__aexit__(None, None, None)


@pytest.fixture
async def dataflow_multitenant(dataflow_config_multitenant):
    """Provide multi-tenant DataFlow instance."""
    db = DataFlow(dataflow_config_multitenant)
    yield db
    # Cleanup
    if hasattr(db, "__aexit__"):
        await db.__aexit__(None, None, None)


@pytest.fixture
def runtime():
    """Provide LocalRuntime for workflow execution."""
    return LocalRuntime()


@pytest.fixture
def workflow_builder():
    """Provide clean WorkflowBuilder instance."""
    return WorkflowBuilder()


@pytest.fixture
async def clean_database(dataflow):
    """Ensure database is clean before test."""
    # Drop all tables in test database
    workflow = WorkflowBuilder()
    workflow.add_node(
        "SQLDatabaseNode",
        "drop_tables",
        {
            "connection_string": dataflow.config.database.get_connection_url(
                dataflow.config.environment
            ),
            "query": """
            DO $$
            DECLARE
                r RECORD;
            BEGIN
                FOR r IN (SELECT tablename FROM pg_tables WHERE schemaname = 'public')
                LOOP
                    EXECUTE 'DROP TABLE IF EXISTS ' || quote_ident(r.tablename) || ' CASCADE';
                END LOOP;
            END $$;
        """,
        },
    )

    runtime = LocalRuntime()
    await runtime.execute_async(workflow.build())

    yield

    # Cleanup after test (optional)


@pytest.fixture
def sample_models():
    """Provide sample model definitions for testing."""

    def create_models(db: DataFlow):
        @db.model
        class User:
            email: str
            name: str
            active: bool = True

        @db.model
        class Post:
            title: str
            content: str
            author_id: int
            published: bool = False
            views: int = 0

        @db.model
        class Comment:
            post_id: int
            author_id: int
            content: str

        return User, Post, Comment

    return create_models


@pytest.fixture
def test_data():
    """Provide sample test data."""
    return {
        "users": [
            {"email": "alice@example.com", "name": "Alice Smith"},
            {"email": "bob@example.com", "name": "Bob Jones"},
            {"email": "charlie@example.com", "name": "Charlie Brown"},
        ],
        "posts": [
            {
                "title": "Introduction to DataFlow",
                "content": "DataFlow makes database operations simple...",
                "author_id": 1,
                "published": True,
                "views": 100,
            },
            {
                "title": "Advanced DataFlow Features",
                "content": "Let's explore advanced features...",
                "author_id": 1,
                "published": False,
                "views": 0,
            },
            {
                "title": "DataFlow Performance Tips",
                "content": "Optimize your DataFlow applications...",
                "author_id": 2,
                "published": True,
                "views": 50,
            },
        ],
        "comments": [
            {"post_id": 1, "author_id": 2, "content": "Great introduction!"},
            {"post_id": 1, "author_id": 3, "content": "Very helpful, thanks!"},
            {"post_id": 3, "author_id": 1, "content": "Good performance tips."},
        ],
    }


# Pytest markers
def pytest_configure(config):
    """Configure custom pytest markers."""
    config.addinivalue_line("markers", "requires_postgres: test requires PostgreSQL")
    config.addinivalue_line("markers", "requires_redis: test requires Redis")
    config.addinivalue_line("markers", "requires_docker: test requires Docker services")
    config.addinivalue_line("markers", "slow: slow running test")
    config.addinivalue_line("markers", "critical: critical functionality test")
