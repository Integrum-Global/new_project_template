"""
Quickstart examples for AI Registry MCP Server.

This module provides simple examples to get users started quickly
with the AI Registry MCP Server and workflows.
"""

import json
from typing import Any, Dict

# Import workflows
from ..workflows import (
    execute_agent_search,
    execute_domain_deep_dive,
    execute_domain_overview,
    execute_simple_search,
)


def quickstart_basic_search() -> Dict[str, Any]:
    """
    Quickstart Example 1: Basic Search

    This example shows how to perform a simple keyword search
    across the AI Registry.
    """
    print("🔍 Quickstart Example 1: Basic Search")
    print("=" * 50)

    try:
        # Simple keyword search
        results = execute_simple_search(query="machine learning healthcare", limit=5)

        print(f"✅ Found {results.get('count', 0)} use cases")
        print("\nTop Results:")

        for i, uc in enumerate(results.get("results", [])[:3], 1):
            print(f"\n{i}. {uc.get('name', 'Unknown')}")
            print(f"   Domain: {uc.get('application_domain', 'Unknown')}")
            print(f"   Status: {uc.get('status', 'Unknown')}")
            if score := uc.get("_relevance_score"):
                print(f"   Relevance: {score:.2f}")

        return results

    except Exception as e:
        print(f"❌ Error: {e}")
        return {"error": str(e)}


def quickstart_filtered_search() -> Dict[str, Any]:
    """
    Quickstart Example 2: Filtered Search

    This example shows how to search with filters for more
    targeted results.
    """
    print("\n🎯 Quickstart Example 2: Filtered Search")
    print("=" * 50)

    try:
        # Search for production-ready finance applications
        results = execute_simple_search(
            query="",  # Empty query to get all results
            filters={"domain": "Finance", "status": "Production"},
            limit=10,
        )

        print(
            f"✅ Found {results.get('count', 0)} production-ready finance AI use cases"
        )

        if results.get("results"):
            print("\nProduction Finance AI Applications:")
            for i, uc in enumerate(results["results"], 1):
                print(f"\n{i}. {uc.get('name', 'Unknown')}")
                methods = uc.get("ai_methods", [])
                print(f"   AI Methods: {', '.join(methods[:3])}")
                if narrative := uc.get("narrative"):
                    print(f"   Summary: {narrative[:100]}...")

        return results

    except Exception as e:
        print(f"❌ Error: {e}")
        return {"error": str(e)}


def quickstart_agent_conversation() -> Dict[str, Any]:
    """
    Quickstart Example 3: Agent Conversation

    This example shows how to have a natural language conversation
    with the AI Registry using an LLM agent.
    """
    print("\n🤖 Quickstart Example 3: Agent Conversation")
    print("=" * 50)

    try:
        # Natural language query
        results = execute_agent_search(
            user_query="What are the most common AI methods used in healthcare? Give me examples of successful implementations.",
            provider="ollama",
            model="llama3.1:8b-instruct-q8_0",
        )

        if results.get("success"):
            response = results.get("response", {})
            print("🤖 AI Agent Response:")
            print("-" * 30)

            # Extract message content
            if isinstance(response, dict) and "content" in response:
                print(response["content"])
            elif isinstance(response, str):
                print(response)
            else:
                print("Agent provided a response (format not displayed in quickstart)")

            # Show tool calls if any
            if tool_calls := response.get("tool_calls"):
                print(f"\n🔧 Agent used {len(tool_calls)} tools:")
                for call in tool_calls:
                    func_name = call.get("function", {}).get("name", "unknown")
                    print(f"   - {func_name}")
        else:
            print(f"❌ Agent error: {results.get('error', 'Unknown error')}")

        return results

    except Exception as e:
        print(f"❌ Error: {e}")
        return {"error": str(e)}


def quickstart_domain_analysis() -> Dict[str, Any]:
    """
    Quickstart Example 4: Domain Analysis

    This example shows how to get insights about AI adoption
    across different domains.
    """
    print("\n📊 Quickstart Example 4: Domain Analysis")
    print("=" * 50)

    try:
        # Get overview of all domains
        results = execute_domain_overview(output_format="summary")

        if results.get("success"):
            stats = results.get("basic_stats", {})
            print("✅ Registry Overview:")
            print(f"   Total Use Cases: {stats.get('total_use_cases', 0)}")
            print(f"   Domains: {stats.get('domains', {}).get('count', 0)}")
            print(f"   AI Methods: {stats.get('ai_methods', {}).get('count', 0)}")

            # Show top domains
            domain_dist = stats.get("domain_distribution", {})
            if domain_dist:
                print("\n📈 Top Domains by Use Case Count:")
                top_domains = sorted(
                    domain_dist.items(), key=lambda x: x[1], reverse=True
                )[:5]
                for i, (domain, count) in enumerate(top_domains, 1):
                    print(f"   {i}. {domain}: {count} use cases")

            # Show summary if available
            if summary := results.get("summary"):
                print(f"\n📝 Summary: {summary}")

        return results

    except Exception as e:
        print(f"❌ Error: {e}")
        return {"error": str(e)}


def quickstart_healthcare_deep_dive() -> Dict[str, Any]:
    """
    Quickstart Example 5: Healthcare Deep Dive

    This example shows how to perform a detailed analysis
    of AI implementations in healthcare.
    """
    print("\n🏥 Quickstart Example 5: Healthcare Deep Dive")
    print("=" * 50)

    try:
        # Deep dive into healthcare domain
        results = execute_domain_deep_dive(
            domain="Healthcare", provider="ollama", model="llama3.1:8b-instruct-q8_0"
        )

        use_cases = results.get("use_cases", {})
        analytics = results.get("analytics", {})

        print("✅ Healthcare AI Analysis Complete")
        print(f"   Use Cases Found: {use_cases.get('count', 0)}")

        # Show analytics summary
        if analytics.get("success") and "domains" in analytics:
            healthcare_data = analytics["domains"].get("Healthcare", {})
            print(
                f"   Top AI Methods: {', '.join([m[0] for m in healthcare_data.get('top_methods', [])[:3]])}"
            )
            print(f"   Maturity Index: {healthcare_data.get('maturity_index', 0)}/4.0")

        # Show AI insights
        insights = results.get("insights", {})
        if insights.get("success"):
            print("\n🧠 AI-Generated Insights:")
            print(
                "   (Insights would be displayed here - see full response for details)"
            )

        return results

    except Exception as e:
        print(f"❌ Error: {e}")
        return {"error": str(e)}


def run_all_quickstart_examples() -> Dict[str, Any]:
    """
    Run all quickstart examples in sequence.

    This function demonstrates the main capabilities of the
    AI Registry MCP Server and workflows.
    """
    print("🚀 AI Registry MCP Server - Quickstart Examples")
    print("=" * 60)
    print("Running all examples to demonstrate key capabilities...\n")

    results = {}

    # Example 1: Basic Search
    results["basic_search"] = quickstart_basic_search()

    # Example 2: Filtered Search
    results["filtered_search"] = quickstart_filtered_search()

    # Example 3: Agent Conversation (skip if no LLM available)
    try:
        results["agent_conversation"] = quickstart_agent_conversation()
    except Exception as e:
        print(f"\n⚠️  Skipping agent example (LLM not available): {e}")
        results["agent_conversation"] = {"skipped": str(e)}

    # Example 4: Domain Analysis
    results["domain_analysis"] = quickstart_domain_analysis()

    # Example 5: Healthcare Deep Dive (skip if no LLM available)
    try:
        results["healthcare_deep_dive"] = quickstart_healthcare_deep_dive()
    except Exception as e:
        print(f"\n⚠️  Skipping deep dive example (LLM not available): {e}")
        results["healthcare_deep_dive"] = {"skipped": str(e)}

    print("\n" + "=" * 60)
    print("🎉 Quickstart Examples Complete!")
    print("\nNext Steps:")
    print("1. Explore the workflows/ directory for more advanced patterns")
    print("2. Check the examples/ directory for specialized use cases")
    print("3. Read the documentation for detailed API reference")
    print("4. Start the MCP server: python -m apps.ai_registry")

    return results


# Utility functions for demonstration
def demo_mcp_server_tools():
    """
    Demonstrate the MCP server tools available.

    This shows what tools are available when connecting to
    the AI Registry MCP server.
    """
    print("\n🔧 Available MCP Server Tools")
    print("=" * 40)

    tools = [
        {
            "name": "search_use_cases",
            "description": "Search AI use cases using full-text search",
            "example": "search_use_cases(query='machine learning healthcare', limit=10)",
        },
        {
            "name": "filter_by_domain",
            "description": "Get all AI use cases for a specific domain",
            "example": "filter_by_domain(domain='Healthcare')",
        },
        {
            "name": "filter_by_ai_method",
            "description": "Get use cases using specific AI methods",
            "example": "filter_by_ai_method(method='Deep Learning')",
        },
        {
            "name": "filter_by_status",
            "description": "Get use cases by implementation status",
            "example": "filter_by_status(status='Production')",
        },
        {
            "name": "get_use_case_details",
            "description": "Get detailed info for a specific use case",
            "example": "get_use_case_details(use_case_id=42)",
        },
        {
            "name": "get_statistics",
            "description": "Get comprehensive registry statistics",
            "example": "get_statistics()",
        },
        {
            "name": "list_domains",
            "description": "List all available domains",
            "example": "list_domains()",
        },
        {
            "name": "list_ai_methods",
            "description": "List all AI methods in the registry",
            "example": "list_ai_methods()",
        },
        {
            "name": "find_similar_cases",
            "description": "Find use cases similar to a given one",
            "example": "find_similar_cases(use_case_id=42, limit=5)",
        },
        {
            "name": "analyze_trends",
            "description": "Analyze trends and patterns",
            "example": "analyze_trends(analysis_type='domain_trends')",
        },
    ]

    for i, tool in enumerate(tools, 1):
        print(f"{i:2d}. {tool['name']}")
        print(f"    {tool['description']}")
        print(f"    Example: {tool['example']}")
        print()


def demo_workflow_patterns():
    """
    Demonstrate the available workflow patterns.
    """
    print("\n⚙️  Available Workflow Patterns")
    print("=" * 40)

    patterns = [
        {
            "name": "Simple Search",
            "module": "workflows.basic_search",
            "function": "execute_simple_search",
            "description": "Direct search with optional filters",
            "use_case": "Quick lookups and programmatic access",
        },
        {
            "name": "Agent Search",
            "module": "workflows.basic_search",
            "function": "execute_agent_search",
            "description": "Natural language search via LLM agent",
            "use_case": "Conversational queries and complex research",
        },
        {
            "name": "Domain Overview",
            "module": "workflows.domain_analysis",
            "function": "execute_domain_overview",
            "description": "Analysis across all domains",
            "use_case": "Strategic planning and market research",
        },
        {
            "name": "Domain Deep Dive",
            "module": "workflows.domain_analysis",
            "function": "execute_domain_deep_dive",
            "description": "Detailed analysis of specific domain",
            "use_case": "Domain expertise and competitive analysis",
        },
        {
            "name": "Cross-Domain Comparison",
            "module": "workflows.domain_analysis",
            "function": "execute_cross_domain_comparison",
            "description": "Compare AI adoption across domains",
            "use_case": "Cross-industry learning and benchmarking",
        },
    ]

    for i, pattern in enumerate(patterns, 1):
        print(f"{i}. {pattern['name']}")
        print(f"   Module: {pattern['module']}")
        print(f"   Function: {pattern['function']}")
        print(f"   Description: {pattern['description']}")
        print(f"   Use Case: {pattern['use_case']}")
        print()


def save_example_results(
    results: Dict[str, Any], filename: str = "quickstart_results.json"
):
    """
    Save example results to a file for inspection.

    Args:
        results: Results from running examples
        filename: Output filename
    """
    try:
        with open(filename, "w") as f:
            json.dump(results, f, indent=2, default=str)
        print(f"📁 Results saved to {filename}")
    except Exception as e:
        print(f"❌ Error saving results: {e}")


# Main execution
if __name__ == "__main__":
    # Run quickstart examples
    results = run_all_quickstart_examples()

    # Show additional information
    demo_mcp_server_tools()
    demo_workflow_patterns()

    # Save results for inspection
    save_example_results(results)
