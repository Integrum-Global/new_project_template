"""
Integration tests for API endpoints

Tests the REST API endpoints with real HTTP requests.
"""

import pytest
import json
from datetime import datetime
from unittest.mock import AsyncMock, patch
import uuid

from fastapi import status
from httpx import AsyncClient

from apps.user_management.main import main
from apps.user_management.api import setup_routes


class TestUserEndpoints:
    """Test user management API endpoints."""
    
    @pytest.mark.asyncio
    async def test_create_user_success(self, test_client, sample_user_data, auth_token):
        """Test successful user creation."""
        headers = {"Authorization": f"Bearer {auth_token}"}
        
        # Mock the workflow execution
        with patch('apps.user_management.core.startup.agent_ui') as mock_agent_ui:
            mock_agent_ui.create_session = AsyncMock(return_value="test_session")
            mock_agent_ui.execute_workflow_template = AsyncMock(return_value="test_execution")
            mock_agent_ui.wait_for_execution = AsyncMock(return_value={
                "outputs": {
                    "create_user": {
                        "user": {
                            "id": str(uuid.uuid4()),
                            "email": sample_user_data["email"],
                            "first_name": sample_user_data["first_name"],
                            "last_name": sample_user_data["last_name"],
                            "sso_enabled": True,
                            "mfa_enabled": True,
                            "created_at": datetime.now().isoformat()
                        }
                    }
                }
            })
            
            response = await test_client.post(
                "/api/users/",
                json=sample_user_data,
                headers=headers
            )
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["email"] == sample_user_data["email"]
        assert data["first_name"] == sample_user_data["first_name"]
        assert data["sso_enabled"] is True
    
    @pytest.mark.asyncio
    async def test_create_user_invalid_data(self, test_client, auth_token):
        """Test user creation with invalid data."""
        headers = {"Authorization": f"Bearer {auth_token}"}
        
        # Missing required fields
        invalid_data = {
            "email": "invalid-email",  # Invalid email format
            "first_name": "",  # Empty name
        }
        
        response = await test_client.post(
            "/api/users/",
            json=invalid_data,
            headers=headers
        )
        
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    
    @pytest.mark.asyncio
    async def test_list_users(self, test_client, auth_token):
        """Test listing users with pagination."""
        headers = {"Authorization": f"Bearer {auth_token}"}
        
        # Mock the workflow execution
        with patch('apps.user_management.core.startup.agent_ui') as mock_agent_ui:
            mock_agent_ui.create_session = AsyncMock(return_value="test_session")
            mock_agent_ui.create_dynamic_workflow = AsyncMock(return_value="test_workflow")
            mock_agent_ui.execute_workflow = AsyncMock(return_value="test_execution")
            mock_agent_ui.wait_for_execution = AsyncMock(return_value={
                "outputs": {
                    "filter_processor": {
                        "result": {
                            "users": [
                                {
                                    "id": str(uuid.uuid4()),
                                    "email": "user1@example.com",
                                    "first_name": "User",
                                    "last_name": "One",
                                    "is_active": True
                                },
                                {
                                    "id": str(uuid.uuid4()),
                                    "email": "user2@example.com", 
                                    "first_name": "User",
                                    "last_name": "Two",
                                    "is_active": True
                                }
                            ],
                            "total": 2,
                            "page": 1,
                            "limit": 50,
                            "has_next": False
                        }
                    }
                }
            })
            
            response = await test_client.get(
                "/api/users/?page=1&limit=50",
                headers=headers
            )
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "users" in data
        assert "total" in data
        assert len(data["users"]) == 2
    
    @pytest.mark.asyncio
    async def test_get_user(self, test_client, auth_token):
        """Test getting specific user."""
        user_id = str(uuid.uuid4())
        headers = {"Authorization": f"Bearer {auth_token}"}
        
        with patch('apps.user_management.core.startup.agent_ui') as mock_agent_ui:
            mock_agent_ui.create_session = AsyncMock(return_value="test_session")
            mock_agent_ui.create_dynamic_workflow = AsyncMock(return_value="test_workflow")
            mock_agent_ui.execute_workflow = AsyncMock(return_value="test_execution")
            mock_agent_ui.wait_for_execution = AsyncMock(return_value={
                "outputs": {
                    "user_manager": {
                        "user": {
                            "id": user_id,
                            "email": "test@example.com",
                            "first_name": "Test",
                            "last_name": "User",
                            "is_active": True
                        }
                    }
                }
            })
            
            response = await test_client.get(
                f"/api/users/{user_id}",
                headers=headers
            )
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["id"] == user_id
        assert data["email"] == "test@example.com"
    
    @pytest.mark.asyncio
    async def test_get_user_not_found(self, test_client, auth_token):
        """Test getting non-existent user."""
        user_id = str(uuid.uuid4())
        headers = {"Authorization": f"Bearer {auth_token}"}
        
        with patch('apps.user_management.core.startup.agent_ui') as mock_agent_ui:
            mock_agent_ui.create_session = AsyncMock(return_value="test_session")
            mock_agent_ui.create_dynamic_workflow = AsyncMock(return_value="test_workflow")
            mock_agent_ui.execute_workflow = AsyncMock(return_value="test_execution")
            mock_agent_ui.wait_for_execution = AsyncMock(return_value={
                "outputs": {
                    "user_manager": {
                        "user": None
                    }
                }
            })
            
            response = await test_client.get(
                f"/api/users/{user_id}",
                headers=headers
            )
        
        assert response.status_code == status.HTTP_404_NOT_FOUND
    
    @pytest.mark.asyncio
    async def test_update_user(self, test_client, auth_token):
        """Test updating user."""
        user_id = str(uuid.uuid4())
        headers = {"Authorization": f"Bearer {auth_token}"}
        
        update_data = {
            "first_name": "Updated",
            "department": "New Department"
        }
        
        with patch('apps.user_management.core.startup.agent_ui') as mock_agent_ui:
            mock_agent_ui.create_session = AsyncMock(return_value="test_session")
            mock_agent_ui.execute_workflow_template = AsyncMock(return_value="test_execution")
            mock_agent_ui.wait_for_execution = AsyncMock(return_value={
                "outputs": {
                    "update_user": {
                        "user": {
                            "id": user_id,
                            "first_name": "Updated",
                            "department": "New Department",
                            "updated_at": datetime.now().isoformat()
                        }
                    }
                }
            })
            
            response = await test_client.put(
                f"/api/users/{user_id}",
                json=update_data,
                headers=headers
            )
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["first_name"] == "Updated"
        assert data["department"] == "New Department"
    
    @pytest.mark.asyncio
    async def test_delete_user(self, test_client, auth_token):
        """Test deleting user."""
        user_id = str(uuid.uuid4())
        headers = {"Authorization": f"Bearer {auth_token}"}
        
        with patch('apps.user_management.core.startup.agent_ui') as mock_agent_ui:
            mock_agent_ui.create_session = AsyncMock(return_value="test_session")
            mock_agent_ui.execute_workflow_template = AsyncMock(return_value="test_execution")
            mock_agent_ui.wait_for_execution = AsyncMock(return_value={
                "outputs": {
                    "delete_user": {
                        "deletion_result": {
                            "success": True,
                            "archive_id": str(uuid.uuid4())
                        }
                    }
                }
            })
            
            response = await test_client.delete(
                f"/api/users/{user_id}?reason=Test deletion",
                headers=headers
            )
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["message"] == "User deleted successfully"
        assert "archive_id" in data


class TestAuthEndpoints:
    """Test authentication API endpoints."""
    
    @pytest.mark.asyncio
    async def test_login_success(self, test_client):
        """Test successful login."""
        login_data = {
            "username": "test@example.com",
            "password": "test_password",
            "device_id": "test_device",
            "ip_address": "192.168.1.1"
        }
        
        with patch('apps.user_management.core.startup.agent_ui') as mock_agent_ui:
            mock_agent_ui.create_session = AsyncMock(return_value="test_session")
            mock_agent_ui.execute_workflow_template = AsyncMock(return_value="test_execution")
            mock_agent_ui.wait_for_execution = AsyncMock(return_value={
                "outputs": {
                    "authenticate": {
                        "auth_result": {
                            "authenticated": True,
                            "user_id": str(uuid.uuid4()),
                            "risk_score": 0.1
                        }
                    },
                    "create_session": {
                        "session": {
                            "session_id": str(uuid.uuid4()),
                            "access_token": "test_access_token",
                            "refresh_token": "test_refresh_token"
                        }
                    }
                }
            })
            
            response = await test_client.post(
                "/api/auth/login",
                json=login_data
            )
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["access_token"] == "test_access_token"
        assert data["token_type"] == "bearer"
    
    @pytest.mark.asyncio
    async def test_login_failure(self, test_client):
        """Test failed login."""
        login_data = {
            "username": "test@example.com",
            "password": "wrong_password"
        }
        
        with patch('apps.user_management.core.startup.agent_ui') as mock_agent_ui:
            mock_agent_ui.create_session = AsyncMock(return_value="test_session")
            mock_agent_ui.execute_workflow_template = AsyncMock(return_value="test_execution")
            mock_agent_ui.wait_for_execution = AsyncMock(return_value={
                "outputs": {
                    "authenticate": {
                        "auth_result": {
                            "authenticated": False,
                            "error": "Invalid credentials"
                        }
                    }
                }
            })
            
            response = await test_client.post(
                "/api/auth/login",
                json=login_data
            )
        
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
    
    @pytest.mark.asyncio
    async def test_login_mfa_required(self, test_client):
        """Test login requiring MFA."""
        login_data = {
            "username": "test@example.com",
            "password": "test_password"
        }
        
        with patch('apps.user_management.core.startup.agent_ui') as mock_agent_ui:
            mock_agent_ui.create_session = AsyncMock(return_value="test_session")
            mock_agent_ui.execute_workflow_template = AsyncMock(return_value="test_execution")
            mock_agent_ui.wait_for_execution = AsyncMock(return_value={
                "outputs": {
                    "authenticate": {
                        "auth_result": {
                            "authenticated": False,
                            "mfa_required": True,
                            "mfa_methods": ["totp", "sms"]
                        }
                    }
                }
            })
            
            response = await test_client.post(
                "/api/auth/login",
                json=login_data
            )
        
        assert response.status_code == status.HTTP_428_PRECONDITION_REQUIRED
        data = response.json()
        assert "mfa_methods" in data["detail"]
    
    @pytest.mark.asyncio
    async def test_logout(self, test_client, auth_token):
        """Test logout."""
        headers = {"Authorization": f"Bearer {auth_token}"}
        
        with patch('apps.user_management.core.startup.agent_ui') as mock_agent_ui:
            mock_agent_ui.create_session = AsyncMock(return_value="test_session")
            mock_agent_ui.create_dynamic_workflow = AsyncMock(return_value="test_workflow")
            mock_agent_ui.execute_workflow = AsyncMock(return_value="test_execution")
            mock_agent_ui.wait_for_execution = AsyncMock(return_value={
                "outputs": {
                    "invalidate_session": {
                        "result": {"success": True}
                    }
                }
            })
            
            response = await test_client.post(
                "/api/auth/logout",
                headers=headers
            )
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["message"] == "Logged out successfully"


class TestRoleEndpoints:
    """Test role management API endpoints."""
    
    @pytest.mark.asyncio
    async def test_list_roles(self, test_client, auth_token):
        """Test listing roles."""
        headers = {"Authorization": f"Bearer {auth_token}"}
        
        with patch('apps.user_management.core.startup.agent_ui') as mock_agent_ui:
            mock_agent_ui.create_session = AsyncMock(return_value="test_session")
            mock_agent_ui.create_dynamic_workflow = AsyncMock(return_value="test_workflow")
            mock_agent_ui.execute_workflow = AsyncMock(return_value="test_execution")
            mock_agent_ui.wait_for_execution = AsyncMock(return_value={
                "outputs": {
                    "process_roles": {
                        "result": {
                            "roles": [
                                {
                                    "id": str(uuid.uuid4()),
                                    "name": "admin",
                                    "description": "Administrator role",
                                    "user_count": 5,
                                    "is_system_role": True
                                },
                                {
                                    "id": str(uuid.uuid4()),
                                    "name": "user",
                                    "description": "Regular user role", 
                                    "user_count": 50,
                                    "is_system_role": False
                                }
                            ],
                            "total": 2,
                            "hierarchy": {}
                        }
                    }
                }
            })
            
            response = await test_client.get(
                "/api/roles/",
                headers=headers
            )
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert len(data["roles"]) == 2
        assert data["total"] == 2
    
    @pytest.mark.asyncio
    async def test_create_role(self, test_client, auth_token, sample_role_data):
        """Test creating role."""
        headers = {"Authorization": f"Bearer {auth_token}"}
        
        with patch('apps.user_management.core.startup.agent_ui') as mock_agent_ui:
            mock_agent_ui.create_session = AsyncMock(return_value="test_session")
            mock_agent_ui.create_dynamic_workflow = AsyncMock(return_value="test_workflow")
            mock_agent_ui.execute_workflow = AsyncMock(return_value="test_execution")
            mock_agent_ui.wait_for_execution = AsyncMock(return_value={
                "outputs": {
                    "validate_role": {
                        "result": {
                            "valid": True,
                            "errors": []
                        }
                    },
                    "create_role": {
                        "role": {
                            "id": str(uuid.uuid4()),
                            "name": sample_role_data["name"],
                            "description": sample_role_data["description"],
                            "permissions": sample_role_data["permissions"],
                            "is_system_role": False
                        }
                    }
                }
            })
            
            response = await test_client.post(
                "/api/roles/",
                json=sample_role_data,
                headers=headers
            )
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["name"] == sample_role_data["name"]
        assert data["permissions"] == sample_role_data["permissions"]
    
    @pytest.mark.asyncio
    async def test_assign_role(self, test_client, auth_token):
        """Test role assignment."""
        headers = {"Authorization": f"Bearer {auth_token}"}
        
        assignment_data = {
            "user_id": str(uuid.uuid4()),
            "role_name": "test_role",
            "reason": "Test assignment"
        }
        
        with patch('apps.user_management.core.startup.agent_ui') as mock_agent_ui:
            mock_agent_ui.create_session = AsyncMock(return_value="test_session")
            mock_agent_ui.execute_workflow_template = AsyncMock(return_value="test_execution")
            mock_agent_ui.wait_for_execution = AsyncMock(return_value={
                "outputs": {
                    "manage_role": {
                        "result": {
                            "success": True,
                            "assignment_id": str(uuid.uuid4())
                        }
                    }
                }
            })
            
            response = await test_client.post(
                "/api/roles/assign",
                json=assignment_data,
                headers=headers
            )
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["message"] == "Role assigned successfully"


class TestPermissionEndpoints:
    """Test permission management API endpoints."""
    
    @pytest.mark.asyncio
    async def test_check_permission(self, test_client, auth_token):
        """Test permission checking."""
        headers = {"Authorization": f"Bearer {auth_token}"}
        
        permission_data = {
            "user_id": str(uuid.uuid4()),
            "resource": "users:123",
            "action": "read",
            "context": {"department": "Engineering"}
        }
        
        with patch('apps.user_management.core.startup.agent_ui') as mock_agent_ui:
            mock_agent_ui.create_session = AsyncMock(return_value="test_session")
            mock_agent_ui.execute_workflow_template = AsyncMock(return_value="test_execution")
            mock_agent_ui.wait_for_execution = AsyncMock(return_value={
                "outputs": {
                    "format_response": {
                        "result": {
                            "allowed": True,
                            "reason": "User has read permission",
                            "applicable_policies": ["user_read_policy"],
                            "evaluation_time_ms": 12.5
                        }
                    }
                }
            })
            
            response = await test_client.post(
                "/api/permissions/check",
                json=permission_data,
                headers=headers
            )
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["allowed"] is True
        assert data["evaluation_time_ms"] == 12.5
    
    @pytest.mark.asyncio
    async def test_check_permission_denied(self, test_client, auth_token):
        """Test permission denied."""
        headers = {"Authorization": f"Bearer {auth_token}"}
        
        permission_data = {
            "user_id": str(uuid.uuid4()),
            "resource": "admin:settings",
            "action": "write"
        }
        
        with patch('apps.user_management.core.startup.agent_ui') as mock_agent_ui:
            mock_agent_ui.create_session = AsyncMock(return_value="test_session")
            mock_agent_ui.execute_workflow_template = AsyncMock(return_value="test_execution")
            mock_agent_ui.wait_for_execution = AsyncMock(return_value={
                "outputs": {
                    "format_response": {
                        "result": {
                            "allowed": False,
                            "reason": "User lacks admin privileges",
                            "applicable_policies": [],
                            "evaluation_time_ms": 8.2
                        }
                    }
                }
            })
            
            response = await test_client.post(
                "/api/permissions/check",
                json=permission_data,
                headers=headers
            )
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["allowed"] is False
        assert "admin privileges" in data["reason"]


class TestAdminEndpoints:
    """Test admin dashboard API endpoints."""
    
    @pytest.mark.asyncio
    async def test_get_dashboard(self, test_client, auth_token):
        """Test getting admin dashboard."""
        headers = {"Authorization": f"Bearer {auth_token}"}
        
        with patch('apps.user_management.core.startup.agent_ui') as mock_agent_ui:
            mock_agent_ui.create_session = AsyncMock(return_value="test_session")
            mock_agent_ui.execute_workflow_template = AsyncMock(return_value="test_execution")
            mock_agent_ui.wait_for_execution = AsyncMock(return_value={
                "outputs": {
                    "aggregate_stats": {
                        "result": {
                            "user_metrics": {
                                "total_users": 100,
                                "active_users": 85,
                                "new_users_today": 5
                            },
                            "auth_metrics": {
                                "active_sessions": 45,
                                "logins_today": 120
                            },
                            "security_metrics": {
                                "security_events_today": 3,
                                "high_risk_events": 0
                            },
                            "performance_metrics": {
                                "avg_response_time_ms": 45,
                                "requests_per_second": 1250
                            },
                            "active_features": {
                                "sso_enabled": True,
                                "mfa_enabled": True,
                                "ai_reasoning": True
                            }
                        }
                    }
                }
            })
            
            response = await test_client.get(
                "/api/admin/dashboard",
                headers=headers
            )
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "user_metrics" in data
        assert "auth_metrics" in data
        assert "security_metrics" in data
        assert "performance_metrics" in data
        assert data["user_metrics"]["total_users"] == 100
    
    @pytest.mark.asyncio
    async def test_system_health(self, test_client):
        """Test system health endpoint (no auth required)."""
        response = await test_client.get("/api/admin/health")
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["status"] == "healthy"
        assert "services" in data
        assert "timestamp" in data


class TestAPIPerformance:
    """Test API performance characteristics."""
    
    @pytest.mark.asyncio
    async def test_api_response_time(self, test_client, auth_token, performance_timer):
        """Test API response times."""
        headers = {"Authorization": f"Bearer {auth_token}"}
        
        with patch('apps.user_management.core.startup.agent_ui') as mock_agent_ui:
            mock_agent_ui.create_session = AsyncMock(return_value="test_session")
            mock_agent_ui.create_dynamic_workflow = AsyncMock(return_value="test_workflow")
            mock_agent_ui.execute_workflow = AsyncMock(return_value="test_execution")
            mock_agent_ui.wait_for_execution = AsyncMock(return_value={
                "outputs": {
                    "filter_processor": {
                        "result": {
                            "users": [],
                            "total": 0,
                            "page": 1,
                            "limit": 50,
                            "has_next": False
                        }
                    }
                }
            })
            
            performance_timer.start()
            response = await test_client.get("/api/users/", headers=headers)
            elapsed = performance_timer.stop()
        
        assert response.status_code == status.HTTP_200_OK
        # API should respond quickly (mocked, so very fast)
        assert elapsed < 1000  # Less than 1 second
    
    @pytest.mark.asyncio
    async def test_concurrent_api_requests(self, test_client, auth_token):
        """Test concurrent API requests."""
        headers = {"Authorization": f"Bearer {auth_token}"}
        
        with patch('apps.user_management.core.startup.agent_ui') as mock_agent_ui:
            mock_agent_ui.create_session = AsyncMock(return_value="test_session")
            mock_agent_ui.create_dynamic_workflow = AsyncMock(return_value="test_workflow")
            mock_agent_ui.execute_workflow = AsyncMock(return_value="test_execution")
            mock_agent_ui.wait_for_execution = AsyncMock(return_value={
                "outputs": {
                    "filter_processor": {
                        "result": {
                            "users": [],
                            "total": 0,
                            "page": 1,
                            "limit": 50,
                            "has_next": False
                        }
                    }
                }
            })
            
            # Make multiple concurrent requests
            import asyncio
            tasks = [
                test_client.get("/api/users/", headers=headers)
                for _ in range(5)
            ]
            
            responses = await asyncio.gather(*tasks)
        
        # All requests should succeed
        for response in responses:
            assert response.status_code == status.HTTP_200_OK