#!/usr/bin/env python3
"""
MCP Tool Orchestration Example

This example demonstrates advanced tool orchestration patterns including:
- Tool chaining and composition
- Parallel tool execution
- Conditional tool selection
- Tool result aggregation
- Error handling and retries
"""

import asyncio
from typing import Any, Dict, List

from apps.mcp_platform import BasicMCPServer, MCPService
from kailash import LocalRuntime, WorkflowBuilder


# Example 1: Tool Chaining
def create_data_processing_tools():
    """Create a set of data processing tools that can be chained."""

    server = BasicMCPServer(
        name="data-processor", description="Data processing and transformation tools"
    )

    @server.tool("fetch_data")
    async def fetch_data(source: str) -> dict:
        """Fetch data from a source."""
        # Simulated data fetch
        data = {
            "users": [
                {"id": 1, "name": "Alice", "score": 85},
                {"id": 2, "name": "Bob", "score": 92},
                {"id": 3, "name": "Charlie", "score": 78},
            ]
        }
        return {"data": data, "source": source, "timestamp": "2024-01-01T10:00:00"}

    @server.tool("filter_data")
    async def filter_data(data: dict, criteria: dict) -> dict:
        """Filter data based on criteria."""
        users = data.get("users", [])
        min_score = criteria.get("min_score", 0)
        filtered = [u for u in users if u["score"] >= min_score]
        return {"filtered_data": filtered, "count": len(filtered)}

    @server.tool("transform_data")
    async def transform_data(data: list, format: str) -> dict:
        """Transform data to specified format."""
        if format == "summary":
            avg_score = sum(u["score"] for u in data) / len(data) if data else 0
            return {
                "format": "summary",
                "total_users": len(data),
                "average_score": avg_score,
                "top_performer": (
                    max(data, key=lambda x: x["score"])["name"] if data else None
                ),
            }
        return {"data": data, "format": format}

    @server.tool("save_results")
    async def save_results(data: dict, destination: str) -> dict:
        """Save processed results."""
        # Simulated save operation
        return {
            "status": "saved",
            "destination": destination,
            "records": data.get("total_users", len(data.get("data", []))),
        }

    return server


# Example 2: Parallel Tool Execution
async def parallel_analysis_example():
    """Execute multiple analysis tools in parallel."""

    server = BasicMCPServer(name="analyzer", description="Analysis tools")

    @server.tool("sentiment_analysis")
    async def analyze_sentiment(text: str) -> dict:
        """Analyze text sentiment."""
        await asyncio.sleep(0.1)  # Simulate processing
        return {"text": text, "sentiment": "positive", "confidence": 0.85}

    @server.tool("keyword_extraction")
    async def extract_keywords(text: str) -> dict:
        """Extract keywords from text."""
        await asyncio.sleep(0.1)  # Simulate processing
        return {"text": text, "keywords": ["MCP", "platform", "tools"]}

    @server.tool("language_detection")
    async def detect_language(text: str) -> dict:
        """Detect text language."""
        await asyncio.sleep(0.1)  # Simulate processing
        return {"text": text, "language": "en", "confidence": 0.99}

    # Create service and execute tools in parallel
    service = MCPService()
    service.add_server(server)

    text = "The MCP platform provides excellent tools for orchestration"

    # Execute all analyses in parallel
    results = await asyncio.gather(
        service.execute_tool("analyzer", "sentiment_analysis", {"text": text}),
        service.execute_tool("analyzer", "keyword_extraction", {"text": text}),
        service.execute_tool("analyzer", "language_detection", {"text": text}),
    )

    return {"sentiment": results[0], "keywords": results[1], "language": results[2]}


# Example 3: Conditional Tool Selection
def create_conditional_workflow():
    """Create workflow with conditional tool selection."""

    builder = WorkflowBuilder()

    # Input validation
    builder.add_node(
        "PythonCodeNode",
        "validate_input",
        code="""
        data_type = inputs.get("data_type", "unknown")
        size = inputs.get("size", 0)

        if data_type == "image" and size > 1000000:
            processing_path = "heavy"
        elif data_type == "text" and size < 10000:
            processing_path = "light"
        else:
            processing_path = "standard"

        return {
            "data_type": data_type,
            "size": size,
            "processing_path": processing_path
        }
        """,
    )

    # Switch node for conditional routing
    builder.add_node(
        "SwitchNode",
        "route_processor",
        config={
            "switch_on": "processing_path",
            "cases": {
                "heavy": "heavy_processor",
                "light": "light_processor",
                "standard": "standard_processor",
            },
        },
    )

    # Different processing paths
    builder.add_node(
        "MCPToolNode",
        "heavy_processor",
        config={
            "server": "processors",
            "tool": "heavy_processing",
            "retry_count": 3,
            "timeout": 300,
        },
    )

    builder.add_node(
        "MCPToolNode",
        "light_processor",
        config={"server": "processors", "tool": "light_processing", "timeout": 30},
    )

    builder.add_node(
        "MCPToolNode",
        "standard_processor",
        config={"server": "processors", "tool": "standard_processing", "timeout": 120},
    )

    # Result aggregation
    builder.add_node(
        "MergeNode", "aggregate_results", config={"merge_strategy": "deep"}
    )

    # Connections
    builder.add_connection("validate_input", "route_processor", "result", "")
    builder.add_connection("heavy_processor", "aggregate_results", "result", "")
    builder.add_connection("light_processor", "aggregate_results", "result", "")
    builder.add_connection("standard_processor", "aggregate_results", "result", "")

    return builder.build()


# Example 4: Tool Composition Pattern
class CompositeToolServer:
    """Server that composes multiple tools into higher-level operations."""

    def __init__(self):
        self.server = BasicMCPServer(
            name="composite-tools", description="High-level composed operations"
        )
        self._setup_tools()

    def _setup_tools(self):
        """Set up composite tools."""

        @self.server.tool("analyze_document")
        async def analyze_document(document_path: str) -> dict:
            """Comprehensive document analysis using multiple tools."""

            # Simulate calling multiple underlying tools
            results = {
                "extraction": await self._extract_text(document_path),
                "analysis": await self._analyze_content(document_path),
                "metadata": await self._extract_metadata(document_path),
            }

            # Compose results
            return {
                "document": document_path,
                "word_count": results["extraction"]["word_count"],
                "summary": results["analysis"]["summary"],
                "topics": results["analysis"]["topics"],
                "created_date": results["metadata"]["created"],
                "author": results["metadata"]["author"],
                "confidence_scores": {
                    "extraction": 0.95,
                    "analysis": 0.88,
                    "metadata": 0.99,
                },
            }

        @self.server.tool("process_batch")
        async def process_batch(items: List[dict], operation: str) -> dict:
            """Process multiple items with specified operation."""

            results = []
            errors = []

            for i, item in enumerate(items):
                try:
                    if operation == "transform":
                        result = await self._transform_item(item)
                    elif operation == "validate":
                        result = await self._validate_item(item)
                    else:
                        result = {"error": f"Unknown operation: {operation}"}

                    results.append(result)
                except Exception as e:
                    errors.append({"index": i, "error": str(e)})

            return {
                "processed": len(results),
                "errors": len(errors),
                "results": results,
                "error_details": errors,
            }

    async def _extract_text(self, path: str) -> dict:
        """Extract text from document."""
        return {"word_count": 1500, "pages": 5}

    async def _analyze_content(self, path: str) -> dict:
        """Analyze document content."""
        return {
            "summary": "Technical documentation about MCP",
            "topics": ["MCP", "tools", "orchestration"],
        }

    async def _extract_metadata(self, path: str) -> dict:
        """Extract document metadata."""
        return {"created": "2024-01-01", "author": "System"}

    async def _transform_item(self, item: dict) -> dict:
        """Transform a single item."""
        return {"transformed": True, "id": item.get("id")}

    async def _validate_item(self, item: dict) -> dict:
        """Validate a single item."""
        return {"valid": True, "id": item.get("id")}


# Example 5: Error Handling and Retry Pattern
async def resilient_tool_execution():
    """Demonstrate error handling and retry patterns."""

    server = BasicMCPServer(name="resilient", description="Resilient tools")

    attempt_count = 0

    @server.tool("flaky_operation")
    async def flaky_operation(success_rate: float = 0.5) -> dict:
        """Operation that may fail (for demonstration)."""
        nonlocal attempt_count
        attempt_count += 1

        import random

        if random.random() > success_rate:
            raise Exception(f"Operation failed on attempt {attempt_count}")

        return {"status": "success", "attempts": attempt_count}

    # Create workflow with retry logic
    builder = WorkflowBuilder()

    builder.add_node(
        "MCPToolNode",
        "execute_with_retry",
        config={
            "server": "resilient",
            "tool": "flaky_operation",
            "retry_count": 3,
            "retry_delay": 1,
            "exponential_backoff": True,
            "error_handler": "handle_error",
        },
    )

    builder.add_node(
        "PythonCodeNode",
        "handle_error",
        code="""
        error_msg = inputs.get("error", "Unknown error")
        attempts = inputs.get("attempts", 0)

        return {
            "status": "failed",
            "error": error_msg,
            "total_attempts": attempts,
            "fallback_result": {"data": "default"}
        }
        """,
    )

    workflow = builder.build()

    # Execute with runtime
    runtime = LocalRuntime()
    result = await runtime.execute(workflow, {"success_rate": 0.3})

    return result


if __name__ == "__main__":
    print("MCP Tool Orchestration Examples")
    print("=" * 50)

    # Example 1: Tool chaining
    print("\n1. Tool Chaining:")
    processor = create_data_processing_tools()
    print(f"   Created: {processor.name}")
    print(f"   Tools: {list(processor.list_tools().keys())}")

    # Example 2: Parallel execution
    print("\n2. Parallel Analysis:")
    parallel_results = asyncio.run(parallel_analysis_example())
    print(f"   Sentiment: {parallel_results['sentiment']['sentiment']}")
    print(f"   Keywords: {parallel_results['keywords']['keywords']}")
    print(f"   Language: {parallel_results['language']['language']}")

    # Example 3: Conditional workflow
    print("\n3. Conditional Workflow:")
    workflow = create_conditional_workflow()
    print(f"   Nodes: {len(workflow.nodes)}")
    print("   Routes: heavy, light, standard")

    # Example 4: Composite tools
    print("\n4. Composite Tools:")
    composite = CompositeToolServer()
    print(f"   Server: {composite.server.name}")
    print("   High-level operations: analyze_document, process_batch")

    # Example 5: Resilient execution
    print("\n5. Resilient Execution:")
    resilient_result = asyncio.run(resilient_tool_execution())
    print(f"   Final status: {resilient_result.get('status', 'completed')}")

    print("\n✓ Orchestration examples completed!")
