"""
Test Authentication and Session Management
"""

from datetime import datetime, timedelta
from unittest.mock import AsyncMock, patch

import jwt
import pytest

from apps.user_management.api.user_api import UserAPI
from apps.user_management.config.settings import UserManagementConfig
from apps.user_management.middleware.auth_middleware import AuthMiddleware
from apps.user_management.workflows.auth_workflows import AuthWorkflows
from kailash.runtime.local import LocalRuntime


class TestAuthentication:
    """Test authentication workflows"""

    @pytest.fixture
    def config(self):
        """Get config instance"""
        return UserManagementConfig()

    @pytest.fixture
    def user_api(self):
        """Create UserAPI instance"""
        return UserAPI()

    @pytest.fixture
    def auth_workflows(self):
        """Create AuthWorkflows instance"""
        return AuthWorkflows()

    @pytest.fixture
    def auth_middleware(self):
        """Create AuthMiddleware instance"""
        return AuthMiddleware()

    @pytest.fixture
    def runtime(self):
        """Create runtime instance"""
        return LocalRuntime()

    @pytest.fixture
    def mock_user(self):
        """Create mock user data"""
        return {
            "id": "user123",
            "username": "testuser",
            "email": "test@example.com",
            "password_hash": "$2b$12$KIXxPfnK.6Z5LwapTLFb4OqQZyT7Xw1L8c3r2K1jT9nRlD5D2qQ9i",  # "password123"
            "status": "active",
        }

    @pytest.mark.asyncio
    async def test_successful_login(self, user_api, runtime, mock_user):
        """Test successful user login"""
        workflow = user_api.create_login_workflow()

        # Mock the user fetcher to return our test user
        with patch.object(runtime, "execute_node_async") as mock_execute:
            mock_execute.return_value = {"user": mock_user}

            login_data = {"email": "test@example.com", "password": "password123"}

            result = await runtime.execute_async(workflow, login_data)

            # Should return success with tokens
            assert result.get("success") is True
            assert "tokens" in result
            assert "access" in result["tokens"]
            assert "refresh" in result["tokens"]

    @pytest.mark.asyncio
    async def test_invalid_credentials(self, user_api, runtime):
        """Test login with invalid credentials"""
        workflow = user_api.create_login_workflow()

        with patch.object(runtime, "execute_node_async") as mock_execute:
            # User not found
            mock_execute.return_value = {"user": None}

            login_data = {
                "email": "nonexistent@example.com",
                "password": "wrongpassword",
            }

            result = await runtime.execute_async(workflow, login_data)

            assert result.get("success") is False
            assert "error" in result

    @pytest.mark.asyncio
    async def test_jwt_token_generation(self, config):
        """Test JWT token generation"""
        user_data = {
            "user_id": "user123",
            "username": "testuser",
            "email": "test@example.com",
        }

        # Generate token
        now = datetime.utcnow()
        payload = {**user_data, "exp": now + timedelta(hours=1), "iat": now}

        token = jwt.encode(
            payload, config.JWT_SECRET_KEY, algorithm=config.JWT_ALGORITHM
        )

        # Decode and verify
        decoded = jwt.decode(
            token, config.JWT_SECRET_KEY, algorithms=[config.JWT_ALGORITHM]
        )

        assert decoded["user_id"] == user_data["user_id"]
        assert decoded["username"] == user_data["username"]
        assert decoded["email"] == user_data["email"]

    @pytest.mark.asyncio
    async def test_token_expiration(self, config):
        """Test JWT token expiration"""
        # Create expired token
        past_time = datetime.utcnow() - timedelta(hours=2)
        payload = {
            "user_id": "user123",
            "exp": past_time,
            "iat": past_time - timedelta(hours=1),
        }

        token = jwt.encode(
            payload, config.JWT_SECRET_KEY, algorithm=config.JWT_ALGORITHM
        )

        # Should raise exception on decode
        with pytest.raises(jwt.ExpiredSignatureError):
            jwt.decode(token, config.JWT_SECRET_KEY, algorithms=[config.JWT_ALGORITHM])

    @pytest.mark.asyncio
    async def test_password_reset_workflow(self, auth_workflows, runtime):
        """Test password reset request workflow"""
        workflow = auth_workflows.create_password_reset_workflow()

        with patch.object(runtime, "execute_node_async") as mock_execute:
            # Mock user found
            mock_execute.return_value = {
                "user": {
                    "id": "user123",
                    "email": "test@example.com",
                    "username": "testuser",
                }
            }

            result = await runtime.execute_async(
                workflow, {"email": "test@example.com"}
            )

            assert result.get("success") is True
            assert "reset_token" in result
            assert "email_data" in result

    @pytest.mark.asyncio
    async def test_password_reset_confirmation(self, auth_workflows, runtime):
        """Test password reset confirmation"""
        workflow = auth_workflows.create_password_reset_confirm_workflow()

        reset_data = {
            "token": "valid_reset_token_12345678901234567890123456",
            "user_id": "user123",
            "new_password": "NewSecurePass123!",
        }

        with patch.object(runtime, "execute_node_async") as mock_execute:
            mock_execute.return_value = {"user": {"id": "user123"}, "success": True}

            result = await runtime.execute_async(workflow, reset_data)

            assert result.get("success") is True
            assert result.get("sessions_invalidated") is True

    @pytest.mark.asyncio
    async def test_2fa_setup(self, auth_workflows, runtime):
        """Test 2FA setup workflow"""
        workflow = auth_workflows.create_2fa_setup_workflow()

        with patch.object(runtime, "execute_node_async") as mock_execute:
            mock_execute.return_value = {"success": True}

            result = await runtime.execute_async(
                workflow, {"user_id": "user123", "allowed": True}
            )

            assert "provisioning_uri" in result
            assert "totp_secret" in result["updates"]["two_factor_secret"]

    @pytest.mark.asyncio
    async def test_session_management(self, auth_workflows, runtime, config):
        """Test session management workflow"""
        workflow = auth_workflows.create_session_management_workflow()

        # Create valid token
        now = datetime.utcnow()
        payload = {
            "user_id": "user123",
            "session_id": "session123",
            "exp": now + timedelta(minutes=5),  # Expires soon
            "iat": now,
        }

        token = jwt.encode(
            payload, config.JWT_SECRET_KEY, algorithm=config.JWT_ALGORITHM
        )

        result = await runtime.execute_async(workflow, {"access_token": token})

        assert result.get("success") is True
        assert result.get("refreshed") is True  # Should refresh due to short expiry
        assert "new_token" in result

    @pytest.mark.asyncio
    async def test_concurrent_login_sessions(self, user_api, runtime, config):
        """Test handling of concurrent login sessions"""
        workflow = user_api.create_login_workflow()

        # Simulate multiple login attempts
        sessions = []
        for i in range(3):
            with patch.object(runtime, "execute_node_async") as mock_execute:
                mock_execute.return_value = {
                    "user": {
                        "id": f"user{i}",
                        "email": f"user{i}@example.com",
                        "password_hash": "hashed",
                    }
                }

                result = await runtime.execute_async(
                    workflow, {"email": f"user{i}@example.com", "password": "password"}
                )

                if result.get("success"):
                    sessions.append(result.get("session"))

        # Should handle multiple sessions
        assert len(sessions) <= config.MAX_SESSIONS_PER_USER
