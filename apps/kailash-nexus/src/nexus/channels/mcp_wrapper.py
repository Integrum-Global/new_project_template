"""
MCP Channel Wrapper for Nexus

Wraps SDK's MCPChannel with enterprise features.
"""

import logging
from datetime import datetime, timezone
from typing import Any, Callable, Dict, List, Optional

from kailash.channels.mcp_channel import MCPChannel
from kailash.workflow import Workflow

logger = logging.getLogger(__name__)


class MCPChannelWrapper:
    """MCP Channel wrapper with enterprise features.

    Adds tool versioning, usage tracking, and multi-tenant support
    to the SDK's MCPChannel.
    """

    def __init__(
        self,
        mcp_channel: MCPChannel,
        multi_tenant_manager: Optional[Any] = None,
        auth_manager: Optional[Any] = None,
        marketplace_registry: Optional[Any] = None,
    ):
        """Initialize MCP channel wrapper.

        Args:
            mcp_channel: SDK's MCPChannel instance
            multi_tenant_manager: Multi-tenant manager
            auth_manager: Authentication manager
            marketplace_registry: Marketplace registry
        """
        self.mcp_channel = mcp_channel
        self.multi_tenant_manager = multi_tenant_manager
        self.auth_manager = auth_manager
        self.marketplace_registry = marketplace_registry

        # Tool tracking
        self._tool_versions: Dict[str, str] = {}
        self._tool_usage: Dict[str, Dict[str, Any]] = {}

        # Add enterprise capabilities
        self._setup_enterprise_tools()

        logger.info("MCP channel wrapper initialized")

    def _setup_enterprise_tools(self):
        """Setup enterprise MCP tools."""
        # Marketplace tool
        if self.marketplace_registry:
            self.register_tool(
                "marketplace_search",
                self._marketplace_search_tool,
                {
                    "description": "Search workflow marketplace",
                    "parameters": {
                        "query": {"type": "string", "description": "Search query"},
                        "category": {
                            "type": "string",
                            "description": "Category filter",
                        },
                        "limit": {"type": "integer", "description": "Result limit"},
                    },
                },
                version="1.0.0",
            )

            self.register_tool(
                "marketplace_install",
                self._marketplace_install_tool,
                {
                    "description": "Install workflow from marketplace",
                    "parameters": {
                        "item_id": {
                            "type": "string",
                            "description": "Marketplace item ID",
                        }
                    },
                },
                version="1.0.0",
                auth_required=True,
            )

        # Tenant management tool
        if self.multi_tenant_manager:
            self.register_tool(
                "tenant_info",
                self._tenant_info_tool,
                {
                    "description": "Get tenant information",
                    "parameters": {
                        "tenant_id": {"type": "string", "description": "Tenant ID"}
                    },
                },
                version="1.0.0",
                auth_required=True,
            )

    async def _marketplace_search_tool(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Search marketplace tool.

        Args:
            params: Tool parameters

        Returns:
            Search results
        """
        query = params.get("query", "")
        category = params.get("category")
        limit = params.get("limit", 10)

        categories = [category] if category else None
        items, total = self.marketplace_registry.search(
            query=query, categories=categories, limit=limit
        )

        results = []
        for item in items:
            results.append(
                {
                    "id": item.item_id,
                    "name": item.name,
                    "description": item.description,
                    "rating": item.stats.average_rating,
                    "installs": item.stats.total_installs,
                    "price": item.price,
                }
            )

        return {"results": results, "total": total, "query": query}

    async def _marketplace_install_tool(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Install from marketplace tool.

        Args:
            params: Tool parameters

        Returns:
            Installation result
        """
        item_id = params.get("item_id")
        if not item_id:
            return {"error": "item_id required"}

        # Get user context from MCP session
        user = self.mcp_channel.session_data.get("user", {})
        user_id = user.get("user_id", "anonymous")
        tenant_id = self.mcp_channel.session_data.get("tenant_id")

        try:
            result = self.marketplace_registry.install(
                item_id=item_id, user_id=user_id, tenant_id=tenant_id
            )

            return {
                "success": True,
                "workflow_id": result["workflow_id"],
                "message": f"Successfully installed {item_id}",
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def _tenant_info_tool(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Get tenant information tool.

        Args:
            params: Tool parameters

        Returns:
            Tenant information
        """
        tenant_id = params.get("tenant_id")
        if not tenant_id:
            # Use session tenant
            tenant_id = self.mcp_channel.session_data.get("tenant_id")

        if not tenant_id:
            return {"error": "No tenant context"}

        tenant = self.multi_tenant_manager.get_tenant(tenant_id)
        if not tenant:
            return {"error": f"Tenant {tenant_id} not found"}

        # Get usage
        usage = self.multi_tenant_manager.get_usage(tenant_id)

        return {"tenant": tenant.to_dict(), "usage": usage.to_dict() if usage else None}

    def register_tool(
        self,
        name: str,
        handler: Callable,
        schema: Dict[str, Any],
        version: str = "1.0.0",
        auth_required: bool = False,
        tenant_required: bool = False,
    ):
        """Register a tool with enterprise features.

        Args:
            name: Tool name
            handler: Tool handler
            schema: Tool schema
            version: Tool version
            auth_required: Require authentication
            tenant_required: Require tenant context
        """
        # Track version
        self._tool_versions[name] = version

        # Initialize usage tracking
        self._tool_usage[name] = {
            "total_calls": 0,
            "success_calls": 0,
            "error_calls": 0,
            "last_called": None,
            "average_duration": 0,
        }

        # Create wrapped handler
        async def enterprise_handler(params: Dict[str, Any]) -> Dict[str, Any]:
            start_time = datetime.now(timezone.utc)

            # Check auth if required
            if auth_required and "user" not in self.mcp_channel.session_data:
                return {"error": "Authentication required"}

            # Check tenant if required
            if tenant_required and "tenant_id" not in self.mcp_channel.session_data:
                return {"error": "Tenant context required"}

            # Track usage
            self._tool_usage[name]["total_calls"] += 1
            self._tool_usage[name]["last_called"] = start_time.isoformat()

            try:
                # Execute handler
                result = await handler(params)

                # Track success
                self._tool_usage[name]["success_calls"] += 1

                # Update average duration
                duration = (datetime.now(timezone.utc) - start_time).total_seconds()
                avg = self._tool_usage[name]["average_duration"]
                count = self._tool_usage[name]["success_calls"]
                self._tool_usage[name]["average_duration"] = (
                    avg * (count - 1) + duration
                ) / count

                return result

            except Exception as e:
                # Track error
                self._tool_usage[name]["error_calls"] += 1
                logger.error(f"Tool {name} error: {str(e)}")

                return {"error": f"Tool execution failed: {str(e)}"}

        # Add version to schema
        schema["version"] = version

        # Register with SDK channel
        self.mcp_channel.register_tool(
            name=name, handler=enterprise_handler, schema=schema
        )

        logger.info(f"Registered enterprise MCP tool: {name} v{version}")

    def register_workflow_tool(
        self,
        name: str,
        workflow: Workflow,
        schema: Dict[str, Any],
        version: str = "1.0.0",
        auth_required: bool = True,
        tenant_required: bool = True,
    ):
        """Register a workflow as an MCP tool.

        Args:
            name: Tool name
            workflow: Workflow to execute
            schema: Tool schema
            version: Tool version
            auth_required: Require authentication
            tenant_required: Require tenant context
        """

        async def workflow_handler(params: Dict[str, Any]) -> Dict[str, Any]:
            # Add context to params
            params["user"] = self.mcp_channel.session_data.get("user")
            params["tenant_id"] = self.mcp_channel.session_data.get("tenant_id")

            try:
                # In production, would execute through runtime
                result = {
                    "workflow": name,
                    "params": params,
                    "status": "completed",
                    "outputs": {},
                }

                return result

            except Exception as e:
                return {"error": f"Workflow execution failed: {str(e)}"}

        self.register_tool(
            name=name,
            handler=workflow_handler,
            schema=schema,
            version=version,
            auth_required=auth_required,
            tenant_required=tenant_required,
        )

    def get_tools(self) -> List[Dict[str, Any]]:
        """Get available tools with enterprise metadata.

        Returns:
            List of tool information
        """
        tools = []

        if hasattr(self.mcp_channel, "_tool_registry"):
            for name, tool_info in self.mcp_channel._tool_registry.items():
                tool_data = {
                    "name": name,
                    "description": tool_info.get("schema", {}).get("description", ""),
                    "version": self._tool_versions.get(name, "1.0.0"),
                    "usage": self._tool_usage.get(name, {}),
                }
                tools.append(tool_data)

        return sorted(tools, key=lambda x: x["name"])

    def get_tool_usage(self, name: Optional[str] = None) -> Dict[str, Any]:
        """Get tool usage statistics.

        Args:
            name: Specific tool name or None for all

        Returns:
            Usage statistics
        """
        if name:
            return self._tool_usage.get(name, {})

        # Aggregate statistics
        total_calls = sum(u["total_calls"] for u in self._tool_usage.values())
        success_calls = sum(u["success_calls"] for u in self._tool_usage.values())
        error_calls = sum(u["error_calls"] for u in self._tool_usage.values())

        return {
            "total_tools": len(self._tool_usage),
            "total_calls": total_calls,
            "success_calls": success_calls,
            "error_calls": error_calls,
            "success_rate": success_calls / total_calls if total_calls > 0 else 0,
            "by_tool": self._tool_usage,
        }

    async def start(self):
        """Start the MCP channel."""
        # Register system tools
        self.register_tool(
            "get_tool_usage",
            lambda params: self.get_tool_usage(params.get("name")),
            {
                "description": "Get tool usage statistics",
                "parameters": {
                    "name": {"type": "string", "description": "Tool name (optional)"}
                },
            },
            version="1.0.0",
        )

        await self.mcp_channel.start()
        logger.info("MCP channel wrapper started")

    async def stop(self):
        """Stop the MCP channel."""
        await self.mcp_channel.stop()
        logger.info("MCP channel wrapper stopped")
