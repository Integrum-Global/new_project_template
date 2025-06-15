#!/usr/bin/env python3
"""
Scenario Generation System for QA Agentic Testing

This module automatically generates comprehensive test scenarios based on application
discovery, persona analysis, and intelligent pattern matching.
"""

import asyncio
import itertools
import json
import logging
from dataclasses import asdict, dataclass
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

from .personas import Persona, PersonaManager


class ScenarioType(Enum):
    """Types of test scenarios that can be generated."""

    FUNCTIONAL = "functional"
    SECURITY = "security"
    PERFORMANCE = "performance"
    USABILITY = "usability"
    INTEGRATION = "integration"
    ACCESSIBILITY = "accessibility"
    REGRESSION = "regression"


class InterfaceType(Enum):
    """Application interface types."""

    CLI = "cli"
    WEB = "web"
    API = "api"
    MOBILE = "mobile"


@dataclass
class TestStep:
    """Individual step within a test scenario."""

    step_id: str
    description: str
    action: str
    expected_result: str
    validation_criteria: List[str]
    interface: InterfaceType
    parameters: Dict[str, Any] = None
    prerequisites: List[str] = None
    cleanup_required: bool = False

    def __post_init__(self):
        if self.parameters is None:
            self.parameters = {}
        if self.prerequisites is None:
            self.prerequisites = []


@dataclass
class TestScenario:
    """Complete test scenario with multiple steps and validation criteria."""

    scenario_id: str
    name: str
    description: str
    scenario_type: ScenarioType
    target_personas: List[str]  # Persona keys
    interface_types: List[InterfaceType]
    priority: str  # high, medium, low
    estimated_duration_minutes: int
    steps: List[TestStep]
    success_criteria: List[str]
    failure_conditions: List[str]
    performance_targets: Dict[str, Any] = None
    security_considerations: List[str] = None
    business_impact: str = "medium"
    tags: List[str] = None

    def __post_init__(self):
        if self.performance_targets is None:
            self.performance_targets = {}
        if self.security_considerations is None:
            self.security_considerations = []
        if self.tags is None:
            self.tags = []

    def get_persona_expectations(self, persona_key: str) -> Dict[str, Any]:
        """Get expected outcomes for a specific persona."""
        return {
            "expected_success_rate": self._calculate_persona_success_rate(persona_key),
            "expected_failures": self._get_expected_failures(persona_key),
            "validation_adjustments": self._get_validation_adjustments(persona_key),
        }

    def _calculate_persona_success_rate(self, persona_key: str) -> float:
        """Calculate expected success rate for persona."""
        if "admin" in persona_key.lower():
            return 95.0  # Admins should pass most tests
        elif "manager" in persona_key.lower():
            return 75.0  # Managers have some restrictions
        elif "user" in persona_key.lower():
            return 60.0  # Regular users more limited
        elif "security" in persona_key.lower():
            return 90.0  # Security officers should have high success rate
        else:
            return 70.0  # Default expectation

    def _get_expected_failures(self, persona_key: str) -> List[str]:
        """Get list of steps expected to fail for this persona."""
        expected_failures = []

        for step in self.steps:
            # Check if step involves actions persona shouldn't be able to perform
            if "create" in step.action.lower() and "user" in persona_key.lower():
                expected_failures.append(step.step_id)
            elif "delete" in step.action.lower() and "manager" in persona_key.lower():
                expected_failures.append(step.step_id)

        return expected_failures

    def _get_validation_adjustments(self, persona_key: str) -> Dict[str, str]:
        """Get persona-specific validation adjustments."""
        if "security" in persona_key.lower():
            return {"focus": "security_validations", "enhanced_checks": True}
        elif "performance" in persona_key.lower():
            return {"focus": "performance_metrics", "timing_critical": True}
        else:
            return {"focus": "standard_validations", "enhanced_checks": False}

    def to_dict(self) -> Dict[str, Any]:
        """Convert scenario to dictionary format."""
        data = asdict(self)
        # Convert enums to string values
        data["scenario_type"] = self.scenario_type.value

        # Handle interface_types - they might be strings or enums
        interface_values = []
        for iface in self.interface_types:
            if isinstance(iface, InterfaceType):
                interface_values.append(iface.value)
            elif isinstance(iface, str):
                interface_values.append(iface)
            else:
                interface_values.append(str(iface))
        data["interface_types"] = interface_values

        # Handle steps
        step_list = []
        for step in self.steps:
            step_data = asdict(step)
            if isinstance(step.interface, InterfaceType):
                step_data["interface"] = step.interface.value
            elif isinstance(step.interface, str):
                step_data["interface"] = step.interface
            else:
                step_data["interface"] = str(step.interface)
            step_list.append(step_data)
        data["steps"] = step_list

        return data

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "TestScenario":
        """Create scenario from dictionary."""
        # Convert string values back to enums
        data["scenario_type"] = ScenarioType(data["scenario_type"])
        data["interface_types"] = [
            InterfaceType(iface) for iface in data["interface_types"]
        ]

        # Convert steps
        steps = []
        for step_data in data["steps"]:
            step_data["interface"] = InterfaceType(step_data["interface"])
            steps.append(TestStep(**step_data))
        data["steps"] = steps

        return cls(**data)


class ScenarioGenerator:
    """Generates test scenarios automatically based on application analysis."""

    def __init__(self, templates_dir: Optional[Path] = None):
        self.templates_dir = (
            templates_dir or Path(__file__).parent.parent / "templates" / "scenarios"
        )
        self.scenario_templates: Dict[str, Dict[str, Any]] = {}
        self.generated_scenarios: Dict[str, TestScenario] = {}
        self.logger = logging.getLogger(__name__)
        self._load_scenario_templates()

    def _load_scenario_templates(self):
        """Load scenario templates from files."""
        if self.templates_dir.exists():
            for template_file in self.templates_dir.glob("*.json"):
                try:
                    with open(template_file, "r") as f:
                        template_data = json.load(f)
                        template_name = template_file.stem
                        self.scenario_templates[template_name] = template_data
                except Exception as e:
                    print(
                        f"Warning: Could not load scenario template {template_file}: {e}"
                    )

    def analyze_application(self, app_structure: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze application structure to determine testing needs."""
        analysis = {
            "interfaces": [],
            "operations": [],
            "data_entities": [],
            "security_features": [],
            "performance_targets": {},
            "business_workflows": [],
        }

        # Analyze interfaces - convert strings to InterfaceType enums
        raw_interfaces = app_structure.get("interfaces", [])
        for interface_name in raw_interfaces:
            if isinstance(interface_name, str):
                interface_name = interface_name.lower()
                if interface_name in ["cli", "command", "terminal"]:
                    analysis["interfaces"].append(InterfaceType.CLI)
                elif interface_name in ["web", "http", "html", "ui"]:
                    analysis["interfaces"].append(InterfaceType.WEB)
                elif interface_name in ["api", "rest", "graphql", "endpoint"]:
                    analysis["interfaces"].append(InterfaceType.API)
                elif interface_name in ["mobile", "app", "ios", "android"]:
                    analysis["interfaces"].append(InterfaceType.MOBILE)
            elif isinstance(interface_name, InterfaceType):
                analysis["interfaces"].append(interface_name)

        # Fallback: check for legacy boolean flags
        if app_structure.get("has_cli", False):
            analysis["interfaces"].append(InterfaceType.CLI)
        if app_structure.get("has_web", False):
            analysis["interfaces"].append(InterfaceType.WEB)
        if app_structure.get("has_api", False):
            analysis["interfaces"].append(InterfaceType.API)

        # Extract operations from discovered APIs, CLI commands, etc.
        for operation in app_structure.get("operations", []):
            analysis["operations"].append(
                {
                    "name": operation.get("name"),
                    "type": operation.get("type", "unknown"),
                    "permissions_required": operation.get("permissions", []),
                    "interface": operation.get("interface", "unknown"),
                }
            )

        # Identify data entities
        analysis["data_entities"] = app_structure.get("data_entities", [])

        # Security feature detection
        if app_structure.get("has_authentication", False):
            analysis["security_features"].append("authentication")
        if app_structure.get("has_authorization", False):
            analysis["security_features"].append("authorization")
        if app_structure.get("has_audit_logging", False):
            analysis["security_features"].append("audit_logging")

        # Performance targets from documentation or defaults
        analysis["performance_targets"] = app_structure.get(
            "performance_targets",
            {"response_time_ms": 200, "throughput_rps": 100, "concurrent_users": 50},
        )

        return analysis

    def generate_scenarios_for_personas(
        self,
        personas: List[Persona],
        app_analysis: Dict[str, Any],
        scenario_types: Optional[List[ScenarioType]] = None,
    ) -> List[TestScenario]:
        """Generate scenarios tailored for specific personas."""

        if scenario_types is None:
            scenario_types = [
                ScenarioType.FUNCTIONAL,
                ScenarioType.SECURITY,
                ScenarioType.PERFORMANCE,
                ScenarioType.USABILITY,
            ]

        scenarios = []

        for scenario_type in scenario_types:
            for persona in personas:
                scenario = self._generate_scenario_for_persona(
                    persona, scenario_type, app_analysis
                )
                if scenario:
                    scenarios.append(scenario)
                    self.generated_scenarios[scenario.scenario_id] = scenario

        return scenarios

    def _generate_scenario_for_persona(
        self,
        persona: Persona,
        scenario_type: ScenarioType,
        app_analysis: Dict[str, Any],
    ) -> Optional[TestScenario]:
        """Generate a specific scenario for a persona and scenario type."""

        scenario_generators = {
            ScenarioType.FUNCTIONAL: self._generate_functional_scenario,
            ScenarioType.SECURITY: self._generate_security_scenario,
            ScenarioType.PERFORMANCE: self._generate_performance_scenario,
            ScenarioType.USABILITY: self._generate_usability_scenario,
            ScenarioType.INTEGRATION: self._generate_integration_scenario,
        }

        generator = scenario_generators.get(scenario_type)
        if generator:
            return generator(persona, app_analysis)

        return None

    def _generate_functional_scenario(
        self, persona: Persona, app_analysis: Dict[str, Any]
    ) -> TestScenario:
        """Generate functional testing scenario."""

        scenario_id = f"functional_{persona.key}_{len(self.generated_scenarios)}"

        # Generate steps based on persona permissions and app operations
        steps = []
        step_counter = 1

        # Common workflow: Login -> Navigate -> Perform Operations -> Logout
        for interface in app_analysis["interfaces"]:

            # Authentication step
            if "authentication" in app_analysis["security_features"]:
                steps.append(
                    TestStep(
                        step_id=f"step_{step_counter}",
                        description=f"Authenticate as {persona.name}",
                        action="authenticate",
                        expected_result="Successful authentication",
                        validation_criteria=[
                            "Authentication successful",
                            "Session established",
                        ],
                        interface=interface,
                        parameters={"persona": persona.key},
                    )
                )
                step_counter += 1

            # Operation steps based on persona permissions
            for operation in app_analysis["operations"]:
                if self._persona_can_attempt_operation(persona, operation):
                    expected_success = self._should_operation_succeed(
                        persona, operation
                    )

                    steps.append(
                        TestStep(
                            step_id=f"step_{step_counter}",
                            description=f"Attempt {operation['name']} operation",
                            action=operation["name"],
                            expected_result=(
                                "Success" if expected_success else "Permission denied"
                            ),
                            validation_criteria=self._get_operation_validation_criteria(
                                operation, expected_success
                            ),
                            interface=interface,
                            parameters={
                                "operation": operation["name"],
                                "persona_permissions": persona.permissions,
                            },
                        )
                    )
                    step_counter += 1

        return TestScenario(
            scenario_id=scenario_id,
            name=f"Functional Testing - {persona.name}",
            description=f"Comprehensive functional testing from {persona.role} perspective",
            scenario_type=ScenarioType.FUNCTIONAL,
            target_personas=[persona.key],
            interface_types=app_analysis["interfaces"],
            priority="high",
            estimated_duration_minutes=len(steps) * 2,  # 2 minutes per step
            steps=steps,
            success_criteria=[
                "All expected operations succeed",
                "All unauthorized operations are properly denied",
                "No system errors occur",
                f"Performance within targets: {app_analysis['performance_targets']}",
            ],
            failure_conditions=[
                "Authorized operations fail unexpectedly",
                "Unauthorized operations succeed",
                "System crashes or errors",
                "Performance exceeds acceptable limits",
            ],
            performance_targets=app_analysis["performance_targets"],
            tags=["functional", "permissions", persona.role.lower().replace(" ", "_")],
        )

    def _generate_security_scenario(
        self, persona: Persona, app_analysis: Dict[str, Any]
    ) -> TestScenario:
        """Generate security testing scenario."""

        scenario_id = f"security_{persona.key}_{len(self.generated_scenarios)}"

        steps = []
        step_counter = 1

        # Permission boundary testing
        steps.append(
            TestStep(
                step_id=f"step_{step_counter}",
                description="Test permission boundaries",
                action="permission_boundary_test",
                expected_result="Proper permission enforcement",
                validation_criteria=[
                    "Unauthorized access attempts blocked",
                    "Proper error messages returned",
                    "No sensitive data leakage",
                ],
                interface=(
                    InterfaceType.API
                    if InterfaceType.API in app_analysis.get("interfaces", [])
                    else (
                        app_analysis.get("interfaces", [InterfaceType.CLI])[0]
                        if app_analysis.get("interfaces")
                        else InterfaceType.CLI
                    )
                ),
                parameters={"persona_permissions": persona.permissions},
            )
        )
        step_counter += 1

        # Input validation testing
        if any("create" in op["name"].lower() for op in app_analysis["operations"]):
            steps.append(
                TestStep(
                    step_id=f"step_{step_counter}",
                    description="Test input validation",
                    action="input_validation_test",
                    expected_result="Malicious input rejected",
                    validation_criteria=[
                        "SQL injection attempts blocked",
                        "XSS attempts sanitized",
                        "Invalid data formats rejected",
                    ],
                    interface=(
                        InterfaceType.API
                        if InterfaceType.API in app_analysis.get("interfaces", [])
                        else (
                            app_analysis.get("interfaces", [InterfaceType.CLI])[0]
                            if app_analysis.get("interfaces")
                            else InterfaceType.CLI
                        )
                    ),
                    parameters={
                        "test_payloads": [
                            "'; DROP TABLE users; --",
                            "<script>alert('xss')</script>",
                        ]
                    },
                )
            )
            step_counter += 1

        return TestScenario(
            scenario_id=scenario_id,
            name=f"Security Testing - {persona.name}",
            description=f"Security validation from {persona.role} perspective",
            scenario_type=ScenarioType.SECURITY,
            target_personas=[persona.key],
            interface_types=app_analysis["interfaces"],
            priority="high",
            estimated_duration_minutes=len(steps) * 5,  # 5 minutes per security step
            steps=steps,
            success_criteria=[
                "All permission boundaries properly enforced",
                "No unauthorized access possible",
                "Input validation working correctly",
                "No security vulnerabilities detected",
            ],
            failure_conditions=[
                "Permission bypass possible",
                "Unauthorized data access",
                "Injection attacks succeed",
                "Security errors in logs",
            ],
            security_considerations=[
                "Test with various attack vectors",
                "Validate error message safety",
                "Check for information disclosure",
            ],
            tags=[
                "security",
                "permissions",
                "validation",
                persona.role.lower().replace(" ", "_"),
            ],
        )

    def _generate_performance_scenario(
        self, persona: Persona, app_analysis: Dict[str, Any]
    ) -> TestScenario:
        """Generate performance testing scenario."""

        scenario_id = f"performance_{persona.key}_{len(self.generated_scenarios)}"
        performance_targets = app_analysis["performance_targets"]

        steps = []
        step_counter = 1

        # Response time testing
        steps.append(
            TestStep(
                step_id=f"step_{step_counter}",
                description="Measure response times for common operations",
                action="response_time_test",
                expected_result=f"Response times under {performance_targets.get('response_time_ms', 200)}ms",
                validation_criteria=[
                    f"Average response time < {performance_targets.get('response_time_ms', 200)}ms",
                    "95th percentile within acceptable limits",
                    "No timeout errors",
                ],
                interface=(
                    InterfaceType.API
                    if InterfaceType.API in app_analysis.get("interfaces", [])
                    else (
                        app_analysis.get("interfaces", [InterfaceType.CLI])[0]
                        if app_analysis.get("interfaces")
                        else InterfaceType.CLI
                    )
                ),
                parameters={
                    "iterations": 10,
                    "target_ms": performance_targets.get("response_time_ms", 200),
                },
            )
        )
        step_counter += 1

        # Load testing (if persona has appropriate permissions)
        if len(persona.permissions) > 2:  # Avoid load testing with restricted users
            steps.append(
                TestStep(
                    step_id=f"step_{step_counter}",
                    description="Test application under load",
                    action="load_test",
                    expected_result=f"Handles {performance_targets.get('concurrent_users', 10)} concurrent users",
                    validation_criteria=[
                        "No performance degradation under load",
                        "All requests complete successfully",
                        "Response times remain stable",
                    ],
                    interface=(
                        InterfaceType.API
                        if InterfaceType.API in app_analysis.get("interfaces", [])
                        else (
                            app_analysis.get("interfaces", [InterfaceType.CLI])[0]
                            if app_analysis.get("interfaces")
                            else InterfaceType.CLI
                        )
                    ),
                    parameters={
                        "concurrent_users": performance_targets.get(
                            "concurrent_users", 10
                        ),
                        "duration_seconds": 30,
                    },
                )
            )
            step_counter += 1

        return TestScenario(
            scenario_id=scenario_id,
            name=f"Performance Testing - {persona.name}",
            description=f"Performance validation from {persona.role} perspective",
            scenario_type=ScenarioType.PERFORMANCE,
            target_personas=[persona.key],
            interface_types=app_analysis["interfaces"],
            priority="medium",
            estimated_duration_minutes=len(steps) * 3,  # 3 minutes per performance step
            steps=steps,
            success_criteria=[
                f"Response times under {performance_targets.get('response_time_ms', 200)}ms",
                "No performance regressions",
                "Stable performance under load",
                "Resource usage within acceptable limits",
            ],
            failure_conditions=[
                "Response times exceed targets",
                "Performance degradation detected",
                "System becomes unresponsive",
                "Memory or CPU usage spikes",
            ],
            performance_targets=performance_targets,
            tags=[
                "performance",
                "load_testing",
                "response_time",
                persona.role.lower().replace(" ", "_"),
            ],
        )

    def _generate_usability_scenario(
        self, persona: Persona, app_analysis: Dict[str, Any]
    ) -> TestScenario:
        """Generate usability testing scenario."""

        scenario_id = f"usability_{persona.key}_{len(self.generated_scenarios)}"

        steps = []
        step_counter = 1

        # Navigation and discoverability
        if InterfaceType.WEB in app_analysis["interfaces"]:
            steps.append(
                TestStep(
                    step_id=f"step_{step_counter}",
                    description="Test navigation and user interface",
                    action="navigation_test",
                    expected_result="Intuitive navigation and clear interface",
                    validation_criteria=[
                        "Main features easily discoverable",
                        "Navigation consistent across pages",
                        "Clear visual feedback for actions",
                    ],
                    interface=InterfaceType.WEB,
                    parameters={"persona_goals": persona.goals},
                )
            )
            step_counter += 1

        # Error handling and messages
        steps.append(
            TestStep(
                step_id=f"step_{step_counter}",
                description="Test error handling and user feedback",
                action="error_handling_test",
                expected_result="Clear, helpful error messages",
                validation_criteria=[
                    "Error messages are user-friendly",
                    "Clear guidance on how to resolve issues",
                    "No technical jargon in user-facing errors",
                ],
                interface=(
                    app_analysis.get("interfaces", [InterfaceType.CLI])[0]
                    if app_analysis.get("interfaces")
                    else InterfaceType.CLI
                ),
                parameters={
                    "persona_level": (
                        "beginner" if "new" in persona.key else "experienced"
                    )
                },
            )
        )
        step_counter += 1

        return TestScenario(
            scenario_id=scenario_id,
            name=f"Usability Testing - {persona.name}",
            description=f"User experience validation from {persona.role} perspective",
            scenario_type=ScenarioType.USABILITY,
            target_personas=[persona.key],
            interface_types=app_analysis["interfaces"],
            priority="medium",
            estimated_duration_minutes=len(steps) * 4,  # 4 minutes per usability step
            steps=steps,
            success_criteria=[
                "Features are easily discoverable",
                "Navigation is intuitive",
                "Error messages are helpful",
                "Overall user experience is positive",
            ],
            failure_conditions=[
                "Features difficult to find",
                "Confusing navigation",
                "Unhelpful error messages",
                "User frustration indicators",
            ],
            tags=[
                "usability",
                "user_experience",
                "navigation",
                persona.role.lower().replace(" ", "_"),
            ],
        )

    def _generate_integration_scenario(
        self, persona: Persona, app_analysis: Dict[str, Any]
    ) -> TestScenario:
        """Generate integration testing scenario."""

        scenario_id = f"integration_{persona.key}_{len(self.generated_scenarios)}"

        steps = []
        step_counter = 1

        # Cross-interface testing
        if len(app_analysis["interfaces"]) > 1:
            steps.append(
                TestStep(
                    step_id=f"step_{step_counter}",
                    description="Test consistency across interfaces",
                    action="cross_interface_test",
                    expected_result="Consistent behavior across interfaces",
                    validation_criteria=[
                        "Same operations produce same results",
                        "Permission enforcement consistent",
                        "Data consistency maintained",
                    ],
                    interface=InterfaceType.API,  # Use API as coordination interface
                    parameters={
                        "interfaces_to_test": [
                            iface.value for iface in app_analysis["interfaces"]
                        ]
                    },
                )
            )
            step_counter += 1

        return TestScenario(
            scenario_id=scenario_id,
            name=f"Integration Testing - {persona.name}",
            description=f"Integration validation from {persona.role} perspective",
            scenario_type=ScenarioType.INTEGRATION,
            target_personas=[persona.key],
            interface_types=app_analysis["interfaces"],
            priority="low",
            estimated_duration_minutes=len(steps) * 6,  # 6 minutes per integration step
            steps=steps,
            success_criteria=[
                "Consistent behavior across interfaces",
                "No data inconsistencies",
                "Proper error propagation",
            ],
            failure_conditions=[
                "Inconsistent behavior detected",
                "Data corruption or loss",
                "Interface communication failures",
            ],
            tags=[
                "integration",
                "cross_interface",
                persona.role.lower().replace(" ", "_"),
            ],
        )

    def _persona_can_attempt_operation(
        self, persona: Persona, operation: Dict[str, Any]
    ) -> bool:
        """Check if persona should attempt an operation (for testing purposes)."""
        # For testing, we want personas to attempt operations they might not have access to
        # This helps validate permission enforcement
        return True

    def _should_operation_succeed(
        self, persona: Persona, operation: Dict[str, Any]
    ) -> bool:
        """Determine if operation should succeed for this persona."""
        required_permissions = operation.get("permissions_required", [])

        if not required_permissions:
            return True  # No permissions required

        # Check if persona has required permissions
        for required in required_permissions:
            if not persona.can_perform_action(required):
                return False

        return True

    def _get_operation_validation_criteria(
        self, operation: Dict[str, Any], should_succeed: bool
    ) -> List[str]:
        """Get validation criteria for an operation."""
        if should_succeed:
            return [
                "Operation completes successfully",
                "Expected output generated",
                "No error messages",
                "Performance within targets",
            ]
        else:
            return [
                "Operation properly denied",
                "Appropriate error message",
                "No unauthorized access",
                "Security audit logged",
            ]

    def generate_regression_scenarios(
        self, baseline_results: Dict[str, Any]
    ) -> List[TestScenario]:
        """Generate regression test scenarios based on previous results."""
        scenarios = []

        for scenario_id, results in baseline_results.items():
            # Create regression scenario
            regression_scenario = TestScenario(
                scenario_id=f"regression_{scenario_id}",
                name=f"Regression Test - {results.get('name', 'Unknown')}",
                description="Validate that previous functionality still works",
                scenario_type=ScenarioType.REGRESSION,
                target_personas=results.get("target_personas", []),
                interface_types=[
                    InterfaceType(iface)
                    for iface in results.get("interface_types", ["api"])
                ],
                priority="high",
                estimated_duration_minutes=results.get(
                    "estimated_duration_minutes", 10
                ),
                steps=[TestStep.from_dict(step) for step in results.get("steps", [])],
                success_criteria=results.get("success_criteria", []),
                failure_conditions=results.get("failure_conditions", []),
                tags=["regression", "validation"],
            )
            scenarios.append(regression_scenario)

        return scenarios

    def get_scenario_matrix(
        self, personas: List[Persona], scenario_types: List[ScenarioType]
    ) -> List[TestScenario]:
        """Generate a comprehensive test matrix covering all persona/scenario combinations."""
        matrix_scenarios = []

        for persona, scenario_type in itertools.product(personas, scenario_types):
            # Use a simplified app analysis for matrix generation
            app_analysis = {
                "interfaces": [InterfaceType.CLI, InterfaceType.WEB, InterfaceType.API],
                "operations": [
                    {"name": "create_user", "permissions_required": ["user:create"]},
                    {"name": "read_user", "permissions_required": ["user:read"]},
                    {"name": "update_user", "permissions_required": ["user:update"]},
                    {"name": "delete_user", "permissions_required": ["user:delete"]},
                ],
                "security_features": ["authentication", "authorization"],
                "performance_targets": {
                    "response_time_ms": 200,
                    "concurrent_users": 10,
                },
            }

            scenario = self._generate_scenario_for_persona(
                persona, scenario_type, app_analysis
            )
            if scenario:
                matrix_scenarios.append(scenario)

        return matrix_scenarios

    def export_scenarios(self, file_path: Path):
        """Export all generated scenarios to a JSON file."""
        scenarios_data = [
            scenario.to_dict() for scenario in self.generated_scenarios.values()
        ]
        with open(file_path, "w") as f:
            json.dump(scenarios_data, f, indent=2)

    def import_scenarios(self, file_path: Path):
        """Import scenarios from a JSON file."""
        with open(file_path, "r") as f:
            scenarios_data = json.load(f)

        for scenario_dict in scenarios_data:
            scenario = TestScenario.from_dict(scenario_dict)
            self.generated_scenarios[scenario.scenario_id] = scenario

    def get_scenarios_by_priority(self, priority: str) -> List[TestScenario]:
        """Get scenarios filtered by priority level."""
        return [s for s in self.generated_scenarios.values() if s.priority == priority]

    def get_scenarios_by_type(self, scenario_type: ScenarioType) -> List[TestScenario]:
        """Get scenarios filtered by type."""
        return [
            s
            for s in self.generated_scenarios.values()
            if s.scenario_type == scenario_type
        ]

    def get_estimated_total_duration(self) -> int:
        """Get total estimated duration for all scenarios in minutes."""
        return sum(
            scenario.estimated_duration_minutes
            for scenario in self.generated_scenarios.values()
        )

    # Async Methods for improved performance

    async def generate_scenarios_for_personas_async(
        self,
        personas: List[Persona],
        app_analysis: Dict[str, Any],
        scenario_types: Optional[List[ScenarioType]] = None,
    ) -> List[TestScenario]:
        """Async version of generate_scenarios_for_personas with concurrent generation."""

        if scenario_types is None:
            scenario_types = [
                ScenarioType.FUNCTIONAL,
                ScenarioType.SECURITY,
                ScenarioType.PERFORMANCE,
                ScenarioType.USABILITY,
            ]

        self.logger.info(
            f"Generating scenarios for {len(personas)} personas and {len(scenario_types)} types"
        )

        # Create tasks for concurrent scenario generation
        tasks = []
        for persona in personas:
            for scenario_type in scenario_types:
                task = self._generate_scenario_async(
                    persona, scenario_type, app_analysis
                )
                tasks.append(task)

        # Execute scenario generation concurrently
        scenario_results = await asyncio.gather(*tasks, return_exceptions=True)

        # Filter out None results and exceptions
        scenarios = []
        for result in scenario_results:
            if isinstance(result, TestScenario):
                scenarios.append(result)
                self.generated_scenarios[result.scenario_id] = result
            elif isinstance(result, Exception):
                self.logger.warning(f"Scenario generation failed: {result}")

        self.logger.info(f"Generated {len(scenarios)} scenarios asynchronously")
        return scenarios

    async def _generate_scenario_async(
        self,
        persona: Persona,
        scenario_type: ScenarioType,
        app_analysis: Dict[str, Any],
    ) -> Optional[TestScenario]:
        """Async wrapper for scenario generation to enable concurrency."""

        # Add small delay to simulate async processing and avoid overwhelming
        await asyncio.sleep(0.01)

        # Delegate to existing sync method - this could be further optimized
        # by making the individual generators async as well
        return self._generate_scenario_for_persona(persona, scenario_type, app_analysis)

    async def get_scenario_matrix_async(
        self, personas: List[Persona], scenario_types: List[ScenarioType]
    ) -> List[TestScenario]:
        """Async version of get_scenario_matrix with concurrent processing."""

        # Use the async generator
        return await self.generate_scenarios_for_personas_async(
            personas, {}, scenario_types
        )
