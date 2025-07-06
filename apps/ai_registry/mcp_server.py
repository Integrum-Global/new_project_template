"""
AI Registry Enhanced MCP Server using Kailash SDK.

This server uses the true Enhanced MCP Server from Kailash SDK v0.3.1+
with built-in caching, metrics, and formatting capabilities.
"""

import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional

from kailash.middleware.mcp import MiddlewareMCPServer as MCPServer

from .indexer import RegistryIndexer

logger = logging.getLogger(__name__)


class AIRegistryMCPServer:
    """
    AI Registry MCP Server using Kailash Enhanced MCP Server.

    This implementation uses the real Enhanced MCP Server from the SDK,
    eliminating the need for custom caching, metrics, and formatting code.
    """

    def __init__(
        self,
        config_file: Optional[str] = None,
        config_override: Optional[Dict[str, Any]] = None,
    ):
        """
        Initialize the AI Registry MCP server.

        Args:
            config_file: Path to YAML configuration file
            config_override: Optional configuration overrides
        """
        # Default config file path
        if not config_file:
            config_file = Path(__file__).parent / "data" / "server_config.yaml"

        # Initialize Enhanced MCP Server with all features enabled
        self.server = MCPServer(
            name="ai-registry",
            config_file=config_file if Path(config_file).exists() else None,
            enable_cache=True,
            cache_ttl=300,  # 5 minute default
            enable_metrics=True,
            enable_formatting=True,
        )

        # Apply config overrides if provided
        if config_override:
            # Apply overrides to disable features if requested
            if config_override.get("cache.enabled") is False:
                self.server.enable_cache = False
            if config_override.get("metrics.enabled") is False:
                self.server.enable_metrics = False
            if config_override.get("formatting.enabled") is False:
                self.server.enable_formatting = False

        # Initialize indexer with search configuration
        search_config = config_override.get("search", {}) if config_override else {}
        self.indexer = RegistryIndexer(search_config)

        # Load registry data
        registry_file = (
            config_override.get("registry.file") if config_override else None
        )
        if not registry_file:
            registry_file = Path(__file__).parent / "data" / "combined_ai_registry.json"

        logger.info(f"Loading AI Registry from {registry_file}")
        self.indexer.load_and_index(str(registry_file))

        # Set up all tool handlers
        self._setup_tools()
        self._setup_resources()

    def _setup_tools(self):
        """Set up all MCP tools with Enhanced server features."""

        # Search tool with caching and search formatting
        @self.server.tool(
            cache_key="search",
            cache_ttl=300,  # 5 minute cache
            format_response="search",
        )
        def search_use_cases(query: str, limit: int = 20) -> dict:
            """Search AI use cases with full-text search."""
            results = self.indexer.search(query, limit)
            return {"query": query, "total_results": len(results), "results": results}

        # Domain filter with longer cache
        @self.server.tool(
            cache_key="domain",
            cache_ttl=1800,  # 30 minute cache
            format_response="markdown",
        )
        def filter_by_domain(domain: str) -> dict:
            """Filter use cases by application domain."""
            results = self.indexer.filter_by_domain(domain)
            return {
                "domain": domain,
                "count": len(results),
                "use_cases": results,
                "available_domains": (
                    self.indexer.get_domains() if not results else None
                ),
            }

        # AI method filter
        @self.server.tool(
            cache_key="ai_method", cache_ttl=1800, format_response="markdown"
        )
        def filter_by_ai_method(method: str) -> dict:
            """Filter use cases by AI method."""
            results = self.indexer.filter_by_ai_method(method)
            return {
                "method": method,
                "count": len(results),
                "use_cases": results,
                "available_methods": (
                    self.indexer.get_ai_methods()[:10] if not results else None
                ),
            }

        # Status filter
        @self.server.tool(
            cache_key="status", cache_ttl=1800, format_response="markdown"
        )
        def filter_by_status(status: str) -> dict:
            """Filter use cases by implementation status."""
            results = self.indexer.filter_by_status(status)
            return {
                "status": status,
                "count": len(results),
                "use_cases": results,
                "available_statuses": (
                    self.indexer.get_statuses() if not results else None
                ),
            }

        # Get specific use case
        @self.server.tool(format_response="markdown")
        def get_use_case_details(use_case_id: int) -> dict:
            """Get detailed information about a specific use case."""
            # Find use case by ID
            use_case = None
            for uc in self.indexer.use_cases:
                if uc.get("use_case_id") == use_case_id:
                    use_case = uc
                    break

            if use_case:
                return {"found": True, "use_case": use_case}

            return {
                "found": False,
                "error": f"Use case with ID {use_case_id} not found",
                "total_use_cases": len(self.indexer.use_cases),
            }

        # Statistics with moderate caching
        @self.server.tool(
            cache_key="statistics",
            cache_ttl=600,  # 10 minute cache
            format_response="markdown",
        )
        def get_statistics() -> dict:
            """Get comprehensive registry statistics."""
            stats = self.indexer.get_statistics()
            return {
                "registry_statistics": stats,
                "summary": {
                    "total_use_cases": stats["total_use_cases"],
                    "domains": stats["domains"]["count"],
                    "ai_methods": stats["ai_methods"]["count"],
                    "statuses": stats["statuses"]["count"],
                },
            }

        # List domains - stable data, long cache
        @self.server.tool(
            cache_key="domains_list",
            cache_ttl=3600,  # 1 hour cache
            format_response="markdown",
        )
        def list_domains() -> dict:
            """List all available application domains."""
            domains = self.indexer.get_domains()
            domain_counts = {}
            for domain in domains:
                domain_counts[domain] = len(self.indexer.filter_by_domain(domain))

            return {"total_domains": len(domains), "domains": domain_counts}

        # List AI methods
        @self.server.tool(
            cache_key="methods_list", cache_ttl=3600, format_response="markdown"
        )
        def list_ai_methods() -> dict:
            """List all AI methods and technologies."""
            methods = self.indexer.get_ai_methods()
            return {
                "total_methods": len(methods),
                "methods": methods[:50],  # Limit to top 50
                "note": "Showing top 50 methods" if len(methods) > 50 else None,
            }

        # Find similar cases
        @self.server.tool(
            cache_key="similar", cache_ttl=300, format_response="markdown"
        )
        def find_similar_cases(use_case_id: int, limit: int = 5) -> dict:
            """Find similar use cases based on AI methods and domain."""
            # Find reference use case
            reference = None
            for uc in self.indexer.use_cases:
                if uc.get("use_case_id") == use_case_id:
                    reference = uc
                    break

            if not reference:
                return {
                    "found": False,
                    "error": f"Reference use case {use_case_id} not found",
                }

            similar = self.indexer.find_similar_cases(use_case_id, limit)
            return {
                "reference_case": reference,
                "similar_cases": similar,
                "count": len(similar),
            }

        # Trend analysis
        @self.server.tool(
            cache_key="trends",
            cache_ttl=900,  # 15 minute cache
            format_response="markdown",
        )
        def analyze_trends(domain: Optional[str] = None) -> dict:
            """Analyze trends in AI adoption."""
            results = self._analyze_trends_impl(domain)
            return {"domain": domain or "All domains", "trends": results}

        # Health check - no caching
        @self.server.tool(format_response="json")
        def health_check() -> dict:
            """Get server health and metrics."""
            stats = self.server.get_server_stats()
            return {
                "status": "healthy",
                "server_stats": stats,
                "registry_stats": {
                    "total_use_cases": len(self.indexer.use_cases),
                    "indexed": self.indexer.stats is not None,
                },
            }

    def _setup_resources(self):
        """Set up MCP resources."""

        @self.server.resource("ai-registry://overview")
        def registry_overview() -> str:
            """Registry overview resource."""
            stats = self.indexer.get_statistics()
            return self._format_overview(stats)

        # Add a dynamic domain resource handler
        @self.server.resource("ai-registry://domain/{domain}")
        def domain_resource(domain: str) -> str:
            """Domain-specific resource."""
            results = self.indexer.filter_by_domain(domain)
            return self._format_domain_results(domain, results)

    def _analyze_trends_impl(self, domain: Optional[str]) -> Dict[str, Any]:
        """Implement trend analysis logic."""
        trends = {"top_methods": [], "growth_areas": [], "maturity_distribution": {}}

        if domain:
            use_cases = self.indexer.filter_by_domain(domain)
        else:
            use_cases = self.indexer.use_cases

        # Analyze AI methods
        method_counts = {}
        status_counts = {}

        for uc in use_cases:
            for method in uc.get("ai_methods", []):
                method_counts[method] = method_counts.get(method, 0) + 1

            status = uc.get("status", "Unknown")
            status_counts[status] = status_counts.get(status, 0) + 1

        # Top methods
        sorted_methods = sorted(method_counts.items(), key=lambda x: x[1], reverse=True)
        trends["top_methods"] = [
            {"method": m, "count": c} for m, c in sorted_methods[:10]
        ]

        # Maturity distribution
        trends["maturity_distribution"] = status_counts

        # Growth areas (methods used in production)
        production_methods = {}
        for uc in use_cases:
            if uc.get("status") == "Production":
                for method in uc.get("ai_methods", []):
                    production_methods[method] = production_methods.get(method, 0) + 1

        sorted_production = sorted(
            production_methods.items(), key=lambda x: x[1], reverse=True
        )
        trends["growth_areas"] = [
            {"method": m, "production_count": c} for m, c in sorted_production[:5]
        ]

        return trends

    def _format_overview(self, stats: Dict[str, Any]) -> str:
        """Format registry overview as markdown."""
        overview = "# AI Registry Overview\n\n"
        overview += f"Total use cases: **{stats['total_use_cases']}**\n"
        overview += f"Application domains: **{stats['domains']['count']}**\n"
        overview += f"AI methods: **{stats['ai_methods']['count']}**\n"
        overview += f"Implementation statuses: **{stats['statuses']['count']}**\n\n"

        overview += "## Top Domains\n"
        for domain in stats["domains"]["top"][:5]:
            overview += f"- {domain}\n"

        overview += "\n## Top AI Methods\n"
        for method in stats["ai_methods"]["top"][:5]:
            overview += f"- {method}\n"

        return overview

    def _format_domain_results(self, domain: str, results: List[Dict[str, Any]]) -> str:
        """Format domain results as markdown."""
        markdown = f"# {domain} AI Use Cases\n\n"
        markdown += f"Found **{len(results)}** use cases in this domain.\n\n"

        for i, uc in enumerate(results[:20], 1):  # Limit to 20
            markdown += f"## {i}. {uc.get('name', 'Unnamed')}\n"
            markdown += f"**ID:** {uc.get('use_case_id', 'N/A')}\n"
            if desc := uc.get("description"):
                markdown += f"\n{desc}\n"
            if methods := uc.get("ai_methods"):
                markdown += f"\n**AI Methods:** {', '.join(methods)}\n"
            markdown += "\n---\n\n"

        return markdown

    def run(self):
        """Run the Enhanced MCP server."""
        logger.info("Starting AI Registry Enhanced MCP Server (Kailash v0.3.1+)")
        logger.info(f"Loaded {len(self.indexer.use_cases)} use cases")
        logger.info("Features: Enhanced Caching ✓ | Metrics ✓ | Formatting ✓")

        # The Enhanced MCP Server handles everything
        self.server.run()


# Keep this for backward compatibility
AIRegistryServer = AIRegistryMCPServer


if __name__ == "__main__":
    server = AIRegistryMCPServer()
    server.run()
