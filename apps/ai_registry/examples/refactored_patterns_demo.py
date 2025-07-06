#!/usr/bin/env python3
"""
Demonstration of refactored AI Registry patterns using modern Kailash SDK.

This example showcases:
1. Proper node initialization order
2. WorkflowBuilder for dynamic workflows
3. Auto-mapping parameters
4. PythonCodeNode.from_function() for complex logic
5. Enhanced MCP Server features
6. LocalRuntime with enterprise features
"""

import json
from typing import Any, Dict, List

# Import our custom nodes (automatically registered)
from apps.ai_registry import node_registry
from kailash import WorkflowBuilder
from kailash.nodes.code import PythonCodeNode
from kailash.runtime import LocalRuntime


def create_advanced_search_workflow():
    """
    Create an advanced search workflow using modern patterns.

    Demonstrates:
    - WorkflowBuilder for dynamic workflow creation
    - String-based node creation
    - Auto-mapping parameters
    - Proper connection patterns
    """
    builder = WorkflowBuilder("advanced_search", "Advanced AI Registry Search")

    # 1. Add input validator using PythonCodeNode.from_function()
    validator_id = builder.add_node(
        "PythonCodeNode",
        node_id="input_validator",
        config={
            "name": "input_validator",
            "code": """
def validate_search_input(query: str, filters: dict = None) -> dict:
    \"\"\"Validate and normalize search input.\"\"\"
    # Ensure query is not empty
    if not query or not query.strip():
        return {"error": "Query cannot be empty", "valid": False}

    # Normalize query
    normalized_query = query.strip().lower()

    # Validate filters if provided
    valid_filters = {}
    if filters:
        allowed_keys = ["domain", "ai_methods", "status", "min_score"]
        for key, value in filters.items():
            if key in allowed_keys:
                valid_filters[key] = value

    return {
        "result": {
            "normalized_query": normalized_query,
            "filters": valid_filters,
            "valid": True
        }
    }
""",
            "inputs": ["query", "filters"],
            "outputs": ["result", "error", "valid"],
        },
    )

    # 2. Add registry search node (custom node registered via node_registry)
    search_id = builder.add_node(
        "RegistrySearchNode",
        node_id="registry_search",
        config={
            "name": "registry_search",
            # Auto-mapping will connect normalized_query to query parameter
            "auto_map_primary": True,
            "auto_map_from": ["normalized_query"],
        },
    )

    # 3. Add analytics node for result enrichment
    analytics_id = builder.add_node(
        "RegistryAnalyticsNode",
        node_id="result_analytics",
        config={"name": "result_analytics", "analysis_type": "domain_analysis"},
    )

    # 4. Add result formatter using PythonCodeNode
    formatter_id = builder.add_node(
        "PythonCodeNode",
        node_id="result_formatter",
        config={
            "name": "result_formatter",
            "code": """
def format_results(search_results: dict, analytics: dict) -> dict:
    \"\"\"Format and combine search and analytics results.\"\"\"
    formatted = {
        "query": search_results.get("query", ""),
        "total_results": search_results.get("count", 0),
        "results": search_results.get("results", [])[:10],  # Top 10
        "analytics": {
            "domains": analytics.get("domains", {}),
            "insights": analytics.get("comparison", {})
        },
        "success": search_results.get("success", False)
    }

    # Add result summary
    if formatted["results"]:
        domains = set(r.get("application_domain") for r in formatted["results"])
        methods = set()
        for r in formatted["results"]:
            methods.update(r.get("ai_methods", []))

        formatted["summary"] = {
            "unique_domains": len(domains),
            "unique_methods": len(methods),
            "domains": list(domains),
            "methods": list(methods)[:5]  # Top 5 methods
        }

    return {"result": formatted}
""",
            "inputs": ["search_results", "analytics"],
            "outputs": ["result"],
        },
    )

    # Connect nodes using proper 4-parameter format
    # Validator -> Search (with auto-mapping)
    builder.add_connection(
        validator_id,
        "result.normalized_query",  # Dot notation for nested data
        search_id,
        "query",
    )
    builder.add_connection(validator_id, "result.filters", search_id, "filters")

    # Search -> Analytics (for domain analysis)
    builder.add_connection(
        search_id, "results", analytics_id, "use_cases"  # Analytics expects use_cases
    )

    # Both results -> Formatter
    builder.add_connection(
        search_id, "output", formatter_id, "search_results"  # Full output
    )
    builder.add_connection(analytics_id, "output", formatter_id, "analytics")

    return builder.build()


def create_llm_enhanced_workflow():
    """
    Create an LLM-enhanced workflow with MCP integration.

    Demonstrates:
    - LLMAgentNode with MCP tools
    - PythonCodeNode for preprocessing
    - Enterprise features integration
    """
    builder = WorkflowBuilder("llm_enhanced", "LLM-Enhanced AI Registry Analysis")

    # 1. Query preprocessor
    preprocess_id = builder.add_node(
        "PythonCodeNode",
        node_id="query_preprocessor",
        config={
            "name": "query_preprocessor",
            "code": """
def preprocess_query(user_input: str) -> dict:
    \"\"\"Preprocess user input to extract intent and entities.\"\"\"
    import re

    # Extract potential domains
    domains = []
    domain_keywords = {
        "healthcare": ["health", "medical", "clinical", "patient"],
        "finance": ["financial", "banking", "trading", "investment"],
        "manufacturing": ["manufacturing", "production", "factory", "industrial"]
    }

    lower_input = user_input.lower()
    for domain, keywords in domain_keywords.items():
        if any(keyword in lower_input for keyword in keywords):
            domains.append(domain)

    # Extract AI methods
    methods = []
    method_patterns = {
        "Machine Learning": r"\\b(machine learning|ml|supervised|unsupervised)\\b",
        "Deep Learning": r"\\b(deep learning|neural network|cnn|rnn)\\b",
        "NLP": r"\\b(nlp|natural language|text processing|chatbot)\\b",
        "Computer Vision": r"\\b(computer vision|image recognition|visual)\\b"
    }

    for method, pattern in method_patterns.items():
        if re.search(pattern, lower_input, re.IGNORECASE):
            methods.append(method)

    # Determine query type
    query_type = "general"
    if "compare" in lower_input or "versus" in lower_input:
        query_type = "comparison"
    elif "trend" in lower_input or "popular" in lower_input:
        query_type = "trends"
    elif "gap" in lower_input or "missing" in lower_input:
        query_type = "gaps"

    return {
        "result": {
            "original_query": user_input,
            "extracted_domains": domains,
            "extracted_methods": methods,
            "query_type": query_type,
            "enhanced_prompt": f"User is asking about {query_type} related to {', '.join(domains or ['all domains'])} using {', '.join(methods or ['any AI methods'])}"
        }
    }
""",
            "inputs": ["user_input"],
            "outputs": ["result"],
        },
    )

    # 2. LLM Agent with MCP tools
    agent_id = builder.add_node(
        "LLMAgentNode",
        node_id="llm_agent",
        config={
            "name": "ai_registry_agent",
            "provider": "openai",
            "model": "gpt-4o-mini",
            "system_prompt": """You are an AI Registry expert assistant with access to a comprehensive database of AI implementations.

Use the available MCP tools to:
1. Search for relevant AI use cases
2. Analyze domains and methods
3. Compare implementations
4. Identify trends and gaps

Always provide specific examples and actionable insights based on the registry data.""",
            "mcp_servers": [
                {
                    "name": "ai-registry",
                    "transport": "stdio",
                    "command": "python",
                    "args": ["-m", "apps.ai_registry"],
                }
            ],
            "auto_discover_tools": True,
            "generation_config": {
                "tool_choice": "auto",
                "max_tool_calls": 5,
                "temperature": 0.1,
            },
        },
    )

    # 3. Response enhancer
    enhancer_id = builder.add_node(
        "PythonCodeNode",
        node_id="response_enhancer",
        config={
            "name": "response_enhancer",
            "code": """
def enhance_response(agent_response: dict, preprocessing: dict) -> dict:
    \"\"\"Enhance LLM response with additional context and formatting.\"\"\"

    response = agent_response.get("response", "")
    tool_calls = agent_response.get("tool_calls", [])

    # Extract key findings from tool calls
    findings = []
    for call in tool_calls:
        if call.get("tool") == "search_use_cases":
            results = call.get("result", {})
            findings.append(f"Found {results.get('total_results', 0)} relevant use cases")
        elif call.get("tool") == "get_statistics":
            stats = call.get("result", {}).get("registry_statistics", {})
            findings.append(f"Registry contains {stats.get('total_use_cases', 0)} total use cases")

    # Create enhanced response
    enhanced = {
        "response": response,
        "metadata": {
            "query_type": preprocessing.get("query_type"),
            "domains_mentioned": preprocessing.get("extracted_domains", []),
            "methods_mentioned": preprocessing.get("extracted_methods", []),
            "tool_calls_made": len(tool_calls),
            "key_findings": findings
        },
        "success": True
    }

    return {"result": enhanced}
""",
            "inputs": ["agent_response", "preprocessing"],
            "outputs": ["result"],
        },
    )

    # Connect nodes
    builder.add_connection(preprocess_id, "result", agent_id, "context")
    builder.add_connection(preprocess_id, "result.original_query", agent_id, "prompt")
    builder.add_connection(agent_id, "output", enhancer_id, "agent_response")
    builder.add_connection(preprocess_id, "result", enhancer_id, "preprocessing")

    return builder.build()


def demonstrate_enterprise_features():
    """
    Demonstrate enterprise features with the refactored implementation.
    """
    print("🚀 AI Registry - Enterprise Features Demo")
    print("=" * 60)

    # Initialize runtime with enterprise features
    runtime = LocalRuntime(
        debug=True,
        enable_async=True,
        enable_monitoring=True,
        max_concurrency=5,
        resource_limits={"memory_mb": 1024, "timeout_seconds": 30},
    )

    # Example 1: Advanced Search Workflow
    print("\n📋 Example 1: Advanced Search with Analytics")
    print("-" * 40)

    search_workflow = create_advanced_search_workflow()

    search_params = {
        "input_validator": {
            "query": "machine learning healthcare diagnosis",
            "filters": {"domain": "Healthcare", "status": "Production"},
        }
    }

    try:
        results, run_id = runtime.execute(search_workflow, parameters=search_params)

        formatted_results = results.get("result_formatter", {}).get("result", {})
        print(f"✅ Search completed (Run ID: {run_id})")
        print(f"Found {formatted_results.get('total_results', 0)} results")

        if summary := formatted_results.get("summary"):
            print(f"Domains: {', '.join(summary.get('domains', []))}")
            print(f"Top methods: {', '.join(summary.get('methods', []))}")

    except Exception as e:
        print(f"❌ Search failed: {str(e)}")

    # Example 2: LLM-Enhanced Analysis
    print("\n\n🤖 Example 2: LLM-Enhanced Analysis")
    print("-" * 40)

    llm_workflow = create_llm_enhanced_workflow()

    llm_params = {
        "query_preprocessor": {
            "user_input": "Compare AI implementations in healthcare versus finance. What are the gaps?"
        }
    }

    try:
        results, run_id = runtime.execute(llm_workflow, parameters=llm_params)

        enhanced_response = results.get("response_enhancer", {}).get("result", {})
        print(f"✅ Analysis completed (Run ID: {run_id})")

        metadata = enhanced_response.get("metadata", {})
        print(f"Query type: {metadata.get('query_type')}")
        print(f"Tool calls made: {metadata.get('tool_calls_made', 0)}")

        if findings := metadata.get("key_findings"):
            print("\nKey findings:")
            for finding in findings:
                print(f"  - {finding}")

    except Exception as e:
        print(f"❌ Analysis failed: {str(e)}")

    # Example 3: Performance Monitoring
    print("\n\n📊 Example 3: Performance Monitoring")
    print("-" * 40)

    if hasattr(runtime, "get_metrics"):
        metrics = runtime.get_metrics()
        print(f"Total executions: {metrics.get('total_executions', 0)}")
        print(f"Average execution time: {metrics.get('avg_execution_time', 0):.2f}s")
        print(f"Success rate: {metrics.get('success_rate', 0):.1%}")

    print("\n" + "=" * 60)
    print(
        "✨ Demo completed! The AI Registry is now using modern Kailash SDK patterns."
    )


if __name__ == "__main__":
    # Register nodes (happens automatically on import)
    print(f"📦 Registered custom nodes: {list(node_registry._registered_nodes.keys())}")

    # Run the demonstration
    demonstrate_enterprise_features()
