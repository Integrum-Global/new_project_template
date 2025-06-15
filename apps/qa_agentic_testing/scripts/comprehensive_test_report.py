#!/usr/bin/env python3
"""
Comprehensive Test Report for QA Agentic Testing App

This script provides a complete analysis of the app's functionality,
identifies all issues, and provides detailed fixes.
"""

import asyncio
import os
import sys
from pathlib import Path

# Setup paths
current_dir = Path(__file__).parent
root_dir = current_dir.parent.parent.parent
sys.path.insert(0, str(root_dir / "src"))
sys.path.insert(0, str(root_dir))


class TestReport:
    def __init__(self):
        self.results = {
            "core_imports": [],
            "functionality": [],
            "issues": [],
            "fixes": [],
            "recommendations": [],
        }

    def add_result(self, category: str, test: str, status: bool, details: str = ""):
        """Add a test result."""
        self.results[category].append(
            {"test": test, "status": status, "details": details}
        )

    def add_issue(self, issue: str, severity: str, fix: str):
        """Add an identified issue."""
        self.results["issues"].append(
            {"issue": issue, "severity": severity, "fix": fix}
        )

    def add_recommendation(self, recommendation: str):
        """Add a recommendation."""
        self.results["recommendations"].append(recommendation)


def test_import_structure(report: TestReport):
    """Test import structure and identify issues."""
    print("🔍 Testing Import Structure...")

    # Test core module imports
    try:
        os.chdir(current_dir)
        from core.models import TestProject, TestStatus, create_test_project

        report.add_result("core_imports", "Core models", True)
    except Exception as e:
        report.add_result("core_imports", "Core models", False, str(e))

    try:
        from core.database import QADatabase

        report.add_result("core_imports", "Database", True)
    except Exception as e:
        report.add_result("core_imports", "Database", False, str(e))

    try:
        from core.personas import PersonaManager

        report.add_result("core_imports", "Personas", True)
    except Exception as e:
        report.add_result("core_imports", "Personas", False, str(e))

    try:
        from core.scenario_generator import ScenarioGenerator

        report.add_result("core_imports", "Scenario Generator", True)
    except Exception as e:
        report.add_result("core_imports", "Scenario Generator", False, str(e))

    try:
        from core.llm_coordinator import AgentCoordinator

        report.add_result("core_imports", "LLM Coordinator", True)
    except Exception as e:
        report.add_result("core_imports", "LLM Coordinator", False, str(e))

    try:
        from core.test_executor import AutonomousQATester

        report.add_result("core_imports", "Test Executor", True)
    except Exception as e:
        report.add_result("core_imports", "Test Executor", False, str(e))

    try:
        from core.report_generator import ReportGenerator

        report.add_result("core_imports", "Report Generator", True)
    except Exception as e:
        report.add_result("core_imports", "Report Generator", False, str(e))

    try:
        from core.services import ProjectService

        report.add_result("core_imports", "Services", True)
    except Exception as e:
        report.add_result("core_imports", "Services", False, str(e))


def test_package_imports(report: TestReport):
    """Test package-level imports."""
    print("🔍 Testing Package Imports...")

    # Test the main package import (this was fixed)
    try:
        from apps.qa_agentic_testing import AgentCoordinator, AutonomousQATester

        report.add_result("core_imports", "Main package import", True)
    except Exception as e:
        report.add_result("core_imports", "Main package import", False, str(e))
        report.add_issue(
            "Package import fails",
            "HIGH",
            "Add apps directory to PYTHONPATH or run with: PYTHONPATH=. python script.py",
        )


def test_api_cli_components(report: TestReport):
    """Test API and CLI components."""
    print("🔍 Testing API and CLI Components...")

    original_cwd = os.getcwd()
    try:
        os.chdir(current_dir)

        # Test API
        try:
            from api.main import create_app

            app = create_app()
            report.add_result("functionality", "API creation", True)
        except Exception as e:
            report.add_result("functionality", "API creation", False, str(e))
            report.add_issue(
                "API imports use relative imports beyond top-level package",
                "MEDIUM",
                "Run API from app directory or restructure imports",
            )

        # Test CLI
        try:
            from cli.main import cli

            report.add_result("functionality", "CLI import", True)
        except Exception as e:
            report.add_result("functionality", "CLI import", False, str(e))
            report.add_issue(
                "CLI imports use relative imports beyond top-level package",
                "MEDIUM",
                "Run CLI from app directory or restructure imports",
            )

    finally:
        os.chdir(original_cwd)


def test_core_functionality(report: TestReport):
    """Test core functionality with proper app analysis structure."""
    print("🔍 Testing Core Functionality...")

    try:
        os.chdir(current_dir)
        from core.test_executor import AutonomousQATester

        # Create tester
        tester = AutonomousQATester()

        # Set proper app analysis structure (this was the issue)
        tester.app_analysis = {
            "app_path": "/test/app",
            "discovery_timestamp": 1699234567.89,
            "interfaces": ["web", "api"],
            "operations": [
                {
                    "name": "get_users",
                    "type": "read",
                    "permissions_required": ["user:read"],
                    "interface": "api",
                }
            ],
            "permissions": ["user:read", "user:write"],
            "data_entities": ["users", "roles"],
            "performance_targets": {"response_time_ms": 200, "concurrent_users": 50},
            "security_features": [
                "authentication",
                "authorization",
            ],  # This was missing!
            "documentation": {"README.md": "Test application"},
        }

        # Test persona generation
        personas = tester.generate_personas()
        report.add_result(
            "functionality",
            "Persona generation",
            True,
            f"Generated {len(personas)} personas",
        )

        # Test scenario generation
        scenarios = tester.generate_scenarios(personas[:2])
        report.add_result(
            "functionality",
            "Scenario generation",
            True,
            f"Generated {len(scenarios)} scenarios",
        )

    except Exception as e:
        report.add_result("functionality", "Core workflow", False, str(e))
        if "security_features" in str(e):
            report.add_issue(
                "App analysis missing required 'security_features' field",
                "HIGH",
                "Ensure app_analysis dict includes 'security_features': [] field",
            )


async def test_async_functionality(report: TestReport):
    """Test async functionality."""
    print("🔍 Testing Async Functionality...")

    try:
        os.chdir(current_dir)
        from core.database import QADatabase
        from core.services import ProjectService

        # Test async database
        db = QADatabase(":memory:")
        await db.initialize()
        report.add_result("functionality", "Async database", True)

        # Test async service
        project_service = ProjectService(db)
        report.add_result("functionality", "Async services", True)

    except Exception as e:
        report.add_result("functionality", "Async operations", False, str(e))


def analyze_dependencies(report: TestReport):
    """Analyze dependency issues."""
    print("🔍 Analyzing Dependencies...")

    # Check for required dependencies
    required_deps = [
        ("fastapi", "FastAPI web framework"),
        ("pydantic", "Data validation"),
        ("click", "CLI framework"),
        ("aiosqlite", "Async SQLite"),
        ("jinja2", "Template engine"),
        ("httpx", "HTTP client"),
    ]

    for dep, description in required_deps:
        try:
            __import__(dep)
            report.add_result("core_imports", f"Dependency: {dep}", True)
        except ImportError:
            report.add_result(
                "core_imports",
                f"Dependency: {dep}",
                False,
                f"{description} not available",
            )
            report.add_issue(
                f"Missing dependency: {dep}", "HIGH", f"Install with: pip install {dep}"
            )


def generate_usage_examples(report: TestReport):
    """Generate usage examples for working functionality."""
    print("🔍 Generating Usage Examples...")

    examples = []

    # Example 1: Direct usage from app directory
    examples.append(
        {
            "name": "Direct Usage (Recommended)",
            "description": "Run from the app directory for full functionality",
            "code": """
cd apps/qa_agentic_testing

# Basic usage
python -c "
from core.test_executor import AutonomousQATester
tester = AutonomousQATester()
print('✅ QA Tester ready!')
"

# API server
python -c "
from api.main import create_app
app = create_app()
print('✅ API app ready!')
"

# CLI
python -c "
from cli.main import cli
print('✅ CLI ready!')
"
""",
        }
    )

    # Example 2: Package import with PYTHONPATH
    examples.append(
        {
            "name": "Package Import (Alternative)",
            "description": "Import as package with proper Python path",
            "code": """
# From SDK root directory
PYTHONPATH=. python -c "
from apps.qa_agentic_testing import AutonomousQATester
tester = AutonomousQATester()
print('✅ Package import works!')
"
""",
        }
    )

    # Example 3: Basic workflow
    examples.append(
        {
            "name": "Basic Testing Workflow",
            "description": "Complete testing workflow example",
            "code": """
cd apps/qa_agentic_testing

python -c "
from core.test_executor import AutonomousQATester

# Initialize tester
tester = AutonomousQATester()

# Set up app analysis (IMPORTANT: include all required fields)
tester.app_analysis = {
    'app_path': '/your/app/path',
    'interfaces': ['web', 'api'],
    'operations': [{'name': 'get_data', 'type': 'read'}],
    'permissions': ['read', 'write'],
    'data_entities': ['users'],
    'security_features': ['authentication'],  # Required!
    'performance_targets': {'response_time_ms': 200}
}

# Generate personas and scenarios
personas = tester.generate_personas()
scenarios = tester.generate_scenarios(personas[:3])

print(f'Generated {len(personas)} personas, {len(scenarios)} scenarios')
"
""",
        }
    )

    for example in examples:
        report.add_recommendation(f"{example['name']}: {example['description']}")


def print_report(report: TestReport):
    """Print the comprehensive test report."""
    print("\n" + "=" * 80)
    print("📊 COMPREHENSIVE QA AGENTIC TESTING APP REPORT")
    print("=" * 80)

    # Import Results
    print("\n🔍 IMPORT TEST RESULTS:")
    print("-" * 40)
    passed_imports = sum(1 for r in report.results["core_imports"] if r["status"])
    total_imports = len(report.results["core_imports"])
    print(f"Overall: {passed_imports}/{total_imports} imports successful")

    for result in report.results["core_imports"]:
        status = "✅" if result["status"] else "❌"
        print(f"{status} {result['test']}")
        if not result["status"] and result["details"]:
            print(f"   Error: {result['details']}")

    # Functionality Results
    print("\n⚡ FUNCTIONALITY TEST RESULTS:")
    print("-" * 40)
    passed_func = sum(1 for r in report.results["functionality"] if r["status"])
    total_func = len(report.results["functionality"])
    print(f"Overall: {passed_func}/{total_func} functionality tests passed")

    for result in report.results["functionality"]:
        status = "✅" if result["status"] else "❌"
        print(f"{status} {result['test']}")
        if result["details"]:
            print(f"   Details: {result['details']}")

    # Issues and Fixes
    if report.results["issues"]:
        print("\n🚨 IDENTIFIED ISSUES:")
        print("-" * 40)
        for i, issue in enumerate(report.results["issues"], 1):
            severity_icon = {"HIGH": "🔴", "MEDIUM": "🟡", "LOW": "🟢"}.get(
                issue["severity"], "⚪"
            )
            print(f"{i}. {severity_icon} {issue['issue']} ({issue['severity']})")
            print(f"   Fix: {issue['fix']}")

    # Recommendations
    if report.results["recommendations"]:
        print("\n💡 RECOMMENDATIONS:")
        print("-" * 40)
        for i, rec in enumerate(report.results["recommendations"], 1):
            print(f"{i}. {rec}")

    # Overall Status
    total_tests = passed_imports + passed_func
    total_possible = total_imports + total_func
    success_rate = (total_tests / total_possible) * 100 if total_possible > 0 else 0

    print("\n📈 OVERALL STATUS:")
    print(f"Success Rate: {success_rate:.1f}% ({total_tests}/{total_possible})")

    if success_rate >= 80:
        print("🎉 The QA Agentic Testing app is largely functional!")
    elif success_rate >= 60:
        print("⚠️  The app has some issues but core functionality works.")
    else:
        print("🚨 The app needs significant fixes before use.")

    # Quick Start Guide
    print("\n🚀 QUICK START GUIDE:")
    print("-" * 40)
    print("1. Navigate to app directory: cd apps/qa_agentic_testing")
    print(
        "2. Test core functionality: python -c \"from core.test_executor import AutonomousQATester; print('Works!')\""
    )
    print("3. For API/CLI: Run from app directory")
    print("4. For package imports: Use PYTHONPATH=. from SDK root")
    print("5. Always include 'security_features': [] in app_analysis")


def main():
    """Run comprehensive test report."""
    report = TestReport()
    original_cwd = os.getcwd()

    try:
        print("🚀 Starting Comprehensive QA Agentic Testing App Analysis...")
        print("=" * 70)

        # Run all tests
        analyze_dependencies(report)
        test_import_structure(report)
        test_package_imports(report)
        test_api_cli_components(report)
        test_core_functionality(report)
        generate_usage_examples(report)

        # Run async tests
        try:
            asyncio.run(test_async_functionality(report))
        except Exception as e:
            report.add_result("functionality", "Async test runner", False, str(e))

        # Generate final report
        print_report(report)

    finally:
        os.chdir(original_cwd)


if __name__ == "__main__":
    main()
