"""
Efficient data indexing for AI Registry.

This module provides indexing capabilities for the 187 AI use cases,
enabling fast searches and queries across multiple fields.
"""

import json
import logging
import re
from collections import defaultdict
from difflib import SequenceMatcher
from typing import Any, Dict, List, Optional, Set, Tuple

logger = logging.getLogger(__name__)


class RegistryIndexer:
    """Index AI Registry data for efficient searching."""

    def __init__(self, config: Dict[str, Any]):
        """
        Initialize the indexer.

        Args:
            config: Indexing configuration
        """
        self.config = config
        self.index_fields = config.get(
            "index_fields",
            [
                "name",
                "description",
                "narrative",
                "application_domain",
                "ai_methods",
                "tasks",
            ],
        )
        self.fuzzy_matching = config.get("fuzzy_matching", True)
        self.similarity_threshold = config.get("similarity_threshold", 0.7)

        # Data storage
        self.use_cases: List[Dict[str, Any]] = []
        self.stats: Optional[Dict[str, Any]] = None

        # Search indexes
        self.text_index: Dict[str, Set[int]] = defaultdict(set)
        self.domain_index: Dict[str, Set[int]] = defaultdict(set)
        self.method_index: Dict[str, Set[int]] = defaultdict(set)
        self.status_index: Dict[str, Set[int]] = defaultdict(set)

    def load_and_index(self, registry_file: str):
        """
        Load registry data from JSON file and build search indexes.

        Args:
            registry_file: Path to the registry JSON file
        """
        try:
            with open(registry_file, "r") as f:
                data = json.load(f)

            # Extract use cases
            if isinstance(data, dict) and "use_cases" in data:
                self.use_cases = data["use_cases"]
            elif isinstance(data, list):
                self.use_cases = data
            else:
                raise ValueError("Invalid registry file format")

            # Build search indexes
            self._build_indexes()

            # Generate statistics
            self.stats = self._generate_statistics()

            logger.info(f"Loaded and indexed {len(self.use_cases)} use cases")

        except Exception as e:
            logger.error(f"Error loading registry: {e}")
            raise

    def _build_indexes(self):
        """Build search indexes for efficient querying."""
        for idx, use_case in enumerate(self.use_cases):
            # Text index for full-text search
            text_content = self._extract_text_content(use_case)
            words = self._tokenize(text_content)

            for word in words:
                self.text_index[word.lower()].add(idx)

            # Domain index
            domain = use_case.get("application_domain", "")
            if domain:
                self.domain_index[domain].add(idx)

            # AI methods index
            methods = use_case.get("ai_methods", [])
            if isinstance(methods, list):
                for method in methods:
                    self.method_index[method].add(idx)

            # Status index
            status = use_case.get("status", "")
            if status:
                self.status_index[status].add(idx)

    def _extract_text_content(self, use_case: Dict[str, Any]) -> str:
        """Extract searchable text from a use case."""
        text_parts = []

        for field in self.index_fields:
            value = use_case.get(field, "")
            if isinstance(value, str):
                text_parts.append(value)
            elif isinstance(value, list):
                text_parts.extend(str(item) for item in value)

        return " ".join(text_parts)

    def _tokenize(self, text: str) -> List[str]:
        """Tokenize text for indexing."""
        # Remove special characters and split on whitespace
        text = re.sub(r"[^\w\s]", " ", text)
        words = text.split()

        # Filter out very short words
        return [word for word in words if len(word) > 2]

    def search(self, query: str, limit: int = 20) -> List[Dict[str, Any]]:
        """
        Search use cases using full-text search.

        Args:
            query: Search query
            limit: Maximum number of results

        Returns:
            List of matching use cases with relevance scores
        """
        if not query.strip():
            return []

        query_words = [word.lower() for word in self._tokenize(query)]
        if not query_words:
            return []

        # Find matching documents
        doc_scores = defaultdict(float)

        for word in query_words:
            # Exact matches
            if word in self.text_index:
                for doc_idx in self.text_index[word]:
                    doc_scores[doc_idx] += 1.0

            # Fuzzy matching if enabled
            if self.fuzzy_matching:
                for indexed_word in self.text_index:
                    similarity = SequenceMatcher(None, word, indexed_word).ratio()
                    if similarity >= self.similarity_threshold:
                        for doc_idx in self.text_index[indexed_word]:
                            doc_scores[doc_idx] += similarity * 0.8

        # Sort by relevance and return top results
        sorted_docs = sorted(doc_scores.items(), key=lambda x: x[1], reverse=True)
        results = []

        for doc_idx, score in sorted_docs[:limit]:
            use_case = self.use_cases[doc_idx].copy()
            use_case["_relevance_score"] = score
            results.append(use_case)

        return results

    def filter_by_domain(self, domain: str) -> List[Dict[str, Any]]:
        """Filter use cases by application domain."""
        if domain not in self.domain_index:
            return []

        results = []
        for idx in self.domain_index[domain]:
            results.append(self.use_cases[idx])

        return results

    def filter_by_ai_method(self, method: str) -> List[Dict[str, Any]]:
        """Filter use cases by AI method."""
        if method not in self.method_index:
            return []

        results = []
        for idx in self.method_index[method]:
            results.append(self.use_cases[idx])

        return results

    def filter_by_status(self, status: str) -> List[Dict[str, Any]]:
        """Filter use cases by implementation status."""
        if status not in self.status_index:
            return []

        results = []
        for idx in self.status_index[status]:
            results.append(self.use_cases[idx])

        return results

    def get_domains(self) -> List[str]:
        """Get all available domains."""
        return sorted(list(self.domain_index.keys()))

    def get_ai_methods(self) -> List[str]:
        """Get all AI methods, sorted by frequency."""
        method_counts = {
            method: len(indices) for method, indices in self.method_index.items()
        }
        return sorted(
            method_counts.keys(), key=lambda x: method_counts[x], reverse=True
        )

    def get_statuses(self) -> List[str]:
        """Get all implementation statuses."""
        return sorted(list(self.status_index.keys()))

    def find_similar_cases(
        self, use_case_id: int, limit: int = 5
    ) -> List[Dict[str, Any]]:
        """Find similar use cases based on AI methods and domain."""
        # Find the reference use case
        reference = None
        for uc in self.use_cases:
            if uc.get("use_case_id") == use_case_id:
                reference = uc
                break

        if not reference:
            return []

        # Calculate similarity scores
        ref_methods = set(reference.get("ai_methods", []))
        ref_domain = reference.get("application_domain", "")
        ref_tasks = set(reference.get("tasks", []))

        similarities = []

        for uc in self.use_cases:
            if uc.get("use_case_id") == use_case_id:
                continue  # Skip the reference case itself

            # Calculate similarity based on multiple factors
            uc_methods = set(uc.get("ai_methods", []))
            uc_domain = uc.get("application_domain", "")
            uc_tasks = set(uc.get("tasks", []))

            # Method similarity
            method_overlap = len(ref_methods & uc_methods)
            method_union = len(ref_methods | uc_methods)
            method_sim = method_overlap / method_union if method_union > 0 else 0

            # Domain similarity
            domain_sim = 1.0 if ref_domain == uc_domain else 0.0

            # Task similarity
            task_overlap = len(ref_tasks & uc_tasks)
            task_union = len(ref_tasks | uc_tasks)
            task_sim = task_overlap / task_union if task_union > 0 else 0

            # Combined similarity score
            similarity = (method_sim * 0.5) + (domain_sim * 0.3) + (task_sim * 0.2)

            if similarity > 0:
                uc_copy = uc.copy()
                uc_copy["_similarity_score"] = similarity
                similarities.append(uc_copy)

        # Sort by similarity and return top results
        similarities.sort(key=lambda x: x["_similarity_score"], reverse=True)
        return similarities[:limit]

    def get_statistics(self) -> Dict[str, Any]:
        """Get comprehensive statistics about the registry."""
        if self.stats is None:
            self.stats = self._generate_statistics()
        return self.stats

    def _generate_statistics(self) -> Dict[str, Any]:
        """Generate comprehensive statistics."""
        total_cases = len(self.use_cases)

        # Domain statistics
        domain_counts = {
            domain: len(indices) for domain, indices in self.domain_index.items()
        }
        sorted_domains = sorted(domain_counts.items(), key=lambda x: x[1], reverse=True)

        # AI method statistics
        method_counts = {
            method: len(indices) for method, indices in self.method_index.items()
        }
        sorted_methods = sorted(method_counts.items(), key=lambda x: x[1], reverse=True)

        # Status statistics
        status_counts = {
            status: len(indices) for status, indices in self.status_index.items()
        }

        # Task statistics
        all_tasks = set()
        for uc in self.use_cases:
            tasks = uc.get("tasks", [])
            if isinstance(tasks, list):
                all_tasks.update(tasks)

        return {
            "total_use_cases": total_cases,
            "domains": {
                "count": len(domain_counts),
                "top": [domain for domain, _ in sorted_domains[:10]],
                "distribution": domain_counts,
            },
            "ai_methods": {
                "count": len(method_counts),
                "top": [method for method, _ in sorted_methods[:10]],
                "distribution": method_counts,
            },
            "statuses": {
                "count": len(status_counts),
                "distribution": status_counts,
            },
            "tasks": {
                "count": len(all_tasks),
                "unique_tasks": sorted(list(all_tasks)),
            },
            "domain_distribution": domain_counts,
            "ai_method_distribution": method_counts,
            "status_distribution": status_counts,
        }
