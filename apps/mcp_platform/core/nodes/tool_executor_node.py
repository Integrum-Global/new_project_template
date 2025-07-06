"""
Tool Executor Node

Custom Kailash node for executing MCP tools with advanced features.
"""

import asyncio
import hashlib
import json
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

from kailash.node import Node
from kailash.node.parameter import NodeParameter, ParameterType

logger = logging.getLogger(__name__)


class ToolExecutorNode(Node):
    """
    Node for executing MCP tools with caching, retry, and batch support.

    Features:
    - Single tool execution
    - Batch tool execution
    - Result caching
    - Automatic retry on failure
    - Parallel execution support
    - Tool validation
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize the tool executor node."""
        self.config = config or {}

        # Execution settings
        self.timeout = self.config.get("timeout", 120)
        self.retry_attempts = self.config.get("retry_attempts", 3)
        self.retry_delay = self.config.get("retry_delay", 1.0)
        self.cache_results = self.config.get("cache_results", True)
        self.cache_ttl = self.config.get("cache_ttl", 3600)

        # Simple in-memory cache
        self._cache = {}

        super().__init__()

    def get_parameters(self) -> Dict[str, NodeParameter]:
        """Define node parameters."""
        return {
            "operation": NodeParameter(
                name="operation",
                type=ParameterType.STRING,
                required=True,
                description="Operation to perform",
                allowed_values=["execute", "batch_execute", "validate"],
            ),
            "mcp_client": NodeParameter(
                name="mcp_client",
                type=ParameterType.OBJECT,
                required=True,
                description="MCP client instance for tool execution",
            ),
            "tool_name": NodeParameter(
                name="tool_name",
                type=ParameterType.STRING,
                required=False,
                description="Tool name for single execution",
            ),
            "parameters": NodeParameter(
                name="parameters",
                type=ParameterType.DICT,
                required=False,
                default={},
                description="Tool parameters",
            ),
            "executions": NodeParameter(
                name="executions",
                type=ParameterType.LIST,
                required=False,
                description="List of tool executions for batch operation",
            ),
            "parallel": NodeParameter(
                name="parallel",
                type=ParameterType.BOOLEAN,
                required=False,
                default=True,
                description="Execute batch operations in parallel",
            ),
            "cache_key": NodeParameter(
                name="cache_key",
                type=ParameterType.STRING,
                required=False,
                description="Custom cache key (auto-generated if not provided)",
            ),
            "skip_cache": NodeParameter(
                name="skip_cache",
                type=ParameterType.BOOLEAN,
                required=False,
                default=False,
                description="Skip cache lookup",
            ),
        }

    async def execute(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute the tool operation."""
        operation = context.get("operation")

        try:
            if operation == "execute":
                return await self._execute_tool(context)
            elif operation == "batch_execute":
                return await self._batch_execute_tools(context)
            elif operation == "validate":
                return await self._validate_tool(context)
            else:
                return {"success": False, "error": f"Unknown operation: {operation}"}

        except Exception as e:
            logger.error(f"Error in tool executor: {e}")
            return {"success": False, "error": str(e), "operation": operation}

    async def _execute_tool(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a single tool."""
        mcp_client = context.get("mcp_client")
        tool_name = context.get("tool_name")
        parameters = context.get("parameters", {})
        skip_cache = context.get("skip_cache", False)

        if not mcp_client:
            return {"success": False, "error": "MCP client required"}

        if not tool_name:
            return {"success": False, "error": "Tool name required"}

        # Generate cache key
        cache_key = context.get("cache_key") or self._generate_cache_key(
            tool_name, parameters
        )

        # Check cache
        if self.cache_results and not skip_cache:
            cached_result = self._get_cached_result(cache_key)
            if cached_result:
                logger.info(f"Cache hit for tool {tool_name}")
                return {
                    "success": True,
                    "result": cached_result["result"],
                    "cached": True,
                    "cache_key": cache_key,
                    "cached_at": cached_result["timestamp"],
                }

        # Execute with retry
        start_time = datetime.utcnow()
        last_error = None

        for attempt in range(self.retry_attempts):
            try:
                # Execute tool with timeout
                result = await asyncio.wait_for(
                    mcp_client.call_tool(tool_name, parameters), timeout=self.timeout
                )

                # Calculate duration
                duration_ms = (datetime.utcnow() - start_time).total_seconds() * 1000

                # Cache successful result
                if self.cache_results:
                    self._cache_result(cache_key, result)

                return {
                    "success": True,
                    "result": result,
                    "tool_name": tool_name,
                    "duration_ms": duration_ms,
                    "attempts": attempt + 1,
                    "cached": False,
                    "cache_key": cache_key,
                }

            except asyncio.TimeoutError:
                last_error = f"Tool execution timed out after {self.timeout}s"
                logger.warning(f"Timeout on attempt {attempt + 1} for {tool_name}")

            except Exception as e:
                last_error = str(e)
                logger.warning(f"Error on attempt {attempt + 1} for {tool_name}: {e}")

            # Wait before retry
            if attempt < self.retry_attempts - 1:
                await asyncio.sleep(self.retry_delay * (attempt + 1))

        # All attempts failed
        duration_ms = (datetime.utcnow() - start_time).total_seconds() * 1000

        return {
            "success": False,
            "error": last_error,
            "tool_name": tool_name,
            "duration_ms": duration_ms,
            "attempts": self.retry_attempts,
        }

    async def _batch_execute_tools(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute multiple tools in batch."""
        mcp_client = context.get("mcp_client")
        executions = context.get("executions", [])
        parallel = context.get("parallel", True)

        if not mcp_client:
            return {"success": False, "error": "MCP client required"}

        if not executions:
            return {"success": False, "error": "No executions provided"}

        start_time = datetime.utcnow()

        if parallel:
            # Execute in parallel
            tasks = []
            for execution in executions:
                task_context = {
                    "operation": "execute",
                    "mcp_client": mcp_client,
                    "tool_name": execution.get("tool_name"),
                    "parameters": execution.get("parameters", {}),
                    "skip_cache": execution.get("skip_cache", False),
                }
                tasks.append(self._execute_tool(task_context))

            results = await asyncio.gather(*tasks, return_exceptions=True)

            # Process results
            processed_results = []
            for i, result in enumerate(results):
                if isinstance(result, Exception):
                    processed_results.append(
                        {
                            "success": False,
                            "error": str(result),
                            "index": i,
                            "tool_name": executions[i].get("tool_name"),
                        }
                    )
                else:
                    result["index"] = i
                    processed_results.append(result)

        else:
            # Execute sequentially
            processed_results = []
            for i, execution in enumerate(executions):
                task_context = {
                    "operation": "execute",
                    "mcp_client": mcp_client,
                    "tool_name": execution.get("tool_name"),
                    "parameters": execution.get("parameters", {}),
                    "skip_cache": execution.get("skip_cache", False),
                }

                result = await self._execute_tool(task_context)
                result["index"] = i
                processed_results.append(result)

                # Stop on error if requested
                if not result["success"] and execution.get("stop_on_error", False):
                    break

        # Calculate totals
        total_duration_ms = (datetime.utcnow() - start_time).total_seconds() * 1000
        successful = sum(1 for r in processed_results if r.get("success"))
        failed = len(processed_results) - successful

        return {
            "success": True,
            "total": len(executions),
            "executed": len(processed_results),
            "successful": successful,
            "failed": failed,
            "duration_ms": total_duration_ms,
            "parallel": parallel,
            "results": processed_results,
        }

    async def _validate_tool(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Validate tool parameters without execution."""
        tool_name = context.get("tool_name")
        parameters = context.get("parameters", {})
        tool_schema = context.get("tool_schema")

        if not tool_name:
            return {"success": False, "error": "Tool name required"}

        validation_errors = []

        # Basic validation
        if not isinstance(parameters, dict):
            validation_errors.append("Parameters must be a dictionary")

        # Schema validation if provided
        if tool_schema:
            # Validate required parameters
            required = tool_schema.get("required", [])
            for param in required:
                if param not in parameters:
                    validation_errors.append(f"Missing required parameter: {param}")

            # Validate parameter types
            properties = tool_schema.get("properties", {})
            for param_name, param_value in parameters.items():
                if param_name in properties:
                    param_schema = properties[param_name]
                    param_type = param_schema.get("type")

                    # Simple type validation
                    if param_type == "string" and not isinstance(param_value, str):
                        validation_errors.append(
                            f"Parameter {param_name} must be a string"
                        )
                    elif param_type == "number" and not isinstance(
                        param_value, (int, float)
                    ):
                        validation_errors.append(
                            f"Parameter {param_name} must be a number"
                        )
                    elif param_type == "boolean" and not isinstance(param_value, bool):
                        validation_errors.append(
                            f"Parameter {param_name} must be a boolean"
                        )
                    elif param_type == "array" and not isinstance(param_value, list):
                        validation_errors.append(
                            f"Parameter {param_name} must be an array"
                        )
                    elif param_type == "object" and not isinstance(param_value, dict):
                        validation_errors.append(
                            f"Parameter {param_name} must be an object"
                        )

        # Security validation
        param_str = json.dumps(parameters)
        suspicious_patterns = [
            "'; DROP TABLE",
            "<script>",
            "javascript:",
            "../",
            "file://",
            "eval(",
            "__import__",
        ]

        for pattern in suspicious_patterns:
            if pattern.lower() in param_str.lower():
                validation_errors.append(f"Suspicious pattern detected: {pattern}")

        return {
            "success": len(validation_errors) == 0,
            "tool_name": tool_name,
            "valid": len(validation_errors) == 0,
            "errors": validation_errors,
            "parameter_count": len(parameters),
        }

    def _generate_cache_key(self, tool_name: str, parameters: Dict[str, Any]) -> str:
        """Generate a cache key for tool execution."""
        # Create stable string representation
        param_str = json.dumps(parameters, sort_keys=True)

        # Generate hash
        hasher = hashlib.sha256()
        hasher.update(f"{tool_name}:{param_str}".encode())

        return hasher.hexdigest()[:16]

    def _get_cached_result(self, cache_key: str) -> Optional[Dict[str, Any]]:
        """Get cached result if available and not expired."""
        if cache_key not in self._cache:
            return None

        cached = self._cache[cache_key]

        # Check expiry
        age_seconds = (datetime.utcnow() - cached["timestamp"]).total_seconds()
        if age_seconds > self.cache_ttl:
            # Expired
            del self._cache[cache_key]
            return None

        return cached

    def _cache_result(self, cache_key: str, result: Any):
        """Cache a tool execution result."""
        self._cache[cache_key] = {"result": result, "timestamp": datetime.utcnow()}

        # Simple cache size management
        if len(self._cache) > 1000:
            # Remove oldest entries
            sorted_keys = sorted(
                self._cache.keys(), key=lambda k: self._cache[k]["timestamp"]
            )
            for key in sorted_keys[:100]:
                del self._cache[key]
