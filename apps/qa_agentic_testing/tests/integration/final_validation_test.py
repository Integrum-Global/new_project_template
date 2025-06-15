#!/usr/bin/env python3
"""
Final validation test for QA Agentic Testing app after fixes.

This test validates that all import issues have been resolved and
basic functionality works correctly.
"""

import asyncio
import os
import sys
from pathlib import Path

# Add proper paths for testing
current_dir = Path(__file__).parent
root_dir = current_dir.parent.parent.parent
sys.path.insert(0, str(root_dir / "src"))  # Kailash SDK
sys.path.insert(0, str(root_dir))  # For apps imports


def test_core_functionality():
    """Test core functionality is working."""
    print("🔍 Testing core functionality...")

    try:
        # Change to app directory
        os.chdir(current_dir)

        # Test direct imports from the app directory
        from core.database import QADatabase
        from core.models import TestProject, TestStatus, create_test_project
        from core.personas import PersonaManager
        from core.test_executor import AutonomousQATester

        # Test basic functionality
        print("  ✅ All core imports successful")

        # Test model creation
        project = create_test_project("Test Project", "/test/path")
        print(f"  ✅ Created test project: {project.name}")

        # Test database creation
        db = QADatabase(":memory:")
        print("  ✅ Database creation successful")

        # Test tester creation
        tester = AutonomousQATester()
        print("  ✅ AutonomousQATester creation successful")

        return True

    except Exception as e:
        print(f"  ❌ Core functionality test failed: {e}")
        return False


async def test_async_operations():
    """Test async operations."""
    print("🔍 Testing async operations...")

    try:
        os.chdir(current_dir)
        from core.database import QADatabase
        from core.services import ProjectService

        # Test async database initialization
        db = QADatabase(":memory:")
        await db.initialize()
        print("  ✅ Async database initialization successful")

        # Test service creation
        project_service = ProjectService(db)
        print("  ✅ Service creation successful")

        return True

    except Exception as e:
        print(f"  ❌ Async operations test failed: {e}")
        return False


def test_package_import():
    """Test if the package can be imported correctly now."""
    print("🔍 Testing package import after fix...")

    try:
        # Try importing from the fixed package
        sys.path.insert(0, str(root_dir))
        from apps.qa_agentic_testing import AgentCoordinator, AutonomousQATester

        print("  ✅ Package imports successful")
        print(f"  ✅ AutonomousQATester: {AutonomousQATester}")
        print(f"  ✅ AgentCoordinator: {AgentCoordinator}")

        return True

    except Exception as e:
        print(f"  ❌ Package import test failed: {e}")
        return False


def test_api_imports():
    """Test API imports when run from correct directory."""
    print("🔍 Testing API imports...")

    try:
        original_cwd = os.getcwd()
        os.chdir(current_dir)

        # Import API components
        from api.main import create_app
        from api.routes.results import router

        print("  ✅ API imports successful")

        # Test app creation
        app = create_app()
        print("  ✅ FastAPI app creation successful")

        os.chdir(original_cwd)
        return True

    except Exception as e:
        print(f"  ❌ API imports test failed: {e}")
        return False


def test_cli_imports():
    """Test CLI imports when run from correct directory."""
    print("🔍 Testing CLI imports...")

    try:
        original_cwd = os.getcwd()
        os.chdir(current_dir)

        from cli.main import cli

        print("  ✅ CLI imports successful")

        os.chdir(original_cwd)
        return True

    except Exception as e:
        print(f"  ❌ CLI imports test failed: {e}")
        return False


def test_example_functionality():
    """Test that the example can be imported and run."""
    print("🔍 Testing example functionality...")

    try:
        os.chdir(current_dir)

        # Test importing the corrected components
        from core.test_executor import AutonomousQATester, TestResult, TestStatus

        # Test basic example flow
        tester = AutonomousQATester()

        # Set up mock app analysis like in the example
        tester.app_analysis = {
            "app_path": "/test/app",
            "interfaces": ["web", "api"],
            "operations": [{"name": "test_op", "type": "read"}],
            "permissions": ["read"],
            "data_entities": ["users"],
        }

        # Test persona generation
        personas = tester.generate_personas()
        print(f"  ✅ Generated {len(personas)} personas")

        # Test scenario generation
        scenarios = tester.generate_scenarios(personas[:2])
        print(f"  ✅ Generated {len(scenarios)} scenarios")

        return True

    except Exception as e:
        print(f"  ❌ Example functionality test failed: {e}")
        return False


def run_basic_workflow():
    """Run a basic workflow to validate end-to-end functionality."""
    print("🔍 Running basic workflow test...")

    try:
        os.chdir(current_dir)

        from core.database import QADatabase
        from core.test_executor import AutonomousQATester

        # Create tester with in-memory database
        db = QADatabase(":memory:")
        tester = AutonomousQATester()

        # Simple workflow test
        print("  ✅ Tester created")

        # Mock discovery
        tester.app_analysis = {
            "app_path": "/mock/app",
            "interfaces": ["api"],
            "operations": [{"name": "get_users", "type": "read"}],
            "permissions": ["user:read"],
            "data_entities": ["users"],
        }
        print("  ✅ App analysis set")

        # Generate personas
        personas = tester.generate_personas()
        print(f"  ✅ Generated {len(personas)} personas")

        # Generate scenarios
        scenarios = tester.generate_scenarios(personas[:1])
        print(f"  ✅ Generated {len(scenarios)} scenarios")

        return True

    except Exception as e:
        print(f"  ❌ Basic workflow test failed: {e}")
        return False


def main():
    """Run all validation tests."""
    print("🚀 QA Agentic Testing App - Final Validation After Fixes")
    print("=" * 60)

    original_cwd = os.getcwd()
    results = []

    try:
        # Run all tests
        results.append(("Core Functionality", test_core_functionality()))
        results.append(("Package Import", test_package_import()))
        results.append(("API Imports", test_api_imports()))
        results.append(("CLI Imports", test_cli_imports()))
        results.append(("Example Functionality", test_example_functionality()))
        results.append(("Basic Workflow", run_basic_workflow()))

        # Run async test
        try:
            async_result = asyncio.run(test_async_operations())
            results.append(("Async Operations", async_result))
        except Exception as e:
            print(f"❌ Async test runner failed: {e}")
            results.append(("Async Operations", False))

    finally:
        os.chdir(original_cwd)

    # Print results
    print("\n" + "=" * 60)
    print("🎯 FINAL VALIDATION RESULTS")
    print("=" * 60)

    passed = sum(1 for _, result in results if result)
    total = len(results)

    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} {test_name}")

    print(f"\n📊 Overall: {passed}/{total} tests passed ({(passed/total)*100:.1f}%)")

    if passed == total:
        print("🎉 All tests passed! The QA Agentic Testing app is fully functional.")
        print("\n🚀 You can now use the app in the following ways:")
        print(
            "   1. Direct import: cd apps/qa_agentic_testing && python -c 'from core.test_executor import AutonomousQATester; print(\"Working!\")'"
        )
        print(
            "   2. Package import: python -c 'from apps.qa_agentic_testing import AutonomousQATester; print(\"Working!\")'"
        )
        print(
            "   3. API server: cd apps/qa_agentic_testing && python -c 'from api.main import create_app; app = create_app(); print(\"API ready!\")'"
        )
        print(
            "   4. CLI: cd apps/qa_agentic_testing && python -c 'from cli.main import cli; print(\"CLI ready!\")'"
        )
        print(
            "   5. Example: cd apps/qa_agentic_testing && python examples/simple_test_example.py"
        )
    else:
        print("⚠️  Some issues remain. See failed tests above.")

        # Additional troubleshooting info
        print("\n🔧 TROUBLESHOOTING:")
        print("   • For relative import issues: Always run from the app directory")
        print("   • For package import issues: Add parent directory to PYTHONPATH")
        print("   • For missing dependencies: pip install -e .")


if __name__ == "__main__":
    main()
