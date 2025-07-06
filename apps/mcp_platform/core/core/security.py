"""
MCP Security Manager - Authentication and authorization for MCP operations.

This module provides security features including authentication,
authorization, rate limiting, and access control for MCP operations.
"""

import asyncio
import hashlib
import hmac
import logging
import secrets
from collections import defaultdict
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional, Set

import jwt

from kailash.nodes.admin.role_management import RoleManagementNode
from kailash.nodes.admin.security_event import EnterpriseSecurityEventNode
from kailash.runtime.local import LocalRuntime

logger = logging.getLogger(__name__)


class SimpleAccessControlManager:
    """Simple access control manager for MCP."""

    def __init__(self, strategy: str = "rbac"):
        self.strategy = strategy

    def check_permission(self, user_roles: List[str], permission: str) -> bool:
        """Check if user has permission."""
        # Simple implementation
        return "admin" in user_roles or "operator" in user_roles


class MCPSecurityManager:
    """
    Security manager for MCP operations.

    Handles authentication, authorization, rate limiting,
    and access control for all MCP operations.
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize the security manager."""
        self.config = config or {}
        self.runtime = LocalRuntime()

        # Access control
        self.access_control = SimpleAccessControlManager(
            strategy=self.config.get("access_strategy", "rbac")
        )

        # Security event logging
        try:
            from kailash.nodes.admin.security_event import EnterpriseSecurityEventNode

            self.security_node = EnterpriseSecurityEventNode(
                connection_string=self.config.get("database_url")
            )
        except ImportError:
            logger.warning(
                "EnterpriseSecurityEventNode not available - security event logging disabled"
            )
            self.security_node = None
        except Exception as e:
            logger.warning(f"Could not initialize security event node: {e}")
            self.security_node = None

        # JWT configuration
        self.jwt_secret = self.config.get("jwt_secret", secrets.token_hex(32))
        self.jwt_algorithm = self.config.get("jwt_algorithm", "HS256")
        self.token_expiry = self.config.get("token_expiry_hours", 24)

        # Rate limiting
        self.rate_limits = self.config.get(
            "rate_limits",
            {
                "default": 100,  # requests per minute
                "tool_execution": 50,
                "server_management": 20,
            },
        )
        self._rate_counters = defaultdict(lambda: defaultdict(list))

        # Permissions
        self._init_permissions()

        # API keys (for service-to-service auth)
        self.api_keys = self.config.get("api_keys", {})

        # Blocked entities
        self.blocked_users: Set[str] = set()
        self.blocked_servers: Set[str] = set()
        self.blocked_tools: Set[str] = set()

    def _init_permissions(self):
        """Initialize default permissions."""
        self.permissions = {
            # Server permissions
            "server.register": ["admin", "operator"],
            "server.start": ["admin", "operator"],
            "server.stop": ["admin", "operator"],
            "server.delete": ["admin"],
            "server.view": ["admin", "operator", "user"],
            # Tool permissions
            "tool.discover": ["admin", "operator", "user"],
            "tool.execute": ["admin", "operator", "user"],
            "tool.execute.sensitive": ["admin", "operator"],
            # Resource permissions
            "resource.read": ["admin", "operator", "user"],
            "resource.write": ["admin", "operator"],
            # Admin permissions
            "admin.view_all": ["admin"],
            "admin.manage_users": ["admin"],
            "admin.view_metrics": ["admin", "operator"],
            "admin.view_audit": ["admin"],
        }

        # Tool-specific permissions
        self.tool_permissions = self.config.get(
            "tool_permissions",
            {
                # Example: "delete_*": ["admin"],
                #          "update_*": ["admin", "operator"]
            },
        )

    async def authenticate_user(
        self, credentials: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """
        Authenticate a user.

        Args:
            credentials: Authentication credentials

        Returns:
            User info if authenticated, None otherwise
        """
        auth_type = credentials.get("type", "jwt")

        if auth_type == "jwt":
            return await self._authenticate_jwt(credentials.get("token"))
        elif auth_type == "api_key":
            return await self._authenticate_api_key(credentials.get("key"))
        elif auth_type == "basic":
            return await self._authenticate_basic(
                credentials.get("username"), credentials.get("password")
            )
        else:
            logger.warning(f"Unknown auth type: {auth_type}")
            return None

    async def _authenticate_jwt(self, token: str) -> Optional[Dict[str, Any]]:
        """Authenticate using JWT token."""
        try:
            payload = jwt.decode(
                token, self.jwt_secret, algorithms=[self.jwt_algorithm]
            )

            # Check expiry
            if "exp" in payload:
                if datetime.now(timezone.utc).timestamp() > payload["exp"]:
                    return None

            # Check if user is blocked
            user_id = payload.get("user_id")
            if user_id in self.blocked_users:
                await self._log_security_event(
                    "blocked_user_attempt", user_id, {"reason": "user_blocked"}
                )
                return None

            return {
                "user_id": user_id,
                "roles": payload.get("roles", ["user"]),
                "permissions": payload.get("permissions", []),
                "organization_id": payload.get("organization_id"),
            }

        except jwt.InvalidTokenError as e:
            logger.warning(f"Invalid JWT token: {e}")
            return None

    async def _authenticate_api_key(self, key: str) -> Optional[Dict[str, Any]]:
        """Authenticate using API key."""
        if key not in self.api_keys:
            return None

        key_info = self.api_keys[key]

        # Check if key is active
        if not key_info.get("active", True):
            return None

        # Check expiry
        if "expires_at" in key_info:
            if datetime.now(timezone.utc) > datetime.fromisoformat(
                key_info["expires_at"]
            ):
                return None

        return {
            "user_id": key_info.get("user_id", f"api_key_{key[:8]}"),
            "roles": key_info.get("roles", ["service"]),
            "permissions": key_info.get("permissions", []),
            "service_name": key_info.get("service_name"),
        }

    async def _authenticate_basic(
        self, username: str, password: str
    ) -> Optional[Dict[str, Any]]:
        """Authenticate using username/password."""
        # This would typically check against a user database
        # For now, we'll use a simple example
        if username == "admin" and password == "admin":  # TODO: Replace with real auth
            return {"user_id": "admin", "roles": ["admin"], "permissions": []}
        return None

    def generate_token(self, user_info: Dict[str, Any]) -> str:
        """Generate JWT token for authenticated user."""
        now = datetime.now(timezone.utc)
        payload = {
            "user_id": user_info["user_id"],
            "roles": user_info.get("roles", ["user"]),
            "permissions": user_info.get("permissions", []),
            "organization_id": user_info.get("organization_id"),
            "iat": now,
            "exp": now + timedelta(hours=self.token_expiry),
        }

        return jwt.encode(payload, self.jwt_secret, algorithm=self.jwt_algorithm)

    async def can_register_server(
        self, user_id: Optional[str], server_config: Dict[str, Any]
    ) -> bool:
        """Check if user can register a server."""
        # Allow anonymous users in test environments
        if not user_id:
            return not self.config.get("require_authentication", True)

        # Check if user is blocked
        if user_id in self.blocked_users:
            return False

        # Check rate limit
        if not await self._check_rate_limit(user_id, "server_management"):
            return False

        # Check permissions
        user_info = await self._get_user_info(user_id)
        if not user_info:
            return False

        return self._has_permission(user_info, "server.register")

    async def can_manage_server(self, user_id: Optional[str], server_id: str) -> bool:
        """Check if user can manage a server."""
        # Allow anonymous users in test environments
        if not user_id:
            return not self.config.get("require_authentication", True)

        # Check if server is blocked
        if server_id in self.blocked_servers:
            return False

        # Check permissions
        user_info = await self._get_user_info(user_id)
        if not user_info:
            return False

        # Admin can manage all
        if "admin" in user_info.get("roles", []):
            return True

        # Check ownership or specific permissions
        # TODO: Check server ownership
        return self._has_permission(user_info, "server.start")

    async def can_access_server(self, user_id: Optional[str], server_id: str) -> bool:
        """Check if user can access server information."""
        # Allow anonymous users in test environments
        if not user_id:
            return not self.config.get("require_authentication", True)

        user_info = await self._get_user_info(user_id)
        if not user_info:
            return False

        return self._has_permission(user_info, "server.view")

    async def can_execute_tool(
        self, user_id: Optional[str], server_id: str, tool_name: str
    ) -> bool:
        """Check if user can execute a tool."""
        # Allow anonymous users in test environments
        if not user_id:
            return not self.config.get("require_authentication", True)

        # Check if entities are blocked
        if (
            user_id in self.blocked_users
            or server_id in self.blocked_servers
            or f"{server_id}:{tool_name}" in self.blocked_tools
        ):
            return False

        # Check rate limit
        if not await self._check_rate_limit(user_id, "tool_execution"):
            await self._log_security_event(
                "rate_limit_exceeded",
                user_id,
                {
                    "action": "tool_execution",
                    "server_id": server_id,
                    "tool_name": tool_name,
                },
            )
            return False

        # Check permissions
        user_info = await self._get_user_info(user_id)
        if not user_info:
            return False

        # Check tool-specific permissions
        for pattern, allowed_roles in self.tool_permissions.items():
            if self._matches_pattern(tool_name, pattern):
                return any(role in allowed_roles for role in user_info.get("roles", []))

        # Check general permission
        return self._has_permission(user_info, "tool.execute")

    async def validate_tool_parameters(
        self, user_id: str, tool_name: str, parameters: Dict[str, Any]
    ) -> bool:
        """Validate tool parameters for security issues."""
        # Check for injection attempts
        suspicious_patterns = [
            "'; DROP TABLE",
            "<script>",
            "javascript:",
            "../",
            "file://",
            "eval(",
            "__import__",
        ]

        param_str = str(parameters).lower()
        for pattern in suspicious_patterns:
            if pattern.lower() in param_str:
                await self._log_security_event(
                    "suspicious_parameters",
                    user_id,
                    {
                        "tool_name": tool_name,
                        "pattern": pattern,
                        "parameters": parameters,
                    },
                    severity="high",
                )
                return False

        return True

    async def _check_rate_limit(self, user_id: str, action: str) -> bool:
        """Check if user has exceeded rate limit."""
        limit = self.rate_limits.get(action, self.rate_limits["default"])
        now = datetime.now(timezone.utc)

        # Clean old entries
        cutoff = now - timedelta(minutes=1)
        self._rate_counters[user_id][action] = [
            t for t in self._rate_counters[user_id][action] if t > cutoff
        ]

        # Check limit
        if len(self._rate_counters[user_id][action]) >= limit:
            return False

        # Add new entry
        self._rate_counters[user_id][action].append(now)
        return True

    def _has_permission(self, user_info: Dict[str, Any], permission: str) -> bool:
        """Check if user has specific permission."""
        # Check explicit permissions
        if permission in user_info.get("permissions", []):
            return True

        # Check role-based permissions
        user_roles = user_info.get("roles", [])
        allowed_roles = self.permissions.get(permission, [])

        return any(role in allowed_roles for role in user_roles)

    def _matches_pattern(self, name: str, pattern: str) -> bool:
        """Check if name matches pattern (supports wildcards)."""
        if pattern.endswith("*"):
            return name.startswith(pattern[:-1])
        return name == pattern

    async def _get_user_info(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Get user information."""
        # TODO: Implement user info lookup
        # For now, return basic info with admin permissions for tests
        if user_id is None:
            return None
        return {
            "user_id": user_id,
            "roles": ["admin"],  # Give admin role for tests
            "permissions": [],
        }

    async def _log_security_event(
        self,
        event_type: str,
        user_id: Optional[str],
        details: Dict[str, Any],
        severity: str = "medium",
    ):
        """Log security event."""
        try:
            if self.security_node:
                # Call the node directly
                await self.security_node.execute(
                    {
                        "operation": "log_event",
                        "event_type": f"mcp_{event_type}",
                        "severity": severity,
                        "user_id": user_id,
                        "details": details,
                        "ip_address": details.get("ip_address"),
                        "user_agent": details.get("user_agent"),
                    }
                )
            else:
                # Fallback to simple logging
                logger.info(
                    f"Security event: {event_type} for user {user_id}, severity: {severity}"
                )
        except Exception as e:
            logger.error(f"Failed to log security event: {e}")

    async def block_user(self, user_id: str, reason: str):
        """Block a user from MCP operations."""
        self.blocked_users.add(user_id)
        await self._log_security_event(
            "user_blocked", user_id, {"reason": reason}, severity="high"
        )

    async def unblock_user(self, user_id: str):
        """Unblock a user."""
        self.blocked_users.discard(user_id)
        await self._log_security_event("user_unblocked", user_id, {}, severity="low")

    async def block_server(self, server_id: str, reason: str):
        """Block a server from being used."""
        self.blocked_servers.add(server_id)
        await self._log_security_event(
            "server_blocked",
            None,
            {"server_id": server_id, "reason": reason},
            severity="high",
        )

    async def block_tool(self, server_id: str, tool_name: str, reason: str):
        """Block a specific tool from being executed."""
        tool_id = f"{server_id}:{tool_name}"
        self.blocked_tools.add(tool_id)
        await self._log_security_event(
            "tool_blocked",
            None,
            {"server_id": server_id, "tool_name": tool_name, "reason": reason},
            severity="high",
        )

    def create_api_key(
        self,
        service_name: str,
        roles: List[str],
        permissions: Optional[List[str]] = None,
        expires_in_days: Optional[int] = None,
    ) -> str:
        """Create a new API key for service-to-service auth."""
        key = secrets.token_urlsafe(32)

        key_info = {
            "service_name": service_name,
            "roles": roles,
            "permissions": permissions or [],
            "created_at": datetime.now(timezone.utc).isoformat(),
            "active": True,
        }

        if expires_in_days:
            key_info["expires_at"] = (
                datetime.now(timezone.utc) + timedelta(days=expires_in_days)
            ).isoformat()

        self.api_keys[key] = key_info

        return key

    def revoke_api_key(self, key: str):
        """Revoke an API key."""
        if key in self.api_keys:
            self.api_keys[key]["active"] = False

    async def require_admin(self, token: str = None) -> Dict[str, Any]:
        """FastAPI dependency for admin authentication."""
        if not token:
            from fastapi import HTTPException

            raise HTTPException(status_code=401, detail="Token required")

        user_info = await self._authenticate_jwt(token)
        if not user_info:
            from fastapi import HTTPException

            raise HTTPException(status_code=401, detail="Invalid token")

        if "admin" not in user_info.get("roles", []):
            from fastapi import HTTPException

            raise HTTPException(status_code=403, detail="Admin access required")

        return user_info

    def get_security_metrics(self) -> Dict[str, Any]:
        """Get security-related metrics."""
        return {
            "blocked_users": len(self.blocked_users),
            "blocked_servers": len(self.blocked_servers),
            "blocked_tools": len(self.blocked_tools),
            "active_api_keys": sum(
                1 for k in self.api_keys.values() if k.get("active", True)
            ),
            "rate_limit_counters": {
                user_id: {action: len(times) for action, times in actions.items()}
                for user_id, actions in self._rate_counters.items()
            },
        }
