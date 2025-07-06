"""
AI Registry MCP Server Solution.

A comprehensive Model Context Protocol server for querying and analyzing
the ISO/IEC AI Registry containing 187 documented AI implementations
across 22 domains.

Main Components:
- MCP Server with 10 specialized tools
- Custom Kailash nodes for advanced operations
- Pre-built workflows for common analysis patterns
- LLM agent integration for natural language queries
- Comprehensive examples and documentation

Quick Start:
    # Start the MCP server
    python -m apps.ai_registry

    # Basic search
    from apps.ai_registry.workflows import execute_simple_search
    results = execute_simple_search("machine learning healthcare")

    # Agent conversation
    from apps.ai_registry.workflows import execute_agent_search
    response = execute_agent_search("What AI methods work best in finance?")

For detailed documentation, see README.md and IMPLEMENTATION.md.
"""

# Register custom nodes with WorkflowBuilder
from . import node_registry
from .config import config
from .indexer import RegistryIndexer
from .mcp_server import AIRegistryMCPServer, AIRegistryServer

# Import enterprise servers
from .servers import APIAggregatorServer, IoTProcessorServer, SharePointConnectorServer
from .workflows import AnalysisWorkflows, RAGWorkflows, SearchWorkflows

__version__ = "1.0.0"

__all__ = [
    # Configuration
    "config",
    # Main server components
    "AIRegistryMCPServer",
    "AIRegistryServer",
    "RegistryIndexer",
    # Enterprise servers
    "SharePointConnectorServer",
    "APIAggregatorServer",
    "IoTProcessorServer",
    # Main workflow classes
    "RAGWorkflows",
    "SearchWorkflows",
    "AnalysisWorkflows",
]
