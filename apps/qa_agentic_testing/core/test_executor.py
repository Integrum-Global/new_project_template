#!/usr/bin/env python3
"""
Test Execution Engine for QA Agentic Testing

This module provides the main AutonomousQATester class that orchestrates
the entire testing process from app discovery to report generation.
"""

import asyncio
import json
import logging
import time
import traceback
from dataclasses import asdict, dataclass
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

import aiofiles
import aiofiles.os

from .agent_coordinator import AgentCoordinator, AnalysisType, ConsensusAnalysis
from .personas import Persona, PersonaManager
from .report_generator import ReportGenerator
from .scenario_generator import (
    InterfaceType,
    ScenarioGenerator,
    ScenarioType,
    TestScenario,
)


class TestStatus(Enum):
    """Status of test execution."""

    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


class ValidationResult(Enum):
    """Result of test validation."""

    PASS = "pass"
    FAIL = "fail"
    WARNING = "warning"
    INCONCLUSIVE = "inconclusive"


@dataclass
class TestResult:
    """Result of a single test execution."""

    test_id: str
    scenario_id: str
    persona_key: str
    status: TestStatus
    validation_result: ValidationResult
    start_time: float
    end_time: float
    duration_seconds: float
    llm_analysis: Optional[ConsensusAnalysis]
    execution_log: List[str]
    performance_metrics: Dict[str, Any]
    validation_details: Dict[str, Any]
    error_message: Optional[str] = None
    confidence_score: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary format."""
        data = asdict(self)
        data["status"] = self.status.value
        data["validation_result"] = self.validation_result.value
        if self.llm_analysis:
            data["llm_analysis"] = self.llm_analysis.to_dict()
        return data


@dataclass
class TestExecutionSummary:
    """Summary of test execution results."""

    total_tests: int
    passed_tests: int
    failed_tests: int
    warning_tests: int
    skipped_tests: int
    success_rate: float
    average_duration: float
    total_duration: float
    confidence_score: float
    performance_summary: Dict[str, Any]
    persona_results: Dict[str, Dict[str, int]]
    scenario_results: Dict[str, Dict[str, int]]

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary format."""
        return asdict(self)


class AutonomousQATester:
    """Main class for autonomous QA testing of applications."""

    def __init__(
        self,
        app_path: Optional[Path] = None,
        config_dir: Optional[Path] = None,
        output_dir: Optional[Path] = None,
    ):
        """Initialize the autonomous QA tester.

        Args:
            app_path: Path to the application to test
            config_dir: Directory containing configuration files
            output_dir: Directory for test outputs and reports (defaults to target app's qa_results)
        """
        self.app_path = app_path
        self.config_dir = config_dir or Path.cwd() / "qa_config"

        # Default to target app's qa_results folder if app_path is provided
        if output_dir:
            self.output_dir = output_dir
        elif app_path:
            # Store results in target app's qa_results folder
            self.output_dir = Path(app_path) / "qa_results"
        else:
            # Fallback to current directory
            self.output_dir = Path.cwd() / "qa_results"

        # Ensure output directory exists
        self.output_dir.mkdir(parents=True, exist_ok=True)

        # Initialize core components
        self.persona_manager = PersonaManager()
        self.scenario_generator = ScenarioGenerator()
        self.agent_coordinator = AgentCoordinator()
        self.report_generator = ReportGenerator()

        # Test state
        self.app_analysis: Dict[str, Any] = {}
        self.generated_scenarios: List[TestScenario] = []
        self.test_results: List[TestResult] = []
        self.execution_summary: Optional[TestExecutionSummary] = None

        # Configuration
        self.config = self._load_default_config()

        # Setup logging
        self.logger = logging.getLogger(__name__)
        logging.basicConfig(level=logging.INFO)

    def _load_default_config(self) -> Dict[str, Any]:
        """Load default configuration."""
        return {
            "discovery": {
                "analyze_code": True,
                "analyze_docs": True,
                "analyze_tests": True,
                "extract_permissions": True,
                "detect_interfaces": True,
            },
            "testing": {
                "max_concurrent_tests": 3,
                "test_timeout_minutes": 10,
                "retry_failed_tests": True,
                "skip_slow_tests": False,
            },
            "llm": {
                "use_consensus": True,
                "max_providers": 2,
                "analysis_timeout_seconds": 30,
            },
            "reporting": {
                "generate_html": True,
                "generate_json": True,
                "include_llm_responses": True,
                "confidence_threshold": 70.0,
            },
        }

    async def discover_app(self, app_path: Optional[Path] = None) -> Dict[str, Any]:
        """Discover application structure and capabilities.

        Args:
            app_path: Path to the application (overrides instance path)

        Returns:
            Dictionary containing application analysis
        """
        if app_path:
            self.app_path = app_path

        if not self.app_path or not self.app_path.exists():
            raise ValueError("Valid application path required for discovery")

        self.logger.info(f"Discovering application structure at: {self.app_path}")

        # Initialize discovery results
        self.app_analysis = {
            "app_path": str(self.app_path),
            "discovery_timestamp": time.time(),
            "interfaces": [],
            "operations": [],
            "permissions": [],
            "data_entities": [],
            "performance_targets": {},
            "security_features": [],
            "documentation": {},
        }

        # Discover interfaces
        await self._discover_interfaces()

        # Analyze code structure
        if self.config["discovery"]["analyze_code"]:
            await self._analyze_code_structure()

        # Parse documentation
        if self.config["discovery"]["analyze_docs"]:
            await self._analyze_documentation()

        # Extract permissions
        if self.config["discovery"]["extract_permissions"]:
            await self._extract_permissions()

        # Analyze existing tests
        if self.config["discovery"]["analyze_tests"]:
            await self._analyze_existing_tests()

        self.logger.info(
            f"Discovery completed. Found {len(self.app_analysis['interfaces'])} interfaces, "
            f"{len(self.app_analysis['operations'])} operations"
        )

        return self.app_analysis

    async def _discover_interfaces(self):
        """Discover application interfaces (CLI, Web, API)."""
        interfaces = []

        # Check for CLI interface
        cli_indicators = ["main.py", "cli.py", "console.py", "__main__.py"]
        cli_dirs = ["cli", "console", "command", "commands"]

        # Check for CLI files in root directory
        for indicator in cli_indicators:
            if (self.app_path / indicator).exists():
                interfaces.append(InterfaceType.CLI)
                break

        # Check for CLI subdirectories
        if InterfaceType.CLI not in interfaces:
            for cli_dir in cli_dirs:
                cli_path = self.app_path / cli_dir
                if cli_path.exists() and cli_path.is_dir():
                    # Look for main.py or other CLI files in the directory
                    for indicator in cli_indicators:
                        if (cli_path / indicator).exists():
                            interfaces.append(InterfaceType.CLI)
                            break
                    if InterfaceType.CLI in interfaces:
                        break

        # Check for CLI patterns in any Python file
        if InterfaceType.CLI not in interfaces:
            for py_file in self.app_path.rglob("*.py"):
                try:
                    async with aiofiles.open(py_file, "r", encoding="utf-8") as f:
                        content = await f.read()
                    cli_patterns = [
                        "argparse",
                        "click",
                        "typer",
                        "sys.argv",
                        "ArgumentParser",
                        "@click.",
                        "@typer.",
                    ]
                    if any(pattern in content for pattern in cli_patterns):
                        interfaces.append(InterfaceType.CLI)
                        break
                except Exception:
                    continue

        # Check for web interface
        web_indicators = ["app.py", "server.py", "wsgi.py", "asgi.py", "manage.py"]
        web_dirs = ["templates", "static", "web", "ui"]

        for indicator in web_indicators:
            if (self.app_path / indicator).exists():
                interfaces.append(InterfaceType.WEB)
                break

        for web_dir in web_dirs:
            if (self.app_path / web_dir).exists():
                interfaces.append(InterfaceType.WEB)
                break

        # Check for API interface
        api_file_indicators = ["api.py", "routes.py", "endpoints.py"]
        api_content_indicators = [
            "fastapi",
            "flask",
            "django",
            "from fastapi",
            "from flask",
            "from django",
        ]

        # Check for API files by name
        for indicator in api_file_indicators:
            if any(
                f.name.lower().find(indicator) != -1
                for f in self.app_path.rglob("*.py")
            ):
                interfaces.append(InterfaceType.API)
                break

        # Check for API patterns in file content
        if InterfaceType.API not in interfaces:
            for py_file in self.app_path.rglob("*.py"):
                try:
                    async with aiofiles.open(py_file, "r", encoding="utf-8") as f:
                        content = await f.read()
                    if any(
                        pattern in content.lower() for pattern in api_content_indicators
                    ):
                        interfaces.append(InterfaceType.API)
                        break
                except Exception:
                    continue

        # Convert InterfaceType enums to strings
        interface_strings = [
            iface.value if hasattr(iface, "value") else str(iface)
            for iface in interfaces
        ]
        self.app_analysis["interfaces"] = list(set(interface_strings))

    async def _analyze_code_structure(self):
        """Analyze code to understand operations and structure."""
        operations = []

        # Simple analysis - look for function definitions
        for py_file in self.app_path.rglob("*.py"):
            try:
                async with aiofiles.open(py_file, "r", encoding="utf-8") as f:
                    content = await f.read()

                # Extract function definitions
                lines = content.split("\n")
                for line in lines:
                    line = line.strip()
                    if line.startswith("def ") and not line.startswith("def _"):
                        func_name = line.split("(")[0].replace("def ", "").strip()

                        # Infer operation type and permissions
                        operation_type = self._infer_operation_type(func_name)
                        permissions = self._infer_permissions_from_name(func_name)
                        interface = await self._infer_interface_from_file(py_file)

                        operations.append(
                            {
                                "name": func_name,
                                "type": operation_type,
                                "file": str(py_file.relative_to(self.app_path)),
                                "permissions_required": permissions,
                                "interface": interface,
                            }
                        )

            except Exception as e:
                self.logger.warning(f"Could not analyze {py_file}: {e}")

        self.app_analysis["operations"] = operations[:20]  # Limit to first 20

    async def _analyze_documentation(self):
        """Analyze documentation files for additional context."""
        doc_files = ["README.md", "README.rst", "docs", "API.md", "USAGE.md"]
        documentation = {}

        for doc_file in doc_files:
            doc_path = self.app_path / doc_file
            if doc_path.exists():
                try:
                    if doc_path.is_file():
                        async with aiofiles.open(doc_path, "r", encoding="utf-8") as f:
                            content = await f.read()
                        documentation[doc_file] = content[:2000]  # First 2000 chars
                    elif doc_path.is_dir():
                        # Look for index files in docs directory
                        for index_file in ["index.md", "README.md", "index.rst"]:
                            index_path = doc_path / index_file
                            if index_path.exists():
                                async with aiofiles.open(
                                    index_path, "r", encoding="utf-8"
                                ) as f:
                                    content = await f.read()
                                documentation[f"docs/{index_file}"] = content[:2000]
                                break
                except Exception as e:
                    self.logger.warning(f"Could not read {doc_path}: {e}")

        self.app_analysis["documentation"] = documentation

    async def _extract_permissions(self):
        """Extract permission patterns from code."""
        permissions = set()

        # Look for permission-related patterns
        permission_patterns = [
            r"permission[s]?['\"]?\s*[=:]\s*['\"]([^'\"]+)['\"]",
            r"can_([a-zA-Z_]+)",
            r"has_permission\(['\"]([^'\"]+)['\"]",
            r"@require[s]?_permission\(['\"]([^'\"]+)['\"]",
            r"['\"]([a-zA-Z_]+:[a-zA-Z_*]+)['\"]",  # permission:action patterns
        ]

        for py_file in self.app_analysis.get("operations", []):
            file_path = self.app_path / py_file["file"]
            try:
                async with aiofiles.open(file_path, "r", encoding="utf-8") as f:
                    content = await f.read()

                # Simple pattern matching
                for line in content.split("\n"):
                    if any(
                        keyword in line.lower()
                        for keyword in ["permission", "auth", "role"]
                    ):
                        # Extract potential permissions
                        if ":" in line:
                            parts = line.split(":")
                            for part in parts:
                                part = part.strip().strip("'\"")
                                if (
                                    len(part) > 2
                                    and len(part) < 50
                                    and part.replace("_", "").replace(":", "").isalnum()
                                ):
                                    permissions.add(part)

            except Exception as e:
                self.logger.warning(
                    f"Could not extract permissions from {file_path}: {e}"
                )

        # Add default permissions if none found
        if not permissions:
            permissions.update(
                [
                    "user:read",
                    "user:create",
                    "user:update",
                    "user:delete",
                    "admin:all",
                    "manager:team",
                ]
            )

        self.app_analysis["permissions"] = list(permissions)[:20]  # Limit to first 20

    async def _analyze_existing_tests(self):
        """Analyze existing tests to understand expected behavior."""
        test_dirs = ["tests", "test", "testing"]
        test_patterns = []

        for test_dir in test_dirs:
            test_path = self.app_path / test_dir
            if test_path.exists():
                for test_file in test_path.rglob("test_*.py"):
                    try:
                        async with aiofiles.open(test_file, "r", encoding="utf-8") as f:
                            content = await f.read()

                        # Extract test function names
                        for line in content.split("\n"):
                            if line.strip().startswith("def test_"):
                                test_name = (
                                    line.split("(")[0].replace("def ", "").strip()
                                )
                                test_patterns.append(test_name)

                    except Exception as e:
                        self.logger.warning(f"Could not analyze test {test_file}: {e}")

        self.app_analysis["existing_test_patterns"] = test_patterns[
            :10
        ]  # Limit to first 10

    def _infer_operation_type(self, func_name: str) -> str:
        """Infer operation type from function name."""
        name_lower = func_name.lower()

        if any(keyword in name_lower for keyword in ["create", "add", "new", "insert"]):
            return "create"
        elif any(
            keyword in name_lower
            for keyword in ["read", "get", "fetch", "list", "show"]
        ):
            return "read"
        elif any(
            keyword in name_lower for keyword in ["update", "modify", "edit", "change"]
        ):
            return "update"
        elif any(keyword in name_lower for keyword in ["delete", "remove", "destroy"]):
            return "delete"
        else:
            return "other"

    def _infer_permissions_from_name(self, func_name: str) -> List[str]:
        """Infer required permissions from function name."""
        operation_type = self._infer_operation_type(func_name)
        name_lower = func_name.lower()

        # Extract resource type
        resource = "resource"
        if "user" in name_lower:
            resource = "user"
        elif "role" in name_lower:
            resource = "role"
        elif "permission" in name_lower:
            resource = "permission"
        elif "admin" in name_lower:
            resource = "admin"

        return [f"{resource}:{operation_type}"]

    async def _infer_interface_from_file(self, file_path: Path) -> str:
        """Infer the interface type from file path and content."""
        relative_path = str(file_path.relative_to(self.app_path)).lower()

        # Check file path for interface indicators
        if any(part in relative_path for part in ["cli", "console", "command"]):
            return "cli"
        elif any(part in relative_path for part in ["api", "routes", "endpoints"]):
            return "api"
        elif any(
            part in relative_path for part in ["web", "ui", "frontend", "templates"]
        ):
            return "web"

        # Check file content for interface patterns
        try:
            async with aiofiles.open(file_path, "r", encoding="utf-8") as f:
                content = await f.read()

            # CLI patterns
            cli_patterns = [
                "argparse",
                "click",
                "typer",
                "sys.argv",
                "ArgumentParser",
                "@click.",
                "@typer.",
            ]
            if any(pattern in content for pattern in cli_patterns):
                return "cli"

            # API patterns
            api_patterns = [
                "@app.route",
                "@router.",
                "FastAPI",
                "Flask",
                "@api.",
                "APIRouter",
            ]
            if any(pattern in content for pattern in api_patterns):
                return "api"

            # Web patterns
            web_patterns = [
                "render_template",
                "HttpResponse",
                "redirect",
                "request.GET",
                "request.POST",
            ]
            if any(pattern in content for pattern in web_patterns):
                return "web"

        except Exception:
            pass

        # Default to API
        return "api"

    def generate_personas(
        self, custom_personas: Optional[List[Dict[str, Any]]] = None
    ) -> List[Persona]:
        """Generate personas for testing based on discovered permissions.

        Args:
            custom_personas: Optional list of custom persona definitions

        Returns:
            List of generated personas
        """
        self.logger.info("Generating personas for testing")

        # Add custom personas if provided
        if custom_personas:
            for persona_data in custom_personas:
                persona = Persona.from_dict(persona_data)
                self.persona_manager.add_persona(persona)

        # Get testing matrix (uses built-in personas first)
        testing_personas = self.persona_manager.get_testing_matrix()

        # Only generate additional personas if we need more coverage
        if len(testing_personas) < 4 and self.app_analysis.get("permissions"):
            generated = self.persona_manager.generate_personas_from_permissions(
                self.app_analysis["permissions"]
            )
            self.logger.info(
                f"Generated {len(generated)} additional personas from permissions"
            )
            # Refresh testing matrix to include new personas
            testing_personas = self.persona_manager.get_testing_matrix()

        self.logger.info(
            f"Selected {len(testing_personas)} personas for testing: {[p.name for p in testing_personas]}"
        )
        return testing_personas

    def generate_scenarios(
        self,
        personas: Optional[List[Persona]] = None,
        scenario_types: Optional[List[ScenarioType]] = None,
    ) -> List[TestScenario]:
        """Generate test scenarios (sync version for compatibility)."""
        return self._generate_scenarios_sync(personas, scenario_types)

    async def generate_scenarios_async(
        self,
        personas: Optional[List[Persona]] = None,
        scenario_types: Optional[List[ScenarioType]] = None,
    ) -> List[TestScenario]:
        """Generate test scenarios asynchronously for better performance."""
        return await self._generate_scenarios_async(personas, scenario_types)

    def _generate_scenarios_sync(
        self,
        personas: Optional[List[Persona]] = None,
        scenario_types: Optional[List[ScenarioType]] = None,
    ) -> List[TestScenario]:
        """Internal sync scenario generation."""
        if personas is None:
            personas = self.persona_manager.get_testing_matrix()

        if scenario_types is None:
            scenario_types = [
                ScenarioType.FUNCTIONAL,
                ScenarioType.SECURITY,
                ScenarioType.PERFORMANCE,
                ScenarioType.USABILITY,
            ]

        self.logger.info(
            f"Generating scenarios for {len(personas)} personas and {len(scenario_types)} scenario types"
        )

        # Use discovered app analysis for scenario generation
        app_analysis = (
            self.app_analysis if self.app_analysis else self._get_default_app_analysis()
        )

        self.generated_scenarios = (
            self.scenario_generator.generate_scenarios_for_personas(
                personas, app_analysis, scenario_types
            )
        )

        self.logger.info(f"Generated {len(self.generated_scenarios)} test scenarios")
        return self.generated_scenarios

    async def _generate_scenarios_async(
        self,
        personas: Optional[List[Persona]] = None,
        scenario_types: Optional[List[ScenarioType]] = None,
    ) -> List[TestScenario]:
        """Generate test scenarios asynchronously based on personas and app analysis."""
        if personas is None:
            personas = self.persona_manager.get_testing_matrix()

        if scenario_types is None:
            scenario_types = [
                ScenarioType.FUNCTIONAL,
                ScenarioType.SECURITY,
                ScenarioType.PERFORMANCE,
                ScenarioType.USABILITY,
            ]

        self.logger.info(
            f"Generating scenarios asynchronously for {len(personas)} personas and {len(scenario_types)} scenario types"
        )

        # Use discovered app analysis for scenario generation
        app_analysis = (
            self.app_analysis if self.app_analysis else self._get_default_app_analysis()
        )

        # Use async scenario generation for better performance
        self.generated_scenarios = (
            await self.scenario_generator.generate_scenarios_for_personas_async(
                personas, app_analysis, scenario_types
            )
        )

        self.logger.info(
            f"Generated {len(self.generated_scenarios)} test scenarios asynchronously"
        )
        return self.generated_scenarios

    def _get_default_app_analysis(self) -> Dict[str, Any]:
        """Get default app analysis if discovery wasn't run."""
        return {
            "interfaces": [InterfaceType.CLI, InterfaceType.API],
            "operations": [
                {
                    "name": "list_items",
                    "type": "read",
                    "permissions_required": ["item:read"],
                },
                {
                    "name": "create_item",
                    "type": "create",
                    "permissions_required": ["item:create"],
                },
                {
                    "name": "update_item",
                    "type": "update",
                    "permissions_required": ["item:update"],
                },
                {
                    "name": "delete_item",
                    "type": "delete",
                    "permissions_required": ["item:delete"],
                },
            ],
            "security_features": ["authentication", "authorization"],
            "performance_targets": {"response_time_ms": 200, "concurrent_users": 10},
        }

    async def execute_tests(
        self,
        scenarios: Optional[List[TestScenario]] = None,
        max_concurrent: Optional[int] = None,
    ) -> TestExecutionSummary:
        """Execute all test scenarios.

        Args:
            scenarios: Scenarios to execute (uses generated scenarios if None)
            max_concurrent: Maximum concurrent test executions

        Returns:
            Test execution summary
        """
        if scenarios is None:
            scenarios = self.generated_scenarios

        if not scenarios:
            raise ValueError(
                "No scenarios available for execution. Run generate_scenarios() first."
            )

        max_concurrent = (
            max_concurrent or self.config["testing"]["max_concurrent_tests"]
        )

        self.logger.info(
            f"Executing {len(scenarios)} test scenarios with max {max_concurrent} concurrent"
        )

        # Reset test results
        self.test_results = []

        # Create test execution tasks
        test_tasks = []
        for i, scenario in enumerate(scenarios):
            for persona_key in scenario.target_personas:
                persona = self.persona_manager.get_persona(persona_key)
                if persona:
                    test_id = f"test_{i}_{persona_key}"
                    task = self._execute_single_test(test_id, scenario, persona)
                    test_tasks.append(task)

        # Execute tests with concurrency limit
        semaphore = asyncio.Semaphore(max_concurrent)

        async def limited_test(task):
            async with semaphore:
                return await task

        limited_tasks = [limited_test(task) for task in test_tasks]
        results = await asyncio.gather(*limited_tasks, return_exceptions=True)

        # Process results
        for result in results:
            if isinstance(result, TestResult):
                self.test_results.append(result)
            elif isinstance(result, Exception):
                self.logger.error(f"Test execution failed: {result}")

        # Generate execution summary
        self.execution_summary = self._generate_execution_summary()

        self.logger.info(
            f"Test execution completed. Success rate: {self.execution_summary.success_rate:.1f}%"
        )
        return self.execution_summary

    async def _execute_single_test(
        self, test_id: str, scenario: TestScenario, persona: Persona
    ) -> TestResult:
        """Execute a single test scenario with a specific persona.

        Args:
            test_id: Unique test identifier
            scenario: Test scenario to execute
            persona: Persona to test with

        Returns:
            Test result
        """
        start_time = time.time()
        execution_log = []
        performance_metrics = {}

        try:
            execution_log.append(f"Starting test {test_id} for persona {persona.name}")

            # Get persona expectations for this scenario
            expectations = scenario.get_persona_expectations(persona.key)

            # Execute scenario steps
            step_results = []
            for step in scenario.steps:
                step_start = time.time()

                # Simulate step execution (in real implementation, this would interface with the app)
                step_success = await self._simulate_step_execution(step, persona)
                step_duration = time.time() - step_start

                step_results.append(
                    {
                        "step_id": step.step_id,
                        "success": step_success,
                        "duration": step_duration,
                        "expected": step.step_id
                        not in expectations["expected_failures"],
                    }
                )

                execution_log.append(
                    f"Step {step.step_id}: {'PASS' if step_success else 'FAIL'} ({step_duration:.3f}s)"
                )

            # Perform LLM analysis
            llm_analysis = None
            if self.config["llm"]["use_consensus"]:
                try:
                    analysis_prompt = self._create_analysis_prompt(
                        scenario, persona, step_results
                    )
                    persona_context = {
                        "name": persona.name,
                        "role": persona.role,
                        "permissions": persona.permissions,
                        "goals": persona.goals,
                        "behavior_style": persona.behavior_style,
                        "typical_actions": persona.typical_actions,
                    }

                    llm_analysis = await self.agent_coordinator.analyze_consensus(
                        analysis_prompt,
                        AnalysisType.FUNCTIONAL,  # Default to functional analysis
                        persona_context,
                        self.config["llm"].get("max_providers", 2),
                    )
                    execution_log.append("LLM analysis completed")

                except Exception as e:
                    execution_log.append(f"LLM analysis failed: {e}")
                    self.logger.warning(f"LLM analysis failed for {test_id}: {e}")

            # Validate test results
            validation_result, validation_details = self._validate_test_results(
                scenario, persona, step_results, expectations
            )

            # Calculate performance metrics
            total_duration = time.time() - start_time
            performance_metrics = {
                "total_duration": total_duration,
                "step_count": len(step_results),
                "average_step_duration": sum(r["duration"] for r in step_results)
                / len(step_results),
                "success_rate": sum(1 for r in step_results if r["success"])
                / len(step_results)
                * 100,
            }

            # Calculate confidence score
            confidence_score = self._calculate_test_confidence(
                validation_result, llm_analysis, step_results
            )

            return TestResult(
                test_id=test_id,
                scenario_id=scenario.scenario_id,
                persona_key=persona.key,
                status=TestStatus.COMPLETED,
                validation_result=validation_result,
                start_time=start_time,
                end_time=time.time(),
                duration_seconds=total_duration,
                llm_analysis=llm_analysis,
                execution_log=execution_log,
                performance_metrics=performance_metrics,
                validation_details=validation_details,
                confidence_score=confidence_score,
            )

        except Exception as e:
            total_duration = time.time() - start_time
            execution_log.append(f"Test failed with error: {e}")

            return TestResult(
                test_id=test_id,
                scenario_id=scenario.scenario_id,
                persona_key=persona.key,
                status=TestStatus.FAILED,
                validation_result=ValidationResult.FAIL,
                start_time=start_time,
                end_time=time.time(),
                duration_seconds=total_duration,
                llm_analysis=None,
                execution_log=execution_log,
                performance_metrics=performance_metrics,
                validation_details={"error": str(e)},
                error_message=str(e),
                confidence_score=0.0,
            )

    async def _simulate_step_execution(self, step, persona: Persona) -> bool:
        """Simulate step execution (placeholder for real implementation).

        In a real implementation, this would:
        1. Execute the actual command/API call/UI interaction
        2. Measure performance
        3. Validate permissions
        4. Check expected outcomes

        For now, it simulates based on persona permissions.
        """
        # Simulate some processing time
        await asyncio.sleep(0.1)

        # Simple simulation: check if persona can perform the action
        if step.action in ["authenticate", "login"]:
            return True  # Authentication usually succeeds in testing

        # For other actions, check permissions
        required_permissions = step.parameters.get("persona_permissions", [])
        if required_permissions:
            for perm in required_permissions:
                if persona.can_perform_action(perm):
                    return True
            return False  # Permission denied

        return True  # Default to success for actions without specific permission requirements

    def _create_analysis_prompt(
        self, scenario: TestScenario, persona: Persona, step_results: List[Dict]
    ) -> str:
        """Create analysis prompt for LLM evaluation."""

        prompt = f"""
Analyze the following test execution from the perspective of {persona.name} ({persona.role}):

SCENARIO: {scenario.name}
TYPE: {scenario.scenario_type.value}
DESCRIPTION: {scenario.description}

PERSONA DETAILS:
- Role: {persona.role}
- Permissions: {', '.join(persona.permissions)}
- Goals: {', '.join(persona.goals)}
- Behavior Style: {persona.behavior_style}

TEST RESULTS:
"""

        for result in step_results:
            status = "✅ PASS" if result["success"] else "❌ FAIL"
            expected = " (expected)" if result["expected"] else " (unexpected)"
            prompt += f"- Step {result['step_id']}: {status}{expected} - {result['duration']:.3f}s\n"

        prompt += f"""

SUCCESS CRITERIA:
{chr(10).join('- ' + criterion for criterion in scenario.success_criteria)}

FAILURE CONDITIONS:
{chr(10).join('- ' + condition for condition in scenario.failure_conditions)}

Please analyze:
1. Whether the test results meet expectations for this persona
2. If permission enforcement is working correctly
3. Any security or usability concerns
4. Performance assessment
5. Overall confidence in the application behavior
6. Specific recommendations for improvement

Provide a structured analysis with clear conclusions.
"""

        return prompt

    def _validate_test_results(
        self,
        scenario: TestScenario,
        persona: Persona,
        step_results: List[Dict],
        expectations: Dict[str, Any],
    ) -> Tuple[ValidationResult, Dict[str, Any]]:
        """Validate test results against expectations."""

        validation_details = {
            "total_steps": len(step_results),
            "passed_steps": sum(1 for r in step_results if r["success"]),
            "failed_steps": sum(1 for r in step_results if not r["success"]),
            "expected_failures": len(expectations["expected_failures"]),
            "unexpected_failures": 0,
            "unexpected_successes": 0,
        }

        # Check for unexpected results
        for result in step_results:
            if result["step_id"] in expectations["expected_failures"]:
                if result["success"]:
                    validation_details["unexpected_successes"] += 1
            else:
                if not result["success"]:
                    validation_details["unexpected_failures"] += 1

        # Calculate success rate
        success_rate = (
            validation_details["passed_steps"] / validation_details["total_steps"] * 100
        )
        expected_success_rate = expectations["expected_success_rate"]

        # Determine validation result
        if validation_details["unexpected_failures"] > 0:
            validation_result = ValidationResult.FAIL
        elif validation_details["unexpected_successes"] > 1:  # Allow some tolerance
            validation_result = ValidationResult.WARNING
        elif (
            success_rate < expected_success_rate - 20
        ):  # Significantly worse than expected
            validation_result = ValidationResult.WARNING
        else:
            # Pass if equal to or better than expected, or within reasonable tolerance
            validation_result = ValidationResult.PASS

        validation_details["success_rate"] = success_rate
        validation_details["expected_success_rate"] = expected_success_rate
        validation_details["deviation"] = abs(success_rate - expected_success_rate)

        return validation_result, validation_details

    def _calculate_test_confidence(
        self,
        validation_result: ValidationResult,
        llm_analysis: Optional[ConsensusAnalysis],
        step_results: List[Dict],
    ) -> float:
        """Calculate confidence score for test results."""

        base_confidence = {
            ValidationResult.PASS: 90.0,
            ValidationResult.WARNING: 70.0,
            ValidationResult.FAIL: 30.0,
            ValidationResult.INCONCLUSIVE: 50.0,
        }[validation_result]

        # Adjust based on LLM analysis confidence
        if llm_analysis:
            llm_confidence = llm_analysis.confidence_score
            base_confidence = (base_confidence + llm_confidence) / 2

        # Adjust based on step success consistency
        step_success_rate = sum(1 for r in step_results if r["success"]) / len(
            step_results
        )
        if (
            step_success_rate > 0.8 or step_success_rate < 0.2
        ):  # Very high or very low success rate
            base_confidence += 10  # More confident in clear results

        return min(base_confidence, 100.0)

    def _generate_execution_summary(self) -> TestExecutionSummary:
        """Generate summary of test execution results."""

        if not self.test_results:
            raise ValueError("No test results available")

        # Count results by validation
        validation_counts = {
            ValidationResult.PASS: 0,
            ValidationResult.FAIL: 0,
            ValidationResult.WARNING: 0,
            ValidationResult.INCONCLUSIVE: 0,
        }

        for result in self.test_results:
            validation_counts[result.validation_result] += 1

        # Count by status
        status_counts = {}
        for result in self.test_results:
            status_counts[result.status] = status_counts.get(result.status, 0) + 1

        # Calculate metrics
        total_tests = len(self.test_results)
        passed_tests = validation_counts[ValidationResult.PASS]
        failed_tests = validation_counts[ValidationResult.FAIL]
        warning_tests = validation_counts[ValidationResult.WARNING]
        skipped_tests = status_counts.get(TestStatus.SKIPPED, 0)

        success_rate = (passed_tests / total_tests) * 100 if total_tests > 0 else 0

        # Duration metrics
        durations = [
            r.duration_seconds for r in self.test_results if r.duration_seconds > 0
        ]
        average_duration = sum(durations) / len(durations) if durations else 0
        total_duration = sum(durations)

        # Confidence score
        confidence_scores = [
            r.confidence_score for r in self.test_results if r.confidence_score > 0
        ]
        overall_confidence = (
            sum(confidence_scores) / len(confidence_scores) if confidence_scores else 0
        )

        # Performance summary
        performance_summary = {
            "average_response_time": average_duration,
            "total_execution_time": total_duration,
            "tests_per_minute": (
                len(self.test_results) / (total_duration / 60)
                if total_duration > 0
                else 0
            ),
        }

        # Results by persona
        persona_results = {}
        for result in self.test_results:
            if result.persona_key not in persona_results:
                persona_results[result.persona_key] = {
                    "pass": 0,
                    "fail": 0,
                    "warning": 0,
                    "total": 0,
                }

            persona_results[result.persona_key]["total"] += 1
            if result.validation_result == ValidationResult.PASS:
                persona_results[result.persona_key]["pass"] += 1
            elif result.validation_result == ValidationResult.FAIL:
                persona_results[result.persona_key]["fail"] += 1
            elif result.validation_result == ValidationResult.WARNING:
                persona_results[result.persona_key]["warning"] += 1

        # Results by scenario
        scenario_results = {}
        for result in self.test_results:
            if result.scenario_id not in scenario_results:
                scenario_results[result.scenario_id] = {
                    "pass": 0,
                    "fail": 0,
                    "warning": 0,
                    "total": 0,
                }

            scenario_results[result.scenario_id]["total"] += 1
            if result.validation_result == ValidationResult.PASS:
                scenario_results[result.scenario_id]["pass"] += 1
            elif result.validation_result == ValidationResult.FAIL:
                scenario_results[result.scenario_id]["fail"] += 1
            elif result.validation_result == ValidationResult.WARNING:
                scenario_results[result.scenario_id]["warning"] += 1

        return TestExecutionSummary(
            total_tests=total_tests,
            passed_tests=passed_tests,
            failed_tests=failed_tests,
            warning_tests=warning_tests,
            skipped_tests=skipped_tests,
            success_rate=success_rate,
            average_duration=average_duration,
            total_duration=total_duration,
            confidence_score=overall_confidence,
            performance_summary=performance_summary,
            persona_results=persona_results,
            scenario_results=scenario_results,
        )

    async def generate_report(
        self, output_file: Optional[Path] = None, format: str = "html"
    ) -> Path:
        """Generate test report.

        Args:
            output_file: Output file path (auto-generated if None)
            format: Report format ("html", "json", or "both")

        Returns:
            Path to generated report file
        """
        if not self.test_results:
            raise ValueError("No test results available for report generation")

        # Prepare report data
        from datetime import datetime

        report_data = {
            "test_info": {
                "test_name": "QA Agentic Testing Report",
                "test_framework": "QA Agentic Testing v0.1.0",
                "test_date": datetime.now().isoformat(),
                "test_date_formatted": datetime.now().strftime("%B %d, %Y at %I:%M %p"),
                "duration_estimated_minutes": int(
                    (time.time() - self.config.get("start_time", time.time())) / 60
                )
                + 1,
                "app_name": (
                    self.app_path.name if self.app_path else "Unknown Application"
                ),
                "app_path": str(self.app_path) if self.app_path else "Unknown",
            },
            "metadata": {
                "app_path": str(self.app_path) if self.app_path else "Unknown",
                "generation_time": time.time(),
                "total_scenarios": len(self.generated_scenarios),
                "total_tests": len(self.test_results),
            },
            "app_analysis": self.app_analysis,
            "execution_summary": (
                self.execution_summary.to_dict() if self.execution_summary else {}
            ),
            "test_results": [result.to_dict() for result in self.test_results],
            "scenarios": [scenario.to_dict() for scenario in self.generated_scenarios],
            "personas": {
                key: persona.to_dict()
                for key, persona in self.persona_manager.personas.items()
            },
            "llm_analysis_history": [
                analysis.to_dict()
                for analysis in self.agent_coordinator.analysis_history
            ],
        }

        # Generate report asynchronously
        if format == "html" or format == "both":
            html_file = output_file or self.output_dir / "qa_test_report.html"
            # Convert report data to expected format
            from .report_data_adapter import adapt_report_data

            adapted_data = adapt_report_data(report_data)
            await self.report_generator.generate_comprehensive_report_async(
                adapted_data, html_file
            )
            self.logger.info(f"HTML report generated: {html_file}")

            if format == "html":
                return html_file

        if format == "json" or format == "both":
            json_file = output_file or self.output_dir / "qa_test_results.json"
            if format == "both":
                json_file = json_file.with_suffix(".json")

            await self.report_generator.generate_json_report_async(
                report_data, json_file
            )
            self.logger.info(f"JSON report generated: {json_file}")

            if format == "json":
                return json_file

        # Return HTML file by default for "both" format
        return self.output_dir / "qa_test_report.html"

    def load_config(self, config_file: Path):
        """Load configuration from file."""
        with open(config_file, "r") as f:
            self.config.update(json.load(f))

    def save_config(self, config_file: Path):
        """Save current configuration to file."""
        with open(config_file, "w") as f:
            json.dump(self.config, f, indent=2)

    async def quick_test(
        self, app_path: Path, output_dir: Optional[Path] = None
    ) -> TestExecutionSummary:
        """Perform a quick test of an application with default settings.

        Args:
            app_path: Path to the application to test
            output_dir: Directory for outputs (auto-generated if None)

        Returns:
            Test execution summary
        """
        if output_dir:
            self.output_dir = output_dir

        # Full testing pipeline (fully async)
        await self.discover_app(app_path)
        personas = self.generate_personas()
        scenarios = await self.generate_scenarios_async(personas)
        summary = await self.execute_tests(scenarios)

        # Generate reports
        await self.generate_report(format="both")

        return summary
