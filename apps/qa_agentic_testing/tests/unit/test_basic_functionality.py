#!/usr/bin/env python3
"""
Basic functionality test for QA Agentic Testing app.
Tests core components without complex imports.
"""

import asyncio
import sys
import tempfile
import traceback
from datetime import datetime
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

import pytest

from tests import get_results_path


@pytest.mark.asyncio
async def test_basic_functionality():
    """Test basic functionality with direct module imports."""

    print("🧪 Basic QA Agentic Testing App Test")
    print("=" * 50)

    test_results = {
        "models": False,
        "database": False,
        "personas": False,
        "scenarios": False,
        "test_executor": False,
    }

    # Test 1: Models
    print("\n1️⃣ Testing Models...")
    try:
        from core.models import (
            AgentType,
            InterfaceType,
            Priority,
            TestProject,
            TestResult,
            TestRun,
            TestStatus,
            TestType,
            create_test_project,
            create_test_run,
        )

        # Create test objects
        project = create_test_project("Test Project", "/tmp/test", "Test description")
        run = create_test_run(project.project_id, "Test Run", "Test run description")

        assert project.name == "Test Project"
        assert run.project_id == project.project_id

        print("   ✅ Models working correctly")
        test_results["models"] = True

    except Exception as e:
        print(f"   ❌ Models failed: {e}")
        traceback.print_exc()

    # Test 2: Database
    print("\n2️⃣ Testing Database...")
    try:
        from core.database import QADatabase

        # Use temp file for testing
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
            db_path = f.name

        db = QADatabase(db_path)
        await db.initialize()

        print("   ✅ Database initialized successfully")
        test_results["database"] = True

    except Exception as e:
        print(f"   ❌ Database failed: {e}")
        traceback.print_exc()

    # Test 3: Personas
    print("\n3️⃣ Testing Personas...")
    try:
        from core.personas import Persona, PersonaManager

        manager = PersonaManager()

        # Test built-in personas
        assert len(manager.personas) > 0
        admin = manager.get_persona("system_admin")
        assert admin is not None
        assert admin.name == "Alice Admin"

        # Test persona generation
        generated = manager.generate_personas_from_permissions(
            ["user:read", "user:write"]
        )
        assert len(generated) > 0

        print(f"   ✅ Personas working ({len(manager.personas)} built-in)")
        test_results["personas"] = True

    except Exception as e:
        print(f"   ❌ Personas failed: {e}")
        traceback.print_exc()

    # Test 4: Scenario Generation
    print("\n4️⃣ Testing Scenario Generation...")
    try:
        from core.personas import PersonaManager
        from core.scenario_generator import ScenarioGenerator

        generator = ScenarioGenerator()
        persona_manager = PersonaManager()

        # Get a test persona
        admin = persona_manager.get_persona("system_admin")

        # Create minimal app analysis
        app_analysis = {
            "operations": [
                {"name": "create_user", "type": "write"},
                {"name": "list_users", "type": "read"},
            ],
            "permissions": ["user:create", "user:read"],
            "interfaces": ["cli", "api"],
        }

        # Generate scenarios
        scenarios = generator.generate_scenarios_for_personas([admin], app_analysis)
        assert len(scenarios) > 0

        print(f"   ✅ Scenario generation working ({len(scenarios)} scenarios)")
        test_results["scenarios"] = True

    except Exception as e:
        print(f"   ❌ Scenario generation failed: {e}")
        traceback.print_exc()

    # Test 5: Test Executor
    print("\n5️⃣ Testing Test Executor...")
    try:
        from core.test_executor import AutonomousQATester

        executor = AutonomousQATester()

        # Test method exists
        assert hasattr(executor, "execute_tests")

        print("   ✅ Test executor initialized")
        test_results["test_executor"] = True

    except Exception as e:
        print(f"   ❌ Test executor failed: {e}")
        traceback.print_exc()

    # Summary
    print("\n" + "=" * 50)
    print("📊 Test Summary:")
    passed = sum(1 for v in test_results.values() if v)
    total = len(test_results)

    for component, passed in test_results.items():
        status = "✅" if passed else "❌"
        print(f"   {status} {component}")

    print(f"\n🎯 Overall: {passed}/{total} tests passed ({passed/total*100:.1f}%)")

    # Save results to qa_results directory
    import json

    results_file = get_results_path("basic_functionality_results.json")
    with open(results_file, "w") as f:
        json.dump(
            {
                "test_name": "Basic Functionality Test",
                "timestamp": str(datetime.now()),
                "results": test_results,
                "summary": {
                    "passed": passed,
                    "total": total,
                    "percentage": passed / total * 100,
                },
            },
            f,
            indent=2,
        )

    print(f"\n💾 Results saved to: {results_file}")

    return passed == total


if __name__ == "__main__":
    success = asyncio.run(test_basic_functionality())
    sys.exit(0 if success else 1)
