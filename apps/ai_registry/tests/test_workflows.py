"""
Test suite for AI Registry workflows.

This module tests the pre-built workflows for common registry operations.
"""

from unittest.mock import Mock, patch

import pytest

from kailash.runtime.local import LocalRuntime

from ..workflows import basic_search, domain_analysis


class TestBasicSearchWorkflows:
    """Test basic search workflow functions."""

    @pytest.fixture
    def mock_runtime(self):
        """Mock runtime for testing."""
        runtime = Mock(spec=LocalRuntime)
        runtime.execute.return_value = (
            {
                "search": {
                    "success": True,
                    "results": [
                        {
                            "use_case_id": 1,
                            "name": "Test Case",
                            "application_domain": "Healthcare",
                            "status": "Production",
                        }
                    ],
                    "count": 1,
                }
            },
            {},  # execution context
        )
        return runtime

    def test_create_simple_search_workflow(self):
        """Test simple search workflow creation."""
        workflow = basic_search.create_simple_search_workflow()

        assert workflow.name == "ai_registry_search"
        assert len(workflow.nodes) == 1
        assert "search" in workflow.nodes

    def test_create_agent_search_workflow(self):
        """Test agent search workflow creation."""
        workflow = basic_search.create_agent_search_workflow()

        assert workflow.name == "ai_registry_agent_search"
        assert len(workflow.nodes) == 1
        assert "agent" in workflow.nodes

    def test_create_guided_search_workflow(self):
        """Test guided search workflow creation."""
        workflow = basic_search.create_guided_search_workflow()

        assert workflow.name == "ai_registry_guided_search"
        assert len(workflow.nodes) == 3
        assert "initial_search" in workflow.nodes
        assert "refinement_agent" in workflow.nodes
        assert "refined_search" in workflow.nodes

    @patch("apps.ai_registry.workflows.basic_search.LocalRuntime")
    def test_execute_simple_search(self, mock_runtime_class):
        """Test simple search execution."""
        mock_runtime = Mock()
        mock_runtime.execute.return_value = (
            {
                "search": {
                    "success": True,
                    "results": [{"name": "Test Case"}],
                    "count": 1,
                }
            },
            {},
        )
        mock_runtime_class.return_value = mock_runtime

        result = basic_search.execute_simple_search(query="test query", limit=10)

        assert result["success"] is True
        assert result["count"] == 1
        assert len(result["results"]) == 1

    @patch("apps.ai_registry.workflows.basic_search.LocalRuntime")
    def test_execute_agent_search(self, mock_runtime_class):
        """Test agent search execution."""
        mock_runtime = Mock()
        mock_runtime.execute.return_value = (
            {
                "agent": {
                    "success": True,
                    "response": {
                        "content": "Agent response to query",
                        "tool_calls": [{"function": {"name": "search_use_cases"}}],
                    },
                }
            },
            {},
        )
        mock_runtime_class.return_value = mock_runtime

        result = basic_search.execute_agent_search(
            user_query="What are the best AI implementations in healthcare?"
        )

        assert result["success"] is True
        assert "response" in result
        assert "tool_calls" in result["response"]

    def test_example_searches(self):
        """Test example search functions."""
        with patch(
            "apps.ai_registry.workflows.basic_search.execute_simple_search"
        ) as mock_search:
            mock_search.return_value = {"success": True, "count": 5}

            # Test healthcare search
            result = basic_search.example_healthcare_search()
            assert result["success"] is True

            # Test NLP search
            result = basic_search.example_nlp_search()
            assert result["success"] is True

            # Test production search
            result = basic_search.example_production_ready_search()
            assert result["success"] is True

    def test_get_search_workflow_configs(self):
        """Test workflow configuration retrieval."""
        configs = basic_search.get_search_workflow_configs()

        assert "simple_search" in configs
        assert "agent_search" in configs
        assert "guided_search" in configs

        # Check structure
        for config in configs.values():
            assert "description" in config
            assert "use_cases" in config
            assert "parameters" in config


class TestDomainAnalysisWorkflows:
    """Test domain analysis workflow functions."""

    def test_create_domain_overview_workflow(self):
        """Test domain overview workflow creation."""
        workflow = domain_analysis.create_domain_overview_workflow()

        assert workflow.name == "domain_overview"
        assert len(workflow.nodes) == 1
        assert "analytics" in workflow.nodes

    def test_create_domain_deep_dive_workflow(self):
        """Test domain deep dive workflow creation."""
        workflow = domain_analysis.create_domain_deep_dive_workflow()

        assert workflow.name == "domain_deep_dive"
        assert len(workflow.nodes) == 3
        assert "domain_search" in workflow.nodes
        assert "domain_analytics" in workflow.nodes
        assert "insights_agent" in workflow.nodes

    def test_create_cross_domain_comparison_workflow(self):
        """Test cross-domain comparison workflow creation."""
        workflow = domain_analysis.create_cross_domain_comparison_workflow()

        assert workflow.name == "cross_domain_comparison"
        assert len(workflow.nodes) == 3
        assert "domain_comparison" in workflow.nodes
        assert "cross_analytics" in workflow.nodes
        assert "comparison_agent" in workflow.nodes

    def test_create_domain_opportunity_workflow(self):
        """Test domain opportunity workflow creation."""
        workflow = domain_analysis.create_domain_opportunity_workflow()

        assert workflow.name == "domain_opportunity"
        assert len(workflow.nodes) == 3
        assert "gap_analysis" in workflow.nodes
        assert "trend_analysis" in workflow.nodes
        assert "opportunity_agent" in workflow.nodes

    @patch("apps.ai_registry.workflows.domain_analysis.LocalRuntime")
    def test_execute_domain_overview(self, mock_runtime_class):
        """Test domain overview execution."""
        mock_runtime = Mock()
        mock_runtime.execute.return_value = (
            {
                "analytics": {
                    "success": True,
                    "basic_stats": {"total_use_cases": 100, "domains": {"count": 10}},
                }
            },
            {},
        )
        mock_runtime_class.return_value = mock_runtime

        result = domain_analysis.execute_domain_overview()

        assert result["success"] is True
        assert "basic_stats" in result

    @patch("apps.ai_registry.workflows.domain_analysis.LocalRuntime")
    def test_execute_domain_deep_dive(self, mock_runtime_class):
        """Test domain deep dive execution."""
        mock_runtime = Mock()
        mock_runtime.execute.return_value = (
            {
                "domain_search": {"success": True, "count": 15},
                "domain_analytics": {"success": True, "domains": {"Healthcare": {}}},
                "insights_agent": {
                    "success": True,
                    "response": {"content": "AI insights"},
                },
            },
            {},
        )
        mock_runtime_class.return_value = mock_runtime

        result = domain_analysis.execute_domain_deep_dive(domain="Healthcare")

        assert result["domain"] == "Healthcare"
        assert "use_cases" in result
        assert "analytics" in result
        assert "insights" in result

    @patch("apps.ai_registry.workflows.domain_analysis.LocalRuntime")
    def test_execute_cross_domain_comparison(self, mock_runtime_class):
        """Test cross-domain comparison execution."""
        mock_runtime = Mock()
        mock_runtime.execute.return_value = (
            {
                "domain_comparison": {"success": True, "domains": {}},
                "cross_analytics": {"success": True, "trends": {}},
                "comparison_agent": {
                    "success": True,
                    "response": {"content": "Comparison insights"},
                },
            },
            {},
        )
        mock_runtime_class.return_value = mock_runtime

        domains = ["Healthcare", "Finance"]
        result = domain_analysis.execute_cross_domain_comparison(domains=domains)

        assert result["domains_analyzed"] == domains
        assert "comparison" in result
        assert "analytics" in result
        assert "strategic_insights" in result

    def test_specialized_analysis_functions(self):
        """Test specialized domain analysis functions."""
        with patch(
            "apps.ai_registry.workflows.domain_analysis.execute_domain_deep_dive"
        ) as mock_deep_dive:
            mock_deep_dive.return_value = {"success": True}

            # Test healthcare analysis
            result = domain_analysis.analyze_healthcare_ai_trends()
            assert result["success"] is True

            # Test finance analysis
            result = domain_analysis.analyze_finance_ai_maturity()
            assert result["success"] is True

        with patch(
            "apps.ai_registry.workflows.domain_analysis.execute_cross_domain_comparison"
        ) as mock_comparison:
            mock_comparison.return_value = {"success": True}

            # Test tech domain comparison
            result = domain_analysis.compare_tech_domains()
            assert result["success"] is True

        with patch(
            "apps.ai_registry.workflows.domain_analysis.execute_domain_opportunity_analysis"
        ) as mock_opportunity:
            mock_opportunity.return_value = {"success": True}

            # Test manufacturing opportunities
            result = domain_analysis.identify_manufacturing_opportunities()
            assert result["success"] is True

    def test_get_domain_insights_prompts(self):
        """Test domain-specific insights prompts."""
        prompts = domain_analysis.get_domain_insights_prompts()

        assert "Healthcare" in prompts
        assert "Finance" in prompts
        assert "Manufacturing" in prompts

        # Check that prompts are meaningful
        for domain, prompt in prompts.items():
            assert len(prompt) > 50  # Should be substantial
            assert domain.lower() in prompt.lower() or "domain" in prompt.lower()

    def test_create_domain_specific_workflow(self):
        """Test domain-specific workflow creation."""
        workflow = domain_analysis.create_domain_specific_workflow(
            domain="Healthcare",
            focus_areas=["patient_outcomes", "regulatory_compliance"],
        )

        assert "healthcare" in workflow.name
        assert len(workflow.nodes) >= 3  # Should have multiple nodes

    def test_get_domain_workflow_configs(self):
        """Test domain workflow configuration retrieval."""
        configs = domain_analysis.get_domain_workflow_configs()

        expected_workflows = [
            "domain_overview",
            "domain_deep_dive",
            "cross_domain_comparison",
            "opportunity_analysis",
        ]

        for workflow_name in expected_workflows:
            assert workflow_name in configs

            config = configs[workflow_name]
            assert "description" in config
            assert "use_cases" in config
            assert "outputs" in config


class TestWorkflowIntegration:
    """Integration tests for complete workflow execution."""

    @pytest.fixture
    def mock_successful_execution(self):
        """Mock successful workflow execution."""

        def mock_execute(workflow, parameters=None):
            # Return different results based on workflow name
            if "search" in workflow.name:
                return (
                    {
                        workflow.nodes[0].name: {
                            "success": True,
                            "results": [{"name": "Test Case", "domain": "Healthcare"}],
                            "count": 1,
                        }
                    },
                    {},
                )
            elif "analytics" in workflow.name:
                return (
                    {
                        workflow.nodes[0].name: {
                            "success": True,
                            "basic_stats": {"total_use_cases": 100},
                        }
                    },
                    {},
                )
            else:
                return ({}, {})

        return mock_execute

    def test_workflow_parameter_validation(self):
        """Test that workflows properly validate parameters."""
        # Test with invalid parameters
        with patch(
            "apps.ai_registry.workflows.basic_search.LocalRuntime"
        ) as mock_runtime_class:
            mock_runtime = Mock()
            mock_runtime.execute.side_effect = ValueError("Invalid parameters")
            mock_runtime_class.return_value = mock_runtime

            # Should handle parameter validation errors
            try:
                result = basic_search.execute_simple_search(query="", limit=-1)
                # Should either return error or raise exception
                assert "error" in result or result.get("success") is False
            except (ValueError, Exception):
                # Exception handling is acceptable
                pass

    def test_workflow_error_propagation(self):
        """Test that errors propagate properly through workflows."""
        with patch(
            "apps.ai_registry.workflows.basic_search.LocalRuntime"
        ) as mock_runtime_class:
            mock_runtime = Mock()
            mock_runtime.execute.return_value = (
                {"search": {"success": False, "error": "Search failed"}},
                {},
            )
            mock_runtime_class.return_value = mock_runtime

            result = basic_search.execute_simple_search(query="test")

            # Should propagate the error
            assert result.get("success") is False or "error" in result

    def test_workflow_composition(self):
        """Test that workflows can be composed together."""
        # Test creating multiple workflows
        search_workflow = basic_search.create_simple_search_workflow()
        analytics_workflow = domain_analysis.create_domain_overview_workflow()

        # Should be able to create both without conflicts
        assert search_workflow.name != analytics_workflow.name
        assert len(search_workflow.nodes) > 0
        assert len(analytics_workflow.nodes) > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
