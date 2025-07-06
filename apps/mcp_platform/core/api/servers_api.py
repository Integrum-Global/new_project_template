"""
MCP Servers API

API endpoints for MCP server management.
"""

import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

from fastapi import Depends, FastAPI, HTTPException, Query
from pydantic import BaseModel

from apps.mcp_platform.core.core.gateway import MCPGateway
from apps.mcp_platform.core.core.security import MCPSecurityManager

logger = logging.getLogger(__name__)


# Pydantic models for request/response
class ServerConfig(BaseModel):
    """Server configuration model."""

    name: str
    transport: str
    config: Dict[str, Any]
    auto_start: bool = False
    tags: List[str] = []
    description: Optional[str] = None


class ServerUpdate(BaseModel):
    """Server update model."""

    name: Optional[str] = None
    tags: Optional[List[str]] = None
    description: Optional[str] = None
    auto_start: Optional[bool] = None


class ServerResponse(BaseModel):
    """Server response model."""

    id: str
    name: str
    transport: str
    status: str
    created_at: str
    tool_count: int = 0
    tags: List[str] = []
    description: Optional[str] = None


class ServersAPI:
    """API for MCP server management."""

    def __init__(self, gateway: MCPGateway, security: MCPSecurityManager):
        """Initialize the servers API."""
        self.gateway = gateway
        self.security = security

    def register_routes(self, app: FastAPI):
        """Register server management routes."""

        @app.post("/api/v1/servers", response_model=ServerResponse)
        async def create_server(
            server_config: ServerConfig,
            current_user: Dict = Depends(self._get_current_user),
        ):
            """Register a new MCP server."""
            try:
                # Convert to dict and add metadata
                config_dict = server_config.dict()
                config_dict["tags"] = server_config.tags
                config_dict["description"] = server_config.description

                # Register server
                server_id = await self.gateway.register_server(
                    config_dict, user_id=current_user.get("user_id")
                )

                # Get server details
                server = await self.gateway.registry.get_server(server_id)

                return ServerResponse(
                    id=server.id,
                    name=server.name,
                    transport=server.transport,
                    status=server.status.value,
                    created_at=server.created_at.isoformat(),
                    tool_count=server.tool_count,
                    tags=server.tags,
                    description=server.description,
                )

            except ValueError as e:
                raise HTTPException(status_code=400, detail=str(e))
            except PermissionError as e:
                raise HTTPException(status_code=403, detail=str(e))
            except Exception as e:
                logger.error(f"Error creating server: {e}")
                raise HTTPException(status_code=500, detail="Internal server error")

        @app.get("/api/v1/servers", response_model=List[ServerResponse])
        async def list_servers(
            status: Optional[str] = Query(None, description="Filter by status"),
            transport: Optional[str] = Query(None, description="Filter by transport"),
            tags: Optional[str] = Query(
                None, description="Filter by tags (comma-separated)"
            ),
            current_user: Dict = Depends(self._get_current_user),
        ):
            """List MCP servers."""
            try:
                # Build filters
                filters = {}
                if status:
                    filters["status"] = status
                if transport:
                    filters["transport"] = transport
                if tags:
                    filters["tags"] = tags.split(",")

                # Get servers
                servers = await self.gateway.list_servers(
                    user_id=current_user.get("user_id"), filters=filters
                )

                # Convert to response models
                return [
                    ServerResponse(
                        id=server.id,
                        name=server.name,
                        transport=server.transport,
                        status=server.status.value,
                        created_at=server.created_at.isoformat(),
                        tool_count=server.tool_count,
                        tags=server.tags,
                        description=server.description,
                    )
                    for server in servers
                ]

            except Exception as e:
                logger.error(f"Error listing servers: {e}")
                raise HTTPException(status_code=500, detail="Internal server error")

        @app.get("/api/v1/servers/{server_id}")
        async def get_server(
            server_id: str, current_user: Dict = Depends(self._get_current_user)
        ):
            """Get detailed server information."""
            try:
                # Get server status
                status = await self.gateway.get_server_status(
                    server_id, user_id=current_user.get("user_id")
                )

                return status

            except ValueError as e:
                raise HTTPException(status_code=404, detail=str(e))
            except PermissionError as e:
                raise HTTPException(status_code=403, detail=str(e))
            except Exception as e:
                logger.error(f"Error getting server: {e}")
                raise HTTPException(status_code=500, detail="Internal server error")

        @app.put("/api/v1/servers/{server_id}")
        async def update_server(
            server_id: str,
            update: ServerUpdate,
            current_user: Dict = Depends(self._get_current_user),
        ):
            """Update server configuration."""
            try:
                # Check permissions
                if not await self.security.can_manage_server(
                    current_user.get("user_id"), server_id
                ):
                    raise PermissionError("Not authorized to manage server")

                # Get server
                server = await self.gateway.registry.get_server(server_id)
                if not server:
                    raise ValueError("Server not found")

                # Update fields
                if update.name is not None:
                    server.name = update.name
                if update.tags is not None:
                    server.tags = update.tags
                if update.description is not None:
                    server.description = update.description
                if update.auto_start is not None:
                    server.auto_start = update.auto_start

                # Save updates
                await self.gateway.registry.update_server(server)

                return {"status": "updated", "server_id": server_id}

            except ValueError as e:
                raise HTTPException(status_code=404, detail=str(e))
            except PermissionError as e:
                raise HTTPException(status_code=403, detail=str(e))
            except Exception as e:
                logger.error(f"Error updating server: {e}")
                raise HTTPException(status_code=500, detail="Internal server error")

        @app.post("/api/v1/servers/{server_id}/start")
        async def start_server(
            server_id: str, current_user: Dict = Depends(self._get_current_user)
        ):
            """Start an MCP server."""
            try:
                result = await self.gateway.start_server(
                    server_id, user_id=current_user.get("user_id")
                )

                return result

            except ValueError as e:
                raise HTTPException(status_code=404, detail=str(e))
            except PermissionError as e:
                raise HTTPException(status_code=403, detail=str(e))
            except Exception as e:
                logger.error(f"Error starting server: {e}")
                raise HTTPException(status_code=500, detail=str(e))

        @app.post("/api/v1/servers/{server_id}/stop")
        async def stop_server(
            server_id: str, current_user: Dict = Depends(self._get_current_user)
        ):
            """Stop an MCP server."""
            try:
                result = await self.gateway.stop_server(
                    server_id, user_id=current_user.get("user_id")
                )

                return result

            except ValueError as e:
                raise HTTPException(status_code=404, detail=str(e))
            except PermissionError as e:
                raise HTTPException(status_code=403, detail=str(e))
            except Exception as e:
                logger.error(f"Error stopping server: {e}")
                raise HTTPException(status_code=500, detail="Internal server error")

        @app.delete("/api/v1/servers/{server_id}")
        async def delete_server(
            server_id: str, current_user: Dict = Depends(self._get_current_user)
        ):
            """Delete an MCP server."""
            try:
                # Check permissions
                if not await self.security.can_manage_server(
                    current_user.get("user_id"), server_id
                ):
                    raise PermissionError("Not authorized to delete server")

                # Stop server if running
                try:
                    await self.gateway.stop_server(
                        server_id, user_id=current_user.get("user_id")
                    )
                except:
                    pass  # Server might not be running

                # Delete from registry
                # TODO: Implement delete in registry

                return {"status": "deleted", "server_id": server_id}

            except PermissionError as e:
                raise HTTPException(status_code=403, detail=str(e))
            except Exception as e:
                logger.error(f"Error deleting server: {e}")
                raise HTTPException(status_code=500, detail="Internal server error")

        @app.get("/api/v1/servers/{server_id}/health")
        async def check_server_health(
            server_id: str, current_user: Dict = Depends(self._get_current_user)
        ):
            """Check server health status."""
            try:
                # Check permissions
                if not await self.security.can_access_server(
                    current_user.get("user_id"), server_id
                ):
                    raise PermissionError("Not authorized to access server")

                # Get server
                server = await self.gateway.registry.get_server(server_id)
                if not server:
                    raise ValueError("Server not found")

                # Get connection
                connection = self.gateway._active_connections.get(server_id)
                if not connection:
                    return {
                        "server_id": server_id,
                        "healthy": False,
                        "status": "not_running",
                        "error": "Server is not running",
                    }

                # Check health
                health = await self.gateway.service.check_health(server, connection)
                health["server_id"] = server_id

                return health

            except ValueError as e:
                raise HTTPException(status_code=404, detail=str(e))
            except PermissionError as e:
                raise HTTPException(status_code=403, detail=str(e))
            except Exception as e:
                logger.error(f"Error checking server health: {e}")
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
