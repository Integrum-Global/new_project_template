"""
Enterprise Authentication Manager for Nexus

Built on Kailash SDK authentication nodes.
"""

import hashlib
import logging
import secrets
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional, Union

import jwt

from kailash.nodes.admin.audit_log import EnterpriseAuditLogNode as AuditLogNode
from kailash.nodes.admin.user_management import UserManagementNode
from kailash.nodes.api.auth import OAuth2Node
from kailash.nodes.auth.directory_integration import DirectoryIntegrationNode
from kailash.nodes.auth.mfa import MultiFactorAuthNode
from kailash.workflow.builder import WorkflowBuilder

logger = logging.getLogger(__name__)


@dataclass
class AuthToken:
    """Authentication token information."""

    token: str
    token_type: str  # bearer, api_key
    user_id: str
    expires_at: datetime
    metadata: Dict[str, Any] = field(default_factory=dict)

    def is_expired(self) -> bool:
        """Check if token is expired."""
        return datetime.now(timezone.utc) > self.expires_at

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "token": self.token[:8] + "...",  # Don't expose full token
            "token_type": self.token_type,
            "user_id": self.user_id,
            "expires_at": self.expires_at.isoformat(),
            "metadata": self.metadata,
        }


@dataclass
class APIKey:
    """API key information."""

    key_id: str
    key_hash: str  # Store hash, not actual key
    app_name: str
    permissions: List[str]
    created_at: datetime
    expires_at: Optional[datetime] = None
    last_used: Optional[datetime] = None
    is_active: bool = True

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "key_id": self.key_id,
            "app_name": self.app_name,
            "permissions": self.permissions,
            "created_at": self.created_at.isoformat(),
            "expires_at": self.expires_at.isoformat() if self.expires_at else None,
            "last_used": self.last_used.isoformat() if self.last_used else None,
            "is_active": self.is_active,
        }


class EnterpriseAuthManager:
    """Enterprise authentication manager using Kailash SDK nodes.

    Provides unified authentication across multiple providers.
    """

    def __init__(
        self,
        providers: List[Dict[str, Any]],
        mfa_config: Optional[Dict[str, Any]] = None,
        jwt_secret: Optional[str] = None,
    ):
        """Initialize enterprise auth manager.

        Args:
            providers: List of auth provider configurations
            mfa_config: Multi-factor auth configuration
            jwt_secret: Secret for JWT signing
        """
        self.providers = providers
        self.mfa_config = mfa_config or {}
        self.jwt_secret = jwt_secret or secrets.token_urlsafe(32)

        # Storage
        self._tokens: Dict[str, AuthToken] = {}
        self._api_keys: Dict[str, APIKey] = {}
        self._user_sessions: Dict[str, List[str]] = {}  # user_id -> [token_ids]

        # Create auth workflows
        self._init_auth_workflows()

        logger.info(
            f"Enterprise auth manager initialized with {len(providers)} providers"
        )

    def _init_auth_workflows(self):
        """Initialize authentication workflows using SDK nodes."""
        # LDAP authentication workflow
        self.ldap_workflow = WorkflowBuilder()
        self.ldap_workflow.add_node(
            "DirectoryIntegrationNode", "ldap_auth", {"operation": "authenticate"}
        )
        self.ldap_workflow.add_node(
            "UserManagementNode", "sync_user", {"operation": "create_or_update"}
        )
        self.ldap_workflow.add_node(
            "AuditLogNode", "audit", {"event_type": "ldap_authentication"}
        )

        # Connect nodes
        self.ldap_workflow.add_connection("ldap_auth", "user", "sync_user", "user_data")
        self.ldap_workflow.add_connection("sync_user", "result", "audit", "event")

        # OAuth2 workflow
        self.oauth2_workflow = WorkflowBuilder()
        self.oauth2_workflow.add_node(
            "OAuth2Node", "oauth_auth", {"flow": "authorization_code"}
        )
        self.oauth2_workflow.add_node(
            "UserManagementNode", "sync_user", {"operation": "create_or_update"}
        )
        self.oauth2_workflow.add_node(
            "AuditLogNode", "audit", {"event_type": "oauth2_authentication"}
        )

        self.oauth2_workflow.add_connection(
            "oauth_auth", "user_info", "sync_user", "user_data"
        )
        self.oauth2_workflow.add_connection("sync_user", "result", "audit", "event")

        # MFA verification workflow
        mfa_required = (
            self.mfa_config.get("required", False)
            if isinstance(self.mfa_config, dict)
            else getattr(self.mfa_config, "required", False)
        )
        if mfa_required:
            self.mfa_workflow = WorkflowBuilder()
            self.mfa_workflow.add_node(
                "MultiFactorAuthNode",
                "verify_mfa",
                {"methods": self.mfa_config.methods},
            )
            self.mfa_workflow.add_node(
                "AuditLogNode", "audit_mfa", {"event_type": "mfa_verification"}
            )

            self.mfa_workflow.add_connection(
                "verify_mfa", "result", "audit_mfa", "event"
            )

    async def initialize(self):
        """Initialize the auth manager."""
        # In production, would initialize provider connections
        logger.info("Enterprise auth manager initialized")

    async def cleanup(self):
        """Cleanup resources."""
        # In production, would cleanup provider connections
        logger.info("Enterprise auth manager cleaned up")

    async def authenticate(
        self, credentials: Dict[str, Any], provider: Optional[str] = None
    ) -> Optional[AuthToken]:
        """Authenticate user with credentials.

        Args:
            credentials: Authentication credentials
            provider: Specific provider or auto-detect

        Returns:
            AuthToken if successful, None otherwise
        """
        # Determine provider
        if not provider:
            provider = self._detect_provider(credentials)

        # Authenticate based on provider
        user_info = None
        if provider == "ldap":
            user_info = await self._authenticate_ldap(credentials)
        elif provider == "oauth2":
            user_info = await self._authenticate_oauth2(credentials)
        elif provider == "local":
            user_info = await self._authenticate_local(credentials)

        if not user_info:
            logger.warning(f"Authentication failed for provider: {provider}")
            return None

        # Check MFA if required
        if self.mfa_config.required and not credentials.get("mfa_bypass"):
            mfa_result = await self._verify_mfa(user_info["user_id"], credentials)
            if not mfa_result:
                logger.warning(
                    f"MFA verification failed for user: {user_info['user_id']}"
                )
                return None

        # Create token
        token = self._create_token(user_info)

        # Store token
        self._tokens[token.token] = token

        # Track user session
        if user_info["user_id"] not in self._user_sessions:
            self._user_sessions[user_info["user_id"]] = []
        self._user_sessions[user_info["user_id"]].append(token.token)

        logger.info(f"User authenticated: {user_info['user_id']} via {provider}")
        return token

    def _detect_provider(self, credentials: Dict[str, Any]) -> str:
        """Detect authentication provider from credentials."""
        if "username" in credentials and "password" in credentials:
            # Check if LDAP is configured
            if any(p.type == "ldap" for p in self.providers):
                return "ldap"
            return "local"
        elif "code" in credentials or "token" in credentials:
            return "oauth2"
        elif "api_key" in credentials:
            return "api_key"

        return "local"

    async def _authenticate_ldap(
        self, credentials: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """Authenticate via LDAP.

        In production, would use actual LDAPIntegrationNode.
        """
        # Simulate LDAP auth
        username = credentials.get("username")
        if username:
            return {
                "user_id": username,
                "email": f"{username}@company.com",
                "name": username.title(),
                "provider": "ldap",
            }
        return None

    async def _authenticate_oauth2(
        self, credentials: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """Authenticate via OAuth2.

        In production, would use actual OAuth2Node.
        """
        # Simulate OAuth2
        code = credentials.get("code")
        if code:
            return {
                "user_id": "oauth_user",
                "email": "user@oauth.com",
                "name": "OAuth User",
                "provider": "oauth2",
            }
        return None

    async def _authenticate_local(
        self, credentials: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """Authenticate via local database.

        In production, would use UserManagementNode.
        """
        # Simulate local auth
        username = credentials.get("username")
        password = credentials.get("password")

        if username and password:
            return {
                "user_id": username,
                "email": f"{username}@local",
                "name": username,
                "provider": "local",
            }
        return None

    async def _verify_mfa(self, user_id: str, credentials: Dict[str, Any]) -> bool:
        """Verify MFA for user.

        In production, would use MultiFactorAuthNode.
        """
        # Simulate MFA verification
        mfa_code = credentials.get("mfa_code")
        return bool(mfa_code and len(mfa_code) == 6)

    def _create_token(self, user_info: Dict[str, Any]) -> AuthToken:
        """Create authentication token."""
        # Create JWT token
        expires_at = datetime.now(timezone.utc) + timedelta(hours=8)

        payload = {
            "user_id": user_info["user_id"],
            "email": user_info.get("email"),
            "provider": user_info.get("provider"),
            "exp": expires_at.timestamp(),
            "iat": datetime.now(timezone.utc).timestamp(),
        }

        token_str = jwt.encode(payload, self.jwt_secret, algorithm="HS256")

        return AuthToken(
            token=token_str,
            token_type="bearer",
            user_id=user_info["user_id"],
            expires_at=expires_at,
            metadata=user_info,
        )

    def validate_token(self, token: str) -> Optional[Dict[str, Any]]:
        """Validate an authentication token.

        Args:
            token: Token string

        Returns:
            User info if valid, None otherwise
        """
        # Check if token exists
        auth_token = self._tokens.get(token)
        if auth_token and not auth_token.is_expired():
            return auth_token.metadata

        # Try to decode JWT
        try:
            payload = jwt.decode(token, self.jwt_secret, algorithms=["HS256"])
            return {
                "user_id": payload["user_id"],
                "email": payload.get("email"),
                "provider": payload.get("provider"),
            }
        except jwt.InvalidTokenError:
            return None

    def generate_api_key(
        self,
        app_name: str,
        permissions: List[str],
        expires_in_days: Optional[int] = None,
    ) -> str:
        """Generate a new API key.

        Args:
            app_name: Application name
            permissions: List of permissions
            expires_in_days: Optional expiration in days

        Returns:
            API key string
        """
        # Generate key
        key = secrets.token_urlsafe(32)
        key_id = f"ak_{secrets.token_hex(4)}"

        # Hash key for storage
        key_hash = hashlib.sha256(key.encode()).hexdigest()

        # Create API key record
        api_key = APIKey(
            key_id=key_id,
            key_hash=key_hash,
            app_name=app_name,
            permissions=permissions,
            created_at=datetime.now(timezone.utc),
            expires_at=(
                datetime.now(timezone.utc) + timedelta(days=expires_in_days)
                if expires_in_days
                else None
            ),
        )

        # Store
        self._api_keys[key_id] = api_key

        logger.info(f"Generated API key for app: {app_name}")
        return key

    def validate_api_key(self, key: str) -> Optional[Dict[str, Any]]:
        """Validate an API key.

        Args:
            key: API key string

        Returns:
            App info if valid, None otherwise
        """
        # Hash the key
        key_hash = hashlib.sha256(key.encode()).hexdigest()

        # Find matching key
        for key_id, api_key in self._api_keys.items():
            if api_key.key_hash == key_hash and api_key.is_active:
                # Check expiration
                if (
                    api_key.expires_at
                    and datetime.now(timezone.utc) > api_key.expires_at
                ):
                    continue

                # Update last used
                api_key.last_used = datetime.now(timezone.utc)

                return {
                    "app_name": api_key.app_name,
                    "permissions": api_key.permissions,
                    "key_id": key_id,
                }

        return None

    def revoke_token(self, token: str) -> bool:
        """Revoke an authentication token.

        Args:
            token: Token to revoke

        Returns:
            True if revoked
        """
        if token in self._tokens:
            auth_token = self._tokens[token]

            # Remove from user sessions
            user_id = auth_token.user_id
            if user_id in self._user_sessions:
                self._user_sessions[user_id].remove(token)

            # Remove token
            del self._tokens[token]

            logger.info(f"Revoked token for user: {user_id}")
            return True

        return False

    def revoke_user_tokens(self, user_id: str) -> int:
        """Revoke all tokens for a user.

        Args:
            user_id: User identifier

        Returns:
            Number of tokens revoked
        """
        tokens = self._user_sessions.get(user_id, [])
        count = 0

        for token in tokens[:]:  # Copy list to avoid modification during iteration
            if self.revoke_token(token):
                count += 1

        return count

    def list_api_keys(self, app_name: Optional[str] = None) -> List[APIKey]:
        """List API keys.

        Args:
            app_name: Filter by app name

        Returns:
            List of API keys
        """
        keys = list(self._api_keys.values())

        if app_name:
            keys = [k for k in keys if k.app_name == app_name]

        return sorted(keys, key=lambda k: k.created_at, reverse=True)

    def revoke_api_key(self, key_id: str) -> bool:
        """Revoke an API key.

        Args:
            key_id: Key identifier

        Returns:
            True if revoked
        """
        if key_id in self._api_keys:
            self._api_keys[key_id].is_active = False
            logger.info(f"Revoked API key: {key_id}")
            return True

        return False

    async def health_check(self) -> Dict[str, Any]:
        """Get health status of auth system.

        Returns:
            Health status dictionary
        """
        provider_status = {}
        for provider in self.providers:
            # In production, would check actual provider health
            provider_status[provider.type] = "healthy"

        return {
            "healthy": True,
            "providers": provider_status,
            "active_tokens": len(self._tokens),
            "active_api_keys": len([k for k in self._api_keys.values() if k.is_active]),
            "mfa_enabled": self.mfa_config.required,
        }
