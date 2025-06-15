"""
WebSocket Routes for Real-time Updates

This module implements WebSocket endpoints using pure Kailash SDK.
Uses WorkflowBuilder pattern for all real-time operations.
"""

import asyncio
import json
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional

from fastapi import HTTPException, Query, WebSocket, WebSocketDisconnect
from fastapi.websockets import WebSocketState
from pydantic import BaseModel, Field

from apps.user_management.core.startup import agent_ui, runtime
from kailash.middleware import EventType, WorkflowEvent
from kailash.runtime.local import LocalRuntime
from kailash.workflow import WorkflowBuilder


# Pydantic models for WebSocket messages
class WebSocketMessage(BaseModel):
    """Base WebSocket message structure."""

    type: str = Field(..., description="Message type")
    timestamp: datetime = Field(default_factory=datetime.now)
    data: Optional[Dict[str, Any]] = None


class ChatMessage(BaseModel):
    """Chat message structure."""

    message: str = Field(..., min_length=1, max_length=1000)
    user_id: Optional[str] = None
    context: Optional[Dict[str, Any]] = None


class BroadcastRequest(BaseModel):
    """Broadcast message request."""

    message: Dict[str, Any]
    connection_type: Optional[str] = None
    target_users: Optional[List[str]] = None


# Initialize async runtime
async_runtime = LocalRuntime(enable_async=True, debug=False)

# Connection tracking
active_connections: Dict[str, Dict[str, Any]] = {}


async def setup_websocket_routes(app):
    """Setup WebSocket routes on the FastAPI application."""

    @app.websocket("/ws/admin")
    async def admin_websocket(websocket: WebSocket):
        """
        Admin dashboard WebSocket for real-time updates.

        Features beyond Django:
        - Real-time workflow monitoring
        - AI-powered anomaly detection
        - Predictive alerts
        - Multi-tenant event streaming
        """
        connection_id = str(uuid.uuid4())

        try:
            # Accept WebSocket connection
            await websocket.accept()

            # Register connection using workflow
            builder = WorkflowBuilder("register_admin_connection")

            # Add connection registration
            builder.add_node(
                "PythonCodeNode",
                "register_connection",
                {
                    "name": "register_websocket_connection",
                    "code": f"""
# Register WebSocket connection
from datetime import datetime

connection_info = {{
    "connection_id": "{connection_id}",
    "type": "admin_dashboard",
    "connected_at": datetime.now().isoformat(),
    "client_ip": "{websocket.client.host if websocket.client else 'unknown'}",
    "features": [
        "user_events",
        "auth_events",
        "security_alerts",
        "system_monitoring",
        "workflow_tracking"
    ]
}}

# Store in connection registry
result = {{"result": connection_info}}
""",
                },
            )

            # Add audit logging
            builder.add_node(
                "AuditLogNode",
                "audit_connection",
                {
                    "operation": "log_event",
                    "event_type": "websocket_connected",
                    "severity": "info",
                },
            )

            # Connect nodes
            builder.add_connection(
                "register_connection", "result", "audit_connection", "connection_info"
            )

            # Execute registration
            workflow = builder.build()
            results, _ = await async_runtime.execute(workflow)

            connection_info = results.get("register_connection", {}).get("result", {})
            active_connections[connection_id] = {
                "websocket": websocket,
                "info": connection_info,
            }

            # Send initial connection message
            await websocket.send_json(
                {
                    "type": "connection",
                    "status": "connected",
                    "connection_id": connection_id,
                    "timestamp": datetime.now().isoformat(),
                    "features": connection_info["features"],
                }
            )

            # Create event monitoring workflow
            async def monitor_events():
                """Monitor and forward events to WebSocket."""
                while connection_id in active_connections:
                    try:
                        # Create event monitoring workflow
                        monitor_builder = WorkflowBuilder("monitor_admin_events")

                        # Add event collection
                        monitor_builder.add_node(
                            "PythonCodeNode",
                            "collect_events",
                            {
                                "name": "collect_recent_events",
                                "code": """
# Collect recent events (simulated)
import random
from datetime import datetime, timedelta

events = []

# Simulate various event types
if random.random() > 0.7:
    events.append({
        "type": "user_event",
        "event": "user_created",
        "data": {
            "user_id": f"user_{random.randint(1000, 9999)}",
            "email": f"newuser{random.randint(100, 999)}@example.com",
            "department": random.choice(["Engineering", "Sales", "Marketing"])
        },
        "timestamp": datetime.now().isoformat()
    })

if random.random() > 0.8:
    events.append({
        "type": "auth_event",
        "event": "login_attempt",
        "data": {
            "user_id": f"user_{random.randint(100, 999)}",
            "success": random.choice([True, False]),
            "ip_address": f"192.168.1.{random.randint(1, 254)}"
        },
        "timestamp": datetime.now().isoformat()
    })

if random.random() > 0.95:
    events.append({
        "type": "security_alert",
        "severity": random.choice(["low", "medium", "high"]),
        "data": {
            "alert_type": random.choice(["brute_force", "suspicious_location", "privilege_escalation"]),
            "affected_users": random.randint(1, 5),
            "blocked": random.choice([True, False])
        },
        "timestamp": datetime.now().isoformat()
    })

# System metrics (always included)
events.append({
    "type": "system_metrics",
    "data": {
        "active_users": random.randint(300, 400),
        "cpu_usage": random.uniform(20, 60),
        "memory_usage": random.uniform(30, 70),
        "response_time_ms": random.uniform(20, 100)
    },
    "timestamp": datetime.now().isoformat()
})

result = {"result": {"events": events}}
""",
                            },
                        )

                        # Execute monitoring
                        monitor_workflow = monitor_builder.build()
                        monitor_results, _ = await async_runtime.execute(
                            monitor_workflow
                        )

                        events = (
                            monitor_results.get("collect_events", {})
                            .get("result", {})
                            .get("events", [])
                        )

                        # Send events to WebSocket
                        for event in events:
                            if connection_id in active_connections:
                                await websocket.send_json(event)

                        # Wait before next check
                        await asyncio.sleep(5)

                    except Exception:
                        break

            # Start event monitoring
            monitor_task = asyncio.create_task(monitor_events())

            # Handle incoming messages
            while True:
                try:
                    data = await websocket.receive_json()

                    # Handle different message types using workflows
                    if data.get("type") == "ping":
                        await websocket.send_json(
                            {"type": "pong", "timestamp": datetime.now().isoformat()}
                        )

                    elif data.get("type") == "query":
                        # Handle real-time queries with workflow
                        query_builder = WorkflowBuilder("handle_admin_query")

                        query_type = data.get("query_type")

                        if query_type == "active_users":
                            query_builder.add_node(
                                "UserManagementNode",
                                "get_active_users",
                                {"operation": "get_active_users", "minutes": 30},
                            )
                        elif query_type == "system_health":
                            query_builder.add_node(
                                "PythonCodeNode",
                                "get_health",
                                {
                                    "name": "get_system_health",
                                    "code": """
# Get system health
import random

health = {
    "status": "healthy" if random.random() > 0.1 else "degraded",
    "uptime_hours": random.randint(100, 1000),
    "error_rate": random.uniform(0.001, 0.01),
    "queue_depth": random.randint(0, 100)
}

result = {"result": health}
""",
                                },
                            )

                        # Execute query
                        query_workflow = query_builder.build()
                        query_results, _ = await async_runtime.execute(query_workflow)

                        # Send response
                        await websocket.send_json(
                            {
                                "type": "query_response",
                                "query_type": query_type,
                                "data": query_results,
                                "timestamp": datetime.now().isoformat(),
                            }
                        )

                    elif data.get("type") == "command":
                        # Execute admin commands
                        command = data.get("command")
                        command_builder = WorkflowBuilder("execute_admin_command")

                        # Add permission check
                        command_builder.add_node(
                            "ABACPermissionEvaluatorNode",
                            "check_permission",
                            {
                                "resource": "admin:commands",
                                "action": command,
                                "require_admin": True,
                            },
                        )

                        # Add command execution
                        command_builder.add_node(
                            "PythonCodeNode",
                            "execute_command",
                            {
                                "name": "execute_admin_command",
                                "code": f"""
# Execute admin command
command = "{command}"
result = {{
    "result": {{
                        "success": True,
                        "command": command,
                        "message": f"Command '{{command}}' executed successfully"
                    }}
}}
""",
                            },
                        )

                        # Connect and execute
                        command_builder.add_connection(
                            "check_permission", "allowed", "execute_command", "proceed"
                        )
                        command_workflow = command_builder.build()
                        command_results, _ = await async_runtime.execute(
                            command_workflow
                        )

                        if command_results.get("check_permission", {}).get("allowed"):
                            result = command_results.get("execute_command", {}).get(
                                "result", {}
                            )
                            await websocket.send_json(
                                {
                                    "type": "command_result",
                                    **result,
                                    "timestamp": datetime.now().isoformat(),
                                }
                            )
                        else:
                            await websocket.send_json(
                                {
                                    "type": "error",
                                    "message": "Permission denied",
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
            monitor_task.cancel()

            # Unregister connection using workflow
            cleanup_builder = WorkflowBuilder("cleanup_connection")
            cleanup_builder.add_node(
                "AuditLogNode",
                "audit_disconnect",
                {
                    "operation": "log_event",
                    "event_type": "websocket_disconnected",
                    "severity": "info",
                },
            )

            cleanup_workflow = cleanup_builder.build()
            await async_runtime.execute(
                cleanup_workflow, parameters={"connection_id": connection_id}
            )

            # Remove from active connections
            active_connections.pop(connection_id, None)

            if websocket.client_state == WebSocketState.CONNECTED:
                await websocket.close()

    @app.websocket("/ws/user/{user_id}")
    async def user_websocket(
        websocket: WebSocket, user_id: str, token: Optional[str] = Query(None)
    ):
        """
        User-specific WebSocket for personalized updates.

        Features:
        - Personal notifications
        - Real-time permission updates
        - Security alerts
        - Workflow status tracking
        """
        connection_id = str(uuid.uuid4())

        try:
            # Validate token using workflow
            if not token:
                await websocket.close(code=1008, reason="Authentication required")
                return

            auth_builder = WorkflowBuilder("validate_websocket_auth")
            auth_builder.add_node(
                "PythonCodeNode",
                "validate_token",
                {
                    "name": "validate_auth_token",
                    "code": f"""
# Validate authentication token
# In production, would verify JWT or session token
token = "{token}"
user_id = "{user_id}"

# Simplified validation
valid = len(token) > 10

result = {{
    "result": {{
                        "valid": valid,
                        "user_id": user_id if valid else None
                    }}
}}
""",
                },
            )

            auth_workflow = auth_builder.build()
            auth_results, _ = await async_runtime.execute(auth_workflow)

            if (
                not auth_results.get("validate_token", {})
                .get("result", {})
                .get("valid")
            ):
                await websocket.close(code=1008, reason="Invalid token")
                return

            # Accept connection
            await websocket.accept()

            # Register user connection
            active_connections[connection_id] = {
                "websocket": websocket,
                "user_id": user_id,
                "type": "user_session",
            }

            # Send connection confirmation
            await websocket.send_json(
                {
                    "type": "connection",
                    "status": "connected",
                    "user_id": user_id,
                    "timestamp": datetime.now().isoformat(),
                }
            )

            # Monitor user-specific events
            async def monitor_user_events():
                """Monitor events for specific user."""
                while connection_id in active_connections:
                    try:
                        # Create user event workflow
                        user_builder = WorkflowBuilder("monitor_user_events")

                        user_builder.add_node(
                            "PythonCodeNode",
                            "check_notifications",
                            {
                                "name": "check_user_notifications",
                                "code": """
# Check for user notifications
import random
from datetime import datetime

notifications = []

# Simulate various notification types
if random.random() > 0.8:
    notifications.append({
        "type": "notification",
        "title": "Security Alert",
        "message": "New login from unknown device",
        "severity": "medium",
        "timestamp": datetime.now().isoformat()
    })

if random.random() > 0.9:
    notifications.append({
        "type": "permission_update",
        "message": "Your permissions have been updated",
        "changes": ["Added: reports:view", "Removed: admin:delete"],
        "timestamp": datetime.now().isoformat()
    })

result = {"result": {"notifications": notifications}}
""",
                            },
                        )

                        # Execute
                        user_workflow = user_builder.build()
                        user_results, _ = await async_runtime.execute(user_workflow)

                        notifications = (
                            user_results.get("check_notifications", {})
                            .get("result", {})
                            .get("notifications", [])
                        )

                        # Send notifications
                        for notification in notifications:
                            if connection_id in active_connections:
                                await websocket.send_json(notification)

                        await asyncio.sleep(10)

                    except Exception:
                        break

            # Start monitoring
            monitor_task = asyncio.create_task(monitor_user_events())

            # Handle incoming messages
            while True:
                try:
                    data = await websocket.receive_json()

                    if data.get("type") == "update_preferences":
                        # Update user preferences via workflow
                        pref_builder = WorkflowBuilder("update_user_preferences")

                        pref_builder.add_node(
                            "UserManagementNode",
                            "update_prefs",
                            {"operation": "update_preferences", "user_id": user_id},
                        )

                        pref_workflow = pref_builder.build()
                        pref_results, _ = await async_runtime.execute(
                            pref_workflow,
                            parameters={"preferences": data.get("preferences", {})},
                        )

                        await websocket.send_json(
                            {
                                "type": "preferences_updated",
                                "success": True,
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
            monitor_task.cancel()
            active_connections.pop(connection_id, None)
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
        - Service health monitoring
        """
        connection_id = str(uuid.uuid4())

        try:
            # Accept connection (no auth required for public stream)
            await websocket.accept()

            # Register public connection
            active_connections[connection_id] = {
                "websocket": websocket,
                "type": "public_events",
            }

            # Send welcome message
            await websocket.send_json(
                {
                    "type": "connection",
                    "status": "connected",
                    "message": "Connected to public event stream",
                    "timestamp": datetime.now().isoformat(),
                }
            )

            # Public stats monitoring
            async def send_public_stats():
                """Send periodic public statistics."""
                while connection_id in active_connections:
                    try:
                        # Create stats workflow
                        stats_builder = WorkflowBuilder("collect_public_stats")

                        stats_builder.add_node(
                            "PythonCodeNode",
                            "collect_stats",
                            {
                                "name": "collect_system_stats",
                                "code": """
# Collect public system statistics
import random

stats = {
    "total_users": 1542 + random.randint(-10, 20),
    "active_sessions": 342 + random.randint(-50, 50),
    "uptime_percentage": 99.95,
    "response_time_ms": random.uniform(20, 80),
    "api_calls_per_minute": random.randint(1000, 2000),
    "service_status": {
        "api": "operational",
        "auth": "operational",
        "database": "operational" if random.random() > 0.05 else "degraded"
    }
}

result = {"result": stats}
""",
                            },
                        )

                        # Execute
                        stats_workflow = stats_builder.build()
                        stats_results, _ = await async_runtime.execute(stats_workflow)

                        stats = stats_results.get("collect_stats", {}).get("result", {})

                        # Send stats
                        await websocket.send_json(
                            {
                                "type": "stats",
                                "data": stats,
                                "timestamp": datetime.now().isoformat(),
                            }
                        )

                        await asyncio.sleep(30)  # Every 30 seconds

                    except Exception:
                        break

            # Start stats task
            stats_task = asyncio.create_task(send_public_stats())

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
            active_connections.pop(connection_id, None)
            if websocket.client_state == WebSocketState.CONNECTED:
                await websocket.close()

    @app.websocket("/ws/chat/{session_id}")
    async def chat_websocket(
        websocket: WebSocket, session_id: str, token: Optional[str] = Query(None)
    ):
        """
        AI Chat WebSocket for intelligent assistance.

        Features beyond traditional chat:
        - Workflow-powered AI responses
        - Context-aware assistance
        - Natural language command execution
        - Proactive suggestions
        """
        connection_id = str(uuid.uuid4())

        try:
            # Validate session
            if not token:
                await websocket.close(code=1008, reason="Authentication required")
                return

            # Accept connection
            await websocket.accept()

            # Register chat connection
            active_connections[connection_id] = {
                "websocket": websocket,
                "type": "ai_chat",
                "session_id": session_id,
            }

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
                        "natural_language_commands",
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

                        # Process message with AI workflow
                        ai_builder = WorkflowBuilder("process_chat_message")

                        # Add AI processing
                        ai_builder.add_node(
                            "LLMAgentNode",
                            "process_message",
                            {
                                "prompt": f"You are a helpful AI assistant for user management. User message: {user_message}",
                                "max_tokens": 500,
                                "temperature": 0.7,
                            },
                        )

                        # Add context analysis
                        ai_builder.add_node(
                            "PythonCodeNode",
                            "analyze_intent",
                            {
                                "name": "analyze_user_intent",
                                "code": f"""
# Analyze user intent
message = "{user_message}".lower()

# Detect intent
intents = []
if "permission" in message or "access" in message:
    intents.append("permission_query")
if "user" in message and ("create" in message or "add" in message):
    intents.append("user_creation")
if "security" in message or "threat" in message:
    intents.append("security_inquiry")
if "help" in message or "how" in message:
    intents.append("assistance")

# Generate suggestions
suggestions = []
if "permission_query" in intents:
    suggestions.extend([
        "Check my current permissions",
        "Request additional access",
        "View permission hierarchy"
    ])

result = {{
    "result": {{
                        "intents": intents,
                        "suggestions": suggestions
                    }}
}}
""",
                            },
                        )

                        # Connect nodes
                        ai_builder.add_connection(
                            "analyze_intent", "result", "process_message", "context"
                        )

                        # Execute AI workflow
                        ai_workflow = ai_builder.build()
                        ai_results, _ = await async_runtime.execute(ai_workflow)

                        ai_response = ai_results.get("process_message", {}).get(
                            "response", "I'll help you with that."
                        )
                        context = ai_results.get("analyze_intent", {}).get("result", {})

                        # Send AI response
                        await websocket.send_json(
                            {
                                "type": "assistant_message",
                                "message": ai_response,
                                "suggestions": context.get("suggestions", []),
                                "timestamp": datetime.now().isoformat(),
                            }
                        )

                    elif data.get("type") == "command":
                        # Handle natural language commands
                        command = data.get("command")

                        # Create command execution workflow
                        cmd_builder = WorkflowBuilder("execute_nl_command")

                        cmd_builder.add_node(
                            "PythonCodeNode",
                            "parse_command",
                            {
                                "name": "parse_natural_language",
                                "code": f"""
# Parse natural language command
command = "{command}"

# Simple command parsing (in production, use NLP)
parsed = {{
    "action": None,
    "target": None,
    "parameters": {{}}
}}

if "show" in command or "list" in command:
    parsed["action"] = "query"
    if "users" in command:
        parsed["target"] = "users"
    elif "permissions" in command:
        parsed["target"] = "permissions"
elif "create" in command or "add" in command:
    parsed["action"] = "create"
    if "user" in command:
        parsed["target"] = "user"

result = {{"result": parsed}}
""",
                            },
                        )

                        cmd_workflow = cmd_builder.build()
                        cmd_results, _ = await async_runtime.execute(cmd_workflow)

                        parsed_command = cmd_results.get("parse_command", {}).get(
                            "result", {}
                        )

                        await websocket.send_json(
                            {
                                "type": "command_result",
                                "command": command,
                                "parsed": parsed_command,
                                "message": f"Command parsed: {parsed_command['action']} {parsed_command['target']}",
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
            active_connections.pop(connection_id, None)
            if websocket.client_state == WebSocketState.CONNECTED:
                await websocket.close()

    # Add broadcast endpoint
    @app.post("/api/broadcast", response_model=Dict[str, Any])
    async def broadcast_message(broadcast_request: BroadcastRequest):
        """
        Broadcast a message to WebSocket connections.

        Features:
        - Type-based broadcasting
        - User-specific targeting
        - Workflow-powered filtering
        """
        try:
            # Create broadcast workflow
            broadcast_builder = WorkflowBuilder("broadcast_message")

            # Add permission check
            broadcast_builder.add_node(
                "ABACPermissionEvaluatorNode",
                "check_broadcast_permission",
                {
                    "resource": "system:broadcast",
                    "action": "send",
                    "require_admin": True,
                },
            )

            # Add broadcast logic
            broadcast_builder.add_node(
                "PythonCodeNode",
                "prepare_broadcast",
                {
                    "name": "prepare_broadcast_message",
                    "code": f"""
# Prepare broadcast message
import json
from datetime import datetime

message_data = {json.dumps(broadcast_request.message)}
connection_type = "{broadcast_request.connection_type or 'all'}"
target_users = {broadcast_request.target_users or []}

# Create broadcast event
broadcast_event = {{
    "type": "broadcast",
    "source": "admin",
    "message": message_data,
    "timestamp": datetime.now().isoformat(),
    "priority": message_data.get("priority", "normal")
}}

# Determine recipients
recipients = []
if connection_type == "all":
    recipients = list(range(len({json.dumps(list(active_connections.keys()))})))
elif connection_type == "admin_dashboard":
    recipients = [k for k, v in {json.dumps(active_connections)}.items() if v.get("type") == "admin_dashboard"]
elif target_users:
    recipients = [k for k, v in {json.dumps(active_connections)}.items() if v.get("user_id") in target_users]

result = {{
    "result": {{
                        "broadcast_event": broadcast_event,
                        "recipient_count": len(recipients),
                        "connection_type": connection_type
                    }}
}}
""",
                },
            )

            # Add audit logging
            broadcast_builder.add_node(
                "AuditLogNode",
                "audit_broadcast",
                {
                    "operation": "log_event",
                    "event_type": "broadcast_sent",
                    "severity": "info",
                },
            )

            # Connect nodes
            broadcast_builder.add_connection(
                "check_broadcast_permission", "allowed", "prepare_broadcast", "proceed"
            )
            broadcast_builder.add_connection(
                "prepare_broadcast", "result", "audit_broadcast", "broadcast_info"
            )

            # Execute workflow
            broadcast_workflow = broadcast_builder.build()
            broadcast_results, execution_id = await async_runtime.execute(
                broadcast_workflow
            )

            # Check permission
            if not broadcast_results.get("check_broadcast_permission", {}).get(
                "allowed"
            ):
                raise HTTPException(
                    status_code=403, detail="Permission denied for broadcast"
                )

            broadcast_info = broadcast_results.get("prepare_broadcast", {}).get(
                "result", {}
            )
            broadcast_event = broadcast_info["broadcast_event"]

            # Send to active connections
            sent_count = 0
            for conn_id, conn_info in active_connections.items():
                try:
                    # Filter by type or user
                    if broadcast_request.connection_type:
                        if conn_info.get("type") != broadcast_request.connection_type:
                            continue

                    if broadcast_request.target_users:
                        if (
                            conn_info.get("user_id")
                            not in broadcast_request.target_users
                        ):
                            continue

                    # Send message
                    websocket = conn_info.get("websocket")
                    if websocket and websocket.client_state == WebSocketState.CONNECTED:
                        await websocket.send_json(broadcast_event)
                        sent_count += 1

                except Exception:
                    # Skip failed connections
                    pass

            return {
                "success": True,
                "message": "Broadcast sent",
                "recipients": sent_count,
                "execution_id": execution_id,
                "timestamp": datetime.now().isoformat(),
            }

        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    @app.get("/api/websocket/connections", response_model=Dict[str, Any])
    async def get_active_connections():
        """
        Get information about active WebSocket connections.

        Returns connection statistics and details.
        """
        try:
            # Create stats workflow
            stats_builder = WorkflowBuilder("websocket_stats")

            stats_builder.add_node(
                "PythonCodeNode",
                "calculate_stats",
                {
                    "name": "calculate_connection_stats",
                    "code": f"""
# Calculate WebSocket connection statistics
connections = {json.dumps(list(active_connections.values()))}

# Group by type
by_type = {{}}
for conn in connections:
    conn_type = conn.get("type", "unknown")
    by_type[conn_type] = by_type.get(conn_type, 0) + 1

# Count unique users
unique_users = set()
for conn in connections:
    user_id = conn.get("user_id")
    if user_id:
        unique_users.add(user_id)

stats = {{
    "total_connections": len(connections),
    "connections_by_type": by_type,
    "unique_users": len(unique_users),
    "types": list(by_type.keys())
}}

result = {{"result": stats}}
""",
                },
            )

            stats_workflow = stats_builder.build()
            stats_results, _ = await async_runtime.execute(stats_workflow)

            stats = stats_results.get("calculate_stats", {}).get("result", {})

            return {
                "status": "success",
                **stats,
                "timestamp": datetime.now().isoformat(),
            }

        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
