"""
Unit tests for Enhanced Session Management.
"""

from datetime import datetime, timedelta
from unittest.mock import AsyncMock, Mock, patch

import pytest
from nexus.core.session import EnhancedSession, EnhancedSessionManager


class TestEnhancedSessionManager:
    """Test EnhancedSessionManager class."""

    @pytest.fixture
    def mock_base_manager(self):
        """Create a mock base session manager."""
        manager = Mock()

        # Create a mock session object
        mock_session = Mock()
        mock_session.session_id = "session123"
        mock_session.user_id = "user1"
        mock_session.metadata = {}
        mock_session.shared_data = {}

        # Setup default returns
        manager.create_session = Mock(return_value=mock_session)
        manager.get_session = Mock(return_value=mock_session)
        manager._sessions = {}

        return manager

    @pytest.mark.asyncio
    async def test_create_session_basic(self, mock_base_manager):
        """Test basic session creation."""
        manager = EnhancedSessionManager(mock_base_manager, create_workflows=False)

        session_id = await manager.create_session(user_id="user1")

        assert session_id == "session123"
        mock_base_manager.create_session.assert_called_once()

        # Check internal tracking
        assert session_id in manager._session_metadata
        metadata = manager._session_metadata[session_id]
        assert metadata["created_at"] is not None

    @pytest.mark.asyncio
    async def test_create_session_with_tenant(self, mock_base_manager):
        """Test session creation with tenant context."""
        manager = EnhancedSessionManager(
            mock_base_manager, multi_tenant=True, create_workflows=False
        )

        session_id = await manager.create_session(
            user_id="user1", tenant_id="tenant123"
        )

        assert session_id == "session123"

        # Check tenant tracking in metadata
        assert session_id in manager._session_metadata
        assert manager._session_metadata[session_id]["tenant_id"] == "tenant123"

    @pytest.mark.asyncio
    async def test_create_session_with_permissions(self, mock_base_manager):
        """Test session creation with permissions."""
        manager = EnhancedSessionManager(mock_base_manager, create_workflows=False)

        session_id = await manager.create_session(
            user_id="user1", permissions=["read", "write", "delete"]
        )

        assert session_id == "session123"
        assert manager._session_metadata[session_id]["permissions"] == [
            "read",
            "write",
            "delete",
        ]

    @pytest.mark.asyncio
    async def test_get_session(self, mock_base_manager):
        """Test getting session data."""
        manager = EnhancedSessionManager(mock_base_manager, create_workflows=False)

        # Create session first
        session_id = await manager.create_session(user_id="user1", channel="api")

        # Get session
        session_data = await manager.get_session("session123")

        assert session_data["user_id"] == "user1"
        assert session_data["session_id"] == "session123"
        assert "last_accessed" in session_data

        # Verify get_session was called on base manager
        mock_base_manager.get_session.assert_called_with("session123")

    @pytest.mark.asyncio
    async def test_update_session(self, mock_base_manager):
        """Test updating session data."""
        manager = EnhancedSessionManager(mock_base_manager, create_workflows=False)

        # Create session
        session_id = await manager.create_session(user_id="user1", channel="api")

        # Update session
        await manager.update_session(
            session_id, {"test_key": "test_value", "counter": 42}
        )

        # Check metadata was updated
        assert manager._session_metadata[session_id]["test_key"] == "test_value"
        assert manager._session_metadata[session_id]["counter"] == 42

    @pytest.mark.asyncio
    async def test_close_session(self, mock_base_manager):
        """Test closing a session."""
        manager = EnhancedSessionManager(mock_base_manager, create_workflows=False)

        # Create session
        session_id = await manager.create_session(
            user_id="user1", tenant_id="tenant123"
        )

        # Close session
        result = await manager.close_session(session_id)

        assert result is True
        assert session_id not in manager._session_metadata

    @pytest.mark.asyncio
    async def test_delete_session(self, mock_base_manager):
        """Test delete_session which is an alias for close_session."""
        manager = EnhancedSessionManager(mock_base_manager, create_workflows=False)

        # Create session
        session_id = await manager.create_session(user_id="user1")

        # Delete session (should call close_session)
        result = await manager.delete_session(session_id)

        assert result is True
        assert session_id not in manager._session_metadata

    @pytest.mark.asyncio
    async def test_list_user_sessions(self, mock_base_manager):
        """Test listing sessions for a user."""
        manager = EnhancedSessionManager(mock_base_manager, create_workflows=False)

        # Setup mock sessions in _sessions
        mock_session1 = Mock()
        mock_session1.session_id = "session123"
        mock_session1.user_id = "user1"
        mock_session2 = Mock()
        mock_session2.session_id = "session456"
        mock_session2.user_id = "user1"
        mock_session3 = Mock()
        mock_session3.session_id = "session789"
        mock_session3.user_id = "user2"

        mock_base_manager._sessions = {
            "session123": mock_session1,
            "session456": mock_session2,
            "session789": mock_session3,
        }

        # Create metadata for sessions
        manager._session_metadata = {
            "session123": {"tenant_id": "tenant1"},
            "session456": {"tenant_id": "tenant1"},
            "session789": {"tenant_id": "tenant2"},
        }

        # Mock get_session to return session data
        def mock_get_session(sid):
            return {
                "session_id": sid,
                "user_id": mock_base_manager._sessions[sid].user_id,
            }

        manager.get_session = AsyncMock(side_effect=mock_get_session)

        # List user sessions
        sessions = await manager.list_user_sessions("user1")

        assert len(sessions) == 2
        session_ids = [s["session_id"] for s in sessions]
        assert "session123" in session_ids
        assert "session456" in session_ids

    @pytest.mark.asyncio
    async def test_list_tenant_sessions(self, mock_base_manager):
        """Test listing sessions for a tenant."""
        manager = EnhancedSessionManager(
            mock_base_manager, multi_tenant=True, create_workflows=False
        )

        # Create sessions with metadata
        manager._session_metadata = {
            "session123": {"tenant_id": "tenant1"},
            "session456": {"tenant_id": "tenant1"},
            "session789": {"tenant_id": "tenant2"},
        }

        # Mock base manager get_session to return valid sessions
        mock_base_manager.get_session = Mock(
            side_effect=lambda sid: Mock(session_id=sid)
        )

        # List tenant sessions
        sessions = await manager.list_tenant_sessions("tenant1")

        assert len(sessions) == 2
        assert "session123" in sessions
        assert "session456" in sessions
        assert "session789" not in sessions

    @pytest.mark.asyncio
    async def test_validate_tenant_access(self, mock_base_manager):
        """Test tenant access validation."""
        manager = EnhancedSessionManager(
            mock_base_manager, multi_tenant=True, create_workflows=False
        )

        # Create session with tenant
        session_id = await manager.create_session(
            user_id="user1", tenant_id="tenant123"
        )

        # Mock get_session to return session data
        manager.get_session = AsyncMock(
            return_value={"tenant_id": "tenant123", "permissions": []}
        )

        # Test access to same tenant
        assert await manager.validate_tenant_access(session_id, "tenant123") is True

        # Test access to different tenant
        assert await manager.validate_tenant_access(session_id, "tenant456") is False

        # Test system access
        manager.get_session = AsyncMock(
            return_value={"tenant_id": "tenant123", "permissions": ["system:*"]}
        )
        assert await manager.validate_tenant_access(session_id, "tenant456") is True

    @pytest.mark.asyncio
    async def test_cleanup_expired(self, mock_base_manager):
        """Test cleanup of expired sessions."""
        manager = EnhancedSessionManager(mock_base_manager, create_workflows=False)

        # Create some metadata
        manager._session_metadata = {
            "session123": {"created_at": "2024-01-01"},
            "session456": {"created_at": "2024-01-01"},
            "session789": {"created_at": "2024-01-01"},
        }

        # Mock _sessions to simulate some sessions being removed
        mock_base_manager._sessions = {
            "session123": Mock(),  # This one remains
            # session456 and session789 are gone
        }

        # Run cleanup
        cleaned = await manager.cleanup_expired()

        # Check that metadata was cleaned up
        assert "session123" in manager._session_metadata
        assert "session456" not in manager._session_metadata
        assert "session789" not in manager._session_metadata

    @pytest.mark.asyncio
    async def test_get_session_metrics(self, mock_base_manager):
        """Test getting session metrics."""
        manager = EnhancedSessionManager(
            mock_base_manager, multi_tenant=True, create_workflows=False
        )

        # Setup sessions
        mock_base_manager._sessions = {
            "session123": Mock(),
            "session456": Mock(),
            "session789": Mock(),
        }

        # Setup metadata
        manager._session_metadata = {
            "session123": {"tenant_id": "tenant1"},
            "session456": {"tenant_id": "tenant1"},
            "session789": {"tenant_id": "tenant2"},
        }

        # Get metrics
        metrics = await manager.get_session_metrics()

        assert metrics["total_sessions"] == 3
        assert metrics["active_sessions"] == 3
        assert metrics["tenant_breakdown"]["tenant1"] == 2
        assert metrics["tenant_breakdown"]["tenant2"] == 1

    @pytest.mark.asyncio
    async def test_enhanced_session_model(self):
        """Test the EnhancedSession model."""
        session = EnhancedSession(
            session_id="test123", user_id="user1", tenant_id="tenant1"
        )

        # Test permission management
        session.add_permission("read")
        session.add_permission("write")
        session.add_permission("read")  # Duplicate

        assert len(session.permissions) == 2
        assert session.has_permission("read")
        assert session.has_permission("write")
        assert not session.has_permission("delete")

        # Test wildcard permission
        session.add_permission("*")
        assert session.has_permission("delete")

        # Test usage tracking
        session.track_usage("api_calls", 5)
        session.track_usage("api_calls", 3)
        assert session.quota_usage["api_calls"] == 8

        # Test audit trail
        assert len(session.audit_trail) >= 4  # Permission adds + usage tracking

        # Test to_dict
        data = session.to_dict()
        assert data["session_id"] == "test123"
        assert data["user_id"] == "user1"
        assert data["tenant_id"] == "tenant1"
        assert len(data["permissions"]) == 3
        assert data["quota_usage"]["api_calls"] == 8
