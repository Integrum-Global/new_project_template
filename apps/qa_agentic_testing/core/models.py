"""
Domain models for the QA Agentic Testing System.

These are pure Python models that define the business entities.
They are framework-agnostic and can be used with any database.
"""

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional, Union


class TestStatus(Enum):
    """Test status enumeration."""

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    QUEUED = "queued"


class TestType(Enum):
    """Test type enumeration."""

    FUNCTIONAL = "functional"
    SECURITY = "security"
    PERFORMANCE = "performance"
    USABILITY = "usability"
    INTEGRATION = "integration"
    REGRESSION = "regression"
    SMOKE = "smoke"
    ACCEPTANCE = "acceptance"


class AgentType(Enum):
    """Agent type enumeration."""

    BASIC_LLM = "basic_llm"
    ITERATIVE_AGENT = "iterative_agent"
    A2A_AGENT = "a2a_agent"
    SELF_ORGANIZING = "self_organizing"
    MCP_AGENT = "mcp_agent"
    ORCHESTRATION_MANAGER = "orchestration_manager"
    AGENT_POOL = "agent_pool"


class InterfaceType(Enum):
    """Interface type enumeration."""

    CLI = "cli"
    WEB = "web"
    API = "api"
    MOBILE = "mobile"


class Priority(Enum):
    """Priority enumeration."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class TestProject:
    """Test project entity representing an application under test."""

    # Core fields
    project_id: str
    name: str
    description: str
    app_path: str

    # Configuration
    interfaces: List[InterfaceType] = field(default_factory=list)
    test_types: List[TestType] = field(default_factory=list)
    agent_config: Dict[str, Any] = field(default_factory=dict)

    # Discovery results
    discovered_permissions: List[str] = field(default_factory=list)
    discovered_endpoints: List[str] = field(default_factory=list)
    discovered_commands: List[str] = field(default_factory=list)

    # Metadata
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: Optional[datetime] = None
    created_by: Optional[str] = None
    is_active: bool = True
    tenant_id: str = "default"
    tags: List[str] = field(default_factory=list)
    attributes: Dict[str, Any] = field(default_factory=dict)

    # Statistics
    total_test_runs: int = 0
    last_test_run: Optional[datetime] = None
    average_success_rate: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "project_id": self.project_id,
            "name": self.name,
            "description": self.description,
            "app_path": self.app_path,
            "interfaces": [i.value for i in self.interfaces],
            "test_types": [t.value for t in self.test_types],
            "agent_config": self.agent_config,
            "discovered_permissions": self.discovered_permissions,
            "discovered_endpoints": self.discovered_endpoints,
            "discovered_commands": self.discovered_commands,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "created_by": self.created_by,
            "is_active": self.is_active,
            "tenant_id": self.tenant_id,
            "tags": self.tags,
            "attributes": self.attributes,
            "total_test_runs": self.total_test_runs,
            "last_test_run": (
                self.last_test_run.isoformat() if self.last_test_run else None
            ),
            "average_success_rate": self.average_success_rate,
        }


@dataclass
class TestRun:
    """Test run entity representing a single test execution."""

    # Core fields
    run_id: str
    project_id: str
    name: str
    description: str = ""

    # Configuration
    test_types: List[TestType] = field(default_factory=list)
    personas_used: List[str] = field(default_factory=list)
    agent_types: List[AgentType] = field(default_factory=list)
    interfaces_tested: List[InterfaceType] = field(default_factory=list)

    # Execution details
    status: TestStatus = TestStatus.PENDING
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    duration_seconds: Optional[float] = None

    # Results
    total_scenarios: int = 0
    passed_scenarios: int = 0
    failed_scenarios: int = 0
    skipped_scenarios: int = 0
    success_rate: float = 0.0

    # AI Analysis
    ai_insights: List[str] = field(default_factory=list)
    confidence_score: float = 0.0
    agent_consensus: Dict[str, Any] = field(default_factory=dict)

    # Metadata
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    created_by: Optional[str] = None
    tenant_id: str = "default"
    priority: Priority = Priority.MEDIUM

    # Reports
    html_report_path: Optional[str] = None
    json_report_path: Optional[str] = None

    # Error handling
    error_message: Optional[str] = None
    error_details: Dict[str, Any] = field(default_factory=dict)

    @property
    def is_running(self) -> bool:
        """Check if test run is currently running."""
        return self.status in [TestStatus.RUNNING, TestStatus.QUEUED]

    @property
    def is_completed(self) -> bool:
        """Check if test run is completed."""
        return self.status in [
            TestStatus.COMPLETED,
            TestStatus.FAILED,
            TestStatus.CANCELLED,
        ]

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "run_id": self.run_id,
            "project_id": self.project_id,
            "name": self.name,
            "description": self.description,
            "test_types": [t.value for t in self.test_types],
            "personas_used": self.personas_used,
            "agent_types": [a.value for a in self.agent_types],
            "interfaces_tested": [i.value for i in self.interfaces_tested],
            "status": self.status.value,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": (
                self.completed_at.isoformat() if self.completed_at else None
            ),
            "duration_seconds": self.duration_seconds,
            "total_scenarios": self.total_scenarios,
            "passed_scenarios": self.passed_scenarios,
            "failed_scenarios": self.failed_scenarios,
            "skipped_scenarios": self.skipped_scenarios,
            "success_rate": self.success_rate,
            "ai_insights": self.ai_insights,
            "confidence_score": self.confidence_score,
            "agent_consensus": self.agent_consensus,
            "created_at": self.created_at.isoformat(),
            "created_by": self.created_by,
            "tenant_id": self.tenant_id,
            "priority": self.priority.value,
            "html_report_path": self.html_report_path,
            "json_report_path": self.json_report_path,
            "error_message": self.error_message,
            "error_details": self.error_details,
        }


@dataclass
class TestResult:
    """Individual test result entity."""

    # Core fields
    result_id: str
    run_id: str
    scenario_id: str
    scenario_name: str

    # Test details
    test_type: TestType
    persona: str
    interface_type: InterfaceType

    # Execution
    status: TestStatus
    started_at: datetime
    completed_at: Optional[datetime] = None
    duration_ms: Optional[int] = None

    # Results
    passed: bool = False
    expected_result: str = ""
    actual_result: str = ""
    validation_details: Dict[str, Any] = field(default_factory=dict)

    # AI Analysis
    ai_analysis: str = ""
    confidence_score: float = 0.0
    agent_insights: List[str] = field(default_factory=list)

    # Performance metrics
    response_time_ms: Optional[int] = None
    memory_usage_mb: Optional[float] = None
    cpu_usage_percent: Optional[float] = None

    # Error handling
    error_message: Optional[str] = None
    error_traceback: Optional[str] = None

    # Metadata
    tenant_id: str = "default"

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "result_id": self.result_id,
            "run_id": self.run_id,
            "scenario_id": self.scenario_id,
            "scenario_name": self.scenario_name,
            "test_type": self.test_type.value,
            "persona": self.persona,
            "interface_type": self.interface_type.value,
            "status": self.status.value,
            "started_at": self.started_at.isoformat(),
            "completed_at": (
                self.completed_at.isoformat() if self.completed_at else None
            ),
            "duration_ms": self.duration_ms,
            "passed": self.passed,
            "expected_result": self.expected_result,
            "actual_result": self.actual_result,
            "validation_details": self.validation_details,
            "ai_analysis": self.ai_analysis,
            "confidence_score": self.confidence_score,
            "agent_insights": self.agent_insights,
            "response_time_ms": self.response_time_ms,
            "memory_usage_mb": self.memory_usage_mb,
            "cpu_usage_percent": self.cpu_usage_percent,
            "error_message": self.error_message,
            "error_traceback": self.error_traceback,
            "tenant_id": self.tenant_id,
        }


@dataclass
class AgentSession:
    """Agent session entity for tracking agent interactions."""

    # Core fields
    session_id: str
    run_id: str
    agent_type: AgentType
    agent_name: str

    # Configuration
    agent_config: Dict[str, Any] = field(default_factory=dict)
    specializations: List[str] = field(default_factory=list)

    # Session details
    started_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    ended_at: Optional[datetime] = None
    is_active: bool = True

    # Interaction tracking
    total_interactions: int = 0
    successful_interactions: int = 0
    failed_interactions: int = 0

    # Performance
    average_response_time_ms: float = 0.0
    total_tokens_used: int = 0
    cost_estimate: float = 0.0

    # Memory and collaboration
    shared_memory_keys: List[str] = field(default_factory=list)
    collaboration_partners: List[str] = field(default_factory=list)

    # Results
    insights_generated: List[str] = field(default_factory=list)
    consensus_votes: Dict[str, Any] = field(default_factory=dict)

    # Metadata
    tenant_id: str = "default"

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "session_id": self.session_id,
            "run_id": self.run_id,
            "agent_type": self.agent_type.value,
            "agent_name": self.agent_name,
            "agent_config": self.agent_config,
            "specializations": self.specializations,
            "started_at": self.started_at.isoformat(),
            "ended_at": self.ended_at.isoformat() if self.ended_at else None,
            "is_active": self.is_active,
            "total_interactions": self.total_interactions,
            "successful_interactions": self.successful_interactions,
            "failed_interactions": self.failed_interactions,
            "average_response_time_ms": self.average_response_time_ms,
            "total_tokens_used": self.total_tokens_used,
            "cost_estimate": self.cost_estimate,
            "shared_memory_keys": self.shared_memory_keys,
            "collaboration_partners": self.collaboration_partners,
            "insights_generated": self.insights_generated,
            "consensus_votes": self.consensus_votes,
            "tenant_id": self.tenant_id,
        }


@dataclass
class TestMetrics:
    """Test metrics for analytics and reporting."""

    # Core fields
    metrics_id: str
    project_id: Optional[str] = None
    run_id: Optional[str] = None

    # Time period
    period_start: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    period_end: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    # Execution metrics
    total_runs: int = 0
    successful_runs: int = 0
    failed_runs: int = 0
    average_duration_seconds: float = 0.0

    # Quality metrics
    average_success_rate: float = 0.0
    average_confidence_score: float = 0.0
    total_scenarios_executed: int = 0
    unique_bugs_found: int = 0

    # Performance metrics
    average_response_time_ms: float = 0.0
    peak_response_time_ms: float = 0.0
    total_api_calls: int = 0

    # Agent metrics
    agents_used: Dict[str, int] = field(default_factory=dict)
    total_agent_interactions: int = 0
    total_tokens_consumed: int = 0
    estimated_cost: float = 0.0

    # Trend data
    success_rate_trend: List[float] = field(default_factory=list)
    performance_trend: List[float] = field(default_factory=list)

    # Metadata
    tenant_id: str = "default"
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "metrics_id": self.metrics_id,
            "project_id": self.project_id,
            "run_id": self.run_id,
            "period_start": self.period_start.isoformat(),
            "period_end": self.period_end.isoformat(),
            "total_runs": self.total_runs,
            "successful_runs": self.successful_runs,
            "failed_runs": self.failed_runs,
            "average_duration_seconds": self.average_duration_seconds,
            "average_success_rate": self.average_success_rate,
            "average_confidence_score": self.average_confidence_score,
            "total_scenarios_executed": self.total_scenarios_executed,
            "unique_bugs_found": self.unique_bugs_found,
            "average_response_time_ms": self.average_response_time_ms,
            "peak_response_time_ms": self.peak_response_time_ms,
            "total_api_calls": self.total_api_calls,
            "agents_used": self.agents_used,
            "total_agent_interactions": self.total_agent_interactions,
            "total_tokens_consumed": self.total_tokens_consumed,
            "estimated_cost": self.estimated_cost,
            "success_rate_trend": self.success_rate_trend,
            "performance_trend": self.performance_trend,
            "tenant_id": self.tenant_id,
            "created_at": self.created_at.isoformat(),
        }


# Helper functions for model creation
def create_test_project(name: str, app_path: str, description: str = "") -> TestProject:
    """Create a new test project with default settings."""
    return TestProject(
        project_id=str(uuid.uuid4()),
        name=name,
        description=description,
        app_path=app_path,
        interfaces=[InterfaceType.CLI, InterfaceType.WEB, InterfaceType.API],
        test_types=[TestType.FUNCTIONAL, TestType.SECURITY, TestType.PERFORMANCE],
    )


def create_test_run(project_id: str, name: str, description: str = "") -> TestRun:
    """Create a new test run with default settings."""
    return TestRun(
        run_id=str(uuid.uuid4()),
        project_id=project_id,
        name=name,
        description=description,
        test_types=[TestType.FUNCTIONAL, TestType.SECURITY],
        agent_types=[AgentType.A2A_AGENT, AgentType.ITERATIVE_AGENT],
    )


def create_test_result(
    run_id: str,
    scenario_id: str,
    scenario_name: str,
    test_type: TestType,
    persona: str,
    interface_type: InterfaceType,
) -> TestResult:
    """Create a new test result with default settings."""
    return TestResult(
        result_id=str(uuid.uuid4()),
        run_id=run_id,
        scenario_id=scenario_id,
        scenario_name=scenario_name,
        test_type=test_type,
        persona=persona,
        interface_type=interface_type,
        status=TestStatus.PENDING,
        started_at=datetime.now(timezone.utc),
    )
