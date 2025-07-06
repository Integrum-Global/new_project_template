"""
Registry Compare Node for comparing AI use cases.

This node provides capabilities to compare multiple AI use cases
across various dimensions.
"""

from typing import Any, Dict, List, Optional, Tuple

from kailash.nodes.base import Node, NodeParameter

from ..config import config
from ..indexer import RegistryIndexer


class RegistryCompareNode(Node):
    """
    Node for comparing AI use cases in the registry.

    This node provides:
    - Side-by-side comparison of use cases
    - Similarity scoring between use cases
    - Gap analysis between use cases
    - Comparative reports
    """

    def __init__(self, name: str = "registry_compare", **kwargs):
        """
        Initialize the Registry Compare Node.

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
        Execute comparison operation.

        Parameters:
            comparison_type (str): Type of comparison
                - 'direct': Direct comparison of specified use cases
                - 'similarity': Find similar use cases
                - 'gap_analysis': Analyze gaps between use cases
                - 'domain_comparison': Compare use cases across domains
            use_case_ids (List[int]): IDs of use cases to compare
            base_id (int): Base use case ID for similarity comparison
            domains (List[str]): Domains to compare (for domain comparison)
            comparison_criteria (List[str]): Specific criteria to compare
            output_format (str): 'json', 'table', 'report'

        Returns:
            Dict containing comparison results
        """
        self._ensure_initialized()

        # Extract parameters
        comparison_type = kwargs.get("comparison_type", "direct")
        use_case_ids = kwargs.get("use_case_ids", [])
        base_id = kwargs.get("base_id")
        domains = kwargs.get("domains", [])
        criteria = kwargs.get(
            "comparison_criteria",
            ["domain", "ai_methods", "tasks", "status", "challenges"],
        )
        output_format = kwargs.get("output_format", "json")

        # Validate inputs
        if comparison_type in ["direct", "gap_analysis"] and not use_case_ids:
            return {
                "success": False,
                "error": "use_case_ids required for direct comparison or gap analysis",
            }

        if comparison_type == "similarity" and not base_id:
            return {
                "success": False,
                "error": "base_id required for similarity comparison",
            }

        # Perform comparison
        if comparison_type == "direct":
            results = self._compare_direct(use_case_ids, criteria)
        elif comparison_type == "similarity":
            results = self._compare_similarity(base_id, use_case_ids)
        elif comparison_type == "gap_analysis":
            results = self._analyze_gaps(use_case_ids)
        elif comparison_type == "domain_comparison":
            results = self._compare_domains(domains or self.indexer.get_domains()[:5])
        else:
            return {
                "success": False,
                "error": f"Unknown comparison type: {comparison_type}",
            }

        # Format output
        if output_format == "table":
            results["table"] = self._format_as_table(results, comparison_type)
        elif output_format == "report":
            results["report"] = self._generate_report(results, comparison_type)

        results["success"] = True
        results["comparison_type"] = comparison_type

        return results

    def _compare_direct(
        self, use_case_ids: List[int], criteria: List[str]
    ) -> Dict[str, Any]:
        """Perform direct comparison of use cases."""
        # Get use cases
        use_cases = []
        for uid in use_case_ids:
            uc = self.indexer.get_by_id(uid)
            if uc:
                use_cases.append(uc)

        if not use_cases:
            return {"error": "No valid use cases found"}

        # Build comparison matrix
        comparison = {"use_cases": [], "criteria_comparison": {}}

        # Basic info for each use case
        for uc in use_cases:
            comparison["use_cases"].append(
                {
                    "id": uc.get("use_case_id"),
                    "name": uc.get("name"),
                    "domain": uc.get("application_domain"),
                }
            )

        # Compare each criterion
        for criterion in criteria:
            comparison["criteria_comparison"][criterion] = self._compare_criterion(
                use_cases, criterion
            )

        # Calculate similarity matrix
        comparison["similarity_matrix"] = self._calculate_similarity_matrix(use_cases)

        # Identify commonalities and differences
        comparison["commonalities"] = self._find_commonalities(use_cases)
        comparison["differences"] = self._find_differences(use_cases)

        return comparison

    def _compare_criterion(
        self, use_cases: List[Dict[str, Any]], criterion: str
    ) -> Dict[str, Any]:
        """Compare use cases on a specific criterion."""
        result = {"values": {}, "analysis": {}}

        # Extract values for each use case
        for uc in use_cases:
            uc_id = uc.get("use_case_id")
            if criterion in ["ai_methods", "tasks", "kpis"]:
                # List fields
                result["values"][uc_id] = uc.get(criterion, [])
            else:
                # Single value fields
                result["values"][uc_id] = uc.get(criterion, "N/A")

        # Analyze based on criterion type
        if criterion in ["ai_methods", "tasks", "kpis"]:
            # List analysis
            all_values = set()
            for values in result["values"].values():
                all_values.update(values)

            result["analysis"]["all_values"] = list(all_values)
            result["analysis"]["common_values"] = self._find_common_list_values(
                result["values"]
            )
            result["analysis"]["unique_values"] = self._find_unique_list_values(
                result["values"]
            )
        else:
            # Single value analysis
            unique_values = set(result["values"].values())
            result["analysis"]["unique_count"] = len(unique_values)
            result["analysis"]["all_same"] = len(unique_values) == 1

        return result

    def _compare_similarity(
        self, base_id: int, compare_ids: Optional[List[int]] = None
    ) -> Dict[str, Any]:
        """Compare similarity of use cases to a base case."""
        base_case = self.indexer.get_by_id(base_id)
        if not base_case:
            return {"error": f"Base use case {base_id} not found"}

        # If no comparison IDs provided, find similar cases
        if not compare_ids:
            similar_cases = self.indexer.find_similar_cases(base_id, 10)
            compare_cases = similar_cases
        else:
            compare_cases = [
                self.indexer.get_by_id(uid)
                for uid in compare_ids
                if self.indexer.get_by_id(uid)
            ]

        # Calculate detailed similarity scores
        similarity_details = []

        for uc in compare_cases:
            if uc.get("use_case_id") == base_id:
                continue

            similarity = self._calculate_detailed_similarity(base_case, uc)
            similarity_details.append(
                {
                    "use_case": {
                        "id": uc.get("use_case_id"),
                        "name": uc.get("name"),
                        "domain": uc.get("application_domain"),
                    },
                    "similarity": similarity,
                }
            )

        # Sort by overall similarity
        similarity_details.sort(key=lambda x: x["similarity"]["overall"], reverse=True)

        return {
            "base_case": {
                "id": base_case.get("use_case_id"),
                "name": base_case.get("name"),
                "domain": base_case.get("application_domain"),
            },
            "comparisons": similarity_details,
            "most_similar": similarity_details[0] if similarity_details else None,
            "least_similar": similarity_details[-1] if similarity_details else None,
        }

    def _analyze_gaps(self, use_case_ids: List[int]) -> Dict[str, Any]:
        """Analyze gaps between use cases."""
        use_cases = [
            self.indexer.get_by_id(uid)
            for uid in use_case_ids
            if self.indexer.get_by_id(uid)
        ]

        if len(use_cases) < 2:
            return {"error": "At least 2 use cases required for gap analysis"}

        gaps = {
            "method_gaps": self._analyze_method_gaps(use_cases),
            "maturity_gaps": self._analyze_maturity_gaps(use_cases),
            "task_gaps": self._analyze_task_gaps(use_cases),
            "implementation_gaps": self._analyze_implementation_gaps(use_cases),
        }

        # Generate recommendations
        gaps["recommendations"] = self._generate_gap_recommendations(gaps)

        return gaps

    def _compare_domains(self, domains: List[str]) -> Dict[str, Any]:
        """Compare use cases across domains."""
        domain_comparison = {}

        for domain in domains:
            use_cases = self.indexer.filter_by_domain(domain)

            if not use_cases:
                continue

            # Aggregate statistics
            all_methods = []
            all_tasks = []
            statuses = {}

            for uc in use_cases:
                all_methods.extend(uc.get("ai_methods", []))
                all_tasks.extend(uc.get("tasks", []))
                status = uc.get("status", "Unknown")
                statuses[status] = statuses.get(status, 0) + 1

            # Count unique values
            unique_methods = set(all_methods)
            unique_tasks = set(all_tasks)

            domain_comparison[domain] = {
                "use_case_count": len(use_cases),
                "unique_methods": len(unique_methods),
                "unique_tasks": len(unique_tasks),
                "top_methods": self._get_top_items(all_methods, 3),
                "top_tasks": self._get_top_items(all_tasks, 3),
                "maturity_distribution": statuses,
                "production_rate": (
                    statuses.get("Production", 0) / len(use_cases) if use_cases else 0
                ),
            }

        # Cross-domain analysis
        analysis = {
            "domains": domain_comparison,
            "cross_domain_methods": self._find_cross_domain_methods(domains),
            "domain_specialization": self._analyze_domain_specialization(
                domain_comparison
            ),
            "maturity_comparison": self._compare_domain_maturity(domain_comparison),
        }

        return analysis

    def _calculate_similarity_matrix(
        self, use_cases: List[Dict[str, Any]]
    ) -> List[List[float]]:
        """Calculate pairwise similarity matrix."""
        n = len(use_cases)
        matrix = [[0.0] * n for _ in range(n)]

        for i in range(n):
            for j in range(n):
                if i == j:
                    matrix[i][j] = 1.0
                else:
                    similarity = self._calculate_detailed_similarity(
                        use_cases[i], use_cases[j]
                    )
                    matrix[i][j] = similarity["overall"]

        return matrix

    def _calculate_detailed_similarity(
        self, uc1: Dict[str, Any], uc2: Dict[str, Any]
    ) -> Dict[str, float]:
        """Calculate detailed similarity between two use cases."""
        # Domain similarity (binary)
        domain_sim = (
            1.0
            if uc1.get("application_domain") == uc2.get("application_domain")
            else 0.0
        )

        # Method similarity (Jaccard index)
        methods1 = set(uc1.get("ai_methods", []))
        methods2 = set(uc2.get("ai_methods", []))
        method_sim = (
            len(methods1 & methods2) / len(methods1 | methods2)
            if methods1 | methods2
            else 0.0
        )

        # Task similarity (Jaccard index)
        tasks1 = set(uc1.get("tasks", []))
        tasks2 = set(uc2.get("tasks", []))
        task_sim = (
            len(tasks1 & tasks2) / len(tasks1 | tasks2) if tasks1 | tasks2 else 0.0
        )

        # Status similarity (weighted)
        status_weights = {
            "Research": 1,
            "listed_only": 1,
            "PoC": 2,
            "Pilot": 3,
            "Production": 4,
        }
        status1 = status_weights.get(uc1.get("status", "listed_only"), 1)
        status2 = status_weights.get(uc2.get("status", "listed_only"), 1)
        status_sim = 1.0 - (abs(status1 - status2) / 3.0)  # Normalize to 0-1

        # Overall similarity (weighted average)
        overall = (
            domain_sim * 0.3 + method_sim * 0.3 + task_sim * 0.25 + status_sim * 0.15
        )

        return {
            "overall": round(overall, 3),
            "domain": domain_sim,
            "methods": round(method_sim, 3),
            "tasks": round(task_sim, 3),
            "status": round(status_sim, 3),
        }

    def _find_commonalities(self, use_cases: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Find common elements across use cases."""
        if not use_cases:
            return {}

        # Find common methods
        common_methods = set(use_cases[0].get("ai_methods", []))
        for uc in use_cases[1:]:
            common_methods &= set(uc.get("ai_methods", []))

        # Find common tasks
        common_tasks = set(use_cases[0].get("tasks", []))
        for uc in use_cases[1:]:
            common_tasks &= set(uc.get("tasks", []))

        # Check if all same domain
        domains = [uc.get("application_domain") for uc in use_cases]
        same_domain = len(set(domains)) == 1

        # Check if all same status
        statuses = [uc.get("status") for uc in use_cases]
        same_status = len(set(statuses)) == 1

        return {
            "common_methods": list(common_methods),
            "common_tasks": list(common_tasks),
            "same_domain": same_domain,
            "domain": domains[0] if same_domain else None,
            "same_status": same_status,
            "status": statuses[0] if same_status else None,
        }

    def _find_differences(self, use_cases: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Find differences between use cases."""
        differences = {
            "unique_methods": {},
            "unique_tasks": {},
            "domains": set(),
            "statuses": set(),
        }

        # Collect all methods and tasks
        all_methods = set()
        all_tasks = set()

        for uc in use_cases:
            all_methods.update(uc.get("ai_methods", []))
            all_tasks.update(uc.get("tasks", []))
            differences["domains"].add(uc.get("application_domain"))
            differences["statuses"].add(uc.get("status"))

        # Find unique methods for each use case
        for uc in use_cases:
            uc_id = uc.get("use_case_id")
            uc_methods = set(uc.get("ai_methods", []))

            # Methods unique to this use case
            unique = uc_methods.copy()
            for other_uc in use_cases:
                if other_uc.get("use_case_id") != uc_id:
                    unique -= set(other_uc.get("ai_methods", []))

            if unique:
                differences["unique_methods"][uc_id] = list(unique)

        # Find unique tasks for each use case
        for uc in use_cases:
            uc_id = uc.get("use_case_id")
            uc_tasks = set(uc.get("tasks", []))

            # Tasks unique to this use case
            unique = uc_tasks.copy()
            for other_uc in use_cases:
                if other_uc.get("use_case_id") != uc_id:
                    unique -= set(other_uc.get("tasks", []))

            if unique:
                differences["unique_tasks"][uc_id] = list(unique)

        differences["domains"] = list(differences["domains"])
        differences["statuses"] = list(differences["statuses"])

        return differences

    def _find_common_list_values(self, values_dict: Dict[int, List[str]]) -> List[str]:
        """Find common values across all lists."""
        if not values_dict:
            return []

        # Start with first list
        common = set(list(values_dict.values())[0])

        # Intersect with all other lists
        for values in list(values_dict.values())[1:]:
            common &= set(values)

        return list(common)

    def _find_unique_list_values(
        self, values_dict: Dict[int, List[str]]
    ) -> Dict[int, List[str]]:
        """Find unique values for each list."""
        unique = {}

        for key, values in values_dict.items():
            values_set = set(values)

            # Remove values that appear in other lists
            for other_key, other_values in values_dict.items():
                if key != other_key:
                    values_set -= set(other_values)

            if values_set:
                unique[key] = list(values_set)

        return unique

    def _analyze_method_gaps(self, use_cases: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze gaps in AI methods between use cases."""
        # Collect all methods used
        all_methods = set()
        method_usage = {}

        for uc in use_cases:
            uc_id = uc.get("use_case_id")
            methods = set(uc.get("ai_methods", []))
            all_methods.update(methods)
            method_usage[uc_id] = methods

        # Find gaps (methods not used by each use case)
        gaps = {}
        for uc in use_cases:
            uc_id = uc.get("use_case_id")
            missing = all_methods - method_usage[uc_id]
            if missing:
                gaps[uc_id] = list(missing)

        return {
            "total_methods": len(all_methods),
            "gaps_by_use_case": gaps,
            "coverage": {
                uc_id: len(methods) / len(all_methods) if all_methods else 0
                for uc_id, methods in method_usage.items()
            },
        }

    def _analyze_maturity_gaps(self, use_cases: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze maturity gaps between use cases."""
        maturity_scores = {
            "Research": 1,
            "listed_only": 1,
            "PoC": 2,
            "Pilot": 3,
            "Production": 4,
        }

        scores = {}
        for uc in use_cases:
            status = uc.get("status", "listed_only")
            scores[uc.get("use_case_id")] = maturity_scores.get(status, 1)

        max_score = max(scores.values())
        min_score = min(scores.values())

        return {
            "scores": scores,
            "gap": max_score - min_score,
            "highest_maturity": [
                uid for uid, score in scores.items() if score == max_score
            ],
            "lowest_maturity": [
                uid for uid, score in scores.items() if score == min_score
            ],
        }

    def _analyze_task_gaps(self, use_cases: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze gaps in tasks between use cases."""
        # Similar to method gaps
        all_tasks = set()
        task_usage = {}

        for uc in use_cases:
            uc_id = uc.get("use_case_id")
            tasks = set(uc.get("tasks", []))
            all_tasks.update(tasks)
            task_usage[uc_id] = tasks

        gaps = {}
        for uc in use_cases:
            uc_id = uc.get("use_case_id")
            missing = all_tasks - task_usage[uc_id]
            if missing:
                gaps[uc_id] = list(missing)

        return {
            "total_tasks": len(all_tasks),
            "gaps_by_use_case": gaps,
            "task_diversity": len(all_tasks) / len(use_cases) if use_cases else 0,
        }

    def _analyze_implementation_gaps(
        self, use_cases: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Analyze implementation detail gaps."""
        has_narrative = []
        has_challenges = []
        has_kpis = []

        for uc in use_cases:
            uc_id = uc.get("use_case_id")

            if uc.get("narrative"):
                has_narrative.append(uc_id)
            if uc.get("challenges"):
                has_challenges.append(uc_id)
            if uc.get("kpis"):
                has_kpis.append(uc_id)

        total = len(use_cases)

        return {
            "documentation_completeness": {
                "narrative": len(has_narrative) / total if total > 0 else 0,
                "challenges": len(has_challenges) / total if total > 0 else 0,
                "kpis": len(has_kpis) / total if total > 0 else 0,
            },
            "missing_documentation": {
                "narrative": [
                    uc.get("use_case_id") for uc in use_cases if not uc.get("narrative")
                ],
                "challenges": [
                    uc.get("use_case_id")
                    for uc in use_cases
                    if not uc.get("challenges")
                ],
                "kpis": [
                    uc.get("use_case_id") for uc in use_cases if not uc.get("kpis")
                ],
            },
        }

    def _generate_gap_recommendations(self, gaps: Dict[str, Any]) -> List[str]:
        """Generate recommendations based on gap analysis."""
        recommendations = []

        # Method gap recommendations
        method_gaps = gaps.get("method_gaps", {})
        if method_gaps.get("gaps_by_use_case"):
            recommendations.append(
                "Consider cross-pollination of AI methods between use cases to improve coverage"
            )

        # Maturity gap recommendations
        maturity_gaps = gaps.get("maturity_gaps", {})
        if maturity_gaps.get("gap", 0) > 2:
            recommendations.append(
                "Significant maturity gap detected. Consider knowledge transfer from mature to less mature implementations"
            )

        # Documentation recommendations
        impl_gaps = gaps.get("implementation_gaps", {})
        doc_complete = impl_gaps.get("documentation_completeness", {})

        if doc_complete.get("narrative", 1) < 0.5:
            recommendations.append(
                "Many use cases lack narrative descriptions. Adding narratives would improve understanding"
            )

        if doc_complete.get("kpis", 1) < 0.5:
            recommendations.append(
                "KPIs are missing for many use cases. Define success metrics for better evaluation"
            )

        return recommendations

    def _get_top_items(self, items: List[str], n: int) -> List[Tuple[str, int]]:
        """Get top N most frequent items."""
        counts = {}
        for item in items:
            counts[item] = counts.get(item, 0) + 1

        return sorted(counts.items(), key=lambda x: x[1], reverse=True)[:n]

    def _find_cross_domain_methods(self, domains: List[str]) -> Dict[str, List[str]]:
        """Find methods used across multiple domains."""
        method_domains = {}

        for domain in domains:
            use_cases = self.indexer.filter_by_domain(domain)

            for uc in use_cases:
                for method in uc.get("ai_methods", []):
                    if method not in method_domains:
                        method_domains[method] = set()
                    method_domains[method].add(domain)

        # Filter methods used in multiple domains
        cross_domain = {
            method: list(domains_set)
            for method, domains_set in method_domains.items()
            if len(domains_set) > 1
        }

        return cross_domain

    def _analyze_domain_specialization(
        self, domain_comparison: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Analyze which domains specialize in specific methods."""
        # Find methods that are predominantly used in specific domains
        method_specialization = {}

        # Collect all methods and their domain usage
        method_domain_counts = {}

        for domain, info in domain_comparison.items():
            for method, count in info.get("top_methods", []):
                if method not in method_domain_counts:
                    method_domain_counts[method] = {}
                method_domain_counts[method][domain] = count

        # Find specialized methods (used primarily in one domain)
        for method, domain_counts in method_domain_counts.items():
            total = sum(domain_counts.values())
            for domain, count in domain_counts.items():
                if count / total > 0.6:  # 60% threshold for specialization
                    if domain not in method_specialization:
                        method_specialization[domain] = []
                    method_specialization[domain].append(method)

        return method_specialization

    def _compare_domain_maturity(
        self, domain_comparison: Dict[str, Any]
    ) -> List[Tuple[str, float]]:
        """Compare domains by maturity metrics."""
        maturity_scores = []

        for domain, info in domain_comparison.items():
            # Calculate weighted maturity score
            maturity_dist = info.get("maturity_distribution", {})
            weights = {
                "Research": 1,
                "listed_only": 1,
                "PoC": 2,
                "Pilot": 3,
                "Production": 4,
            }

            total_score = 0
            total_count = 0

            for status, count in maturity_dist.items():
                weight = weights.get(status, 1)
                total_score += weight * count
                total_count += count

            avg_maturity = total_score / total_count if total_count > 0 else 0
            maturity_scores.append((domain, round(avg_maturity, 2)))

        return sorted(maturity_scores, key=lambda x: x[1], reverse=True)

    def _format_as_table(self, results: Dict[str, Any], comparison_type: str) -> str:
        """Format results as a table."""
        # This would ideally use a table formatting library
        # For now, simple text formatting

        if comparison_type == "direct":
            lines = ["Use Case Comparison Table", "=" * 50]

            # Header
            use_cases = results.get("use_cases", [])
            if use_cases:
                lines.append(
                    f"{'Criterion':<20} | "
                    + " | ".join(f"UC {uc['id']}" for uc in use_cases)
                )
                lines.append("-" * 50)

                # Rows
                for criterion, data in results.get("criteria_comparison", {}).items():
                    values = data.get("values", {})
                    row = f"{criterion:<20} | "

                    for uc in use_cases:
                        value = values.get(uc["id"], "N/A")
                        if isinstance(value, list):
                            value = f"[{len(value)} items]"
                        row += f"{str(value)[:10]:<10} | "

                    lines.append(row)

            return "\n".join(lines)

        return "Table format not implemented for this comparison type"

    def _generate_report(self, results: Dict[str, Any], comparison_type: str) -> str:
        """Generate a comprehensive comparison report."""
        lines = [
            "# AI Use Case Comparison Report",
            f"## Comparison Type: {comparison_type}",
            "",
        ]

        if comparison_type == "direct":
            # Summary
            use_cases = results.get("use_cases", [])
            lines.append(f"### Comparing {len(use_cases)} use cases")

            for uc in use_cases:
                lines.append(
                    f"- **{uc['name']}** (ID: {uc['id']}, Domain: {uc['domain']})"
                )

            lines.append("")

            # Commonalities
            common = results.get("commonalities", {})
            lines.append("### Commonalities")

            if common.get("common_methods"):
                lines.append(
                    f"- **Shared AI Methods:** {', '.join(common['common_methods'])}"
                )
            if common.get("common_tasks"):
                lines.append(f"- **Shared Tasks:** {', '.join(common['common_tasks'])}")
            if common.get("same_domain"):
                lines.append(f"- **All in same domain:** {common['domain']}")

            lines.append("")

            # Differences
            diff = results.get("differences", {})
            lines.append("### Key Differences")

            if diff.get("domains") and len(diff["domains"]) > 1:
                lines.append(f"- **Domains represented:** {', '.join(diff['domains'])}")
            if diff.get("statuses") and len(diff["statuses"]) > 1:
                lines.append(f"- **Status variance:** {', '.join(diff['statuses'])}")

            # Unique methods
            if diff.get("unique_methods"):
                lines.append("- **Unique methods by use case:**")
                for uc_id, methods in diff["unique_methods"].items():
                    lines.append(f"  - UC {uc_id}: {', '.join(methods)}")

        elif comparison_type == "gap_analysis":
            lines.append("### Gap Analysis Results")

            # Method gaps
            method_gaps = results.get("method_gaps", {})
            if method_gaps:
                lines.append(
                    f"- **Total unique methods:** {method_gaps.get('total_methods', 0)}"
                )
                lines.append("- **Method coverage by use case:**")

                for uc_id, coverage in method_gaps.get("coverage", {}).items():
                    lines.append(f"  - UC {uc_id}: {coverage:.1%}")

            # Recommendations
            if recommendations := results.get("recommendations"):
                lines.append("\n### Recommendations")
                for rec in recommendations:
                    lines.append(f"- {rec}")

        return "\n".join(lines)

    def get_parameters(self) -> Dict[str, NodeParameter]:
        """Get required parameters for the node."""
        return {
            "comparison_type": NodeParameter(
                name="comparison_type",
                type=str,
                required=False,  # Make it optional with default
                default="direct",
                description="Type of comparison to perform (direct, similarity, gap_analysis, domain_comparison)",
            ),
            "use_case_ids": NodeParameter(
                name="use_case_ids",
                type=list,  # Use list instead of List[int]
                required=False,
                default=[],
                description="IDs of use cases to compare",
            ),
            "base_id": NodeParameter(
                name="base_id",
                type=int,
                required=False,
                default=None,
                description="Base use case ID for similarity comparison",
            ),
            "domains": NodeParameter(
                name="domains",
                type=list,  # Use list instead of List[str]
                required=False,
                default=[],
                description="Domains to compare",
            ),
            "comparison_criteria": NodeParameter(
                name="comparison_criteria",
                type=list,  # Use list instead of List[str]
                required=False,
                default=["domain", "ai_methods", "tasks", "status", "challenges"],
                description="Specific criteria to compare",
            ),
            "output_format": NodeParameter(
                name="output_format",
                type=str,
                required=False,
                default="json",
                description="Output format (json, table, report)",
            ),
        }

    def get_config_schema(self) -> Dict[str, Any]:
        """Get configuration schema for the node."""
        return {
            "type": "object",
            "properties": {
                "similarity_weights": {
                    "type": "object",
                    "description": "Weights for similarity calculation",
                    "properties": {
                        "domain": {"type": "number", "default": 0.3},
                        "methods": {"type": "number", "default": 0.3},
                        "tasks": {"type": "number", "default": 0.25},
                        "status": {"type": "number", "default": 0.15},
                    },
                },
                "specialization_threshold": {
                    "type": "number",
                    "description": "Threshold for domain specialization",
                    "default": 0.6,
                    "minimum": 0.0,
                    "maximum": 1.0,
                },
            },
        }
