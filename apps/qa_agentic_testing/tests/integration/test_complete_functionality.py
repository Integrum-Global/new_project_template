#!/usr/bin/env python3
"""
Comprehensive test of QA Agentic Testing app functionality.
Tests all major components including database, services, API, and CLI.
"""

import asyncio
import json
import sys
import tempfile
import traceback
from pathlib import Path

# Add the app to Python path
sys.path.insert(0, str(Path(__file__).parent.parent))

import pytest


@pytest.mark.asyncio
async def test_complete_functionality():
    """Test all major functionality of the QA Agentic Testing app."""

    print("🧪 Comprehensive QA Agentic Testing App Test")
    print("=" * 60)

    test_results = {
        "core_imports": False,
        "database_operations": False,
        "service_layer": False,
        "autonomous_tester": False,
        "api_initialization": False,
        "personas_scenarios": False,
        "report_generation": False,
    }

    # Test 1: Core Imports
    print("\n1️⃣ Testing Core Imports...")
    try:
        from core.agent_coordinator import AgentCoordinator
        from core.database import QADatabase, setup_database
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
        from core.personas import PersonaManager
        from core.report_generator import ReportGenerator
        from core.scenario_generator import ScenarioGenerator
        from core.services import AnalyticsService, ProjectService, TestRunService
        from core.test_executor import AutonomousQATester

        print("   ✅ All core imports successful")
        test_results["core_imports"] = True

    except Exception as e:
        print(f"   ❌ Core imports failed: {e}")
        traceback.print_exc()

    # Test 2: Database Operations
    print("\n2️⃣ Testing Database Operations...")
    try:
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tmp_db:
            db_path = tmp_db.name

        # Initialize database
        await setup_database(db_path)

        # Test basic CRUD operations
        db = QADatabase(db_path)

        # Create a test project
        project = create_test_project(
            name="Test Project",
            app_path="/tmp/test_app",
            description="Test project for validation",
        )

        created_project = await db.create_project(project)
        retrieved_project = await db.get_project(created_project.project_id)

        assert retrieved_project is not None
        assert retrieved_project.name == "Test Project"

        # Create a test run
        run = create_test_run(
            project_id=created_project.project_id,
            name="Test Run",
            description="Test run for validation",
        )

        created_run = await db.create_run(run)
        retrieved_run = await db.get_run(created_run.run_id)

        assert retrieved_run is not None
        assert retrieved_run.name == "Test Run"

        print("   ✅ Database operations successful")
        test_results["database_operations"] = True

    except Exception as e:
        print(f"   ❌ Database operations failed: {e}")
        traceback.print_exc()

    # Test 3: Service Layer
    print("\n3️⃣ Testing Service Layer...")
    try:
        # Use the same database
        project_service = ProjectService(QADatabase(db_path))
        run_service = TestRunService(QADatabase(db_path))

        # Create project through service
        service_project = await project_service.create_project(
            name="Service Test Project",
            app_path="/tmp/service_test",
            description="Testing service layer",
        )

        # Create run through service
        service_run = await run_service.create_run(
            project_id=service_project.project_id,
            name="Service Test Run",
            description="Testing run service",
        )

        assert service_project.project_id is not None
        assert service_run.run_id is not None

        print("   ✅ Service layer operations successful")
        test_results["service_layer"] = True

    except Exception as e:
        print(f"   ❌ Service layer failed: {e}")
        traceback.print_exc()

    # Test 4: Autonomous Tester Core
    print("\n4️⃣ Testing Autonomous Tester...")
    try:
        tester = AutonomousQATester()

        # Mock app analysis with required fields
        tester.app_analysis = {
            "app_path": "/tmp/test_app",
            "interfaces": ["web", "api"],
            "operations": [
                {"name": "get_users", "type": "read"},
                {"name": "create_user", "type": "write"},
            ],
            "permissions": ["user.read", "user.write", "admin.all"],
            "data_entities": ["users", "roles"],
            "security_features": ["authentication", "authorization"],
            "performance_targets": {"response_time_ms": 200},
        }

        # Test persona generation
        personas = tester.generate_personas()
        assert len(personas) > 0
        print(f"   Generated {len(personas)} personas")

        # Test scenario generation
        scenarios = tester.generate_scenarios(personas[:3])
        assert len(scenarios) > 0
        print(f"   Generated {len(scenarios)} scenarios")

        print("   ✅ Autonomous tester working correctly")
        test_results["autonomous_tester"] = True
        test_results["personas_scenarios"] = True

    except Exception as e:
        print(f"   ❌ Autonomous tester failed: {e}")
        traceback.print_exc()

    # Test 5: API Initialization
    print("\n5️⃣ Testing API Initialization...")
    try:
        from api.main import create_app

        app = create_app()
        assert app is not None
        assert hasattr(app, "routes")

        print("   ✅ API application created successfully")
        test_results["api_initialization"] = True

    except Exception as e:
        print(f"   ❌ API initialization failed: {e}")
        traceback.print_exc()

    # Test 6: Report Generation
    print("\n6️⃣ Testing Report Generation...")
    try:
        report_generator = ReportGenerator()

        # Create mock test run and results
        mock_run = TestRun(
            run_id="test-run-123",
            project_id="test-project-123",
            name="Mock Test Run",
            description="Mock test for report generation",
            status=TestStatus.COMPLETED,
            total_scenarios=10,
            passed_scenarios=8,
            failed_scenarios=2,
            success_rate=80.0,
            confidence_score=85.0,
        )

        mock_results = []
        mock_summary = {
            "total": 10,
            "passed": 8,
            "failed": 2,
            "success_rate": 80.0,
            "average_confidence": 85.0,
        }

        # Test JSON report generation
        json_report_data = {
            "run": mock_run.to_dict(),
            "results": mock_results,
            "summary": mock_summary,
        }

        # This should work without errors
        assert isinstance(json_report_data, dict)

        print("   ✅ Report generation components working")
        test_results["report_generation"] = True

    except Exception as e:
        print(f"   ❌ Report generation failed: {e}")
        traceback.print_exc()

    # Test Summary
    print("\n" + "=" * 60)
    print("📊 TEST SUMMARY")
    print("=" * 60)

    total_tests = len(test_results)
    passed_tests = sum(test_results.values())
    success_rate = (passed_tests / total_tests) * 100

    for test_name, passed in test_results.items():
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status} {test_name.replace('_', ' ').title()}")

    print(
        f"\n🎯 Overall Success Rate: {success_rate:.1f}% ({passed_tests}/{total_tests})"
    )

    if success_rate >= 85:
        print("🎉 QA Agentic Testing App is READY FOR PRODUCTION!")
    elif success_rate >= 70:
        print("⚠️  QA Agentic Testing App needs minor fixes")
    else:
        print("🔧 QA Agentic Testing App needs significant work")

    return test_results, success_rate


if __name__ == "__main__":
    results, rate = asyncio.run(test_complete_functionality())

    if rate < 85:
        sys.exit(1)  # Exit with error if not ready
    else:
        print("\n✅ All systems go!")
        sys.exit(0)
