"""
MCP Resources API

API endpoints for MCP resource management.
"""

import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

from fastapi import Depends, FastAPI, HTTPException, Query
from pydantic import BaseModel

from apps.mcp_platform.core.core.gateway import MCPGateway
from apps.mcp_platform.core.core.security import MCPSecurityManager

logger = logging.getLogger(__name__)


# Pydantic models
class ResourceResponse(BaseModel):
    """Resource response model."""

    uri: str
    name: str
    server_id: str
    description: Optional[str] = None
    mime_type: Optional[str] = None
    size_bytes: Optional[int] = None
    cache_enabled: bool = True
    last_accessed: Optional[str] = None


class ResourcesAPI:
    """API for MCP resource management."""

    def __init__(self, gateway: MCPGateway, security: MCPSecurityManager):
        """Initialize the resources API."""
        self.gateway = gateway
        self.security = security

    def register_routes(self, app: FastAPI):
        """Register resource management routes."""

        @app.get(
            "/api/v1/servers/{server_id}/resources",
            response_model=List[ResourceResponse],
        )
        async def list_server_resources(
            server_id: str,
            refresh: bool = Query(
                False, description="Force refresh resource discovery"
            ),
            current_user: Dict = Depends(self._get_current_user),
        ):
            """List resources available on a server."""
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
                    raise RuntimeError("Server is not running")

                # Discover resources
                resources = await self.gateway.service.discover_resources(
                    server, connection
                )

                # Convert to response models
                return [
                    ResourceResponse(
                        uri=resource.uri,
                        name=resource.name,
                        server_id=resource.server_id,
                        description=resource.description,
                        mime_type=resource.mime_type,
                        size_bytes=resource.size_bytes,
                        cache_enabled=resource.cache_enabled,
                        last_accessed=(
                            resource.last_accessed.isoformat()
                            if resource.last_accessed
                            else None
                        ),
                    )
                    for resource in resources
                ]

            except ValueError as e:
                raise HTTPException(status_code=404, detail=str(e))
            except PermissionError as e:
                raise HTTPException(status_code=403, detail=str(e))
            except RuntimeError as e:
                raise HTTPException(status_code=503, detail=str(e))
            except Exception as e:
                logger.error(f"Error listing resources: {e}")
                raise HTTPException(status_code=500, detail="Internal server error")

        @app.get("/api/v1/resources/{server_id}/{resource_uri:path}")
        async def get_resource(
            server_id: str,
            resource_uri: str,
            current_user: Dict = Depends(self._get_current_user),
        ):
            """Get a specific resource from a server."""
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
                    raise RuntimeError("Server is not running")

                # Get resource
                result = await self.gateway.service.get_resource(
                    server, connection, resource_uri
                )

                if not result.get("success"):
                    raise ValueError(result.get("error", "Failed to get resource"))

                return {
                    "uri": resource_uri,
                    "server_id": server_id,
                    "content": result.get("content"),
                    "mime_type": result.get("mime_type"),
                    "metadata": result.get("metadata", {}),
                    "cached": False,  # TODO: Check if cached
                }

            except ValueError as e:
                raise HTTPException(status_code=404, detail=str(e))
            except PermissionError as e:
                raise HTTPException(status_code=403, detail=str(e))
            except RuntimeError as e:
                raise HTTPException(status_code=503, detail=str(e))
            except Exception as e:
                logger.error(f"Error getting resource: {e}")
                raise HTTPException(status_code=500, detail="Internal server error")

        @app.get("/api/v1/resources/search")
        async def search_resources(
            query: str = Query(..., description="Search query"),
            server_id: Optional[str] = Query(None, description="Filter by server"),
            mime_type: Optional[str] = Query(None, description="Filter by MIME type"),
            limit: int = Query(20, ge=1, le=100, description="Maximum results"),
            current_user: Dict = Depends(self._get_current_user),
        ):
            """Search for resources across servers."""
            try:
                # Get all servers user can access
                servers = await self.gateway.list_servers(
                    user_id=current_user.get("user_id")
                )

                # Search resources
                all_resources = []
                for server in servers:
                    if server_id and server.id != server_id:
                        continue

                    # Skip if server not running
                    if server.id not in self.gateway._active_connections:
                        continue

                    try:
                        # Get server resources
                        connection = self.gateway._active_connections[server.id]
                        resources = await self.gateway.service.discover_resources(
                            server, connection
                        )

                        # Filter by query and mime type
                        for resource in resources:
                            if query.lower() in resource.name.lower() or (
                                resource.description
                                and query.lower() in resource.description.lower()
                            ):
                                if not mime_type or resource.mime_type == mime_type:
                                    all_resources.append(resource)

                    except Exception as e:
                        logger.warning(
                            f"Error searching resources on server {server.id}: {e}"
                        )

                # Sort by relevance (simple name match first)
                all_resources.sort(
                    key=lambda r: (query.lower() not in r.name.lower(), r.name)
                )

                # Limit results
                limited_resources = all_resources[:limit]

                return {
                    "query": query,
                    "total": len(all_resources),
                    "returned": len(limited_resources),
                    "resources": [
                        {
                            "uri": resource.uri,
                            "name": resource.name,
                            "server_id": resource.server_id,
                            "description": resource.description,
                            "mime_type": resource.mime_type,
                            "size_bytes": resource.size_bytes,
                        }
                        for resource in limited_resources
                    ],
                }

            except Exception as e:
                logger.error(f"Error searching resources: {e}")
                raise HTTPException(status_code=500, detail="Internal server error")

        @app.post("/api/v1/resources/{server_id}/cache")
        async def cache_resource(
            server_id: str,
            resource_uri: str,
            ttl: Optional[int] = Query(None, description="Cache TTL in seconds"),
            current_user: Dict = Depends(self._get_current_user),
        ):
            """Cache a resource for faster access."""
            try:
                # Check permissions
                if not await self.security.can_access_server(
                    current_user.get("user_id"), server_id
                ):
                    raise PermissionError("Not authorized to access server")

                # TODO: Implement resource caching

                return {
                    "status": "cached",
                    "server_id": server_id,
                    "resource_uri": resource_uri,
                    "ttl": ttl or 3600,
                    "cached_at": datetime.utcnow().isoformat(),
                }

            except PermissionError as e:
                raise HTTPException(status_code=403, detail=str(e))
            except Exception as e:
                logger.error(f"Error caching resource: {e}")
                raise HTTPException(status_code=500, detail="Internal server error")

        @app.delete("/api/v1/resources/{server_id}/cache")
        async def clear_resource_cache(
            server_id: str,
            resource_uri: Optional[str] = Query(
                None, description="Specific resource to clear"
            ),
            current_user: Dict = Depends(self._get_current_user),
        ):
            """Clear cached resources."""
            try:
                # Check permissions
                if not await self.security.can_manage_server(
                    current_user.get("user_id"), server_id
                ):
                    raise PermissionError("Not authorized to manage server")

                # TODO: Implement cache clearing

                return {
                    "status": "cleared",
                    "server_id": server_id,
                    "resource_uri": resource_uri,
                    "cleared_at": datetime.utcnow().isoformat(),
                }

            except PermissionError as e:
                raise HTTPException(status_code=403, detail=str(e))
            except Exception as e:
                logger.error(f"Error clearing resource cache: {e}")
                raise HTTPException(status_code=500, detail="Internal server error")

        @app.get("/api/v1/resources/stats")
        async def get_resource_stats(
            server_id: Optional[str] = Query(None, description="Filter by server"),
            current_user: Dict = Depends(self._get_current_user),
        ):
            """Get resource usage statistics."""
            try:
                # Get servers
                if server_id:
                    # Check permissions
                    if not await self.security.can_access_server(
                        current_user.get("user_id"), server_id
                    ):
                        raise PermissionError("Not authorized to access server")
                    servers = [await self.gateway.registry.get_server(server_id)]
                else:
                    servers = await self.gateway.list_servers(
                        user_id=current_user.get("user_id")
                    )

                # Collect stats
                stats = {
                    "total_servers": len(servers),
                    "total_resources": 0,
                    "total_size_bytes": 0,
                    "cached_resources": 0,
                    "by_mime_type": {},
                    "by_server": {},
                }

                for server in servers:
                    if server.id not in self.gateway._active_connections:
                        continue

                    try:
                        # Get resources
                        connection = self.gateway._active_connections[server.id]
                        resources = await self.gateway.service.discover_resources(
                            server, connection
                        )

                        server_stats = {
                            "resource_count": len(resources),
                            "total_size_bytes": 0,
                            "by_mime_type": {},
                        }

                        for resource in resources:
                            stats["total_resources"] += 1

                            if resource.size_bytes:
                                stats["total_size_bytes"] += resource.size_bytes
                                server_stats["total_size_bytes"] += resource.size_bytes

                            if resource.cache_enabled:
                                stats["cached_resources"] += 1

                            # Count by MIME type
                            mime_type = resource.mime_type or "unknown"
                            stats["by_mime_type"][mime_type] = (
                                stats["by_mime_type"].get(mime_type, 0) + 1
                            )
                            server_stats["by_mime_type"][mime_type] = (
                                server_stats["by_mime_type"].get(mime_type, 0) + 1
                            )

                        stats["by_server"][server.id] = server_stats

                    except Exception as e:
                        logger.warning(
                            f"Error getting resources for server {server.id}: {e}"
                        )

                return stats

            except PermissionError as e:
                raise HTTPException(status_code=403, detail=str(e))
            except Exception as e:
                logger.error(f"Error getting resource stats: {e}")
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
