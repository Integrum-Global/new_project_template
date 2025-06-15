#!/usr/bin/env python3
"""
Test Report Generation functionality.
Demonstrates how to generate comprehensive HTML reports.
"""

import asyncio
import json
import sys
from datetime import datetime
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

import pytest
from core.report_generator import ReportGenerator

from tests import get_results_path


@pytest.mark.asyncio
async def test_report_generation():
    """Test HTML report generation capabilities."""

    print("🧪 Report Generation Test")
    print("=" * 50)

    test_results = {
        "report_generator_import": False,
        "html_generation": False,
        "json_generation": False,
        "report_features": False,
    }

    # Test 1: Import Report Generator
    print("\n1️⃣ Testing Report Generator Import...")
    try:
        report_gen = ReportGenerator()
        print("   ✅ Report generator imported successfully")
        test_results["report_generator_import"] = True
    except Exception as e:
        print(f"   ❌ Import failed: {e}")
        return False

    # Test 2: Generate Sample Report Data
    print("\n2️⃣ Generating Sample Report Data...")

    sample_report_data = {
        "metadata": {
            "app_name": "Test Application",
            "app_path": "/test/path",
            "test_date": datetime.now().isoformat(),
            "test_count": 10,
            "duration": 45.2,
        },
        "execution_summary": {
            "total_tests": 10,
            "passed": 8,
            "failed": 1,
            "timeout": 0,
            "error": 1,
            "success_rate": 80.0,
            "total_duration": 45.2,
            "average_duration": 4.52,
        },
        "test_results": [
            {
                "test_id": "test_sample_1",
                "persona": "admin",
                "scenario": "create_user",
                "status": "pass",
                "confidence": 95,
                "duration": 3.2,
                "timestamp": datetime.now().isoformat(),
            },
            {
                "test_id": "test_sample_2",
                "persona": "user",
                "scenario": "read_data",
                "status": "pass",
                "confidence": 90,
                "duration": 2.1,
                "timestamp": datetime.now().isoformat(),
            },
            {
                "test_id": "test_sample_3",
                "persona": "manager",
                "scenario": "approve_request",
                "status": "warning",
                "confidence": 75,
                "duration": 5.5,
                "timestamp": datetime.now().isoformat(),
            },
            {
                "test_id": "test_sample_4",
                "persona": "user",
                "scenario": "unauthorized_access",
                "status": "fail",
                "confidence": 100,
                "duration": 1.2,
                "timestamp": datetime.now().isoformat(),
            },
        ],
        "app_analysis": {
            "interfaces": ["CLI", "Web", "API"],
            "operations": [
                {"name": "create", "type": "write"},
                {"name": "read", "type": "read"},
                {"name": "update", "type": "write"},
                {"name": "delete", "type": "write"},
            ],
            "permissions": [
                "user:read",
                "user:write",
                "admin:all",
                "manager:approve",
                "data:export",
            ],
        },
        "scenarios": [
            {
                "name": "Admin User Creation",
                "type": "functional",
                "priority": "high",
                "personas": ["admin"],
                "steps": 5,
            },
            {
                "name": "Security Boundary Test",
                "type": "security",
                "priority": "high",
                "personas": ["user", "admin"],
                "steps": 8,
            },
        ],
        "personas": {
            "admin": {
                "name": "Admin User",
                "role": "System Administrator",
                "permissions": ["*"],
                "goals": ["Manage system", "Ensure security"],
            },
            "user": {
                "name": "Regular User",
                "role": "Standard User",
                "permissions": ["user:read:self", "data:read:own"],
                "goals": ["Access data", "Complete tasks"],
            },
            "manager": {
                "name": "Department Manager",
                "role": "Manager",
                "permissions": ["user:read", "user:update", "manager:approve"],
                "goals": ["Manage team", "Approve requests"],
            },
        },
    }

    # Test 3: Generate JSON Report
    print("\n3️⃣ Generating JSON Report...")
    try:
        json_path = get_results_path("sample_report.json")
        with open(json_path, "w") as f:
            json.dump(sample_report_data, f, indent=2)

        print(f"   ✅ JSON report saved: {json_path}")
        print(f"   📊 Size: {json_path.stat().st_size:,} bytes")
        test_results["json_generation"] = True
    except Exception as e:
        print(f"   ❌ JSON generation failed: {e}")

    # Test 4: Generate HTML Report
    print("\n4️⃣ Generating HTML Report...")
    try:
        html_path = get_results_path("sample_report.html")
        report_gen.generate_html_report(sample_report_data, html_path)

        print(f"   ✅ HTML report generated: {html_path}")
        print(f"   📊 Size: {html_path.stat().st_size:,} bytes")
        test_results["html_generation"] = True

        # Verify HTML contains expected sections
        with open(html_path, "r") as f:
            html_content = f.read()

        expected_sections = [
            "Overview",
            "Methodology",
            "Personas",
            "Results",
            "Validation",
            "AI Insights",
            "Performance",
        ]

        missing_sections = []
        for section in expected_sections:
            if section not in html_content:
                missing_sections.append(section)

        if missing_sections:
            print(f"   ⚠️ Missing sections: {', '.join(missing_sections)}")
        else:
            print(f"   ✅ All {len(expected_sections)} sections present")
            test_results["report_features"] = True

    except Exception as e:
        print(f"   ❌ HTML generation failed: {e}")
        import traceback

        traceback.print_exc()

    # Summary
    print("\n" + "=" * 50)
    print("📊 Test Summary:")
    passed = sum(1 for v in test_results.values() if v)
    total = len(test_results)

    for component, passed_test in test_results.items():
        status = "✅" if passed_test else "❌"
        print(f"   {status} {component.replace('_', ' ').title()}")

    print(f"\n🎯 Overall: {passed}/{total} tests passed ({passed/total*100:.1f}%)")

    # Save test results
    results_file = get_results_path("report_generation_test_results.json")
    with open(results_file, "w") as f:
        json.dump(
            {
                "test_name": "Report Generation Test",
                "timestamp": datetime.now().isoformat(),
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
    success = asyncio.run(test_report_generation())
    sys.exit(0 if success else 1)
