#!/usr/bin/env python3
"""Production MCP Server - Full-featured implementation with auth, caching, and monitoring."""

import asyncio
import hashlib
import json
import logging
import os
import statistics
import time
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from kailash.mcp_server import MCPServer
from kailash.mcp_server.auth import APIKeyAuth, BearerTokenAuth
from kailash.mcp_server.discovery import ServiceRegistry
from kailash.mcp_server.errors import ToolExecutionError

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class ProductionMCPServer:
    """Production-ready MCP server with full features."""

    def __init__(
        self, name: str = "production-mcp-server", config_file: Optional[str] = None
    ):
        """Initialize production server with configuration."""
        self.name = name
        self.config = self._load_config(config_file)
        self.server = self._create_server()
        self.discovery = (
            ServiceRegistry()
            if self.config.get("discovery", {}).get("enabled", True)
            else None
        )

    def _load_config(self, config_file: Optional[str]) -> Dict[str, Any]:
        """Load configuration from file or use defaults."""
        default_config = {
            "server": {"host": "0.0.0.0", "port": 8080, "workers": 4},
            "auth": {
                "enabled": True,
                "type": "bearer",
                "token": os.getenv("MCP_AUTH_TOKEN", "production-secret-token"),
            },
            "cache": {"enabled": True, "ttl": 300, "max_size": 1000},
            "metrics": {"enabled": True, "export_interval": 60},
            "discovery": {"enabled": True, "health_check_interval": 30},
        }

        if config_file and Path(config_file).exists():
            with open(config_file) as f:
                loaded_config = json.load(f)
                # Merge with defaults
                return {**default_config, **loaded_config}

        return default_config

    def _create_server(self) -> MCPServer:
        """Create MCP server with configuration."""
        # Setup authentication
        auth = None
        if self.config["auth"]["enabled"]:
            auth_type = self.config["auth"]["type"]
            if auth_type == "bearer":
                auth = BearerTokenAuth(token=self.config["auth"]["token"])
            elif auth_type == "api_key":
                auth = APIKeyAuth(api_keys=self.config["auth"].get("api_keys", []))

        # Create server with correct parameters
        server = MCPServer(
            self.name,
            auth_provider=auth,
            enable_cache=self.config["cache"]["enabled"],
            cache_ttl=self.config["cache"]["ttl"],
            enable_metrics=self.config["metrics"]["enabled"],
            cache_backend="memory",
        )

        # Register all tools
        self._register_math_tools(server)
        self._register_data_tools(server)
        self._register_file_tools(server)
        self._register_utility_tools(server)
        self._register_resources(server)

        return server

    def _register_math_tools(self, server: MCPServer):
        """Register mathematical operation tools."""

        @server.tool()
        async def calculate(a: float, b: float, operation: str) -> Dict[str, Any]:
            """Perform arithmetic operations."""
            operations = {
                "add": lambda x, y: x + y,
                "subtract": lambda x, y: x - y,
                "multiply": lambda x, y: x * y,
                "divide": lambda x, y: x / y if y != 0 else None,
                "power": lambda x, y: x**y,
                "modulo": lambda x, y: x % y if y != 0 else None,
            }

            if operation not in operations:
                raise ToolExecutionError(f"Unknown operation: {operation}")

            result = operations[operation](a, b)
            if result is None:
                raise ToolExecutionError("Invalid operation (division by zero)")

            return {
                "result": result,
                "operation": operation,
                "inputs": {"a": a, "b": b},
            }

        @server.tool(cache_key="factorial_{n}")
        def factorial(n: int) -> Dict[str, Any]:
            """Calculate factorial of a number."""
            if n < 0:
                raise ToolExecutionError("Factorial not defined for negative numbers")
            if n > 20:
                raise ToolExecutionError("Number too large (max 20)")

            result = 1
            for i in range(1, n + 1):
                result *= i

            return {"result": result, "input": n}

        @server.tool()
        def fibonacci(n: int) -> Dict[str, Any]:
            """Generate Fibonacci sequence up to n terms."""
            if n <= 0:
                raise ToolExecutionError("Number of terms must be positive")
            if n > 100:
                raise ToolExecutionError("Too many terms (max 100)")

            sequence = []
            a, b = 0, 1
            for _ in range(n):
                sequence.append(a)
                a, b = b, a + b

            return {"sequence": sequence, "count": n}

        @server.tool()
        def statistics_calc(
            numbers: List[float], operations: List[str] = None
        ) -> Dict[str, Any]:
            """Calculate statistical measures."""
            if not numbers:
                raise ToolExecutionError("Numbers list cannot be empty")

            if operations is None:
                operations = ["mean", "median", "mode", "stdev"]

            results = {}

            if "mean" in operations:
                results["mean"] = statistics.mean(numbers)
            if "median" in operations:
                results["median"] = statistics.median(numbers)
            if "mode" in operations:
                try:
                    results["mode"] = statistics.mode(numbers)
                except statistics.StatisticsError:
                    results["mode"] = "No unique mode"
            if "stdev" in operations and len(numbers) > 1:
                results["stdev"] = statistics.stdev(numbers)
            if "min" in operations:
                results["min"] = min(numbers)
            if "max" in operations:
                results["max"] = max(numbers)

            return {"results": results, "count": len(numbers), "input": numbers}

    def _register_data_tools(self, server: MCPServer):
        """Register data processing tools."""

        @server.tool()
        def json_parse(json_string: str) -> Dict[str, Any]:
            """Parse and validate JSON string."""
            try:
                data = json.loads(json_string)
                return {"valid": True, "data": data, "type": type(data).__name__}
            except json.JSONDecodeError as e:
                return {
                    "valid": False,
                    "error": str(e),
                    "position": e.pos if hasattr(e, "pos") else None,
                }

        @server.tool()
        def data_transform(
            data: Dict[str, Any], operations: List[Dict[str, Any]]
        ) -> Dict[str, Any]:
            """Transform data with a series of operations."""
            result = data.copy()

            for op in operations:
                op_type = op.get("type")

                if op_type == "filter":
                    key = op.get("key")
                    value = op.get("value")
                    if isinstance(result, list):
                        result = [item for item in result if item.get(key) == value]

                elif op_type == "map":
                    field = op.get("field")
                    transform = op.get("transform")
                    if isinstance(result, list):
                        for item in result:
                            if field in item:
                                if transform == "uppercase":
                                    item[field] = str(item[field]).upper()
                                elif transform == "lowercase":
                                    item[field] = str(item[field]).lower()

                elif op_type == "sort":
                    key = op.get("key")
                    reverse = op.get("reverse", False)
                    if isinstance(result, list):
                        result.sort(key=lambda x: x.get(key, ""), reverse=reverse)

            return {"transformed": result, "operations_applied": len(operations)}

        @server.tool(cache_key="aggregate_{data_hash}")
        def aggregate(
            data: List[Dict[str, Any]],
            group_by: str,
            aggregate_field: str,
            operation: str,
        ) -> Dict[str, Any]:
            """Aggregate data by grouping."""
            groups = {}

            for item in data:
                key = item.get(group_by)
                if key not in groups:
                    groups[key] = []

                value = item.get(aggregate_field)
                if value is not None:
                    groups[key].append(value)

            results = {}
            for key, values in groups.items():
                if operation == "sum":
                    results[key] = sum(values)
                elif operation == "avg":
                    results[key] = sum(values) / len(values) if values else 0
                elif operation == "count":
                    results[key] = len(values)
                elif operation == "min":
                    results[key] = min(values) if values else None
                elif operation == "max":
                    results[key] = max(values) if values else None

            return {
                "aggregated": results,
                "groups": len(results),
                "operation": operation,
            }

    def _register_file_tools(self, server: MCPServer):
        """Register file operation tools."""

        @server.tool()
        def read_file(path: str, encoding: str = "utf-8") -> Dict[str, Any]:
            """Read file contents."""
            try:
                file_path = Path(path)
                if not file_path.exists():
                    raise ToolExecutionError(f"File not found: {path}")

                content = file_path.read_text(encoding=encoding)
                return {
                    "content": content,
                    "size": len(content),
                    "lines": content.count("\n") + 1,
                    "path": str(file_path.absolute()),
                }
            except Exception as e:
                raise ToolExecutionError(f"Error reading file: {e}")

        @server.tool()
        def write_file(
            path: str, content: str, encoding: str = "utf-8"
        ) -> Dict[str, Any]:
            """Write content to file."""
            try:
                file_path = Path(path)
                file_path.parent.mkdir(parents=True, exist_ok=True)

                file_path.write_text(content, encoding=encoding)
                return {
                    "written": True,
                    "size": len(content),
                    "path": str(file_path.absolute()),
                }
            except Exception as e:
                raise ToolExecutionError(f"Error writing file: {e}")

        @server.tool()
        def list_directory(path: str = ".", pattern: str = "*") -> Dict[str, Any]:
            """List directory contents."""
            try:
                dir_path = Path(path)
                if not dir_path.exists():
                    raise ToolExecutionError(f"Directory not found: {path}")

                files = []
                for item in dir_path.glob(pattern):
                    files.append(
                        {
                            "name": item.name,
                            "type": "directory" if item.is_dir() else "file",
                            "size": item.stat().st_size if item.is_file() else None,
                            "modified": datetime.fromtimestamp(
                                item.stat().st_mtime
                            ).isoformat(),
                        }
                    )

                return {
                    "files": files,
                    "count": len(files),
                    "path": str(dir_path.absolute()),
                }
            except Exception as e:
                raise ToolExecutionError(f"Error listing directory: {e}")

    def _register_utility_tools(self, server: MCPServer):
        """Register utility tools."""

        @server.tool()
        def datetime_now(format: str = "%Y-%m-%d %H:%M:%S") -> Dict[str, Any]:
            """Get current datetime."""
            now = datetime.now()
            return {
                "datetime": now.strftime(format),
                "timestamp": now.timestamp(),
                "iso": now.isoformat(),
            }

        @server.tool()
        def uuid_generate(version: int = 4) -> Dict[str, Any]:
            """Generate UUID."""
            if version == 1:
                uid = uuid.uuid1()
            elif version == 4:
                uid = uuid.uuid4()
            else:
                raise ToolExecutionError(f"Unsupported UUID version: {version}")

            return {"uuid": str(uid), "version": version, "hex": uid.hex}

        @server.tool()
        def hash_data(data: str, algorithm: str = "sha256") -> Dict[str, Any]:
            """Hash data with specified algorithm."""
            algorithms = ["md5", "sha1", "sha256", "sha512"]

            if algorithm not in algorithms:
                raise ToolExecutionError(f"Unsupported algorithm: {algorithm}")

            hasher = hashlib.new(algorithm)
            hasher.update(data.encode())

            return {
                "hash": hasher.hexdigest(),
                "algorithm": algorithm,
                "input_length": len(data),
            }

        @server.tool()
        def sleep(seconds: float) -> Dict[str, Any]:
            """Sleep for specified seconds (max 10)."""
            if seconds < 0:
                raise ToolExecutionError("Sleep time must be non-negative")
            if seconds > 10:
                raise ToolExecutionError("Sleep time too long (max 10 seconds)")

            start = time.time()
            time.sleep(seconds)
            actual = time.time() - start

            return {
                "requested": seconds,
                "actual": actual,
                "difference": abs(actual - seconds),
            }

    def _register_resources(self, server: MCPServer):
        """Register server resources."""

        @server.resource()
        async def server_info() -> Dict[str, Any]:
            """Provide server information."""
            return {
                "name": self.name,
                "version": "2.0.0",
                "uptime": time.time(),
                "config": {
                    "auth_enabled": self.config["auth"]["enabled"],
                    "cache_enabled": self.config["cache"]["enabled"],
                    "metrics_enabled": self.config["metrics"]["enabled"],
                },
                "tools": {
                    "count": len(server._tools),
                    "categories": ["math", "data", "file", "utility"],
                },
            }

        @server.resource()
        async def api_documentation() -> Dict[str, Any]:
            """Provide API documentation."""
            tools_doc = {}
            for name, tool in server._tools.items():
                tools_doc[name] = {
                    "description": tool.get("description", ""),
                    "parameters": tool.get("parameters", {}),
                    "cached": bool(tool.get("cache_key")),
                }

            return {
                "version": "1.0",
                "tools": tools_doc,
                "authentication": {
                    "required": self.config["auth"]["enabled"],
                    "type": self.config["auth"]["type"],
                },
            }

    async def start(self):
        """Start the production server."""
        try:
            # Register with service discovery
            if self.discovery:
                await self.discovery.register(
                    name=self.name,
                    host=self.config["server"]["host"],
                    port=self.config["server"]["port"],
                    metadata={
                        "version": "2.0.0",
                        "auth_required": self.config["auth"]["enabled"],
                        "tools_count": len(self.server._tools),
                    },
                    health_endpoint="/health",
                )
                logger.info("Registered with service discovery")

            # Start server
            logger.info(
                f"Starting production MCP server on {self.config['server']['host']}:{self.config['server']['port']}"
            )
            await self.server.start(
                host=self.config["server"]["host"], port=self.config["server"]["port"]
            )

            # Keep running
            await asyncio.Event().wait()

        except KeyboardInterrupt:
            logger.info("Shutting down...")
        finally:
            if self.discovery:
                await self.discovery.deregister(self.name)
            await self.server.shutdown()
            logger.info("Server stopped")


async def main():
    """Run the production MCP server."""
    # Load config from environment or file
    config_file = os.getenv("MCP_CONFIG_FILE")

    server = ProductionMCPServer(
        name=os.getenv("MCP_SERVER_NAME", "production-mcp-server"),
        config_file=config_file,
    )

    await server.start()


if __name__ == "__main__":
    asyncio.run(main())
