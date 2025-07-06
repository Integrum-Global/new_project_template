"""Tool routing and load balancing for Enterprise Gateway."""

import asyncio
import random
from collections import defaultdict
from datetime import datetime
from typing import Any, Callable, Dict, List, Optional

import httpx
import structlog
from circuit_breaker import CircuitBreaker

from kailash.core.execution import LocalRuntime
from kailash.workflow.builder import WorkflowBuilder

logger = structlog.get_logger(__name__)


class ToolInstance:
    """Represents a tool instance."""

    def __init__(self, instance_id: str, url: str, weight: int = 1):
        self.instance_id = instance_id
        self.url = url
        self.weight = weight
        self.healthy = True
        self.last_health_check = None
        self.response_times = []
        self.error_count = 0
        self.success_count = 0

    @property
    def average_response_time(self) -> float:
        """Get average response time."""
        if not self.response_times:
            return 0
        return sum(self.response_times) / len(self.response_times)

    @property
    def error_rate(self) -> float:
        """Get error rate."""
        total = self.error_count + self.success_count
        if total == 0:
            return 0
        return self.error_count / total

    def record_response(self, response_time: float, success: bool):
        """Record a response."""
        self.response_times.append(response_time)
        if len(self.response_times) > 100:
            self.response_times.pop(0)

        if success:
            self.success_count += 1
        else:
            self.error_count += 1


class LoadBalancer:
    """Load balancer for tool instances."""

    def __init__(self, strategy: str = "round_robin"):
        self.strategy = strategy
        self.instances: List[ToolInstance] = []
        self.current_index = 0

    def add_instance(self, instance: ToolInstance):
        """Add an instance to the load balancer."""
        self.instances.append(instance)

    def remove_instance(self, instance_id: str):
        """Remove an instance from the load balancer."""
        self.instances = [i for i in self.instances if i.instance_id != instance_id]

    def get_next_instance(self) -> Optional[ToolInstance]:
        """Get the next instance based on strategy."""
        healthy_instances = [i for i in self.instances if i.healthy]

        if not healthy_instances:
            return None

        if self.strategy == "round_robin":
            instance = healthy_instances[self.current_index % len(healthy_instances)]
            self.current_index += 1
            return instance

        elif self.strategy == "random":
            return random.choice(healthy_instances)

        elif self.strategy == "weighted":
            # Weighted random selection
            weights = [i.weight for i in healthy_instances]
            return random.choices(healthy_instances, weights=weights)[0]

        elif self.strategy == "least_connections":
            # In a real implementation, track active connections
            return min(healthy_instances, key=lambda i: i.success_count)

        elif self.strategy == "least_response_time":
            return min(healthy_instances, key=lambda i: i.average_response_time)

        else:
            return healthy_instances[0]


class ToolRouter:
    """Routes tool requests to appropriate handlers."""

    def __init__(self):
        self.tools: Dict[str, Dict[str, Any]] = {}
        self.load_balancers: Dict[str, LoadBalancer] = {}
        self.circuit_breakers: Dict[str, CircuitBreaker] = {}
        self.runtime = LocalRuntime()
        self.health_check_interval = 30  # seconds
        self._health_check_task = None

    async def initialize(self):
        """Initialize the router."""
        # Start health check task
        self._health_check_task = asyncio.create_task(self._health_check_loop())

        # Register default tools
        await self._register_default_tools()

    async def cleanup(self):
        """Cleanup resources."""
        if self._health_check_task:
            self._health_check_task.cancel()

    def register_tool(self, name: str, config: Dict[str, Any]):
        """Register a tool."""
        self.tools[name] = config

        # Create load balancer if multiple instances
        if "instances" in config:
            lb_strategy = config.get("load_balancing", "round_robin")
            lb = LoadBalancer(strategy=lb_strategy)

            for instance_config in config["instances"]:
                instance = ToolInstance(
                    instance_config["id"],
                    instance_config["url"],
                    instance_config.get("weight", 1),
                )
                lb.add_instance(instance)

            self.load_balancers[name] = lb

        # Create circuit breaker
        cb_config = config.get("circuit_breaker", {})
        self.circuit_breakers[name] = CircuitBreaker(
            failure_threshold=cb_config.get("failure_threshold", 5),
            recovery_timeout=cb_config.get("recovery_timeout", 60),
            expected_exception=Exception,
        )

        logger.info(f"Registered tool: {name}")

    async def execute(
        self,
        tool_name: str,
        action: str,
        params: Dict[str, Any],
        context: Dict[str, Any],
    ) -> Any:
        """Execute a tool action."""
        if tool_name not in self.tools:
            raise ValueError(f"Tool '{tool_name}' not found")

        tool_config = self.tools[tool_name]

        # Get circuit breaker
        circuit_breaker = self.circuit_breakers[tool_name]

        try:
            # Execute with circuit breaker
            result = await circuit_breaker.call(
                self._execute_tool, tool_name, action, params, context
            )
            return result

        except Exception as e:
            logger.error(f"Tool execution failed: {tool_name}", error=str(e))
            raise

    async def _execute_tool(
        self,
        tool_name: str,
        action: str,
        params: Dict[str, Any],
        context: Dict[str, Any],
    ) -> Any:
        """Internal tool execution."""
        tool_config = self.tools[tool_name]

        # Check if tool has multiple instances
        if tool_name in self.load_balancers:
            # Use load balancer
            lb = self.load_balancers[tool_name]
            instance = lb.get_next_instance()

            if not instance:
                raise Exception("No healthy instances available")

            # Execute on selected instance
            start_time = datetime.utcnow()

            try:
                result = await self._execute_remote_tool(
                    instance.url, tool_name, action, params, context
                )

                # Record success
                response_time = (datetime.utcnow() - start_time).total_seconds()
                instance.record_response(response_time, True)

                return result

            except Exception as e:
                # Record failure
                response_time = (datetime.utcnow() - start_time).total_seconds()
                instance.record_response(response_time, False)
                raise

        else:
            # Execute locally
            if "workflow" in tool_config:
                # Execute as workflow
                return await self._execute_workflow_tool(
                    tool_config["workflow"], params, context
                )
            elif "handler" in tool_config:
                # Execute handler function
                handler = tool_config["handler"]
                return await handler(action, params, context)
            else:
                raise ValueError(f"Tool '{tool_name}' has no execution method")

    async def _execute_remote_tool(
        self,
        url: str,
        tool_name: str,
        action: str,
        params: Dict[str, Any],
        context: Dict[str, Any],
    ) -> Any:
        """Execute tool on remote instance."""
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                f"{url}/tools/{tool_name}/execute",
                json={"action": action, "params": params, "context": context},
            )
            response.raise_for_status()
            return response.json()

    async def _execute_workflow_tool(
        self,
        workflow_config: Dict[str, Any],
        params: Dict[str, Any],
        context: Dict[str, Any],
    ) -> Any:
        """Execute a workflow-based tool."""
        # Build workflow from config
        builder = WorkflowBuilder(workflow_config["name"])

        for node in workflow_config["nodes"]:
            builder.add_node(node["name"], node["type"], node.get("config", {}))

        for connection in workflow_config["connections"]:
            builder.add_connection(
                connection["from_node"],
                connection["from_output"],
                connection["to_node"],
                connection["to_input"],
            )

        # Execute workflow
        workflow = builder.build()
        result = await self.runtime.execute_workflow(
            workflow, {**params, "context": context}
        )

        return result

    def list_tools(self) -> List[Dict[str, Any]]:
        """List all registered tools."""
        tools = []

        for name, config in self.tools.items():
            tool_info = {
                "name": name,
                "description": config.get("description", ""),
                "actions": config.get("actions", []),
                "parameters": config.get("parameters", {}),
                "requires_auth": config.get("requires_auth", True),
            }

            # Add instance info if using load balancer
            if name in self.load_balancers:
                lb = self.load_balancers[name]
                tool_info["instances"] = [
                    {
                        "id": instance.instance_id,
                        "healthy": instance.healthy,
                        "error_rate": instance.error_rate,
                        "avg_response_time": instance.average_response_time,
                    }
                    for instance in lb.instances
                ]

            tools.append(tool_info)

        return tools

    def get_tool(self, name: str) -> Optional[Dict[str, Any]]:
        """Get tool details."""
        if name not in self.tools:
            return None

        config = self.tools[name].copy()

        # Add runtime info
        if name in self.circuit_breakers:
            cb = self.circuit_breakers[name]
            config["circuit_breaker_state"] = cb.current_state

        return config

    async def _health_check_loop(self):
        """Periodic health check for tool instances."""
        while True:
            try:
                await asyncio.sleep(self.health_check_interval)
                await self._check_all_instances()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Health check error: {e}")

    async def _check_all_instances(self):
        """Check health of all instances."""
        for tool_name, lb in self.load_balancers.items():
            for instance in lb.instances:
                await self._check_instance_health(instance)

    async def _check_instance_health(self, instance: ToolInstance):
        """Check health of a single instance."""
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get(f"{instance.url}/health")

                if response.status_code == 200:
                    instance.healthy = True
                else:
                    instance.healthy = False

                instance.last_health_check = datetime.utcnow()

        except Exception as e:
            logger.warning(f"Health check failed for {instance.instance_id}: {e}")
            instance.healthy = False
            instance.last_health_check = datetime.utcnow()

    async def _register_default_tools(self):
        """Register default system tools."""
        # Data processing tool
        self.register_tool(
            "data_processor",
            {
                "description": "Process and transform data",
                "actions": ["transform", "validate", "aggregate"],
                "parameters": {"transform": {"data": "array", "operations": "array"}},
                "handler": self._data_processor_handler,
            },
        )

        # Analytics tool
        self.register_tool(
            "analytics",
            {
                "description": "Run analytics queries",
                "actions": ["query", "report"],
                "parameters": {"query": {"sql": "string", "database": "string"}},
                "handler": self._analytics_handler,
            },
        )

    async def _data_processor_handler(
        self, action: str, params: Dict[str, Any], context: Dict[str, Any]
    ) -> Any:
        """Handle data processing requests."""
        if action == "transform":
            # Implement data transformation
            data = params.get("data", [])
            operations = params.get("operations", [])

            # Apply transformations
            result = data
            for op in operations:
                if op == "uppercase":
                    result = [
                        item.upper() if isinstance(item, str) else item
                        for item in result
                    ]
                # Add more operations

            return {"transformed_data": result}

        return {"error": f"Unknown action: {action}"}

    async def _analytics_handler(
        self, action: str, params: Dict[str, Any], context: Dict[str, Any]
    ) -> Any:
        """Handle analytics requests."""
        if action == "query":
            # Implement analytics query
            # This is a mock implementation
            return {"results": [], "row_count": 0, "execution_time": 0.1}

        return {"error": f"Unknown action: {action}"}


# Route decorators for registering tools
class RouteDecorator:
    """Decorator for registering tool routes."""

    def __init__(self, router: ToolRouter):
        self.router = router

    def tool(self, name: str, **config):
        """Decorator to register a tool."""

        def decorator(func: Callable):
            # Create handler wrapper
            async def handler(
                action: str, params: Dict[str, Any], context: Dict[str, Any]
            ) -> Any:
                return await func(action, params, context)

            # Register tool
            tool_config = {"handler": handler, **config}
            self.router.register_tool(name, tool_config)

            return func

        return decorator
