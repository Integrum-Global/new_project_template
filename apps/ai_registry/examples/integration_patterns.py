"""
Integration pattern examples for AI Registry.

This module demonstrates various ways to integrate the AI Registry
with other systems, workflows, and applications.
"""

import json
from pathlib import Path
from typing import Any, Callable, Dict, Optional

from kailash import Workflow
from kailash.nodes.ai import LLMAgentNode
from kailash.nodes.api import HTTPRequestNode
from kailash.nodes.data import JSONReaderNode, JSONWriterNode
from kailash.runtime.local import LocalRuntime

from ..nodes import RegistryAnalyticsNode, RegistrySearchNode
from ..workflows import execute_domain_overview, execute_simple_search


class RegistryIntegrationPatterns:
    """Collection of integration pattern examples."""

    def __init__(self):
        """Initialize integration patterns."""
        self.runtime = LocalRuntime()

    def create_data_pipeline_workflow(self) -> Workflow:
        """
        Create a data pipeline that enriches existing data with AI Registry insights.

        This pattern shows how to integrate AI Registry data into existing
        data processing workflows.
        """
        workflow = Workflow("registry_data_pipeline", "AI Registry Data Pipeline")

        # Read input data (e.g., list of companies or projects)
        workflow.add_node("data_reader", JSONReaderNode(name="input_reader"))

        # Search registry for relevant use cases
        workflow.add_node(
            "registry_search", RegistrySearchNode(name="registry_enrichment")
        )

        # Enrich data with registry insights
        workflow.add_node("enrichment_agent", LLMAgentNode(name="data_enricher"))

        # Write enriched data
        workflow.add_node("data_writer", JSONWriterNode(name="output_writer"))

        # Connect pipeline
        workflow.connect("data_reader", "enrichment_agent")
        workflow.connect("registry_search", "enrichment_agent")
        workflow.connect("enrichment_agent", "data_writer")

        return workflow

    def create_api_integration_workflow(self) -> Workflow:
        """
        Create a workflow that integrates AI Registry with external APIs.

        This pattern shows how to combine AI Registry data with
        external data sources for comprehensive analysis.
        """
        workflow = Workflow("registry_api_integration", "Registry API Integration")

        # Get registry data
        workflow.add_node(
            "registry_analytics", RegistryAnalyticsNode(name="registry_data")
        )

        # Call external API for additional context
        workflow.add_node("external_api", HTTPRequestNode(name="market_data_api"))

        # Combine and analyze data
        workflow.add_node("integration_agent", LLMAgentNode(name="data_integrator"))

        # Connect workflow
        workflow.connect("registry_analytics", "integration_agent")
        workflow.connect("external_api", "integration_agent")

        return workflow

    def create_report_generation_workflow(self) -> Workflow:
        """
        Create a workflow for automated report generation.

        This pattern shows how to create automated reports
        combining AI Registry data with analysis and insights.
        """
        workflow = Workflow("registry_report_generation", "Automated Report Generation")

        # Get overview statistics
        workflow.add_node("overview_analytics", RegistryAnalyticsNode(name="overview"))

        # Get domain-specific insights
        workflow.add_node(
            "domain_analytics", RegistryAnalyticsNode(name="domain_focus")
        )

        # Generate report with AI
        workflow.add_node("report_generator", LLMAgentNode(name="report_writer"))

        # Save report
        workflow.add_node("report_saver", JSONWriterNode(name="report_output"))

        # Connect workflow
        workflow.connect("overview_analytics", "report_generator")
        workflow.connect("domain_analytics", "report_generator")
        workflow.connect("report_generator", "report_saver")

        return workflow

    def demonstrate_webhook_integration(self) -> Dict[str, Any]:
        """
        Demonstrate how to integrate with webhook systems.

        This shows how the AI Registry could respond to external
        events and provide contextual AI insights.
        """
        print("🔗 Webhook Integration Pattern")
        print("=" * 40)

        # Simulated webhook payload
        webhook_payload = {
            "event": "new_project_proposal",
            "data": {
                "project_name": "Smart Healthcare Assistant",
                "domain": "Healthcare",
                "proposed_methods": ["Natural Language Processing", "Machine Learning"],
                "objectives": [
                    "Improve patient communication",
                    "Automate routine tasks",
                ],
            },
        }

        print(f"📨 Received webhook: {webhook_payload['event']}")
        print(f"Project: {webhook_payload['data']['project_name']}")

        # Process webhook with registry insights
        try:
            # Search for similar projects
            similar_results = execute_simple_search(
                query=" ".join(webhook_payload["data"]["proposed_methods"]),
                filters={"domain": webhook_payload["data"]["domain"]},
                limit=5,
            )

            response = {
                "webhook_id": "webhook_123",
                "processed_at": "2024-01-01T12:00:00Z",
                "insights": {
                    "similar_projects": similar_results.get("count", 0),
                    "domain_maturity": (
                        "high" if similar_results.get("count", 0) > 10 else "low"
                    ),
                    "recommendations": [
                        "Review similar implementations before starting",
                        "Consider production-ready examples for guidance",
                        "Identify common challenges to prepare for",
                    ],
                },
                "related_use_cases": [
                    {
                        "id": uc.get("use_case_id"),
                        "name": uc.get("name"),
                        "status": uc.get("status"),
                    }
                    for uc in similar_results.get("results", [])[:3]
                ],
            }

            print("✅ Processed successfully")
            print(f"Found {response['insights']['similar_projects']} similar projects")
            print(f"Domain maturity: {response['insights']['domain_maturity']}")

            return response

        except Exception as e:
            print(f"❌ Error processing webhook: {e}")
            return {"error": str(e)}

    def demonstrate_batch_processing(self) -> Dict[str, Any]:
        """
        Demonstrate batch processing of multiple queries.

        This shows how to efficiently process large volumes
        of registry queries.
        """
        print("\n📦 Batch Processing Pattern")
        print("=" * 40)

        # Batch of queries to process
        batch_queries = [
            {"type": "search", "query": "machine learning healthcare", "limit": 5},
            {
                "type": "search",
                "query": "natural language processing finance",
                "limit": 5,
            },
            {"type": "domain_filter", "domain": "Manufacturing"},
            {"type": "statistics", "analysis_type": "overview"},
            {"type": "search", "query": "computer vision transportation", "limit": 3},
        ]

        print(f"Processing batch of {len(batch_queries)} queries...")

        results = []

        for i, query in enumerate(batch_queries):
            print(f"Processing query {i+1}/{len(batch_queries)}: {query['type']}")

            try:
                if query["type"] == "search":
                    result = execute_simple_search(
                        query=query["query"], limit=query.get("limit", 10)
                    )
                elif query["type"] == "domain_filter":
                    result = execute_simple_search(
                        query="", filters={"domain": query["domain"]}
                    )
                elif query["type"] == "statistics":
                    result = execute_domain_overview()
                else:
                    result = {"error": f"Unknown query type: {query['type']}"}

                results.append(
                    {
                        "query": query,
                        "result": result,
                        "status": "success" if result.get("success", True) else "error",
                    }
                )

            except Exception as e:
                results.append({"query": query, "error": str(e), "status": "error"})

        # Summary
        successful = sum(1 for r in results if r["status"] == "success")
        print(f"✅ Batch complete: {successful}/{len(batch_queries)} successful")

        return {
            "batch_size": len(batch_queries),
            "successful": successful,
            "results": results,
        }

    def demonstrate_streaming_integration(self) -> Dict[str, Any]:
        """
        Demonstrate streaming data integration pattern.

        This shows how to handle real-time data streams
        that need AI Registry context.
        """
        print("\n🌊 Streaming Integration Pattern")
        print("=" * 40)

        # Simulated data stream
        data_stream = [
            {
                "timestamp": "2024-01-01T10:00:00Z",
                "event": "ai_project_started",
                "domain": "Healthcare",
            },
            {
                "timestamp": "2024-01-01T10:01:00Z",
                "event": "technology_inquiry",
                "method": "Deep Learning",
            },
            {
                "timestamp": "2024-01-01T10:02:00Z",
                "event": "competitor_analysis",
                "domain": "Finance",
            },
            {
                "timestamp": "2024-01-01T10:03:00Z",
                "event": "implementation_challenge",
                "challenge": "data privacy",
            },
            {
                "timestamp": "2024-01-01T10:04:00Z",
                "event": "success_story_needed",
                "domain": "Manufacturing",
            },
        ]

        print(f"Processing stream of {len(data_stream)} events...")

        processed_events = []

        for event in data_stream:
            print(f"📊 Processing: {event['event']} at {event['timestamp']}")

            # Process each event type with appropriate registry query
            try:
                if event["event"] == "ai_project_started":
                    context = execute_simple_search(
                        query="", filters={"domain": event["domain"]}, limit=3
                    )
                    insight = f"Found {context.get('count', 0)} similar projects in {event['domain']}"

                elif event["event"] == "technology_inquiry":
                    context = execute_simple_search(query=event["method"], limit=5)
                    insight = f"{event['method']} is used in {context.get('count', 0)} documented use cases"

                elif event["event"] == "competitor_analysis":
                    context = execute_domain_overview()
                    domain_stats = context.get("basic_stats", {}).get(
                        "domain_distribution", {}
                    )
                    count = domain_stats.get(event["domain"], 0)
                    insight = (
                        f"{event['domain']} has {count} documented AI implementations"
                    )

                elif event["event"] == "implementation_challenge":
                    context = execute_simple_search(query=event["challenge"], limit=10)
                    insight = f"Found {context.get('count', 0)} use cases mentioning '{event['challenge']}'"

                elif event["event"] == "success_story_needed":
                    context = execute_simple_search(
                        query="",
                        filters={"domain": event["domain"], "status": "Production"},
                        limit=5,
                    )
                    insight = f"Found {context.get('count', 0)} production success stories in {event['domain']}"

                else:
                    insight = "Event type not recognized"
                    context = {}

                processed_events.append(
                    {
                        "original_event": event,
                        "insight": insight,
                        "context_found": bool(context.get("results")),
                    }
                )

                print(f"   💡 {insight}")

            except Exception as e:
                processed_events.append({"original_event": event, "error": str(e)})
                print(f"   ❌ Error: {e}")

        print("✅ Stream processing complete")

        return {
            "events_processed": len(data_stream),
            "successful_enrichments": sum(
                1 for e in processed_events if "insight" in e
            ),
            "events": processed_events,
        }

    def demonstrate_caching_strategy(self) -> Dict[str, Any]:
        """
        Demonstrate caching strategies for performance optimization.

        This shows how to implement caching for frequently
        accessed registry data.
        """
        print("\n🗄️  Caching Strategy Pattern")
        print("=" * 40)

        # Simulated cache
        cache = {}
        cache_hits = 0
        cache_misses = 0

        def cached_search(query: str, filters: Optional[Dict] = None) -> Dict[str, Any]:
            nonlocal cache_hits, cache_misses

            # Create cache key
            cache_key = f"{query}_{json.dumps(filters or {}, sort_keys=True)}"

            if cache_key in cache:
                cache_hits += 1
                print(f"🎯 Cache HIT for: {query[:30]}...")
                return cache[cache_key]
            else:
                cache_misses += 1
                print(f"⏳ Cache MISS for: {query[:30]}...")

                # Execute query
                result = execute_simple_search(query=query, filters=filters or {})

                # Cache result
                cache[cache_key] = result
                return result

        # Simulate repeated queries (some duplicates)
        queries = [
            ("machine learning healthcare", {"domain": "Healthcare"}),
            ("natural language processing", {}),
            ("machine learning healthcare", {"domain": "Healthcare"}),  # Duplicate
            ("computer vision", {}),
            ("natural language processing", {}),  # Duplicate
            ("deep learning finance", {"domain": "Finance"}),
            ("machine learning healthcare", {"domain": "Healthcare"}),  # Duplicate
        ]

        print(f"Executing {len(queries)} queries with caching...")

        results = []
        for query, filters in queries:
            result = cached_search(query, filters)
            results.append(result)

        hit_rate = (
            cache_hits / (cache_hits + cache_misses)
            if (cache_hits + cache_misses) > 0
            else 0
        )

        print("📊 Cache Performance:")
        print(f"   Hits: {cache_hits}")
        print(f"   Misses: {cache_misses}")
        print(f"   Hit Rate: {hit_rate:.1%}")
        print(f"   Cache Size: {len(cache)} entries")

        return {
            "total_queries": len(queries),
            "cache_hits": cache_hits,
            "cache_misses": cache_misses,
            "hit_rate": hit_rate,
            "cache_size": len(cache),
        }

    def demonstrate_error_handling(self) -> Dict[str, Any]:
        """
        Demonstrate robust error handling patterns.

        This shows how to handle various error conditions
        gracefully in registry integrations.
        """
        print("\n🛡️  Error Handling Pattern")
        print("=" * 40)

        def robust_registry_call(
            operation: Callable, fallback_value: Any = None, max_retries: int = 3
        ) -> Dict[str, Any]:
            """Execute registry operation with error handling and retries."""

            for attempt in range(max_retries):
                try:
                    result = operation()
                    return {"success": True, "result": result, "attempts": attempt + 1}

                except ConnectionError as e:
                    print(f"🔄 Connection error on attempt {attempt + 1}: {e}")
                    if attempt == max_retries - 1:
                        return {
                            "success": False,
                            "error": "Connection failed",
                            "fallback": fallback_value,
                        }

                except TimeoutError as e:
                    print(f"⏰ Timeout on attempt {attempt + 1}: {e}")
                    if attempt == max_retries - 1:
                        return {
                            "success": False,
                            "error": "Request timeout",
                            "fallback": fallback_value,
                        }

                except Exception as e:
                    print(f"❌ Unexpected error on attempt {attempt + 1}: {e}")
                    return {
                        "success": False,
                        "error": str(e),
                        "fallback": fallback_value,
                    }

            return {
                "success": False,
                "error": "Max retries exceeded",
                "fallback": fallback_value,
            }

        # Test different error scenarios
        scenarios = [
            {
                "name": "Normal Operation",
                "operation": lambda: execute_simple_search("healthcare AI", limit=3),
                "fallback": {"count": 0, "results": []},
            },
            {
                "name": "Invalid Query",
                "operation": lambda: execute_simple_search(
                    "", limit=-1
                ),  # Invalid limit
                "fallback": {"count": 0, "results": []},
            },
            {
                "name": "Complex Query",
                "operation": lambda: execute_simple_search(
                    "machine learning healthcare NLP", limit=5
                ),
                "fallback": {"count": 0, "results": []},
            },
        ]

        results = []

        for scenario in scenarios:
            print(f"\nTesting: {scenario['name']}")

            result = robust_registry_call(scenario["operation"], scenario["fallback"])

            if result["success"]:
                print(f"✅ Success in {result['attempts']} attempt(s)")
            else:
                print(f"❌ Failed: {result['error']}")
                print("🔄 Using fallback value")

            results.append({"scenario": scenario["name"], "result": result})

        success_rate = sum(1 for r in results if r["result"]["success"]) / len(results)
        print(f"\n📊 Overall success rate: {success_rate:.1%}")

        return {
            "scenarios_tested": len(scenarios),
            "success_rate": success_rate,
            "results": results,
        }


def run_integration_examples() -> Dict[str, Any]:
    """
    Run all integration pattern examples.

    Returns:
        Results from all integration demonstrations
    """
    print("🔗 AI Registry Integration Patterns")
    print("=" * 60)

    patterns = RegistryIntegrationPatterns()
    results = {}

    try:
        # Webhook integration
        results["webhook"] = patterns.demonstrate_webhook_integration()

        # Batch processing
        results["batch_processing"] = patterns.demonstrate_batch_processing()

        # Streaming integration
        results["streaming"] = patterns.demonstrate_streaming_integration()

        # Caching strategy
        results["caching"] = patterns.demonstrate_caching_strategy()

        # Error handling
        results["error_handling"] = patterns.demonstrate_error_handling()

        print("\n" + "=" * 60)
        print("🎉 All integration pattern demonstrations complete!")

        # Summary
        print("\n📋 Integration Patterns Summary:")
        print("- Webhook: Real-time event processing with AI insights")
        print("- Batch: Efficient processing of multiple queries")
        print("- Streaming: Real-time data enrichment")
        print("- Caching: Performance optimization strategies")
        print("- Error Handling: Robust failure management")

    except Exception as e:
        print(f"\n❌ Error running integration examples: {e}")
        results["error"] = str(e)

    return results


def save_integration_examples(
    results: Dict[str, Any], output_dir: str = "integration_outputs"
):
    """
    Save integration example outputs for inspection.

    Args:
        results: Results from integration examples
        output_dir: Directory to save outputs
    """
    output_path = Path(output_dir)
    output_path.mkdir(exist_ok=True)

    for pattern_name, pattern_results in results.items():
        if pattern_name != "error":
            filename = output_path / f"{pattern_name}_example.json"

            try:
                with open(filename, "w") as f:
                    json.dump(pattern_results, f, indent=2, default=str)
                print(f"💾 Saved {pattern_name} results to {filename}")
            except Exception as e:
                print(f"❌ Error saving {pattern_name}: {e}")


# Main execution
if __name__ == "__main__":
    # Run integration pattern demonstrations
    results = run_integration_examples()

    # Save results for inspection
    save_integration_examples(results)

    print("\n🎯 Key Integration Takeaways:")
    print("- Registry data can be seamlessly integrated into existing workflows")
    print("- Multiple integration patterns support different use cases")
    print("- Caching and error handling ensure robust production deployment")
    print("- Real-time and batch processing patterns provide flexibility")
    print("- The registry acts as a knowledge layer for AI-powered applications")
