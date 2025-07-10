"""
Unit tests for Enterprise Authentication Manager.
"""

import hashlib
from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock, Mock, patch

import jwt
import pytest
from nexus.core.config import AuthProvider, MFAConfig
from nexus.enterprise.auth import APIKey, AuthToken, EnterpriseAuthManager


class TestEnterpriseAuthManager:
    """Test EnterpriseAuthManager class."""

    @pytest.fixture
    def auth_manager(self):
        """Create an auth manager instance."""
        providers = [
            AuthProvider(type="ldap", config={"name": "Corporate LDAP"}),
            AuthProvider(type="oauth2", config={"name": "Google OAuth"}),
            AuthProvider(type="local", config={"name": "Local Auth"}),
        ]
        mfa_config = MFAConfig(required=False, methods=["totp"])
        return EnterpriseAuthManager(providers, mfa_config)

    def test_initialization(self, auth_manager):
        """Test auth manager initialization."""
        assert len(auth_manager.providers) == 3
        assert auth_manager.mfa_config.required is False
        assert isinstance(auth_manager.jwt_secret, str)
        assert len(auth_manager._tokens) == 0
        assert len(auth_manager._api_keys) == 0

    @pytest.mark.asyncio
    async def test_authenticate_local(self, auth_manager):
        """Test local authentication."""
        credentials = {"username": "testuser", "password": "testpass"}

        token = await auth_manager.authenticate(credentials)

        assert token is not None
        assert isinstance(token, AuthToken)
        assert token.user_id == "testuser"
        assert token.token_type == "bearer"
        assert token.expires_at > datetime.now(timezone.utc)

        # Check token is stored
        assert token.token in auth_manager._tokens
        assert "testuser" in auth_manager._user_sessions

    @pytest.mark.asyncio
    async def test_authenticate_ldap(self, auth_manager):
        """Test LDAP authentication."""
        credentials = {"username": "ldapuser", "password": "ldappass"}

        token = await auth_manager.authenticate(credentials, provider="ldap")

        assert token is not None
        assert token.user_id == "ldapuser"
        assert token.metadata["provider"] == "ldap"
        assert token.metadata["email"] == "ldapuser@company.com"

    @pytest.mark.asyncio
    async def test_authenticate_oauth2(self, auth_manager):
        """Test OAuth2 authentication."""
        credentials = {"code": "auth_code_123"}

        token = await auth_manager.authenticate(credentials, provider="oauth2")

        assert token is not None
        assert token.user_id == "oauth_user"
        assert token.metadata["provider"] == "oauth2"

    @pytest.mark.asyncio
    async def test_authenticate_with_mfa(self):
        """Test authentication with MFA required."""
        providers = [AuthProvider(type="local", config={"name": "Local"})]
        mfa_config = MFAConfig(required=True, methods=["totp"])
        auth_manager = EnterpriseAuthManager(providers, mfa_config)

        # Without MFA code
        credentials = {"username": "mfauser", "password": "mfapass"}
        token = await auth_manager.authenticate(credentials)
        assert token is None  # Should fail without MFA

        # With MFA code
        credentials["mfa_code"] = "123456"
        token = await auth_manager.authenticate(credentials)
        assert token is not None
        assert token.user_id == "mfauser"

    @pytest.mark.asyncio
    async def test_authenticate_invalid(self, auth_manager):
        """Test invalid authentication."""
        # Missing credentials
        token = await auth_manager.authenticate({})
        assert token is None

        # Invalid provider
        token = await auth_manager.authenticate(
            {"username": "test", "password": "test"}, provider="invalid"
        )
        assert token is None

    def test_validate_token(self, auth_manager):
        """Test token validation."""
        # Create a token manually
        token = AuthToken(
            token="test_token",
            token_type="bearer",
            user_id="testuser",
            expires_at=datetime.now(timezone.utc) + timedelta(hours=1),
            metadata={"email": "test@example.com"},
        )
        auth_manager._tokens["test_token"] = token

        # Validate existing token
        user_info = auth_manager.validate_token("test_token")
        assert user_info is not None
        assert user_info["email"] == "test@example.com"

        # Validate expired token
        token.expires_at = datetime.now(timezone.utc) - timedelta(hours=1)
        user_info = auth_manager.validate_token("test_token")
        assert user_info is None

        # Validate JWT token
        import time

        payload = {
            "user_id": "jwtuser",
            "email": "jwt@example.com",
            "provider": "local",
            "exp": int(time.time()) + 3600,  # 1 hour from now
        }
        jwt_token = jwt.encode(payload, auth_manager.jwt_secret, algorithm="HS256")

        user_info = auth_manager.validate_token(jwt_token)
        assert user_info is not None
        assert user_info["user_id"] == "jwtuser"
        assert user_info["email"] == "jwt@example.com"

    def test_generate_api_key(self, auth_manager):
        """Test API key generation."""
        key = auth_manager.generate_api_key(
            app_name="Test App", permissions=["read", "write"], expires_in_days=30
        )

        assert isinstance(key, str)
        assert len(key) > 20

        # Check key is stored
        assert len(auth_manager._api_keys) == 1
        api_key = list(auth_manager._api_keys.values())[0]
        assert api_key.app_name == "Test App"
        assert api_key.permissions == ["read", "write"]
        assert api_key.expires_at is not None
        assert api_key.is_active is True

        # Key should be hashed
        assert api_key.key_hash != key
        assert api_key.key_hash == hashlib.sha256(key.encode()).hexdigest()

    def test_validate_api_key(self, auth_manager):
        """Test API key validation."""
        # Generate a key
        key = auth_manager.generate_api_key(app_name="Valid App", permissions=["read"])

        # Validate valid key
        app_info = auth_manager.validate_api_key(key)
        assert app_info is not None
        assert app_info["app_name"] == "Valid App"
        assert app_info["permissions"] == ["read"]
        assert "key_id" in app_info

        # Check last used was updated
        api_key = list(auth_manager._api_keys.values())[0]
        assert api_key.last_used is not None

        # Validate invalid key
        app_info = auth_manager.validate_api_key("invalid_key")
        assert app_info is None

        # Validate inactive key
        api_key.is_active = False
        app_info = auth_manager.validate_api_key(key)
        assert app_info is None

        # Validate expired key
        api_key.is_active = True
        api_key.expires_at = datetime.now(timezone.utc) - timedelta(days=1)
        app_info = auth_manager.validate_api_key(key)
        assert app_info is None

    def test_revoke_token(self, auth_manager):
        """Test token revocation."""
        # Create tokens
        token1 = AuthToken(
            token="token1",
            token_type="bearer",
            user_id="user1",
            expires_at=datetime.now(timezone.utc) + timedelta(hours=1),
        )
        token2 = AuthToken(
            token="token2",
            token_type="bearer",
            user_id="user1",
            expires_at=datetime.now(timezone.utc) + timedelta(hours=1),
        )

        auth_manager._tokens["token1"] = token1
        auth_manager._tokens["token2"] = token2
        auth_manager._user_sessions["user1"] = ["token1", "token2"]

        # Revoke one token
        result = auth_manager.revoke_token("token1")
        assert result is True
        assert "token1" not in auth_manager._tokens
        assert "token1" not in auth_manager._user_sessions["user1"]
        assert "token2" in auth_manager._user_sessions["user1"]

        # Revoke non-existent token
        result = auth_manager.revoke_token("nonexistent")
        assert result is False

    def test_revoke_user_tokens(self, auth_manager):
        """Test revoking all tokens for a user."""
        # Create multiple tokens
        for i in range(3):
            token = AuthToken(
                token=f"token{i}",
                token_type="bearer",
                user_id="multiuser",
                expires_at=datetime.now(timezone.utc) + timedelta(hours=1),
            )
            auth_manager._tokens[f"token{i}"] = token
        auth_manager._user_sessions["multiuser"] = ["token0", "token1", "token2"]

        # Revoke all user tokens
        count = auth_manager.revoke_user_tokens("multiuser")
        assert count == 3
        assert len(auth_manager._tokens) == 0
        assert len(auth_manager._user_sessions.get("multiuser", [])) == 0

    def test_list_api_keys(self, auth_manager):
        """Test listing API keys."""
        # Generate multiple keys
        auth_manager.generate_api_key("App 1", ["read"])
        auth_manager.generate_api_key("App 2", ["write"])
        auth_manager.generate_api_key("App 1", ["admin"])

        # List all keys
        all_keys = auth_manager.list_api_keys()
        assert len(all_keys) == 3

        # List by app name
        app1_keys = auth_manager.list_api_keys(app_name="App 1")
        assert len(app1_keys) == 2
        assert all(k.app_name == "App 1" for k in app1_keys)

        # Check sorting (newest first)
        assert all_keys[0].created_at >= all_keys[1].created_at

    def test_revoke_api_key(self, auth_manager):
        """Test revoking API key."""
        # Generate key
        key = auth_manager.generate_api_key("Revoke Test", ["read"])
        key_id = list(auth_manager._api_keys.keys())[0]

        # Revoke key
        result = auth_manager.revoke_api_key(key_id)
        assert result is True

        # Check key is inactive
        api_key = auth_manager._api_keys[key_id]
        assert api_key.is_active is False

        # Validate should fail
        app_info = auth_manager.validate_api_key(key)
        assert app_info is None

        # Revoke non-existent
        result = auth_manager.revoke_api_key("nonexistent")
        assert result is False

    @pytest.mark.asyncio
    async def test_health_check(self, auth_manager):
        """Test health check."""
        # Create some data
        await auth_manager.authenticate({"username": "test", "password": "test"})
        auth_manager.generate_api_key("Health App", ["read"])

        health = await auth_manager.health_check()

        assert health["healthy"] is True
        assert health["active_tokens"] == 1
        assert health["active_api_keys"] == 1
        assert health["mfa_enabled"] is False
        assert "providers" in health
        assert len(health["providers"]) == 3

    def test_auth_token_model(self):
        """Test AuthToken model."""
        token = AuthToken(
            token="test123",
            token_type="bearer",
            user_id="user1",
            expires_at=datetime.now(timezone.utc) + timedelta(hours=1),
            metadata={"role": "admin"},
        )

        assert token.token == "test123"
        assert token.token_type == "bearer"
        assert token.user_id == "user1"
        assert not token.is_expired()

        # Test expiration
        token.expires_at = datetime.now(timezone.utc) - timedelta(hours=1)
        assert token.is_expired()

        # Test to_dict
        token_dict = token.to_dict()
        assert token_dict["token"] == "test123..."  # Should be truncated
        assert token_dict["user_id"] == "user1"
        assert "expires_at" in token_dict

    def test_api_key_model(self):
        """Test APIKey model."""
        api_key = APIKey(
            key_id="ak_123",
            key_hash="hash123",
            app_name="Test App",
            permissions=["read", "write"],
            created_at=datetime.now(timezone.utc),
        )

        assert api_key.key_id == "ak_123"
        assert api_key.app_name == "Test App"
        assert api_key.permissions == ["read", "write"]
        assert api_key.is_active is True

        # Test to_dict
        key_dict = api_key.to_dict()
        assert key_dict["key_id"] == "ak_123"
        assert "key_hash" not in key_dict  # Should not expose hash
        assert key_dict["app_name"] == "Test App"
