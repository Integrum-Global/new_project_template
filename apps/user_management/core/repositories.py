"""
Repository Layer with AsyncSQLDatabaseNode

This module implements the repository pattern using AsyncSQLDatabaseNode.
Provides data access abstraction with connection pooling and optimization.
"""

import json
import uuid
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from apps.user_management.config import settings
from kailash.nodes.data import AsyncSQLDatabaseNode
from kailash.runtime.local import LocalRuntime
from kailash.workflow import WorkflowBuilder


class BaseRepository:
    """Base repository with common database operations."""

    def __init__(self):
        self.db_node = AsyncSQLDatabaseNode(
            name="repository_db",
            connection_string=settings.DATABASE_URL,
            pool_size=settings.DATABASE_POOL_SIZE,
            max_overflow=settings.DATABASE_MAX_OVERFLOW,
            echo=False,
        )
        self.runtime = LocalRuntime(enable_async=True)

    async def execute_query(
        self, query: str, params: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """Execute a query and return results."""
        workflow = WorkflowBuilder("query_workflow")
        workflow.add_node(
            "AsyncSQLDatabaseNode",
            "db_query",
            {"name": "query_executor", "connection_string": settings.DATABASE_URL},
        )

        built_workflow = workflow.build()
        results, _ = await self.runtime.execute(
            built_workflow, parameters={"query": query, "params": params or {}}
        )

        return results.get("db_query", {}).get("results", [])

    async def execute_command(
        self, command: str, params: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Execute a command (INSERT, UPDATE, DELETE) and return result."""
        workflow = WorkflowBuilder("command_workflow")
        workflow.add_node(
            "AsyncSQLDatabaseNode",
            "db_command",
            {"name": "command_executor", "connection_string": settings.DATABASE_URL},
        )

        built_workflow = workflow.build()
        results, _ = await self.runtime.execute(
            built_workflow, parameters={"query": command, "params": params or {}}
        )

        return results.get("db_command", {}).get("result", {})


class UserRepository(BaseRepository):
    """Repository for user data operations."""

    async def create_user(self, user_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new user."""
        user_id = str(uuid.uuid4())
        now = datetime.now()

        query = """
        INSERT INTO users (
            id, email, first_name, last_name, department, title, phone,
            is_active, sso_enabled, mfa_enabled, created_at, updated_at
        ) VALUES (
            :id, :email, :first_name, :last_name, :department, :title, :phone,
            :is_active, :sso_enabled, :mfa_enabled, :created_at, :updated_at
        ) RETURNING *
        """

        params = {
            "id": user_id,
            "email": user_data["email"],
            "first_name": user_data["first_name"],
            "last_name": user_data["last_name"],
            "department": user_data.get("department"),
            "title": user_data.get("title"),
            "phone": user_data.get("phone"),
            "is_active": True,
            "sso_enabled": user_data.get("enable_sso", True),
            "mfa_enabled": user_data.get("enable_mfa", True),
            "created_at": now,
            "updated_at": now,
        }

        result = await self.execute_command(query, params)
        return result.get("row", {})

    async def get_user(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Get user by ID."""
        query = "SELECT * FROM users WHERE id = :user_id"
        results = await self.execute_query(query, {"user_id": user_id})
        return results[0] if results else None

    async def get_user_by_email(self, email: str) -> Optional[Dict[str, Any]]:
        """Get user by email."""
        query = "SELECT * FROM users WHERE email = :email"
        results = await self.execute_query(query, {"email": email})
        return results[0] if results else None

    async def list_users(
        self,
        offset: int = 0,
        limit: int = 50,
        search: Optional[str] = None,
        department: Optional[str] = None,
        is_active: Optional[bool] = None,
    ) -> List[Dict[str, Any]]:
        """List users with filtering and pagination."""
        query = "SELECT * FROM users WHERE 1=1"
        params = {}

        if search:
            query += " AND (email ILIKE :search OR first_name ILIKE :search OR last_name ILIKE :search)"
            params["search"] = f"%{search}%"

        if department:
            query += " AND department = :department"
            params["department"] = department

        if is_active is not None:
            query += " AND is_active = :is_active"
            params["is_active"] = is_active

        query += " ORDER BY created_at DESC LIMIT :limit OFFSET :offset"
        params["limit"] = limit
        params["offset"] = offset

        return await self.execute_query(query, params)

    async def update_user(
        self, user_id: str, update_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Update user information."""
        query = """
        UPDATE users SET
            email = COALESCE(:email, email),
            first_name = COALESCE(:first_name, first_name),
            last_name = COALESCE(:last_name, last_name),
            department = COALESCE(:department, department),
            title = COALESCE(:title, title),
            phone = COALESCE(:phone, phone),
            updated_at = :updated_at
        WHERE id = :user_id
        RETURNING *
        """

        params = {
            "user_id": user_id,
            "email": update_data.get("email"),
            "first_name": update_data.get("first_name"),
            "last_name": update_data.get("last_name"),
            "department": update_data.get("department"),
            "title": update_data.get("title"),
            "phone": update_data.get("phone"),
            "updated_at": datetime.now(),
        }

        result = await self.execute_command(query, params)
        return result.get("row", {})

    async def delete_user(self, user_id: str) -> bool:
        """Delete user (soft delete)."""
        query = """
        UPDATE users SET
            is_active = false,
            deleted_at = :deleted_at,
            updated_at = :updated_at
        WHERE id = :user_id
        RETURNING id
        """

        params = {
            "user_id": user_id,
            "deleted_at": datetime.now(),
            "updated_at": datetime.now(),
        }

        result = await self.execute_command(query, params)
        return bool(result.get("row"))

    async def count_users(self, filters: Optional[Dict[str, Any]] = None) -> int:
        """Count users with optional filters."""
        query = "SELECT COUNT(*) as count FROM users WHERE 1=1"
        params = {}

        if filters:
            if filters.get("is_active") is not None:
                query += " AND is_active = :is_active"
                params["is_active"] = filters["is_active"]

            if filters.get("department"):
                query += " AND department = :department"
                params["department"] = filters["department"]

        results = await self.execute_query(query, params)
        return results[0]["count"] if results else 0


class RoleRepository(BaseRepository):
    """Repository for role data operations."""

    async def create_role(self, role_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new role."""
        role_id = str(uuid.uuid4())
        now = datetime.now()

        query = """
        INSERT INTO roles (
            id, name, description, parent_role_id, permissions,
            attributes, is_system_role, max_users, expires_at,
            created_at, updated_at
        ) VALUES (
            :id, :name, :description, :parent_role_id, :permissions,
            :attributes, :is_system_role, :max_users, :expires_at,
            :created_at, :updated_at
        ) RETURNING *
        """

        params = {
            "id": role_id,
            "name": role_data["name"],
            "description": role_data.get("description"),
            "parent_role_id": role_data.get("parent_role_id"),
            "permissions": json.dumps(role_data.get("permissions", [])),
            "attributes": json.dumps(role_data.get("attributes", {})),
            "is_system_role": role_data.get("is_system_role", False),
            "max_users": role_data.get("max_users"),
            "expires_at": role_data.get("expires_at"),
            "created_at": now,
            "updated_at": now,
        }

        result = await self.execute_command(query, params)
        return result.get("row", {})

    async def get_role(self, role_id: str) -> Optional[Dict[str, Any]]:
        """Get role by ID."""
        query = """
        SELECT r.*,
               COUNT(DISTINCT ur.user_id) as user_count,
               p.name as parent_role_name
        FROM roles r
        LEFT JOIN user_roles ur ON r.id = ur.role_id
        LEFT JOIN roles p ON r.parent_role_id = p.id
        WHERE r.id = :role_id
        GROUP BY r.id, p.name
        """
        results = await self.execute_query(query, {"role_id": role_id})
        return results[0] if results else None

    async def get_role_by_name(self, name: str) -> Optional[Dict[str, Any]]:
        """Get role by name."""
        query = """
        SELECT r.*,
               COUNT(DISTINCT ur.user_id) as user_count,
               p.name as parent_role_name
        FROM roles r
        LEFT JOIN user_roles ur ON r.id = ur.role_id
        LEFT JOIN roles p ON r.parent_role_id = p.id
        WHERE r.name = :name
        GROUP BY r.id, p.name
        """
        results = await self.execute_query(query, {"name": name})
        return results[0] if results else None

    async def list_roles(
        self, include_system: bool = True, include_expired: bool = False
    ) -> List[Dict[str, Any]]:
        """List all roles with user counts."""
        query = """
        SELECT r.*,
               COUNT(DISTINCT ur.user_id) as user_count,
               p.name as parent_role_name
        FROM roles r
        LEFT JOIN user_roles ur ON r.id = ur.role_id
        LEFT JOIN roles p ON r.parent_role_id = p.id
        WHERE 1=1
        """
        params = {}

        if not include_system:
            query += " AND r.is_system_role = false"

        if not include_expired:
            query += " AND (r.expires_at IS NULL OR r.expires_at > :now)"
            params["now"] = datetime.now()

        query += " GROUP BY r.id, p.name ORDER BY r.name"

        return await self.execute_query(query, params)

    async def get_role_hierarchy(self) -> List[Dict[str, Any]]:
        """Get complete role hierarchy."""
        query = """
        WITH RECURSIVE role_tree AS (
            SELECT id, name, parent_role_id, 0 as level
            FROM roles
            WHERE parent_role_id IS NULL

            UNION ALL

            SELECT r.id, r.name, r.parent_role_id, rt.level + 1
            FROM roles r
            JOIN role_tree rt ON r.parent_role_id = rt.id
        )
        SELECT * FROM role_tree ORDER BY level, name
        """
        return await self.execute_query(query)

    async def assign_role_to_user(
        self, user_id: str, role_id: str, expires_at: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """Assign role to user."""
        assignment_id = str(uuid.uuid4())

        query = """
        INSERT INTO user_roles (
            id, user_id, role_id, assigned_at, expires_at
        ) VALUES (
            :id, :user_id, :role_id, :assigned_at, :expires_at
        ) ON CONFLICT (user_id, role_id)
        DO UPDATE SET expires_at = :expires_at
        RETURNING *
        """

        params = {
            "id": assignment_id,
            "user_id": user_id,
            "role_id": role_id,
            "assigned_at": datetime.now(),
            "expires_at": expires_at,
        }

        result = await self.execute_command(query, params)
        return result.get("row", {})

    async def revoke_role_from_user(self, user_id: str, role_id: str) -> bool:
        """Revoke role from user."""
        query = """
        DELETE FROM user_roles
        WHERE user_id = :user_id AND role_id = :role_id
        RETURNING id
        """

        params = {"user_id": user_id, "role_id": role_id}
        result = await self.execute_command(query, params)
        return bool(result.get("row"))

    async def get_user_roles(self, user_id: str) -> List[Dict[str, Any]]:
        """Get all roles for a user."""
        query = """
        SELECT r.*, ur.assigned_at, ur.expires_at
        FROM roles r
        JOIN user_roles ur ON r.id = ur.role_id
        WHERE ur.user_id = :user_id
        AND (ur.expires_at IS NULL OR ur.expires_at > :now)
        ORDER BY r.name
        """

        params = {"user_id": user_id, "now": datetime.now()}
        return await self.execute_query(query, params)


class PermissionRepository(BaseRepository):
    """Repository for permission data operations."""

    async def create_permission(
        self, permission_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Create a new permission."""
        permission_id = str(uuid.uuid4())
        now = datetime.now()

        query = """
        INSERT INTO permissions (
            id, name, resource, action, description,
            conditions, created_at, updated_at
        ) VALUES (
            :id, :name, :resource, :action, :description,
            :conditions, :created_at, :updated_at
        ) RETURNING *
        """

        params = {
            "id": permission_id,
            "name": permission_data["name"],
            "resource": permission_data["resource"],
            "action": permission_data["action"],
            "description": permission_data.get("description"),
            "conditions": json.dumps(permission_data.get("conditions", {})),
            "created_at": now,
            "updated_at": now,
        }

        result = await self.execute_command(query, params)
        return result.get("row", {})

    async def get_permission(self, permission_id: str) -> Optional[Dict[str, Any]]:
        """Get permission by ID."""
        query = "SELECT * FROM permissions WHERE id = :permission_id"
        results = await self.execute_query(query, {"permission_id": permission_id})
        return results[0] if results else None

    async def list_permissions(
        self, resource: Optional[str] = None, action: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """List permissions with optional filtering."""
        query = "SELECT * FROM permissions WHERE 1=1"
        params = {}

        if resource:
            query += " AND resource = :resource"
            params["resource"] = resource

        if action:
            query += " AND action = :action"
            params["action"] = action

        query += " ORDER BY resource, action"

        return await self.execute_query(query, params)

    async def get_role_permissions(self, role_id: str) -> List[Dict[str, Any]]:
        """Get all permissions for a role including inherited."""
        query = """
        WITH RECURSIVE role_hierarchy AS (
            SELECT id, parent_role_id
            FROM roles
            WHERE id = :role_id

            UNION ALL

            SELECT r.id, r.parent_role_id
            FROM roles r
            JOIN role_hierarchy rh ON r.id = rh.parent_role_id
        )
        SELECT DISTINCT p.*
        FROM permissions p
        JOIN role_permissions rp ON p.id = rp.permission_id
        JOIN role_hierarchy rh ON rp.role_id = rh.id
        ORDER BY p.resource, p.action
        """

        return await self.execute_query(query, {"role_id": role_id})

    async def check_user_permission(
        self, user_id: str, resource: str, action: str
    ) -> bool:
        """Check if user has specific permission."""
        query = """
        SELECT COUNT(*) > 0 as has_permission
        FROM permissions p
        JOIN role_permissions rp ON p.id = rp.permission_id
        JOIN user_roles ur ON rp.role_id = ur.role_id
        WHERE ur.user_id = :user_id
        AND p.resource = :resource
        AND p.action = :action
        AND (ur.expires_at IS NULL OR ur.expires_at > :now)
        """

        params = {
            "user_id": user_id,
            "resource": resource,
            "action": action,
            "now": datetime.now(),
        }

        results = await self.execute_query(query, params)
        return results[0]["has_permission"] if results else False


class SessionRepository(BaseRepository):
    """Repository for session management."""

    async def create_session(self, session_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new session."""
        session_id = str(uuid.uuid4())
        now = datetime.now()

        query = """
        INSERT INTO sessions (
            id, user_id, token, ip_address, user_agent,
            device_id, expires_at, created_at, last_activity
        ) VALUES (
            :id, :user_id, :token, :ip_address, :user_agent,
            :device_id, :expires_at, :created_at, :last_activity
        ) RETURNING *
        """

        params = {
            "id": session_id,
            "user_id": session_data["user_id"],
            "token": session_data["token"],
            "ip_address": session_data.get("ip_address"),
            "user_agent": session_data.get("user_agent"),
            "device_id": session_data.get("device_id"),
            "expires_at": session_data.get("expires_at", now + timedelta(hours=24)),
            "created_at": now,
            "last_activity": now,
        }

        result = await self.execute_command(query, params)
        return result.get("row", {})

    async def get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get session by ID."""
        query = """
        SELECT s.*, u.email, u.first_name, u.last_name
        FROM sessions s
        JOIN users u ON s.user_id = u.id
        WHERE s.id = :session_id
        AND s.expires_at > :now
        """

        params = {"session_id": session_id, "now": datetime.now()}
        results = await self.execute_query(query, params)
        return results[0] if results else None

    async def update_session_activity(self, session_id: str) -> bool:
        """Update session last activity."""
        query = """
        UPDATE sessions SET
            last_activity = :last_activity
        WHERE id = :session_id
        AND expires_at > :now
        RETURNING id
        """

        params = {
            "session_id": session_id,
            "last_activity": datetime.now(),
            "now": datetime.now(),
        }

        result = await self.execute_command(query, params)
        return bool(result.get("row"))

    async def invalidate_session(self, session_id: str) -> bool:
        """Invalidate a session."""
        query = """
        UPDATE sessions SET
            expires_at = :expires_at
        WHERE id = :session_id
        RETURNING id
        """

        params = {"session_id": session_id, "expires_at": datetime.now()}

        result = await self.execute_command(query, params)
        return bool(result.get("row"))

    async def get_user_sessions(self, user_id: str) -> List[Dict[str, Any]]:
        """Get all active sessions for a user."""
        query = """
        SELECT * FROM sessions
        WHERE user_id = :user_id
        AND expires_at > :now
        ORDER BY last_activity DESC
        """

        params = {"user_id": user_id, "now": datetime.now()}
        return await self.execute_query(query, params)

    async def cleanup_expired_sessions(self) -> int:
        """Clean up expired sessions."""
        query = """
        DELETE FROM sessions
        WHERE expires_at < :now
        RETURNING id
        """

        result = await self.execute_command(query, {"now": datetime.now()})
        return len(result.get("rows", []))


class AuditRepository(BaseRepository):
    """Repository for audit log operations."""

    async def create_audit_log(self, audit_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new audit log entry."""
        audit_id = str(uuid.uuid4())

        query = """
        INSERT INTO audit_logs (
            id, event_type, severity, user_id, resource_id,
            action, description, metadata, ip_address,
            user_agent, session_id, correlation_id, created_at
        ) VALUES (
            :id, :event_type, :severity, :user_id, :resource_id,
            :action, :description, :metadata, :ip_address,
            :user_agent, :session_id, :correlation_id, :created_at
        ) RETURNING *
        """

        params = {
            "id": audit_id,
            "event_type": audit_data["event_type"],
            "severity": audit_data.get("severity", "info"),
            "user_id": audit_data.get("user_id"),
            "resource_id": audit_data.get("resource_id"),
            "action": audit_data["action"],
            "description": audit_data.get("description"),
            "metadata": json.dumps(audit_data.get("metadata", {})),
            "ip_address": audit_data.get("ip_address"),
            "user_agent": audit_data.get("user_agent"),
            "session_id": audit_data.get("session_id"),
            "correlation_id": audit_data.get("correlation_id"),
            "created_at": datetime.now(),
        }

        result = await self.execute_command(query, params)
        return result.get("row", {})

    async def list_audit_logs(
        self,
        filters: Optional[Dict[str, Any]] = None,
        offset: int = 0,
        limit: int = 100,
    ) -> List[Dict[str, Any]]:
        """List audit logs with filtering."""
        query = """
        SELECT al.*, u.email as user_email
        FROM audit_logs al
        LEFT JOIN users u ON al.user_id = u.id
        WHERE 1=1
        """
        params = {"limit": limit, "offset": offset}

        if filters:
            if filters.get("event_type"):
                query += " AND al.event_type = :event_type"
                params["event_type"] = filters["event_type"]

            if filters.get("severity"):
                query += " AND al.severity = :severity"
                params["severity"] = filters["severity"]

            if filters.get("user_id"):
                query += " AND al.user_id = :user_id"
                params["user_id"] = filters["user_id"]

            if filters.get("start_date"):
                query += " AND al.created_at >= :start_date"
                params["start_date"] = filters["start_date"]

            if filters.get("end_date"):
                query += " AND al.created_at <= :end_date"
                params["end_date"] = filters["end_date"]

        query += " ORDER BY al.created_at DESC LIMIT :limit OFFSET :offset"

        return await self.execute_query(query, params)

    async def get_audit_summary(
        self, start_date: datetime, end_date: datetime
    ) -> Dict[str, Any]:
        """Get audit log summary statistics."""
        query = """
        SELECT
            COUNT(*) as total_events,
            COUNT(DISTINCT user_id) as unique_users,
            COUNT(DISTINCT session_id) as unique_sessions,
            event_type,
            severity,
            COUNT(*) as count
        FROM audit_logs
        WHERE created_at BETWEEN :start_date AND :end_date
        GROUP BY event_type, severity
        """

        params = {"start_date": start_date, "end_date": end_date}
        results = await self.execute_query(query, params)

        summary = {
            "total_events": 0,
            "unique_users": 0,
            "unique_sessions": 0,
            "by_type": {},
            "by_severity": {},
        }

        for row in results:
            summary["total_events"] = row["total_events"]
            summary["unique_users"] = row["unique_users"]
            summary["unique_sessions"] = row["unique_sessions"]

            event_type = row["event_type"]
            severity = row["severity"]
            count = row["count"]

            if event_type not in summary["by_type"]:
                summary["by_type"][event_type] = 0
            summary["by_type"][event_type] += count

            if severity not in summary["by_severity"]:
                summary["by_severity"][severity] = 0
            summary["by_severity"][severity] += count

        return summary


# Initialize repository instances
user_repository = UserRepository()
role_repository = RoleRepository()
permission_repository = PermissionRepository()
session_repository = SessionRepository()
audit_repository = AuditRepository()


# Note: Duplicate repository classes were removed - using first definitions above
