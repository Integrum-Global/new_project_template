"""
MCP Application - Main entry point

This is the main application file that creates and runs the MCP management system.
"""

import asyncio
import logging
import os
from contextlib import asynccontextmanager
from datetime import datetime
from typing import Dict, List, Optional

import uvicorn
from fastapi import Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from apps.mcp_platform.core.api.admin_api import AdminAPI
from apps.mcp_platform.core.api.resources_api import ResourcesAPI
from apps.mcp_platform.core.api.servers_api import ServersAPI
from apps.mcp_platform.core.api.tools_api import ToolsAPI
from apps.mcp_platform.core.api.webhooks_api import WebhooksAPI
from apps.mcp_platform.core.config.settings import MCPConfig
from apps.mcp_platform.core.core.gateway import MCPGateway
from apps.mcp_platform.core.core.security import MCPSecurityManager
from kailash.middleware import create_gateway

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class MCPApplication:
    """Main MCP application class."""

    def __init__(self):
        """Initialize the application."""
        self.config = MCPConfig()

        # Core components
        self.gateway = MCPGateway(
            config={
                "database_url": self.config.DATABASE_URL,
                "security": {
                    "jwt_secret": self.config.JWT_SECRET_KEY,
                    "jwt_algorithm": self.config.JWT_ALGORITHM,
                    "access_strategy": self.config.ACCESS_STRATEGY,
                    "rate_limits": self.config.RATE_LIMITS,
                },
                "enable_monitoring": self.config.ENABLE_MONITORING,
                "monitor_interval": self.config.MONITOR_INTERVAL,
            }
        )

        self.security = self.gateway.security

        # API components
        self.servers_api = ServersAPI(self.gateway, self.security)
        self.tools_api = ToolsAPI(self.gateway, self.security)
        self.resources_api = ResourcesAPI(self.gateway, self.security)
        self.admin_api = AdminAPI(self.gateway, self.security)
        self.webhooks_api = WebhooksAPI(self.gateway, self.security)

    async def startup(self):
        """Initialize application on startup."""
        logger.info("Starting MCP Application")

        # Initialize gateway
        await self.gateway.initialize()

        # Load initial servers from config
        if self.config.AUTO_START_SERVERS:
            await self._load_initial_servers()

        logger.info("MCP Application started successfully")

    async def shutdown(self):
        """Cleanup on application shutdown."""
        logger.info("Shutting down MCP Application")

        # Shutdown gateway
        await self.gateway.shutdown()

        logger.info("MCP Application shutdown complete")

    async def _load_initial_servers(self):
        """Load and start servers from configuration."""
        servers_config = self.config.INITIAL_SERVERS

        for server_config in servers_config:
            try:
                server_id = await self.gateway.register_server(
                    server_config, user_id="system"
                )

                if server_config.get("auto_start", False):
                    await self.gateway.start_server(server_id, "system")

                logger.info(f"Loaded server: {server_config['name']}")

            except Exception as e:
                logger.error(f"Failed to load server {server_config['name']}: {e}")

    def create_app(self) -> FastAPI:
        """Create and configure the FastAPI application."""

        @asynccontextmanager
        async def lifespan(app: FastAPI):
            # Startup
            await self.startup()
            yield
            # Shutdown
            await self.shutdown()

        # Create app with Kailash gateway
        gateway = create_gateway(
            title="MCP Management System",
            description="Enterprise-grade Model Context Protocol management built with Kailash SDK",
            version="1.0.0",
        )

        # Get the underlying FastAPI app
        app = gateway.app

        # Set the lifespan manually
        app.router.lifespan_context = lifespan

        # Configure CORS
        app.add_middleware(
            CORSMiddleware,
            allow_origins=self.config.ALLOWED_ORIGINS,
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )

        # Add global middleware
        @app.middleware("http")
        async def add_process_time_header(request, call_next):
            """Add processing time header to responses."""
            import time

            start_time = time.time()
            response = await call_next(request)
            process_time = time.time() - start_time
            response.headers["X-Process-Time"] = str(process_time)
            return response

        # Register API routes
        self._register_routes(app)

        # Add health check
        @app.get("/health")
        async def health_check():
            """Health check endpoint."""
            return {
                "status": "healthy",
                "service": "mcp_management",
                "version": "1.0.0",
            }

        # Add metrics endpoint
        @app.get("/metrics")
        async def metrics():
            """Basic metrics endpoint."""
            stats = self.gateway.service.get_connection_stats()
            security_metrics = self.security.get_security_metrics()

            return {
                "connections": stats,
                "security": security_metrics,
                "timestamp": datetime.utcnow().isoformat(),
            }

        return app

    def _register_routes(self, app: FastAPI):
        """Register all API routes."""
        # Server management routes
        self.servers_api.register_routes(app)

        # Tool management routes
        self.tools_api.register_routes(app)

        # Resource management routes
        self.resources_api.register_routes(app)

        # Admin routes
        self.admin_api.register_routes(app)

        # Webhook routes
        self.webhooks_api.register_routes(app)

        # Authentication routes
        self._register_auth_routes(app)

    def _register_auth_routes(self, app: FastAPI):
        """Register authentication routes."""

        @app.post("/api/v1/auth/login")
        async def login(credentials: Dict):
            """Authenticate and get access token."""
            user_info = await self.security.authenticate_user(credentials)

            if not user_info:
                raise HTTPException(status_code=401, detail="Invalid credentials")

            token = self.security.generate_token(user_info)

            return {
                "access_token": token,
                "token_type": "bearer",
                "user_info": user_info,
            }

        @app.post("/api/v1/auth/api-key")
        async def create_api_key(
            service_name: str,
            roles: List[str],
            permissions: Optional[List[str]] = None,
            expires_in_days: Optional[int] = None,
            current_user: Dict = Depends(self.security.require_admin),
        ):
            """Create API key for service authentication."""
            key = self.security.create_api_key(
                service_name, roles, permissions, expires_in_days
            )

            return {
                "api_key": key,
                "service_name": service_name,
                "roles": roles,
                "permissions": permissions,
                "expires_in_days": expires_in_days,
            }

        @app.delete("/api/v1/auth/api-key/{key}")
        async def revoke_api_key(
            key: str, current_user: Dict = Depends(self.security.require_admin)
        ):
            """Revoke an API key."""
            self.security.revoke_api_key(key)

            return {"status": "revoked", "key": key[:8] + "..."}


def create_mcp_app() -> FastAPI:
    """Factory function to create the MCP app."""
    app_manager = MCPApplication()
    return app_manager.create_app()


if __name__ == "__main__":
    # Create and run the app
    app = create_mcp_app()

    # Get configuration
    config = MCPConfig()

    # Run with uvicorn
    uvicorn.run(
        app,
        host=config.HOST,
        port=config.PORT,
        reload=config.DEBUG,
        log_level="info" if config.DEBUG else "warning",
    )
