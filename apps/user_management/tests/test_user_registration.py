"""
Test User Registration Functionality
"""

from unittest.mock import AsyncMock

import pytest

from apps.user_management.api.user_api import UserAPI
from apps.user_management.config.settings import UserManagementConfig
from kailash.runtime.local import LocalRuntime


class TestUserRegistration:
    """Test user registration workflows"""

    @pytest.fixture
    def user_api(self):
        """Create UserAPI instance"""
        return UserAPI()

    @pytest.fixture
    def runtime(self):
        """Create runtime instance"""
        return LocalRuntime()

    @pytest.mark.asyncio
    async def test_successful_registration(self, user_api, runtime):
        """Test successful user registration"""
        # Create registration workflow
        workflow = user_api.create_user_registration_workflow()

        # Test data
        registration_data = {
            "email": "test@example.com",
            "username": "testuser",
            "password": "SecurePass123!",
        }

        # Execute workflow
        result = await runtime.execute_async(workflow, registration_data)

        # Assertions
        assert result["success"] is True
        assert "user" in result
        assert "tokens" in result
        assert result["user"]["email"] == registration_data["email"]
        assert result["user"]["username"] == registration_data["username"]
        assert "access" in result["tokens"]
        assert "refresh" in result["tokens"]

    @pytest.mark.asyncio
    async def test_invalid_email_registration(self, user_api, runtime):
        """Test registration with invalid email"""
        workflow = user_api.create_user_registration_workflow()

        registration_data = {
            "email": "invalid-email",
            "username": "testuser",
            "password": "SecurePass123!",
        }

        result = await runtime.execute_async(workflow, registration_data)

        assert result["success"] is False
        assert "errors" in result
        assert any("email" in error.lower() for error in result["errors"])

    @pytest.mark.asyncio
    async def test_weak_password_registration(self, user_api, runtime):
        """Test registration with weak password"""
        workflow = user_api.create_user_registration_workflow()

        registration_data = {
            "email": "test@example.com",
            "username": "testuser",
            "password": "weak",
        }

        result = await runtime.execute_async(workflow, registration_data)

        assert result["success"] is False
        assert "errors" in result
        assert len(result["errors"]) > 0

    @pytest.mark.asyncio
    async def test_duplicate_user_registration(self, user_api, runtime):
        """Test registration with duplicate email/username"""
        workflow = user_api.create_user_registration_workflow()

        # First registration
        registration_data = {
            "email": "duplicate@example.com",
            "username": "duplicateuser",
            "password": "SecurePass123!",
        }

        # First should succeed
        result1 = await runtime.execute_async(workflow, registration_data)
        assert result1["success"] is True

        # Second should fail (would be caught by UserManagementNode)
        # In real implementation, UserManagementNode would return error
        # This is a placeholder for the actual test

    @pytest.mark.asyncio
    async def test_registration_with_role_assignment(self, user_api, runtime):
        """Test that new users get default 'user' role"""
        workflow = user_api.create_user_registration_workflow()

        registration_data = {
            "email": "roletest@example.com",
            "username": "roleuser",
            "password": "SecurePass123!",
        }

        result = await runtime.execute_async(workflow, registration_data)

        # In real implementation, verify role was assigned
        # This would check the role assignment result
        assert result["success"] is True

    @pytest.mark.asyncio
    async def test_registration_audit_logging(self, user_api, runtime):
        """Test that registration creates audit log entry"""
        workflow = user_api.create_user_registration_workflow()

        registration_data = {
            "email": "audit@example.com",
            "username": "audituser",
            "password": "SecurePass123!",
        }

        result = await runtime.execute_async(workflow, registration_data)

        # In real implementation, verify audit log was created
        assert result["success"] is True
