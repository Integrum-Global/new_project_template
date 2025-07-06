"""Distributed AI Agent Network using MCP and Kailash SDK.

This example demonstrates how to build a network of AI agents that can discover
each other, share capabilities, and collaborate on complex tasks using MCP
for communication and Kailash workflows for processing.

Features demonstrated:
- Multi-agent architecture with MCP communication
- Capability-based agent discovery
- Task delegation and coordination
- Result aggregation and consensus
- Fault tolerance and failover
"""

import asyncio
import json
import logging
import time
import uuid
from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, List, Optional, Set

from kailash import LocalRuntime, WorkflowBuilder
from kailash.mcp_server import (
    MCPClient,
    MCPServer,
    ServiceRegistry,
    discover_mcp_servers,
)
from kailash.mcp_server.auth import APIKeyAuth
from kailash.nodes.ai import LLMAgentNode
from kailash.nodes.logic import MergeNode, SwitchNode

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class AgentType(Enum):
    """Types of AI agents in the network."""

    COORDINATOR = "coordinator"
    ANALYST = "analyst"
    PROCESSOR = "processor"
    VALIDATOR = "validator"


@dataclass
class TaskRequest:
    """Represents a task request in the agent network."""

    task_id: str
    task_type: str
    payload: Dict[str, Any]
    requester_id: str
    priority: int = 1
    timeout: float = 300.0
    created_at: float = None

    def __post_init__(self):
        if self.created_at is None:
            self.created_at = time.time()


@dataclass
class TaskResult:
    """Represents a task result from an agent."""

    task_id: str
    agent_id: str
    agent_type: str
    result: Dict[str, Any]
    confidence: float
    processing_time: float
    timestamp: float = None

    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = time.time()


class BaseAgent(ABC):
    """Base class for all agents in the network."""

    def __init__(
        self,
        agent_id: str,
        agent_type: AgentType,
        capabilities: List[str],
        port: int = None,
    ):
        """Initialize the base agent."""
        self.agent_id = agent_id
        self.agent_type = agent_type
        self.capabilities = capabilities
        self.port = port or (8080 + hash(agent_id) % 1000)

        # Setup authentication
        self.auth = APIKeyAuth(
            {
                f"agent_{agent_id}": {
                    "permissions": ["agent", "tasks", "coordination"]
                },
                "network_admin": {
                    "permissions": ["admin", "agent", "tasks", "coordination"]
                },
            }
        )

        # Initialize MCP server
        self.server = MCPServer(
            f"agent_{agent_id}", auth_provider=self.auth, enable_metrics=True
        )

        # Initialize Kailash runtime
        self.runtime = LocalRuntime()

        # Network state
        self.known_agents: Dict[str, Dict[str, Any]] = {}
        self.active_tasks: Dict[str, TaskRequest] = {}
        self.completed_tasks: Dict[str, TaskResult] = {}

        # Register MCP tools
        self._register_agent_tools()

        logger.info(f"Initialized {agent_type.value} agent: {agent_id}")

    def _register_agent_tools(self):
        """Register MCP tools for agent communication."""

        @self.server.tool(required_permission="tasks")
        def submit_task(task_type: str, payload: dict, priority: int = 1) -> dict:
            """Submit a task to this agent."""
            task_id = str(uuid.uuid4())
            task = TaskRequest(
                task_id=task_id,
                task_type=task_type,
                payload=payload,
                requester_id="external",
                priority=priority,
            )

            # Process task based on agent capabilities
            if task_type in self.capabilities:
                result = self._process_task(task)
                return {
                    "task_id": task_id,
                    "status": "completed",
                    "result": result.__dict__ if result else None,
                }
            else:
                return {
                    "task_id": task_id,
                    "status": "rejected",
                    "reason": f"Task type '{task_type}' not supported by this agent",
                }

        @self.server.tool(required_permission="coordination")
        def register_peer_agent(agent_id: str, agent_info: dict) -> dict:
            """Register a peer agent in the network."""
            self.known_agents[agent_id] = {**agent_info, "registered_at": time.time()}
            logger.info(f"Registered peer agent: {agent_id}")
            return {"status": "registered", "agent_id": agent_id}

        @self.server.tool(required_permission="agent")
        def get_agent_status() -> dict:
            """Get current agent status and capabilities."""
            return {
                "agent_id": self.agent_id,
                "agent_type": self.agent_type.value,
                "capabilities": self.capabilities,
                "active_tasks": len(self.active_tasks),
                "completed_tasks": len(self.completed_tasks),
                "known_agents": len(self.known_agents),
                "uptime": time.time() - getattr(self, "_start_time", time.time()),
            }

        @self.server.tool(required_permission="coordination")
        def delegate_task(target_agent_id: str, task_type: str, payload: dict) -> dict:
            """Delegate a task to another agent."""
            if target_agent_id not in self.known_agents:
                return {"error": "Unknown target agent", "agent_id": target_agent_id}

            # This would normally make an MCP call to the target agent
            # For demo purposes, we'll simulate the delegation
            task_id = str(uuid.uuid4())
            return {
                "task_id": task_id,
                "target_agent": target_agent_id,
                "task_type": task_type,
                "status": "delegated",
            }

        @self.server.resource("agent://info")
        def get_agent_info():
            """Get detailed agent information."""
            return {
                "agent_id": self.agent_id,
                "agent_type": self.agent_type.value,
                "capabilities": self.capabilities,
                "network_info": {
                    "port": self.port,
                    "auth_required": True,
                    "mcp_version": "1.0",
                },
                "statistics": {
                    "tasks_processed": len(self.completed_tasks),
                    "network_size": len(self.known_agents),
                    "average_response_time": self._calculate_avg_response_time(),
                },
            }

    @abstractmethod
    def _process_task(self, task: TaskRequest) -> Optional[TaskResult]:
        """Process a task specific to this agent type."""
        pass

    def _calculate_avg_response_time(self) -> float:
        """Calculate average response time for completed tasks."""
        if not self.completed_tasks:
            return 0.0

        total_time = sum(
            result.processing_time for result in self.completed_tasks.values()
        )
        return total_time / len(self.completed_tasks)

    async def discover_network_agents(self) -> List[Dict[str, Any]]:
        """Discover other agents in the network."""
        try:
            # Discover MCP servers with agent capabilities
            servers = await discover_mcp_servers(capability="agent")

            agents = []
            for server in servers:
                if server.name != f"agent_{self.agent_id}":  # Exclude self
                    agents.append(
                        {
                            "agent_id": server.name.replace("agent_", ""),
                            "name": server.name,
                            "capabilities": server.capabilities,
                            "transport": server.transport,
                            "metadata": getattr(server, "metadata", {}),
                        }
                    )

            logger.info(f"Discovered {len(agents)} network agents")
            return agents

        except Exception as e:
            logger.error(f"Agent discovery failed: {e}")
            return []

    async def start(self):
        """Start the agent server."""
        self._start_time = time.time()
        logger.info(f"Starting agent {self.agent_id} on port {self.port}")

        # Start server in background
        asyncio.create_task(self._run_server())

        # Discover and register with network
        await self._join_network()

    async def _run_server(self):
        """Run the MCP server."""
        self.server.run(enable_http_transport=True, host="localhost", port=self.port)

    async def _join_network(self):
        """Join the agent network."""
        # Discover existing agents
        agents = await self.discover_network_agents()

        # Register with discovered agents
        for agent in agents:
            try:
                # Create client to register with peer
                client_config = {
                    "name": f"client_{self.agent_id}",
                    "transport": "http",
                    "url": f"http://localhost:{8080}",  # Default port for demo
                    "auth": {
                        "type": "api_key",
                        "key": f"agent_{self.agent_id}",
                        "header": "X-API-Key",
                    },
                }

                client = MCPClient(client_config)
                await client.connect()

                # Register with peer agent
                await client.call_tool(
                    "register_peer_agent",
                    {
                        "agent_id": self.agent_id,
                        "agent_info": {
                            "agent_type": self.agent_type.value,
                            "capabilities": self.capabilities,
                            "port": self.port,
                        },
                    },
                )

                await client.disconnect()

            except Exception as e:
                logger.warning(
                    f"Failed to register with agent {agent['agent_id']}: {e}"
                )


class CoordinatorAgent(BaseAgent):
    """Coordinator agent that orchestrates complex tasks."""

    def __init__(self, agent_id: str = "coordinator_001"):
        super().__init__(
            agent_id=agent_id,
            agent_type=AgentType.COORDINATOR,
            capabilities=[
                "task_coordination",
                "workflow_orchestration",
                "result_aggregation",
            ],
            port=8080,
        )

    def _process_task(self, task: TaskRequest) -> Optional[TaskResult]:
        """Process coordination tasks."""
        start_time = time.time()

        try:
            if task.task_type == "task_coordination":
                result = self._coordinate_complex_task(task.payload)
            elif task.task_type == "workflow_orchestration":
                result = self._orchestrate_workflow(task.payload)
            elif task.task_type == "result_aggregation":
                result = self._aggregate_results(task.payload)
            else:
                return None

            processing_time = time.time() - start_time

            return TaskResult(
                task_id=task.task_id,
                agent_id=self.agent_id,
                agent_type=self.agent_type.value,
                result=result,
                confidence=0.9,
                processing_time=processing_time,
            )

        except Exception as e:
            logger.error(f"Task processing failed: {e}")
            return None

    def _coordinate_complex_task(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Coordinate a complex multi-agent task."""
        # Build coordination workflow
        workflow = WorkflowBuilder()

        # Add coordination logic
        workflow.add_node(
            "SwitchNode", node_id="task_router", switch_key="task_complexity"
        )

        workflow.add_node("MergeNode", node_id="result_merger")

        # Execute coordination workflow
        result = self.runtime.execute(workflow, payload)

        return {
            "coordination_result": result,
            "delegated_tasks": payload.get("subtasks", []),
            "coordination_strategy": "divide_and_conquer",
        }

    def _orchestrate_workflow(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Orchestrate a multi-agent workflow."""
        return {
            "workflow_id": str(uuid.uuid4()),
            "steps_completed": len(payload.get("steps", [])),
            "orchestration_result": "workflow_orchestrated",
        }

    def _aggregate_results(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Aggregate results from multiple agents."""
        results = payload.get("results", [])

        return {
            "aggregated_count": len(results),
            "confidence_score": sum(r.get("confidence", 0) for r in results)
            / max(len(results), 1),
            "aggregation_method": "weighted_average",
        }


class AnalystAgent(BaseAgent):
    """Analyst agent specialized in data analysis."""

    def __init__(self, agent_id: str = "analyst_001"):
        super().__init__(
            agent_id=agent_id,
            agent_type=AgentType.ANALYST,
            capabilities=["data_analysis", "pattern_recognition", "insight_generation"],
            port=8081,
        )

    def _process_task(self, task: TaskRequest) -> Optional[TaskResult]:
        """Process analysis tasks."""
        start_time = time.time()

        try:
            if task.task_type == "data_analysis":
                result = self._analyze_data(task.payload)
            elif task.task_type == "pattern_recognition":
                result = self._recognize_patterns(task.payload)
            elif task.task_type == "insight_generation":
                result = self._generate_insights(task.payload)
            else:
                return None

            processing_time = time.time() - start_time

            return TaskResult(
                task_id=task.task_id,
                agent_id=self.agent_id,
                agent_type=self.agent_type.value,
                result=result,
                confidence=0.85,
                processing_time=processing_time,
            )

        except Exception as e:
            logger.error(f"Analysis task failed: {e}")
            return None

    def _analyze_data(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Perform data analysis using Kailash workflows."""
        # Build analysis workflow
        workflow = WorkflowBuilder()

        # Add LLM agent for analysis
        workflow.add_node(
            "LLMAgentNode",
            node_id="data_analyzer",
            prompt_template="Analyze this data and provide insights: {data}",
            model_name="gpt-3.5-turbo",
            temperature=0.1,
        )

        # Execute analysis
        result = self.runtime.execute(workflow, payload)

        return {
            "analysis_type": "statistical_analysis",
            "data_points": len(payload.get("data", [])),
            "analysis_result": result,
            "key_metrics": ["mean", "median", "std_dev"],
        }

    def _recognize_patterns(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Recognize patterns in data."""
        return {
            "patterns_found": ["trend_upward", "seasonal_variation"],
            "pattern_confidence": 0.78,
            "pattern_strength": "moderate",
        }

    def _generate_insights(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Generate insights from analysis."""
        return {
            "insights": [
                "Data shows strong growth trend",
                "Seasonal patterns detected",
                "Anomalies in Q3 data",
            ],
            "insight_confidence": 0.82,
            "actionable_recommendations": 3,
        }


class ProcessorAgent(BaseAgent):
    """Processor agent for data transformation and processing."""

    def __init__(self, agent_id: str = "processor_001"):
        super().__init__(
            agent_id=agent_id,
            agent_type=AgentType.PROCESSOR,
            capabilities=["data_processing", "transformation", "enrichment"],
            port=8082,
        )

    def _process_task(self, task: TaskRequest) -> Optional[TaskResult]:
        """Process data processing tasks."""
        start_time = time.time()

        try:
            if task.task_type == "data_processing":
                result = self._process_data(task.payload)
            elif task.task_type == "transformation":
                result = self._transform_data(task.payload)
            elif task.task_type == "enrichment":
                result = self._enrich_data(task.payload)
            else:
                return None

            processing_time = time.time() - start_time

            return TaskResult(
                task_id=task.task_id,
                agent_id=self.agent_id,
                agent_type=self.agent_type.value,
                result=result,
                confidence=0.92,
                processing_time=processing_time,
            )

        except Exception as e:
            logger.error(f"Processing task failed: {e}")
            return None

    def _process_data(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Process raw data."""
        data = payload.get("data", [])

        return {
            "processed_records": len(data),
            "processing_method": "batch_processing",
            "output_format": "structured_json",
            "quality_score": 0.95,
        }

    def _transform_data(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Transform data format."""
        return {
            "transformation_type": "normalization",
            "input_format": payload.get("input_format", "unknown"),
            "output_format": payload.get("output_format", "json"),
            "transformation_success": True,
        }

    def _enrich_data(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Enrich data with additional information."""
        return {
            "enrichment_sources": ["external_api", "reference_data"],
            "enrichment_fields": ["geo_location", "demographics"],
            "enrichment_success_rate": 0.88,
        }


async def demo_agent_network():
    """Demonstrate the distributed agent network."""
    print("🤖 Starting Distributed AI Agent Network Demo")

    # Create agents
    coordinator = CoordinatorAgent("coord_001")
    analyst = AnalystAgent("analyst_001")
    processor = ProcessorAgent("proc_001")

    agents = [coordinator, analyst, processor]

    try:
        # Start all agents
        print("\n🚀 Starting agents...")
        for agent in agents:
            await agent.start()
            await asyncio.sleep(1)  # Give time to start

        print("✅ All agents started successfully")

        # Demo task coordination
        print("\n📋 Demonstrating task coordination...")

        # Submit a complex task to coordinator
        task_result = await coordinator._process_task(
            TaskRequest(
                task_id="demo_001",
                task_type="task_coordination",
                payload={
                    "task_complexity": "high",
                    "subtasks": [
                        {"type": "data_analysis", "target": "analyst"},
                        {"type": "data_processing", "target": "processor"},
                    ],
                },
                requester_id="demo",
            )
        )

        if task_result:
            print(f"Coordination result: {json.dumps(task_result.__dict__, indent=2)}")

        # Demo direct agent task
        print("\n🔍 Demonstrating direct agent task...")

        analysis_result = await analyst._process_task(
            TaskRequest(
                task_id="demo_002",
                task_type="data_analysis",
                payload={
                    "data": [1, 2, 3, 4, 5, 6, 7, 8, 9, 10],
                    "analysis_type": "statistical",
                },
                requester_id="demo",
            )
        )

        if analysis_result:
            print(f"Analysis result: {json.dumps(analysis_result.__dict__, indent=2)}")

        # Demo processing task
        print("\n⚙️ Demonstrating processing task...")

        processing_result = await processor._process_task(
            TaskRequest(
                task_id="demo_003",
                task_type="data_processing",
                payload={
                    "data": ["item1", "item2", "item3"],
                    "processing_type": "batch",
                },
                requester_id="demo",
            )
        )

        if processing_result:
            print(
                f"Processing result: {json.dumps(processing_result.__dict__, indent=2)}"
            )

        print("\n🌐 Agent network status:")
        for agent in agents:
            status = agent.server.tool_handlers.get("get_agent_status", lambda: {})()
            print(
                f"  {agent.agent_id}: {status.get('active_tasks', 0)} active, {status.get('completed_tasks', 0)} completed"
            )

    except Exception as e:
        logger.error(f"Demo failed: {e}")

    finally:
        print("\n🛑 Shutting down agents...")
        # In a real implementation, you would properly shut down the servers
        print("✅ Demo completed")


if __name__ == "__main__":
    asyncio.run(demo_agent_network())
