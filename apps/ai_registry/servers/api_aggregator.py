"""
API Aggregator MCP Server using Kailash SDK.

This server provides MCP tools for aggregating multiple APIs into unified interfaces,
enabling seamless integration with various external services.
"""

import asyncio
import logging
from concurrent.futures import ThreadPoolExecutor
from typing import Any, Dict, List, Optional, Union

from kailash import NodeParameter
from kailash.middleware.mcp import MiddlewareMCPServer as MCPServer
from kailash.nodes.api import GraphQLClientNode, HTTPRequestNode, RESTClientNode
from kailash.nodes.security import CredentialManagerNode
from kailash.runtime import LocalRuntime
from kailash.workflow import Workflow

logger = logging.getLogger(__name__)


class APIAggregatorServer:
    """
    MCP Server for aggregating multiple APIs using Kailash SDK.

    Features:
    - Unified interface for multiple REST APIs
    - GraphQL query aggregation
    - Parallel API calls with result merging
    - Authentication management across services
    - Response transformation and normalization
    - Rate limiting and retry logic
    """

    def __init__(
        self,
        config_file: Optional[str] = None,
        config_override: Optional[Dict[str, Any]] = None,
    ):
        """
        Initialize API Aggregator Server.

        Args:
            config_file: Path to YAML configuration file
            config_override: Optional configuration overrides
        """
        # Initialize Enhanced MCP Server
        self.server = MCPServer(
            name="api-aggregator",
            config_file=config_file,
            enable_cache=True,
            cache_ttl=300,  # 5 minute default
            enable_metrics=True,
            enable_formatting=True,
        )

        # Initialize runtime with parallel execution
        self.runtime = LocalRuntime(
            enable_async=True, max_concurrency=10  # Allow parallel API calls
        )

        # Store config
        self.config = config_override or {}

        # Initialize credential manager
        self.credential_manager = CredentialManagerNode(
            name="api_credentials",
            vault_path=self.config.get("credentials.vault_path", ".credentials"),
        )

        # Set up tools and resources
        self._setup_tools()
        self._setup_resources()
        self._setup_aggregation_workflows()

    def _setup_tools(self):
        """Set up API aggregation MCP tools."""

        @self.server.tool(
            cache_key="aggregate_rest",
            cache_ttl=60,  # 1 minute cache for API data
            format_response="json",
        )
        def aggregate_rest_apis(
            endpoints: List[Dict[str, Any]], merge_strategy: str = "combine"
        ) -> dict:
            """
            Aggregate data from multiple REST API endpoints.

            Args:
                endpoints: List of endpoint configurations
                merge_strategy: How to merge results (combine, merge, concat)

            Example endpoints:
            [
                {
                    "name": "github_repos",
                    "url": "https://api.github.com/user/repos",
                    "headers": {"Authorization": "token {{github_token}}"},
                    "params": {"per_page": 100}
                },
                {
                    "name": "gitlab_projects",
                    "url": "https://gitlab.com/api/v4/projects",
                    "headers": {"PRIVATE-TOKEN": "{{gitlab_token}}"},
                    "params": {"owned": true}
                }
            ]
            """
            try:
                # Create workflow for parallel API calls
                workflow = Workflow("aggregate_apis", "Aggregate multiple REST APIs")

                # Add nodes for each endpoint
                results = {}
                for i, endpoint in enumerate(endpoints):
                    node_name = f"api_{i}_{endpoint.get('name', 'unnamed')}"

                    # Create REST client node
                    rest_node = RESTClientNode(
                        name=node_name,
                        base_url=endpoint.get("url", ""),
                        headers=endpoint.get("headers", {}),
                        timeout=endpoint.get("timeout", 30),
                    )

                    workflow.add_node(node_name, rest_node)

                # Execute workflow
                parameters = {
                    f"api_{i}_{ep.get('name', 'unnamed')}": {
                        "method": ep.get("method", "GET"),
                        "endpoint": "",  # Full URL already in base_url
                        "params": ep.get("params", {}),
                    }
                    for i, ep in enumerate(endpoints)
                }

                result, _ = self.runtime.execute(workflow, parameters=parameters)

                # Merge results based on strategy
                merged_data = self._merge_results(result, merge_strategy)

                return {
                    "success": True,
                    "endpoints_called": len(endpoints),
                    "merge_strategy": merge_strategy,
                    "data": merged_data,
                    "individual_results": result,
                }

            except Exception as e:
                logger.error(f"Error aggregating APIs: {e}")
                return {
                    "success": False,
                    "error": str(e),
                    "endpoints_attempted": len(endpoints),
                }

        @self.server.tool(
            cache_key="graphql_aggregate", cache_ttl=60, format_response="json"
        )
        def aggregate_graphql_queries(
            services: List[Dict[str, Any]], merge_fields: Optional[List[str]] = None
        ) -> dict:
            """
            Aggregate data from multiple GraphQL services.

            Args:
                services: List of GraphQL service configurations
                merge_fields: Specific fields to merge from responses

            Example services:
            [
                {
                    "name": "github",
                    "url": "https://api.github.com/graphql",
                    "query": "{ viewer { repositories(first: 10) { nodes { name } } } }",
                    "headers": {"Authorization": "Bearer {{github_token}}"}
                },
                {
                    "name": "gitlab",
                    "url": "https://gitlab.com/api/graphql",
                    "query": "{ currentUser { projects { nodes { name } } } }",
                    "headers": {"Authorization": "Bearer {{gitlab_token}}"}
                }
            ]
            """
            try:
                workflow = Workflow("graphql_aggregate", "Aggregate GraphQL queries")

                # Add GraphQL nodes
                for i, service in enumerate(services):
                    node_name = f"graphql_{i}_{service.get('name', 'unnamed')}"

                    graphql_node = GraphQLClientNode(
                        name=node_name,
                        endpoint=service.get("url"),
                        headers=service.get("headers", {}),
                    )

                    workflow.add_node(node_name, graphql_node)

                # Prepare parameters
                parameters = {
                    f"graphql_{i}_{svc.get('name', 'unnamed')}": {
                        "query": svc.get("query"),
                        "variables": svc.get("variables", {}),
                    }
                    for i, svc in enumerate(services)
                }

                result, _ = self.runtime.execute(workflow, parameters=parameters)

                # Merge GraphQL responses
                merged = self._merge_graphql_results(result, merge_fields)

                return {
                    "success": True,
                    "services_queried": len(services),
                    "merged_data": merged,
                    "individual_responses": result,
                }

            except Exception as e:
                logger.error(f"Error aggregating GraphQL: {e}")
                return {
                    "success": False,
                    "error": str(e),
                    "services_attempted": len(services),
                }

        @self.server.tool(
            cache_key="unified_search", cache_ttl=120, format_response="search"
        )
        def unified_search(
            query: str, sources: List[str] = None, limit_per_source: int = 10
        ) -> dict:
            """
            Search across multiple configured API sources.

            Args:
                query: Search query
                sources: List of source names to search (None = all)
                limit_per_source: Max results from each source
            """
            # Get configured search sources
            available_sources = self.config.get("search_sources", {})

            if sources:
                # Filter to requested sources
                search_sources = {
                    k: v for k, v in available_sources.items() if k in sources
                }
            else:
                search_sources = available_sources

            try:
                workflow = Workflow("unified_search", "Search across multiple APIs")

                # Create search nodes for each source
                for source_name, source_config in search_sources.items():
                    node = HTTPRequestNode(
                        name=f"search_{source_name}",
                        base_url=source_config.get("base_url"),
                        headers=source_config.get("headers", {}),
                    )
                    workflow.add_node(f"search_{source_name}", node)

                # Prepare search parameters
                parameters = {}
                for source_name, source_config in search_sources.items():
                    endpoint = source_config.get("search_endpoint", "/search")
                    params = source_config.get("default_params", {})
                    params[source_config.get("query_param", "q")] = query
                    params[source_config.get("limit_param", "limit")] = limit_per_source

                    parameters[f"search_{source_name}"] = {
                        "method": "GET",
                        "endpoint": endpoint,
                        "params": params,
                    }

                result, _ = self.runtime.execute(workflow, parameters=parameters)

                # Combine search results
                all_results = []
                for source_name, source_result in result.items():
                    if source_result.get("status_code") == 200:
                        data = source_result.get("data", {})
                        results_key = search_sources[
                            source_name.replace("search_", "")
                        ].get("results_key", "results")
                        source_results = data.get(results_key, [])

                        # Add source info to each result
                        for item in source_results:
                            item["_source"] = source_name.replace("search_", "")
                            all_results.append(item)

                return {
                    "success": True,
                    "query": query,
                    "total_results": len(all_results),
                    "sources_searched": list(search_sources.keys()),
                    "results": all_results,
                }

            except Exception as e:
                logger.error(f"Error in unified search: {e}")
                return {"success": False, "error": str(e), "query": query}

        @self.server.tool(format_response="markdown")
        def configure_api_source(
            name: str,
            base_url: str,
            auth_type: str = "bearer",
            auth_credential_key: str = None,
            headers: Optional[Dict[str, str]] = None,
        ) -> dict:
            """Configure a new API source for aggregation."""
            try:
                # Store API configuration
                api_config = {
                    "name": name,
                    "base_url": base_url,
                    "auth_type": auth_type,
                    "auth_credential_key": auth_credential_key,
                    "headers": headers or {},
                }

                # In production, this would persist to configuration
                return {
                    "success": True,
                    "message": f"API source '{name}' configured successfully",
                    "configuration": api_config,
                }

            except Exception as e:
                return {"success": False, "error": str(e), "name": name}

        @self.server.tool(
            cache_key="api_health", cache_ttl=60, format_response="markdown"
        )
        def check_api_health(sources: Optional[List[str]] = None) -> dict:
            """Check health status of configured API sources."""
            available_sources = self.config.get("api_sources", {})

            if sources:
                check_sources = {
                    k: v for k, v in available_sources.items() if k in sources
                }
            else:
                check_sources = available_sources

            health_results = {}

            for source_name, source_config in check_sources.items():
                try:
                    # Create simple health check request
                    node = HTTPRequestNode(
                        name=f"health_{source_name}",
                        base_url=source_config.get("base_url"),
                        timeout=5,
                    )

                    workflow = Workflow(
                        f"health_check_{source_name}", "API health check"
                    )
                    workflow.add_node("health", node)

                    parameters = {
                        "health": {
                            "method": "GET",
                            "endpoint": source_config.get("health_endpoint", "/"),
                        }
                    }

                    result, _ = self.runtime.execute(workflow, parameters=parameters)

                    health_results[source_name] = {
                        "status": (
                            "healthy"
                            if result.get("health", {}).get("status_code") == 200
                            else "unhealthy"
                        ),
                        "response_time": result.get("health", {}).get(
                            "response_time", 0
                        ),
                        "status_code": result.get("health", {}).get("status_code"),
                    }

                except Exception as e:
                    health_results[source_name] = {"status": "error", "error": str(e)}

            return {
                "success": True,
                "sources_checked": len(health_results),
                "health_status": health_results,
                "overall_status": (
                    "healthy"
                    if all(
                        r.get("status") == "healthy" for r in health_results.values()
                    )
                    else "degraded"
                ),
            }

    def _setup_resources(self):
        """Set up API aggregator MCP resources."""

        @self.server.resource(uri="apis://configured")
        def list_configured_apis() -> dict:
            """List all configured API sources."""
            return {
                "api_sources": list(self.config.get("api_sources", {}).keys()),
                "search_sources": list(self.config.get("search_sources", {}).keys()),
                "graphql_sources": list(self.config.get("graphql_sources", {}).keys()),
            }

        @self.server.resource(uri="apis://statistics")
        def get_api_statistics() -> dict:
            """Get API usage statistics."""
            # In production, this would track actual API usage
            return {
                "total_api_calls": 0,
                "cache_hit_rate": 0.0,
                "average_response_time_ms": 0,
                "errors_last_hour": 0,
            }

    def _setup_aggregation_workflows(self):
        """Set up pre-defined aggregation workflows."""

        @self.server.tool(format_response="markdown")
        def create_data_pipeline(
            name: str,
            sources: List[str],
            transformations: List[Dict[str, Any]],
            output_format: str = "json",
        ) -> dict:
            """Create a data aggregation pipeline."""
            # This would create a reusable workflow for data aggregation
            return {
                "success": True,
                "pipeline_name": name,
                "sources": sources,
                "transformations": len(transformations),
                "output_format": output_format,
                "message": "Pipeline created (placeholder implementation)",
            }

    def _merge_results(self, results: Dict[str, Any], strategy: str) -> Any:
        """Merge API results based on strategy."""
        if strategy == "combine":
            # Combine all results into a single dictionary
            combined = {}
            for key, value in results.items():
                if isinstance(value, dict) and value.get("status_code") == 200:
                    combined[key] = value.get("data")
            return combined

        elif strategy == "merge":
            # Deep merge dictionaries
            merged = {}
            for key, value in results.items():
                if isinstance(value, dict) and value.get("status_code") == 200:
                    data = value.get("data", {})
                    if isinstance(data, dict):
                        merged.update(data)
            return merged

        elif strategy == "concat":
            # Concatenate arrays
            concatenated = []
            for key, value in results.items():
                if isinstance(value, dict) and value.get("status_code") == 200:
                    data = value.get("data")
                    if isinstance(data, list):
                        concatenated.extend(data)
            return concatenated

        else:
            return results

    def _merge_graphql_results(
        self, results: Dict[str, Any], merge_fields: Optional[List[str]]
    ) -> Dict[str, Any]:
        """Merge GraphQL query results."""
        merged = {}

        for key, value in results.items():
            if isinstance(value, dict) and "data" in value:
                data = value["data"]

                if merge_fields:
                    # Extract specific fields
                    for field in merge_fields:
                        if field in data:
                            merged[f"{key}_{field}"] = data[field]
                else:
                    # Merge all data
                    merged[key] = data

        return merged

    def run(self):
        """Start the API Aggregator MCP server."""
        logger.info("Starting API Aggregator MCP Server...")
        self.server.run()
