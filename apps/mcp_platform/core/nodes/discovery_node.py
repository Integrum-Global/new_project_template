"""
Discovery Node

Custom Kailash node for MCP service discovery and cataloging.
"""

import asyncio
import json
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

from kailash.node import Node
from kailash.node.parameter import NodeParameter, ParameterType

logger = logging.getLogger(__name__)


class DiscoveryNode(Node):
    """
    Node for discovering and cataloging MCP services, tools, and resources.

    Features:
    - Service discovery (find MCP servers on network)
    - Tool cataloging with metadata enrichment
    - Resource indexing
    - Capability mapping
    - Service health probing
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize the discovery node."""
        self.config = config or {}

        # Discovery settings
        self.discovery_timeout = self.config.get("discovery_timeout", 30)
        self.probe_timeout = self.config.get("probe_timeout", 5)
        self.catalog_embeddings = self.config.get("catalog_embeddings", True)

        super().__init__()

    def get_parameters(self) -> Dict[str, NodeParameter]:
        """Define node parameters."""
        return {
            "operation": NodeParameter(
                name="operation",
                type=ParameterType.STRING,
                required=True,
                description="Discovery operation to perform",
                allowed_values=[
                    "discover_servers",
                    "catalog_tools",
                    "index_resources",
                    "map_capabilities",
                    "probe_health",
                ],
            ),
            "target": NodeParameter(
                name="target",
                type=ParameterType.STRING,
                required=False,
                description="Target for discovery (network, directory, registry)",
            ),
            "servers": NodeParameter(
                name="servers",
                type=ParameterType.LIST,
                required=False,
                description="List of servers to catalog",
            ),
            "filters": NodeParameter(
                name="filters",
                type=ParameterType.DICT,
                required=False,
                default={},
                description="Filters for discovery",
            ),
            "enrich_metadata": NodeParameter(
                name="enrich_metadata",
                type=ParameterType.BOOLEAN,
                required=False,
                default=True,
                description="Enrich discovered items with metadata",
            ),
        }

    async def execute(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute the discovery operation."""
        operation = context.get("operation")

        try:
            if operation == "discover_servers":
                return await self._discover_servers(context)
            elif operation == "catalog_tools":
                return await self._catalog_tools(context)
            elif operation == "index_resources":
                return await self._index_resources(context)
            elif operation == "map_capabilities":
                return await self._map_capabilities(context)
            elif operation == "probe_health":
                return await self._probe_health(context)
            else:
                return {"success": False, "error": f"Unknown operation: {operation}"}

        except Exception as e:
            logger.error(f"Error in discovery operation: {e}")
            return {"success": False, "error": str(e), "operation": operation}

    async def _discover_servers(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Discover MCP servers on the network or in a directory."""
        target = context.get("target", "local")
        filters = context.get("filters", {})

        discovered_servers = []

        if target == "local":
            # Discover local MCP servers
            discovered_servers.extend(await self._discover_local_servers())

        elif target == "network":
            # Discover network MCP servers
            discovered_servers.extend(await self._discover_network_servers(filters))

        elif target == "registry":
            # Discover from a registry service
            registry_url = filters.get("registry_url")
            if registry_url:
                discovered_servers.extend(
                    await self._discover_registry_servers(registry_url)
                )

        # Enrich metadata if requested
        if context.get("enrich_metadata", True):
            for server in discovered_servers:
                await self._enrich_server_metadata(server)

        return {
            "success": True,
            "discovered_count": len(discovered_servers),
            "servers": discovered_servers,
            "discovery_method": target,
            "timestamp": datetime.utcnow().isoformat(),
        }

    async def _discover_local_servers(self) -> List[Dict[str, Any]]:
        """Discover MCP servers running locally."""
        servers = []

        # Check common MCP server locations
        import subprocess

        # Check for running processes
        try:
            # Use ps to find MCP-related processes
            result = subprocess.run(["ps", "aux"], capture_output=True, text=True)

            for line in result.stdout.split("\n"):
                if "mcp" in line.lower() or "modelcontext" in line.lower():
                    # Parse process info
                    parts = line.split()
                    if len(parts) > 10:
                        command = " ".join(parts[10:])
                        servers.append(
                            {
                                "type": "local_process",
                                "pid": parts[1],
                                "command": command,
                                "discovered_at": datetime.utcnow().isoformat(),
                            }
                        )

        except Exception as e:
            logger.warning(f"Error discovering local processes: {e}")

        # Check for known MCP server configs
        import os

        config_paths = [
            "~/.mcp/servers.json",
            "~/.config/mcp/servers.json",
            "/etc/mcp/servers.json",
        ]

        for path in config_paths:
            expanded_path = os.path.expanduser(path)
            if os.path.exists(expanded_path):
                try:
                    with open(expanded_path) as f:
                        config = json.load(f)
                        if isinstance(config, list):
                            servers.extend(config)
                        elif isinstance(config, dict) and "servers" in config:
                            servers.extend(config["servers"])
                except Exception as e:
                    logger.warning(f"Error reading config from {path}: {e}")

        return servers

    async def _discover_network_servers(
        self, filters: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Discover MCP servers on the network."""
        servers = []

        # Network discovery would typically use:
        # - mDNS/Bonjour for local network discovery
        # - Port scanning for known MCP ports
        # - API discovery endpoints

        # For now, return mock data
        # In production, implement actual network discovery

        return servers

    async def _discover_registry_servers(
        self, registry_url: str
    ) -> List[Dict[str, Any]]:
        """Discover servers from a registry service."""
        servers = []

        try:
            import aiohttp

            async with aiohttp.ClientSession() as session:
                async with session.get(f"{registry_url}/servers") as response:
                    if response.status == 200:
                        data = await response.json()
                        servers = data.get("servers", [])

        except Exception as e:
            logger.error(f"Error querying registry: {e}")

        return servers

    async def _enrich_server_metadata(self, server: Dict[str, Any]):
        """Enrich server with additional metadata."""
        # Add discovery metadata
        server["discovery_metadata"] = {
            "discovered_at": datetime.utcnow().isoformat(),
            "discovery_node": "DiscoveryNode",
            "enriched": True,
        }

        # Try to determine server type and capabilities
        if "command" in server:
            command = server["command"].lower()
            if "filesystem" in command:
                server["capabilities"] = ["file_operations", "directory_listing"]
            elif "database" in command or "sql" in command:
                server["capabilities"] = ["database_queries", "data_manipulation"]
            elif "api" in command or "http" in command:
                server["capabilities"] = ["api_calls", "web_requests"]

    async def _catalog_tools(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Catalog tools from multiple servers."""
        servers = context.get("servers", [])

        all_tools = []
        tool_categories = {}
        tool_signatures = set()

        for server in servers:
            # Get tools from server (mock for now)
            server_tools = await self._get_server_tools(server)

            for tool in server_tools:
                # Create tool signature for deduplication
                signature = f"{tool['name']}:{tool.get('version', '1.0')}"

                if signature not in tool_signatures:
                    tool_signatures.add(signature)

                    # Categorize tool
                    category = self._categorize_tool(tool)
                    tool["category"] = category

                    if category not in tool_categories:
                        tool_categories[category] = []
                    tool_categories[category].append(tool)

                    # Add to all tools
                    all_tools.append(tool)

        # Generate catalog summary
        catalog = {
            "total_tools": len(all_tools),
            "unique_tools": len(tool_signatures),
            "categories": {cat: len(tools) for cat, tools in tool_categories.items()},
            "tools": all_tools,
            "catalog_date": datetime.utcnow().isoformat(),
        }

        # Generate embeddings if requested
        if self.catalog_embeddings:
            await self._generate_tool_embeddings(all_tools)

        return {"success": True, "catalog": catalog, "servers_processed": len(servers)}

    async def _get_server_tools(self, server: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Get tools from a server."""
        # In production, this would connect to the server and get tools
        # For now, return mock tools based on server type

        tools = []

        if "filesystem" in str(server.get("command", "")).lower():
            tools = [
                {
                    "name": "read_file",
                    "description": "Read contents of a file",
                    "parameters": ["path"],
                },
                {
                    "name": "write_file",
                    "description": "Write contents to a file",
                    "parameters": ["path", "content"],
                },
                {
                    "name": "list_directory",
                    "description": "List files in a directory",
                    "parameters": ["path"],
                },
            ]
        elif "database" in str(server.get("command", "")).lower():
            tools = [
                {
                    "name": "execute_query",
                    "description": "Execute SQL query",
                    "parameters": ["query"],
                },
                {
                    "name": "list_tables",
                    "description": "List database tables",
                    "parameters": [],
                },
            ]

        return tools

    def _categorize_tool(self, tool: Dict[str, Any]) -> str:
        """Categorize a tool based on its name and description."""
        name = tool.get("name", "").lower()
        description = tool.get("description", "").lower()

        # Simple categorization based on keywords
        if any(
            word in name + description
            for word in ["read", "write", "file", "directory"]
        ):
            return "file_operations"
        elif any(
            word in name + description for word in ["query", "database", "sql", "table"]
        ):
            return "database"
        elif any(
            word in name + description for word in ["api", "http", "request", "webhook"]
        ):
            return "web_api"
        elif any(
            word in name + description for word in ["analyze", "process", "transform"]
        ):
            return "data_processing"
        elif any(
            word in name + description for word in ["generate", "create", "build"]
        ):
            return "generation"
        else:
            return "utility"

    async def _generate_tool_embeddings(self, tools: List[Dict[str, Any]]):
        """Generate embeddings for tools (for semantic search)."""
        # In production, use an embedding model
        # For now, just add a placeholder
        for tool in tools:
            tool["embedding_generated"] = True
            tool["embedding_model"] = "placeholder"

    async def _index_resources(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Index resources from servers."""
        servers = context.get("servers", [])

        all_resources = []
        resource_types = {}

        for server in servers:
            # Get resources from server (mock for now)
            resources = await self._get_server_resources(server)

            for resource in resources:
                # Categorize by MIME type
                mime_type = resource.get("mime_type", "unknown")
                if mime_type not in resource_types:
                    resource_types[mime_type] = []
                resource_types[mime_type].append(resource)

                all_resources.append(resource)

        return {
            "success": True,
            "total_resources": len(all_resources),
            "resource_types": {
                mime: len(resources) for mime, resources in resource_types.items()
            },
            "resources": all_resources,
            "index_date": datetime.utcnow().isoformat(),
        }

    async def _get_server_resources(
        self, server: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Get resources from a server."""
        # Mock implementation
        return [
            {
                "uri": f"resource://{server.get('name', 'server')}/data",
                "mime_type": "application/json",
                "size_bytes": 1024,
            }
        ]

    async def _map_capabilities(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Map capabilities across all discovered services."""
        servers = context.get("servers", [])

        capability_map = {}
        server_capabilities = {}

        for server in servers:
            server_id = server.get("id", server.get("name", "unknown"))
            capabilities = server.get("capabilities", [])

            # Get tools and derive capabilities
            tools = await self._get_server_tools(server)
            for tool in tools:
                category = self._categorize_tool(tool)
                if category not in capabilities:
                    capabilities.append(category)

            server_capabilities[server_id] = capabilities

            # Build capability map
            for capability in capabilities:
                if capability not in capability_map:
                    capability_map[capability] = []
                capability_map[capability].append(server_id)

        return {
            "success": True,
            "capability_map": capability_map,
            "server_capabilities": server_capabilities,
            "total_capabilities": len(capability_map),
            "mapping_date": datetime.utcnow().isoformat(),
        }

    async def _probe_health(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Probe health of discovered servers."""
        servers = context.get("servers", [])

        health_results = []

        # Probe servers in parallel
        tasks = [self._probe_server_health(server) for server in servers]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        for i, result in enumerate(results):
            if isinstance(result, Exception):
                health_results.append(
                    {"server": servers[i], "healthy": False, "error": str(result)}
                )
            else:
                health_results.append(result)

        # Summary
        healthy_count = sum(1 for r in health_results if r.get("healthy", False))

        return {
            "success": True,
            "total_servers": len(servers),
            "healthy_servers": healthy_count,
            "unhealthy_servers": len(servers) - healthy_count,
            "health_results": health_results,
            "probe_date": datetime.utcnow().isoformat(),
        }

    async def _probe_server_health(self, server: Dict[str, Any]) -> Dict[str, Any]:
        """Probe health of a single server."""
        # Mock implementation
        # In production, actually connect and check server health

        import random

        is_healthy = random.random() > 0.1  # 90% chance of being healthy

        return {
            "server": server,
            "healthy": is_healthy,
            "response_time_ms": random.randint(10, 100) if is_healthy else None,
            "last_checked": datetime.utcnow().isoformat(),
        }
