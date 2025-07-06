"""
Registry Search Node for AI Registry queries.

This node provides optimized search capabilities for the AI Registry,
with support for fuzzy matching, relevance scoring, and multi-field search.
"""

from typing import Any, Dict, List

from kailash.nodes.base import Node, NodeParameter

from ..config import config
from ..indexer import RegistryIndexer


class RegistrySearchNode(Node):
    """
    Specialized node for searching the AI Registry.

    This node provides advanced search capabilities including:
    - Full-text search across multiple fields
    - Fuzzy matching with configurable threshold
    - Relevance scoring
    - Result filtering and sorting
    """

    def __init__(self, name: str = "registry_search", **kwargs):
        """
        Initialize the Registry Search Node.

        Args:
            name: Node name
            **kwargs: Additional node configuration
        """
        # MUST set attributes BEFORE calling super().__init__()
        self.indexer = None
        self._initialized = False
        super().__init__(name=name, **kwargs)

    def _ensure_initialized(self):
        """Ensure the indexer is initialized."""
        if not self._initialized:
            # Create indexer with config
            self.indexer = RegistryIndexer(config.get("indexing", {}))

            # Load registry data
            registry_file = config.get("registry_file")
            self.indexer.load_and_index(registry_file)

            self._initialized = True

    def run(self, **kwargs) -> Dict[str, Any]:
        """
        Execute the search operation.

        Parameters:
            query (str): Search query string
            limit (int): Maximum results to return (default: 20)
            filters (Dict): Optional filters to apply:
                - domain (str): Filter by application domain
                - ai_methods (List[str]): Filter by AI methods
                - status (str): Filter by implementation status
                - min_score (float): Minimum relevance score
            sort_by (str): Sort results by 'relevance', 'name', 'id'
            include_stats (bool): Include search statistics

        Returns:
            Dict containing:
                - results: List of matching use cases
                - count: Total number of results
                - query: Original query
                - stats: Search statistics (if requested)
        """
        self._ensure_initialized()

        # Extract parameters
        query = kwargs.get("query", "")
        limit = kwargs.get("limit", 20)
        filters = kwargs.get("filters", {})
        sort_by = kwargs.get("sort_by", "relevance")
        include_stats = kwargs.get("include_stats", False)

        if not query:
            return {
                "success": False,
                "error": "Query parameter is required",
                "results": [],
                "count": 0,
            }

        # Perform search
        results = self.indexer.search(query, limit * 2)  # Get extra for filtering

        # Apply filters
        if filters:
            results = self._apply_filters(results, filters)

        # Sort results
        results = self._sort_results(results, sort_by)

        # Limit results
        results = results[:limit]

        # Prepare response
        response = {
            "success": True,
            "results": results,
            "count": len(results),
            "query": query,
            "total_in_registry": self.indexer.stats["total_use_cases"],
        }

        # Add statistics if requested
        if include_stats:
            response["stats"] = self._generate_search_stats(results)

        return response

    def _apply_filters(
        self, results: List[Dict[str, Any]], filters: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Apply filters to search results."""
        filtered = results

        # Domain filter
        if domain := filters.get("domain"):
            filtered = [
                r
                for r in filtered
                if r.get("application_domain", "").lower() == domain.lower()
            ]

        # AI methods filter
        if methods := filters.get("ai_methods"):
            methods_lower = [m.lower() for m in methods]
            filtered = [
                r
                for r in filtered
                if any(m.lower() in methods_lower for m in r.get("ai_methods", []))
            ]

        # Status filter
        if status := filters.get("status"):
            filtered = [
                r for r in filtered if r.get("status", "").lower() == status.lower()
            ]

        # Minimum score filter
        if min_score := filters.get("min_score"):
            filtered = [
                r for r in filtered if r.get("_relevance_score", 0) >= min_score
            ]

        return filtered

    def _sort_results(
        self, results: List[Dict[str, Any]], sort_by: str
    ) -> List[Dict[str, Any]]:
        """Sort results based on criteria."""
        if sort_by == "relevance":
            return sorted(
                results, key=lambda x: x.get("_relevance_score", 0), reverse=True
            )
        elif sort_by == "name":
            return sorted(results, key=lambda x: x.get("name", ""))
        elif sort_by == "id":
            return sorted(results, key=lambda x: x.get("use_case_id", 0))
        else:
            return results

    def _generate_search_stats(self, results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Generate statistics about search results."""
        if not results:
            return {"domains": {}, "methods": {}, "statuses": {}}

        # Count domains
        domains = {}
        for r in results:
            domain = r.get("application_domain", "Unknown")
            domains[domain] = domains.get(domain, 0) + 1

        # Count AI methods
        methods = {}
        for r in results:
            for method in r.get("ai_methods", []):
                methods[method] = methods.get(method, 0) + 1

        # Count statuses
        statuses = {}
        for r in results:
            status = r.get("status", "Unknown")
            statuses[status] = statuses.get(status, 0) + 1

        # Calculate score statistics
        scores = [r.get("_relevance_score", 0) for r in results]

        return {
            "domains": domains,
            "methods": methods,
            "statuses": statuses,
            "score_range": {
                "min": min(scores) if scores else 0,
                "max": max(scores) if scores else 0,
                "avg": sum(scores) / len(scores) if scores else 0,
            },
        }

    def get_parameters(self) -> Dict[str, NodeParameter]:
        """Get required parameters for the node."""
        return {
            "query": NodeParameter(
                name="query",
                type=str,
                required=False,  # Make it optional with empty default
                default="",
                description="Search query string",
            ),
            "limit": NodeParameter(
                name="limit",
                type=int,
                required=False,
                default=20,
                description="Maximum number of results to return (1-50)",
            ),
            "filters": NodeParameter(
                name="filters",
                type=dict,  # Use dict instead of Dict[str, Any]
                required=False,
                default={},
                description="Optional filters to apply (domain, ai_method, status)",
            ),
            "sort_by": NodeParameter(
                name="sort_by",
                type=str,
                required=False,
                default="relevance",
                description="Sort results by criteria (relevance, name, id)",
            ),
            "include_stats": NodeParameter(
                name="include_stats",
                type=bool,
                required=False,
                default=False,
                description="Include search statistics",
            ),
        }

    def get_config_schema(self) -> Dict[str, Any]:
        """Get configuration schema for the node."""
        return {
            "type": "object",
            "properties": {
                "enable_fuzzy": {
                    "type": "boolean",
                    "description": "Enable fuzzy matching",
                    "default": True,
                },
                "similarity_threshold": {
                    "type": "number",
                    "description": "Similarity threshold for fuzzy matching",
                    "default": 0.7,
                    "minimum": 0.0,
                    "maximum": 1.0,
                },
                "index_fields": {
                    "type": "array",
                    "description": "Fields to index for search",
                    "items": {"type": "string"},
                    "default": [
                        "name",
                        "description",
                        "narrative",
                        "application_domain",
                        "ai_methods",
                        "tasks",
                    ],
                },
            },
        }
