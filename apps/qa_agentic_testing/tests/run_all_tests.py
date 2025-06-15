#!/usr/bin/env python3
"""
Test Runner for QA Agentic Testing

Runs all tests and generates comprehensive HTML reports.
"""

import asyncio
import json
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.report_generator import ReportGenerator

from tests import get_results_path


class TestRunner:
    """Runs all QA Agentic tests and generates reports."""

    def __init__(self):
        self.report_generator = ReportGenerator()
        self.test_results = []
        self.start_time = None
        self.end_time = None

    async def run_all_tests(self):
        """Run all tests in the test suite."""
        print("🚀 QA Agentic Testing - Full Test Suite")
        print("=" * 60)

        self.start_time = time.time()

        # Define test categories and their tests
        test_categories = {
            "unit": [
                "test_basic_functionality.py",
                "test_working_components.py",
                "test_imports_and_functionality.py",
                "test_imports_fixed.py",
            ],
            "integration": [
                "test_complete_functionality.py",
                "final_validation_test.py",
            ],
            "functional": ["test_user_management_system.py"],
        }

        # Run tests by category
        for category, test_files in test_categories.items():
            print(f"\n📁 Running {category.upper()} tests...")
            print("-" * 40)

            for test_file in test_files:
                test_path = Path(__file__).parent / category / test_file
                if test_path.exists():
                    await self.run_test(test_path, category)
                else:
                    print(f"   ⚠️ Test not found: {test_file}")

        self.end_time = time.time()

        # Generate comprehensive report
        await self.generate_report()

    async def run_test(self, test_path: Path, category: str):
        """Run a single test file."""
        test_name = test_path.stem
        print(f"\n   🧪 Running: {test_name}")

        start_time = time.time()

        try:
            # Run the test as a subprocess
            result = subprocess.run(
                [sys.executable, str(test_path)],
                capture_output=True,
                text=True,
                timeout=300,  # 5 minute timeout
            )

            duration = time.time() - start_time

            # Determine test status
            if result.returncode == 0:
                status = "pass"
                print(f"      ✅ PASSED ({duration:.2f}s)")
            else:
                status = "fail"
                print(f"      ❌ FAILED ({duration:.2f}s)")

            # Store result
            self.test_results.append(
                {
                    "test_id": test_name,
                    "category": category,
                    "status": status,
                    "duration": duration,
                    "stdout": result.stdout,
                    "stderr": result.stderr,
                    "returncode": result.returncode,
                    "timestamp": datetime.now().isoformat(),
                }
            )

        except subprocess.TimeoutExpired:
            duration = time.time() - start_time
            print(f"      ⏱️ TIMEOUT ({duration:.2f}s)")

            self.test_results.append(
                {
                    "test_id": test_name,
                    "category": category,
                    "status": "timeout",
                    "duration": duration,
                    "stdout": "",
                    "stderr": "Test timed out after 300 seconds",
                    "returncode": -1,
                    "timestamp": datetime.now().isoformat(),
                }
            )

        except Exception as e:
            duration = time.time() - start_time
            print(f"      💥 ERROR: {e}")

            self.test_results.append(
                {
                    "test_id": test_name,
                    "category": category,
                    "status": "error",
                    "duration": duration,
                    "stdout": "",
                    "stderr": str(e),
                    "returncode": -1,
                    "timestamp": datetime.now().isoformat(),
                }
            )

    async def generate_report(self):
        """Generate comprehensive HTML report."""
        print("\n📊 Generating Test Report...")
        print("=" * 60)

        # Calculate statistics
        total_tests = len(self.test_results)
        passed_tests = sum(1 for r in self.test_results if r["status"] == "pass")
        failed_tests = sum(1 for r in self.test_results if r["status"] == "fail")
        timeout_tests = sum(1 for r in self.test_results if r["status"] == "timeout")
        error_tests = sum(1 for r in self.test_results if r["status"] == "error")

        total_duration = self.end_time - self.start_time

        # Prepare report data
        report_data = {
            "metadata": {
                "app_name": "QA Agentic Testing",
                "app_path": str(Path(__file__).parent.parent),
                "test_date": datetime.now().isoformat(),
                "test_count": total_tests,
                "duration": total_duration,
            },
            "execution_summary": {
                "total_tests": total_tests,
                "passed": passed_tests,
                "failed": failed_tests,
                "timeout": timeout_tests,
                "error": error_tests,
                "success_rate": (
                    (passed_tests / total_tests * 100) if total_tests > 0 else 0
                ),
                "total_duration": total_duration,
                "average_duration": (
                    total_duration / total_tests if total_tests > 0 else 0
                ),
            },
            "test_results": self.test_results,
            "app_analysis": {
                "interfaces": ["CLI", "API", "Library"],
                "operations": self._extract_operations_from_results(),
                "permissions": ["test:read", "test:write", "test:execute"],
            },
            "scenarios": [],  # Could be populated from test outputs
            "personas": {},  # Could be populated from test outputs
            "llm_analysis_history": [],  # Placeholder for future LLM analysis
        }

        # Save JSON report
        json_report_path = get_results_path("test_suite_results.json")
        with open(json_report_path, "w") as f:
            json.dump(report_data, f, indent=2)

        # Generate HTML report
        html_report_path = get_results_path("test_suite_report.html")
        self.report_generator.generate_comprehensive_report(
            report_data, html_report_path
        )

        # Print summary
        print("\n✅ Test Execution Complete!")
        print(f"   • Total Tests: {total_tests}")
        print(f"   • Passed: {passed_tests} ({passed_tests/total_tests*100:.1f}%)")
        print(f"   • Failed: {failed_tests}")
        print(f"   • Timeouts: {timeout_tests}")
        print(f"   • Errors: {error_tests}")
        print(f"   • Duration: {total_duration:.2f}s")

        print("\n📄 Reports generated:")
        print(f"   • JSON: {json_report_path}")
        print(f"   • HTML: {html_report_path}")

        return passed_tests == total_tests

    def _extract_operations_from_results(self) -> List[Dict[str, str]]:
        """Extract operations from test results."""
        operations = []

        # Parse test outputs to find operations
        for result in self.test_results:
            if "Testing" in result.get("stdout", ""):
                # Basic operation extraction
                if "Models" in result["stdout"]:
                    operations.append({"name": "test_models", "type": "validate"})
                if "Database" in result["stdout"]:
                    operations.append({"name": "test_database", "type": "validate"})
                if "Personas" in result["stdout"]:
                    operations.append({"name": "test_personas", "type": "validate"})
                if "Scenarios" in result["stdout"]:
                    operations.append({"name": "test_scenarios", "type": "validate"})

        return operations


async def main():
    """Main entry point."""
    runner = TestRunner()
    success = await runner.run_all_tests()

    # Exit with appropriate code
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    asyncio.run(main())
