"""
MCP Server Workflows

Workflows for MCP server lifecycle management.
"""

import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

from kailash.runtime.local import LocalRuntime
from kailash.workflow.builder import WorkflowBuilder

logger = logging.getLogger(__name__)


class ServerWorkflows:
    """Workflows for MCP server management."""

    def __init__(self, runtime: Optional[LocalRuntime] = None):
        """Initialize server workflows."""
        self.runtime = runtime or LocalRuntime()

    def create_server_deployment_workflow(self) -> WorkflowBuilder:
        """
        Create workflow for deploying an MCP server.

        Steps:
        1. Validate server configuration
        2. Check prerequisites (commands, permissions)
        3. Start the server
        4. Health check
        5. Discover tools and resources
        6. Register in database
        7. Send notifications
        """
        workflow = WorkflowBuilder("server_deployment")

        # Add nodes
        workflow.add_node("validator", "PythonCodeNode")
        workflow.add_node("prerequisite_check", "PythonCodeNode")
        workflow.add_node("server_starter", "MCPServerNode")
        workflow.add_node("health_checker", "MCPServerNode")
        workflow.add_node("tool_discoverer", "MCPServerNode")
        workflow.add_node(
            "db_registrar", "SQLDatabaseNode", {"connection_string": "${DATABASE_URL}"}
        )
        workflow.add_node(
            "notifier",
            "EmailNode",
            {"smtp_config": {"host": "localhost", "port": 1025}},
        )
        workflow.add_node(
            "audit_logger",
            "EnterpriseAuditLogNode",
            {"connection_string": "${DATABASE_URL}"},
        )

        # Connect nodes
        workflow.add_connection("input", "validator", "data", "input")
        workflow.add_connection("validator", "prerequisite_check", "result", "input")
        workflow.add_connection(
            "prerequisite_check", "server_starter", "result", "input"
        )
        workflow.add_connection("server_starter", "health_checker", "result", "input")
        workflow.add_connection("health_checker", "tool_discoverer", "result", "input")
        workflow.add_connection("tool_discoverer", "db_registrar", "result", "input")
        workflow.add_connection("db_registrar", "notifier", "result", "input")
        workflow.add_connection("notifier", "audit_logger", "result", "input")
        workflow.add_connection("audit_logger", "output", "result", "result")

        # Configure validator
        validator_code = """
# Validate server configuration
config = input_data.get("server_config", {})
errors = []

# Check required fields
required_fields = ["name", "transport", "command"]
for field in required_fields:
    if field not in config:
        errors.append(f"Missing required field: {field}")

# Validate transport type
valid_transports = ["stdio", "http", "sse", "websocket"]
if config.get("transport") not in valid_transports:
    errors.append(f"Invalid transport: {config.get('transport')}")

# Validate command security
if config.get("transport") == "stdio":
    command = config.get("command", "")
    # Check against allowed commands
    allowed_commands = input_data.get("allowed_commands", [])
    if allowed_commands and command not in allowed_commands:
        errors.append(f"Command not allowed: {command}")

result = {
    "success": len(errors) == 0,
    "errors": errors,
    "config": config,
    "validated_at": datetime.utcnow().isoformat()
}
"""
        workflow.update_node("validator", {"code": validator_code})

        # Configure prerequisite check
        prereq_code = """
import shutil
import os

config = input_data["config"]
checks = []

# Check if command exists
if config.get("transport") == "stdio":
    command = config.get("command")
    if shutil.which(command) is None:
        checks.append({
            "check": "command_exists",
            "passed": False,
            "error": f"Command not found: {command}"
        })
    else:
        checks.append({
            "check": "command_exists",
            "passed": True
        })

# Check permissions
# TODO: Add more permission checks

# Check resources (ports, etc.)
if config.get("transport") == "http":
    # TODO: Check if port is available
    pass

all_passed = all(check.get("passed", False) for check in checks)

result = {
    "success": all_passed,
    "checks": checks,
    "server_config": config
}
"""
        workflow.update_node("prerequisite_check", {"code": prereq_code})

        # Configure server starter
        workflow.update_node(
            "server_starter",
            {"operation": "start_server", "server_config": "$.server_config"},
        )

        # Configure health checker
        workflow.update_node(
            "health_checker", {"operation": "check_health", "server_id": "$.server_id"}
        )

        # Configure tool discoverer
        workflow.update_node(
            "tool_discoverer",
            {"operation": "discover_tools", "server_id": "$.server_id"},
        )

        # Configure database registration
        workflow.update_node(
            "db_registrar",
            {
                "operation": "insert",
                "table": "mcp_servers",
                "data": {
                    "id": "$.server_id",
                    "name": "$.server_config.name",
                    "transport": "$.server_config.transport",
                    "config": "$.server_config",
                    "status": "running",
                    "tool_count": "$.tool_count",
                    "created_at": "$.started_at",
                },
            },
        )

        # Configure notifier
        workflow.update_node(
            "notifier",
            {
                "to": "${ADMIN_EMAIL}",
                "subject": "MCP Server Deployed",
                "body": "Server {{server_id}} ({{server_config.name}}) has been deployed successfully with {{tool_count}} tools.",
            },
        )

        # Configure audit logger
        workflow.update_node(
            "audit_logger",
            {
                "operation": "log_event",
                "event_type": "server_deployed",
                "severity": "low",
                "details": {
                    "server_id": "$.server_id",
                    "server_name": "$.server_config.name",
                    "tool_count": "$.tool_count",
                },
            },
        )

        return workflow

    def create_server_health_monitoring_workflow(self) -> WorkflowBuilder:
        """
        Create workflow for monitoring server health.

        Steps:
        1. Get list of active servers
        2. Check health of each server in parallel
        3. Update server status
        4. Send alerts for unhealthy servers
        5. Log metrics
        """
        workflow = WorkflowBuilder("server_health_monitoring")

        # Add nodes
        workflow.add_node(
            "server_fetcher",
            "SQLDatabaseNode",
            {"connection_string": "${DATABASE_URL}"},
        )
        workflow.add_node("health_checker", "PythonCodeNode")
        workflow.add_node(
            "status_updater",
            "SQLDatabaseNode",
            {"connection_string": "${DATABASE_URL}"},
        )
        workflow.add_node("alert_sender", "ConditionalNode")
        workflow.add_node("metrics_logger", "PythonCodeNode")

        # Connect nodes
        workflow.add_connection("input", "server_fetcher", "data", "input")
        workflow.add_connection("server_fetcher", "health_checker", "result", "input")
        workflow.add_connection("health_checker", "status_updater", "result", "input")
        workflow.add_connection("status_updater", "alert_sender", "result", "input")
        workflow.add_connection("alert_sender", "metrics_logger", "result", "input")
        workflow.add_connection("metrics_logger", "output", "result", "result")

        # Configure server fetcher
        workflow.update_node(
            "server_fetcher",
            {
                "operation": "select",
                "table": "mcp_servers",
                "where": {"status": ["running", "unhealthy"]},
                "limit": 100,
            },
        )

        # Configure health checker
        health_code = """
import asyncio
from datetime import datetime

servers = input_data.get("rows", [])
health_results = []

# Create health check tasks
async def check_server_health(server):
    # Simulate health check (in real implementation, use MCPServerNode)
    # For now, return mock data
    import random
    is_healthy = random.random() > 0.1  # 90% healthy

    return {
        "server_id": server["id"],
        "server_name": server["name"],
        "healthy": is_healthy,
        "response_time_ms": random.randint(10, 100) if is_healthy else None,
        "error": None if is_healthy else "Connection timeout",
        "checked_at": datetime.utcnow().isoformat()
    }

# Run health checks in parallel
async def run_health_checks():
    tasks = [check_server_health(server) for server in servers]
    return await asyncio.gather(*tasks)

# Execute
health_results = asyncio.run(run_health_checks())

# Categorize results
healthy_servers = [r for r in health_results if r["healthy"]]
unhealthy_servers = [r for r in health_results if not r["healthy"]]

result = {
    "total_servers": len(servers),
    "healthy_count": len(healthy_servers),
    "unhealthy_count": len(unhealthy_servers),
    "health_results": health_results,
    "unhealthy_servers": unhealthy_servers
}
"""
        workflow.update_node("health_checker", {"code": health_code})

        # Configure status updater
        workflow.update_node(
            "status_updater",
            {
                "operation": "batch_update",
                "updates": [
                    {
                        "table": "mcp_servers",
                        "where": {"id": "$.server_id"},
                        "data": {
                            "status": "$.healthy ? 'running' : 'unhealthy'",
                            "last_health_check": "$.checked_at",
                            "health_status": {
                                "healthy": "$.healthy",
                                "response_time_ms": "$.response_time_ms",
                                "error": "$.error",
                            },
                        },
                    }
                    for _ in "$.health_results"
                ],
            },
        )

        # Configure alert sender
        workflow.update_node(
            "alert_sender",
            {
                "condition": "$.unhealthy_count > 0",
                "true_path": {
                    "node_type": "EmailNode",
                    "config": {
                        "to": "${ADMIN_EMAIL}",
                        "subject": "MCP Server Health Alert",
                        "body": "{{unhealthy_count}} servers are unhealthy. Please check the system.",
                    },
                },
            },
        )

        # Configure metrics logger
        metrics_code = """
from datetime import datetime

# Log metrics
metrics = {
    "timestamp": datetime.utcnow().isoformat(),
    "total_servers": input_data["total_servers"],
    "healthy_servers": input_data["healthy_count"],
    "unhealthy_servers": input_data["unhealthy_count"],
    "health_percentage": (
        input_data["healthy_count"] / input_data["total_servers"] * 100
        if input_data["total_servers"] > 0 else 0
    ),
    "average_response_time_ms": sum(
        r["response_time_ms"] for r in input_data["health_results"]
        if r.get("response_time_ms")
    ) / input_data["healthy_count"] if input_data["healthy_count"] > 0 else 0
}

# In production, send to metrics system (Prometheus, etc.)
print(f"Server health metrics: {metrics}")

result = {
    "success": True,
    "metrics": metrics,
    "monitoring_complete": True
}
"""
        workflow.update_node("metrics_logger", {"code": metrics_code})

        return workflow

    def create_server_scaling_workflow(self) -> WorkflowBuilder:
        """
        Create workflow for auto-scaling MCP servers.

        Steps:
        1. Get current load metrics
        2. Analyze scaling needs
        3. Deploy additional servers if needed
        4. Remove idle servers if over-provisioned
        5. Update load balancer
        """
        workflow = WorkflowBuilder("server_scaling")

        # Add nodes
        workflow.add_node("metrics_collector", "PythonCodeNode")
        workflow.add_node("scaling_analyzer", "PythonCodeNode")
        workflow.add_node("scaler", "ConditionalNode")
        workflow.add_node(
            "load_balancer_updater",
            "HTTPRequestNode",
            {"base_url": "${LOAD_BALANCER_URL}"},
        )

        # Connect nodes
        workflow.add_connection("input", "metrics_collector", "data", "input")
        workflow.add_connection(
            "metrics_collector", "scaling_analyzer", "result", "input"
        )
        workflow.add_connection("scaling_analyzer", "scaler", "result", "input")
        workflow.add_connection("scaler", "load_balancer_updater", "result", "input")
        workflow.add_connection("load_balancer_updater", "output", "result", "result")

        # Configure metrics collector
        metrics_code = """
# Collect metrics from all servers
# In production, query from metrics system

import random

# Simulate metrics
servers = input_data.get("servers", [])
metrics = []

for server in servers:
    metrics.append({
        "server_id": server["id"],
        "cpu_percent": random.uniform(10, 90),
        "memory_percent": random.uniform(20, 80),
        "active_connections": random.randint(0, 100),
        "tool_executions_per_minute": random.randint(0, 50)
    })

result = {
    "server_count": len(servers),
    "metrics": metrics,
    "timestamp": datetime.utcnow().isoformat()
}
"""
        workflow.update_node("metrics_collector", {"code": metrics_code})

        # Configure scaling analyzer
        analyzer_code = """
# Analyze if scaling is needed
metrics = input_data["metrics"]

# Calculate averages
avg_cpu = sum(m["cpu_percent"] for m in metrics) / len(metrics) if metrics else 0
avg_memory = sum(m["memory_percent"] for m in metrics) / len(metrics) if metrics else 0
total_connections = sum(m["active_connections"] for m in metrics)

# Scaling thresholds
scale_up_threshold = 70  # CPU or memory > 70%
scale_down_threshold = 30  # CPU and memory < 30%
min_servers = 2
max_servers = 10

# Determine scaling action
current_count = len(metrics)
scaling_action = "none"
target_count = current_count

if (avg_cpu > scale_up_threshold or avg_memory > scale_up_threshold) and current_count < max_servers:
    scaling_action = "scale_up"
    target_count = min(current_count + 1, max_servers)
elif avg_cpu < scale_down_threshold and avg_memory < scale_down_threshold and current_count > min_servers:
    scaling_action = "scale_down"
    target_count = max(current_count - 1, min_servers)

result = {
    "scaling_action": scaling_action,
    "current_servers": current_count,
    "target_servers": target_count,
    "metrics_summary": {
        "avg_cpu": avg_cpu,
        "avg_memory": avg_memory,
        "total_connections": total_connections
    }
}
"""
        workflow.update_node("scaling_analyzer", {"code": analyzer_code})

        # Configure scaler
        workflow.update_node(
            "scaler",
            {
                "condition": "$.scaling_action != 'none'",
                "true_path": {
                    "node_type": "PythonCodeNode",
                    "config": {
                        "code": """
# Perform scaling action
if input_data["scaling_action"] == "scale_up":
    # Deploy new server
    result = {
        "action": "deployed",
        "new_server": {
            "id": f"server-{datetime.utcnow().timestamp()}",
            "status": "starting"
        }
    }
elif input_data["scaling_action"] == "scale_down":
    # Remove least loaded server
    result = {
        "action": "removed",
        "removed_server": {
            "id": "server-123",  # In production, select actual server
            "status": "stopping"
        }
    }
else:
    result = {"action": "none"}

result.update(input_data)
"""
                    },
                },
                "false_path": {
                    "node_type": "PythonCodeNode",
                    "config": {"code": "result = {'action': 'none', **input_data}"},
                },
            },
        )

        # Configure load balancer updater
        workflow.update_node(
            "load_balancer_updater",
            {
                "method": "POST",
                "endpoint": "/update-backends",
                "data": {"action": "$.action", "servers": "$.target_servers"},
            },
        )

        return workflow
