"""Basic MCP integration with Kailash SDK workflows.

This example demonstrates how to create an MCP server that exposes Kailash workflows
as tools, allowing external clients to discover and execute your AI workflows.

Features demonstrated:
- MCP server setup with Kailash integration
- Workflow registration as MCP tools
- Resource management for configurations
- Error handling and logging
- Authentication integration
"""

import asyncio
import json
import logging
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

from kailash import LocalRuntime, WorkflowBuilder
from kailash.mcp_server import MCPServer
from kailash.mcp_server.auth import APIKeyAuth
from kailash.nodes.ai import LLMAgentNode
from kailash.nodes.data import CSVReaderNode, JSONReaderNode
from kailash.nodes.logic import SwitchNode

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class KailashMCPServer:
    """MCP server that exposes Kailash workflows as tools."""

    def __init__(self, server_name: str = "kailash-workflow-server"):
        """Initialize the Kailash MCP server."""
        # Setup authentication
        self.auth = APIKeyAuth(
            {
                "admin_key_123": {"permissions": ["admin", "workflows", "resources"]},
                "user_key_456": {"permissions": ["workflows"]},
                "readonly_key_789": {"permissions": ["resources"]},
            }
        )

        # Create MCP server with authentication
        self.server = MCPServer(
            server_name,
            auth_provider=self.auth,
            enable_metrics=True,
            rate_limit_config={"requests_per_minute": 60},
        )

        # Initialize Kailash runtime
        self.runtime = LocalRuntime()

        # Workflow registry
        self.workflows: Dict[str, Dict[str, Any]] = {}

        # Register tools and resources
        self._register_workflow_tools()
        self._register_configuration_resources()

        logger.info(f"Initialized {server_name} with {len(self.workflows)} workflows")

    def _register_workflow_tools(self):
        """Register workflow execution tools."""

        @self.server.tool(required_permission="workflows")
        def execute_text_analysis(text: str, analysis_type: str = "sentiment") -> dict:
            """Analyze text using Kailash AI workflows.

            Args:
                text: Text content to analyze
                analysis_type: Type of analysis (sentiment, classification, extraction)

            Returns:
                Analysis results with metadata
            """
            try:
                # Build analysis workflow
                workflow = self._build_text_analysis_workflow(analysis_type)

                # Execute with inputs
                result = self.runtime.execute(
                    workflow, {"text_input": text, "analysis_type": analysis_type}
                )

                return {
                    "analysis_type": analysis_type,
                    "input_text": text[:100] + "..." if len(text) > 100 else text,
                    "result": result,
                    "timestamp": time.time(),
                    "workflow_id": f"text_analysis_{analysis_type}",
                }

            except Exception as e:
                logger.error(f"Text analysis failed: {e}")
                return {
                    "error": str(e),
                    "analysis_type": analysis_type,
                    "timestamp": time.time(),
                }

        @self.server.tool(
            required_permission="workflows", cache_key="data_processing", cache_ttl=300
        )
        def process_data_file(file_path: str, operation: str = "analyze") -> dict:
            """Process data files using Kailash workflows.

            Args:
                file_path: Path to data file (CSV, JSON)
                operation: Processing operation (analyze, transform, validate)

            Returns:
                Processing results
            """
            try:
                # Determine file type and build appropriate workflow
                if file_path.endswith(".csv"):
                    workflow = self._build_csv_processing_workflow(operation)
                elif file_path.endswith(".json"):
                    workflow = self._build_json_processing_workflow(operation)
                else:
                    return {
                        "error": "Unsupported file type",
                        "supported": [".csv", ".json"],
                    }

                # Execute workflow
                result = self.runtime.execute(
                    workflow, {"file_path": file_path, "operation": operation}
                )

                return {
                    "file_path": file_path,
                    "operation": operation,
                    "result": result,
                    "timestamp": time.time(),
                }

            except Exception as e:
                logger.error(f"Data processing failed: {e}")
                return {"error": str(e), "file_path": file_path, "operation": operation}

        @self.server.tool(required_permission="workflows")
        def list_available_workflows() -> dict:
            """List all available workflows and their capabilities."""
            workflows = {
                "text_analysis": {
                    "description": "Analyze text for sentiment, classification, or extraction",
                    "inputs": ["text", "analysis_type"],
                    "analysis_types": ["sentiment", "classification", "extraction"],
                    "permissions_required": ["workflows"],
                },
                "data_processing": {
                    "description": "Process CSV and JSON files",
                    "inputs": ["file_path", "operation"],
                    "supported_formats": [".csv", ".json"],
                    "operations": ["analyze", "transform", "validate"],
                    "permissions_required": ["workflows"],
                    "cached": True,
                    "cache_ttl": 300,
                },
            }

            return {
                "workflows": workflows,
                "total_count": len(workflows),
                "server_info": {
                    "name": self.server.name,
                    "version": "1.0.0",
                    "auth_required": True,
                },
            }

        @self.server.tool(required_permission="admin")
        def get_server_metrics() -> dict:
            """Get server performance metrics (admin only)."""
            if hasattr(self.server, "get_metrics"):
                metrics = self.server.get_metrics()
                metrics.update(
                    {
                        "runtime_info": {
                            "workflows_executed": len(self.workflows),
                            "uptime": time.time()
                            - getattr(self, "_start_time", time.time()),
                        }
                    }
                )
                return metrics
            else:
                return {"message": "Metrics not available"}

    def _register_configuration_resources(self):
        """Register configuration and metadata resources."""

        @self.server.resource("config://server/settings")
        def get_server_settings():
            """Get server configuration settings."""
            return {
                "server_name": self.server.name,
                "authentication": {
                    "enabled": True,
                    "type": "api_key",
                    "permissions": ["admin", "workflows", "resources"],
                },
                "features": {
                    "metrics": True,
                    "rate_limiting": True,
                    "caching": True,
                    "async_execution": True,
                },
                "workflows": {
                    "supported_types": ["text_analysis", "data_processing"],
                    "max_concurrent": 10,
                    "timeout_seconds": 300,
                },
            }

        @self.server.resource("config://workflows/templates")
        def get_workflow_templates():
            """Get available workflow templates."""
            return {
                "text_analysis_template": {
                    "nodes": ["LLMAgentNode"],
                    "connections": [],
                    "inputs": ["text_input", "analysis_type"],
                    "outputs": ["analysis_result"],
                },
                "data_processing_template": {
                    "nodes": ["CSVReaderNode", "JSONReaderNode", "SwitchNode"],
                    "connections": ["reader -> switch", "switch -> processor"],
                    "inputs": ["file_path", "operation"],
                    "outputs": ["processed_data"],
                },
            }

        @self.server.resource("docs://api/usage")
        def get_usage_documentation():
            """Get API usage documentation."""
            return {
                "authentication": {
                    "header": "X-API-Key",
                    "description": "Include your API key in the X-API-Key header",
                },
                "tools": {
                    "execute_text_analysis": {
                        "description": "Analyze text content",
                        "parameters": {
                            "text": "Text to analyze (required)",
                            "analysis_type": "Type of analysis: sentiment, classification, extraction",
                        },
                    },
                    "process_data_file": {
                        "description": "Process data files",
                        "parameters": {
                            "file_path": "Path to CSV or JSON file (required)",
                            "operation": "Operation: analyze, transform, validate",
                        },
                    },
                },
                "examples": {
                    "text_analysis": {
                        "text": "This product is amazing!",
                        "analysis_type": "sentiment",
                    },
                    "data_processing": {
                        "file_path": "/data/sales.csv",
                        "operation": "analyze",
                    },
                },
            }

    def _build_text_analysis_workflow(self, analysis_type: str) -> WorkflowBuilder:
        """Build a text analysis workflow."""
        workflow = WorkflowBuilder()

        # Add LLM agent for text analysis
        workflow.add_node(
            "LLMAgentNode",
            node_id="text_analyzer",
            prompt_template=self._get_analysis_prompt(analysis_type),
            model_name="gpt-3.5-turbo",
            temperature=0.1,
        )

        return workflow

    def _build_csv_processing_workflow(self, operation: str) -> WorkflowBuilder:
        """Build a CSV processing workflow."""
        workflow = WorkflowBuilder()

        # CSV reader
        workflow.add_node("CSVReaderNode", node_id="csv_reader", encoding="utf-8")

        # Processing logic based on operation
        if operation == "analyze":
            workflow.add_node(
                "LLMAgentNode",
                node_id="data_analyzer",
                prompt_template="Analyze this CSV data and provide insights: {data}",
                model_name="gpt-3.5-turbo",
            )
            workflow.add_connection("csv_reader", "data_analyzer", "data", "data")

        return workflow

    def _build_json_processing_workflow(self, operation: str) -> WorkflowBuilder:
        """Build a JSON processing workflow."""
        workflow = WorkflowBuilder()

        # JSON reader
        workflow.add_node("JSONReaderNode", node_id="json_reader")

        # Switch node for operation routing
        workflow.add_node(
            "SwitchNode", node_id="operation_switch", switch_key="operation"
        )

        workflow.add_connection("json_reader", "operation_switch", "data", "input_data")

        return workflow

    def _get_analysis_prompt(self, analysis_type: str) -> str:
        """Get analysis prompt template based on type."""
        prompts = {
            "sentiment": "Analyze the sentiment of this text: {text_input}. Return positive, negative, or neutral.",
            "classification": "Classify this text into categories: {text_input}. Provide the most likely category.",
            "extraction": "Extract key entities and topics from this text: {text_input}. Return as structured data.",
        }
        return prompts.get(analysis_type, prompts["sentiment"])

    def run(self, host: str = "localhost", port: int = 8080):
        """Run the MCP server."""
        self._start_time = time.time()
        logger.info(f"Starting Kailash MCP server on {host}:{port}")

        # Run with HTTP transport for easier client access
        self.server.run(enable_http_transport=True, host=host, port=port)


async def main():
    """Main function to run the server."""
    # Create and run the server
    server = KailashMCPServer("kailash-demo-server")

    # Run the server
    server.run()


if __name__ == "__main__":
    asyncio.run(main())
