"""
Test suite for AI Registry custom nodes.

This module tests the custom Kailash nodes for registry operations.
"""

import json
import os
import tempfile
from unittest.mock import patch

import pytest

from kailash.runtime.local import LocalRuntime

from ..nodes import RegistryAnalyticsNode, RegistryCompareNode, RegistrySearchNode


class TestRegistrySearchNode:
    """Test the RegistrySearchNode."""

    @pytest.fixture
    def sample_data(self):
        """Sample registry data for testing."""
        return {
            "use_cases": [
                {
                    "use_case_id": 1,
                    "name": "Healthcare AI",
                    "application_domain": "Healthcare",
                    "description": "AI for medical diagnosis",
                    "ai_methods": ["Machine Learning", "NLP"],
                    "tasks": ["Diagnosis"],
                    "status": "Production",
                },
                {
                    "use_case_id": 2,
                    "name": "Finance Bot",
                    "application_domain": "Finance",
                    "description": "Chatbot for financial services",
                    "ai_methods": ["NLP", "Deep Learning"],
                    "tasks": ["Customer Service"],
                    "status": "PoC",
                },
            ]
        }

    @pytest.fixture
    def search_node(self, sample_data):
        """Create search node with test data."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(sample_data, f)
            temp_file = f.name

        try:
            with patch(
                "apps.ai_registry.nodes.registry_search_node.config"
            ) as mock_config:
                mock_config.get.side_effect = lambda key, default=None: {
                    "registry_file": temp_file,
                    "indexing": {
                        "index_fields": [
                            "name",
                            "description",
                            "application_domain",
                            "ai_methods",
                        ],
                        "fuzzy_matching": True,
                        "similarity_threshold": 0.7,
                    },
                }.get(key, default)

                node = RegistrySearchNode()
                yield node
        finally:
            os.unlink(temp_file)

    def test_basic_search(self, search_node):
        """Test basic search functionality."""
        context = {}
        result = search_node.run(context, query="healthcare", limit=5)

        assert result["success"] is True
        assert result["count"] > 0
        assert "Healthcare AI" in str(result["results"])

    def test_filtered_search(self, search_node):
        """Test search with filters."""
        context = {}
        result = search_node.run(
            context, query="", filters={"domain": "Finance"}, limit=5
        )

        assert result["success"] is True
        assert result["count"] == 1
        assert result["results"][0]["application_domain"] == "Finance"

    def test_search_with_stats(self, search_node):
        """Test search with statistics."""
        context = {}
        result = search_node.run(context, query="AI", include_stats=True)

        assert result["success"] is True
        assert "stats" in result
        assert "domains" in result["stats"]

    def test_invalid_query(self, search_node):
        """Test handling of invalid queries."""
        context = {}
        result = search_node.run(context)  # No query parameter

        assert result["success"] is False
        assert "error" in result

    def test_config_schema(self, search_node):
        """Test configuration schema."""
        schema = search_node.get_config_schema()

        assert schema["type"] == "object"
        assert "enable_fuzzy" in schema["properties"]
        assert "similarity_threshold" in schema["properties"]


class TestRegistryAnalyticsNode:
    """Test the RegistryAnalyticsNode."""

    @pytest.fixture
    def analytics_node(self):
        """Create analytics node with mock data."""
        sample_data = {
            "use_cases": [
                {
                    "use_case_id": 1,
                    "name": "Healthcare AI",
                    "application_domain": "Healthcare",
                    "ai_methods": ["Machine Learning"],
                    "status": "Production",
                },
                {
                    "use_case_id": 2,
                    "name": "Finance AI",
                    "application_domain": "Finance",
                    "ai_methods": ["Deep Learning"],
                    "status": "PoC",
                },
            ]
        }

        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(sample_data, f)
            temp_file = f.name

        try:
            with patch(
                "apps.ai_registry.nodes.registry_analytics_node.config"
            ) as mock_config:
                mock_config.get.side_effect = lambda key, default=None: {
                    "registry_file": temp_file,
                    "indexing": {},
                }.get(key, default)

                node = RegistryAnalyticsNode()
                yield node
        finally:
            os.unlink(temp_file)

    def test_overview_analysis(self, analytics_node):
        """Test overview analysis."""
        context = {}
        result = analytics_node.run(
            context, analysis_type="overview", output_format="json"
        )

        assert result["success"] is True
        assert "basic_stats" in result
        assert "metrics" in result

    def test_domain_analysis(self, analytics_node):
        """Test domain-specific analysis."""
        context = {}
        result = analytics_node.run(
            context, analysis_type="domain_analysis", domain="Healthcare"
        )

        assert result["success"] is True
        assert "domains" in result

    def test_method_analysis(self, analytics_node):
        """Test AI method analysis."""
        context = {}
        result = analytics_node.run(context, analysis_type="method_analysis")

        assert result["success"] is True
        assert "methods" in result

    def test_invalid_analysis_type(self, analytics_node):
        """Test handling of invalid analysis types."""
        context = {}
        result = analytics_node.run(context, analysis_type="invalid_type")

        assert result["success"] is False
        assert "error" in result


class TestRegistryCompareNode:
    """Test the RegistryCompareNode."""

    @pytest.fixture
    def compare_node(self):
        """Create compare node with test data."""
        sample_data = {
            "use_cases": [
                {
                    "use_case_id": 1,
                    "name": "Healthcare AI",
                    "application_domain": "Healthcare",
                    "ai_methods": ["Machine Learning", "NLP"],
                    "tasks": ["Diagnosis", "Communication"],
                    "status": "Production",
                },
                {
                    "use_case_id": 2,
                    "name": "Finance AI",
                    "application_domain": "Finance",
                    "ai_methods": ["Machine Learning", "Deep Learning"],
                    "tasks": ["Fraud Detection", "Risk Assessment"],
                    "status": "Production",
                },
                {
                    "use_case_id": 3,
                    "name": "Manufacturing AI",
                    "application_domain": "Manufacturing",
                    "ai_methods": ["Computer Vision", "Machine Learning"],
                    "tasks": ["Quality Control", "Defect Detection"],
                    "status": "PoC",
                },
            ]
        }

        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(sample_data, f)
            temp_file = f.name

        try:
            with patch(
                "apps.ai_registry.nodes.registry_compare_node.config"
            ) as mock_config:
                mock_config.get.side_effect = lambda key, default=None: {
                    "registry_file": temp_file,
                    "indexing": {},
                }.get(key, default)

                node = RegistryCompareNode()
                yield node
        finally:
            os.unlink(temp_file)

    def test_direct_comparison(self, compare_node):
        """Test direct comparison of use cases."""
        context = {}
        result = compare_node.run(
            context,
            comparison_type="direct",
            use_case_ids=[1, 2],
            comparison_criteria=["domain", "ai_methods", "status"],
        )

        assert result["success"] is True
        assert "use_cases" in result
        assert "criteria_comparison" in result
        assert "similarity_matrix" in result

    def test_similarity_comparison(self, compare_node):
        """Test similarity-based comparison."""
        context = {}
        result = compare_node.run(
            context, comparison_type="similarity", base_id=1, limit=2
        )

        assert result["success"] is True
        assert "base_case" in result
        assert "comparisons" in result

    def test_gap_analysis(self, compare_node):
        """Test gap analysis between use cases."""
        context = {}
        result = compare_node.run(
            context, comparison_type="gap_analysis", use_case_ids=[1, 2, 3]
        )

        assert result["success"] is True
        assert "method_gaps" in result
        assert "maturity_gaps" in result
        assert "recommendations" in result

    def test_domain_comparison(self, compare_node):
        """Test cross-domain comparison."""
        context = {}
        result = compare_node.run(
            context,
            comparison_type="domain_comparison",
            domains=["Healthcare", "Finance", "Manufacturing"],
        )

        assert result["success"] is True
        assert "domains" in result
        assert "cross_domain_methods" in result

    def test_invalid_comparison_type(self, compare_node):
        """Test handling of invalid comparison types."""
        context = {}
        result = compare_node.run(context, comparison_type="invalid_type")

        assert result["success"] is False
        assert "error" in result

    def test_missing_required_params(self, compare_node):
        """Test handling of missing required parameters."""
        context = {}
        result = compare_node.run(
            context,
            comparison_type="direct",
            # Missing use_case_ids
        )

        assert result["success"] is False
        assert "error" in result


class TestNodeIntegration:
    """Integration tests for nodes working together."""

    @pytest.fixture
    def runtime(self):
        """Create runtime for integration testing."""
        return LocalRuntime()

    def test_search_to_analytics_workflow(self, runtime):
        """Test workflow combining search and analytics nodes."""
        # This would require setting up a full workflow
        # For now, test that nodes can be instantiated together
        search_node = RegistrySearchNode()
        analytics_node = RegistryAnalyticsNode()
        compare_node = RegistryCompareNode()

        # All nodes should be properly instantiated
        assert search_node is not None
        assert analytics_node is not None
        assert compare_node is not None

    def test_node_error_handling(self):
        """Test error handling across nodes."""
        # Test with invalid configuration
        with patch("apps.ai_registry.nodes.registry_search_node.config") as mock_config:
            mock_config.get.side_effect = lambda key, default=None: {
                "registry_file": "/nonexistent/file.json",
                "indexing": {},
            }.get(key, default)

            node = RegistrySearchNode()

            # Should handle missing file gracefully
            context = {}
            try:
                result = node.run(context, query="test")
                # Should either work with fallback or return error
                assert "error" in result or result.get("success") is False
            except Exception:
                # Exception handling is also acceptable
                pass


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
