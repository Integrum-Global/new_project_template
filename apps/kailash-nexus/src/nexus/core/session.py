"""
Enhanced Session Management for Nexus Application

Built on top of SDK's SessionManager with enterprise features.
"""

import asyncio
import json
import logging
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional

from kailash.channels.session import CrossChannelSession as Session
from kailash.channels.session import SessionManager as SDKSessionManager
from kailash.nodes.cache.cache import CacheNode
from kailash.nodes.data.async_sql import AsyncSQLDatabaseNode
from kailash.workflow.builder import WorkflowBuilder

logger = logging.getLogger(__name__)


class EnhancedSession(Session):
    """Enhanced session with enterprise features."""

    def __init__(
        self,
        session_id: str,
        user_id: Optional[str] = None,
        tenant_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
        **kwargs,
    ):
        """Initialize enhanced session.

        Args:
            session_id: Session identifier
            user_id: User identifier
            tenant_id: Optional tenant identifier for multi-tenant support
            metadata: Optional metadata
        """
        # Filter out metadata from kwargs as CrossChannelSession doesn't accept it
        if "metadata" in kwargs:
            kwargs.pop("metadata")
        super().__init__(session_id=session_id, user_id=user_id, **kwargs)
        self.tenant_id = tenant_id
        self.permissions: List[str] = []
        self.audit_trail: List[Dict[str, Any]] = []
        self.quota_usage: Dict[str, int] = {}
        self.metadata = metadata or {}

    def add_permission(self, permission: str):
        """Add a permission to the session."""
        if permission not in self.permissions:
            self.permissions.append(permission)
            self._audit("permission_added", {"permission": permission})

    def has_permission(self, permission: str) -> bool:
        """Check if session has a permission."""
        return permission in self.permissions or "*" in self.permissions

    def track_usage(self, resource: str, amount: int = 1):
        """Track resource usage for quotas."""
        if resource not in self.quota_usage:
            self.quota_usage[resource] = 0
        self.quota_usage[resource] += amount
        self._audit("resource_usage", {"resource": resource, "amount": amount})

    def _audit(self, action: str, details: Optional[Dict[str, Any]] = None):
        """Add entry to audit trail."""
        entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "action": action,
            "details": details or {},
        }
        self.audit_trail.append(entry)

    def to_dict(self) -> Dict[str, Any]:
        """Convert session to dictionary."""
        data = super().to_dict()
        data.update(
            {
                "tenant_id": self.tenant_id,
                "permissions": self.permissions,
                "quota_usage": self.quota_usage,
                "audit_entries": len(self.audit_trail),
            }
        )
        return data


class EnhancedSessionManager:
    """Enhanced session manager with enterprise features."""

    def __init__(
        self,
        base_manager: SDKSessionManager,
        multi_tenant: bool = False,
        create_workflows: bool = True,
    ):
        """Initialize enhanced session manager.

        Args:
            base_manager: SDK session manager to enhance
            multi_tenant: Enable multi-tenant support
            create_workflows: Whether to create workflows (set False for unit tests)
        """
        self._base_manager = base_manager
        self._multi_tenant = multi_tenant

        # Create persistence workflow if needed
        self._persistence_workflow = (
            self._create_persistence_workflow() if create_workflows else None
        )

        # Session metadata cache
        self._session_metadata: Dict[str, Dict[str, Any]] = {}

        logger.info("Enhanced session manager initialized")

    def _create_persistence_workflow(self) -> WorkflowBuilder:
        """Create workflow for session persistence using SDK nodes."""
        builder = WorkflowBuilder()

        # Add distributed cache node for fast access
        builder.add_node(
            "CacheNode",
            "cache",
            {"backend": "redis", "ttl": 3600, "key_prefix": "nexus_session:"},
        )

        # Add database node for persistent storage
        builder.add_node(
            "AsyncSQLDatabaseNode",
            "database",
            {
                "table": "nexus_sessions",
                "operation": "upsert",
                "key_column": "session_id",
            },
        )

        # Connect nodes
        builder.add_connection("cache", "result", "database", "data")

        return builder.build()

    async def create_session(
        self,
        user_id: str,
        metadata: Optional[Dict[str, Any]] = None,
        tenant_id: Optional[str] = None,
        permissions: Optional[List[str]] = None,
        channel: Optional[str] = None,
    ) -> str:
        """Create an enhanced session.

        Args:
            user_id: User identifier
            metadata: Optional session metadata
            tenant_id: Optional tenant identifier
            permissions: Optional initial permissions

        Returns:
            Enhanced session instance
        """
        # Create base session
        # Check if create_session is async or sync
        if asyncio.iscoroutinefunction(self._base_manager.create_session):
            base_session = await self._base_manager.create_session(user_id, metadata)
        else:
            base_session = self._base_manager.create_session(user_id, metadata)

        # Enhance with enterprise features
        enhanced = EnhancedSession(
            session_id=base_session.session_id, user_id=user_id, tenant_id=tenant_id
        )

        # Set shared data from metadata
        if metadata:
            if hasattr(enhanced, "shared_data") and isinstance(
                enhanced.shared_data, dict
            ):
                enhanced.shared_data.update(metadata)
            else:
                enhanced.metadata = metadata

        # Add permissions
        if permissions:
            for permission in permissions:
                enhanced.add_permission(permission)

        # Store enhanced metadata
        self._session_metadata[enhanced.session_id] = {
            "tenant_id": tenant_id,
            "permissions": permissions or [],
            "created_at": datetime.now(timezone.utc).isoformat(),
        }

        # Audit session creation
        enhanced._audit("session_created", {"user_id": user_id, "tenant_id": tenant_id})

        logger.info(f"Created enhanced session: {enhanced.session_id}")
        return enhanced.session_id

    async def get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get an enhanced session by ID.

        Args:
            session_id: Session identifier

        Returns:
            Enhanced session or None if not found
        """
        # Get base session
        # Check if get_session is async or sync
        if asyncio.iscoroutinefunction(self._base_manager.get_session):
            base_session = await self._base_manager.get_session(session_id)
        else:
            base_session = self._base_manager.get_session(session_id)
        if not base_session:
            return None

        # Get enhanced metadata
        metadata = self._session_metadata.get(session_id, {})

        # Create enhanced session
        enhanced = EnhancedSession(
            session_id=base_session.session_id,
            user_id=base_session.user_id,
            metadata=getattr(
                base_session, "metadata", getattr(base_session, "shared_data", {})
            ),
            tenant_id=metadata.get("tenant_id"),
        )

        # Restore permissions
        for permission in metadata.get("permissions", []):
            enhanced.add_permission(permission)

        # Update last accessed time
        enhanced.last_accessed = datetime.now(timezone.utc)

        # Merge in any additional metadata we've stored
        result_data = {
            "session_id": enhanced.session_id,
            "user_id": enhanced.user_id,
            "tenant_id": enhanced.tenant_id,
            "permissions": enhanced.permissions,
            "shared_data": getattr(
                enhanced, "shared_data", getattr(enhanced, "metadata", {})
            ),
            "created_at": getattr(enhanced, "created_at", datetime.now(timezone.utc)),
            "last_accessed": enhanced.last_accessed,
            "metadata": getattr(enhanced, "metadata", {}),
        }

        # Include any additional data stored in our metadata
        if session_id in self._session_metadata:
            for key, value in self._session_metadata[session_id].items():
                if key not in result_data:
                    result_data[key] = value

        return result_data

    async def validate_tenant_access(
        self, session_id: str, resource_tenant_id: str
    ) -> bool:
        """Validate session has access to tenant resource.

        Args:
            session_id: Session identifier
            resource_tenant_id: Tenant ID of resource

        Returns:
            True if access allowed
        """
        if not self._multi_tenant:
            return True

        session = await self.get_session(session_id)
        if not session:
            return False

        # System sessions can access any tenant
        if "system:*" in session.get("permissions", []):
            return True

        # Check tenant match
        return session.get("tenant_id") == resource_tenant_id

    async def update_session(self, session_id: str, data: Dict[str, Any]):
        """Update session with data.

        Args:
            session_id: Session identifier
            data: Data to update
        """
        # Since base manager doesn't have update methods, we'll store in our metadata
        if session_id not in self._session_metadata:
            self._session_metadata[session_id] = {}

        # Update local metadata
        self._session_metadata[session_id].update(data)

        # Also update the session's shared_data if it exists
        if (
            hasattr(self._base_manager, "_sessions")
            and session_id in self._base_manager._sessions
        ):
            session = self._base_manager._sessions[session_id]
            if hasattr(session, "shared_data"):
                session.shared_data.update(data)

    async def update_session_data(self, session_id: str, key: str, value: Any) -> bool:
        """Update session data.

        Args:
            session_id: Session identifier
            key: Data key
            value: Data value

        Returns:
            True if updated successfully
        """
        # Update in base manager
        if asyncio.iscoroutinefunction(self._base_manager.set_session_data):
            success = await self._base_manager.set_session_data(session_id, key, value)
        else:
            success = self._base_manager.set_session_data(session_id, key, value)

        if success:
            # Audit the update by adding to metadata
            if session_id in self._session_metadata:
                if "audit_trail" not in self._session_metadata[session_id]:
                    self._session_metadata[session_id]["audit_trail"] = []
                self._session_metadata[session_id]["audit_trail"].append(
                    {
                        "timestamp": datetime.now(timezone.utc).isoformat(),
                        "action": "data_updated",
                        "details": {"key": key},
                    }
                )

        return success

    async def list_tenant_sessions(self, tenant_id: str) -> List[str]:
        """List all sessions for a tenant.

        Args:
            tenant_id: Tenant identifier

        Returns:
            List of session IDs
        """
        tenant_sessions = []

        for session_id, metadata in self._session_metadata.items():
            if metadata.get("tenant_id") == tenant_id:
                # Verify session still active
                if asyncio.iscoroutinefunction(self._base_manager.get_session):
                    session = await self._base_manager.get_session(session_id)
                else:
                    session = self._base_manager.get_session(session_id)
                if session:
                    tenant_sessions.append(session_id)

        return tenant_sessions

    async def revoke_tenant_sessions(self, tenant_id: str) -> int:
        """Revoke all sessions for a tenant.

        Args:
            tenant_id: Tenant identifier

        Returns:
            Number of sessions revoked
        """
        sessions = await self.list_tenant_sessions(tenant_id)

        for session_id in sessions:
            await self.close_session(session_id)

        logger.info(f"Revoked {len(sessions)} sessions for tenant {tenant_id}")
        return len(sessions)

    async def close_session(self, session_id: str) -> bool:
        """Close a session.

        Args:
            session_id: Session identifier

        Returns:
            True if closed successfully
        """
        # Get session for audit
        if session_id in self._session_metadata:
            if "audit_trail" not in self._session_metadata[session_id]:
                self._session_metadata[session_id]["audit_trail"] = []
            self._session_metadata[session_id]["audit_trail"].append(
                {
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "action": "session_closed",
                    "details": {},
                }
            )

        # Remove from metadata
        self._session_metadata.pop(session_id, None)

        # Remove from base manager's sessions if it exists
        if (
            hasattr(self._base_manager, "_sessions")
            and session_id in self._base_manager._sessions
        ):
            del self._base_manager._sessions[session_id]
            return True

        return True  # Always return True since we removed from our metadata

    async def get_session_metrics(self) -> Dict[str, Any]:
        """Get session metrics.

        Returns:
            Session metrics dictionary
        """
        total_sessions = 0
        active_sessions = 0

        if hasattr(self._base_manager, "_sessions"):
            total_sessions = len(self._base_manager._sessions)
            active_sessions = total_sessions  # Assume all are active

        metrics = {
            "total_sessions": total_sessions,
            "active_sessions": active_sessions,
            "tenant_breakdown": {},
        }

        if self._multi_tenant:
            # Count sessions by tenant
            tenant_counts = {}
            for session_id, metadata in self._session_metadata.items():
                tenant_id = metadata.get("tenant_id", "default")
                tenant_counts[tenant_id] = tenant_counts.get(tenant_id, 0) + 1

            metrics["tenant_breakdown"] = tenant_counts

        return metrics

    async def list_user_sessions(self, user_id: str) -> List[Dict[str, Any]]:
        """List all sessions for a user.

        Args:
            user_id: User identifier

        Returns:
            List of session dictionaries
        """
        user_sessions = []

        # Get all sessions from base manager
        # Since list_sessions doesn't exist, we'll iterate over sessions
        if hasattr(self._base_manager, "_sessions"):
            for session_id, session in self._base_manager._sessions.items():
                if hasattr(session, "user_id") and session.user_id == user_id:
                    # Get enhanced session data
                    session_data = await self.get_session(session_id)
                    if session_data:
                        user_sessions.append(session_data)

        return user_sessions

    async def delete_session(self, session_id: str) -> bool:
        """Delete a session.

        Args:
            session_id: Session identifier

        Returns:
            True if deleted successfully
        """
        return await self.close_session(session_id)

    async def cleanup_expired(self) -> int:
        """Clean up expired sessions.

        Returns:
            Number of sessions cleaned up
        """
        # Since base manager doesn't have cleanup_expired,
        # we'll manually clean up expired sessions
        cleaned = 0

        # Get active session IDs
        active_ids = set()
        if hasattr(self._base_manager, "_sessions"):
            active_ids = set(self._base_manager._sessions.keys())

        to_remove = []
        for session_id in self._session_metadata:
            if session_id not in active_ids:
                to_remove.append(session_id)

        for session_id in to_remove:
            self._session_metadata.pop(session_id, None)

        return cleaned
