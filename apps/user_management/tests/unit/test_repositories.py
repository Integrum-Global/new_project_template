"""
Unit tests for repository layer

Tests the repository pattern implementation using AsyncSQLDatabaseNode.
"""

import pytest
import asyncio
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, Mock, patch
import uuid

from apps.user_management.core.repositories import (
    UserRepository,
    RoleRepository,
    SessionRepository,
    AuditRepository,
    PermissionRepository
)


class TestUserRepository:
    """Test UserRepository operations."""
    
    @pytest.fixture
    def user_repo(self):
        """Create UserRepository instance for testing."""
        return UserRepository()
    
    @pytest.mark.asyncio
    async def test_create_user(self, user_repo, sample_user_data):
        """Test user creation."""
        # Mock the execute_command method
        mock_result = {
            "row": {
                "id": str(uuid.uuid4()),
                "email": sample_user_data["email"],
                "first_name": sample_user_data["first_name"],
                "last_name": sample_user_data["last_name"],
                "is_active": True,
                "sso_enabled": True,
                "mfa_enabled": True,
                "created_at": datetime.now(),
                "updated_at": datetime.now()
            }
        }
        
        with patch.object(user_repo, 'execute_command', return_value=mock_result):
            result = await user_repo.create_user(sample_user_data)
            
            assert result["email"] == sample_user_data["email"]
            assert result["first_name"] == sample_user_data["first_name"]
            assert result["is_active"] is True
    
    @pytest.mark.asyncio
    async def test_get_user(self, user_repo):
        """Test getting user by ID."""
        user_id = str(uuid.uuid4())
        mock_result = [{
            "id": user_id,
            "email": "test@example.com",
            "first_name": "Test",
            "last_name": "User"
        }]
        
        with patch.object(user_repo, 'execute_query', return_value=mock_result):
            result = await user_repo.get_user(user_id)
            
            assert result["id"] == user_id
            assert result["email"] == "test@example.com"
    
    @pytest.mark.asyncio
    async def test_get_user_not_found(self, user_repo):
        """Test getting non-existent user."""
        with patch.object(user_repo, 'execute_query', return_value=[]):
            result = await user_repo.get_user("non-existent-id")
            assert result is None
    
    @pytest.mark.asyncio
    async def test_list_users_with_filters(self, user_repo):
        """Test listing users with various filters."""
        mock_users = [
            {"id": str(uuid.uuid4()), "email": "user1@example.com", "department": "Engineering"},
            {"id": str(uuid.uuid4()), "email": "user2@example.com", "department": "Marketing"}
        ]
        
        with patch.object(user_repo, 'execute_query', return_value=mock_users):
            # Test with search filter
            result = await user_repo.list_users(search="user1")
            assert len(result) == 2  # Mock returns all
            
            # Test with department filter
            result = await user_repo.list_users(department="Engineering")
            assert len(result) == 2  # Mock returns all
            
            # Test with pagination
            result = await user_repo.list_users(offset=10, limit=5)
            assert len(result) == 2  # Mock returns all
    
    @pytest.mark.asyncio
    async def test_update_user(self, user_repo):
        """Test user update."""
        user_id = str(uuid.uuid4())
        update_data = {"first_name": "Updated", "department": "New Department"}
        
        mock_result = {
            "row": {
                "id": user_id,
                "first_name": "Updated",
                "department": "New Department",
                "updated_at": datetime.now()
            }
        }
        
        with patch.object(user_repo, 'execute_command', return_value=mock_result):
            result = await user_repo.update_user(user_id, update_data)
            
            assert result["id"] == user_id
            assert result["first_name"] == "Updated"
            assert result["department"] == "New Department"
    
    @pytest.mark.asyncio
    async def test_delete_user(self, user_repo):
        """Test user deletion (soft delete)."""
        user_id = str(uuid.uuid4())
        mock_result = {"rows_affected": 1}
        
        with patch.object(user_repo, 'execute_command', return_value=mock_result):
            result = await user_repo.delete_user(user_id)
            assert result is True
    
    @pytest.mark.asyncio
    async def test_get_user_statistics(self, user_repo):
        """Test getting user statistics."""
        mock_total = [{"total": 100}]
        mock_active = [{"active": 85}]
        mock_new_users = [{"new_today": 5, "new_week": 15, "new_month": 45}]
        mock_departments = [
            {"department": "Engineering", "count": 40},
            {"department": "Marketing", "count": 25}
        ]
        
        with patch.object(user_repo, 'execute_query') as mock_query:
            mock_query.side_effect = [
                mock_total,
                mock_active,
                mock_new_users,
                mock_departments
            ]
            
            stats = await user_repo.get_user_statistics()
            
            assert stats["total_users"] == 100
            assert stats["active_users"] == 85
            assert stats["new_users_today"] == 5
            assert stats["users_by_department"]["Engineering"] == 40


class TestRoleRepository:
    """Test RoleRepository operations."""
    
    @pytest.fixture
    def role_repo(self):
        """Create RoleRepository instance for testing."""
        return RoleRepository()
    
    @pytest.mark.asyncio
    async def test_create_role(self, role_repo, sample_role_data):
        """Test role creation."""
        mock_result = {
            "row": {
                "id": str(uuid.uuid4()),
                "name": sample_role_data["name"],
                "description": sample_role_data["description"],
                "permissions": sample_role_data["permissions"],
                "is_system_role": False,
                "created_at": datetime.now()
            }
        }
        
        with patch.object(role_repo, 'execute_command', return_value=mock_result):
            result = await role_repo.create_role(sample_role_data)
            
            assert result["name"] == sample_role_data["name"]
            assert result["permissions"] == sample_role_data["permissions"]
    
    @pytest.mark.asyncio
    async def test_get_role(self, role_repo):
        """Test getting role by name."""
        role_name = "test_role"
        mock_result = [{
            "id": str(uuid.uuid4()),
            "name": role_name,
            "description": "Test role",
            "user_count": 5
        }]
        
        with patch.object(role_repo, 'execute_query', return_value=mock_result):
            result = await role_repo.get_role(role_name)
            
            assert result["name"] == role_name
            assert result["user_count"] == 5
    
    @pytest.mark.asyncio
    async def test_assign_role(self, role_repo):
        """Test role assignment."""
        user_id = str(uuid.uuid4())
        role_id = str(uuid.uuid4())
        
        mock_result = {
            "row": {
                "id": str(uuid.uuid4()),
                "user_id": user_id,
                "role_id": role_id,
                "assigned_at": datetime.now()
            }
        }
        
        with patch.object(role_repo, 'execute_command', return_value=mock_result):
            result = await role_repo.assign_role(user_id, role_id)
            
            assert result["user_id"] == user_id
            assert result["role_id"] == role_id
    
    @pytest.mark.asyncio
    async def test_revoke_role(self, role_repo):
        """Test role revocation."""
        user_id = str(uuid.uuid4())
        role_id = str(uuid.uuid4())
        
        mock_result = {"rows_affected": 1}
        
        with patch.object(role_repo, 'execute_command', return_value=mock_result):
            result = await role_repo.revoke_role(user_id, role_id)
            
            assert result is True
    
    @pytest.mark.asyncio
    async def test_get_user_roles(self, role_repo):
        """Test getting user roles."""
        user_id = str(uuid.uuid4())
        mock_roles = [
            {
                "id": str(uuid.uuid4()),
                "name": "admin",
                "assigned_at": datetime.now(),
                "expires_at": None
            },
            {
                "id": str(uuid.uuid4()),
                "name": "user",
                "assigned_at": datetime.now(),
                "expires_at": datetime.now() + timedelta(days=30)
            }
        ]
        
        with patch.object(role_repo, 'execute_query', return_value=mock_roles):
            result = await role_repo.get_user_roles(user_id)
            
            assert len(result) == 2
            assert result[0]["name"] == "admin"
            assert result[1]["expires_at"] is not None


class TestSessionRepository:
    """Test SessionRepository operations."""
    
    @pytest.fixture
    def session_repo(self):
        """Create SessionRepository instance for testing."""
        return SessionRepository()
    
    @pytest.mark.asyncio
    async def test_create_session(self, session_repo):
        """Test session creation."""
        session_data = {
            "user_id": str(uuid.uuid4()),
            "access_token": "test_token",
            "device_id": "test_device",
            "ip_address": "192.168.1.1"
        }
        
        mock_result = {
            "row": {
                "id": str(uuid.uuid4()),
                **session_data,
                "created_at": datetime.now(),
                "expires_at": datetime.now() + timedelta(hours=1)
            }
        }
        
        with patch.object(session_repo, 'execute_command', return_value=mock_result):
            result = await session_repo.create_session(session_data)
            
            assert result["user_id"] == session_data["user_id"]
            assert result["access_token"] == session_data["access_token"]
    
    @pytest.mark.asyncio
    async def test_get_session(self, session_repo):
        """Test getting session by ID."""
        session_id = str(uuid.uuid4())
        mock_result = [{
            "id": session_id,
            "user_id": str(uuid.uuid4()),
            "access_token": "test_token",
            "expires_at": datetime.now() + timedelta(hours=1)
        }]
        
        with patch.object(session_repo, 'execute_query', return_value=mock_result):
            result = await session_repo.get_session(session_id)
            
            assert result["id"] == session_id
    
    @pytest.mark.asyncio
    async def test_invalidate_session(self, session_repo):
        """Test session invalidation."""
        session_id = str(uuid.uuid4())
        mock_result = {"rows_affected": 1}
        
        with patch.object(session_repo, 'execute_command', return_value=mock_result):
            result = await session_repo.invalidate_session(session_id)
            
            assert result is True


class TestAuditRepository:
    """Test AuditRepository operations."""
    
    @pytest.fixture
    def audit_repo(self):
        """Create AuditRepository instance for testing."""
        return AuditRepository()
    
    @pytest.mark.asyncio
    async def test_create_audit_entry(self, audit_repo):
        """Test audit entry creation."""
        audit_data = {
            "event_type": "user_created",
            "event_severity": "INFO",
            "user_id": str(uuid.uuid4()),
            "action": "create",
            "event_data": {"test": "data"}
        }
        
        mock_result = {
            "row": {
                "id": str(uuid.uuid4()),
                **audit_data,
                "timestamp": datetime.now()
            }
        }
        
        with patch.object(audit_repo, 'execute_command', return_value=mock_result):
            result = await audit_repo.create_audit_entry(audit_data)
            
            assert result["event_type"] == audit_data["event_type"]
            assert result["user_id"] == audit_data["user_id"]
    
    @pytest.mark.asyncio
    async def test_query_audit_logs(self, audit_repo):
        """Test querying audit logs with filters."""
        mock_logs = [
            {
                "id": str(uuid.uuid4()),
                "event_type": "user_login",
                "event_severity": "INFO",
                "timestamp": datetime.now()
            },
            {
                "id": str(uuid.uuid4()),
                "event_type": "user_logout",
                "event_severity": "INFO",
                "timestamp": datetime.now()
            }
        ]
        
        with patch.object(audit_repo, 'execute_query', return_value=mock_logs):
            # Test basic query
            result = await audit_repo.query_audit_logs()
            assert len(result) == 2
            
            # Test with filters
            result = await audit_repo.query_audit_logs(
                event_type="user_login",
                severity="INFO",
                limit=10
            )
            assert len(result) == 2  # Mock returns all


class TestPermissionRepository:
    """Test PermissionRepository operations."""
    
    @pytest.fixture
    def perm_repo(self):
        """Create PermissionRepository instance for testing."""
        return PermissionRepository()
    
    @pytest.mark.asyncio
    async def test_create_policy(self, perm_repo):
        """Test ABAC policy creation."""
        policy_data = {
            "name": "test_policy",
            "description": "Test policy",
            "resource_pattern": "users:*",
            "conditions": [
                {"attribute": "department", "operator": "equals", "value": "Engineering"}
            ],
            "effect": "allow",
            "priority": 100
        }
        
        mock_result = {
            "row": {
                "id": str(uuid.uuid4()),
                **policy_data,
                "created_at": datetime.now()
            }
        }
        
        with patch.object(perm_repo, 'execute_command', return_value=mock_result):
            result = await perm_repo.create_policy(policy_data)
            
            assert result["name"] == policy_data["name"]
            assert result["effect"] == policy_data["effect"]
    
    @pytest.mark.asyncio
    async def test_get_policies_for_resource(self, perm_repo):
        """Test getting policies for a resource."""
        resource = "users:123"
        mock_policies = [
            {
                "id": str(uuid.uuid4()),
                "name": "user_read_policy",
                "resource_pattern": "users:*",
                "effect": "allow",
                "priority": 100
            }
        ]
        
        with patch.object(perm_repo, 'execute_query', return_value=mock_policies):
            result = await perm_repo.get_policies_for_resource(resource)
            
            assert len(result) == 1
            assert result[0]["name"] == "user_read_policy"
    
    @pytest.mark.asyncio
    async def test_record_permission_check(self, perm_repo):
        """Test recording permission check."""
        check_data = {
            "user_id": str(uuid.uuid4()),
            "resource": "users:123",
            "action": "read",
            "allowed": True,
            "evaluation_time_ms": 15.5
        }
        
        with patch.object(perm_repo, 'execute_command', return_value={"rows_affected": 1}):
            # Should not raise exception
            await perm_repo.record_permission_check(check_data)


# Performance tests
class TestRepositoryPerformance:
    """Test repository performance characteristics."""
    
    @pytest.mark.asyncio
    async def test_user_creation_performance(self, sample_user_data, performance_timer):
        """Test user creation performance."""
        user_repo = UserRepository()
        
        mock_result = {
            "row": {
                "id": str(uuid.uuid4()),
                **sample_user_data,
                "created_at": datetime.now()
            }
        }
        
        with patch.object(user_repo, 'execute_command', return_value=mock_result):
            performance_timer.start()
            await user_repo.create_user(sample_user_data)
            elapsed = performance_timer.stop()
            
            # Should be very fast since it's mocked
            assert elapsed < 100  # Less than 100ms
    
    @pytest.mark.asyncio
    async def test_concurrent_operations(self, sample_user_data):
        """Test concurrent repository operations."""
        user_repo = UserRepository()
        
        mock_result = {
            "row": {
                "id": str(uuid.uuid4()),
                **sample_user_data,
                "created_at": datetime.now()
            }
        }
        
        with patch.object(user_repo, 'execute_command', return_value=mock_result):
            # Test concurrent user creation
            tasks = [
                user_repo.create_user({**sample_user_data, "email": f"user{i}@example.com"})
                for i in range(10)
            ]
            
            results = await asyncio.gather(*tasks)
            
            # All operations should succeed
            assert len(results) == 10
            for result in results:
                assert "id" in result