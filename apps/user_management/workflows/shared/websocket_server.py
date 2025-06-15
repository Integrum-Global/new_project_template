#!/usr/bin/env python3
"""
User Management System - WebSocket Server

This module provides WebSocket support for real-time features including:
- Live notifications
- Activity monitoring
- Collaborative features
- Real-time updates
"""

import os
import sys
import json
import asyncio
import logging
from datetime import datetime
from typing import Dict, Set, Optional, Any
from contextlib import asynccontextmanager

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# FastAPI and WebSocket imports
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

# JWT for authentication
import jwt
from jwt.exceptions import InvalidTokenError

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ConnectionManager:
    """Manages WebSocket connections and message broadcasting"""
    
    def __init__(self):
        # Active connections by user_id
        self.active_connections: Dict[str, Set[WebSocket]] = {}
        # User session data
        self.user_sessions: Dict[str, Dict[str, Any]] = {}
        # Channel subscriptions
        self.channel_subscriptions: Dict[str, Set[str]] = {}
        
    async def connect(self, websocket: WebSocket, user_id: str, session_data: Dict[str, Any]):
        """Accept new WebSocket connection"""
        await websocket.accept()
        
        # Add to active connections
        if user_id not in self.active_connections:
            self.active_connections[user_id] = set()
        self.active_connections[user_id].add(websocket)
        
        # Store session data
        self.user_sessions[user_id] = session_data
        
        # Send welcome message
        await self.send_personal_message(
            user_id,
            {
                "type": "connection",
                "status": "connected",
                "message": "Welcome to User Management real-time system",
                "timestamp": datetime.now().isoformat(),
                "session_id": session_data.get("session_id")
            }
        )
        
        logger.info(f"User {user_id} connected via WebSocket")
        
    async def disconnect(self, websocket: WebSocket, user_id: str):
        """Remove WebSocket connection"""
        if user_id in self.active_connections:
            self.active_connections[user_id].discard(websocket)
            if not self.active_connections[user_id]:
                del self.active_connections[user_id]
                del self.user_sessions[user_id]
                
                # Clean up channel subscriptions
                for channel, users in self.channel_subscriptions.items():
                    users.discard(user_id)
                    
        logger.info(f"User {user_id} disconnected from WebSocket")
        
    async def send_personal_message(self, user_id: str, message: Dict[str, Any]):
        """Send message to specific user"""
        if user_id in self.active_connections:
            disconnected = set()
            for connection in self.active_connections[user_id]:
                try:
                    await connection.send_json(message)
                except Exception as e:
                    logger.error(f"Error sending message to {user_id}: {str(e)}")
                    disconnected.add(connection)
                    
            # Clean up disconnected connections
            for conn in disconnected:
                self.active_connections[user_id].discard(conn)
                
    async def broadcast_to_channel(self, channel: str, message: Dict[str, Any], exclude_user: Optional[str] = None):
        """Broadcast message to all users in a channel"""
        if channel in self.channel_subscriptions:
            for user_id in self.channel_subscriptions[channel]:
                if user_id != exclude_user:
                    await self.send_personal_message(user_id, message)
                    
    async def broadcast_to_department(self, department: str, message: Dict[str, Any]):
        """Broadcast message to all users in a department"""
        for user_id, session in self.user_sessions.items():
            if session.get("department") == department:
                await self.send_personal_message(user_id, message)
                
    async def broadcast_to_role(self, role: str, message: Dict[str, Any]):
        """Broadcast message to all users with specific role"""
        for user_id, session in self.user_sessions.items():
            if role in session.get("roles", []):
                await self.send_personal_message(user_id, message)
                
    async def subscribe_to_channel(self, user_id: str, channel: str):
        """Subscribe user to a channel"""
        if channel not in self.channel_subscriptions:
            self.channel_subscriptions[channel] = set()
        self.channel_subscriptions[channel].add(user_id)
        
        await self.send_personal_message(
            user_id,
            {
                "type": "channel_subscription",
                "channel": channel,
                "status": "subscribed",
                "timestamp": datetime.now().isoformat()
            }
        )
        
    async def unsubscribe_from_channel(self, user_id: str, channel: str):
        """Unsubscribe user from a channel"""
        if channel in self.channel_subscriptions:
            self.channel_subscriptions[channel].discard(user_id)
            
        await self.send_personal_message(
            user_id,
            {
                "type": "channel_subscription",
                "channel": channel,
                "status": "unsubscribed",
                "timestamp": datetime.now().isoformat()
            }
        )
        
    def get_online_users(self) -> Dict[str, Any]:
        """Get list of online users with their session data"""
        return {
            user_id: {
                "user_id": user_id,
                "user_type": session.get("user_type"),
                "department": session.get("department"),
                "connected_at": session.get("connected_at"),
                "connection_count": len(self.active_connections.get(user_id, []))
            }
            for user_id, session in self.user_sessions.items()
        }


# Create connection manager
manager = ConnectionManager()


# Lifespan management
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager"""
    # Startup
    logger.info("Starting WebSocket Server...")
    
    # Initialize background tasks
    app.state.background_tasks = set()
    
    # Start periodic tasks
    task = asyncio.create_task(periodic_health_check())
    app.state.background_tasks.add(task)
    
    yield
    
    # Shutdown
    logger.info("Shutting down WebSocket Server...")
    
    # Cancel background tasks
    for task in app.state.background_tasks:
        task.cancel()
        

# Create FastAPI app for WebSocket
app = FastAPI(
    title="User Management WebSocket Server",
    description="Real-time communication for user management system",
    version="1.0.0",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Authentication
async def verify_websocket_token(token: str) -> Dict[str, Any]:
    """Verify WebSocket authentication token"""
    try:
        # In production, use proper secret key management
        secret_key = os.getenv("JWT_SECRET_KEY", "your-secret-key")
        payload = jwt.decode(token, secret_key, algorithms=["HS256"])
        
        return {
            "user_id": payload.get("sub"),
            "user_type": payload.get("user_type", "user"),
            "department": payload.get("department"),
            "roles": payload.get("roles", []),
            "permissions": payload.get("permissions", []),
            "session_id": f"ws_session_{int(datetime.now().timestamp())}",
            "connected_at": datetime.now().isoformat()
        }
        
    except InvalidTokenError as e:
        logger.error(f"Invalid WebSocket token: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication token"
        )


# WebSocket endpoint
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket, token: str):
    """Main WebSocket endpoint with token authentication"""
    try:
        # Verify authentication
        session_data = await verify_websocket_token(token)
        user_id = session_data["user_id"]
        
        if not user_id:
            await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
            return
            
        # Connect user
        await manager.connect(websocket, user_id, session_data)
        
        # Handle incoming messages
        while True:
            data = await websocket.receive_text()
            message = json.loads(data)
            
            await handle_websocket_message(user_id, message, session_data)
            
    except WebSocketDisconnect:
        if 'user_id' in locals():
            await manager.disconnect(websocket, user_id)
            
            # Notify others about disconnection
            await manager.broadcast_to_department(
                session_data.get("department", ""),
                {
                    "type": "user_status",
                    "user_id": user_id,
                    "status": "offline",
                    "timestamp": datetime.now().isoformat()
                }
            )
            
    except Exception as e:
        logger.error(f"WebSocket error: {str(e)}")
        if 'user_id' in locals():
            await manager.disconnect(websocket, user_id)


async def handle_websocket_message(user_id: str, message: Dict[str, Any], session_data: Dict[str, Any]):
    """Handle incoming WebSocket messages"""
    msg_type = message.get("type")
    
    if msg_type == "ping":
        # Respond to ping
        await manager.send_personal_message(
            user_id,
            {
                "type": "pong",
                "timestamp": datetime.now().isoformat()
            }
        )
        
    elif msg_type == "subscribe":
        # Subscribe to channel
        channel = message.get("channel")
        if channel:
            await manager.subscribe_to_channel(user_id, channel)
            
    elif msg_type == "unsubscribe":
        # Unsubscribe from channel
        channel = message.get("channel")
        if channel:
            await manager.unsubscribe_from_channel(user_id, channel)
            
    elif msg_type == "broadcast":
        # Broadcast message to channel (check permissions)
        if "broadcast_message" in session_data.get("permissions", []):
            channel = message.get("channel")
            content = message.get("content")
            
            if channel and content:
                await manager.broadcast_to_channel(
                    channel,
                    {
                        "type": "channel_message",
                        "channel": channel,
                        "from_user": user_id,
                        "content": content,
                        "timestamp": datetime.now().isoformat()
                    },
                    exclude_user=user_id
                )
                
    elif msg_type == "notification":
        # Send notification to specific user
        target_user = message.get("target_user")
        notification = message.get("notification")
        
        if target_user and notification:
            await manager.send_personal_message(
                target_user,
                {
                    "type": "notification",
                    "from_user": user_id,
                    "notification": notification,
                    "timestamp": datetime.now().isoformat()
                }
            )
            
    elif msg_type == "activity":
        # Broadcast user activity
        activity = message.get("activity")
        if activity:
            await manager.broadcast_to_department(
                session_data.get("department", ""),
                {
                    "type": "user_activity",
                    "user_id": user_id,
                    "activity": activity,
                    "timestamp": datetime.now().isoformat()
                }
            )
            
    elif msg_type == "get_online_users":
        # Get list of online users
        online_users = manager.get_online_users()
        await manager.send_personal_message(
            user_id,
            {
                "type": "online_users",
                "users": online_users,
                "count": len(online_users),
                "timestamp": datetime.now().isoformat()
            }
        )


# REST endpoints for server-side notifications
@app.post("/notify/user/{user_id}")
async def notify_user(user_id: str, notification: Dict[str, Any]):
    """Send notification to specific user via REST API"""
    await manager.send_personal_message(
        user_id,
        {
            "type": "system_notification",
            "notification": notification,
            "timestamp": datetime.now().isoformat()
        }
    )
    return {"success": True, "message": f"Notification sent to {user_id}"}


@app.post("/notify/department/{department}")
async def notify_department(department: str, notification: Dict[str, Any]):
    """Send notification to all users in department"""
    await manager.broadcast_to_department(
        department,
        {
            "type": "department_notification",
            "notification": notification,
            "timestamp": datetime.now().isoformat()
        }
    )
    return {"success": True, "message": f"Notification sent to {department} department"}


@app.post("/notify/role/{role}")
async def notify_role(role: str, notification: Dict[str, Any]):
    """Send notification to all users with specific role"""
    await manager.broadcast_to_role(
        role,
        {
            "type": "role_notification",
            "notification": notification,
            "timestamp": datetime.now().isoformat()
        }
    )
    return {"success": True, "message": f"Notification sent to all {role} users"}


@app.get("/status")
async def get_server_status():
    """Get WebSocket server status"""
    online_users = manager.get_online_users()
    
    return {
        "status": "online",
        "online_users": len(online_users),
        "active_connections": sum(len(conns) for conns in manager.active_connections.values()),
        "channels": list(manager.channel_subscriptions.keys()),
        "server_time": datetime.now().isoformat()
    }


# Background tasks
async def periodic_health_check():
    """Periodic health check and cleanup"""
    while True:
        try:
            await asyncio.sleep(30)  # Every 30 seconds
            
            # Send heartbeat to all connected users
            heartbeat_message = {
                "type": "heartbeat",
                "server_time": datetime.now().isoformat(),
                "online_users": len(manager.get_online_users())
            }
            
            for user_id in list(manager.active_connections.keys()):
                await manager.send_personal_message(user_id, heartbeat_message)
                
        except asyncio.CancelledError:
            break
        except Exception as e:
            logger.error(f"Health check error: {str(e)}")


# Notification types for different events
class NotificationTypes:
    """Standard notification types"""
    
    # User notifications
    PROFILE_UPDATED = "profile_updated"
    PASSWORD_CHANGED = "password_changed"
    MFA_ENABLED = "mfa_enabled"
    
    # Access notifications
    ACCESS_GRANTED = "access_granted"
    ACCESS_REVOKED = "access_revoked"
    ACCESS_EXPIRING = "access_expiring"
    
    # Team notifications
    TEAM_MEMBER_ADDED = "team_member_added"
    TEAM_MEMBER_REMOVED = "team_member_removed"
    TEAM_GOAL_UPDATED = "team_goal_updated"
    
    # Approval notifications
    APPROVAL_REQUIRED = "approval_required"
    APPROVAL_GRANTED = "approval_granted"
    APPROVAL_DENIED = "approval_denied"
    
    # Security notifications
    SECURITY_ALERT = "security_alert"
    SUSPICIOUS_ACTIVITY = "suspicious_activity"
    POLICY_VIOLATION = "policy_violation"
    
    # System notifications
    SYSTEM_MAINTENANCE = "system_maintenance"
    SYSTEM_UPDATE = "system_update"
    BACKUP_COMPLETE = "backup_complete"


# Example notification builders
def build_approval_notification(request_id: str, requester: str, resource: str) -> Dict[str, Any]:
    """Build approval required notification"""
    return {
        "type": NotificationTypes.APPROVAL_REQUIRED,
        "priority": "high",
        "title": "Approval Required",
        "message": f"{requester} has requested access to {resource}",
        "data": {
            "request_id": request_id,
            "requester": requester,
            "resource": resource
        },
        "actions": [
            {"label": "Approve", "action": "approve", "style": "primary"},
            {"label": "Deny", "action": "deny", "style": "danger"},
            {"label": "View Details", "action": "view", "style": "default"}
        ]
    }


def build_security_alert(alert_type: str, details: str, severity: str = "medium") -> Dict[str, Any]:
    """Build security alert notification"""
    return {
        "type": NotificationTypes.SECURITY_ALERT,
        "priority": "urgent" if severity == "high" else "high",
        "title": f"Security Alert: {alert_type}",
        "message": details,
        "data": {
            "alert_type": alert_type,
            "severity": severity,
            "timestamp": datetime.now().isoformat()
        },
        "actions": [
            {"label": "Investigate", "action": "investigate", "style": "primary"},
            {"label": "Dismiss", "action": "dismiss", "style": "default"}
        ]
    }


# Main entry point
if __name__ == "__main__":
    # Get configuration from environment
    host = os.getenv("WEBSOCKET_HOST", "0.0.0.0")
    port = int(os.getenv("WEBSOCKET_PORT", "8001"))
    
    # Run the WebSocket server
    uvicorn.run(
        "websocket_server:app",
        host=host,
        port=port,
        reload=True if os.getenv("ENVIRONMENT") == "development" else False,
        log_level="info"
    )