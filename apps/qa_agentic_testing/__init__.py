"""
QA Agentic Testing Framework

AI-powered autonomous testing framework using advanced agent systems that can test 
any application with minimal configuration.

Features:
- Auto-discovery of application structure and interfaces
- Intelligent persona generation based on user roles
- Advanced agent orchestration (A2A, self-organizing, iterative)
- Comprehensive reporting with AI insights
- Enterprise-ready with CI/CD integration

Usage:
    from qa_agentic_testing import AutonomousQATester
    
    # Quick testing
    tester = AutonomousQATester()
    tester.discover_app("/path/to/app")
    results = tester.execute_tests()
    tester.generate_report("results.html")
    
    # Full application usage via services
    from qa_agentic_testing.core.services import ProjectService, TestRunService
    
    project_service = ProjectService()
    project = await project_service.create_project("My App", "/path/to/app")
    
    run_service = TestRunService()
    run = await run_service.create_run(project.project_id, "Test Run 1")
    await run_service.start_run(run.run_id)
"""

__version__ = "0.1.0"
__author__ = "Kailash SDK Team"
__email__ = "team@kailash.dev"

# Import main testing components for easy access
from .core.test_executor import AutonomousQATester
from .core.personas import PersonaManager, Persona
from .core.scenario_generator import ScenarioGenerator, TestScenario
from .core.agent_coordinator import AgentCoordinator
from .core.report_generator import ReportGenerator

# Import models for API usage
from .core.models import (
    TestProject, TestRun, TestResult, AgentSession, TestMetrics,
    TestStatus, TestType, AgentType, InterfaceType, Priority,
    create_test_project, create_test_run, create_test_result
)

# Import services for application usage
from .core.services import (
    ProjectService, TestRunService, TestResultService, 
    AnalyticsService, ReportService
)

# Import database for setup
from .core.database import setup_database, get_database

# Import API app
from .api.main import app as api_app, create_app

# Import CLI
from .cli.main import cli

__all__ = [
    # Version info
    "__version__", "__author__", "__email__",
    
    # Core testing components
    "AutonomousQATester", "PersonaManager", "Persona",
    "ScenarioGenerator", "TestScenario", "AgentCoordinator",
    "ReportGenerator",
    
    # Domain models
    "TestProject", "TestRun", "TestResult", "AgentSession", "TestMetrics",
    "TestStatus", "TestType", "AgentType", "InterfaceType", "Priority",
    "create_test_project", "create_test_run", "create_test_result",
    
    # Business services
    "ProjectService", "TestRunService", "TestResultService",
    "AnalyticsService", "ReportService",
    
    # Database
    "setup_database", "get_database",
    
    # API and CLI
    "api_app", "create_app", "cli",
]