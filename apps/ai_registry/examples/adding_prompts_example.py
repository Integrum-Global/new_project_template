"""
Example: How to Add MCP Prompts to AI Registry Server

This example shows how prompts enhance LLM capabilities by providing
expert knowledge and structured templates.
"""

# Example prompt templates for AI Registry
AI_REGISTRY_PROMPTS = [
    {
        "name": "analyze_implementation_fit",
        "description": "Analyze if an AI implementation fits your organization",
        "arguments": [
            {
                "name": "use_case_id",
                "description": "ID of the AI use case to analyze",
                "required": True,
            },
            {
                "name": "organization_context",
                "description": "Your organization's industry, size, and goals",
                "required": True,
            },
        ],
        "template": """You are an AI implementation consultant with deep expertise in evaluating AI solutions.

Analyze this AI implementation for organizational fit:

USE CASE DETAILS:
{use_case_details}

ORGANIZATION CONTEXT:
{organization_context}

Provide a comprehensive analysis covering:

1. ALIGNMENT ASSESSMENT
   - How well does this align with the organization's goals?
   - What specific problems would it solve?
   - Expected impact on operations

2. IMPLEMENTATION FEASIBILITY
   - Required technical capabilities
   - Data requirements and availability
   - Integration with existing systems
   - Estimated complexity (1-10 scale)

3. RESOURCE REQUIREMENTS
   - Team composition and skills needed
   - Infrastructure requirements
   - Estimated timeline based on similar implementations
   - Budget considerations

4. RISK ANALYSIS
   - Technical risks and mitigation strategies
   - Organizational change management needs
   - Common pitfalls from similar implementations

5. SUCCESS METRICS
   - KPIs to track
   - Expected ROI timeline
   - Success criteria definition

6. RECOMMENDATION
   - GO/NO-GO recommendation with rationale
   - If GO: Next steps and phase 1 priorities
   - If NO-GO: Alternative approaches to consider

Format as an executive briefing with clear sections and bullet points.""",
    },
    {
        "name": "compare_ai_approaches",
        "description": "Compare different AI approaches for solving a business problem",
        "arguments": [
            {
                "name": "business_problem",
                "description": "The business problem to solve",
                "required": True,
            },
            {
                "name": "approaches",
                "description": "List of AI approaches to compare",
                "required": True,
            },
        ],
        "template": """You are an AI strategy expert helping organizations choose the right AI approach.

BUSINESS PROBLEM:
{business_problem}

APPROACHES TO COMPARE:
{approaches_data}

Provide a detailed comparison:

1. APPROACH OVERVIEW
   For each approach:
   - Core technology and how it works
   - Typical use cases and success stories
   - Maturity level in the industry

2. COMPARATIVE ANALYSIS

   | Criteria | {approach_names} |
   |----------|------------------|
   | Implementation Complexity | ... |
   | Data Requirements | ... |
   | Accuracy/Performance | ... |
   | Scalability | ... |
   | Maintenance Needs | ... |
   | Cost Implications | ... |
   | Time to Value | ... |

3. SUITABILITY ASSESSMENT
   - Best fit scenarios for each approach
   - Deal breakers or limitations
   - Industry-specific considerations

4. RECOMMENDATION
   - Recommended approach with justification
   - Hybrid possibilities
   - Phased implementation strategy

5. SUCCESS EXAMPLES
   - Similar organizations that succeeded with recommended approach
   - Lessons learned from their implementations

Make the analysis actionable and specific to the stated business problem.""",
    },
    {
        "name": "create_ai_roadmap",
        "description": "Create a phased AI implementation roadmap",
        "arguments": [
            {
                "name": "current_state",
                "description": "Organization's current AI maturity and capabilities",
                "required": True,
            },
            {
                "name": "target_implementations",
                "description": "List of desired AI implementations",
                "required": True,
            },
            {
                "name": "timeline",
                "description": "Desired timeline (e.g., 6 months, 1 year, 2 years)",
                "required": True,
            },
        ],
        "template": """You are an AI transformation architect creating implementation roadmaps.

CURRENT STATE:
{current_state}

TARGET IMPLEMENTATIONS:
{target_implementations_details}

TIMELINE: {timeline}

Create a comprehensive AI implementation roadmap:

1. MATURITY ASSESSMENT
   - Current AI maturity level (1-5)
   - Gap analysis to target state
   - Quick wins vs. long-term goals

2. PHASED ROADMAP

   PHASE 1: FOUNDATION (Months 1-X)
   - Priority implementations
   - Infrastructure setup
   - Team building and training
   - Data preparation
   - Success criteria

   PHASE 2: EXPANSION (Months X-Y)
   - Additional implementations
   - Scaling successful pilots
   - Process optimization
   - Success criteria

   PHASE 3: TRANSFORMATION (Months Y-Z)
   - Advanced implementations
   - Enterprise integration
   - Innovation initiatives
   - Success criteria

3. IMPLEMENTATION SEQUENCE
   - Dependency mapping
   - Risk-based prioritization
   - Resource optimization
   - Learning curve considerations

4. RESOURCE PLAN
   - Team composition by phase
   - Budget allocation
   - Technology stack evolution
   - Partner/vendor requirements

5. RISK MITIGATION
   - Phase-specific risks
   - Contingency plans
   - Go/no-go decision points
   - Fallback strategies

6. SUCCESS METRICS
   - Phase-wise KPIs
   - Business value tracking
   - ROI measurement framework
   - Organizational readiness indicators

Format as a visual-friendly roadmap with clear milestones and dependencies.""",
    },
]


def demonstrate_prompt_usage():
    """Show how prompts enhance LLM responses."""

    print("=== MCP Prompts in Action ===\n")

    # Example 1: Without Prompt
    print("1. WITHOUT MCP PROMPT:")
    print("User: 'Should we implement use case 42?'")
    print(
        "Basic LLM: 'Use case 42 is a healthcare AI system. It uses machine learning.'"
    )
    print("(Generic, not very helpful)\n")

    # Example 2: With Prompt
    print("2. WITH MCP PROMPT (analyze_implementation_fit):")
    print("User: 'Should we implement use case 42?'")
    print("\nLLM Process:")
    print("- Recognizes need for implementation analysis")
    print("- Requests 'analyze_implementation_fit' prompt from MCP server")
    print("- Gets use case 42 details via tools")
    print("- Fills prompt template with data")
    print("- Executes enriched prompt")
    print("\nEnhanced Response:")
    print(
        """
EXECUTIVE BRIEFING: Healthcare Diagnostic AI Implementation Analysis

1. ALIGNMENT ASSESSMENT
   ✓ Strong alignment with digital transformation goals
   ✓ Addresses diagnostic accuracy challenges (current error rate: 15%)
   ✓ Expected 40% reduction in diagnostic time

2. IMPLEMENTATION FEASIBILITY
   - Technical Requirements: ML infrastructure, GPU servers
   - Data: 100K+ annotated medical images required
   - Integration: HL7 FHIR compatibility with current EMR
   - Complexity: 7/10 (moderate-high due to regulatory requirements)

3. RESOURCE REQUIREMENTS
   - Team: 2 ML engineers, 1 clinical informaticist, 1 project manager
   - Infrastructure: $150K initial investment
   - Timeline: 6-9 months to production
   - Budget: $500K total (including validation)

4. RECOMMENDATION: GO
   - Strong ROI potential (breakeven in 14 months)
   - Phase 1: Pilot with radiology department
   - Success criteria: 90% accuracy, <2min processing time
"""
    )


def show_prompt_implementation():
    """Show how to implement prompts in MCP server."""

    print("\n\n=== How to Add Prompts to AI Registry Server ===\n")

    code = '''
# In server/registry_server.py

async def list_prompts(self) -> List[Prompt]:
    """List available prompts."""
    prompts = []

    for prompt_def in AI_REGISTRY_PROMPTS:
        prompts.append(Prompt(
            name=prompt_def["name"],
            description=prompt_def["description"],
            arguments=[
                PromptArgument(
                    name=arg["name"],
                    description=arg["description"],
                    required=arg.get("required", True)
                )
                for arg in prompt_def["arguments"]
            ]
        ))

    return prompts

async def get_prompt(self, name: str, arguments: Dict[str, str]) -> str:
    """Get a specific prompt with arguments filled."""

    # Find prompt template
    prompt_def = next((p for p in AI_REGISTRY_PROMPTS if p["name"] == name), None)
    if not prompt_def:
        raise ValueError(f"Unknown prompt: {name}")

    # Prepare data based on prompt needs
    template_data = {}

    if name == "analyze_implementation_fit":
        use_case = self.indexer.get_by_id(int(arguments["use_case_id"]))
        template_data["use_case_details"] = format_use_case(use_case)
        template_data["organization_context"] = arguments["organization_context"]

    elif name == "compare_ai_approaches":
        # Get data for each approach
        approaches_data = []
        for approach in arguments["approaches"].split(","):
            results = self.indexer.filter_by_ai_method(approach.strip())
            approaches_data.append(format_approach_data(approach, results))
        template_data["approaches_data"] = "\\n".join(approaches_data)
        template_data["approach_names"] = " | ".join(arguments["approaches"].split(","))
        template_data["business_problem"] = arguments["business_problem"]

    # Fill template
    return prompt_def["template"].format(**template_data)
'''

    print(code)


def explain_prompt_benefits():
    """Explain why prompts are powerful."""

    print("\n\n=== Why MCP Prompts Are Game-Changing ===\n")

    print("1. EXPERTISE EMBEDDING")
    print("   - Prompts contain domain expert knowledge")
    print("   - Best practices built into templates")
    print("   - Consistent high-quality analysis")
    print()

    print("2. CONTEXT ENRICHMENT")
    print("   - Prompts include relevant data automatically")
    print("   - Similar case studies and patterns")
    print("   - Industry-specific considerations")
    print()

    print("3. STRUCTURED OUTPUT")
    print("   - Consistent formatting across responses")
    print("   - All important aspects covered")
    print("   - Executive-ready presentations")
    print()

    print("4. REUSABILITY")
    print("   - Same prompts work with any LLM")
    print("   - Easy to update and improve")
    print("   - Share expertise across teams")
    print()

    print("5. TOOL + PROMPT SYNERGY")
    print("   Example workflow:")
    print(
        "   - User: 'Help me choose between ML and deep learning for fraud detection'"
    )
    print("   - Claude uses tools: search_use_cases('fraud detection ML'),")
    print("                        search_use_cases('fraud detection deep learning')")
    print("   - Claude uses prompt: compare_ai_approaches with gathered data")
    print("   - Result: Comprehensive comparison with recommendations")


if __name__ == "__main__":
    demonstrate_prompt_usage()
    show_prompt_implementation()
    explain_prompt_benefits()

    print("\n\n=== Key Takeaway ===")
    print("MCP Prompts turn LLMs from generic assistants into domain experts")
    print("by providing structured templates filled with contextual data.")
