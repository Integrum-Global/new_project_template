#!/usr/bin/env python3
"""
Simple QA Agentic Testing Example

This example demonstrates how to use the QA Agentic Testing framework
to test any application autonomously using advanced AI agent systems.
"""

import asyncio
import sys
from pathlib import Path

# Add the parent directory to Python path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from apps.qa_agentic_testing import AutonomousQATester


async def main():
    """Run a simple QA testing example."""

    print("🤖 QA Agentic Testing Framework - Simple Example")
    print("=" * 55)

    # Initialize the autonomous QA tester
    print("\n📋 Step 1: Initialize QA Tester")
    # Note: When testing a real app, pass app_path to automatically store
    # results in the target app's qa_results folder:
    # tester = AutonomousQATester(app_path=Path("/path/to/app"))
    tester = AutonomousQATester(output_dir=Path(__file__).parent / "test_results")
    print("✅ AutonomousQATester initialized")

    # Simulate app discovery (normally this would analyze a real app)
    print("\n🔍 Step 2: Simulate App Discovery")
    tester.app_analysis = {
        "app_path": "/example/sample_app",
        "discovery_timestamp": 1699234567.89,
        "interfaces": ["cli", "web", "api"],
        "operations": [
            {
                "name": "list_users",
                "type": "read",
                "permissions_required": ["user:read"],
                "interface": "api",
            },
            {
                "name": "create_user",
                "type": "create",
                "permissions_required": ["user:create"],
                "interface": "api",
            },
            {
                "name": "update_user",
                "type": "update",
                "permissions_required": ["user:update"],
                "interface": "api",
            },
            {
                "name": "delete_user",
                "type": "delete",
                "permissions_required": ["user:delete"],
                "interface": "api",
            },
            {
                "name": "login",
                "type": "auth",
                "permissions_required": [],
                "interface": "web",
            },
            {
                "name": "dashboard",
                "type": "read",
                "permissions_required": ["user:read"],
                "interface": "web",
            },
        ],
        "permissions": [
            "user:read",
            "user:create",
            "user:update",
            "user:delete",
            "admin:*",
            "manager:team",
            "analyst:reports",
        ],
        "data_entities": ["users", "roles", "permissions"],
        "performance_targets": {
            "response_time_ms": 200,
            "concurrent_users": 50,
            "throughput_rps": 100,
        },
        "security_features": ["authentication", "authorization", "audit_logging"],
        "documentation": {
            "README.md": "Sample application with user management features..."
        },
    }
    print(f"✅ Discovered {len(tester.app_analysis['interfaces'])} interfaces")
    print(f"✅ Found {len(tester.app_analysis['operations'])} operations")
    print(
        f"✅ Identified {len(tester.app_analysis['permissions'])} permission patterns"
    )

    # Generate personas for testing
    print("\n🎭 Step 3: Generate Test Personas")
    personas = tester.generate_personas()
    print(f"✅ Generated {len(personas)} personas:")
    for persona in personas[:3]:  # Show first 3
        print(
            f"   👤 {persona.name} ({persona.role}) - {len(persona.permissions)} permissions"
        )

    # Generate test scenarios
    print("\n📝 Step 4: Generate Test Scenarios")
    scenarios = tester.generate_scenarios(personas[:3])  # Use first 3 personas
    print(f"✅ Generated {len(scenarios)} test scenarios:")
    for scenario in scenarios[:4]:  # Show first 4
        print(
            f"   📋 {scenario.name} - {scenario.scenario_type.value} ({len(scenario.steps)} steps)"
        )

    # Execute tests (simulated execution)
    print("\n⚡ Step 5: Execute Tests (Simulated)")
    print("   🔧 Simulating test execution with AI agent analysis...")

    # Create mock test results for demonstration
    import time

    from apps.qa_agentic_testing.core.test_executor import (
        TestResult,
        TestStatus,
        ValidationResult,
    )

    mock_results = []
    start_time = time.time()

    for i, scenario in enumerate(scenarios[:4]):
        for persona_key in scenario.target_personas[:1]:  # One persona per scenario
            result = TestResult(
                test_id=f"test_{i}_{persona_key}",
                scenario_id=scenario.scenario_id,
                persona_key=persona_key,
                status=TestStatus.COMPLETED,
                validation_result=(
                    ValidationResult.PASS if i < 3 else ValidationResult.WARNING
                ),
                start_time=start_time + i,
                end_time=start_time + i + 0.5,
                duration_seconds=0.5,
                llm_analysis=None,  # Would contain real AI analysis
                execution_log=[
                    f"Starting test for persona {persona_key}",
                    f"Executing {len(scenario.steps)} steps",
                    (
                        "All steps completed successfully"
                        if i < 3
                        else "Some steps had warnings"
                    ),
                ],
                performance_metrics={
                    "total_duration": 0.5,
                    "step_count": len(scenario.steps),
                    "average_step_duration": 0.1,
                    "success_rate": 100.0 if i < 3 else 75.0,
                },
                validation_details={
                    "total_steps": len(scenario.steps),
                    "passed_steps": (
                        len(scenario.steps) if i < 3 else len(scenario.steps) - 1
                    ),
                    "failed_steps": 0 if i < 3 else 1,
                    "success_rate": 100.0 if i < 3 else 75.0,
                    "expected_success_rate": 90.0,
                },
                confidence_score=95.0 if i < 3 else 80.0,
            )
            mock_results.append(result)

    tester.test_results = mock_results

    # Calculate summary
    from apps.qa_agentic_testing.core.test_executor import TestExecutionSummary

    total_tests = len(mock_results)
    passed_tests = sum(
        1 for r in mock_results if r.validation_result == ValidationResult.PASS
    )
    warning_tests = sum(
        1 for r in mock_results if r.validation_result == ValidationResult.WARNING
    )
    failed_tests = sum(
        1 for r in mock_results if r.validation_result == ValidationResult.FAIL
    )

    tester.execution_summary = TestExecutionSummary(
        total_tests=total_tests,
        passed_tests=passed_tests,
        failed_tests=failed_tests,
        warning_tests=warning_tests,
        skipped_tests=0,
        success_rate=(passed_tests / total_tests) * 100,
        average_duration=0.5,
        total_duration=total_tests * 0.5,
        confidence_score=90.0,
        performance_summary={
            "average_response_time": 0.1,
            "total_execution_time": total_tests * 0.5,
            "tests_per_minute": 120,
        },
        persona_results={},
        scenario_results={},
    )

    print(f"✅ Executed {total_tests} tests")
    print(
        f"   📊 Results: {passed_tests} passed, {warning_tests} warnings, {failed_tests} failed"
    )
    print(f"   🎯 Success rate: {tester.execution_summary.success_rate:.1f}%")
    print(f"   🔬 AI confidence: {tester.execution_summary.confidence_score:.1f}%")

    # Generate reports
    print("\n📊 Step 6: Generate Test Reports")
    output_dir = Path(__file__).parent / "test_results"
    output_dir.mkdir(exist_ok=True)

    # Generate HTML report
    html_report = tester.generate_report(
        output_file=output_dir / "qa_test_report.html", format="html"
    )
    print(f"✅ HTML report generated: {html_report}")

    # Generate JSON report
    json_report = tester.generate_report(
        output_file=output_dir / "qa_test_results.json", format="json"
    )
    print(f"✅ JSON report generated: {json_report}")

    # Summary
    print("\n🎉 QA Agentic Testing Complete!")
    print(f"   📈 Tested {len(tester.app_analysis['interfaces'])} interfaces")
    print(f"   🎭 Used {len(personas)} AI personas")
    print(f"   📋 Executed {len(scenarios)} scenarios")
    print("   🤖 Leveraged advanced agent systems (A2A, Self-Organizing, Iterative)")
    print("   📊 Generated comprehensive reports")
    print(f"\n   View results: file://{html_report.absolute()}")


if __name__ == "__main__":
    asyncio.run(main())
