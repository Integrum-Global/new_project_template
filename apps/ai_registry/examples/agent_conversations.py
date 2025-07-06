"""
Agent conversation examples for AI Registry MCP Server.

This module demonstrates how to have rich conversations with
LLM agents that can query and analyze the AI Registry.
"""

from typing import Any, Dict

from kailash.runtime.local import LocalRuntime

from ..workflows import execute_agent_search


class AIRegistryConversationExamples:
    """Collection of conversation examples with the AI Registry agent."""

    def __init__(
        self, provider: str = "ollama", model: str = "llama3.1:8b-instruct-q8_0"
    ):
        """
        Initialize conversation examples.

        Args:
            provider: LLM provider to use
            model: LLM model to use
        """
        self.provider = provider
        self.model = model
        self.runtime = LocalRuntime()

    def research_conversation(self) -> Dict[str, Any]:
        """
        Example: Research-oriented conversation

        Demonstrates how to use the agent for research purposes,
        asking complex questions that require tool usage.
        """
        print("🔬 Research Conversation Example")
        print("=" * 50)

        conversation = [
            "I'm researching AI applications in healthcare. What are the main areas where AI is being applied?",
            "Which healthcare AI implementations have reached production status? I'd like specific examples.",
            "Are there any interesting patterns in how different AI methods are being combined in healthcare?",
            "What challenges are commonly mentioned across healthcare AI implementations?",
            "Can you find similar applications in other domains that might provide insights for healthcare AI?",
        ]

        results = []

        for i, query in enumerate(conversation, 1):
            print(f"\n👤 User Query {i}: {query}")
            print("-" * 40)

            try:
                result = execute_agent_search(
                    user_query=query,
                    provider=self.provider,
                    model=self.model,
                    runtime=self.runtime,
                )

                if result.get("success"):
                    response = result.get("response", {})
                    print(f"🤖 Agent: {self._extract_response_text(response)[:200]}...")

                    # Show tools used
                    if tool_calls := response.get("tool_calls"):
                        print(
                            f"🔧 Tools used: {[call.get('function', {}).get('name', 'unknown') for call in tool_calls]}"
                        )
                else:
                    print(f"❌ Error: {result.get('error', 'Unknown error')}")

                results.append({"query": query, "result": result})

            except Exception as e:
                print(f"❌ Error: {e}")
                results.append({"query": query, "error": str(e)})

        return {"conversation_type": "research", "exchanges": results}

    def strategic_planning_conversation(self) -> Dict[str, Any]:
        """
        Example: Strategic planning conversation

        Demonstrates using the agent for strategic decision making,
        competitive analysis, and market insights.
        """
        print("\n📈 Strategic Planning Conversation Example")
        print("=" * 50)

        conversation = [
            "Our company wants to invest in AI for financial services. What's the current landscape of AI in finance?",
            "Which AI methods show the most promise for production deployment in finance?",
            "How does AI adoption in finance compare to other industries like healthcare or manufacturing?",
            "What gaps do you see in current financial AI implementations that represent opportunities?",
            "Can you identify the most mature financial AI use cases that we could learn from?",
        ]

        results = []

        for i, query in enumerate(conversation, 1):
            print(f"\n👤 Strategic Question {i}: {query}")
            print("-" * 40)

            try:
                result = execute_agent_search(
                    user_query=query,
                    provider=self.provider,
                    model=self.model,
                    runtime=self.runtime,
                )

                if result.get("success"):
                    response = result.get("response", {})
                    print(
                        f"🤖 Advisor: {self._extract_response_text(response)[:200]}..."
                    )
                else:
                    print(f"❌ Error: {result.get('error', 'Unknown error')}")

                results.append({"query": query, "result": result})

            except Exception as e:
                print(f"❌ Error: {e}")
                results.append({"query": query, "error": str(e)})

        return {"conversation_type": "strategic_planning", "exchanges": results}

    def technical_exploration_conversation(self) -> Dict[str, Any]:
        """
        Example: Technical exploration conversation

        Demonstrates using the agent for technical deep dives,
        method comparisons, and implementation insights.
        """
        print("\n🔧 Technical Exploration Conversation Example")
        print("=" * 50)

        conversation = [
            "I'm interested in natural language processing applications. Show me the different ways NLP is being used across domains.",
            "Which domains are combining NLP with other AI methods most effectively?",
            "Are there any NLP implementations that have successfully scaled to production? What can we learn from them?",
            "What are the common challenges mentioned for NLP implementations across different use cases?",
            "Can you find any innovative or unusual applications of NLP that might inspire new ideas?",
        ]

        results = []

        for i, query in enumerate(conversation, 1):
            print(f"\n👤 Technical Query {i}: {query}")
            print("-" * 40)

            try:
                result = execute_agent_search(
                    user_query=query,
                    provider=self.provider,
                    model=self.model,
                    runtime=self.runtime,
                )

                if result.get("success"):
                    response = result.get("response", {})
                    print(
                        f"🤖 Expert: {self._extract_response_text(response)[:200]}..."
                    )
                else:
                    print(f"❌ Error: {result.get('error', 'Unknown error')}")

                results.append({"query": query, "result": result})

            except Exception as e:
                print(f"❌ Error: {e}")
                results.append({"query": query, "error": str(e)})

        return {"conversation_type": "technical_exploration", "exchanges": results}

    def comparative_analysis_conversation(self) -> Dict[str, Any]:
        """
        Example: Comparative analysis conversation

        Demonstrates using the agent for comparing different
        implementations, domains, and approaches.
        """
        print("\n⚖️  Comparative Analysis Conversation Example")
        print("=" * 50)

        conversation = [
            "Compare how machine learning is being applied in healthcare versus manufacturing. What are the key differences?",
            "Which domains have achieved the highest rate of production deployments for AI? What factors contribute to this success?",
            "How do PoC implementations differ from production implementations in terms of challenges and success factors?",
            "Are there any AI methods that work well across multiple domains? What makes them versatile?",
            "What can less mature domains learn from the most advanced AI implementations?",
        ]

        results = []

        for i, query in enumerate(conversation, 1):
            print(f"\n👤 Comparison Question {i}: {query}")
            print("-" * 40)

            try:
                result = execute_agent_search(
                    user_query=query,
                    provider=self.provider,
                    model=self.model,
                    runtime=self.runtime,
                )

                if result.get("success"):
                    response = result.get("response", {})
                    print(
                        f"🤖 Analyst: {self._extract_response_text(response)[:200]}..."
                    )
                else:
                    print(f"❌ Error: {result.get('error', 'Unknown error')}")

                results.append({"query": query, "result": result})

            except Exception as e:
                print(f"❌ Error: {e}")
                results.append({"query": query, "error": str(e)})

        return {"conversation_type": "comparative_analysis", "exchanges": results}

    def innovation_discovery_conversation(self) -> Dict[str, Any]:
        """
        Example: Innovation discovery conversation

        Demonstrates using the agent to discover innovative
        applications and identify emerging trends.
        """
        print("\n💡 Innovation Discovery Conversation Example")
        print("=" * 50)

        conversation = [
            "What are the most innovative or unusual AI applications you can find in the registry?",
            "Are there any emerging AI methods that are just starting to be adopted?",
            "Which domains show the most experimental or cutting-edge AI implementations?",
            "Can you identify any patterns that suggest future directions for AI development?",
            "What combinations of AI methods seem most promising for future exploration?",
        ]

        results = []

        for i, query in enumerate(conversation, 1):
            print(f"\n👤 Innovation Query {i}: {query}")
            print("-" * 40)

            try:
                result = execute_agent_search(
                    user_query=query,
                    provider=self.provider,
                    model=self.model,
                    runtime=self.runtime,
                )

                if result.get("success"):
                    response = result.get("response", {})
                    print(
                        f"🤖 Innovator: {self._extract_response_text(response)[:200]}..."
                    )
                else:
                    print(f"❌ Error: {result.get('error', 'Unknown error')}")

                results.append({"query": query, "result": result})

            except Exception as e:
                print(f"❌ Error: {e}")
                results.append({"query": query, "error": str(e)})

        return {"conversation_type": "innovation_discovery", "exchanges": results}

    def _extract_response_text(self, response: Any) -> str:
        """Extract readable text from agent response."""
        if isinstance(response, dict):
            if "content" in response:
                return str(response["content"])
            elif "message" in response:
                return str(response["message"])
            else:
                return str(response)
        elif isinstance(response, str):
            return response
        else:
            return str(response)


def run_conversation_demos(
    provider: str = "ollama", model: str = "llama3.1:8b-instruct-q8_0"
) -> Dict[str, Any]:
    """
    Run all conversation demonstrations.

    Args:
        provider: LLM provider to use
        model: LLM model to use

    Returns:
        Results from all conversation examples
    """
    print("🗣️  AI Registry Agent Conversation Demonstrations")
    print("=" * 60)

    examples = AIRegistryConversationExamples(provider, model)
    results = {}

    try:
        # Research conversation
        results["research"] = examples.research_conversation()

        # Strategic planning conversation
        results["strategic_planning"] = examples.strategic_planning_conversation()

        # Technical exploration conversation
        results["technical_exploration"] = examples.technical_exploration_conversation()

        # Comparative analysis conversation
        results["comparative_analysis"] = examples.comparative_analysis_conversation()

        # Innovation discovery conversation
        results["innovation_discovery"] = examples.innovation_discovery_conversation()

        print("\n" + "=" * 60)
        print("🎉 All conversation demonstrations complete!")

    except Exception as e:
        print(f"\n❌ Error running conversations: {e}")
        results["error"] = str(e)

    return results


def demonstrate_custom_agent_setup() -> Dict[str, Any]:
    """
    Demonstrate how to set up custom agent configurations
    for different use cases.
    """
    print("\n⚙️  Custom Agent Setup Examples")
    print("=" * 50)

    # Different agent personas for different tasks
    agent_configs = {
        "research_analyst": {
            "system_prompt": """You are an AI research analyst specializing in enterprise AI implementations.
            Focus on providing data-driven insights, concrete examples, and actionable intelligence.
            Always cite specific use case IDs when providing examples.""",
            "temperature": 0.1,  # Low for factual responses
            "max_tool_calls": 8,
        },
        "strategic_advisor": {
            "system_prompt": """You are a strategic AI advisor helping organizations make informed decisions.
            Focus on market trends, competitive positioning, and strategic opportunities.
            Provide balanced analysis of risks and opportunities.""",
            "temperature": 0.3,  # Medium for balanced analysis
            "max_tool_calls": 6,
        },
        "technical_expert": {
            "system_prompt": """You are a technical AI expert with deep knowledge of AI methods and implementations.
            Focus on technical details, method comparisons, and implementation insights.
            Explain complex concepts clearly and provide specific technical guidance.""",
            "temperature": 0.2,  # Low-medium for technical accuracy
            "max_tool_calls": 10,
        },
        "innovation_scout": {
            "system_prompt": """You are an innovation scout looking for emerging trends and breakthrough applications.
            Focus on novel applications, emerging patterns, and future opportunities.
            Be creative in identifying connections and possibilities.""",
            "temperature": 0.4,  # Higher for creative insights
            "max_tool_calls": 12,
        },
    }

    print("Available agent personas:")
    for name, config in agent_configs.items():
        print(f"\n📋 {name.replace('_', ' ').title()}")
        print(f"   Purpose: {config['system_prompt'][:100]}...")
        print(f"   Temperature: {config['temperature']}")
        print(f"   Max Tools: {config['max_tool_calls']}")

    return agent_configs


def demonstrate_multi_turn_conversation() -> Dict[str, Any]:
    """
    Demonstrate a multi-turn conversation that builds context
    across multiple exchanges.
    """
    print("\n🔄 Multi-Turn Conversation Example")
    print("=" * 50)

    # This would require implementing conversation state management
    # For now, show the pattern

    conversation_flow = [
        {
            "turn": 1,
            "user": "Tell me about AI in healthcare",
            "context": "Initial query - broad healthcare AI overview",
        },
        {
            "turn": 2,
            "user": "Which of those healthcare applications are most mature?",
            "context": "Follow-up - filter previous results by maturity",
        },
        {
            "turn": 3,
            "user": "Can you compare the most mature one to similar applications in other domains?",
            "context": "Deep dive - cross-domain comparison based on previous context",
        },
        {
            "turn": 4,
            "user": "What would it take to implement something similar in retail?",
            "context": "Application - practical implementation guidance",
        },
    ]

    print("Multi-turn conversation pattern:")
    for turn in conversation_flow:
        print(f"\nTurn {turn['turn']}: {turn['user']}")
        print(f"Context: {turn['context']}")

    print("\n💡 Implementation note: Multi-turn conversations require:")
    print("   - Context preservation across turns")
    print("   - Reference resolution (e.g., 'those applications')")
    print("   - Progressive refinement of queries")
    print("   - Conversation state management")

    return {"pattern": "multi_turn", "turns": conversation_flow}


# Utility functions for conversation analysis
def analyze_conversation_patterns(
    conversation_results: Dict[str, Any],
) -> Dict[str, Any]:
    """
    Analyze patterns in conversation results to understand
    agent behavior and tool usage.
    """
    analysis = {
        "total_exchanges": 0,
        "successful_exchanges": 0,
        "tools_used": {},
        "common_patterns": [],
        "error_analysis": {},
    }

    for conv_type, conv_data in conversation_results.items():
        if conv_type == "error":
            continue

        exchanges = conv_data.get("exchanges", [])
        analysis["total_exchanges"] += len(exchanges)

        for exchange in exchanges:
            if "error" not in exchange:
                analysis["successful_exchanges"] += 1

                # Analyze tool usage
                result = exchange.get("result", {})
                if result.get("success"):
                    response = result.get("response", {})
                    if tool_calls := response.get("tool_calls"):
                        for call in tool_calls:
                            func_name = call.get("function", {}).get("name", "unknown")
                            analysis["tools_used"][func_name] = (
                                analysis["tools_used"].get(func_name, 0) + 1
                            )

    # Calculate success rate
    total = analysis["total_exchanges"]
    success = analysis["successful_exchanges"]
    analysis["success_rate"] = success / total if total > 0 else 0

    # Most used tools
    analysis["top_tools"] = sorted(
        analysis["tools_used"].items(), key=lambda x: x[1], reverse=True
    )[:5]

    return analysis


# Main execution
if __name__ == "__main__":
    # Run conversation demonstrations
    results = run_conversation_demos()

    # Show custom agent setups
    agent_configs = demonstrate_custom_agent_setup()

    # Show multi-turn pattern
    multi_turn = demonstrate_multi_turn_conversation()

    # Analyze conversation patterns
    if results and "error" not in results:
        analysis = analyze_conversation_patterns(results)

        print("\n📊 Conversation Analysis")
        print("=" * 30)
        print(f"Total Exchanges: {analysis['total_exchanges']}")
        print(f"Success Rate: {analysis['success_rate']:.1%}")
        print(f"Most Used Tools: {[tool for tool, count in analysis['top_tools']]}")

    print("\n🎯 Key Takeaways:")
    print("- Agents can handle complex, multi-step queries")
    print("- Tool usage adapts to query type and complexity")
    print("- Different agent personas work better for different tasks")
    print("- Context building enables more sophisticated analysis")
