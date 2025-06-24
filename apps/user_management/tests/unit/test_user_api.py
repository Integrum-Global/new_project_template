"""
Unit Tests for User API Components
Tests individual API methods with real Kailash SDK components
"""

import json
from datetime import datetime, timedelta

import pytest

from apps.user_management.api.user_api import UserAPI
from apps.user_management.config.settings import UserManagementConfig
from kailash.runtime.local import LocalRuntime
from kailash.workflow.builder import WorkflowBuilder


class TestUserAPI:
    """Unit tests for UserAPI class"""

    @pytest.fixture
    def user_api(self):
        """Create UserAPI instance"""
        return UserAPI()

    @pytest.fixture
    def runtime(self):
        """Create LocalRuntime instance"""
        return LocalRuntime()

    @pytest.fixture
    def config(self):
        """Get configuration"""
        return UserManagementConfig()

    @pytest.mark.asyncio
    async def test_create_user_registration_workflow(self, user_api):
        """Test user registration workflow creation"""
        workflow = user_api.create_user_registration_workflow()

        # Verify workflow structure
        assert workflow.name == "user_registration"

        # Check all required nodes are present
        expected_nodes = [
            "validator",
            "password_hasher",
            "user_creator",
            "role_assigner",
            "audit_logger",
            "token_generator",
        ]

        for node_name in expected_nodes:
            assert node_name in workflow.nodes

        # Verify connections
        assert len(workflow.connections) >= 7  # At least 7 connections

        # Check node configurations
        validator_node = workflow.nodes["validator"]
        assert validator_node["type"] == "PythonCodeNode"
        assert "code" in validator_node["config"]

        user_creator_node = workflow.nodes["user_creator"]
        assert user_creator_node["type"] == "UserManagementNode"

    @pytest.mark.asyncio
    async def test_user_validation_logic(self, user_api, runtime):
        """Test user input validation in isolation"""
        workflow = user_api.create_user_registration_workflow()

        # Extract validator node for testing
        validator_config = workflow.nodes["validator"]["config"]
        validator_node = runtime.create_node("PythonCodeNode", validator_config)

        # Test valid input
        valid_input = {
            "email": "test@example.com",
            "username": "testuser123",
            "password": "SecurePass123!",
        }

        result = await runtime.execute_node_async(validator_node, valid_input)
        assert result["success"] is True
        assert "user_data" in result

        # Test invalid email
        invalid_email = {
            "email": "not-an-email",
            "username": "testuser",
            "password": "SecurePass123!",
        }

        result = await runtime.execute_node_async(validator_node, invalid_email)
        assert result["success"] is False
        assert "errors" in result
        assert any("email" in error.lower() for error in result["errors"])

        # Test weak password
        weak_password = {
            "email": "test@example.com",
            "username": "testuser",
            "password": "weak",
        }

        result = await runtime.execute_node_async(validator_node, weak_password)
        assert result["success"] is False
        assert len(result["errors"]) >= 4  # Multiple password requirements

        # Test short username
        short_username = {
            "email": "test@example.com",
            "username": "ab",
            "password": "SecurePass123!",
        }

        result = await runtime.execute_node_async(validator_node, short_username)
        assert result["success"] is False
        assert any("username" in error.lower() for error in result["errors"])

    @pytest.mark.asyncio
    async def test_password_hashing(self, user_api, runtime):
        """Test password hashing functionality"""
        workflow = user_api.create_user_registration_workflow()

        # Extract password hasher node
        hasher_config = workflow.nodes["password_hasher"]["config"]
        hasher_node = runtime.create_node("PythonCodeNode", hasher_config)

        # Test successful hashing
        input_data = {
            "success": True,
            "user_data": {
                "email": "test@example.com",
                "username": "testuser",
                "password": "PlainTextPass123!",
            },
        }

        result = await runtime.execute_node_async(hasher_node, input_data)

        assert "password_hash" in result["data"]
        assert result["data"]["password_hash"] != input_data["user_data"]["password"]
        assert "password" not in result["data"]  # Plain password removed
        assert result["operation"] == "create_user"

        # Verify bcrypt format
        import bcrypt

        assert result["data"]["password_hash"].startswith("$2b$")

        # Test with validation failure (should pass through)
        failed_input = {"success": False, "errors": ["Invalid input"]}

        result = await runtime.execute_node_async(hasher_node, failed_input)
        assert result["success"] is False
        assert result["errors"] == ["Invalid input"]

    @pytest.mark.asyncio
    async def test_token_generation(self, user_api, runtime, config):
        """Test JWT token generation"""
        workflow = user_api.create_user_registration_workflow()

        # Extract token generator node
        token_config = workflow.nodes["token_generator"]["config"]
        token_node = runtime.create_node("PythonCodeNode", token_config)

        # Test token generation
        input_data = {
            "result": {
                "user": {
                    "id": "test-user-123",
                    "username": "testuser",
                    "email": "test@example.com",
                }
            }
        }

        result = await runtime.execute_node_async(token_node, input_data)

        assert result["success"] is True
        assert "tokens" in result
        assert "access" in result["tokens"]
        assert "refresh" in result["tokens"]

        # Verify token structure
        import jwt

        # Decode access token
        access_payload = jwt.decode(
            result["tokens"]["access"],
            config.JWT_SECRET_KEY,
            algorithms=[config.JWT_ALGORITHM],
        )

        assert access_payload["user_id"] == "test-user-123"
        assert access_payload["username"] == "testuser"
        assert access_payload["email"] == "test@example.com"
        assert "exp" in access_payload
        assert "iat" in access_payload

        # Verify expiration times
        now = datetime.utcnow()
        exp_time = datetime.fromtimestamp(access_payload["exp"])
        assert exp_time > now
        assert exp_time < now + timedelta(hours=2)  # Within expected range

    @pytest.mark.asyncio
    async def test_create_login_workflow(self, user_api):
        """Test login workflow creation"""
        workflow = user_api.create_login_workflow()

        assert workflow.name == "user_login"

        # Check required nodes
        expected_nodes = [
            "user_fetcher",
            "password_verifier",
            "permission_checker",
            "session_creator",
            "audit_logger",
            "security_checker",
        ]

        for node_name in expected_nodes:
            assert node_name in workflow.nodes

        # Verify user fetcher configuration
        fetcher = workflow.nodes["user_fetcher"]
        assert fetcher["config"]["operation"] == "get_user"
        assert fetcher["config"]["identifier"] == "$.email"

    @pytest.mark.asyncio
    async def test_profile_update_workflow(self, user_api):
        """Test profile update workflow creation"""
        workflow = user_api.create_profile_update_workflow()

        assert workflow.name == "profile_update"

        # Check nodes
        expected_nodes = ["permission_checker", "validator", "updater", "audit_logger"]

        for node_name in expected_nodes:
            assert node_name in workflow.nodes

        # Verify permission check configuration
        perm_checker = workflow.nodes["permission_checker"]
        assert perm_checker["config"]["resource"] == "profile"
        assert perm_checker["config"]["action"] == "update"

    @pytest.mark.asyncio
    async def test_password_verification(self, user_api, runtime):
        """Test password verification logic"""
        workflow = user_api.create_login_workflow()

        # Extract password verifier
        verifier_config = workflow.nodes["password_verifier"]["config"]
        verifier_node = runtime.create_node("PythonCodeNode", verifier_config)

        # Test successful verification
        import bcrypt

        password = "TestPass123!"
        salt = bcrypt.gensalt()
        hashed = bcrypt.hashpw(password.encode("utf-8"), salt).decode("utf-8")

        input_data = {
            "user": {"id": "user123", "username": "testuser", "password_hash": hashed},
            "password": password,
        }

        result = await runtime.execute_node_async(verifier_node, input_data)

        assert result["success"] is True
        assert result["user"]["id"] == "user123"
        assert "check_permissions" in result

        # Test failed verification
        wrong_password_input = {
            "user": {"id": "user123", "password_hash": hashed},
            "password": "WrongPassword123!",
        }

        result = await runtime.execute_node_async(verifier_node, wrong_password_input)
        assert result["success"] is False
        assert result["error"] == "Invalid credentials"

        # Test user not found
        no_user_input = {"user": None, "password": "anypassword"}

        result = await runtime.execute_node_async(verifier_node, no_user_input)
        assert result["success"] is False
        assert result["error"] == "User not found"

    @pytest.mark.asyncio
    async def test_session_creation(self, user_api, runtime, config):
        """Test session creation logic"""
        workflow = user_api.create_login_workflow()

        # Extract session creator
        session_config = workflow.nodes["session_creator"]["config"]
        session_node = runtime.create_node("PythonCodeNode", session_config)

        # Test successful session creation
        input_data = {
            "allowed": True,
            "user": {
                "id": "user123",
                "username": "testuser",
                "email": "test@example.com",
            },
        }

        result = await runtime.execute_node_async(session_node, input_data)

        assert result["success"] is True
        assert "session" in result
        assert "id" in result["session"]
        assert "tokens" in result

        # Verify session ID format (UUID)
        import uuid

        try:
            uuid.UUID(result["session"]["id"])
            uuid_valid = True
        except ValueError:
            uuid_valid = False
        assert uuid_valid

        # Test denied access
        denied_input = {"allowed": False, "user": {"id": "user123"}}

        result = await runtime.execute_node_async(session_node, denied_input)
        assert result["success"] is False
        assert result["error"] == "Access denied"

    @pytest.mark.asyncio
    async def test_profile_validation(self, user_api, runtime):
        """Test profile update validation"""
        workflow = user_api.create_profile_update_workflow()

        # Extract validator
        validator_config = workflow.nodes["validator"]["config"]
        validator_node = runtime.create_node("PythonCodeNode", validator_config)

        # Test allowed update
        input_data = {
            "allowed": True,
            "user_id": "user123",
            "updates": {
                "first_name": "John",
                "last_name": "Doe",
                "phone": "+1234567890",
                "bio": "Software engineer",
                "avatar_url": "https://example.com/avatar.jpg",
                "preferences": {"theme": "dark"},
            },
        }

        result = await runtime.execute_node_async(validator_node, input_data)

        assert result["operation"] == "update_profile"
        assert result["user_id"] == "user123"
        assert all(field in result["updates"] for field in input_data["updates"])

        # Test with disallowed fields
        disallowed_input = {
            "allowed": True,
            "user_id": "user123",
            "updates": {
                "first_name": "John",
                "is_superuser": True,  # Not allowed
                "password_hash": "hacked",  # Not allowed
                "id": "different-id",  # Not allowed
            },
        }

        result = await runtime.execute_node_async(validator_node, disallowed_input)

        assert "is_superuser" not in result["updates"]
        assert "password_hash" not in result["updates"]
        assert "id" not in result["updates"]
        assert "first_name" in result["updates"]  # Allowed field

        # Test permission denied
        denied_input = {"allowed": False, "updates": {"first_name": "John"}}

        result = await runtime.execute_node_async(validator_node, denied_input)
        assert result["success"] is False
        assert result["error"] == "Permission denied"
