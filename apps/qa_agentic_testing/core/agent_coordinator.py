#!/usr/bin/env python3
"""
Advanced Agent Coordination System for QA Agentic Testing

This module orchestrates sophisticated AI agent systems for comprehensive testing analysis.
Integrates A2A communication, agent pools, iterative agents, and intelligent orchestration
for multi-perspective consensus-based validation.
"""

import asyncio
import json
import logging
import time
from dataclasses import asdict, dataclass
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

# Import Kailash advanced agent systems
from kailash.nodes.ai.a2a import A2AAgentNode, A2ACoordinatorNode, SharedMemoryPoolNode
from kailash.nodes.ai.intelligent_agent_orchestrator import (
    ConvergenceDetectorNode,
    IntelligentCacheNode,
    MCPAgentNode,
    OrchestrationManagerNode,
    QueryAnalysisNode,
)
from kailash.nodes.ai.iterative_llm_agent import IterativeLLMAgentNode
from kailash.nodes.ai.llm_agent import LLMAgentNode
from kailash.nodes.ai.self_organizing import (
    AgentPoolManagerNode,
    ProblemAnalyzerNode,
    SelfOrganizingAgentNode,
    SolutionEvaluatorNode,
    TeamFormationNode,
)


class AgentType(Enum):
    """Types of AI agents available for analysis."""

    BASIC_LLM = "basic_llm"
    ITERATIVE_AGENT = "iterative_agent"
    A2A_AGENT = "a2a_agent"
    SELF_ORGANIZING = "self_organizing"
    MCP_AGENT = "mcp_agent"
    ORCHESTRATION_MANAGER = "orchestration_manager"
    AGENT_POOL = "agent_pool"


class AnalysisType(Enum):
    """Types of analysis that can be performed."""

    GENERAL = "general"
    SECURITY = "security"
    PERFORMANCE = "performance"
    USABILITY = "usability"
    FUNCTIONAL = "functional"
    INTEGRATION = "integration"
    CONSENSUS = "consensus"
    COLLABORATIVE = "collaborative"


@dataclass
class AgentConfig:
    """Configuration for an AI agent."""

    agent_type: AgentType
    provider: str = "ollama"  # LLM provider (ollama, openai, anthropic)
    model: str = "llama3.2:latest"
    specializations: List[AnalysisType] = None
    priority: int = 1  # Higher numbers = higher priority
    enabled: bool = True
    max_tokens: int = 4000
    temperature: float = 0.1
    timeout_seconds: int = 30
    team_size: int = 1  # For agent pools and teams
    collaboration_mode: str = "independent"  # independent, collaborative, consensus

    def __post_init__(self):
        if self.specializations is None:
            self.specializations = [AnalysisType.GENERAL]

    @classmethod
    def get_recommended_config(
        cls, agent_type: AgentType, preset: str = "balanced"
    ) -> "AgentConfig":
        """Get recommended configuration for agent type and preset."""

        # Model recommendations by preset and agent type
        model_matrix = {
            "development": {
                AgentType.BASIC_LLM: ("ollama", "llama3.2:latest"),
                AgentType.ITERATIVE_AGENT: ("ollama", "llama3.1:8b"),
                AgentType.A2A_AGENT: ("ollama", "llama3.2:latest"),
                AgentType.SELF_ORGANIZING: ("ollama", "codellama:13b"),
                AgentType.MCP_AGENT: ("ollama", "llama3.1:8b"),
            },
            "balanced": {
                AgentType.BASIC_LLM: ("openai", "gpt-3.5-turbo"),
                AgentType.ITERATIVE_AGENT: ("ollama", "llama3.1:8b"),
                AgentType.A2A_AGENT: ("openai", "gpt-3.5-turbo"),
                AgentType.SELF_ORGANIZING: ("anthropic", "claude-3-haiku"),
                AgentType.MCP_AGENT: ("ollama", "codellama:latest"),
            },
            "enterprise": {
                AgentType.BASIC_LLM: ("openai", "gpt-4"),
                AgentType.ITERATIVE_AGENT: ("anthropic", "claude-3-sonnet"),
                AgentType.A2A_AGENT: ("openai", "gpt-4"),
                AgentType.SELF_ORGANIZING: ("anthropic", "claude-3-opus"),
                AgentType.MCP_AGENT: ("openai", "gpt-4"),
            },
        }

        provider, model = model_matrix.get(preset, model_matrix["balanced"]).get(
            agent_type, ("ollama", "llama3.2:latest")
        )

        # Adjust parameters based on agent type
        config_overrides = {
            AgentType.BASIC_LLM: {
                "temperature": 0.1,
                "max_tokens": 2000,
                "timeout_seconds": 20,
            },
            AgentType.ITERATIVE_AGENT: {
                "temperature": 0.2,
                "max_tokens": 3000,
                "timeout_seconds": 45,
            },
            AgentType.A2A_AGENT: {
                "temperature": 0.1,
                "max_tokens": 4000,
                "timeout_seconds": 30,
            },
            AgentType.SELF_ORGANIZING: {
                "temperature": 0.3,
                "max_tokens": 4000,
                "timeout_seconds": 60,
            },
            AgentType.MCP_AGENT: {
                "temperature": 0.1,
                "max_tokens": 3000,
                "timeout_seconds": 25,
            },
        }

        overrides = config_overrides.get(agent_type, {})

        return cls(agent_type=agent_type, provider=provider, model=model, **overrides)

    @classmethod
    def get_security_optimized_config(cls, agent_type: AgentType) -> "AgentConfig":
        """Get security-optimized configuration for agent type."""
        # Security analysis requires high accuracy models
        security_models = {
            AgentType.BASIC_LLM: ("openai", "gpt-4"),
            AgentType.ITERATIVE_AGENT: ("anthropic", "claude-3-sonnet"),
            AgentType.A2A_AGENT: ("openai", "gpt-4"),
            AgentType.SELF_ORGANIZING: ("anthropic", "claude-3-opus"),
            AgentType.MCP_AGENT: ("openai", "gpt-4"),
        }

        provider, model = security_models.get(agent_type, ("openai", "gpt-4"))

        return cls(
            agent_type=agent_type,
            provider=provider,
            model=model,
            temperature=0.05,  # Lower temperature for security analysis
            max_tokens=4000,
            timeout_seconds=45,
            specializations=[AnalysisType.SECURITY],
        )

    @classmethod
    def get_performance_optimized_config(cls, agent_type: AgentType) -> "AgentConfig":
        """Get performance-optimized configuration for agent type."""
        # Performance analysis benefits from analytical models
        performance_models = {
            AgentType.BASIC_LLM: ("anthropic", "claude-3-sonnet"),
            AgentType.ITERATIVE_AGENT: ("openai", "gpt-4"),
            AgentType.A2A_AGENT: ("anthropic", "claude-3-opus"),
            AgentType.SELF_ORGANIZING: ("ollama", "codellama:13b"),
            AgentType.MCP_AGENT: ("anthropic", "claude-3-sonnet"),
        }

        provider, model = performance_models.get(
            agent_type, ("anthropic", "claude-3-sonnet")
        )

        return cls(
            agent_type=agent_type,
            provider=provider,
            model=model,
            temperature=0.1,
            max_tokens=3000,
            timeout_seconds=30,
            specializations=[AnalysisType.PERFORMANCE],
        )


@dataclass
class AgentResponse:
    """Response from an AI agent."""

    agent_type: AgentType
    agent_id: str
    analysis_type: AnalysisType
    prompt: str
    response: str
    timestamp: float
    duration_seconds: float
    confidence_score: float
    collaboration_data: Dict[str, Any]
    performance_metrics: Dict[str, Any]
    error: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary format."""
        data = asdict(self)
        data["agent_type"] = self.agent_type.value
        data["analysis_type"] = self.analysis_type.value
        return data


@dataclass
class ConsensusAnalysis:
    """Consensus analysis from multiple AI agents."""

    analysis_type: AnalysisType
    responses: List[AgentResponse]
    consensus_response: str
    confidence_score: float
    agreements: List[str]
    disagreements: List[str]
    recommendation: str
    collaboration_summary: Dict[str, Any]
    timestamp: float

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary format."""
        data = asdict(self)
        data["analysis_type"] = self.analysis_type.value
        data["responses"] = [r.to_dict() for r in self.responses]
        return data


class AgentCoordinator:
    """Coordinates multiple AI agent systems for comprehensive analysis."""

    def __init__(self, config_file: Optional[Path] = None):
        self.agent_configs: Dict[str, AgentConfig] = {}
        self.active_agents: Dict[str, Any] = {}
        self.response_cache: Dict[str, AgentResponse] = {}
        self.analysis_history: List[ConsensusAnalysis] = []

        # Initialize shared infrastructure
        self.shared_memory = SharedMemoryPoolNode()
        self.agent_pool_manager = AgentPoolManagerNode()
        self.orchestration_manager = OrchestrationManagerNode()
        self.intelligent_cache = IntelligentCacheNode()

        # Setup logging
        self.logger = logging.getLogger(__name__)

        # Load configuration
        if config_file and config_file.exists():
            self.load_config(config_file)
        else:
            self._setup_default_config()

        # Initialize agent systems
        self._initialize_agents()

    def _setup_default_config(self):
        """Setup default agent configurations."""

        # Iterative LLM Agent (deep analysis)
        self.agent_configs["iterative_analyzer"] = AgentConfig(
            agent_type=AgentType.ITERATIVE_AGENT,
            provider="ollama",
            model="llama3.2:latest",
            specializations=[AnalysisType.SECURITY, AnalysisType.FUNCTIONAL],
            priority=3,
            collaboration_mode="iterative",
        )

        # A2A Agent Network (collaborative analysis)
        self.agent_configs["a2a_security_team"] = AgentConfig(
            agent_type=AgentType.A2A_AGENT,
            provider="ollama",
            model="llama3.2:latest",
            specializations=[AnalysisType.SECURITY, AnalysisType.CONSENSUS],
            priority=2,
            team_size=3,
            collaboration_mode="collaborative",
        )

        # Self-Organizing Agent Pool (adaptive analysis)
        self.agent_configs["self_org_performance"] = AgentConfig(
            agent_type=AgentType.SELF_ORGANIZING,
            provider="ollama",
            model="llama3.2:latest",
            specializations=[AnalysisType.PERFORMANCE, AnalysisType.USABILITY],
            priority=2,
            team_size=2,
            collaboration_mode="self_organizing",
        )

        # MCP Agent (tool-enhanced analysis)
        self.agent_configs["mcp_integration"] = AgentConfig(
            agent_type=AgentType.MCP_AGENT,
            provider="ollama",
            model="llama3.2:latest",
            specializations=[AnalysisType.INTEGRATION, AnalysisType.FUNCTIONAL],
            priority=1,
            collaboration_mode="tool_enhanced",
        )

        # Basic LLM (fallback)
        self.agent_configs["basic_llm"] = AgentConfig(
            agent_type=AgentType.BASIC_LLM,
            provider="ollama",
            model="llama3.2:latest",
            specializations=[AnalysisType.GENERAL],
            priority=1,
            collaboration_mode="independent",
        )

    def _initialize_agents(self):
        """Initialize AI agent systems."""

        for agent_id, config in self.agent_configs.items():
            if not config.enabled:
                continue

            try:
                # Create agent based on type (agents are configured at runtime via run parameters)
                if config.agent_type == AgentType.ITERATIVE_AGENT:
                    agent = IterativeLLMAgentNode()

                elif config.agent_type == AgentType.A2A_AGENT:
                    agent = A2AAgentNode()

                elif config.agent_type == AgentType.SELF_ORGANIZING:
                    agent = SelfOrganizingAgentNode()

                elif config.agent_type == AgentType.MCP_AGENT:
                    agent = MCPAgentNode()

                elif config.agent_type == AgentType.BASIC_LLM:
                    agent = LLMAgentNode()

                else:
                    self.logger.warning(f"Unknown agent type: {config.agent_type}")
                    continue

                # Register agent in pool if it's a pooled agent
                if config.agent_type in [
                    AgentType.SELF_ORGANIZING,
                    AgentType.A2A_AGENT,
                ]:
                    self.agent_pool_manager.run(
                        action="register",
                        agent_id=agent_id,
                        capabilities=config.specializations,
                        agent_instance=agent,
                    )

                self.active_agents[agent_id] = agent
                self.logger.info(
                    f"Initialized {config.agent_type.value} agent: {agent_id}"
                )

            except Exception as e:
                self.logger.error(f"Failed to initialize agent {agent_id}: {e}")

    def add_agent(self, agent_id: str, config: AgentConfig):
        """Add a new agent configuration."""
        self.agent_configs[agent_id] = config
        if config.enabled:
            self._initialize_agents()

    def get_available_agents(self) -> List[str]:
        """Get list of available and enabled agents."""
        return [
            agent_id
            for agent_id, config in self.agent_configs.items()
            if config.enabled and agent_id in self.active_agents
        ]

    def get_specialized_agents(self, analysis_type: AnalysisType) -> List[str]:
        """Get agents specialized for a specific analysis type."""
        specialized = []
        for agent_id, config in self.agent_configs.items():
            if (
                config.enabled
                and agent_id in self.active_agents
                and analysis_type in config.specializations
            ):
                specialized.append(agent_id)

        # Sort by priority (higher priority first)
        specialized.sort(key=lambda a: self.agent_configs[a].priority, reverse=True)
        return specialized

    async def analyze_single(
        self,
        prompt: str,
        analysis_type: AnalysisType = AnalysisType.GENERAL,
        agent_id: Optional[str] = None,
        persona_context: Optional[Dict[str, Any]] = None,
    ) -> AgentResponse:
        """Analyze with a single AI agent."""

        # Select agent if not specified
        if agent_id is None:
            specialized_agents = self.get_specialized_agents(analysis_type)
            if not specialized_agents:
                available_agents = self.get_available_agents()
                if not available_agents:
                    raise RuntimeError("No AI agents available")
                agent_id = available_agents[0]
            else:
                agent_id = specialized_agents[0]

        # Check cache first
        cache_key = f"{agent_id}:{analysis_type.value}:{hash(prompt)}"
        if cache_key in self.response_cache:
            return self.response_cache[cache_key]

        # Get agent configuration and instance
        config = self.agent_configs[agent_id]
        agent = self.active_agents[agent_id]

        # Add persona context to prompt if provided
        enhanced_prompt = self._enhance_prompt_with_context(
            prompt, persona_context, analysis_type
        )

        # Execute analysis
        start_time = time.time()
        try:
            response = await self._execute_agent_analysis(
                agent_id, agent, config, enhanced_prompt, analysis_type
            )
            duration = time.time() - start_time

            # Create response object
            agent_response = AgentResponse(
                agent_type=config.agent_type,
                agent_id=agent_id,
                analysis_type=analysis_type,
                prompt=enhanced_prompt,
                response=response["response"],
                timestamp=start_time,
                duration_seconds=duration,
                confidence_score=response.get("confidence_score", 0.0),
                collaboration_data=response.get("collaboration_data", {}),
                performance_metrics=response.get("performance_metrics", {}),
            )

            # Cache response
            self.response_cache[cache_key] = agent_response

            return agent_response

        except Exception as e:
            duration = time.time() - start_time
            error_response = AgentResponse(
                agent_type=config.agent_type,
                agent_id=agent_id,
                analysis_type=analysis_type,
                prompt=enhanced_prompt,
                response="",
                timestamp=start_time,
                duration_seconds=duration,
                confidence_score=0.0,
                collaboration_data={},
                performance_metrics={},
                error=str(e),
            )

            self.logger.error(f"Agent analysis failed for {agent_id}: {e}")
            return error_response

    async def _execute_agent_analysis(
        self,
        agent_id: str,
        agent: Any,
        config: AgentConfig,
        enhanced_prompt: str,
        analysis_type: AnalysisType,
    ) -> Dict[str, Any]:
        """Execute analysis using the specified agent."""

        if config.agent_type == AgentType.ITERATIVE_AGENT:
            result = agent.run(
                provider=config.provider,
                model=config.model,
                messages=[{"role": "user", "content": enhanced_prompt}],
                max_iterations=3,
                convergence_threshold=0.8,
                max_tokens=config.max_tokens,
                temperature=config.temperature,
            )

            return {
                "response": result.get("final_response", ""),
                "confidence_score": result.get("confidence_score", 0.0),
                "collaboration_data": {
                    "iterations": result.get("iterations", []),
                    "convergence_analysis": result.get("convergence_analysis", {}),
                },
                "performance_metrics": {
                    "iteration_count": len(result.get("iterations", [])),
                    "convergence_time": result.get("total_duration", 0),
                },
            }

        elif config.agent_type == AgentType.A2A_AGENT:
            # Use basic A2A agent for now (coordination is complex)
            result = agent.run(
                provider=config.provider,
                model=config.model,
                messages=[{"role": "user", "content": enhanced_prompt}],
                memory_pool_id="qa_testing_memory",
                agent_id=agent_id,
                max_tokens=config.max_tokens,
                temperature=config.temperature,
            )

            return {
                "response": result.get("consensus_response", ""),
                "confidence_score": result.get("consensus_confidence", 0.0),
                "collaboration_data": {
                    "agent_interactions": result.get("agent_interactions", []),
                    "memory_contributions": result.get("memory_contributions", []),
                },
                "performance_metrics": {
                    "collaboration_efficiency": result.get(
                        "collaboration_efficiency", 0.0
                    ),
                    "consensus_time": result.get("duration", 0),
                },
            }

        elif config.agent_type == AgentType.SELF_ORGANIZING:
            # Use basic self-organizing agent
            result = agent.run(
                provider=config.provider,
                model=config.model,
                messages=[{"role": "user", "content": enhanced_prompt}],
                task_type=analysis_type.value,
                team_size=config.team_size,
                max_tokens=config.max_tokens,
                temperature=config.temperature,
            )

            return {
                "response": result.get("response", result.get("solution", "")),
                "confidence_score": result.get("confidence_score", 0.0),
                "collaboration_data": {
                    "team_composition": result.get("team", []),
                    "formation_strategy": result.get("strategy", "self_organizing"),
                    "evaluation_metrics": result.get("metrics", {}),
                },
                "performance_metrics": {
                    "team_formation_time": result.get("formation_time", 0),
                    "solution_quality": result.get("quality_score", 0.0),
                },
            }

        elif config.agent_type == AgentType.MCP_AGENT:
            # Use MCP-enhanced analysis with tool integration
            result = agent.run(
                provider=config.provider,
                model=config.model,
                messages=[{"role": "user", "content": enhanced_prompt}],
                mcp_servers=["http://localhost:8080"],  # Default MCP server
                enable_tools=True,
                max_tokens=config.max_tokens,
                temperature=config.temperature,
            )

            return {
                "response": result.get("response", ""),
                "confidence_score": result.get("confidence_score", 0.0),
                "collaboration_data": {
                    "tools_used": result.get("tools_used", []),
                    "mcp_interactions": result.get("mcp_interactions", []),
                },
                "performance_metrics": {
                    "tool_call_count": len(result.get("tools_used", [])),
                    "cache_hit_rate": result.get("cache_hit_rate", 0.0),
                },
            }

        else:
            # Basic LLM agent
            return await self._execute_basic_agent_analysis(
                agent, enhanced_prompt, config
            )

    async def _execute_basic_agent_analysis(
        self, agent: Any, prompt: str, config: AgentConfig
    ) -> Dict[str, Any]:
        """Execute basic LLM agent analysis."""
        result = agent.run(
            provider=config.provider,
            model=config.model,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=config.max_tokens,
            temperature=config.temperature,
        )

        return {
            "response": result.get("response", ""),
            "confidence_score": self._calculate_confidence_score(
                result.get("response", ""), AnalysisType.GENERAL
            ),
            "collaboration_data": {},
            "performance_metrics": {
                "token_usage": result.get("token_usage", {}),
                "response_time": result.get("duration", 0),
            },
        }

    async def analyze_consensus(
        self,
        prompt: str,
        analysis_type: AnalysisType = AnalysisType.GENERAL,
        persona_context: Optional[Dict[str, Any]] = None,
        max_agents: int = 3,
    ) -> ConsensusAnalysis:
        """Analyze with multiple providers and generate consensus."""

        # Get specialized agents for this analysis type
        agents = self.get_specialized_agents(analysis_type)

        # If no specialized agents, use general agents
        if not agents:
            agents = self.get_available_agents()

        # Limit number of agents
        agents = agents[:max_agents]

        if not agents:
            raise RuntimeError("No AI agents available for consensus analysis")

        # Execute analysis with multiple agents concurrently
        tasks = []
        for agent_id in agents:
            task = self.analyze_single(prompt, analysis_type, agent_id, persona_context)
            tasks.append(task)

        responses = await asyncio.gather(*tasks, return_exceptions=True)

        # Filter out failed responses
        valid_responses = [
            r for r in responses if isinstance(r, AgentResponse) and not r.error
        ]

        if not valid_responses:
            raise RuntimeError("All AI agents failed to analyze the prompt")

        # Generate consensus analysis
        consensus = self._generate_consensus(valid_responses, analysis_type)

        # Store in history
        self.analysis_history.append(consensus)

        return consensus

    def _enhance_prompt_with_context(
        self,
        prompt: str,
        persona_context: Optional[Dict[str, Any]],
        analysis_type: AnalysisType,
    ) -> str:
        """Enhance prompt with persona context and analysis type specific instructions."""

        enhanced_prompt = prompt

        # Add persona context
        if persona_context:
            persona_intro = f"""
You are analyzing from the perspective of {persona_context.get('name', 'Unknown User')},
a {persona_context.get('role', 'User')} with the following characteristics:

Permissions: {', '.join(persona_context.get('permissions', []))}
Goals: {', '.join(persona_context.get('goals', []))}
Behavior Style: {persona_context.get('behavior_style', 'Professional')}
Typical Actions: {', '.join(persona_context.get('typical_actions', []))}

"""
            enhanced_prompt = persona_intro + enhanced_prompt

        # Add analysis type specific instructions
        analysis_instructions = {
            AnalysisType.SECURITY: """
Focus on security aspects:
- Permission enforcement and boundary testing
- Input validation and injection protection
- Authentication and authorization mechanisms
- Data privacy and confidentiality
- Audit logging and monitoring
""",
            AnalysisType.PERFORMANCE: """
Focus on performance aspects:
- Response time measurements and targets
- Throughput and scalability
- Resource utilization (CPU, memory, network)
- Performance bottlenecks and optimization opportunities
- Load testing and stress testing results
""",
            AnalysisType.USABILITY: """
Focus on usability aspects:
- User interface design and navigation
- Error messages and user feedback
- Accessibility and inclusivity
- User workflow efficiency
- Learning curve and discoverability
""",
            AnalysisType.FUNCTIONAL: """
Focus on functional aspects:
- Feature completeness and correctness
- Business logic validation
- Data integrity and consistency
- API behavior and compliance
- Error handling and edge cases
""",
            AnalysisType.INTEGRATION: """
Focus on integration aspects:
- Cross-system compatibility
- Data flow and synchronization
- API integration and consistency
- Service communication and reliability
- End-to-end workflow validation
""",
        }

        if analysis_type in analysis_instructions:
            enhanced_prompt += "\n" + analysis_instructions[analysis_type]

        # Add general analysis guidelines
        enhanced_prompt += """

Provide your analysis in a structured format with:
1. Summary of findings
2. Specific observations
3. Risk assessment (if applicable)
4. Recommendations for improvement
5. Confidence level in your analysis (0-100%)

Be specific, actionable, and consider the persona's perspective and capabilities.
"""

        return enhanced_prompt

    def _calculate_cost(
        self, token_usage: Dict[str, int], cost_per_token: float = 0.0
    ) -> float:
        """Calculate estimated cost for the agent request."""
        total_tokens = token_usage.get("total_tokens", 0)
        return total_tokens * cost_per_token

    def _calculate_confidence_score(
        self, response: str, analysis_type: AnalysisType
    ) -> float:
        """Calculate confidence score based on response quality indicators."""

        # Basic confidence indicators
        confidence_indicators = [
            len(response) > 100,  # Sufficient detail
            "recommendation" in response.lower(),  # Provides recommendations
            "analysis" in response.lower(),  # Contains analysis
            "%" in response,  # Contains metrics or percentages
            any(
                word in response.lower()
                for word in ["good", "bad", "issue", "problem", "improvement"]
            ),  # Clear assessment
        ]

        # Analysis type specific indicators
        type_indicators = {
            AnalysisType.SECURITY: [
                "security",
                "permission",
                "vulnerability",
                "authentication",
            ],
            AnalysisType.PERFORMANCE: [
                "performance",
                "speed",
                "response time",
                "optimization",
            ],
            AnalysisType.USABILITY: ["usability", "user", "interface", "navigation"],
            AnalysisType.FUNCTIONAL: ["function", "feature", "behavior", "logic"],
            AnalysisType.INTEGRATION: [
                "integration",
                "compatibility",
                "api",
                "communication",
            ],
        }

        if analysis_type in type_indicators:
            for indicator in type_indicators[analysis_type]:
                if indicator in response.lower():
                    confidence_indicators.append(True)

        # Calculate confidence as percentage of indicators present
        confidence = (sum(confidence_indicators) / len(confidence_indicators)) * 100
        return min(confidence, 100.0)

    def _generate_consensus(
        self, responses: List[AgentResponse], analysis_type: AnalysisType
    ) -> ConsensusAnalysis:
        """Generate consensus analysis from multiple LLM responses."""

        # Extract key points from each response
        all_points = []
        for response in responses:
            points = self._extract_key_points(response.response)
            all_points.extend(points)

        # Find agreements (points mentioned by multiple LLMs)
        point_counts = {}
        for point in all_points:
            point_counts[point] = point_counts.get(point, 0) + 1

        agreements = [point for point, count in point_counts.items() if count > 1]
        disagreements = [point for point, count in point_counts.items() if count == 1]

        # Generate consensus response
        consensus_response = self._create_consensus_response(
            responses, agreements, disagreements
        )

        # Calculate overall confidence
        avg_confidence = sum(r.confidence_score for r in responses) / len(responses)

        # Generate recommendation
        recommendation = self._generate_recommendation(responses, agreements)

        return ConsensusAnalysis(
            analysis_type=analysis_type,
            responses=responses,
            consensus_response=consensus_response,
            confidence_score=avg_confidence,
            agreements=agreements,
            disagreements=disagreements,
            recommendation=recommendation,
            collaboration_summary={
                "agent_count": len(responses),
                "consensus_method": "multi_agent",
            },
            timestamp=time.time(),
        )

    def _extract_key_points(self, response: str) -> List[str]:
        """Extract key points from an LLM response."""
        # Simple extraction based on sentence patterns
        sentences = response.split(".")
        key_points = []

        for sentence in sentences:
            sentence = sentence.strip()
            if len(sentence) > 20 and any(
                keyword in sentence.lower()
                for keyword in [
                    "recommend",
                    "suggest",
                    "should",
                    "must",
                    "issue",
                    "problem",
                    "good",
                    "excellent",
                    "concern",
                ]
            ):
                key_points.append(sentence)

        return key_points[:5]  # Limit to top 5 points

    def _create_consensus_response(
        self,
        responses: List[AgentResponse],
        agreements: List[str],
        disagreements: List[str],
    ) -> str:
        """Create a consensus response from multiple LLM analyses."""

        consensus = f"Consensus Analysis from {len(responses)} LLM providers:\n\n"

        if agreements:
            consensus += "AGREED FINDINGS:\n"
            for i, agreement in enumerate(agreements[:5], 1):
                consensus += f"{i}. {agreement}\n"
            consensus += "\n"

        if disagreements:
            consensus += "DIVERGENT OPINIONS:\n"
            for i, disagreement in enumerate(disagreements[:3], 1):
                consensus += f"{i}. {disagreement}\n"
            consensus += "\n"

        # Add agent-specific highlights
        consensus += "AGENT HIGHLIGHTS:\n"
        for response in responses:
            consensus += f"- {response.agent_type.value} ({response.agent_id}): {response.response[:100]}...\n"

        return consensus

    def _generate_recommendation(
        self, responses: List[AgentResponse], agreements: List[str]
    ) -> str:
        """Generate overall recommendation based on consensus."""

        if not agreements:
            return "No clear consensus reached. Consider additional analysis or manual review."

        # Priority-based recommendation from highest priority agent
        highest_priority_response = max(
            responses, key=lambda r: self.agent_configs[r.agent_id].priority
        )

        recommendation = "Based on consensus analysis, primary recommendation: "

        # Extract recommendation from highest priority provider
        response_text = highest_priority_response.response.lower()
        if "recommend" in response_text:
            # Extract sentence containing recommendation
            sentences = highest_priority_response.response.split(".")
            for sentence in sentences:
                if "recommend" in sentence.lower():
                    recommendation += sentence.strip()
                    break
        else:
            recommendation += (
                "Follow the agreed findings and address any identified issues."
            )

        return recommendation

    def get_analysis_history(
        self, analysis_type: Optional[AnalysisType] = None
    ) -> List[ConsensusAnalysis]:
        """Get analysis history, optionally filtered by type."""
        if analysis_type:
            return [
                a for a in self.analysis_history if a.analysis_type == analysis_type
            ]
        return self.analysis_history.copy()

    def get_cost_summary(self) -> Dict[str, Any]:
        """Get cost summary across all agents."""
        total_cost = 0.0
        agent_costs = {}

        for analysis in self.analysis_history:
            for response in analysis.responses:
                agent_id = response.agent_id
                # For now, cost is minimal since we're using local Ollama
                cost = 0.0
                agent_costs[agent_id] = agent_costs.get(agent_id, 0.0) + cost
                total_cost += cost

        return {
            "total_cost": total_cost,
            "agent_costs": agent_costs,
            "total_analyses": len(self.analysis_history),
        }

    def load_config(self, config_file: Path):
        """Load agent configuration from file."""
        with open(config_file, "r") as f:
            config_data = json.load(f)

        self.agent_configs.clear()
        for agent_id, agent_data in config_data.get("agents", {}).items():
            agent_data["agent_type"] = AgentType(agent_data["agent_type"])
            config = AgentConfig(**agent_data)
            self.agent_configs[agent_id] = config

    def save_config(self, config_file: Path):
        """Save current agent configuration to file."""
        config_data = {
            "agents": {
                agent_id: {**asdict(config), "agent_type": config.agent_type.value}
                for agent_id, config in self.agent_configs.items()
            }
        }

        with open(config_file, "w") as f:
            json.dump(config_data, f, indent=2)

    def clear_cache(self):
        """Clear response cache."""
        self.response_cache.clear()

    def clear_history(self):
        """Clear analysis history."""
        self.analysis_history.clear()
