"""
MCP Webhooks API

API endpoints for webhook management and event streaming.
"""

import asyncio
import logging
import secrets
from datetime import datetime
from typing import Any, Dict, List, Optional

import aiohttp
from fastapi import (
    Depends,
    FastAPI,
    HTTPException,
    Query,
    WebSocket,
    WebSocketDisconnect,
)
from pydantic import BaseModel, HttpUrl

from apps.mcp_platform.core.core.gateway import MCPGateway
from apps.mcp_platform.core.core.security import MCPSecurityManager

logger = logging.getLogger(__name__)


# Pydantic models
class WebhookConfig(BaseModel):
    """Webhook configuration model."""

    url: HttpUrl
    events: List[str]
    active: bool = True
    headers: Optional[Dict[str, str]] = None
    secret: Optional[str] = None
    description: Optional[str] = None


class WebhookUpdate(BaseModel):
    """Webhook update model."""

    url: Optional[HttpUrl] = None
    events: Optional[List[str]] = None
    active: Optional[bool] = None
    headers: Optional[Dict[str, str]] = None
    description: Optional[str] = None


class WebhookResponse(BaseModel):
    """Webhook response model."""

    id: str
    url: str
    events: List[str]
    active: bool
    created_at: str
    last_triggered: Optional[str] = None
    success_count: int = 0
    failure_count: int = 0


class WebhooksAPI:
    """API for webhook management and event streaming."""

    def __init__(self, gateway: MCPGateway, security: MCPSecurityManager):
        """Initialize the webhooks API."""
        self.gateway = gateway
        self.security = security

        # Webhook storage (in production, use database)
        self._webhooks: Dict[str, Dict[str, Any]] = {}

        # WebSocket connections
        self._websocket_connections: List[WebSocket] = []

        # Event queue for webhooks
        self._event_queue = asyncio.Queue()
        self._webhook_task = None

    def register_routes(self, app: FastAPI):
        """Register webhook management routes."""

        # Start webhook processor
        @app.on_event("startup")
        async def start_webhook_processor():
            self._webhook_task = asyncio.create_task(self._process_webhook_events())

        # Stop webhook processor
        @app.on_event("shutdown")
        async def stop_webhook_processor():
            if self._webhook_task:
                self._webhook_task.cancel()

        @app.post("/api/v1/webhooks", response_model=WebhookResponse)
        async def create_webhook(
            webhook: WebhookConfig, current_user: Dict = Depends(self._get_current_user)
        ):
            """Create a new webhook."""
            try:
                # Check permissions
                if "admin" not in current_user.get(
                    "roles", []
                ) and "operator" not in current_user.get("roles", []):
                    raise PermissionError("Insufficient permissions to create webhooks")

                # Generate webhook ID and secret
                webhook_id = str(secrets.token_urlsafe(16))
                secret = webhook.secret or secrets.token_urlsafe(32)

                # Store webhook
                self._webhooks[webhook_id] = {
                    "id": webhook_id,
                    "url": str(webhook.url),
                    "events": webhook.events,
                    "active": webhook.active,
                    "headers": webhook.headers or {},
                    "secret": secret,
                    "description": webhook.description,
                    "owner_id": current_user.get("user_id"),
                    "created_at": datetime.utcnow(),
                    "last_triggered": None,
                    "success_count": 0,
                    "failure_count": 0,
                }

                # Log creation
                await self.gateway._audit_log(
                    "webhook_created",
                    current_user.get("user_id"),
                    {"webhook_id": webhook_id, "url": str(webhook.url)},
                )

                return WebhookResponse(
                    id=webhook_id,
                    url=str(webhook.url),
                    events=webhook.events,
                    active=webhook.active,
                    created_at=self._webhooks[webhook_id]["created_at"].isoformat(),
                    success_count=0,
                    failure_count=0,
                )

            except PermissionError as e:
                raise HTTPException(status_code=403, detail=str(e))
            except Exception as e:
                logger.error(f"Error creating webhook: {e}")
                raise HTTPException(status_code=500, detail="Internal server error")

        @app.get("/api/v1/webhooks", response_model=List[WebhookResponse])
        async def list_webhooks(
            active_only: bool = Query(False, description="Only show active webhooks"),
            current_user: Dict = Depends(self._get_current_user),
        ):
            """List webhooks."""
            try:
                # Filter webhooks by permissions
                webhooks = []
                for webhook_id, webhook in self._webhooks.items():
                    # Admin can see all, others only their own
                    if "admin" in current_user.get("roles", []) or webhook[
                        "owner_id"
                    ] == current_user.get("user_id"):

                        if not active_only or webhook["active"]:
                            webhooks.append(
                                WebhookResponse(
                                    id=webhook_id,
                                    url=webhook["url"],
                                    events=webhook["events"],
                                    active=webhook["active"],
                                    created_at=webhook["created_at"].isoformat(),
                                    last_triggered=(
                                        webhook["last_triggered"].isoformat()
                                        if webhook["last_triggered"]
                                        else None
                                    ),
                                    success_count=webhook["success_count"],
                                    failure_count=webhook["failure_count"],
                                )
                            )

                return webhooks

            except Exception as e:
                logger.error(f"Error listing webhooks: {e}")
                raise HTTPException(status_code=500, detail="Internal server error")

        @app.get("/api/v1/webhooks/{webhook_id}")
        async def get_webhook(
            webhook_id: str, current_user: Dict = Depends(self._get_current_user)
        ):
            """Get webhook details including secret."""
            try:
                webhook = self._webhooks.get(webhook_id)
                if not webhook:
                    raise ValueError("Webhook not found")

                # Check permissions
                if "admin" not in current_user.get("roles", []) and webhook[
                    "owner_id"
                ] != current_user.get("user_id"):
                    raise PermissionError("Not authorized to view this webhook")

                return {
                    "id": webhook_id,
                    "url": webhook["url"],
                    "events": webhook["events"],
                    "active": webhook["active"],
                    "headers": webhook["headers"],
                    "secret": webhook["secret"],
                    "description": webhook["description"],
                    "created_at": webhook["created_at"].isoformat(),
                    "last_triggered": (
                        webhook["last_triggered"].isoformat()
                        if webhook["last_triggered"]
                        else None
                    ),
                    "success_count": webhook["success_count"],
                    "failure_count": webhook["failure_count"],
                }

            except ValueError as e:
                raise HTTPException(status_code=404, detail=str(e))
            except PermissionError as e:
                raise HTTPException(status_code=403, detail=str(e))
            except Exception as e:
                logger.error(f"Error getting webhook: {e}")
                raise HTTPException(status_code=500, detail="Internal server error")

        @app.put("/api/v1/webhooks/{webhook_id}")
        async def update_webhook(
            webhook_id: str,
            update: WebhookUpdate,
            current_user: Dict = Depends(self._get_current_user),
        ):
            """Update webhook configuration."""
            try:
                webhook = self._webhooks.get(webhook_id)
                if not webhook:
                    raise ValueError("Webhook not found")

                # Check permissions
                if "admin" not in current_user.get("roles", []) and webhook[
                    "owner_id"
                ] != current_user.get("user_id"):
                    raise PermissionError("Not authorized to update this webhook")

                # Update fields
                if update.url is not None:
                    webhook["url"] = str(update.url)
                if update.events is not None:
                    webhook["events"] = update.events
                if update.active is not None:
                    webhook["active"] = update.active
                if update.headers is not None:
                    webhook["headers"] = update.headers
                if update.description is not None:
                    webhook["description"] = update.description

                # Log update
                await self.gateway._audit_log(
                    "webhook_updated",
                    current_user.get("user_id"),
                    {"webhook_id": webhook_id},
                )

                return {"status": "updated", "webhook_id": webhook_id}

            except ValueError as e:
                raise HTTPException(status_code=404, detail=str(e))
            except PermissionError as e:
                raise HTTPException(status_code=403, detail=str(e))
            except Exception as e:
                logger.error(f"Error updating webhook: {e}")
                raise HTTPException(status_code=500, detail="Internal server error")

        @app.delete("/api/v1/webhooks/{webhook_id}")
        async def delete_webhook(
            webhook_id: str, current_user: Dict = Depends(self._get_current_user)
        ):
            """Delete a webhook."""
            try:
                webhook = self._webhooks.get(webhook_id)
                if not webhook:
                    raise ValueError("Webhook not found")

                # Check permissions
                if "admin" not in current_user.get("roles", []) and webhook[
                    "owner_id"
                ] != current_user.get("user_id"):
                    raise PermissionError("Not authorized to delete this webhook")

                # Delete webhook
                del self._webhooks[webhook_id]

                # Log deletion
                await self.gateway._audit_log(
                    "webhook_deleted",
                    current_user.get("user_id"),
                    {"webhook_id": webhook_id},
                )

                return {"status": "deleted", "webhook_id": webhook_id}

            except ValueError as e:
                raise HTTPException(status_code=404, detail=str(e))
            except PermissionError as e:
                raise HTTPException(status_code=403, detail=str(e))
            except Exception as e:
                logger.error(f"Error deleting webhook: {e}")
                raise HTTPException(status_code=500, detail="Internal server error")

        @app.post("/api/v1/webhooks/{webhook_id}/test")
        async def test_webhook(
            webhook_id: str, current_user: Dict = Depends(self._get_current_user)
        ):
            """Test a webhook with sample data."""
            try:
                webhook = self._webhooks.get(webhook_id)
                if not webhook:
                    raise ValueError("Webhook not found")

                # Check permissions
                if "admin" not in current_user.get("roles", []) and webhook[
                    "owner_id"
                ] != current_user.get("user_id"):
                    raise PermissionError("Not authorized to test this webhook")

                # Create test event
                test_event = {
                    "event": "webhook.test",
                    "timestamp": datetime.utcnow().isoformat(),
                    "data": {
                        "message": "This is a test webhook event",
                        "webhook_id": webhook_id,
                    },
                }

                # Send test webhook
                success = await self._send_webhook(webhook, test_event)

                return {
                    "status": "sent",
                    "success": success,
                    "webhook_id": webhook_id,
                    "test_event": test_event,
                }

            except ValueError as e:
                raise HTTPException(status_code=404, detail=str(e))
            except PermissionError as e:
                raise HTTPException(status_code=403, detail=str(e))
            except Exception as e:
                logger.error(f"Error testing webhook: {e}")
                raise HTTPException(status_code=500, detail="Internal server error")

        @app.websocket("/api/v1/events/stream")
        async def event_stream(
            websocket: WebSocket,
            token: str = Query(..., description="Authentication token"),
        ):
            """WebSocket endpoint for real-time event streaming."""
            # Authenticate
            user_info = await self.security.authenticate_user(
                {"type": "jwt", "token": token}
            )

            if not user_info:
                await websocket.close(code=4001, reason="Unauthorized")
                return

            await websocket.accept()
            self._websocket_connections.append(websocket)

            try:
                # Send initial connection message
                await websocket.send_json(
                    {
                        "event": "connection.established",
                        "timestamp": datetime.utcnow().isoformat(),
                        "user_id": user_info.get("user_id"),
                    }
                )

                # Keep connection alive
                while True:
                    # Wait for messages (heartbeat)
                    try:
                        data = await asyncio.wait_for(
                            websocket.receive_text(), timeout=30.0
                        )

                        # Handle ping/pong
                        if data == "ping":
                            await websocket.send_text("pong")

                    except asyncio.TimeoutError:
                        # Send heartbeat
                        await websocket.send_json(
                            {
                                "event": "heartbeat",
                                "timestamp": datetime.utcnow().isoformat(),
                            }
                        )

            except WebSocketDisconnect:
                self._websocket_connections.remove(websocket)
            except Exception as e:
                logger.error(f"WebSocket error: {e}")
                self._websocket_connections.remove(websocket)

        @app.get("/api/v1/events/types")
        async def get_event_types(current_user: Dict = Depends(self._get_current_user)):
            """Get available event types for webhooks."""
            return {
                "event_types": [
                    {"name": "server.created", "description": "MCP server was created"},
                    {"name": "server.started", "description": "MCP server was started"},
                    {"name": "server.stopped", "description": "MCP server was stopped"},
                    {
                        "name": "server.error",
                        "description": "MCP server encountered an error",
                    },
                    {
                        "name": "tool.discovered",
                        "description": "New tools were discovered",
                    },
                    {"name": "tool.executed", "description": "Tool was executed"},
                    {"name": "tool.failed", "description": "Tool execution failed"},
                    {"name": "security.blocked", "description": "Entity was blocked"},
                    {
                        "name": "security.threat",
                        "description": "Security threat detected",
                    },
                ]
            }

    async def _get_current_user(self, authorization: str = None) -> Dict:
        """Get current user from authorization header."""
        if not authorization:
            if not self.security.config.get("require_authentication", True):
                return {"user_id": "anonymous", "roles": ["user"]}
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

    async def trigger_event(self, event_type: str, data: Dict[str, Any]):
        """Trigger an event for webhooks and WebSocket clients."""
        event = {
            "event": event_type,
            "timestamp": datetime.utcnow().isoformat(),
            "data": data,
        }

        # Add to webhook queue
        await self._event_queue.put(event)

        # Send to WebSocket clients
        disconnected = []
        for websocket in self._websocket_connections:
            try:
                await websocket.send_json(event)
            except:
                disconnected.append(websocket)

        # Remove disconnected clients
        for websocket in disconnected:
            self._websocket_connections.remove(websocket)

    async def _process_webhook_events(self):
        """Process webhook events from queue."""
        while True:
            try:
                # Get event from queue
                event = await self._event_queue.get()

                # Find matching webhooks
                for webhook_id, webhook in self._webhooks.items():
                    if webhook["active"] and event["event"] in webhook["events"]:
                        # Send webhook asynchronously
                        asyncio.create_task(self._send_webhook(webhook, event))

            except Exception as e:
                logger.error(f"Error processing webhook event: {e}")

    async def _send_webhook(
        self, webhook: Dict[str, Any], event: Dict[str, Any]
    ) -> bool:
        """Send webhook HTTP request."""
        try:
            # Prepare headers
            headers = webhook["headers"].copy()
            headers["Content-Type"] = "application/json"
            headers["X-MCP-Event"] = event["event"]
            headers["X-MCP-Signature"] = self._generate_signature(
                webhook["secret"], event
            )

            # Send request
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    webhook["url"],
                    json=event,
                    headers=headers,
                    timeout=aiohttp.ClientTimeout(total=30),
                ) as response:
                    success = response.status < 400

                    # Update webhook stats
                    webhook["last_triggered"] = datetime.utcnow()
                    if success:
                        webhook["success_count"] += 1
                    else:
                        webhook["failure_count"] += 1

                    return success

        except Exception as e:
            logger.error(f"Error sending webhook: {e}")
            webhook["failure_count"] += 1
            return False

    def _generate_signature(self, secret: str, payload: Dict[str, Any]) -> str:
        """Generate HMAC signature for webhook payload."""
        import hashlib
        import hmac
        import json

        message = json.dumps(payload, sort_keys=True).encode()
        signature = hmac.new(secret.encode(), message, hashlib.sha256).hexdigest()

        return f"sha256={signature}"
