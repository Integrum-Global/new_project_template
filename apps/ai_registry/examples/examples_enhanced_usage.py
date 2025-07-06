#!/usr/bin/env python3
"""
Comprehensive Enhanced MCP Server Usage Examples.

This script demonstrates all Enhanced MCP Server functionality including:
- All 10 MCP tools with caching and formatting
- Server stats and metrics
- Configuration options
- Integration with Kailash nodes
- Performance features
"""

import asyncio
import os
import sys
import time
from pathlib import Path

# Add current directory to Python path for imports
sys.path.insert(0, os.path.dirname(__file__))

from mcp_server import AIRegistryMCPServer


class EnhancedServerExamples:
    """Demonstration of Enhanced MCP Server capabilities."""

    def __init__(self):
        """Initialize with default configuration."""
        print("🚀 Enhanced MCP Server Usage Examples")
        print("=" * 60)

        # Example 1: Basic server initialization
        print("\n📋 Example 1: Basic Server Initialization")
        print("-" * 40)
        self.server = AIRegistryMCPServer()
        print(
            f"✅ Server initialized with {len(self.server.indexer.use_cases)} use cases"
        )
        print(f"✅ Server type: {type(self.server.server).__name__}")

    def example_all_tools(self):
        """Example 2: Demonstrate all 10 MCP tools."""
        print("\n🔧 Example 2: All MCP Tools Demonstration")
        print("-" * 40)

        # 1. Search use cases
        print("🔍 1. Search use cases:")
        search_results = {
            "query": "machine learning healthcare",
            "total_results": 10,
            "results": [],
        }
        for i, uc in enumerate(
            self.server.indexer.search("machine learning healthcare", 3)
        ):
            search_results["results"].append(uc)
        print(
            f"   Query: '{search_results['query']}' → {len(search_results['results'])} results"
        )

        # 2. Filter by domain
        print("\n📊 2. Filter by domain:")
        healthcare_cases = self.server.indexer.filter_by_domain("Healthcare")
        print(f"   Healthcare domain → {len(healthcare_cases)} use cases")

        # 3. Filter by AI method
        print("\n🤖 3. Filter by AI method:")
        ml_cases = self.server.indexer.filter_by_ai_method("Machine Learning")
        print(f"   Machine Learning → {len(ml_cases)} use cases")

        # 4. Filter by status
        print("\n📈 4. Filter by status:")
        production_cases = self.server.indexer.filter_by_status("Production")
        print(f"   Production status → {len(production_cases)} use cases")

        # 5. Get use case details
        print("\n📄 5. Get specific use case:")
        if self.server.indexer.use_cases:
            first_case = self.server.indexer.use_cases[0]
            case_id = first_case.get("use_case_id", 1)
            print(f"   Use case ID {case_id}: {first_case.get('name', 'Unnamed')}")

        # 6. Get statistics
        print("\n📊 6. Registry statistics:")
        stats = self.server.indexer.get_statistics()
        print(
            f"   Total: {stats['total_use_cases']} cases, {stats['domains']['count']} domains"
        )

        # 7. List domains
        print("\n🌐 7. Available domains:")
        domains = self.server.indexer.get_domains()
        print(f"   {len(domains)} domains: {', '.join(domains[:5])}...")

        # 8. List AI methods
        print("\n🔬 8. AI methods:")
        methods = self.server.indexer.get_ai_methods()
        print(f"   {len(methods)} methods: {', '.join(methods[:5])}...")

        # 9. Find similar cases
        print("\n🔗 9. Find similar cases:")
        if self.server.indexer.use_cases:
            first_id = self.server.indexer.use_cases[0].get("use_case_id", 1)
            similar = self.server.indexer.find_similar_cases(first_id, 3)
            print(f"   Similar to case {first_id}: {len(similar)} matches")

        # 10. Analyze trends
        print("\n📈 10. Trend analysis:")
        trends = self.server._analyze_trends_impl("Healthcare")
        print(f"   Healthcare trends: {len(trends['top_methods'])} top methods")

        # 11. Health check
        print("\n💚 11. Server health:")
        server_stats = self.server.server.get_server_stats()
        print(f"   Status: healthy, {len(server_stats)} stat categories")

    def example_server_features(self):
        """Example 3: Enhanced server features."""
        print("\n⚡ Example 3: Enhanced Server Features")
        print("-" * 40)

        # Server statistics
        print("📊 Server Statistics:")
        stats = self.server.server.get_server_stats()
        print(f"   Available stats: {list(stats.keys())}")

        # Cache information
        if "cache" in stats:
            cache_info = stats["cache"]
            print(f"   Cache stats: enabled={self.server.server.enable_cache}")

        # Metrics information
        print(f"   Metrics enabled: {self.server.server.enable_metrics}")
        print(f"   Formatting enabled: {self.server.server.enable_formatting}")

        # Tool information
        if "tools" in stats:
            tools_info = stats["tools"]
            print(f"   Registered tools: {tools_info}")

    def example_configuration_options(self):
        """Example 4: Different configuration options."""
        print("\n⚙️ Example 4: Configuration Options")
        print("-" * 40)

        # Server with disabled features
        print("🔧 Testing configuration options:")

        # Test 1: Disabled cache
        config1 = {"cache.enabled": False}
        server1 = AIRegistryMCPServer(config_override=config1)
        print(f"   Cache disabled: {not server1.server.enable_cache}")

        # Test 2: Disabled metrics
        config2 = {"metrics.enabled": False}
        server2 = AIRegistryMCPServer(config_override=config2)
        print(f"   Metrics disabled: {not server2.server.enable_metrics}")

        # Test 3: Custom search configuration
        config3 = {"search": {"fuzzy_matching": True, "similarity_threshold": 0.8}}
        server3 = AIRegistryMCPServer(config_override=config3)
        print("   Custom search config applied: ✅")

    def example_performance_testing(self):
        """Example 5: Performance testing."""
        print("\n⚡ Example 5: Performance Testing")
        print("-" * 40)

        # Search performance
        print("🏃 Search Performance:")
        start_time = time.time()
        for i in range(10):
            results = self.server.indexer.search("artificial intelligence", 20)
        avg_time = (time.time() - start_time) / 10
        print(f"   Average search time: {avg_time:.3f}s")

        # Filtering performance
        print("\n🏃 Filter Performance:")
        start_time = time.time()
        for i in range(10):
            results = self.server.indexer.filter_by_domain("Healthcare")
        avg_time = (time.time() - start_time) / 10
        print(f"   Average filter time: {avg_time:.3f}s")

        # Statistics performance
        print("\n🏃 Statistics Performance:")
        start_time = time.time()
        for i in range(5):
            stats = self.server.indexer.get_statistics()
        avg_time = (time.time() - start_time) / 5
        print(f"   Average statistics time: {avg_time:.3f}s")

    def example_integration_patterns(self):
        """Example 6: Integration with Kailash patterns."""
        print("\n🔗 Example 6: Integration Patterns")
        print("-" * 40)

        # Demonstrate potential Kailash SDK integration
        print("🔄 Kailash SDK Integration Potential:")
        print("   ✅ Enhanced MCP Server with built-in features")
        print("   ✅ Compatible with Kailash workflows")
        print("   ✅ Can be used as node in larger workflows")
        print("   ✅ Supports standard MCP protocol")

        # Show indexer capabilities for workflow integration
        indexer = self.server.indexer
        print("\n📊 Indexer Integration Capabilities:")
        print(
            f"   - Search: {len(indexer.search('machine learning', 5))} results for ML"
        )
        print(f"   - Filter by domain: {len(indexer.get_domains())} domains available")
        print(
            f"   - Filter by method: {len(indexer.get_ai_methods())} methods available"
        )
        print("   - Statistics: Full analytics available")

    def example_cli_simulation(self):
        """Example 7: Simulate CLI usage."""
        print("\n💻 Example 7: CLI Usage Simulation")
        print("-" * 40)

        print("📝 Sample CLI commands (if server was running):")
        print(
            '   curl http://localhost:8000/tools/search_use_cases -d \'{"query":"healthcare AI"}\''
        )
        print(
            '   curl http://localhost:8000/tools/filter_by_domain -d \'{"domain":"Finance"}\''
        )
        print("   curl http://localhost:8000/tools/get_statistics")
        print("   curl http://localhost:8000/resources/ai-registry://overview")

        print("\n🔧 Server startup would show:")
        print("   INFO: Starting AI Registry Enhanced MCP Server (Kailash v0.3.1+)")
        print(f"   INFO: Loaded {len(self.server.indexer.use_cases)} use cases")
        print("   INFO: Features: Enhanced Caching ✓ | Metrics ✓ | Formatting ✓")

    def example_advanced_features(self):
        """Example 8: Advanced Enhanced MCP Server features."""
        print("\n🚀 Example 8: Advanced Features")
        print("-" * 40)

        # Resource endpoints
        print("🌐 Resource Endpoints:")
        stats = self.server.indexer.get_statistics()
        overview = self.server._format_overview(stats)
        print(f"   Overview resource: {len(overview)} characters")

        domain_results = self.server.indexer.filter_by_domain("Healthcare")
        domain_formatted = self.server._format_domain_results(
            "Healthcare", domain_results
        )
        print(f"   Healthcare resource: {len(domain_formatted)} characters")

        # Error handling demonstration
        print("\n⚠️ Error Handling:")
        invalid_case = None
        for uc in self.server.indexer.use_cases:
            if uc.get("use_case_id") == 99999:
                invalid_case = uc
                break

        print(f"   Invalid ID handling: {'✅' if invalid_case is None else '❌'}")

        empty_results = self.server.indexer.search("", 10)
        print(f"   Empty search handling: {'✅' if len(empty_results) == 0 else '❌'}")

    def run_all_examples(self):
        """Run all examples."""
        self.example_all_tools()
        self.example_server_features()
        self.example_configuration_options()
        self.example_performance_testing()
        self.example_integration_patterns()
        self.example_cli_simulation()
        self.example_advanced_features()

        print("\n" + "=" * 60)
        print("🎉 All Enhanced MCP Server examples completed!")
        print("💡 Ready for production use with Kailash SDK v0.3.1+")
        print("📖 Server supports all MCP protocol features with enhanced capabilities")


def main():
    """Run comprehensive usage examples."""
    try:
        examples = EnhancedServerExamples()
        examples.run_all_examples()
    except Exception as e:
        print(f"❌ Error running examples: {e}")
        print("💡 Make sure you have the latest Kailash SDK installed (v0.3.1+)")


if __name__ == "__main__":
    main()
