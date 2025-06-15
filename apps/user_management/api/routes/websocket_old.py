"""
WebSocket Routes for Real-time Updates

This module implements WebSocket endpoints for real-time communication.
Uses RealtimeMiddleware for event streaming and live updates.
"""

import asyncio
import json
from datetime import datetime
from typing import Any, Dict, List, Optional

from fastapi import HTTPException, Query, WebSocket, WebSocketDisconnect
from fastapi.websockets import WebSocketState

from apps.user_management.core.startup import agent_ui, realtime
from kailash.middleware import EventStream, EventType, WorkflowEvent


async def setup_websocket_routes(app):
    """Setup WebSocket routes on the FastAPI application."""

    @app.websocket("/ws/admin")
    async def admin_websocket(websocket: WebSocket):
        """
        Admin dashboard WebSocket for real-time updates.

        Receives:
        - User events (create, update, delete)
        - Authentication events
        - Security alerts
        - System status updates
        """
        try:
            # Accept WebSocket connection
            await websocket.accept()

            # Register connection with RealtimeMiddleware
            connection_id = await realtime.register_connection(
                websocket,
                connection_type="admin_dashboard",
                metadata={
                    "connected_at": datetime.now().isoformat(),
                    "client_ip": (
                        websocket.client.host if websocket.client else "unknown"
                    ),
                },
            )

            # Send initial connection message
            await websocket.send_json(
                {
                    "type": "connection",
                    "status": "connected",
                    "connection_id": connection_id,
                    "timestamp": datetime.now().isoformat(),
                    "features": [
                        "user_events",
                        "auth_events",
                        "security_alerts",
                        "system_status",
                    ],
                }
            )

            # Subscribe to relevant events
            async def handle_user_events(event: WorkflowEvent):
                """Handle user-related events."""
                if event.type in [
                    EventType.USER_CREATED,
                    EventType.USER_UPDATED,
                    EventType.USER_DELETED,
                ]:
                    await websocket.send_json(
                        {
                            "type": "user_event",
                            "event": event.type.value,
                            "data": event.data,
                            "timestamp": event.timestamp.isoformat(),
                        }
                    )

            async def handle_auth_events(event: WorkflowEvent):
                """Handle authentication events."""
                if event.type in [
                    EventType.USER_AUTHENTICATED,
                    EventType.USER_LOGGED_OUT,
                ]:
                    await websocket.send_json(
                        {
                            "type": "auth_event",
                            "event": event.type.value,
                            "data": event.data,
                            "timestamp": event.timestamp.isoformat(),
                        }
                    )

            async def handle_security_events(event: WorkflowEvent):
                """Handle security events."""
                if event.type == EventType.SECURITY_ALERT:
                    await websocket.send_json(
                        {
                            "type": "security_alert",
                            "severity": event.data.get("severity", "medium"),
                            "data": event.data,
                            "timestamp": event.timestamp.isoformat(),
                        }
                    )

            # Subscribe to event streams
            await realtime.event_stream.subscribe("user_events", handle_user_events)
            await realtime.event_stream.subscribe("auth_events", handle_auth_events)
            await realtime.event_stream.subscribe(
                "security_events", handle_security_events
            )

            # Send periodic heartbeat
            async def send_heartbeat():
                while websocket.client_state == WebSocketState.CONNECTED:
                    try:
                        await websocket.send_json(
                            {
                                "type": "heartbeat",
                                "timestamp": datetime.now().isoformat(),
                            }
                        )
                        await asyncio.sleep(30)  # Send heartbeat every 30 seconds
                    except:
                        break

            # Start heartbeat task
            heartbeat_task = asyncio.create_task(send_heartbeat())

            # Handle incoming messages
            while True:
                try:
                    data = await websocket.receive_json()

                    # Handle different message types
                    if data.get("type") == "ping":
                        await websocket.send_json(
                            {"type": "pong", "timestamp": datetime.now().isoformat()}
                        )

                    elif data.get("type") == "subscribe":
                        # Handle subscription requests
                        event_types = data.get("event_types", [])
                        await websocket.send_json(
                            {
                                "type": "subscription_confirmed",
                                "event_types": event_types,
                                "timestamp": datetime.now().isoformat(),
                            }
                        )

                    elif data.get("type") == "query":
                        # Handle real-time queries
                        query_type = data.get("query_type")
                        if query_type == "active_users":
                            # Get active user count
                            await websocket.send_json(
                                {
                                    "type": "query_response",
                                    "query_type": query_type,
                                    "data": {"active_users": 342},  # Mock data
                                    "timestamp": datetime.now().isoformat(),
                                }
                            )

                except WebSocketDisconnect:
                    break
                except Exception as e:
                    await websocket.send_json(
                        {
                            "type": "error",
                            "message": str(e),
                            "timestamp": datetime.now().isoformat(),
                        }
                    )

        except Exception as e:
            print(f"WebSocket error: {e}")
        finally:
            # Cleanup
            heartbeat_task.cancel()
            await realtime.unregister_connection(connection_id)
            if websocket.client_state == WebSocketState.CONNECTED:
                await websocket.close()

    @app.websocket("/ws/user/{user_id}")
    async def user_websocket(
        websocket: WebSocket, user_id: str, token: Optional[str] = Query(None)
    ):
        """
        User-specific WebSocket for personalized updates.

        Receives:
        - Personal notifications
        - Account changes
        - Security alerts for their account
        - Session updates
        """
        try:
            # Validate token (simplified for example)
            if not token:
                await websocket.close(code=1008, reason="Authentication required")
                return

            # Accept connection
            await websocket.accept()

            # Register user connection
            connection_id = await realtime.register_connection(
                websocket,
                connection_type="user_session",
                user_id=user_id,
                metadata={
                    "connected_at": datetime.now().isoformat(),
                    "user_id": user_id,
                },
            )

            # Send connection confirmation
            await websocket.send_json(
                {
                    "type": "connection",
                    "status": "connected",
                    "user_id": user_id,
                    "timestamp": datetime.now().isoformat(),
                }
            )

            # Subscribe to user-specific events
            async def handle_personal_events(event: WorkflowEvent):
                """Handle events for this specific user."""
                event_user_id = event.data.get("user_id")
                if event_user_id == user_id:
                    await websocket.send_json(
                        {
                            "type": "personal_event",
                            "event": event.type.value,
                            "data": event.data,
                            "timestamp": event.timestamp.isoformat(),
                        }
                    )

            # Subscribe to personal events
            await realtime.event_stream.subscribe(
                f"user_{user_id}", handle_personal_events
            )

            # Handle incoming messages
            while True:
                try:
                    data = await websocket.receive_json()

                    if data.get("type") == "update_status":
                        # Handle status updates
                        new_status = data.get("status")
                        await websocket.send_json(
                            {
                                "type": "status_updated",
                                "status": new_status,
                                "timestamp": datetime.now().isoformat(),
                            }
                        )

                except WebSocketDisconnect:
                    break
                except Exception as e:
                    await websocket.send_json(
                        {
                            "type": "error",
                            "message": str(e),
                            "timestamp": datetime.now().isoformat(),
                        }
                    )

        except Exception as e:
            print(f"User WebSocket error: {e}")
        finally:
            await realtime.unregister_connection(connection_id)
            if websocket.client_state == WebSocketState.CONNECTED:
                await websocket.close()

    @app.websocket("/ws/events")
    async def events_websocket(websocket: WebSocket):
        """
        Public event stream WebSocket.

        Provides:
        - System status updates
        - Public announcements
        - General statistics
        """
        try:
            # Accept connection
            await websocket.accept()

            # Register public connection
            connection_id = await realtime.register_connection(
                websocket, connection_type="public_events"
            )

            # Send welcome message
            await websocket.send_json(
                {
                    "type": "connection",
                    "status": "connected",
                    "message": "Connected to public event stream",
                    "timestamp": datetime.now().isoformat(),
                }
            )

            # Subscribe to public events
            async def handle_public_events(event: WorkflowEvent):
                """Handle public events."""
                if event.type == EventType.PUBLIC_ANNOUNCEMENT:
                    await websocket.send_json(
                        {
                            "type": "announcement",
                            "data": event.data,
                            "timestamp": event.timestamp.isoformat(),
                        }
                    )

            await realtime.event_stream.subscribe("public_events", handle_public_events)

            # Send periodic stats
            async def send_stats():
                while websocket.client_state == WebSocketState.CONNECTED:
                    try:
                        await websocket.send_json(
                            {
                                "type": "stats",
                                "data": {
                                    "total_users": 1542,
                                    "active_sessions": 342,
                                    "uptime_percentage": 99.95,
                                },
                                "timestamp": datetime.now().isoformat(),
                            }
                        )
                        await asyncio.sleep(60)  # Every minute
                    except:
                        break

            stats_task = asyncio.create_task(send_stats())

            # Keep connection alive
            while True:
                try:
                    await websocket.receive_text()
                except WebSocketDisconnect:
                    break

        except Exception as e:
            print(f"Events WebSocket error: {e}")
        finally:
            stats_task.cancel()
            await realtime.unregister_connection(connection_id)
            if websocket.client_state == WebSocketState.CONNECTED:
                await websocket.close()

    @app.websocket("/ws/chat/{session_id}")
    async def chat_websocket(
        websocket: WebSocket, session_id: str, token: Optional[str] = Query(None)
    ):
        """
        AI Chat WebSocket for intelligent assistance.

        Features:
        - Real-time AI responses
        - Context-aware conversations
        - Workflow assistance
        - Natural language commands
        """
        try:
            # Validate session
            if not token:
                await websocket.close(code=1008, reason="Authentication required")
                return

            # Accept connection
            await websocket.accept()

            # Initialize AI chat session
            chat_session = await agent_ui.ai_chat.create_chat_session(
                session_id,
                metadata={
                    "websocket": True,
                    "connected_at": datetime.now().isoformat(),
                },
            )

            # Send welcome message
            await websocket.send_json(
                {
                    "type": "chat_connected",
                    "session_id": session_id,
                    "assistant": "Kailash AI Assistant",
                    "capabilities": [
                        "user_management",
                        "permission_queries",
                        "workflow_assistance",
                        "security_guidance",
                    ],
                    "timestamp": datetime.now().isoformat(),
                }
            )

            # Handle chat messages
            while True:
                try:
                    data = await websocket.receive_json()

                    if data.get("type") == "message":
                        user_message = data.get("message", "")

                        # Send typing indicator
                        await websocket.send_json(
                            {"type": "typing", "timestamp": datetime.now().isoformat()}
                        )

                        # Process message with AI
                        response = await agent_ui.ai_chat.process_message(
                            chat_session,
                            user_message,
                            context={
                                "user_id": data.get("user_id"),
                                "current_page": data.get("current_page"),
                            },
                        )

                        # Send AI response
                        await websocket.send_json(
                            {
                                "type": "assistant_message",
                                "message": response.get("message"),
                                "suggestions": response.get("suggestions", []),
                                "actions": response.get("actions", []),
                                "timestamp": datetime.now().isoformat(),
                            }
                        )

                    elif data.get("type") == "command":
                        # Handle natural language commands
                        command = data.get("command")
                        result = await agent_ui.ai_chat.execute_command(
                            chat_session, command
                        )

                        await websocket.send_json(
                            {
                                "type": "command_result",
                                "command": command,
                                "result": result,
                                "timestamp": datetime.now().isoformat(),
                            }
                        )

                except WebSocketDisconnect:
                    break
                except Exception as e:
                    await websocket.send_json(
                        {
                            "type": "error",
                            "message": f"Chat error: {str(e)}",
                            "timestamp": datetime.now().isoformat(),
                        }
                    )

        except Exception as e:
            print(f"Chat WebSocket error: {e}")
        finally:
            # Cleanup chat session
            await agent_ui.ai_chat.close_chat_session(chat_session)
            if websocket.client_state == WebSocketState.CONNECTED:
                await websocket.close()

    # Add broadcast endpoint for testing
    @app.post("/api/broadcast")
    async def broadcast_message(
        message: Dict[str, Any], connection_type: Optional[str] = None
    ):
        """
        Broadcast a message to WebSocket connections.

        Useful for testing and system-wide announcements.
        """
        try:
            event = WorkflowEvent(
                type=EventType.PUBLIC_ANNOUNCEMENT,
                workflow_id="broadcast",
                execution_id="manual",
                data=message,
            )

            if connection_type:
                await realtime.broadcast_to_type(connection_type, message)
            else:
                await realtime.broadcast_event(event)

            return {
                "message": "Broadcast sent",
                "recipients": await realtime.get_connection_count(connection_type),
                "timestamp": datetime.now().isoformat(),
            }

        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
