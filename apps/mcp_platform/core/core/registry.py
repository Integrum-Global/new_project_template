"""
MCP Registry - Central registry for servers, tools, and resources.

This module provides a centralized registry for managing MCP entities
with persistence, caching, and search capabilities.
"""

import asyncio
import json
import logging
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional, Set

import redis
from sqlalchemy import JSON, Column, DateTime, Integer, String, create_engine
from sqlalchemy.orm import Session, declarative_base, sessionmaker

from .models import MCPResource, MCPServer, MCPTool, ServerStatus

logger = logging.getLogger(__name__)

Base = declarative_base()


class ServerRecord(Base):
    """Database model for MCP servers."""

    __tablename__ = "mcp_servers"

    id = Column(String, primary_key=True)
    name = Column(String, nullable=False, index=True)
    transport = Column(String, nullable=False)
    config = Column(JSON, nullable=False)
    status = Column(String, nullable=False)
    owner_id = Column(String, index=True)
    organization_id = Column(String, index=True)
    metadata_json = Column(JSON)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(
        DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )


class ToolRecord(Base):
    """Database model for MCP tools."""

    __tablename__ = "mcp_tools"

    id = Column(String, primary_key=True)
    name = Column(String, nullable=False, index=True)
    server_id = Column(String, nullable=False, index=True)
    description = Column(String)
    input_schema = Column(JSON)
    output_schema = Column(JSON)
    metadata_json = Column(JSON)
    execution_count = Column(Integer, default=0)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(
        DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )


class ResourceRecord(Base):
    """Database model for MCP resources."""

    __tablename__ = "mcp_resources"

    id = Column(String, primary_key=True)
    uri = Column(String, nullable=False, index=True)
    name = Column(String, nullable=False)
    server_id = Column(String, nullable=False, index=True)
    metadata_json = Column(JSON)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(
        DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )


class MCPRegistry:
    """
    Central registry for MCP entities.

    Provides persistence, caching, and search capabilities for
    servers, tools, and resources.
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize the registry."""
        self.config = config or {}

        # Database setup
        db_url = self.config.get("database_url", "sqlite:///mcp_registry.db")
        self.engine = create_engine(db_url)
        Base.metadata.create_all(self.engine)
        self.SessionLocal = sessionmaker(bind=self.engine)

        # Redis cache setup (optional)
        self.cache = None
        if self.config.get("enable_cache", True):
            try:
                redis_config = self.config.get("redis", {})
                self.cache = redis.Redis(
                    host=redis_config.get("host", "localhost"),
                    port=redis_config.get("port", 6379),
                    db=redis_config.get("db", 0),
                    decode_responses=True,
                )
                # Test connection
                self.cache.ping()
                logger.info("Redis cache connected")
            except Exception as e:
                logger.warning(f"Redis cache not available: {e}")
                self.cache = None

        # In-memory indices for fast lookup
        self._server_index: Dict[str, MCPServer] = {}
        self._tool_index: Dict[str, Dict[str, MCPTool]] = (
            {}
        )  # server_id -> tool_name -> tool
        self._resource_index: Dict[str, Dict[str, MCPResource]] = (
            {}
        )  # server_id -> uri -> resource

        # Search indices
        self._tool_tags: Dict[str, Set[str]] = {}  # tag -> tool_ids
        self._server_tags: Dict[str, Set[str]] = {}  # tag -> server_ids

        # Background tasks
        self._sync_task: Optional["asyncio.Task"] = None

    async def initialize(self):
        """Initialize the registry and load data."""
        logger.info("Initializing MCP Registry")

        # Load existing data from database
        await self._load_from_database()

        # Start background tasks
        if self.config.get("enable_sync", True):
            self._sync_task = asyncio.create_task(self._sync_to_database())

        logger.info("MCP Registry initialized")

    async def register_server(self, server: MCPServer) -> bool:
        """
        Register a new MCP server.

        Args:
            server: Server to register

        Returns:
            Success status
        """
        # Add to index
        self._server_index[server.id] = server

        # Update tag index
        for tag in server.tags:
            if tag not in self._server_tags:
                self._server_tags[tag] = set()
            self._server_tags[tag].add(server.id)

        # Cache if available
        if self.cache:
            try:
                cache_key = f"mcp:server:{server.id}"
                self.cache.setex(
                    cache_key,
                    self.config.get("cache_ttl", 3600),
                    json.dumps(server.to_dict()),
                )
            except Exception as e:
                logger.error(f"Cache error: {e}")

        # Persist to database
        await self._persist_server(server)

        logger.info(f"Registered server: {server.name} ({server.id})")
        return True

    async def update_server(self, server: MCPServer) -> bool:
        """Update server information."""
        server.updated_at = datetime.now(timezone.utc)

        # Update index
        self._server_index[server.id] = server

        # Update cache
        if self.cache:
            try:
                cache_key = f"mcp:server:{server.id}"
                self.cache.setex(
                    cache_key,
                    self.config.get("cache_ttl", 3600),
                    json.dumps(server.to_dict()),
                )
            except Exception as e:
                logger.error(f"Cache error: {e}")

        # Persist update
        await self._persist_server(server, update=True)

        return True

    async def get_server(self, server_id: str) -> Optional[MCPServer]:
        """Get server by ID."""
        # Check memory index first
        if server_id in self._server_index:
            return self._server_index[server_id]

        # Check cache
        if self.cache:
            try:
                cache_key = f"mcp:server:{server_id}"
                data = self.cache.get(cache_key)
                if data:
                    server_dict = json.loads(data)
                    server = self._dict_to_server(server_dict)
                    self._server_index[server_id] = server
                    return server
            except Exception as e:
                logger.error(f"Cache error: {e}")

        # Load from database
        with self.SessionLocal() as session:
            record = session.query(ServerRecord).filter_by(id=server_id).first()
            if record:
                server = self._record_to_server(record)
                self._server_index[server_id] = server
                return server

        return None

    async def list_servers(
        self, filters: Optional[Dict[str, Any]] = None
    ) -> List[MCPServer]:
        """List servers with optional filters."""
        servers = list(self._server_index.values())

        if not filters:
            return servers

        # Apply filters
        if "status" in filters:
            status = filters["status"]
            if isinstance(status, str):
                status = ServerStatus(status)
            servers = [s for s in servers if s.status == status]

        if "transport" in filters:
            transport = filters["transport"]
            servers = [s for s in servers if s.transport == transport]

        if "owner_id" in filters:
            servers = [s for s in servers if s.owner_id == filters["owner_id"]]

        if "tags" in filters:
            required_tags = set(filters["tags"])
            servers = [s for s in servers if required_tags.issubset(set(s.tags))]

        return servers

    async def register_tool(self, server_id: str, tool: MCPTool) -> bool:
        """Register a tool for a server."""
        # Initialize server tool index if needed
        if server_id not in self._tool_index:
            self._tool_index[server_id] = {}

        # Add to index
        self._tool_index[server_id][tool.name] = tool

        # Update tag index
        for tag in tool.tags:
            tool_id = f"{server_id}:{tool.name}"
            if tag not in self._tool_tags:
                self._tool_tags[tag] = set()
            self._tool_tags[tag].add(tool_id)

        # Cache if available
        if self.cache:
            try:
                cache_key = f"mcp:tool:{server_id}:{tool.name}"
                self.cache.setex(
                    cache_key,
                    self.config.get("cache_ttl", 3600),
                    json.dumps(tool.to_dict()),
                )
            except Exception as e:
                logger.error(f"Cache error: {e}")

        # Persist to database
        await self._persist_tool(tool)

        logger.info(f"Registered tool: {tool.name} on server {server_id}")
        return True

    async def get_tool(self, server_id: str, tool_name: str) -> Optional[MCPTool]:
        """Get a specific tool."""
        # Check memory index
        if server_id in self._tool_index:
            if tool_name in self._tool_index[server_id]:
                return self._tool_index[server_id][tool_name]

        # Check cache
        if self.cache:
            try:
                cache_key = f"mcp:tool:{server_id}:{tool_name}"
                data = self.cache.get(cache_key)
                if data:
                    tool_dict = json.loads(data)
                    tool = self._dict_to_tool(tool_dict)

                    # Update index
                    if server_id not in self._tool_index:
                        self._tool_index[server_id] = {}
                    self._tool_index[server_id][tool_name] = tool

                    return tool
            except Exception as e:
                logger.error(f"Cache error: {e}")

        # Load from database
        with self.SessionLocal() as session:
            tool_id = f"{server_id}:{tool_name}"
            record = session.query(ToolRecord).filter_by(id=tool_id).first()
            if record:
                tool = self._record_to_tool(record)

                # Update index
                if server_id not in self._tool_index:
                    self._tool_index[server_id] = {}
                self._tool_index[server_id][tool_name] = tool

                return tool

        return None

    async def list_tools(
        self, server_id: Optional[str] = None, filters: Optional[Dict[str, Any]] = None
    ) -> List[MCPTool]:
        """List tools with optional filters."""
        tools = []

        # Get tools for specific server or all
        if server_id:
            if server_id in self._tool_index:
                tools = list(self._tool_index[server_id].values())
        else:
            for server_tools in self._tool_index.values():
                tools.extend(server_tools.values())

        if not filters:
            return tools

        # Apply filters
        if "category" in filters:
            tools = [t for t in tools if t.category == filters["category"]]

        if "tags" in filters:
            required_tags = set(filters["tags"])
            tools = [t for t in tools if required_tags.issubset(set(t.tags))]

        return tools

    async def search_tools(self, query: str, limit: int = 10) -> List[MCPTool]:
        """Search for tools by name or description."""
        results = []
        query_lower = query.lower()

        for server_tools in self._tool_index.values():
            for tool in server_tools.values():
                # Search in name and description
                if (
                    query_lower in tool.name.lower()
                    or query_lower in tool.description.lower()
                ):
                    results.append(tool)

                if len(results) >= limit:
                    return results

        return results

    async def update_tool_metrics(
        self, server_id: str, tool_name: str, execution_time_ms: float, success: bool
    ):
        """Update tool execution metrics."""
        tool = await self.get_tool(server_id, tool_name)
        if not tool:
            return

        # Update metrics
        tool.execution_count += 1
        if success:
            tool.success_count += 1
        else:
            tool.failure_count += 1

        # Update average duration
        if tool.execution_count > 1:
            tool.average_duration_ms = (
                tool.average_duration_ms * (tool.execution_count - 1)
                + execution_time_ms
            ) / tool.execution_count
        else:
            tool.average_duration_ms = execution_time_ms

        tool.last_executed = datetime.now(timezone.utc)

        # Save updates
        await self.register_tool(server_id, tool)

    async def _load_from_database(self):
        """Load existing data from database."""
        with self.SessionLocal() as session:
            # Load servers
            server_records = session.query(ServerRecord).all()
            for record in server_records:
                server = self._record_to_server(record)
                self._server_index[server.id] = server

                # Update tag index
                for tag in server.tags:
                    if tag not in self._server_tags:
                        self._server_tags[tag] = set()
                    self._server_tags[tag].add(server.id)

            # Load tools
            tool_records = session.query(ToolRecord).all()
            for record in tool_records:
                tool = self._record_to_tool(record)

                # Initialize server tool index if needed
                if tool.server_id not in self._tool_index:
                    self._tool_index[tool.server_id] = {}

                self._tool_index[tool.server_id][tool.name] = tool

                # Update tag index
                for tag in tool.tags:
                    tool_id = f"{tool.server_id}:{tool.name}"
                    if tag not in self._tool_tags:
                        self._tool_tags[tag] = set()
                    self._tool_tags[tag].add(tool_id)

        logger.info(
            f"Loaded {len(self._server_index)} servers and {sum(len(tools) for tools in self._tool_index.values())} tools from database"
        )

    async def _sync_to_database(self):
        """Periodically sync in-memory data to database."""
        while True:
            try:
                # Sync interval from config
                interval = self.config.get("sync_interval", 60)
                await asyncio.sleep(interval)

                # Sync servers
                for server in self._server_index.values():
                    await self._persist_server(server, update=True)

                # Sync tools
                for server_tools in self._tool_index.values():
                    for tool in server_tools.values():
                        await self._persist_tool(tool, update=True)

            except Exception as e:
                logger.error(f"Error syncing to database: {e}")

    async def _persist_server(self, server: MCPServer, update: bool = False):
        """Persist server to database."""
        with self.SessionLocal() as session:
            if update:
                record = session.query(ServerRecord).filter_by(id=server.id).first()
                if record:
                    record.name = server.name
                    record.transport = server.transport
                    record.config = server.config
                    record.status = (
                        server.status.value
                        if hasattr(server.status, "value")
                        else server.status
                    )
                    record.owner_id = server.owner_id
                    record.organization_id = server.organization_id
                    record.metadata_json = {
                        "description": server.description,
                        "tags": server.tags,
                        "labels": server.labels,
                        "tool_count": server.tool_count,
                        "resource_count": server.resource_count,
                        "health_status": server.health_status,
                    }
                    record.updated_at = datetime.now(timezone.utc)
            else:
                record = ServerRecord(
                    id=server.id,
                    name=server.name,
                    transport=server.transport,
                    config=server.config,
                    status=(
                        server.status.value
                        if hasattr(server.status, "value")
                        else server.status
                    ),
                    owner_id=server.owner_id,
                    organization_id=server.organization_id,
                    metadata_json={
                        "description": server.description,
                        "tags": server.tags,
                        "labels": server.labels,
                        "tool_count": server.tool_count,
                        "resource_count": server.resource_count,
                        "health_status": server.health_status,
                    },
                )
                session.add(record)

            session.commit()

    async def _persist_tool(self, tool: MCPTool, update: bool = False):
        """Persist tool to database."""
        with self.SessionLocal() as session:
            tool_id = f"{tool.server_id}:{tool.name}"

            if update:
                record = session.query(ToolRecord).filter_by(id=tool_id).first()
                if record:
                    record.name = tool.name
                    record.server_id = tool.server_id
                    record.description = tool.description
                    record.input_schema = tool.input_schema
                    record.output_schema = tool.output_schema
                    record.metadata_json = {
                        "category": tool.category.value if tool.category else None,
                        "tags": tool.tags,
                        "version": tool.version,
                        "timeout": tool.timeout,
                        "cache_enabled": tool.cache_enabled,
                        "cache_ttl": tool.cache_ttl,
                        "rate_limit": tool.rate_limit,
                        "required_permissions": tool.required_permissions,
                    }
                    record.execution_count = tool.execution_count
                    record.updated_at = datetime.now(timezone.utc)
            else:
                record = ToolRecord(
                    id=tool_id,
                    name=tool.name,
                    server_id=tool.server_id,
                    description=tool.description,
                    input_schema=tool.input_schema,
                    output_schema=tool.output_schema,
                    metadata_json={
                        "category": tool.category.value if tool.category else None,
                        "tags": tool.tags,
                        "version": tool.version,
                        "timeout": tool.timeout,
                        "cache_enabled": tool.cache_enabled,
                        "cache_ttl": tool.cache_ttl,
                        "rate_limit": tool.rate_limit,
                        "required_permissions": tool.required_permissions,
                    },
                    execution_count=tool.execution_count,
                )
                session.add(record)

            session.commit()

    def _record_to_server(self, record: ServerRecord) -> MCPServer:
        """Convert database record to server model."""
        metadata = record.metadata_json or {}

        server = MCPServer(
            id=record.id,
            name=record.name,
            transport=record.transport,
            config=record.config,
            status=ServerStatus(record.status),
            owner_id=record.owner_id,
            organization_id=record.organization_id,
            created_at=record.created_at,
            updated_at=record.updated_at,
        )

        # Set metadata fields
        server.description = metadata.get("description")
        server.tags = metadata.get("tags", [])
        server.labels = metadata.get("labels", {})
        server.tool_count = metadata.get("tool_count", 0)
        server.resource_count = metadata.get("resource_count", 0)
        server.health_status = metadata.get("health_status", {})

        return server

    def _record_to_tool(self, record: ToolRecord) -> MCPTool:
        """Convert database record to tool model."""
        metadata = record.metadata_json or {}

        tool = MCPTool(
            name=record.name,
            server_id=record.server_id,
            description=record.description or "",
            input_schema=record.input_schema or {},
            output_schema=record.output_schema or {},
            execution_count=record.execution_count,
        )

        # Set metadata fields
        if metadata.get("category"):
            tool.category = metadata["category"]
        tool.tags = metadata.get("tags", [])
        tool.version = metadata.get("version")
        tool.timeout = metadata.get("timeout", 120)
        tool.cache_enabled = metadata.get("cache_enabled", False)
        tool.cache_ttl = metadata.get("cache_ttl", 3600)
        tool.rate_limit = metadata.get("rate_limit")
        tool.required_permissions = metadata.get("required_permissions", [])

        return tool

    def _dict_to_server(self, data: Dict[str, Any]) -> MCPServer:
        """Convert dictionary to server model."""
        server = MCPServer(
            id=data["id"],
            name=data["name"],
            transport=data["transport"],
            config=data["config"],
            status=ServerStatus(data["status"]),
            owner_id=data.get("owner_id"),
            organization_id=data.get("organization_id"),
        )

        # Set optional fields
        for field in [
            "description",
            "tags",
            "labels",
            "tool_count",
            "resource_count",
            "error_message",
            "health_status",
        ]:
            if field in data:
                setattr(server, field, data[field])

        # Set timestamps
        for field in [
            "created_at",
            "updated_at",
            "started_at",
            "stopped_at",
            "last_health_check",
            "last_discovery",
        ]:
            if field in data and data[field]:
                setattr(server, field, datetime.fromisoformat(data[field]))

        return server

    def _dict_to_tool(self, data: Dict[str, Any]) -> MCPTool:
        """Convert dictionary to tool model."""
        tool = MCPTool(
            name=data["name"],
            server_id=data["server_id"],
            description=data.get("description", ""),
            input_schema=data.get("input_schema", {}),
            output_schema=data.get("output_schema", {}),
        )

        # Set optional fields
        for field in [
            "category",
            "tags",
            "version",
            "execution_count",
            "success_count",
            "failure_count",
            "average_duration_ms",
            "timeout",
            "cache_enabled",
            "cache_ttl",
            "rate_limit",
            "required_permissions",
        ]:
            if field in data:
                setattr(tool, field, data[field])

        # Set timestamps
        for field in ["last_executed", "discovered_at", "updated_at"]:
            if field in data and data[field]:
                setattr(tool, field, datetime.fromisoformat(data[field]))

        return tool

    async def shutdown(self):
        """Shutdown the registry."""
        logger.info("Shutting down MCP Registry")

        # Cancel background tasks
        if self._sync_task and not self._sync_task.done():
            self._sync_task.cancel()
            try:
                await self._sync_task
            except asyncio.CancelledError:
                pass

        # Final sync to database
        for server in self._server_index.values():
            await self._persist_server(server, update=True)

        for server_tools in self._tool_index.values():
            for tool in server_tools.values():
                await self._persist_tool(tool, update=True)

        # Close connections
        if self.cache:
            self.cache.close()

        logger.info("MCP Registry shutdown complete")
