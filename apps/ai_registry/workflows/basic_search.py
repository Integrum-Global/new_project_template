"""
Basic search workflows for AI Registry.

This module provides simple, ready-to-use workflows for searching
and querying the AI Registry.
"""

from typing import Any, Dict, Optional

from kailash import Workflow, WorkflowBuilder
from kailash.nodes.ai import LLMAgentNode
from kailash.runtime import LocalRuntime

from ..nodes import RegistrySearchNode


def create_simple_search_workflow(
    workflow_name: str = "ai_registry_search",
) -> Workflow:
    """
    Create a basic search workflow for AI Registry.

    This workflow provides simple search capabilities using the RegistrySearchNode.

    Args:
        workflow_name: Name for the workflow

    Returns:
        Configured Workflow object
    """
    # Use WorkflowBuilder for better flexibility
    builder = WorkflowBuilder()

    # Add search node using string-based node creation
    builder.add_node(
        "RegistrySearchNode", node_id="search", config={"name": "registry_search"}
    )

    return builder.build(name=workflow_name, description="AI Registry Simple Search")


def create_agent_search_workflow(
    workflow_name: str = "ai_registry_agent_search",
) -> Workflow:
    """
    Create an LLM agent-powered search workflow.

    This workflow uses an LLM agent to interpret natural language queries
    and search the AI Registry using MCP tools.

    Args:
        workflow_name: Name for the workflow

    Returns:
        Configured Workflow object
    """
    builder = WorkflowBuilder()

    # Add LLM agent with MCP integration using string-based node creation
    builder.add_node("LLMAgentNode", node_id="agent", config={"name": "search_agent"})

    return builder.build(name=workflow_name, description="AI Registry Agent Search")


def create_guided_search_workflow(
    workflow_name: str = "ai_registry_guided_search",
) -> Workflow:
    """
    Create a guided search workflow with progressive refinement.

    This workflow guides users through a structured search process,
    starting broad and then refining based on results.

    Args:
        workflow_name: Name for the workflow

    Returns:
        Configured Workflow object
    """
    builder = WorkflowBuilder()

    # Initial broad search
    initial_id = builder.add_node(
        "RegistrySearchNode",
        node_id="initial_search",
        config={"name": "initial_search"},
    )

    # Agent for query refinement
    agent_id = builder.add_node(
        "LLMAgentNode", node_id="refinement_agent", config={"name": "refinement_agent"}
    )

    # Refined search
    refined_id = builder.add_node(
        "RegistrySearchNode",
        node_id="refined_search",
        config={"name": "refined_search"},
    )

    # Connect nodes using the proper 4-parameter format
    builder.add_connection(initial_id, "results", agent_id, "context")
    builder.add_connection(agent_id, "response", refined_id, "query")

    return builder.build(name=workflow_name, description="AI Registry Guided Search")


def execute_simple_search(
    query: str,
    limit: int = 20,
    filters: Optional[Dict[str, Any]] = None,
    runtime: Optional[LocalRuntime] = None,
) -> Dict[str, Any]:
    """
    Execute a simple search using the basic search workflow.

    Args:
        query: Search query string
        limit: Maximum number of results
        filters: Optional filters to apply
        runtime: Runtime to use (creates new if None)

    Returns:
        Search results
    """
    if runtime is None:
        runtime = LocalRuntime()

    workflow = create_simple_search_workflow()

    parameters = {
        "search": {
            "query": query,
            "limit": limit,
            "filters": filters or {},
            "include_stats": True,
        }
    }

    results, _ = runtime.execute(workflow, parameters=parameters)
    return results.get("search", {})


def execute_agent_search(
    user_query: str,
    provider: str = "ollama",
    model: str = "llama3.1:8b-instruct-q8_0",
    mcp_server_config: Optional[Dict[str, Any]] = None,
    runtime: Optional[LocalRuntime] = None,
) -> Dict[str, Any]:
    """
    Execute an agent-powered search using natural language.

    Args:
        user_query: Natural language query from user
        provider: LLM provider to use
        model: LLM model to use
        mcp_server_config: MCP server configuration
        runtime: Runtime to use (creates new if None)

    Returns:
        Agent response and search results
    """
    if runtime is None:
        runtime = LocalRuntime()

    workflow = create_agent_search_workflow()

    # Default MCP server config for AI Registry
    if mcp_server_config is None:
        mcp_server_config = {
            "name": "ai-registry",
            "transport": "stdio",
            "command": "python",
            "args": ["-m", "src.solutions.ai_registry"],
        }

    parameters = {
        "agent": {
            "provider": provider,
            "model": model,
            "messages": [
                {
                    "role": "system",
                    "content": """You are an AI Registry search assistant. You help users find AI use cases from the ISO/IEC AI Registry containing 187 documented AI implementations across 22 domains.

Your available tools allow you to:
- Search use cases by keywords across all fields
- Filter by domain (Healthcare, Finance, Manufacturing, etc.)
- Filter by AI methods (Machine Learning, NLP, Computer Vision, etc.)
- Filter by implementation status (PoC, Production, Pilot, etc.)
- Get detailed information about specific use cases
- Find similar use cases
- Get statistics about the registry

When a user asks a question, analyze what they're looking for and use the appropriate tools to help them. Always provide helpful context and explain what you found.""",
                },
                {"role": "user", "content": user_query},
            ],
            "mcp_servers": [mcp_server_config],
            "auto_discover_tools": True,
            "generation_config": {"tool_choice": "auto", "max_tool_calls": 5},
        }
    }

    results, _ = runtime.execute(workflow, parameters=parameters)
    return results.get("agent", {})


def execute_guided_search(
    initial_query: str,
    provider: str = "ollama",
    model: str = "llama3.1:8b-instruct-q8_0",
    runtime: Optional[LocalRuntime] = None,
) -> Dict[str, Any]:
    """
    Execute a guided search with progressive refinement.

    Args:
        initial_query: Initial search query
        provider: LLM provider for refinement agent
        model: LLM model for refinement agent
        runtime: Runtime to use (creates new if None)

    Returns:
        Results from guided search process
    """
    if runtime is None:
        runtime = LocalRuntime()

    workflow = create_guided_search_workflow()

    parameters = {
        "initial_search": {
            "query": initial_query,
            "limit": 50,  # Get more results for analysis
            "include_stats": True,
        },
        "refinement_agent": {
            "provider": provider,
            "model": model,
            "messages": [
                {
                    "role": "system",
                    "content": """You are a search refinement assistant. Your job is to analyze search results and suggest refinements to help users find more relevant AI use cases.

Based on the initial search results, identify:
1. Common domains that might be relevant
2. AI methods that appear frequently
3. Implementation statuses that might filter results appropriately
4. Refined search terms that could improve relevance

Provide specific refinement suggestions including:
- More specific search terms
- Useful filters (domain, AI methods, status)
- Alternative query approaches""",
                }
            ],
        },
        "refined_search": {"limit": 20, "include_stats": True},
    }

    results, execution_context = runtime.execute(workflow, parameters=parameters)

    return {
        "initial_results": results.get("initial_search", {}),
        "refinement_suggestions": results.get("refinement_agent", {}),
        "refined_results": results.get("refined_search", {}),
        "execution_context": execution_context,
    }


# Example usage functions for testing and demonstration
def example_healthcare_search(runtime: Optional[LocalRuntime] = None) -> Dict[str, Any]:
    """Example: Search for healthcare AI use cases."""
    return execute_simple_search(
        query="healthcare medical diagnosis",
        limit=10,
        filters={"domain": "Healthcare"},
        runtime=runtime,
    )


def example_nlp_search(runtime: Optional[LocalRuntime] = None) -> Dict[str, Any]:
    """Example: Search for NLP-based AI use cases."""
    return execute_simple_search(
        query="natural language processing text",
        filters={"ai_methods": ["Natural Language Processing", "NLP"]},
        runtime=runtime,
    )


def example_production_ready_search(
    runtime: Optional[LocalRuntime] = None,
) -> Dict[str, Any]:
    """Example: Search for production-ready implementations."""
    return execute_simple_search(
        query="",  # Empty query to get all
        filters={"status": "Production"},
        limit=30,
        runtime=runtime,
    )


def example_agent_conversation(
    runtime: Optional[LocalRuntime] = None,
) -> Dict[str, Any]:
    """Example: Natural language conversation with AI Registry agent."""
    return execute_agent_search(
        user_query="I'm interested in AI for financial fraud detection. What implementations exist and how mature are they?",
        runtime=runtime,
    )


# Workflow configuration helpers
def get_search_workflow_configs() -> Dict[str, Dict[str, Any]]:
    """Get pre-configured workflow configurations."""
    return {
        "simple_search": {
            "description": "Basic keyword search with optional filters",
            "use_cases": [
                "Quick lookup of specific AI implementations",
                "Filtered searches by domain or method",
                "Programmatic access to registry data",
            ],
            "parameters": {
                "required": ["query"],
                "optional": ["limit", "filters", "sort_by"],
            },
        },
        "agent_search": {
            "description": "Natural language search using LLM agent with MCP tools",
            "use_cases": [
                "Conversational queries about AI use cases",
                "Complex multi-step research",
                "Comparative analysis questions",
            ],
            "parameters": {
                "required": ["user_query"],
                "optional": ["provider", "model", "mcp_server_config"],
            },
        },
        "guided_search": {
            "description": "Progressive search refinement with AI assistance",
            "use_cases": [
                "Exploratory research starting broad",
                "Search optimization and refinement",
                "Discovery of related use cases",
            ],
            "parameters": {
                "required": ["initial_query"],
                "optional": ["provider", "model"],
            },
        },
    }
