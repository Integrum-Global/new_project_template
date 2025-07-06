"""
MCP Admin API

Administrative API endpoints for MCP system management.
"""

import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from fastapi import Depends, FastAPI, HTTPException, Query
from pydantic import BaseModel

from apps.mcp_platform.core.core.gateway import MCPGateway
from apps.mcp_platform.core.core.models import MCPMetrics
from apps.mcp_platform.core.core.security import MCPSecurityManager

logger = logging.getLogger(__name__)


# Pydantic models
class BlockRequest(BaseModel):
    """Block request model."""

    entity_type: str  # user, server, tool
    entity_id: str
    reason: str


class SecurityPolicyUpdate(BaseModel):
    """Security policy update model."""

    policy_type: str
    policy_data: Dict[str, Any]


class AdminAPI:
    """API for MCP administrative operations."""

    def __init__(self, gateway: MCPGateway, security: MCPSecurityManager):
        """Initialize the admin API."""
        self.gateway = gateway
        self.security = security

    def register_routes(self, app: FastAPI):
        """Register administrative routes."""

        # Dependency to require admin role
        async def require_admin(
            current_user: Dict = Depends(self._get_current_user),
        ) -> Dict:
            if "admin" not in current_user.get("roles", []):
                raise HTTPException(status_code=403, detail="Admin access required")
            return current_user

        @app.get("/api/v1/admin/dashboard")
        async def get_dashboard(current_user: Dict = Depends(require_admin)):
            """Get administrative dashboard data."""
            try:
                # Get system metrics
                metrics = await self._collect_metrics()

                # Get connection stats
                connection_stats = self.gateway.service.get_connection_stats()

                # Get security metrics
                security_metrics = self.security.get_security_metrics()

                # Get recent events
                # TODO: Get from audit log
                recent_events = []

                return {
                    "metrics": metrics.to_dict(),
                    "connections": connection_stats,
                    "security": security_metrics,
                    "recent_events": recent_events,
                    "timestamp": datetime.utcnow().isoformat(),
                }

            except Exception as e:
                logger.error(f"Error getting dashboard: {e}")
                raise HTTPException(status_code=500, detail="Internal server error")

        @app.get("/api/v1/admin/metrics")
        async def get_metrics(
            period: str = Query("1h", description="Time period (1h, 24h, 7d, 30d)"),
            current_user: Dict = Depends(require_admin),
        ):
            """Get detailed system metrics."""
            try:
                # Calculate time range
                now = datetime.utcnow()
                if period == "1h":
                    start_time = now - timedelta(hours=1)
                elif period == "24h":
                    start_time = now - timedelta(days=1)
                elif period == "7d":
                    start_time = now - timedelta(days=7)
                elif period == "30d":
                    start_time = now - timedelta(days=30)
                else:
                    start_time = now - timedelta(hours=1)

                # Get current metrics
                current_metrics = await self._collect_metrics()

                # TODO: Get historical metrics from database
                historical_metrics = []

                return {
                    "period": period,
                    "start_time": start_time.isoformat(),
                    "end_time": now.isoformat(),
                    "current": current_metrics.to_dict(),
                    "historical": historical_metrics,
                }

            except Exception as e:
                logger.error(f"Error getting metrics: {e}")
                raise HTTPException(status_code=500, detail="Internal server error")

        @app.get("/api/v1/admin/audit-logs")
        async def get_audit_logs(
            start_time: Optional[datetime] = Query(None, description="Start time"),
            end_time: Optional[datetime] = Query(None, description="End time"),
            event_type: Optional[str] = Query(None, description="Event type filter"),
            user_id: Optional[str] = Query(None, description="User ID filter"),
            severity: Optional[str] = Query(None, description="Severity filter"),
            limit: int = Query(100, ge=1, le=1000, description="Maximum results"),
            offset: int = Query(0, ge=0, description="Offset for pagination"),
            current_user: Dict = Depends(require_admin),
        ):
            """Get audit logs."""
            try:
                # Build filters
                filters = {}
                if start_time:
                    filters["start_time"] = start_time
                if end_time:
                    filters["end_time"] = end_time
                if event_type:
                    filters["event_type"] = event_type
                if user_id:
                    filters["user_id"] = user_id
                if severity:
                    filters["severity"] = severity

                # Get audit logs from node
                result = await self.gateway.runtime.execute_node_async(
                    self.gateway.audit_node,
                    {
                        "operation": "search_logs",
                        "filters": filters,
                        "limit": limit,
                        "offset": offset,
                    },
                )

                return {
                    "total": result.get("total", 0),
                    "limit": limit,
                    "offset": offset,
                    "logs": result.get("logs", []),
                }

            except Exception as e:
                logger.error(f"Error getting audit logs: {e}")
                raise HTTPException(status_code=500, detail="Internal server error")

        @app.get("/api/v1/admin/security-events")
        async def get_security_events(
            event_type: Optional[str] = Query(None, description="Event type filter"),
            severity: Optional[str] = Query(None, description="Severity filter"),
            limit: int = Query(100, ge=1, le=1000, description="Maximum results"),
            current_user: Dict = Depends(require_admin),
        ):
            """Get security events."""
            try:
                # Build filters
                filters = {}
                if event_type:
                    filters["event_type"] = event_type
                if severity:
                    filters["severity"] = severity

                # Get security events
                result = await self.gateway.runtime.execute_node_async(
                    self.gateway.security.security_node,
                    {"operation": "get_events", "filters": filters, "limit": limit},
                )

                return {
                    "total": result.get("total", 0),
                    "events": result.get("events", []),
                }

            except Exception as e:
                logger.error(f"Error getting security events: {e}")
                raise HTTPException(status_code=500, detail="Internal server error")

        @app.post("/api/v1/admin/block")
        async def block_entity(
            request: BlockRequest, current_user: Dict = Depends(require_admin)
        ):
            """Block a user, server, or tool."""
            try:
                if request.entity_type == "user":
                    await self.security.block_user(request.entity_id, request.reason)
                elif request.entity_type == "server":
                    await self.security.block_server(request.entity_id, request.reason)
                elif request.entity_type == "tool":
                    # Parse tool ID (format: server_id:tool_name)
                    parts = request.entity_id.split(":", 1)
                    if len(parts) != 2:
                        raise ValueError(
                            "Tool ID must be in format 'server_id:tool_name'"
                        )
                    await self.security.block_tool(parts[0], parts[1], request.reason)
                else:
                    raise ValueError(f"Unknown entity type: {request.entity_type}")

                return {
                    "status": "blocked",
                    "entity_type": request.entity_type,
                    "entity_id": request.entity_id,
                    "reason": request.reason,
                    "blocked_by": current_user.get("user_id"),
                    "blocked_at": datetime.utcnow().isoformat(),
                }

            except ValueError as e:
                raise HTTPException(status_code=400, detail=str(e))
            except Exception as e:
                logger.error(f"Error blocking entity: {e}")
                raise HTTPException(status_code=500, detail="Internal server error")

        @app.delete("/api/v1/admin/block/{entity_type}/{entity_id}")
        async def unblock_entity(
            entity_type: str,
            entity_id: str,
            current_user: Dict = Depends(require_admin),
        ):
            """Unblock a user, server, or tool."""
            try:
                if entity_type == "user":
                    await self.security.unblock_user(entity_id)
                elif entity_type == "server":
                    self.security.blocked_servers.discard(entity_id)
                elif entity_type == "tool":
                    self.security.blocked_tools.discard(entity_id)
                else:
                    raise ValueError(f"Unknown entity type: {entity_type}")

                return {
                    "status": "unblocked",
                    "entity_type": entity_type,
                    "entity_id": entity_id,
                    "unblocked_by": current_user.get("user_id"),
                    "unblocked_at": datetime.utcnow().isoformat(),
                }

            except ValueError as e:
                raise HTTPException(status_code=400, detail=str(e))
            except Exception as e:
                logger.error(f"Error unblocking entity: {e}")
                raise HTTPException(status_code=500, detail="Internal server error")

        @app.get("/api/v1/admin/blocked-entities")
        async def get_blocked_entities(current_user: Dict = Depends(require_admin)):
            """Get all blocked entities."""
            return {
                "blocked_users": list(self.security.blocked_users),
                "blocked_servers": list(self.security.blocked_servers),
                "blocked_tools": list(self.security.blocked_tools),
            }

        @app.put("/api/v1/admin/security-policy")
        async def update_security_policy(
            update: SecurityPolicyUpdate, current_user: Dict = Depends(require_admin)
        ):
            """Update security policies."""
            try:
                if update.policy_type == "rate_limits":
                    self.security.rate_limits.update(update.policy_data)
                elif update.policy_type == "permissions":
                    self.security.permissions.update(update.policy_data)
                elif update.policy_type == "tool_permissions":
                    self.security.tool_permissions.update(update.policy_data)
                else:
                    raise ValueError(f"Unknown policy type: {update.policy_type}")

                # Log the change
                await self.gateway._audit_log(
                    "security_policy_updated",
                    current_user.get("user_id"),
                    {"policy_type": update.policy_type, "changes": update.policy_data},
                    severity="high",
                )

                return {
                    "status": "updated",
                    "policy_type": update.policy_type,
                    "updated_by": current_user.get("user_id"),
                    "updated_at": datetime.utcnow().isoformat(),
                }

            except ValueError as e:
                raise HTTPException(status_code=400, detail=str(e))
            except Exception as e:
                logger.error(f"Error updating security policy: {e}")
                raise HTTPException(status_code=500, detail="Internal server error")

        @app.post("/api/v1/admin/maintenance-mode")
        async def set_maintenance_mode(
            enabled: bool,
            message: Optional[str] = None,
            current_user: Dict = Depends(require_admin),
        ):
            """Enable or disable maintenance mode."""
            try:
                # TODO: Implement maintenance mode

                # Log the change
                await self.gateway._audit_log(
                    "maintenance_mode_changed",
                    current_user.get("user_id"),
                    {"enabled": enabled, "message": message},
                    severity="high",
                )

                return {
                    "status": "success",
                    "maintenance_mode": enabled,
                    "message": message,
                    "changed_by": current_user.get("user_id"),
                    "changed_at": datetime.utcnow().isoformat(),
                }

            except Exception as e:
                logger.error(f"Error setting maintenance mode: {e}")
                raise HTTPException(status_code=500, detail="Internal server error")

        @app.post("/api/v1/admin/broadcast")
        async def broadcast_message(
            message: str,
            severity: str = "info",
            current_user: Dict = Depends(require_admin),
        ):
            """Broadcast a message to all connected clients."""
            try:
                # TODO: Implement broadcasting via WebSocket

                # Log the broadcast
                await self.gateway._audit_log(
                    "broadcast_sent",
                    current_user.get("user_id"),
                    {"message": message, "severity": severity},
                )

                return {
                    "status": "sent",
                    "message": message,
                    "severity": severity,
                    "sent_by": current_user.get("user_id"),
                    "sent_at": datetime.utcnow().isoformat(),
                }

            except Exception as e:
                logger.error(f"Error broadcasting message: {e}")
                raise HTTPException(status_code=500, detail="Internal server error")

    async def _get_current_user(self, authorization: str = None) -> Dict:
        """Get current user from authorization header."""
        if not authorization:
            raise HTTPException(status_code=401, detail="Authorization required")

        # Extract token
        if not authorization.startswith("Bearer "):
            raise HTTPException(status_code=401, detail="Invalid authorization format")

        token = authorization[7:]  # Remove "Bearer " prefix

        # Authenticate
        user_info = await self.security.authenticate_user(
            {"type": "jwt", "token": token}
        )

        if not user_info:
            raise HTTPException(status_code=401, detail="Invalid or expired token")

        return user_info

    async def _collect_metrics(self) -> MCPMetrics:
        """Collect current system metrics."""
        # Get server counts
        all_servers = await self.gateway.registry.list_servers()
        running_servers = [
            s for s in all_servers if s.id in self.gateway._active_connections
        ]
        error_servers = [s for s in all_servers if s.status.value == "error"]

        # Get tool counts
        all_tools = await self.gateway.registry.list_tools()

        # TODO: Get execution metrics from database

        # Get system metrics
        import psutil

        cpu_percent = psutil.cpu_percent(interval=0.1)
        memory_info = psutil.virtual_memory()

        return MCPMetrics(
            total_servers=len(all_servers),
            running_servers=len(running_servers),
            error_servers=len(error_servers),
            total_tools=len(all_tools),
            active_tools=len(all_tools),  # TODO: Track active tools
            executions_last_hour=0,  # TODO: Get from database
            success_rate=100.0,  # TODO: Calculate from database
            average_duration_ms=0.0,  # TODO: Calculate from database
            total_resources=0,  # TODO: Count resources
            cached_resources=0,  # TODO: Count cached resources
            cache_hit_rate=0.0,  # TODO: Calculate cache hit rate
            cpu_usage_percent=cpu_percent,
            memory_usage_mb=memory_info.used / (1024 * 1024),
            active_sessions=len(self.gateway._active_connections),
        )
