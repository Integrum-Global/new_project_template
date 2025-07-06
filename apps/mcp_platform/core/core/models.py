"""
MCP Data Models

This module defines the core data models for MCP entities.
"""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional


class ServerStatus(Enum):
    """MCP Server status enumeration."""

    REGISTERED = "registered"
    STARTING = "starting"
    RUNNING = "running"
    STOPPED = "stopped"
    ERROR = "error"
    UNHEALTHY = "unhealthy"
    MAINTENANCE = "maintenance"


class TransportType(Enum):
    """MCP Transport types."""

    STDIO = "stdio"
    HTTP = "http"
    SSE = "sse"
    WEBSOCKET = "websocket"


class ToolCategory(Enum):
    """Tool categories for organization."""

    DATA = "data"
    ANALYSIS = "analysis"
    GENERATION = "generation"
    TRANSFORMATION = "transformation"
    INTEGRATION = "integration"
    UTILITY = "utility"
    ADMIN = "admin"


@dataclass
class MCPServer:
    """MCP Server model."""

    id: str
    name: str
    transport: str
    config: Dict[str, Any]
    status: ServerStatus = ServerStatus.REGISTERED
    owner_id: Optional[str] = None
    organization_id: Optional[str] = None

    # Timestamps
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    started_at: Optional[datetime] = None
    stopped_at: Optional[datetime] = None
    last_health_check: Optional[datetime] = None
    last_discovery: Optional[datetime] = None

    # Metadata
    description: Optional[str] = None
    tags: List[str] = field(default_factory=list)
    labels: Dict[str, str] = field(default_factory=dict)

    # Status info
    tool_count: int = 0
    resource_count: int = 0
    error_message: Optional[str] = None
    health_status: Dict[str, Any] = field(default_factory=dict)

    # Configuration
    auto_start: bool = False
    auto_discover: bool = True
    max_retries: int = 3
    timeout: int = 30

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "name": self.name,
            "transport": self.transport,
            "config": self.config,
            "status": (
                self.status.value if isinstance(self.status, Enum) else self.status
            ),
            "owner_id": self.owner_id,
            "organization_id": self.organization_id,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "stopped_at": self.stopped_at.isoformat() if self.stopped_at else None,
            "last_health_check": (
                self.last_health_check.isoformat() if self.last_health_check else None
            ),
            "last_discovery": (
                self.last_discovery.isoformat() if self.last_discovery else None
            ),
            "description": self.description,
            "tags": self.tags,
            "labels": self.labels,
            "tool_count": self.tool_count,
            "resource_count": self.resource_count,
            "error_message": self.error_message,
            "health_status": self.health_status,
        }


@dataclass
class MCPTool:
    """MCP Tool model."""

    name: str
    description: str
    server_id: str

    # Schema
    input_schema: Dict[str, Any] = field(default_factory=dict)
    output_schema: Dict[str, Any] = field(default_factory=dict)

    # Metadata
    category: Optional[ToolCategory] = None
    tags: List[str] = field(default_factory=list)
    version: Optional[str] = None

    # Usage info
    execution_count: int = 0
    success_count: int = 0
    failure_count: int = 0
    average_duration_ms: float = 0.0
    last_executed: Optional[datetime] = None

    # Configuration
    timeout: int = 120
    cache_enabled: bool = False
    cache_ttl: int = 3600
    rate_limit: Optional[int] = None
    required_permissions: List[str] = field(default_factory=list)

    # Discovery info
    discovered_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "name": self.name,
            "description": self.description,
            "server_id": self.server_id,
            "input_schema": self.input_schema,
            "output_schema": self.output_schema,
            "category": self.category.value if self.category else None,
            "tags": self.tags,
            "version": self.version,
            "execution_count": self.execution_count,
            "success_count": self.success_count,
            "failure_count": self.failure_count,
            "average_duration_ms": self.average_duration_ms,
            "last_executed": (
                self.last_executed.isoformat() if self.last_executed else None
            ),
            "timeout": self.timeout,
            "cache_enabled": self.cache_enabled,
            "cache_ttl": self.cache_ttl,
            "rate_limit": self.rate_limit,
            "required_permissions": self.required_permissions,
            "discovered_at": self.discovered_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }


@dataclass
class MCPResource:
    """MCP Resource model."""

    uri: str
    name: str
    server_id: str

    # Metadata
    description: Optional[str] = None
    mime_type: Optional[str] = None
    size_bytes: Optional[int] = None

    # Access info
    read_count: int = 0
    last_accessed: Optional[datetime] = None

    # Configuration
    cache_enabled: bool = True
    cache_ttl: int = 3600
    access_permissions: List[str] = field(default_factory=list)

    # Timestamps
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "uri": self.uri,
            "name": self.name,
            "server_id": self.server_id,
            "description": self.description,
            "mime_type": self.mime_type,
            "size_bytes": self.size_bytes,
            "read_count": self.read_count,
            "last_accessed": (
                self.last_accessed.isoformat() if self.last_accessed else None
            ),
            "cache_enabled": self.cache_enabled,
            "cache_ttl": self.cache_ttl,
            "access_permissions": self.access_permissions,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }


@dataclass
class ToolExecution:
    """Tool execution record."""

    id: str
    server_id: str
    tool_name: str
    parameters: Dict[str, Any]

    # User info
    user_id: Optional[str] = None
    organization_id: Optional[str] = None

    # Execution info
    started_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    completed_at: Optional[datetime] = None
    status: str = "pending"

    # Results
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None

    # Metrics
    duration_ms: Optional[float] = None
    memory_used_mb: Optional[float] = None

    # Context
    context: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "server_id": self.server_id,
            "tool_name": self.tool_name,
            "parameters": self.parameters,
            "user_id": self.user_id,
            "organization_id": self.organization_id,
            "started_at": self.started_at.isoformat(),
            "completed_at": (
                self.completed_at.isoformat() if self.completed_at else None
            ),
            "status": self.status,
            "result": self.result,
            "error": self.error,
            "duration_ms": self.duration_ms,
            "memory_used_mb": self.memory_used_mb,
            "context": self.context,
            "metadata": self.metadata,
        }


@dataclass
class MCPSession:
    """MCP client session."""

    id: str
    user_id: str

    # Connection info
    connected_servers: List[str] = field(default_factory=list)
    active_tools: List[str] = field(default_factory=list)

    # Session info
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    last_activity: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    expires_at: Optional[datetime] = None

    # Metrics
    total_executions: int = 0
    successful_executions: int = 0
    failed_executions: int = 0

    # Configuration
    max_concurrent_executions: int = 10
    timeout_minutes: int = 60

    def is_expired(self) -> bool:
        """Check if session is expired."""
        if self.expires_at:
            return datetime.now(timezone.utc) > self.expires_at
        return False

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "user_id": self.user_id,
            "connected_servers": self.connected_servers,
            "active_tools": self.active_tools,
            "created_at": self.created_at.isoformat(),
            "last_activity": self.last_activity.isoformat(),
            "expires_at": self.expires_at.isoformat() if self.expires_at else None,
            "total_executions": self.total_executions,
            "successful_executions": self.successful_executions,
            "failed_executions": self.failed_executions,
            "is_expired": self.is_expired(),
        }


@dataclass
class MCPMetrics:
    """MCP system metrics."""

    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    # Server metrics
    total_servers: int = 0
    running_servers: int = 0
    error_servers: int = 0

    # Tool metrics
    total_tools: int = 0
    active_tools: int = 0

    # Execution metrics
    executions_last_hour: int = 0
    success_rate: float = 0.0
    average_duration_ms: float = 0.0

    # Resource metrics
    total_resources: int = 0
    cached_resources: int = 0
    cache_hit_rate: float = 0.0

    # System metrics
    cpu_usage_percent: float = 0.0
    memory_usage_mb: float = 0.0
    active_sessions: int = 0

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "timestamp": self.timestamp.isoformat(),
            "servers": {
                "total": self.total_servers,
                "running": self.running_servers,
                "error": self.error_servers,
            },
            "tools": {"total": self.total_tools, "active": self.active_tools},
            "executions": {
                "last_hour": self.executions_last_hour,
                "success_rate": self.success_rate,
                "average_duration_ms": self.average_duration_ms,
            },
            "resources": {
                "total": self.total_resources,
                "cached": self.cached_resources,
                "cache_hit_rate": self.cache_hit_rate,
            },
            "system": {
                "cpu_usage_percent": self.cpu_usage_percent,
                "memory_usage_mb": self.memory_usage_mb,
                "active_sessions": self.active_sessions,
            },
        }
