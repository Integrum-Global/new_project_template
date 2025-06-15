"""
Core modules for QA Agentic Testing Framework

This package contains the core functionality for autonomous AI-powered testing:
- PersonaManager: Manages user personas and their behaviors
- ScenarioGenerator: Auto-generates test scenarios
- LLMCoordinator: Orchestrates multiple LLM providers
- TestExecutor: Executes tests with intelligent validation
- ReportGenerator: Creates comprehensive test reports
"""

from .personas import PersonaManager, Persona
from .scenario_generator import ScenarioGenerator, TestScenario
from .agent_coordinator import AgentCoordinator
from .test_executor import AutonomousQATester, TestResult
from .report_generator import ReportGenerator

__all__ = [
    "PersonaManager",
    "Persona", 
    "ScenarioGenerator",
    "TestScenario",
    "AgentCoordinator",
    "AutonomousQATester", 
    "TestResult",
    "ReportGenerator"
]