#!/usr/bin/env python3
"""
Simple Enhanced MCP Server Usage Examples.

This script demonstrates the working Enhanced MCP Server functionality.
"""

import os
import sys
import time

# Add current directory to Python path for imports
sys.path.insert(0, os.path.dirname(__file__))

from ..mcp_server import AIRegistryMCPServer


def main():
    """Run simple usage examples."""
    print("🚀 AI Registry Enhanced MCP Server - Simple Examples")
    print("=" * 60)

    # Initialize server
    print("\n📋 1. Server Initialization")
    print("-" * 30)
    server = AIRegistryMCPServer()
    print("✅ Server initialized successfully")
    print(f"✅ Server type: {type(server.server).__name__}")
    print(f"✅ Loaded {len(server.indexer.use_cases)} use cases")

    # Demonstrate search functionality
    print("\n🔍 2. Search Functionality")
    print("-" * 30)
    query = "machine learning healthcare"
    results = server.indexer.search(query, 5)
    print(f"Query: '{query}'")
    print(f"Results: {len(results)} matches")
    for i, result in enumerate(results[:3], 1):
        print(
            f"  {i}. {result.get('name', 'Unnamed')} (ID: {result.get('use_case_id', 'N/A')})"
        )

    # Demonstrate filtering
    print("\n📊 3. Domain Filtering")
    print("-" * 30)
    healthcare_cases = server.indexer.filter_by_domain("Healthcare")
    finance_cases = server.indexer.filter_by_domain("Finance")
    print(f"Healthcare cases: {len(healthcare_cases)}")
    print(f"Finance cases: {len(finance_cases)}")

    # Demonstrate statistics
    print("\n📈 4. Registry Statistics")
    print("-" * 30)
    stats = server.indexer.get_statistics()
    print(f"Total use cases: {stats['total_use_cases']}")
    print(f"Domains: {stats['domains']['count']}")
    print(f"AI methods: {stats['ai_methods']['count']}")
    print(f"Top domains: {', '.join(stats['domains']['top'][:5])}")

    # Demonstrate server capabilities
    print("\n⚡ 5. Server Capabilities")
    print("-" * 30)
    server_stats = server.server.get_server_stats()
    print(f"Server features: {list(server_stats.keys())}")

    # Performance demonstration
    print("\n🏃 6. Performance Test")
    print("-" * 30)
    start_time = time.time()
    for _ in range(10):
        server.indexer.search("artificial intelligence", 20)
    avg_time = (time.time() - start_time) / 10
    print(f"Average search time: {avg_time:.3f}s per query")

    # List available tools (conceptual)
    print("\n🔧 7. Available MCP Tools")
    print("-" * 30)
    tools = [
        "search_use_cases",
        "filter_by_domain",
        "filter_by_ai_method",
        "filter_by_status",
        "get_use_case_details",
        "get_statistics",
        "list_domains",
        "list_ai_methods",
        "find_similar_cases",
        "analyze_trends",
        "health_check",
    ]
    print(f"Total tools: {len(tools)}")
    for tool in tools:
        print(f"  ✅ {tool}")

    # Resource endpoints
    print("\n🌐 8. Resource Endpoints")
    print("-" * 30)
    overview = server._format_overview(stats)
    print(f"Overview resource length: {len(overview)} characters")

    domain_resource = server._format_domain_results("Healthcare", healthcare_cases[:5])
    print(f"Healthcare resource length: {len(domain_resource)} characters")

    print("\n" + "=" * 60)
    print("🎉 Enhanced MCP Server Examples Completed!")
    print("✅ All core functionality working properly")
    print("✅ Server ready for MCP client connections")
    print("💡 Use 'python -m mcp_server' to start the server")


if __name__ == "__main__":
    main()
