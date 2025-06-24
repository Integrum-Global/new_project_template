"""
Authentication and Authorization Middleware using Kailash SDK
"""

from datetime import datetime
from functools import wraps
from typing import Any, Callable, Dict, Optional

import jwt
from fastapi import Depends, HTTPException, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from apps.user_management.config.settings import UserManagementConfig
from kailash.runtime.local import LocalRuntime
from kailash.workflow.builder import WorkflowBuilder


class AuthMiddleware:
    """Authentication middleware for API endpoints"""

    def __init__(self):
        self.config = UserManagementConfig()
        self.runtime = LocalRuntime()
        self.security = HTTPBearer()

    async def verify_token(
        self, credentials: HTTPAuthorizationCredentials = Depends(HTTPBearer())
    ):
        """Verify JWT token from request"""
        token = credentials.credentials

        try:
            # Decode token
            payload = jwt.decode(
                token,
                self.config.JWT_SECRET_KEY,
                algorithms=[self.config.JWT_ALGORITHM],
            )

            # Check expiration
            if datetime.utcnow().timestamp() > payload.get("exp", 0):
                raise HTTPException(status_code=401, detail="Token expired")

            return payload

        except jwt.InvalidTokenError:
            raise HTTPException(status_code=401, detail="Invalid token")

    async def get_current_user(self, token_payload: Dict = Depends(verify_token)):
        """Get current user from token"""
        user_id = token_payload.get("user_id")
        if not user_id:
            raise HTTPException(status_code=401, detail="Invalid token payload")

        # Get user details
        user_node = WorkflowBuilder.create_node(
            "UserManagementNode", self.config.NODE_CONFIGS["UserManagementNode"]
        )

        result = await self.runtime.execute_node_async(
            user_node, {"operation": "get_user", "user_id": user_id}
        )

        if not result.get("user"):
            raise HTTPException(status_code=404, detail="User not found")

        return result["user"]

    def require_auth(self):
        """Decorator to require authentication"""

        def decorator(func):
            @wraps(func)
            async def wrapper(*args, **kwargs):
                # The FastAPI dependency injection will handle auth
                return await func(*args, **kwargs)

            return wrapper

        return decorator


class PermissionMiddleware:
    """Permission checking middleware"""

    def __init__(self):
        self.config = UserManagementConfig()
        self.runtime = LocalRuntime()

    def require_permission(self, resource: str, action: str):
        """Decorator to check permissions"""

        async def permission_dependency(
            current_user: Dict = Depends(AuthMiddleware().get_current_user),
            request: Request = None,
        ):
            # Build permission check workflow
            workflow = WorkflowBuilder("permission_check")
            workflow.add_node(
                "checker",
                "PermissionCheckNode",
                self.config.NODE_CONFIGS["PermissionCheckNode"],
            )

            # Get resource attributes from request if needed
            resource_attrs = {}
            if request and hasattr(request.state, "resource_attrs"):
                resource_attrs = request.state.resource_attrs

            # Check permission
            result = await self.runtime.execute_async(
                workflow,
                {
                    "user_id": current_user["id"],
                    "resource": resource,
                    "action": action,
                    "resource_attributes": resource_attrs,
                },
            )

            if not result.get("allowed"):
                raise HTTPException(
                    status_code=403, detail=f"Permission denied: {resource}:{action}"
                )

            return current_user

        return permission_dependency

    def require_role(self, role_name: str):
        """Decorator to require specific role"""

        async def role_dependency(
            current_user: Dict = Depends(AuthMiddleware().get_current_user),
        ):
            # Get user roles
            user_node = WorkflowBuilder.create_node(
                "UserManagementNode", self.config.NODE_CONFIGS["UserManagementNode"]
            )

            result = await self.runtime.execute_node_async(
                user_node,
                {"operation": "get_user_roles", "user_id": current_user["id"]},
            )

            user_roles = [r["name"] for r in result.get("roles", [])]

            if role_name not in user_roles:
                raise HTTPException(
                    status_code=403, detail=f"Role required: {role_name}"
                )

            return current_user

        return role_dependency

    def require_any_role(self, roles: list):
        """Decorator to require any of the specified roles"""

        async def role_dependency(
            current_user: Dict = Depends(AuthMiddleware().get_current_user),
        ):
            # Get user roles
            user_node = WorkflowBuilder.create_node(
                "UserManagementNode", self.config.NODE_CONFIGS["UserManagementNode"]
            )

            result = await self.runtime.execute_node_async(
                user_node,
                {"operation": "get_user_roles", "user_id": current_user["id"]},
            )

            user_roles = [r["name"] for r in result.get("roles", [])]

            if not any(role in user_roles for role in roles):
                raise HTTPException(
                    status_code=403,
                    detail=f"One of these roles required: {', '.join(roles)}",
                )

            return current_user

        return role_dependency


class RateLimitMiddleware:
    """Rate limiting middleware"""

    def __init__(self):
        self.config = UserManagementConfig()
        self.runtime = LocalRuntime()
        # In production, use Redis for distributed rate limiting
        self.request_counts = {}

    def rate_limit(self, requests_per_hour: int = None):
        """Decorator for rate limiting"""
        limit = requests_per_hour or self.config.API_RATE_LIMIT

        async def rate_limit_dependency(
            request: Request,
            current_user: Optional[Dict] = Depends(AuthMiddleware().get_current_user),
        ):
            # Get identifier (user ID or IP)
            identifier = current_user["id"] if current_user else request.client.host

            # Check rate limit
            now = datetime.utcnow()
            hour_ago = now.timestamp() - 3600

            # Get request history
            history = self.request_counts.get(identifier, [])

            # Remove old entries
            history = [ts for ts in history if ts > hour_ago]

            # Check limit
            if len(history) >= limit:
                raise HTTPException(
                    status_code=429,
                    detail=f"Rate limit exceeded: {limit} requests per hour",
                )

            # Add current request
            history.append(now.timestamp())
            self.request_counts[identifier] = history

            return current_user

        return rate_limit_dependency


class SessionMiddleware:
    """Session management middleware"""

    def __init__(self):
        self.config = UserManagementConfig()
        self.runtime = LocalRuntime()

    async def validate_session(
        self,
        request: Request,
        current_user: Dict = Depends(AuthMiddleware().get_current_user),
    ):
        """Validate and update session"""
        # Get session ID from token or header
        auth_header = request.headers.get("Authorization", "")
        if auth_header.startswith("Bearer "):
            token = auth_header.split(" ")[1]

            try:
                payload = jwt.decode(
                    token,
                    self.config.JWT_SECRET_KEY,
                    algorithms=[self.config.JWT_ALGORITHM],
                )
                session_id = payload.get("session_id")

                # Create session validation workflow
                workflow = WorkflowBuilder("session_validation")
                workflow.add_node("validator", "PythonCodeNode")

                validator_code = f"""
from datetime import datetime, timedelta

session_id = "{session_id}"
user_id = "{current_user['id']}"
now = datetime.utcnow()

# In production, check session in Redis/database
# For now, we'll validate based on token data
session_valid = True
session_data = {{
    "id": session_id,
    "user_id": user_id,
    "last_activity": now.isoformat(),
    "expires_at": (now + timedelta(minutes=30)).isoformat()
}}

result = {{
    "valid": session_valid,
    "session": session_data
}}
"""
                workflow.update_node("validator", {"code": validator_code})

                result = await self.runtime.execute_async(workflow, {})

                if not result.get("valid"):
                    raise HTTPException(status_code=401, detail="Invalid session")

                # Update request with session data
                request.state.session = result["session"]

            except Exception:
                pass

        return current_user


class AuditMiddleware:
    """Audit logging middleware"""

    def __init__(self):
        self.config = UserManagementConfig()
        self.runtime = LocalRuntime()

    async def log_request(self, request: Request, current_user: Optional[Dict] = None):
        """Log API request for audit"""
        audit_node = WorkflowBuilder.create_node(
            "EnterpriseAuditLogNode", self.config.NODE_CONFIGS["EnterpriseAuditLogNode"]
        )

        # Prepare audit data
        audit_data = {
            "operation": "log_event",
            "event_type": "api_request",
            "severity": "low",
            "details": {
                "method": request.method,
                "path": request.url.path,
                "user_id": current_user["id"] if current_user else None,
                "ip_address": request.client.host,
                "user_agent": request.headers.get("User-Agent"),
                "timestamp": datetime.utcnow().isoformat(),
            },
        }

        # Log asynchronously
        await self.runtime.execute_node_async(audit_node, audit_data)
