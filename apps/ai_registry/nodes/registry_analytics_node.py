"""
Registry Analytics Node for AI Registry analysis.

This node provides statistical analysis and reporting capabilities
for the AI Registry data.
"""

from typing import Any, Dict, List, Optional, Tuple

from kailash.nodes.base import Node, NodeParameter

from ..config import config
from ..indexer import RegistryIndexer


class RegistryAnalyticsNode(Node):
    """
    Node for performing analytics on the AI Registry.

    This node provides:
    - Statistical analysis of use cases
    - Domain and method distribution analysis
    - Trend identification
    - Report generation
    """

    def __init__(self, name: str = "registry_analytics", **kwargs):
        """
        Initialize the Registry Analytics Node.

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
        Execute analytics operation.

        Parameters:
            analysis_type (str): Type of analysis to perform
                - 'overview': General statistics
                - 'domain_analysis': Domain-specific analysis
                - 'method_analysis': AI method analysis
                - 'trend_analysis': Trend identification
                - 'gap_analysis': Identify gaps in coverage
            domain (str): Optional domain to focus on
            output_format (str): 'json', 'markdown', 'summary'
            include_visualizations (bool): Generate visualization data

        Returns:
            Dict containing analysis results
        """
        self._ensure_initialized()

        # Extract parameters
        analysis_type = kwargs.get("analysis_type", "overview")
        domain = kwargs.get("domain")
        output_format = kwargs.get("output_format", "json")
        include_viz = kwargs.get("include_visualizations", False)

        # Perform analysis
        if analysis_type == "overview":
            results = self._analyze_overview()
        elif analysis_type == "domain_analysis":
            results = self._analyze_domains(domain)
        elif analysis_type == "method_analysis":
            results = self._analyze_methods()
        elif analysis_type == "trend_analysis":
            results = self._analyze_trends()
        elif analysis_type == "gap_analysis":
            results = self._analyze_gaps()
        else:
            return {
                "success": False,
                "error": f"Unknown analysis type: {analysis_type}",
            }

        # Add visualizations if requested
        if include_viz:
            results["visualizations"] = self._generate_visualization_data(
                results, analysis_type
            )

        # Format output
        if output_format == "markdown":
            results["markdown"] = self._format_as_markdown(results, analysis_type)
        elif output_format == "summary":
            results["summary"] = self._generate_summary(results, analysis_type)

        results["success"] = True
        results["analysis_type"] = analysis_type

        return results

    def _analyze_overview(self) -> Dict[str, Any]:
        """Generate overview statistics."""
        stats = self.indexer.get_statistics()

        # Calculate additional metrics
        use_cases = self.indexer.use_cases

        # Multi-domain use cases (placeholder for future implementation)
        # multi_domain = 0
        # Average methods per use case
        total_methods = 0
        # Implementation maturity
        maturity_scores = {
            "Research": 1,
            "listed_only": 1,
            "PoC": 2,
            "Pilot": 3,
            "Production": 4,
        }
        total_maturity = 0

        for uc in use_cases:
            methods = uc.get("ai_methods", [])
            total_methods += len(methods)

            status = uc.get("status", "listed_only")
            total_maturity += maturity_scores.get(status, 1)

        avg_methods = total_methods / len(use_cases) if use_cases else 0
        avg_maturity = total_maturity / len(use_cases) if use_cases else 0

        return {
            "basic_stats": stats,
            "metrics": {
                "average_methods_per_case": round(avg_methods, 2),
                "average_maturity_score": round(avg_maturity, 2),
                "domains_per_case": (
                    round(len(use_cases) / stats["domains"]["count"], 2)
                    if stats["domains"]["count"] > 0
                    else 0
                ),
            },
            "coverage": {
                "domains_with_production": self._count_domains_with_status(
                    "Production"
                ),
                "methods_in_production": self._count_methods_in_status("Production"),
                "poc_to_production_ratio": self._calculate_poc_to_production_ratio(),
            },
        }

    def _analyze_domains(self, specific_domain: Optional[str] = None) -> Dict[str, Any]:
        """Analyze domains in detail."""
        if specific_domain:
            # Analyze specific domain
            use_cases = self.indexer.filter_by_domain(specific_domain)
            if not use_cases:
                return {"error": f"Domain '{specific_domain}' not found"}

            return self._analyze_single_domain(specific_domain, use_cases)
        else:
            # Analyze all domains
            domains_analysis = {}

            for domain in self.indexer.get_domains():
                use_cases = self.indexer.filter_by_domain(domain)
                domains_analysis[domain] = self._analyze_single_domain(
                    domain, use_cases
                )

            return {
                "domains": domains_analysis,
                "comparison": self._compare_domains(domains_analysis),
            }

    def _analyze_single_domain(
        self, domain: str, use_cases: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Analyze a single domain."""
        # Method distribution
        method_counts = {}
        task_counts = {}
        status_counts = {}

        for uc in use_cases:
            for method in uc.get("ai_methods", []):
                method_counts[method] = method_counts.get(method, 0) + 1

            for task in uc.get("tasks", []):
                task_counts[task] = task_counts.get(task, 0) + 1

            status = uc.get("status", "Unknown")
            status_counts[status] = status_counts.get(status, 0) + 1

        return {
            "use_case_count": len(use_cases),
            "top_methods": sorted(
                method_counts.items(), key=lambda x: x[1], reverse=True
            )[:5],
            "top_tasks": sorted(task_counts.items(), key=lambda x: x[1], reverse=True)[
                :5
            ],
            "status_distribution": status_counts,
            "maturity_index": self._calculate_maturity_index(status_counts),
            "diversity_score": len(method_counts) / len(use_cases) if use_cases else 0,
        }

    def _analyze_methods(self) -> Dict[str, Any]:
        """Analyze AI methods in detail."""
        method_analysis = {}

        for method in self.indexer.get_ai_methods():
            use_cases = self.indexer.filter_by_ai_method(method)

            # Collect statistics
            domains = set()
            paired_methods = {}
            statuses = {}

            for uc in use_cases:
                domains.add(uc.get("application_domain", "Unknown"))

                # Count paired methods
                for other_method in uc.get("ai_methods", []):
                    if other_method != method:
                        paired_methods[other_method] = (
                            paired_methods.get(other_method, 0) + 1
                        )

                status = uc.get("status", "Unknown")
                statuses[status] = statuses.get(status, 0) + 1

            method_analysis[method] = {
                "usage_count": len(use_cases),
                "domain_spread": len(domains),
                "domains": list(domains),
                "common_pairings": sorted(
                    paired_methods.items(), key=lambda x: x[1], reverse=True
                )[:5],
                "maturity_distribution": statuses,
                "production_rate": (
                    statuses.get("Production", 0) / len(use_cases) if use_cases else 0
                ),
            }

        return {
            "methods": method_analysis,
            "insights": self._generate_method_insights(method_analysis),
        }

    def _analyze_trends(self) -> Dict[str, Any]:
        """Identify trends in the AI Registry."""
        trends = {
            "emerging_combinations": self._find_emerging_combinations(),
            "maturity_progression": self._analyze_maturity_progression(),
            "domain_convergence": self._analyze_domain_convergence(),
            "method_evolution": self._analyze_method_evolution_trends(),
        }

        return trends

    def _analyze_gaps(self) -> Dict[str, Any]:
        """Identify gaps in AI implementation coverage."""
        gaps = {
            "underrepresented_domains": self._find_underrepresented_domains(),
            "missing_method_combinations": self._find_missing_combinations(),
            "low_maturity_areas": self._find_low_maturity_areas(),
            "single_implementation_methods": self._find_single_implementations(),
        }

        return gaps

    def _count_domains_with_status(self, status: str) -> int:
        """Count domains that have at least one use case with given status."""
        domains_with_status = set()

        for uc in self.indexer.use_cases:
            if uc.get("status") == status:
                domains_with_status.add(uc.get("application_domain"))

        return len(domains_with_status)

    def _count_methods_in_status(self, status: str) -> int:
        """Count unique AI methods used in use cases with given status."""
        methods_in_status = set()

        for uc in self.indexer.use_cases:
            if uc.get("status") == status:
                methods_in_status.update(uc.get("ai_methods", []))

        return len(methods_in_status)

    def _calculate_poc_to_production_ratio(self) -> float:
        """Calculate ratio of PoC to Production implementations."""
        poc_count = len(self.indexer.filter_by_status("PoC"))
        prod_count = len(self.indexer.filter_by_status("Production"))

        if prod_count == 0:
            return float("inf") if poc_count > 0 else 0

        return round(poc_count / prod_count, 2)

    def _calculate_maturity_index(self, status_counts: Dict[str, int]) -> float:
        """Calculate maturity index for a set of use cases."""
        maturity_scores = {
            "Research": 1,
            "listed_only": 1,
            "PoC": 2,
            "Pilot": 3,
            "Production": 4,
        }

        total_score = 0
        total_count = 0

        for status, count in status_counts.items():
            score = maturity_scores.get(status, 1)
            total_score += score * count
            total_count += count

        return round(total_score / total_count, 2) if total_count > 0 else 0

    def _compare_domains(self, domains_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Compare domains across various metrics."""
        # Sort domains by various metrics
        by_count = sorted(
            [(d, info["use_case_count"]) for d, info in domains_analysis.items()],
            key=lambda x: x[1],
            reverse=True,
        )

        by_maturity = sorted(
            [(d, info["maturity_index"]) for d, info in domains_analysis.items()],
            key=lambda x: x[1],
            reverse=True,
        )

        by_diversity = sorted(
            [(d, info["diversity_score"]) for d, info in domains_analysis.items()],
            key=lambda x: x[1],
            reverse=True,
        )

        return {
            "leaders_by_count": by_count[:5],
            "leaders_by_maturity": by_maturity[:5],
            "leaders_by_diversity": by_diversity[:5],
        }

    def _generate_method_insights(
        self, method_analysis: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Generate insights from method analysis."""
        # Most versatile methods (used across many domains)
        versatile = sorted(
            [(m, info["domain_spread"]) for m, info in method_analysis.items()],
            key=lambda x: x[1],
            reverse=True,
        )[:5]

        # Most mature methods (highest production rate)
        mature = sorted(
            [(m, info["production_rate"]) for m, info in method_analysis.items()],
            key=lambda x: x[1],
            reverse=True,
        )[:5]

        # Emerging methods (high usage but low production rate)
        emerging = [
            (m, info["usage_count"])
            for m, info in method_analysis.items()
            if info["production_rate"] < 0.2 and info["usage_count"] > 5
        ]

        return {
            "most_versatile": versatile,
            "most_mature": mature,
            "emerging": sorted(emerging, key=lambda x: x[1], reverse=True)[:5],
        }

    def _find_emerging_combinations(self) -> List[Dict[str, Any]]:
        """Find emerging AI method combinations."""
        # This would require more sophisticated analysis
        # For now, return placeholder
        return []

    def _analyze_maturity_progression(self) -> Dict[str, Any]:
        """Analyze how use cases progress in maturity."""
        # This would require temporal data
        # For now, return current distribution
        status_dist = {}
        for uc in self.indexer.use_cases:
            status = uc.get("status", "Unknown")
            status_dist[status] = status_dist.get(status, 0) + 1

        return {"current_distribution": status_dist}

    def _analyze_domain_convergence(self) -> Dict[str, Any]:
        """Analyze convergence of AI methods across domains."""
        # Find methods used in multiple domains
        method_domains = {}

        for uc in self.indexer.use_cases:
            domain = uc.get("application_domain", "Unknown")
            for method in uc.get("ai_methods", []):
                if method not in method_domains:
                    method_domains[method] = set()
                method_domains[method].add(domain)

        # Find highly convergent methods
        convergent = [
            (method, len(domains))
            for method, domains in method_domains.items()
            if len(domains) >= 3
        ]

        return {
            "convergent_methods": sorted(convergent, key=lambda x: x[1], reverse=True),
            "cross_domain_adoption": (
                len(convergent) / len(method_domains) if method_domains else 0
            ),
        }

    def _analyze_method_evolution_trends(self) -> Dict[str, Any]:
        """Analyze evolution trends in AI methods."""
        # Simplified analysis without temporal data
        return {
            "total_methods": len(self.indexer.get_ai_methods()),
            "methods_per_domain": {
                domain: len(
                    set(
                        m
                        for uc in self.indexer.filter_by_domain(domain)
                        for m in uc.get("ai_methods", [])
                    )
                )
                for domain in self.indexer.get_domains()
            },
        }

    def _find_underrepresented_domains(self) -> List[str]:
        """Find domains with few use cases."""
        domain_counts = {}
        for domain in self.indexer.get_domains():
            count = len(self.indexer.filter_by_domain(domain))
            domain_counts[domain] = count

        avg_count = (
            sum(domain_counts.values()) / len(domain_counts) if domain_counts else 0
        )

        return [
            domain for domain, count in domain_counts.items() if count < avg_count * 0.5
        ]

    def _find_missing_combinations(self) -> List[Tuple[str, str]]:
        """Find potentially valuable method combinations that don't exist."""
        # This would require domain expertise
        # For now, return empty list
        return []

    def _find_low_maturity_areas(self) -> Dict[str, List[str]]:
        """Find domains and methods with low maturity."""
        low_maturity_domains = []
        low_maturity_methods = []

        # Check domains
        for domain in self.indexer.get_domains():
            use_cases = self.indexer.filter_by_domain(domain)
            prod_count = sum(1 for uc in use_cases if uc.get("status") == "Production")
            if prod_count == 0:
                low_maturity_domains.append(domain)

        # Check methods
        for method in self.indexer.get_ai_methods():
            use_cases = self.indexer.filter_by_ai_method(method)
            prod_count = sum(1 for uc in use_cases if uc.get("status") == "Production")
            if prod_count == 0:
                low_maturity_methods.append(method)

        return {"domains": low_maturity_domains, "methods": low_maturity_methods}

    def _find_single_implementations(self) -> Dict[str, List[str]]:
        """Find methods with only single implementations."""
        single_impl_methods = []

        for method in self.indexer.get_ai_methods():
            use_cases = self.indexer.filter_by_ai_method(method)
            if len(use_cases) == 1:
                single_impl_methods.append(method)

        return {"methods": single_impl_methods}

    def _generate_visualization_data(
        self, results: Dict[str, Any], analysis_type: str
    ) -> Dict[str, Any]:
        """Generate data suitable for visualization."""
        viz_data = {}

        if analysis_type == "overview":
            # Pie chart data for status distribution
            viz_data["status_distribution"] = {
                "type": "pie",
                "data": results["basic_stats"]["status_distribution"],
            }

            # Bar chart for top domains
            domain_dist = results["basic_stats"]["domain_distribution"]
            top_domains = sorted(domain_dist.items(), key=lambda x: x[1], reverse=True)[
                :10
            ]
            viz_data["top_domains"] = {"type": "bar", "data": dict(top_domains)}

        elif analysis_type == "domain_analysis" and "domains" in results:
            # Heatmap data for domain-method relationships
            heatmap_data = []
            for domain, info in results["domains"].items():
                for method, count in info["top_methods"]:
                    heatmap_data.append(
                        {"domain": domain, "method": method, "count": count}
                    )

            viz_data["domain_method_heatmap"] = {
                "type": "heatmap",
                "data": heatmap_data,
            }

        return viz_data

    def _format_as_markdown(self, results: Dict[str, Any], analysis_type: str) -> str:
        """Format results as markdown."""
        lines = [f"# AI Registry {analysis_type.replace('_', ' ').title()}", ""]

        if analysis_type == "overview":
            stats = results["basic_stats"]
            metrics = results["metrics"]

            lines.extend(
                [
                    "## Summary Statistics",
                    f"- **Total Use Cases:** {stats['total_use_cases']}",
                    f"- **Domains:** {stats['domains']['count']}",
                    f"- **AI Methods:** {stats['ai_methods']['count']}",
                    f"- **Average Methods per Case:** {metrics['average_methods_per_case']}",
                    f"- **Average Maturity Score:** {metrics['average_maturity_score']}/4.0",
                    "",
                ]
            )

        return "\n".join(lines)

    def _generate_summary(self, results: Dict[str, Any], analysis_type: str) -> str:
        """Generate a text summary of the analysis."""
        if analysis_type == "overview":
            stats = results["basic_stats"]
            return (
                f"The AI Registry contains {stats['total_use_cases']} use cases "
                f"across {stats['domains']['count']} domains, utilizing "
                f"{stats['ai_methods']['count']} different AI methods. "
                f"The average implementation maturity score is {results['metrics']['average_maturity_score']:.1f}/4.0."
            )

        return f"Analysis completed for {analysis_type}"

    def get_parameters(self) -> Dict[str, NodeParameter]:
        """Get required parameters for the node."""
        return {
            "analysis_type": NodeParameter(
                name="analysis_type",
                type=str,
                required=False,  # Make it optional with default
                default="overview",
                description="Type of analysis to perform (overview, domain_analysis, method_analysis, trend_analysis, gap_analysis)",
            ),
            "domain": NodeParameter(
                name="domain",
                type=str,
                required=False,
                default=None,
                description="Optional domain to focus on",
            ),
            "output_format": NodeParameter(
                name="output_format",
                type=str,
                required=False,
                default="json",
                description="Output format (json, markdown, summary)",
            ),
            "include_visualizations": NodeParameter(
                name="include_visualizations",
                type=bool,
                required=False,
                default=False,
                description="Generate visualization data",
            ),
        }

    def get_config_schema(self) -> Dict[str, Any]:
        """Get configuration schema for the node."""
        return {
            "type": "object",
            "properties": {
                "cache_results": {
                    "type": "boolean",
                    "description": "Cache analysis results",
                    "default": True,
                },
                "include_raw_data": {
                    "type": "boolean",
                    "description": "Include raw data in results",
                    "default": False,
                },
            },
        }
