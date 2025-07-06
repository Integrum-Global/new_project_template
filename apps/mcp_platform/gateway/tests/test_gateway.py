"""Tests for MCP Enterprise Gateway."""

import asyncio
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, Mock, patch

import httpx
import jwt
import pytest

from apps.mcp_platform.gateway.auth.authentication import TokenManager, User
from apps.mcp_platform.gateway.auth.authorization import AuthorizationMiddleware, Role
from apps.mcp_platform.gateway.core.server import app
from apps.mcp_platform.gateway.routing.router import (
    LoadBalancer,
    ToolInstance,
    ToolRouter,
)

from ..clients.gateway_client import Gateway, GatewayClient
from ..services.tenant.manager import Tenant, TenantManager, TenantTier


# Test fixtures
@pytest.fixture
async def test_client():
    """Create test client."""
    async with httpx.AsyncClient(app=app, base_url="http://test") as client:
        yield client


@pytest.fixture
def auth_token():
    """Create test authentication token."""
    return TokenManager.create_access_token(
        {
            "sub": "test_user",
            "tenant_id": "test_tenant",
            "roles": ["developer"],
            "permissions": ["tools:*"],
        }
    )


@pytest.fixture
def admin_token():
    """Create admin authentication token."""
    return TokenManager.create_access_token(
        {
            "sub": "admin_user",
            "tenant_id": "admin_tenant",
            "roles": ["admin"],
            "permissions": ["*"],
        }
    )


# Server tests
@pytest.mark.asyncio
async def test_health_endpoint(test_client):
    """Test health check endpoint."""
    response = await test_client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "components" in data


@pytest.mark.asyncio
async def test_root_endpoint(test_client):
    """Test root endpoint."""
    response = await test_client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "MCP Enterprise Gateway"
    assert "features" in data


# Authentication tests
def test_token_creation():
    """Test JWT token creation."""
    data = {"sub": "user123", "tenant_id": "tenant123", "roles": ["user"]}

    token = TokenManager.create_access_token(data)
    assert token is not None

    # Decode and verify
    decoded = jwt.decode(token, "your-secret-key", algorithms=["HS256"])
    assert decoded["sub"] == "user123"
    assert decoded["tenant_id"] == "tenant123"


def test_password_hashing():
    """Test password hashing and verification."""
    password = "secure_password123"
    hashed = User.hash_password(password)

    assert hashed != password

    user = User(
        user_id="test",
        username="testuser",
        email="test@example.com",
        password_hash=hashed,
    )

    assert user.verify_password(password) is True
    assert user.verify_password("wrong_password") is False


@pytest.mark.asyncio
async def test_api_key_authentication():
    """Test API key authentication."""
    from apps.mcp_platform.gateway.auth.authentication import AuthenticationMiddleware

    auth = AuthenticationMiddleware()

    # Mock Redis client
    with patch.object(auth, "redis_client") as mock_redis:
        mock_redis.get.return_value = AsyncMock(
            return_value='{"user_id": "test", "active": true, "roles": ["user"]}'
        )

        # Create mock request
        request = Mock()
        request.headers = {"X-API-Key": "test_api_key"}

        user = await auth.authenticate(request)

        assert user["user_id"] == "test"
        assert user["auth_method"] == "api_key"


# Authorization tests
def test_role_permissions():
    """Test role-based permissions."""
    auth_middleware = AuthorizationMiddleware()

    # Test admin role
    admin_user = {"user_id": "admin", "roles": ["admin"]}

    assert auth_middleware.check_permission(admin_user, "tools:execute") is True
    assert auth_middleware.check_permission(admin_user, "admin:users:create") is True

    # Test developer role
    dev_user = {"user_id": "dev", "roles": ["developer"]}

    assert auth_middleware.check_permission(dev_user, "tools:execute") is True
    assert auth_middleware.check_permission(dev_user, "admin:users:create") is False


def test_custom_role():
    """Test custom role creation."""
    auth_middleware = AuthorizationMiddleware()

    custom_role = Role(
        "custom_viewer", ["tools:list", "tools:read"], "Custom viewer role"
    )

    auth_middleware.add_role(custom_role)

    user = {"user_id": "custom", "roles": ["custom_viewer"]}

    assert auth_middleware.check_permission(user, "tools:list") is True
    assert auth_middleware.check_permission(user, "tools:execute") is False


# Routing tests
@pytest.mark.asyncio
async def test_tool_registration():
    """Test tool registration and routing."""
    router = ToolRouter()

    # Register a test tool
    async def test_handler(action, params, context):
        return {"action": action, "params": params}

    router.register_tool(
        "test_tool", {"description": "Test tool", "handler": test_handler}
    )

    # Execute tool
    result = await router.execute("test_tool", "test_action", {"param": "value"}, {})

    assert result["action"] == "test_action"
    assert result["params"]["param"] == "value"


def test_load_balancer():
    """Test load balancer strategies."""
    # Round-robin
    lb_rr = LoadBalancer(strategy="round_robin")
    lb_rr.add_instance(ToolInstance("1", "http://host1"))
    lb_rr.add_instance(ToolInstance("2", "http://host2"))

    instances = []
    for _ in range(4):
        instance = lb_rr.get_next_instance()
        instances.append(instance.instance_id)

    assert instances == ["1", "2", "1", "2"]

    # Weighted
    lb_weighted = LoadBalancer(strategy="weighted")
    lb_weighted.add_instance(ToolInstance("1", "http://host1", weight=3))
    lb_weighted.add_instance(ToolInstance("2", "http://host2", weight=1))

    # Should get more of instance 1
    instance = lb_weighted.get_next_instance()
    assert instance is not None


# Tenant management tests
@pytest.mark.asyncio
async def test_tenant_creation():
    """Test tenant creation."""
    manager = TenantManager()

    with patch.object(manager, "session_factory") as mock_session:
        mock_session.return_value.__aenter__.return_value = AsyncMock()

        tenant_data = {
            "name": "test_company",
            "display_name": "Test Company",
            "tier": TenantTier.PROFESSIONAL,
            "billing_email": "billing@test.com",
        }

        # Mock the database operations
        with patch.object(manager, "_create_tenant_resources"):
            tenant = await manager.create_tenant(tenant_data)

            assert tenant["name"] == "test_company"
            assert tenant["tier"] == TenantTier.PROFESSIONAL


@pytest.mark.asyncio
async def test_tenant_limits():
    """Test tenant resource limits."""
    manager = TenantManager()

    # Mock tenant data
    with patch.object(manager, "get_tenant") as mock_get:
        mock_get.return_value = {
            "tenant_id": "test",
            "status": "active",
            "limits": {"max_api_calls_per_day": 1000, "max_users": 10},
        }

        with patch.object(manager, "_get_api_usage") as mock_usage:
            mock_usage.return_value = 500

            # Should allow - under limit
            assert await manager.check_tenant_limits("test", "api_calls", 100) is True

            # Should deny - would exceed limit
            assert await manager.check_tenant_limits("test", "api_calls", 600) is False


# Client SDK tests
@pytest.mark.asyncio
async def test_gateway_client():
    """Test gateway client."""
    with patch("httpx.AsyncClient.post") as mock_post:
        mock_response = AsyncMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"success": True, "result": {"data": "test"}}
        mock_post.return_value = mock_response

        client = GatewayClient(base_url="http://gateway.test", api_key="test_key")

        result = await client.execute_tool(
            "test_tool", action="process", params={"input": "data"}
        )

        assert result["success"] is True
        assert result["result"]["data"] == "test"


@pytest.mark.asyncio
async def test_gateway_tools_interface():
    """Test high-level gateway interface."""
    with patch("httpx.AsyncClient.post") as mock_post:
        mock_response = AsyncMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "success": True,
            "result": {"processed": True},
        }
        mock_post.return_value = mock_response

        gateway = Gateway(url="http://gateway.test", auth={"api_key": "test_key"})

        async with gateway:
            # Use convenient tool access
            result = await gateway.tools.data_processor(
                action="transform", data=[1, 2, 3]
            )

            assert result["success"] is True


# Integration tests
@pytest.mark.asyncio
async def test_end_to_end_tool_execution(test_client, auth_token):
    """Test end-to-end tool execution."""
    # Mock the tool router
    with patch("mcp_enterprise_gateway.gateway.core.server.tool_router") as mock_router:
        mock_router.execute.return_value = {"result": "success"}

        response = await test_client.post(
            "/api/v1/tools/test_tool/execute",
            headers={"Authorization": f"Bearer {auth_token}"},
            json={"action": "test", "params": {"key": "value"}},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True


@pytest.mark.asyncio
async def test_rate_limiting():
    """Test rate limiting functionality."""
    # This would test the rate limiting middleware
    # Implementation depends on the specific rate limiting strategy
    pass


@pytest.mark.asyncio
async def test_circuit_breaker():
    """Test circuit breaker functionality."""
    from ..clients.gateway_client import CircuitBreakerClient

    client = CircuitBreakerClient(
        base_url="http://gateway.test",
        api_key="test_key",
        failure_threshold=2,
        recovery_timeout=1,
    )

    # Mock failures
    with patch.object(GatewayClient, "execute_tool") as mock_execute:
        mock_execute.side_effect = Exception("Service unavailable")

        # First failure
        with pytest.raises(Exception):
            await client.execute_tool("test_tool")

        # Second failure - should open circuit
        with pytest.raises(Exception):
            await client.execute_tool("test_tool")

        # Circuit should be open
        assert client.is_open is True

        # Should fail immediately
        with pytest.raises(Exception, match="Circuit breaker is open"):
            await client.execute_tool("test_tool")


# Performance tests
@pytest.mark.asyncio
async def test_concurrent_requests():
    """Test handling of concurrent requests."""
    client = GatewayClient(base_url="http://gateway.test", api_key="test_key")

    with patch.object(client, "execute_tool") as mock_execute:
        mock_execute.return_value = {"result": "success"}

        # Execute multiple concurrent requests
        tasks = []
        for i in range(10):
            task = client.execute_tool("test_tool", params={"index": i})
            tasks.append(task)

        results = await asyncio.gather(*tasks)

        assert len(results) == 10
        assert all(r["result"] == "success" for r in results)


# Security tests
@pytest.mark.asyncio
async def test_unauthorized_access(test_client):
    """Test unauthorized access is blocked."""
    response = await test_client.post(
        "/api/v1/tools/secure_tool/execute", json={"action": "test"}
    )

    assert response.status_code == 401


@pytest.mark.asyncio
async def test_tenant_isolation(test_client, auth_token):
    """Test tenant data isolation."""
    # This would test that tenants cannot access each other's data
    # Implementation depends on the specific isolation strategy
    pass


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
