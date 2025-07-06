"""Enterprise Gateway Client SDK."""

import asyncio
from datetime import datetime, timedelta
from typing import Any, AsyncIterator, Dict, List, Optional

import httpx
import jwt
import structlog
from tenacity import retry, stop_after_attempt, wait_exponential

logger = structlog.get_logger(__name__)


class GatewayClient:
    """Client for interacting with the Enterprise Gateway."""

    def __init__(
        self,
        base_url: str,
        api_key: Optional[str] = None,
        oauth_config: Optional[Dict[str, Any]] = None,
        tenant_id: Optional[str] = None,
        timeout: int = 30,
        retry_config: Optional[Dict[str, Any]] = None,
    ):

        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.oauth_config = oauth_config
        self.tenant_id = tenant_id
        self.timeout = timeout
        self.retry_config = retry_config or {
            "stop": stop_after_attempt(3),
            "wait": wait_exponential(multiplier=1, min=4, max=10),
        }

        self._client = None
        self._token = None
        self._token_expires = None

    async def __aenter__(self):
        """Async context manager entry."""
        self._client = httpx.AsyncClient(timeout=self.timeout)
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        if self._client:
            await self._client.aclose()

    async def _get_headers(self) -> Dict[str, str]:
        """Get request headers with authentication."""
        headers = {"Content-Type": "application/json", "Accept": "application/json"}

        if self.tenant_id:
            headers["X-Tenant-ID"] = self.tenant_id

        if self.api_key:
            headers["X-API-Key"] = self.api_key
        elif self.oauth_config:
            token = await self._get_oauth_token()
            headers["Authorization"] = f"Bearer {token}"

        return headers

    async def _get_oauth_token(self) -> str:
        """Get OAuth token, refreshing if needed."""
        if (
            self._token
            and self._token_expires
            and datetime.utcnow() < self._token_expires
        ):
            return self._token

        # Get new token
        async with httpx.AsyncClient() as client:
            response = await client.post(
                self.oauth_config["token_url"],
                data={
                    "grant_type": "client_credentials",
                    "client_id": self.oauth_config["client_id"],
                    "client_secret": self.oauth_config["client_secret"],
                    "scope": self.oauth_config.get("scope", ""),
                },
            )
            response.raise_for_status()

            data = response.json()
            self._token = data["access_token"]
            expires_in = data.get("expires_in", 3600)
            self._token_expires = datetime.utcnow() + timedelta(seconds=expires_in - 60)

            return self._token

    @retry(**retry_config)
    async def execute_tool(
        self,
        tool_name: str,
        action: str = "default",
        params: Optional[Dict[str, Any]] = None,
        options: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Execute a tool on the gateway."""
        if not self._client:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                return await self._execute_tool_request(
                    client, tool_name, action, params, options
                )
        else:
            return await self._execute_tool_request(
                self._client, tool_name, action, params, options
            )

    async def _execute_tool_request(
        self,
        client: httpx.AsyncClient,
        tool_name: str,
        action: str,
        params: Optional[Dict[str, Any]],
        options: Optional[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """Execute tool request."""
        headers = await self._get_headers()

        response = await client.post(
            f"{self.base_url}/api/v1/tools/{tool_name}/execute",
            headers=headers,
            json={"action": action, "params": params or {}, "options": options or {}},
        )

        response.raise_for_status()
        return response.json()

    async def list_tools(self) -> List[Dict[str, Any]]:
        """List available tools."""
        headers = await self._get_headers()

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.get(
                f"{self.base_url}/api/v1/tools", headers=headers
            )
            response.raise_for_status()

            data = response.json()
            return data.get("tools", [])

    async def get_tool(self, tool_name: str) -> Dict[str, Any]:
        """Get tool details."""
        headers = await self._get_headers()

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.get(
                f"{self.base_url}/api/v1/tools/{tool_name}", headers=headers
            )
            response.raise_for_status()

            return response.json()

    def for_tenant(self, tenant_id: str) -> "GatewayClient":
        """Create a client for a specific tenant."""
        return GatewayClient(
            base_url=self.base_url,
            api_key=self.api_key,
            oauth_config=self.oauth_config,
            tenant_id=tenant_id,
            timeout=self.timeout,
            retry_config=self.retry_config,
        )

    async def stream_execute(
        self,
        tool_name: str,
        action: str = "default",
        params: Optional[Dict[str, Any]] = None,
    ) -> AsyncIterator[Dict[str, Any]]:
        """Execute tool with streaming response."""
        headers = await self._get_headers()
        headers["Accept"] = "text/event-stream"

        async with httpx.AsyncClient(timeout=None) as client:
            async with client.stream(
                "POST",
                f"{self.base_url}/api/v1/tools/{tool_name}/execute",
                headers=headers,
                json={
                    "action": action,
                    "params": params or {},
                    "options": {"stream": True},
                },
            ) as response:
                response.raise_for_status()

                async for line in response.aiter_lines():
                    if line.startswith("data: "):
                        data = line[6:]
                        if data == "[DONE]":
                            break

                        import json

                        yield json.loads(data)


class ToolProxy:
    """Proxy for convenient tool access."""

    def __init__(self, client: GatewayClient, tool_name: str):
        self.client = client
        self.tool_name = tool_name

    async def __call__(self, **params) -> Dict[str, Any]:
        """Execute tool with default action."""
        return await self.client.execute_tool(self.tool_name, params=params)

    def __getattr__(self, action: str):
        """Get action executor."""

        async def execute(**params):
            return await self.client.execute_tool(
                self.tool_name, action=action, params=params
            )

        return execute


class Tools:
    """Tool accessor for convenient access."""

    def __init__(self, client: GatewayClient):
        self.client = client
        self._tools = {}

    def __getattr__(self, tool_name: str) -> ToolProxy:
        """Get tool proxy."""
        if tool_name not in self._tools:
            self._tools[tool_name] = ToolProxy(self.client, tool_name)
        return self._tools[tool_name]


class Gateway:
    """High-level gateway interface."""

    def __init__(self, url: str, auth: Dict[str, Any]):
        if "api_key" in auth:
            self.client = GatewayClient(url, api_key=auth["api_key"])
        elif "oauth" in auth:
            self.client = GatewayClient(url, oauth_config=auth["oauth"])
        else:
            raise ValueError("No valid authentication provided")

        self.tools = Tools(self.client)

    async def __aenter__(self):
        """Async context manager entry."""
        await self.client.__aenter__()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.client.__aexit__(exc_type, exc_val, exc_tb)

    def tool(self, name: str):
        """Decorator for registering local tools."""

        def decorator(func):
            # In a real implementation, this would register the tool
            # with the gateway for remote execution
            return func

        return decorator


# Usage tracking and monitoring
class UsageTracker:
    """Track API usage for billing and monitoring."""

    def __init__(self, client: GatewayClient):
        self.client = client
        self.requests = []
        self.start_time = datetime.utcnow()

    async def track_request(
        self, tool: str, action: str, response_time: float, success: bool
    ):
        """Track a request."""
        self.requests.append(
            {
                "timestamp": datetime.utcnow(),
                "tool": tool,
                "action": action,
                "response_time": response_time,
                "success": success,
            }
        )

    def get_stats(self) -> Dict[str, Any]:
        """Get usage statistics."""
        if not self.requests:
            return {"total_requests": 0, "success_rate": 0, "average_response_time": 0}

        total = len(self.requests)
        successful = sum(1 for r in self.requests if r["success"])
        avg_response_time = sum(r["response_time"] for r in self.requests) / total

        return {
            "total_requests": total,
            "success_rate": successful / total,
            "average_response_time": avg_response_time,
            "duration": (datetime.utcnow() - self.start_time).total_seconds(),
            "requests_per_second": total
            / (datetime.utcnow() - self.start_time).total_seconds(),
        }


# Batch operations
class BatchExecutor:
    """Execute multiple operations in batch."""

    def __init__(self, client: GatewayClient):
        self.client = client
        self.operations = []

    def add(
        self,
        tool: str,
        action: str = "default",
        params: Optional[Dict[str, Any]] = None,
    ):
        """Add operation to batch."""
        self.operations.append({"tool": tool, "action": action, "params": params or {}})
        return self

    async def execute(self, concurrency: int = 5) -> List[Dict[str, Any]]:
        """Execute all operations with limited concurrency."""
        semaphore = asyncio.Semaphore(concurrency)

        async def execute_one(op):
            async with semaphore:
                try:
                    result = await self.client.execute_tool(
                        op["tool"], op["action"], op["params"]
                    )
                    return {"success": True, "result": result, "operation": op}
                except Exception as e:
                    return {"success": False, "error": str(e), "operation": op}

        results = await asyncio.gather(*[execute_one(op) for op in self.operations])

        # Clear operations after execution
        self.operations.clear()

        return results


# Circuit breaker for resilience
class CircuitBreakerClient(GatewayClient):
    """Gateway client with circuit breaker pattern."""

    def __init__(
        self, *args, failure_threshold: int = 5, recovery_timeout: int = 60, **kwargs
    ):
        super().__init__(*args, **kwargs)

        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.failure_count = 0
        self.last_failure_time = None
        self.is_open = False

    async def execute_tool(self, *args, **kwargs) -> Dict[str, Any]:
        """Execute with circuit breaker."""
        # Check if circuit is open
        if self.is_open:
            if datetime.utcnow() - self.last_failure_time < timedelta(
                seconds=self.recovery_timeout
            ):
                raise Exception("Circuit breaker is open")
            else:
                # Try to close circuit
                self.is_open = False
                self.failure_count = 0

        try:
            result = await super().execute_tool(*args, **kwargs)

            # Reset failure count on success
            self.failure_count = 0

            return result

        except Exception as e:
            self.failure_count += 1
            self.last_failure_time = datetime.utcnow()

            if self.failure_count >= self.failure_threshold:
                self.is_open = True
                logger.warning(
                    f"Circuit breaker opened after {self.failure_count} failures"
                )

            raise
