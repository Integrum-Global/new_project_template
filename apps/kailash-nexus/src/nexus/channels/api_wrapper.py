"""
API Channel Wrapper for Nexus

Wraps SDK's APIChannel with enterprise features.
"""

import logging
from datetime import datetime, timezone
from typing import Any, Callable, Dict, List, Optional

from kailash.channels.api_channel import APIChannel
from kailash.workflow import Workflow

logger = logging.getLogger(__name__)


class APIChannelWrapper:
    """API Channel wrapper with enterprise features.

    Adds multi-tenant isolation, rate limiting, and metrics
    to the SDK's APIChannel.
    """

    def __init__(
        self,
        api_channel: APIChannel,
        multi_tenant_manager: Optional[Any] = None,
        auth_manager: Optional[Any] = None,
        metrics_collector: Optional[Any] = None,
    ):
        """Initialize API channel wrapper.

        Args:
            api_channel: SDK's APIChannel instance
            multi_tenant_manager: Multi-tenant manager
            auth_manager: Authentication manager
            metrics_collector: Metrics collection service
        """
        self.api_channel = api_channel
        self.multi_tenant_manager = multi_tenant_manager
        self.auth_manager = auth_manager
        self.metrics_collector = metrics_collector

        # Add middleware
        self._setup_middleware()

        logger.info("API channel wrapper initialized")

    def _setup_middleware(self):
        """Setup enterprise middleware."""
        # In production, would add actual middleware to the API channel
        # For now, we'll track this conceptually
        self._middleware = []

        if self.auth_manager:
            self._middleware.append(self._auth_middleware)

        if self.multi_tenant_manager:
            self._middleware.append(self._tenant_middleware)

        if self.metrics_collector:
            self._middleware.append(self._metrics_middleware)

    async def _auth_middleware(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Authentication middleware.

        Args:
            request: Incoming request

        Returns:
            Authenticated request with user context
        """
        # Extract token from request
        token = (
            request.get("headers", {}).get("Authorization", "").replace("Bearer ", "")
        )

        if token and self.auth_manager:
            user_info = self.auth_manager.validate_token(token)
            if user_info:
                request["user"] = user_info
                request["authenticated"] = True
            else:
                request["authenticated"] = False

        return request

    async def _tenant_middleware(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Multi-tenant isolation middleware.

        Args:
            request: Incoming request

        Returns:
            Request with tenant context
        """
        # Extract tenant from user or headers
        tenant_id = None

        if "user" in request:
            tenant_id = request["user"].get("tenant_id")

        if not tenant_id:
            tenant_id = request.get("headers", {}).get("X-Tenant-ID")

        if tenant_id and self.multi_tenant_manager:
            tenant = self.multi_tenant_manager.get_tenant(tenant_id)
            if tenant and tenant.is_active:
                request["tenant"] = tenant.to_dict()
                request["tenant_id"] = tenant_id

        return request

    async def _metrics_middleware(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Metrics collection middleware.

        Args:
            request: Incoming request

        Returns:
            Request with metrics tracking
        """
        request["metrics"] = {
            "start_time": datetime.now(timezone.utc),
            "endpoint": request.get("path"),
            "method": request.get("method"),
        }
        return request

    def register_workflow(
        self,
        path: str,
        workflow: Workflow,
        methods: List[str] = ["POST"],
        auth_required: bool = True,
        tenant_isolated: bool = True,
        rate_limit: Optional[Dict[str, int]] = None,
    ):
        """Register a workflow with enterprise features.

        Args:
            path: API endpoint path
            workflow: Workflow to execute
            methods: HTTP methods
            auth_required: Require authentication
            tenant_isolated: Apply tenant isolation
            rate_limit: Rate limiting config
        """

        # Create wrapped handler
        async def enterprise_handler(request: Dict[str, Any]) -> Dict[str, Any]:
            # Apply middleware
            for middleware in self._middleware:
                request = await middleware(request)

            # Check auth if required
            if auth_required and not request.get("authenticated"):
                return {"status": 401, "body": {"error": "Authentication required"}}

            # Check tenant isolation
            if tenant_isolated and "tenant_id" not in request:
                return {"status": 403, "body": {"error": "Tenant context required"}}

            # Check rate limit
            if rate_limit and self._check_rate_limit(request, rate_limit):
                return {"status": 429, "body": {"error": "Rate limit exceeded"}}

            # Track metrics
            start_time = datetime.now(timezone.utc)

            # Execute workflow through SDK channel
            result = await self.api_channel.handle_request(
                {
                    "path": path,
                    "method": request.get("method", "POST"),
                    "headers": request.get("headers", {}),
                    "body": request.get("body", {}),
                    "query": request.get("query", {}),
                }
            )

            # Record metrics
            if self.metrics_collector:
                elapsed = (datetime.now(timezone.utc) - start_time).total_seconds()
                self.metrics_collector.record(
                    {
                        "type": "api_request",
                        "path": path,
                        "duration": elapsed,
                        "status": result.get("status", 200),
                        "tenant_id": request.get("tenant_id"),
                    }
                )

            return result

        # Register with SDK channel
        self.api_channel.register_route(
            path=path, handler=enterprise_handler, methods=methods
        )

        logger.info(f"Registered enterprise API endpoint: {path}")

    def _check_rate_limit(
        self, request: Dict[str, Any], rate_limit: Dict[str, int]
    ) -> bool:
        """Check if request exceeds rate limit.

        Args:
            request: Request context
            rate_limit: Rate limit config

        Returns:
            True if rate limit exceeded
        """
        # Simplified rate limiting
        # In production, would use Redis or similar
        return False

    def register_health_check(self, path: str = "/health"):
        """Register health check endpoint.

        Args:
            path: Health check path
        """

        async def health_handler(request: Dict[str, Any]) -> Dict[str, Any]:
            health = {
                "status": "healthy",
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "channel": "api",
            }

            # Add component health
            if self.multi_tenant_manager:
                health["multi_tenant"] = await self.multi_tenant_manager.health_check()

            if self.auth_manager:
                health["auth"] = await self.auth_manager.health_check()

            return {"status": 200, "body": health}

        self.api_channel.register_route(
            path=path, handler=health_handler, methods=["GET"]
        )

    def get_routes(self) -> List[Dict[str, Any]]:
        """Get registered routes.

        Returns:
            List of route information
        """
        # Get routes from SDK channel
        routes = []

        if hasattr(self.api_channel, "_routes"):
            for path, route_info in self.api_channel._routes.items():
                routes.append(
                    {
                        "path": path,
                        "methods": route_info.get("methods", ["POST"]),
                        "auth_required": True,  # Default for enterprise
                        "tenant_isolated": True,
                    }
                )

        return routes

    async def start(self):
        """Start the API channel."""
        # Register default health check
        self.register_health_check()

        # Start SDK channel
        await self.api_channel.start()

        logger.info("API channel wrapper started")

    async def stop(self):
        """Stop the API channel."""
        await self.api_channel.stop()
        logger.info("API channel wrapper stopped")
