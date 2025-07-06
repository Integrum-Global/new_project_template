"""
MCP Tools API

API endpoints for MCP tool discovery and execution.
"""

import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

from fastapi import BackgroundTasks, Depends, FastAPI, HTTPException, Query
from pydantic import BaseModel

from apps.mcp_platform.core.core.gateway import MCPGateway
from apps.mcp_platform.core.core.security import MCPSecurityManager

logger = logging.getLogger(__name__)


# Pydantic models
class ToolExecutionRequest(BaseModel):
    """Tool execution request model."""

    server_id: str
    tool_name: str
    parameters: Dict[str, Any]
    options: Optional[Dict[str, Any]] = None


class BatchExecutionRequest(BaseModel):
    """Batch tool execution request."""

    executions: List[ToolExecutionRequest]
    parallel: bool = True
    stop_on_error: bool = False


class ToolResponse(BaseModel):
    """Tool response model."""

    name: str
    server_id: str
    description: str
    category: Optional[str] = None
    tags: List[str] = []
    execution_count: int = 0
    average_duration_ms: float = 0.0
    last_executed: Optional[str] = None


class ToolsAPI:
    """API for MCP tool management and execution."""

    def __init__(self, gateway: MCPGateway, security: MCPSecurityManager):
        """Initialize the tools API."""
        self.gateway = gateway
        self.security = security

    def register_routes(self, app: FastAPI):
        """Register tool management routes."""

        @app.get("/api/v1/servers/{server_id}/tools", response_model=List[ToolResponse])
        async def discover_tools(
            server_id: str,
            refresh: bool = Query(False, description="Force refresh tool discovery"),
            current_user: Dict = Depends(self._get_current_user),
        ):
            """Discover tools available on a server."""
            try:
                # Check permissions
                if not await self.security.can_access_server(
                    current_user.get("user_id"), server_id
                ):
                    raise PermissionError("Not authorized to access server")

                # Get tools from cache or discover
                if refresh:
                    tools = await self.gateway.discover_tools(
                        server_id, user_id=current_user.get("user_id")
                    )
                else:
                    # Get from registry
                    tools = await self.gateway.registry.list_tools(server_id)

                    # If no tools cached, discover
                    if not tools:
                        tools = await self.gateway.discover_tools(
                            server_id, user_id=current_user.get("user_id")
                        )

                # Convert to response models
                return [
                    ToolResponse(
                        name=tool.name,
                        server_id=tool.server_id,
                        description=tool.description,
                        category=tool.category.value if tool.category else None,
                        tags=tool.tags,
                        execution_count=tool.execution_count,
                        average_duration_ms=tool.average_duration_ms,
                        last_executed=(
                            tool.last_executed.isoformat()
                            if tool.last_executed
                            else None
                        ),
                    )
                    for tool in tools
                ]

            except ValueError as e:
                raise HTTPException(status_code=404, detail=str(e))
            except PermissionError as e:
                raise HTTPException(status_code=403, detail=str(e))
            except RuntimeError as e:
                raise HTTPException(status_code=503, detail=str(e))
            except Exception as e:
                logger.error(f"Error discovering tools: {e}")
                raise HTTPException(status_code=500, detail="Internal server error")

        @app.get("/api/v1/tools/search")
        async def search_tools(
            query: str = Query(..., description="Search query"),
            limit: int = Query(10, ge=1, le=100, description="Maximum results"),
            server_id: Optional[str] = Query(None, description="Filter by server"),
            tags: Optional[str] = Query(
                None, description="Filter by tags (comma-separated)"
            ),
            current_user: Dict = Depends(self._get_current_user),
        ):
            """Search for tools across servers."""
            try:
                # Search tools
                results = await self.gateway.registry.search_tools(query, limit)

                # Apply filters
                if server_id:
                    results = [t for t in results if t.server_id == server_id]

                if tags:
                    required_tags = set(tags.split(","))
                    results = [
                        t for t in results if required_tags.issubset(set(t.tags))
                    ]

                # Filter by permissions
                filtered_results = []
                for tool in results:
                    if await self.security.can_access_server(
                        current_user.get("user_id"), tool.server_id
                    ):
                        filtered_results.append(tool)

                # Convert to response
                return {
                    "query": query,
                    "total": len(filtered_results),
                    "tools": [
                        {
                            "name": tool.name,
                            "server_id": tool.server_id,
                            "description": tool.description,
                            "category": tool.category.value if tool.category else None,
                            "tags": tool.tags,
                        }
                        for tool in filtered_results[:limit]
                    ],
                }

            except Exception as e:
                logger.error(f"Error searching tools: {e}")
                raise HTTPException(status_code=500, detail="Internal server error")

        @app.get("/api/v1/tools/{server_id}/{tool_name}")
        async def get_tool_details(
            server_id: str,
            tool_name: str,
            current_user: Dict = Depends(self._get_current_user),
        ):
            """Get detailed information about a specific tool."""
            try:
                # Check permissions
                if not await self.security.can_access_server(
                    current_user.get("user_id"), server_id
                ):
                    raise PermissionError("Not authorized to access server")

                # Get tool
                tool = await self.gateway.registry.get_tool(server_id, tool_name)
                if not tool:
                    raise ValueError("Tool not found")

                # Return detailed info
                return {
                    "name": tool.name,
                    "server_id": tool.server_id,
                    "description": tool.description,
                    "input_schema": tool.input_schema,
                    "output_schema": tool.output_schema,
                    "category": tool.category.value if tool.category else None,
                    "tags": tool.tags,
                    "version": tool.version,
                    "execution_count": tool.execution_count,
                    "success_count": tool.success_count,
                    "failure_count": tool.failure_count,
                    "average_duration_ms": tool.average_duration_ms,
                    "last_executed": (
                        tool.last_executed.isoformat() if tool.last_executed else None
                    ),
                    "timeout": tool.timeout,
                    "cache_enabled": tool.cache_enabled,
                    "cache_ttl": tool.cache_ttl,
                    "rate_limit": tool.rate_limit,
                    "required_permissions": tool.required_permissions,
                    "discovered_at": tool.discovered_at.isoformat(),
                    "updated_at": tool.updated_at.isoformat(),
                }

            except ValueError as e:
                raise HTTPException(status_code=404, detail=str(e))
            except PermissionError as e:
                raise HTTPException(status_code=403, detail=str(e))
            except Exception as e:
                logger.error(f"Error getting tool details: {e}")
                raise HTTPException(status_code=500, detail="Internal server error")

        @app.post("/api/v1/tools/execute")
        async def execute_tool(
            request: ToolExecutionRequest,
            background_tasks: BackgroundTasks,
            current_user: Dict = Depends(self._get_current_user),
        ):
            """Execute a tool on an MCP server."""
            try:
                # Validate parameters
                if not await self.security.validate_tool_parameters(
                    current_user.get("user_id"), request.tool_name, request.parameters
                ):
                    raise ValueError("Invalid or suspicious tool parameters")

                # Execute tool
                result = await self.gateway.execute_tool(
                    request.server_id,
                    request.tool_name,
                    request.parameters,
                    user_id=current_user.get("user_id"),
                    execution_options=request.options,
                )

                # Update metrics in background
                if result.get("success"):
                    background_tasks.add_task(
                        self._update_tool_metrics,
                        request.server_id,
                        request.tool_name,
                        result.get("duration_ms", 0),
                        True,
                    )

                return result

            except ValueError as e:
                raise HTTPException(status_code=400, detail=str(e))
            except PermissionError as e:
                raise HTTPException(status_code=403, detail=str(e))
            except RuntimeError as e:
                raise HTTPException(status_code=503, detail=str(e))
            except Exception as e:
                logger.error(f"Error executing tool: {e}")
                raise HTTPException(status_code=500, detail=str(e))

        @app.post("/api/v1/tools/execute/batch")
        async def execute_tools_batch(
            request: BatchExecutionRequest,
            background_tasks: BackgroundTasks,
            current_user: Dict = Depends(self._get_current_user),
        ):
            """Execute multiple tools in batch."""
            try:
                # Validate all executions
                for execution in request.executions:
                    if not await self.security.can_execute_tool(
                        current_user.get("user_id"),
                        execution.server_id,
                        execution.tool_name,
                    ):
                        raise PermissionError(
                            f"Not authorized to execute tool {execution.tool_name}"
                        )

                # Execute tools
                if request.parallel:
                    # Execute in parallel
                    results = await self.gateway.service.batch_execute_tools(
                        [e.dict() for e in request.executions]
                    )
                else:
                    # Execute sequentially
                    results = []
                    for execution in request.executions:
                        try:
                            result = await self.gateway.execute_tool(
                                execution.server_id,
                                execution.tool_name,
                                execution.parameters,
                                user_id=current_user.get("user_id"),
                                execution_options=execution.options,
                            )
                            results.append(result)

                            if not result.get("success") and request.stop_on_error:
                                break

                        except Exception as e:
                            error_result = {
                                "success": False,
                                "error": str(e),
                                "server_id": execution.server_id,
                                "tool_name": execution.tool_name,
                            }
                            results.append(error_result)

                            if request.stop_on_error:
                                break

                # Update metrics in background
                for i, result in enumerate(results):
                    if result.get("success"):
                        execution = request.executions[i]
                        background_tasks.add_task(
                            self._update_tool_metrics,
                            execution.server_id,
                            execution.tool_name,
                            result.get("duration_ms", 0),
                            True,
                        )

                return {
                    "total": len(request.executions),
                    "executed": len(results),
                    "successful": sum(1 for r in results if r.get("success")),
                    "failed": sum(1 for r in results if not r.get("success")),
                    "results": results,
                }

            except PermissionError as e:
                raise HTTPException(status_code=403, detail=str(e))
            except Exception as e:
                logger.error(f"Error executing batch tools: {e}")
                raise HTTPException(status_code=500, detail="Internal server error")

        @app.get("/api/v1/tools/categories")
        async def get_tool_categories(
            current_user: Dict = Depends(self._get_current_user),
        ):
            """Get available tool categories."""
            try:
                # Get all tools user can access
                all_tools = await self.gateway.registry.list_tools()

                # Filter by access permissions
                accessible_tools = []
                for tool in all_tools:
                    if await self.security.can_access_server(
                        current_user.get("user_id"), tool.server_id
                    ):
                        accessible_tools.append(tool)

                # Extract categories
                categories = {}
                for tool in accessible_tools:
                    if tool.category:
                        category = (
                            tool.category.value
                            if hasattr(tool.category, "value")
                            else str(tool.category)
                        )
                        if category not in categories:
                            categories[category] = {
                                "name": category,
                                "tool_count": 0,
                                "description": self._get_category_description(category),
                            }
                        categories[category]["tool_count"] += 1

                return {
                    "total_categories": len(categories),
                    "categories": list(categories.values()),
                }

            except Exception as e:
                logger.error(f"Error getting tool categories: {e}")
                raise HTTPException(status_code=500, detail="Internal server error")

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

    async def _update_tool_metrics(
        self, server_id: str, tool_name: str, duration_ms: float, success: bool
    ):
        """Update tool execution metrics."""
        try:
            await self.gateway.registry.update_tool_metrics(
                server_id, tool_name, duration_ms, success
            )
        except Exception as e:
            logger.error(f"Error updating tool metrics: {e}")

    def _get_category_description(self, category: str) -> str:
        """Get description for a tool category."""
        descriptions = {
            "data": "Tools for data processing and manipulation",
            "analysis": "Tools for data analysis and insights",
            "generation": "Tools for content and code generation",
            "transformation": "Tools for data transformation and conversion",
            "integration": "Tools for system integration and APIs",
            "utility": "General utility and helper tools",
            "admin": "Administrative and management tools",
        }
        return descriptions.get(category.lower(), "Tools in this category")
