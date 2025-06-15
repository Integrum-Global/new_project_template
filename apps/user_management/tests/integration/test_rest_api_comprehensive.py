"""
Comprehensive REST API Integration Tests for User Management

This module tests all REST API endpoints using pure Kailash SDK patterns.
Tests verify both functionality and SDK integration.
"""

import asyncio
import json
from datetime import datetime, timedelta
from typing import Any, Dict, List

import pytest
import websockets
from fastapi.testclient import TestClient
from httpx import AsyncClient

from apps.user_management.core.startup import agent_ui, runtime
from apps.user_management.main import app
from kailash.runtime.local import LocalRuntime
from kailash.workflow import WorkflowBuilder


# Test fixtures
@pytest.fixture
async def async_client():
    """Create async HTTP client for testing."""
    async with AsyncClient(app=app, base_url="http://test") as client:
        yield client


@pytest.fixture
def test_client():
    """Create test client for synchronous tests."""
    return TestClient(app)


@pytest.fixture
async def test_user():
    """Create a test user for authentication."""
    # Use workflow to create test user
    builder = WorkflowBuilder("create_test_user")
    builder.add_node(
        "UserManagementNode",
        "create_user",
        {
            "operation": "create",
            "email": "test@example.com",
            "password": "Test123!@#",
            "first_name": "Test",
            "last_name": "User",
            "department": "Engineering",
        },
    )

    workflow = builder.build()
    runtime = LocalRuntime(enable_async=True)
    results, _ = await runtime.execute(workflow)

    return results.get("create_user", {}).get("user", {})


@pytest.fixture
async def auth_headers(test_user):
    """Get authentication headers for test user."""
    # Create auth workflow
    builder = WorkflowBuilder("authenticate_test_user")
    builder.add_node(
        "PythonCodeNode",
        "generate_token",
        {
            "name": "generate_test_token",
            "code": """
# Generate test JWT token
import jwt
from datetime import datetime, timedelta

token_data = {
    "sub": test_user.get("id", "test_user_123"),
    "email": test_user.get("email", "test@example.com"),
    "exp": datetime.utcnow() + timedelta(hours=1)
}

token = jwt.encode(token_data, "test_secret", algorithm="HS256")
result = {"result": {"token": token}}
""",
        },
    )

    workflow = builder.build()
    runtime = LocalRuntime(enable_async=True)
    results, _ = await runtime.execute(workflow, parameters={"test_user": test_user})

    token = (
        results.get("generate_token", {}).get("result", {}).get("token", "test_token")
    )
    return {"Authorization": f"Bearer {token}"}


class TestUserEndpoints:
    """Test user management endpoints."""

    @pytest.mark.asyncio
    async def test_create_user(self, async_client: AsyncClient):
        """Test user creation endpoint."""
        user_data = {
            "email": "newuser@example.com",
            "password": "SecurePass123!",
            "first_name": "New",
            "last_name": "User",
            "department": "Sales",
            "attributes": {"team": "Alpha", "location": "NYC"},
        }

        response = await async_client.post("/api/users", json=user_data)
        assert response.status_code == 201

        data = response.json()
        assert data["email"] == user_data["email"]
        assert data["first_name"] == user_data["first_name"]
        assert "id" in data
        assert "created_at" in data
        assert "password" not in data  # Password should not be returned

    @pytest.mark.asyncio
    async def test_get_user(self, async_client: AsyncClient, test_user, auth_headers):
        """Test get user endpoint."""
        user_id = test_user.get("id", "test_user_123")

        response = await async_client.get(f"/api/users/{user_id}", headers=auth_headers)
        assert response.status_code == 200

        data = response.json()
        assert data["email"] == test_user["email"]
        assert data["first_name"] == test_user["first_name"]

    @pytest.mark.asyncio
    async def test_update_user(
        self, async_client: AsyncClient, test_user, auth_headers
    ):
        """Test update user endpoint."""
        user_id = test_user.get("id", "test_user_123")
        update_data = {
            "first_name": "Updated",
            "department": "Marketing",
            "attributes": {"team": "Beta"},
        }

        response = await async_client.patch(
            f"/api/users/{user_id}", json=update_data, headers=auth_headers
        )
        assert response.status_code == 200

        data = response.json()
        assert data["first_name"] == update_data["first_name"]
        assert data["department"] == update_data["department"]

    @pytest.mark.asyncio
    async def test_list_users_with_filters(
        self, async_client: AsyncClient, auth_headers
    ):
        """Test list users with filtering and pagination."""
        # Test with filters
        response = await async_client.get(
            "/api/users?department=Engineering&active=true&limit=10",
            headers=auth_headers,
        )
        assert response.status_code == 200

        data = response.json()
        assert "users" in data
        assert "total" in data
        assert "page" in data
        assert len(data["users"]) <= 10

    @pytest.mark.asyncio
    async def test_bulk_operations(self, async_client: AsyncClient, auth_headers):
        """Test bulk user operations."""
        # Bulk create
        bulk_data = {
            "users": [
                {
                    "email": f"bulk{i}@example.com",
                    "password": "BulkPass123!",
                    "first_name": f"Bulk{i}",
                    "last_name": "User",
                    "department": "Engineering",
                }
                for i in range(3)
            ]
        }

        response = await async_client.post(
            "/api/users/bulk/create", json=bulk_data, headers=auth_headers
        )
        assert response.status_code == 200

        data = response.json()
        assert data["created"] == 3
        assert len(data["users"]) == 3


class TestPermissionEndpoints:
    """Test permission management endpoints."""

    @pytest.mark.asyncio
    async def test_create_permission(self, async_client: AsyncClient, auth_headers):
        """Test permission creation."""
        permission_data = {
            "name": "reports:generate",
            "description": "Generate reports",
            "resource": "reports",
            "action": "generate",
            "conditions": {"department": ["Sales", "Marketing"]},
        }

        response = await async_client.post(
            "/api/permissions", json=permission_data, headers=auth_headers
        )
        assert response.status_code == 201

        data = response.json()
        assert data["name"] == permission_data["name"]
        assert data["resource"] == permission_data["resource"]

    @pytest.mark.asyncio
    async def test_check_permission(
        self, async_client: AsyncClient, test_user, auth_headers
    ):
        """Test permission checking."""
        check_data = {
            "user_id": test_user.get("id", "test_user_123"),
            "resource": "users",
            "action": "read",
            "context": {"department": "Engineering"},
        }

        response = await async_client.post(
            "/api/permissions/check", json=check_data, headers=auth_headers
        )
        assert response.status_code == 200

        data = response.json()
        assert "allowed" in data
        assert "reasons" in data


class TestRoleEndpoints:
    """Test role management endpoints."""

    @pytest.mark.asyncio
    async def test_create_role(self, async_client: AsyncClient, auth_headers):
        """Test role creation."""
        role_data = {
            "name": "Report Manager",
            "description": "Manages reports",
            "permissions": ["reports:view", "reports:generate", "reports:export"],
        }

        response = await async_client.post(
            "/api/roles", json=role_data, headers=auth_headers
        )
        assert response.status_code == 201

        data = response.json()
        assert data["name"] == role_data["name"]
        assert len(data["permissions"]) == 3

    @pytest.mark.asyncio
    async def test_assign_role(
        self, async_client: AsyncClient, test_user, auth_headers
    ):
        """Test role assignment."""
        assign_data = {
            "user_id": test_user.get("id", "test_user_123"),
            "role_id": "role_manager_123",
        }

        response = await async_client.post(
            "/api/roles/assign", json=assign_data, headers=auth_headers
        )
        assert response.status_code == 200

        data = response.json()
        assert data["success"] is True
        assert "assignment_id" in data


class TestSSOEndpoints:
    """Test SSO integration endpoints."""

    @pytest.mark.asyncio
    async def test_sso_providers(self, async_client: AsyncClient):
        """Test list SSO providers."""
        response = await async_client.get("/api/sso/providers")
        assert response.status_code == 200

        data = response.json()
        assert "providers" in data
        assert any(p["name"] == "google" for p in data["providers"])
        assert any(p["name"] == "okta" for p in data["providers"])

    @pytest.mark.asyncio
    async def test_sso_login_flow(self, async_client: AsyncClient):
        """Test SSO login initiation."""
        response = await async_client.get(
            "/api/sso/login/google?redirect_uri=http://localhost:3000/callback"
        )
        assert response.status_code == 200

        data = response.json()
        assert "auth_url" in data
        assert "state" in data
        assert "google" in data["auth_url"]


class TestComplianceEndpoints:
    """Test GDPR compliance endpoints."""

    @pytest.mark.asyncio
    async def test_data_export(
        self, async_client: AsyncClient, test_user, auth_headers
    ):
        """Test GDPR data export."""
        export_data = {
            "user_id": test_user.get("id", "test_user_123"),
            "format": "json",
            "include_audit_logs": True,
            "include_permissions": True,
            "include_sessions": True,
        }

        response = await async_client.post(
            "/api/compliance/export-data", json=export_data, headers=auth_headers
        )
        assert response.status_code == 200

        # Check response headers
        assert "Content-Disposition" in response.headers
        assert "X-GDPR-Export" in response.headers
        assert response.headers["X-GDPR-Export"] == "true"

    @pytest.mark.asyncio
    async def test_consent_management(
        self, async_client: AsyncClient, test_user, auth_headers
    ):
        """Test consent management."""
        consent_data = {
            "user_id": test_user.get("id", "test_user_123"),
            "consent_type": "marketing",
            "granted": True,
            "ip_address": "192.168.1.100",
        }

        response = await async_client.post(
            "/api/compliance/consent", json=consent_data, headers=auth_headers
        )
        assert response.status_code == 200

        data = response.json()
        assert data["success"] is True
        assert "consent_id" in data
        assert data["granted"] == consent_data["granted"]

    @pytest.mark.asyncio
    async def test_retention_policy(self, async_client: AsyncClient, auth_headers):
        """Test retention policy configuration."""
        policy_data = {
            "data_type": "audit_logs",
            "retention_days": 2555,  # 7 years
            "auto_delete": True,
            "notify_before_days": 30,
        }

        response = await async_client.post(
            "/api/compliance/retention-policy", json=policy_data, headers=auth_headers
        )
        assert response.status_code == 200

        data = response.json()
        assert data["success"] is True
        assert data["retention_days"] == policy_data["retention_days"]


class TestAdminEndpoints:
    """Test admin dashboard endpoints."""

    @pytest.mark.asyncio
    async def test_system_health(self, async_client: AsyncClient, auth_headers):
        """Test system health endpoint."""
        response = await async_client.get("/api/admin/health", headers=auth_headers)
        assert response.status_code == 200

        data = response.json()
        assert "status" in data
        assert data["status"] in ["healthy", "degraded", "critical"]
        assert "uptime_hours" in data
        assert "cpu_usage_percent" in data
        assert "memory_usage_percent" in data

    @pytest.mark.asyncio
    async def test_user_statistics(self, async_client: AsyncClient, auth_headers):
        """Test user statistics endpoint."""
        response = await async_client.get(
            "/api/admin/statistics/users", headers=auth_headers
        )
        assert response.status_code == 200

        data = response.json()
        assert "total_users" in data
        assert "active_users" in data
        assert "new_users_today" in data
        assert "by_department" in data
        assert "by_role" in data

    @pytest.mark.asyncio
    async def test_security_metrics(self, async_client: AsyncClient, auth_headers):
        """Test security metrics endpoint."""
        response = await async_client.get(
            "/api/admin/statistics/security", headers=auth_headers
        )
        assert response.status_code == 200

        data = response.json()
        assert "failed_logins_today" in data
        assert "security_score" in data
        assert "recent_threats" in data
        assert isinstance(data["recent_threats"], list)

    @pytest.mark.asyncio
    async def test_performance_metrics(self, async_client: AsyncClient, auth_headers):
        """Test performance metrics endpoint."""
        response = await async_client.get(
            "/api/admin/statistics/performance", headers=auth_headers
        )
        assert response.status_code == 200

        data = response.json()
        assert "average_response_time_ms" in data
        assert "p95_response_time_ms" in data
        assert "requests_per_second" in data
        assert "error_rate" in data

    @pytest.mark.asyncio
    async def test_export_dashboard(self, async_client: AsyncClient, auth_headers):
        """Test dashboard export."""
        response = await async_client.get(
            "/api/admin/export/dashboard?format=json", headers=auth_headers
        )
        assert response.status_code == 200

        # Parse exported data
        content = response.content.decode()
        data = json.loads(content)
        assert "export_date" in data
        assert "system_health" in data
        assert "user_statistics" in data


class TestWebSocketEndpoints:
    """Test WebSocket real-time endpoints."""

    @pytest.mark.asyncio
    async def test_admin_websocket(self):
        """Test admin dashboard WebSocket."""
        uri = "ws://localhost:8000/ws/admin"

        async with websockets.connect(uri) as websocket:
            # Wait for connection message
            message = await websocket.recv()
            data = json.loads(message)

            assert data["type"] == "connection"
            assert data["status"] == "connected"
            assert "connection_id" in data
            assert "features" in data

            # Send ping
            await websocket.send(json.dumps({"type": "ping"}))

            # Receive pong
            response = await websocket.recv()
            data = json.loads(response)
            assert data["type"] == "pong"

            # Test query
            await websocket.send(
                json.dumps({"type": "query", "query_type": "active_users"})
            )

            # Receive query response
            response = await websocket.recv()
            data = json.loads(response)
            assert data["type"] == "query_response"
            assert data["query_type"] == "active_users"

    @pytest.mark.asyncio
    async def test_user_websocket(self, test_user):
        """Test user-specific WebSocket."""
        user_id = test_user.get("id", "test_user_123")
        uri = f"ws://localhost:8000/ws/user/{user_id}?token=test_token_12345"

        async with websockets.connect(uri) as websocket:
            # Wait for connection message
            message = await websocket.recv()
            data = json.loads(message)

            assert data["type"] == "connection"
            assert data["user_id"] == user_id

            # Test preferences update
            await websocket.send(
                json.dumps(
                    {
                        "type": "update_preferences",
                        "preferences": {"notifications": True, "theme": "dark"},
                    }
                )
            )

            # Wait for confirmation
            response = await websocket.recv()
            data = json.loads(response)
            assert data["type"] == "preferences_updated"
            assert data["success"] is True

    @pytest.mark.asyncio
    async def test_broadcast_api(self, async_client: AsyncClient, auth_headers):
        """Test broadcast API."""
        broadcast_data = {
            "message": {
                "type": "announcement",
                "content": "System maintenance scheduled",
                "priority": "high",
            },
            "connection_type": "admin_dashboard",
        }

        response = await async_client.post(
            "/api/broadcast", json=broadcast_data, headers=auth_headers
        )
        assert response.status_code == 200

        data = response.json()
        assert data["success"] is True
        assert "recipients" in data
        assert "execution_id" in data


class TestWorkflowIntegration:
    """Test workflow integration across endpoints."""

    @pytest.mark.asyncio
    async def test_complete_user_lifecycle(
        self, async_client: AsyncClient, auth_headers
    ):
        """Test complete user lifecycle through API."""
        # 1. Create user
        user_data = {
            "email": "lifecycle@example.com",
            "password": "LifeCycle123!",
            "first_name": "Life",
            "last_name": "Cycle",
            "department": "Engineering",
        }

        create_response = await async_client.post("/api/users", json=user_data)
        assert create_response.status_code == 201
        user = create_response.json()
        user_id = user["id"]

        # 2. Create role
        role_data = {
            "name": "Developer",
            "permissions": ["code:read", "code:write", "pr:create"],
        }

        role_response = await async_client.post(
            "/api/roles", json=role_data, headers=auth_headers
        )
        assert role_response.status_code == 201
        role = role_response.json()

        # 3. Assign role to user
        assign_response = await async_client.post(
            "/api/roles/assign",
            json={"user_id": user_id, "role_id": role["id"]},
            headers=auth_headers,
        )
        assert assign_response.status_code == 200

        # 4. Check permissions
        check_response = await async_client.post(
            "/api/permissions/check",
            json={"user_id": user_id, "resource": "code", "action": "write"},
            headers=auth_headers,
        )
        assert check_response.status_code == 200
        assert check_response.json()["allowed"] is True

        # 5. Export user data (GDPR)
        export_response = await async_client.post(
            "/api/compliance/export-data",
            json={"user_id": user_id, "format": "json", "include_audit_logs": True},
            headers=auth_headers,
        )
        assert export_response.status_code == 200

        # 6. Update user
        update_response = await async_client.patch(
            f"/api/users/{user_id}", json={"department": "DevOps"}, headers=auth_headers
        )
        assert update_response.status_code == 200

        # 7. Deactivate user
        deactivate_response = await async_client.post(
            f"/api/users/{user_id}/deactivate", headers=auth_headers
        )
        assert deactivate_response.status_code == 200

    @pytest.mark.asyncio
    async def test_concurrent_operations(self, async_client: AsyncClient, auth_headers):
        """Test concurrent API operations."""
        # Create multiple users concurrently
        tasks = []
        for i in range(10):
            user_data = {
                "email": f"concurrent{i}@example.com",
                "password": "Concurrent123!",
                "first_name": f"User{i}",
                "last_name": "Concurrent",
                "department": "Testing",
            }

            task = async_client.post("/api/users", json=user_data)
            tasks.append(task)

        # Execute all requests concurrently
        responses = await asyncio.gather(*tasks)

        # Verify all succeeded
        for response in responses:
            assert response.status_code == 201

        # Verify we can list all users
        list_response = await async_client.get(
            "/api/users?department=Testing", headers=auth_headers
        )
        assert list_response.status_code == 200
        assert list_response.json()["total"] >= 10


class TestErrorHandling:
    """Test error handling and edge cases."""

    @pytest.mark.asyncio
    async def test_invalid_user_creation(self, async_client: AsyncClient):
        """Test validation errors."""
        # Missing required fields
        response = await async_client.post("/api/users", json={"email": "invalid"})
        assert response.status_code == 422

        # Invalid email format
        response = await async_client.post(
            "/api/users",
            json={
                "email": "not-an-email",
                "password": "Pass123!",
                "first_name": "Test",
                "last_name": "User",
            },
        )
        assert response.status_code == 422

        # Weak password
        response = await async_client.post(
            "/api/users",
            json={
                "email": "test@example.com",
                "password": "weak",
                "first_name": "Test",
                "last_name": "User",
            },
        )
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_unauthorized_access(self, async_client: AsyncClient):
        """Test unauthorized access."""
        # No auth header
        response = await async_client.get("/api/users")
        assert response.status_code == 401

        # Invalid token
        response = await async_client.get(
            "/api/users", headers={"Authorization": "Bearer invalid_token"}
        )
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_permission_denied(
        self, async_client: AsyncClient, test_user, auth_headers
    ):
        """Test permission denied scenarios."""
        # Try to access admin endpoint without admin role
        response = await async_client.post(
            "/api/admin/maintenance/cleanup", headers=auth_headers
        )
        assert response.status_code == 403

        data = response.json()
        assert "detail" in data
        assert "permission" in data["detail"].lower()


# Performance tests
class TestPerformance:
    """Test performance characteristics."""

    @pytest.mark.asyncio
    async def test_response_times(self, async_client: AsyncClient, auth_headers):
        """Test API response times meet targets."""
        import time

        # Test simple GET
        start = time.time()
        response = await async_client.get("/api/users/me", headers=auth_headers)
        elapsed = (time.time() - start) * 1000  # Convert to ms

        assert response.status_code == 200
        assert elapsed < 100  # Target: <100ms

        # Test complex query
        start = time.time()
        response = await async_client.get(
            "/api/users?department=Engineering&active=true&limit=100",
            headers=auth_headers,
        )
        elapsed = (time.time() - start) * 1000

        assert response.status_code == 200
        assert elapsed < 200  # Target: <200ms for complex queries

    @pytest.mark.asyncio
    async def test_concurrent_load(self, async_client: AsyncClient, auth_headers):
        """Test system under concurrent load."""
        import time

        async def make_request():
            start = time.time()
            response = await async_client.get("/api/users/me", headers=auth_headers)
            elapsed = (time.time() - start) * 1000
            return response.status_code, elapsed

        # Make 50 concurrent requests
        tasks = [make_request() for _ in range(50)]
        results = await asyncio.gather(*tasks)

        # Verify all succeeded
        statuses = [r[0] for r in results]
        times = [r[1] for r in results]

        assert all(status == 200 for status in statuses)
        assert sum(times) / len(times) < 150  # Average response time <150ms
        assert max(times) < 500  # No request takes >500ms


if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v", "--asyncio-mode=auto"])
