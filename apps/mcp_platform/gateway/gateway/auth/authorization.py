"""Authorization module for Enterprise Gateway."""

import fnmatch
from enum import Enum
from typing import Any, Dict, List, Optional, Set

import structlog
from fastapi import HTTPException

logger = structlog.get_logger(__name__)


class Permission(str, Enum):
    """System permissions."""

    # Tool permissions
    TOOLS_LIST = "tools:list"
    TOOLS_READ = "tools:read"
    TOOLS_EXECUTE = "tools:execute"

    # Admin permissions
    ADMIN_USERS_CREATE = "admin:users:create"
    ADMIN_USERS_READ = "admin:users:read"
    ADMIN_USERS_UPDATE = "admin:users:update"
    ADMIN_USERS_DELETE = "admin:users:delete"

    ADMIN_TENANTS_CREATE = "admin:tenants:create"
    ADMIN_TENANTS_READ = "admin:tenants:read"
    ADMIN_TENANTS_UPDATE = "admin:tenants:update"
    ADMIN_TENANTS_DELETE = "admin:tenants:delete"

    ADMIN_USAGE_READ = "admin:usage:read"
    ADMIN_BILLING_READ = "admin:billing:read"
    ADMIN_BILLING_UPDATE = "admin:billing:update"

    # Wildcard
    ALL = "*"


class Role:
    """Role definition."""

    def __init__(self, name: str, permissions: List[str], description: str = ""):
        self.name = name
        self.permissions = set(permissions)
        self.description = description

    def has_permission(self, permission: str) -> bool:
        """Check if role has a specific permission."""
        # Check exact match
        if permission in self.permissions:
            return True

        # Check wildcard permissions
        for perm in self.permissions:
            if fnmatch.fnmatch(permission, perm):
                return True

        return False


# Default roles
DEFAULT_ROLES = {
    "admin": Role("admin", ["*"], "Full system administrator"),
    "developer": Role(
        "developer", ["tools:*", "admin:usage:read"], "Developer with tool access"
    ),
    "operator": Role(
        "operator",
        [
            "tools:list",
            "tools:read",
            "tools:execute",
            "admin:tenants:read",
            "admin:usage:read",
        ],
        "System operator",
    ),
    "viewer": Role(
        "viewer", ["tools:list", "tools:read", "admin:usage:read"], "Read-only access"
    ),
    "billing_admin": Role(
        "billing_admin",
        ["admin:billing:*", "admin:usage:read", "admin:tenants:read"],
        "Billing administrator",
    ),
}


class AuthorizationMiddleware:
    """Handles authorization for the gateway."""

    def __init__(self):
        self.roles = DEFAULT_ROLES.copy()
        self.resource_policies = {}
        self.tenant_policies = {}

    def add_role(self, role: Role):
        """Add a custom role."""
        self.roles[role.name] = role

    def check_permission(self, user: Dict[str, Any], permission: str) -> bool:
        """Check if user has permission."""
        # Super admin bypass
        if user.get("is_superadmin"):
            return True

        # Get user roles
        user_roles = user.get("roles", [])

        # Check each role
        for role_name in user_roles:
            if role_name in self.roles:
                role = self.roles[role_name]
                if role.has_permission(permission):
                    return True

        # Check direct permissions
        user_permissions = user.get("permissions", [])
        for perm in user_permissions:
            if fnmatch.fnmatch(permission, perm):
                return True

        return False

    def check_resource_access(
        self, user: Dict[str, Any], resource_type: str, resource_id: str, action: str
    ) -> bool:
        """Check if user can access a specific resource."""
        # Check general permission first
        general_permission = f"{resource_type}:{action}"
        if not self.check_permission(user, general_permission):
            return False

        # Check resource-specific policies
        policy_key = f"{resource_type}:{resource_id}"
        if policy_key in self.resource_policies:
            policy = self.resource_policies[policy_key]
            return self._evaluate_policy(user, policy, action)

        return True

    def check_tenant_access(
        self, user: Dict[str, Any], tenant_id: str, action: str = "read"
    ) -> bool:
        """Check if user can access a tenant's resources."""
        # User's own tenant
        if user.get("tenant_id") == tenant_id:
            return True

        # Cross-tenant access
        if self.check_permission(user, f"admin:tenants:{action}"):
            return True

        # Check tenant-specific policies
        if tenant_id in self.tenant_policies:
            policy = self.tenant_policies[tenant_id]
            return self._evaluate_policy(user, policy, action)

        return False

    def _evaluate_policy(
        self, user: Dict[str, Any], policy: Dict[str, Any], action: str
    ) -> bool:
        """Evaluate a resource policy."""
        # Check allowed users
        if "allowed_users" in policy:
            if user["user_id"] not in policy["allowed_users"]:
                return False

        # Check allowed roles
        if "allowed_roles" in policy:
            user_roles = set(user.get("roles", []))
            allowed_roles = set(policy["allowed_roles"])
            if not user_roles.intersection(allowed_roles):
                return False

        # Check allowed actions
        if "allowed_actions" in policy:
            if action not in policy["allowed_actions"]:
                return False

        # Check conditions
        if "conditions" in policy:
            for condition in policy["conditions"]:
                if not self._evaluate_condition(user, condition):
                    return False

        return True

    def _evaluate_condition(
        self, user: Dict[str, Any], condition: Dict[str, Any]
    ) -> bool:
        """Evaluate a policy condition."""
        condition_type = condition.get("type")

        if condition_type == "time_range":
            # Check if current time is within allowed range
            from datetime import datetime, time

            now = datetime.utcnow().time()

            start_time = time.fromisoformat(condition["start"])
            end_time = time.fromisoformat(condition["end"])

            if start_time <= end_time:
                return start_time <= now <= end_time
            else:
                # Crosses midnight
                return now >= start_time or now <= end_time

        elif condition_type == "ip_range":
            # Check if user's IP is in allowed range
            user_ip = user.get("ip_address")
            if not user_ip:
                return False

            # Implement IP range checking
            # This is a simplified example
            allowed_ips = condition.get("allowed_ips", [])
            return user_ip in allowed_ips

        elif condition_type == "attribute":
            # Check user attribute
            attribute = condition.get("attribute")
            expected_value = condition.get("value")
            operator = condition.get("operator", "equals")

            actual_value = user.get(attribute)

            if operator == "equals":
                return actual_value == expected_value
            elif operator == "contains":
                return expected_value in actual_value
            elif operator == "gt":
                return actual_value > expected_value
            elif operator == "lt":
                return actual_value < expected_value

        return True


# Dependency for checking permissions
async def check_permission(user: Dict[str, Any], permission: str) -> bool:
    """Check if user has permission."""
    auth_middleware = AuthorizationMiddleware()
    return auth_middleware.check_permission(user, permission)


async def require_permission(user: Dict[str, Any], permission: str):
    """Require user to have permission or raise exception."""
    if not await check_permission(user, permission):
        raise HTTPException(status_code=403, detail=f"Permission denied: {permission}")


# RBAC (Role-Based Access Control) implementation
class RBACManager:
    """Manages role-based access control."""

    def __init__(self):
        self.roles = DEFAULT_ROLES.copy()
        self.role_hierarchy = {
            "admin": ["developer", "operator", "viewer"],
            "developer": ["operator", "viewer"],
            "operator": ["viewer"],
        }

    def get_effective_permissions(self, roles: List[str]) -> Set[str]:
        """Get all effective permissions for a set of roles."""
        permissions = set()

        # Process each role
        for role_name in roles:
            if role_name in self.roles:
                role = self.roles[role_name]
                permissions.update(role.permissions)

                # Add inherited permissions
                if role_name in self.role_hierarchy:
                    for inherited_role in self.role_hierarchy[role_name]:
                        if inherited_role in self.roles:
                            permissions.update(self.roles[inherited_role].permissions)

        return permissions

    def create_custom_role(
        self,
        name: str,
        permissions: List[str],
        inherits_from: Optional[List[str]] = None,
    ) -> Role:
        """Create a custom role."""
        # Start with direct permissions
        all_permissions = set(permissions)

        # Add inherited permissions
        if inherits_from:
            for parent_role in inherits_from:
                if parent_role in self.roles:
                    all_permissions.update(self.roles[parent_role].permissions)

        role = Role(name, list(all_permissions))
        self.roles[name] = role

        return role


# ABAC (Attribute-Based Access Control) implementation
class ABACPolicy:
    """Attribute-based access control policy."""

    def __init__(self, name: str, resource: str, action: str):
        self.name = name
        self.resource = resource
        self.action = action
        self.rules = []

    def add_rule(self, attribute: str, operator: str, value: Any):
        """Add a rule to the policy."""
        self.rules.append(
            {"attribute": attribute, "operator": operator, "value": value}
        )

    def evaluate(self, subject: Dict[str, Any], resource: Dict[str, Any]) -> bool:
        """Evaluate the policy."""
        for rule in self.rules:
            attribute = rule["attribute"]
            operator = rule["operator"]
            expected_value = rule["value"]

            # Get actual value from subject or resource
            if attribute.startswith("subject."):
                actual_value = subject.get(attribute[8:])
            elif attribute.startswith("resource."):
                actual_value = resource.get(attribute[9:])
            else:
                actual_value = None

            # Evaluate rule
            if not self._evaluate_rule(actual_value, operator, expected_value):
                return False

        return True

    def _evaluate_rule(self, actual: Any, operator: str, expected: Any) -> bool:
        """Evaluate a single rule."""
        if operator == "equals":
            return actual == expected
        elif operator == "not_equals":
            return actual != expected
        elif operator == "contains":
            return expected in actual
        elif operator == "not_contains":
            return expected not in actual
        elif operator == "gt":
            return actual > expected
        elif operator == "gte":
            return actual >= expected
        elif operator == "lt":
            return actual < expected
        elif operator == "lte":
            return actual <= expected
        elif operator == "in":
            return actual in expected
        elif operator == "not_in":
            return actual not in expected
        elif operator == "matches":
            import re

            return bool(re.match(expected, str(actual)))

        return False


class ABACManager:
    """Manages attribute-based access control."""

    def __init__(self):
        self.policies = {}

    def add_policy(self, policy: ABACPolicy):
        """Add a policy."""
        key = f"{policy.resource}:{policy.action}"
        if key not in self.policies:
            self.policies[key] = []
        self.policies[key].append(policy)

    def check_access(
        self, subject: Dict[str, Any], resource: Dict[str, Any], action: str
    ) -> bool:
        """Check if subject can perform action on resource."""
        key = f"{resource.get('type', 'unknown')}:{action}"

        if key not in self.policies:
            # No policies defined, check RBAC
            return True

        # Evaluate all policies
        for policy in self.policies[key]:
            if policy.evaluate(subject, resource):
                return True

        return False
