"""
Domain analysis workflows for AI Registry.

This module provides workflows for analyzing AI implementations
across different application domains.
"""

from typing import Any, Dict, List, Optional

from kailash import Workflow
from kailash.nodes.ai import LLMAgentNode
from kailash.runtime.local import LocalRuntime

from ..nodes import RegistryAnalyticsNode, RegistryCompareNode, RegistrySearchNode


def create_domain_overview_workflow(workflow_name: str = "domain_overview") -> Workflow:
    """
    Create a workflow for comprehensive domain analysis.

    This workflow provides insights into AI implementations across domains,
    including distribution, maturity, and trending methods.

    Args:
        workflow_name: Name for the workflow

    Returns:
        Configured Workflow object
    """
    workflow = Workflow(workflow_name, "AI Registry Domain Overview")

    # Analytics node for domain analysis
    workflow.add_node("analytics", RegistryAnalyticsNode(name="domain_analytics"))

    return workflow


def create_domain_deep_dive_workflow(
    workflow_name: str = "domain_deep_dive",
) -> Workflow:
    """
    Create a workflow for deep analysis of a specific domain.

    This workflow provides detailed insights into a single domain,
    including use case examples, method distribution, and maturity analysis.

    Args:
        workflow_name: Name for the workflow

    Returns:
        Configured Workflow object
    """
    workflow = Workflow(workflow_name, "AI Registry Domain Deep Dive")

    # Search for domain use cases
    workflow.add_node("domain_search", RegistrySearchNode(name="domain_search"))

    # Analytics for domain specifics
    workflow.add_node(
        "domain_analytics", RegistryAnalyticsNode(name="domain_analytics")
    )

    # AI agent for insights generation
    workflow.add_node("insights_agent", LLMAgentNode(name="insights_agent"))

    # Connect nodes
    workflow.connect("domain_search", "insights_agent")
    workflow.connect("domain_analytics", "insights_agent")

    return workflow


def create_cross_domain_comparison_workflow(
    workflow_name: str = "cross_domain_comparison",
) -> Workflow:
    """
    Create a workflow for comparing AI implementations across domains.

    This workflow compares multiple domains to identify patterns,
    gaps, and opportunities for cross-domain learning.

    Args:
        workflow_name: Name for the workflow

    Returns:
        Configured Workflow object
    """
    workflow = Workflow(workflow_name, "Cross-Domain AI Comparison")

    # Compare multiple domains
    workflow.add_node(
        "domain_comparison", RegistryCompareNode(name="domain_comparison")
    )

    # Analytics for cross-domain insights
    workflow.add_node("cross_analytics", RegistryAnalyticsNode(name="cross_analytics"))

    # Agent for generating insights
    workflow.add_node("comparison_agent", LLMAgentNode(name="comparison_agent"))

    # Connect nodes
    workflow.connect("domain_comparison", "comparison_agent")
    workflow.connect("cross_analytics", "comparison_agent")

    return workflow


def create_domain_opportunity_workflow(
    workflow_name: str = "domain_opportunity",
) -> Workflow:
    """
    Create a workflow for identifying opportunities in domains.

    This workflow analyzes domains to identify gaps, emerging trends,
    and potential areas for new AI implementations.

    Args:
        workflow_name: Name for the workflow

    Returns:
        Configured Workflow object
    """
    workflow = Workflow(workflow_name, "Domain Opportunity Analysis")

    # Gap analysis
    workflow.add_node("gap_analysis", RegistryAnalyticsNode(name="gap_analysis"))

    # Trend analysis
    workflow.add_node("trend_analysis", RegistryAnalyticsNode(name="trend_analysis"))

    # Opportunity identification agent
    workflow.add_node("opportunity_agent", LLMAgentNode(name="opportunity_agent"))

    # Connect nodes
    workflow.connect("gap_analysis", "opportunity_agent")
    workflow.connect("trend_analysis", "opportunity_agent")

    return workflow


def execute_domain_overview(
    include_visualizations: bool = False,
    output_format: str = "json",
    runtime: Optional[LocalRuntime] = None,
) -> Dict[str, Any]:
    """
    Execute domain overview analysis.

    Args:
        include_visualizations: Whether to include visualization data
        output_format: Output format ('json', 'markdown', 'summary')
        runtime: Runtime to use (creates new if None)

    Returns:
        Domain overview analysis results
    """
    if runtime is None:
        runtime = LocalRuntime()

    workflow = create_domain_overview_workflow()

    parameters = {
        "analytics": {
            "analysis_type": "domain_analysis",
            "output_format": output_format,
            "include_visualizations": include_visualizations,
        }
    }

    results, _ = runtime.execute(workflow, parameters=parameters)
    return results.get("analytics", {})


def execute_domain_deep_dive(
    domain: str,
    provider: str = "ollama",
    model: str = "llama3.1:8b-instruct-q8_0",
    runtime: Optional[LocalRuntime] = None,
) -> Dict[str, Any]:
    """
    Execute deep dive analysis for a specific domain.

    Args:
        domain: Domain to analyze
        provider: LLM provider for insights
        model: LLM model for insights
        runtime: Runtime to use (creates new if None)

    Returns:
        Deep dive analysis results
    """
    if runtime is None:
        runtime = LocalRuntime()

    workflow = create_domain_deep_dive_workflow()

    parameters = {
        "domain_search": {
            "query": "",  # Empty query to get all in domain
            "filters": {"domain": domain},
            "limit": 50,
            "include_stats": True,
        },
        "domain_analytics": {
            "analysis_type": "domain_analysis",
            "domain": domain,
            "output_format": "json",
            "include_visualizations": True,
        },
        "insights_agent": {
            "provider": provider,
            "model": model,
            "messages": [
                {
                    "role": "system",
                    "content": f"""You are an AI domain analysis expert specializing in {domain}.

Analyze the provided data about AI implementations in {domain} and provide insights including:

1. **Key Patterns**: What are the dominant AI methods and tasks in this domain?
2. **Maturity Assessment**: How mature are the implementations? Are most still in PoC or have they reached production?
3. **Innovation Opportunities**: What gaps or opportunities do you see for new AI applications?
4. **Success Factors**: Based on the use cases, what factors seem to drive successful implementations?
5. **Challenges**: What common challenges appear across implementations?
6. **Future Trends**: What emerging trends can you identify?

Provide specific, actionable insights based on the data.""",
                }
            ],
        },
    }

    results, execution_context = runtime.execute(workflow, parameters=parameters)

    return {
        "domain": domain,
        "use_cases": results.get("domain_search", {}),
        "analytics": results.get("domain_analytics", {}),
        "insights": results.get("insights_agent", {}),
        "execution_context": execution_context,
    }


def execute_cross_domain_comparison(
    domains: List[str],
    provider: str = "ollama",
    model: str = "llama3.1:8b-instruct-q8_0",
    runtime: Optional[LocalRuntime] = None,
) -> Dict[str, Any]:
    """
    Execute cross-domain comparison analysis.

    Args:
        domains: List of domains to compare
        provider: LLM provider for insights
        model: LLM model for insights
        runtime: Runtime to use (creates new if None)

    Returns:
        Cross-domain comparison results
    """
    if runtime is None:
        runtime = LocalRuntime()

    workflow = create_cross_domain_comparison_workflow()

    parameters = {
        "domain_comparison": {
            "comparison_type": "domain_comparison",
            "domains": domains,
            "output_format": "json",
        },
        "cross_analytics": {
            "analysis_type": "domain_trends",
            "group_by": "domain",
        },
        "comparison_agent": {
            "provider": provider,
            "model": model,
            "messages": [
                {
                    "role": "system",
                    "content": f"""You are an AI strategy consultant analyzing AI adoption across multiple domains: {', '.join(domains)}.

Based on the comparison data provided, analyze:

1. **Leading Domains**: Which domains are most advanced in AI adoption?
2. **Method Convergence**: Which AI methods are being adopted across multiple domains?
3. **Maturity Gaps**: Which domains lag in implementation maturity and why?
4. **Cross-Pollination Opportunities**: What successful patterns from one domain could benefit others?
5. **Competitive Landscape**: How do domains compare in terms of innovation and production readiness?
6. **Strategic Recommendations**: What strategic moves should each domain consider?

Provide data-driven insights with specific examples and recommendations.""",
                }
            ],
        },
    }

    results, execution_context = runtime.execute(workflow, parameters=parameters)

    return {
        "domains_analyzed": domains,
        "comparison": results.get("domain_comparison", {}),
        "analytics": results.get("cross_analytics", {}),
        "strategic_insights": results.get("comparison_agent", {}),
        "execution_context": execution_context,
    }


def execute_domain_opportunity_analysis(
    domain: Optional[str] = None,
    provider: str = "ollama",
    model: str = "llama3.1:8b-instruct-q8_0",
    runtime: Optional[LocalRuntime] = None,
) -> Dict[str, Any]:
    """
    Execute opportunity analysis for a domain or across all domains.

    Args:
        domain: Specific domain to analyze (None for all domains)
        provider: LLM provider for insights
        model: LLM model for insights
        runtime: Runtime to use (creates new if None)

    Returns:
        Opportunity analysis results
    """
    if runtime is None:
        runtime = LocalRuntime()

    workflow = create_domain_opportunity_workflow()

    parameters = {
        "gap_analysis": {
            "analysis_type": "gap_analysis",
            "domain": domain,
            "output_format": "json",
        },
        "trend_analysis": {
            "analysis_type": "trend_analysis",
            "group_by": "domain" if not domain else "method",
        },
        "opportunity_agent": {
            "provider": provider,
            "model": model,
            "messages": [
                {
                    "role": "system",
                    "content": f"""You are an AI innovation strategist identifying opportunities in {'the ' + domain + ' domain' if domain else 'various domains'}.

Based on the gap and trend analysis provided, identify:

1. **Market Gaps**: What AI applications are underexplored or missing entirely?
2. **Emerging Opportunities**: What trends suggest new AI application areas?
3. **Low-Hanging Fruit**: What proven AI methods could be applied to new problems?
4. **Innovation Potential**: Where do you see the highest potential for breakthrough applications?
5. **Implementation Readiness**: Which opportunities are most ready for development?
6. **Resource Requirements**: What would be needed to pursue these opportunities?

Focus on specific, actionable opportunities with clear business value.""",
                }
            ],
        },
    }

    results, execution_context = runtime.execute(workflow, parameters=parameters)

    return {
        "scope": domain or "all_domains",
        "gaps": results.get("gap_analysis", {}),
        "trends": results.get("trend_analysis", {}),
        "opportunities": results.get("opportunity_agent", {}),
        "execution_context": execution_context,
    }


# Specialized analysis functions
def analyze_healthcare_ai_trends(
    runtime: Optional[LocalRuntime] = None,
) -> Dict[str, Any]:
    """Specialized analysis for Healthcare AI trends."""
    return execute_domain_deep_dive(domain="Healthcare", runtime=runtime)


def analyze_finance_ai_maturity(
    runtime: Optional[LocalRuntime] = None,
) -> Dict[str, Any]:
    """Specialized analysis for Finance AI maturity."""
    return execute_domain_deep_dive(domain="Finance", runtime=runtime)


def compare_tech_domains(runtime: Optional[LocalRuntime] = None) -> Dict[str, Any]:
    """Compare technology-focused domains."""
    tech_domains = [
        "Information Technology",
        "Telecommunications",
        "Software Engineering",
    ]
    return execute_cross_domain_comparison(domains=tech_domains, runtime=runtime)


def identify_manufacturing_opportunities(
    runtime: Optional[LocalRuntime] = None,
) -> Dict[str, Any]:
    """Identify AI opportunities in manufacturing."""
    return execute_domain_opportunity_analysis(domain="Manufacturing", runtime=runtime)


# Domain-specific insights generators
def get_domain_insights_prompts() -> Dict[str, str]:
    """Get domain-specific prompt templates for insights generation."""
    return {
        "Healthcare": """Focus on patient outcomes, regulatory compliance, clinical workflow integration,
                        data privacy, evidence-based medicine, and scalability across healthcare systems.""",
        "Finance": """Emphasize risk management, regulatory compliance, fraud detection, algorithmic trading,
                      customer experience, and financial inclusion implications.""",
        "Manufacturing": """Highlight operational efficiency, quality control, predictive maintenance,
                           supply chain optimization, worker safety, and Industry 4.0 integration.""",
        "Education": """Consider learning outcomes, personalization, accessibility, teacher support,
                       student engagement, and educational equity.""",
        "Transportation": """Focus on safety, efficiency, environmental impact, autonomous systems,
                           traffic management, and multi-modal integration.""",
        "Energy": """Emphasize sustainability, grid optimization, renewable energy integration,
                   energy efficiency, and environmental monitoring.""",
        "Agriculture": """Highlight crop yield optimization, sustainable farming, precision agriculture,
                        food security, and environmental stewardship.""",
        "Retail": """Focus on customer experience, inventory optimization, demand forecasting,
                   personalization, and omnichannel integration.""",
    }


def create_domain_specific_workflow(domain: str, focus_areas: List[str]) -> Workflow:
    """
    Create a workflow tailored to specific domain needs.

    Args:
        domain: Target domain
        focus_areas: Specific areas to focus analysis on

    Returns:
        Domain-specific workflow
    """
    workflow_name = f"{domain.lower().replace(' ', '_')}_analysis"
    workflow = Workflow(workflow_name, f"{domain} AI Analysis")

    # Domain search with focus area filtering
    workflow.add_node("focused_search", RegistrySearchNode(name="focused_search"))

    # Specialized analytics
    workflow.add_node(
        "specialized_analytics", RegistryAnalyticsNode(name="specialized_analytics")
    )

    # Domain expert agent
    workflow.add_node("domain_expert", LLMAgentNode(name="domain_expert"))

    # Connect nodes
    workflow.connect("focused_search", "domain_expert")
    workflow.connect("specialized_analytics", "domain_expert")

    return workflow


# Workflow configuration helpers
def get_domain_workflow_configs() -> Dict[str, Dict[str, Any]]:
    """Get pre-configured domain workflow configurations."""
    return {
        "domain_overview": {
            "description": "Comprehensive analysis across all domains",
            "use_cases": [
                "Strategic planning across AI initiatives",
                "Investment decision support",
                "Market research and competitive analysis",
            ],
            "outputs": ["Domain distribution", "Maturity comparison", "Method trends"],
        },
        "domain_deep_dive": {
            "description": "Detailed analysis of a specific domain",
            "use_cases": [
                "Domain-specific strategy development",
                "Use case discovery and validation",
                "Competitive intelligence",
            ],
            "outputs": [
                "Domain insights",
                "Implementation examples",
                "Success patterns",
            ],
        },
        "cross_domain_comparison": {
            "description": "Comparative analysis across multiple domains",
            "use_cases": [
                "Cross-industry learning",
                "Technology transfer opportunities",
                "Portfolio optimization",
            ],
            "outputs": [
                "Comparative metrics",
                "Cross-pollination opportunities",
                "Best practices",
            ],
        },
        "opportunity_analysis": {
            "description": "Gap and opportunity identification",
            "use_cases": [
                "Innovation pipeline development",
                "Market opportunity assessment",
                "R&D prioritization",
            ],
            "outputs": ["Market gaps", "Emerging trends", "Implementation roadmaps"],
        },
    }
