"""
Test Runner for User Management System
Executes all tests in live Docker environment
"""

import os
import subprocess
import sys
import time
from pathlib import Path


def check_docker_running():
    """Check if Docker is running"""
    try:
        result = subprocess.run(
            ["docker", "info"], capture_output=True, text=True, check=True
        )
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("❌ Docker is not running or not installed")
        return False


def start_services():
    """Start all required services using docker-compose"""
    print("🚀 Starting services...")

    try:
        # Build images
        subprocess.run(["docker-compose", "build"], check=True)

        # Start services
        subprocess.run(["docker-compose", "up", "-d"], check=True)

        # Wait for services to be healthy
        print("⏳ Waiting for services to be healthy...")
        time.sleep(10)

        # Check health
        result = subprocess.run(
            ["docker-compose", "ps"], capture_output=True, text=True
        )

        print(result.stdout)
        return True

    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to start services: {e}")
        return False


def run_unit_tests():
    """Run unit tests"""
    print("\n📋 Running Unit Tests...")

    try:
        result = subprocess.run(
            [
                "docker-compose",
                "exec",
                "-T",
                "user_management",
                "pytest",
                "-v",
                "apps/user_management/tests/unit/",
                "--junitxml=/test_results/unit_tests.xml",
            ],
            capture_output=True,
            text=True,
        )

        print(result.stdout)
        if result.stderr:
            print("Errors:", result.stderr)

        return result.returncode == 0

    except subprocess.CalledProcessError as e:
        print(f"❌ Unit tests failed: {e}")
        return False


def run_integration_tests():
    """Run integration tests"""
    print("\n🔗 Running Integration Tests...")

    try:
        result = subprocess.run(
            [
                "docker-compose",
                "exec",
                "-T",
                "user_management",
                "pytest",
                "-v",
                "apps/user_management/tests/integration/",
                "--junitxml=/test_results/integration_tests.xml",
            ],
            capture_output=True,
            text=True,
        )

        print(result.stdout)
        if result.stderr:
            print("Errors:", result.stderr)

        return result.returncode == 0

    except subprocess.CalledProcessError as e:
        print(f"❌ Integration tests failed: {e}")
        return False


def run_user_flow_tests():
    """Run user flow tests"""
    print("\n👤 Running User Flow Tests...")

    try:
        result = subprocess.run(
            [
                "docker-compose",
                "exec",
                "-T",
                "user_management",
                "pytest",
                "-v",
                "apps/user_management/tests/user_flows/",
                "--junitxml=/test_results/user_flow_tests.xml",
            ],
            capture_output=True,
            text=True,
        )

        print(result.stdout)
        if result.stderr:
            print("Errors:", result.stderr)

        return result.returncode == 0

    except subprocess.CalledProcessError as e:
        print(f"❌ User flow tests failed: {e}")
        return False


def run_performance_tests():
    """Run performance tests"""
    print("\n⚡ Running Performance Tests...")

    try:
        result = subprocess.run(
            [
                "docker-compose",
                "exec",
                "-T",
                "user_management",
                "pytest",
                "-v",
                "apps/user_management/tests/test_performance_load.py",
                "--junitxml=/test_results/performance_tests.xml",
            ],
            capture_output=True,
            text=True,
        )

        print(result.stdout)
        if result.stderr:
            print("Errors:", result.stderr)

        return result.returncode == 0

    except subprocess.CalledProcessError as e:
        print(f"❌ Performance tests failed: {e}")
        return False


def run_security_tests():
    """Run security tests"""
    print("\n🔒 Running Security Tests...")

    try:
        result = subprocess.run(
            [
                "docker-compose",
                "exec",
                "-T",
                "user_management",
                "pytest",
                "-v",
                "apps/user_management/tests/test_security_vulnerabilities.py",
                "--junitxml=/test_results/security_tests.xml",
            ],
            capture_output=True,
            text=True,
        )

        print(result.stdout)
        if result.stderr:
            print("Errors:", result.stderr)

        return result.returncode == 0

    except subprocess.CalledProcessError as e:
        print(f"❌ Security tests failed: {e}")
        return False


def generate_coverage_report():
    """Generate test coverage report"""
    print("\n📊 Generating Coverage Report...")

    try:
        subprocess.run(
            [
                "docker-compose",
                "exec",
                "-T",
                "user_management",
                "pytest",
                "--cov=apps.user_management",
                "--cov-report=html:/test_results/coverage",
                "--cov-report=term",
                "apps/user_management/tests/",
            ],
            check=True,
        )

        print("✅ Coverage report generated in test_results/coverage/")
        return True

    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to generate coverage report: {e}")
        return False


def stop_services():
    """Stop all services"""
    print("\n🛑 Stopping services...")

    try:
        subprocess.run(["docker-compose", "down"], check=True)
        return True

    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to stop services: {e}")
        return False


def main():
    """Main test runner"""
    print("🧪 User Management System - Test Runner")
    print("=" * 50)

    # Check prerequisites
    if not check_docker_running():
        sys.exit(1)

    # Change to app directory
    app_dir = Path(__file__).parent
    os.chdir(app_dir)

    # Start services
    if not start_services():
        sys.exit(1)

    # Run all test suites
    test_results = {
        "unit": run_unit_tests(),
        "integration": run_integration_tests(),
        "user_flows": run_user_flow_tests(),
        "performance": run_performance_tests(),
        "security": run_security_tests(),
    }

    # Generate coverage report
    generate_coverage_report()

    # Summary
    print("\n" + "=" * 50)
    print("📋 Test Summary:")
    print("=" * 50)

    total_passed = 0
    for test_type, passed in test_results.items():
        status = "✅ PASSED" if passed else "❌ FAILED"
        print(f"{test_type.title():<15} {status}")
        if passed:
            total_passed += 1

    print("=" * 50)
    print(f"Total: {total_passed}/{len(test_results)} test suites passed")

    # Stop services
    stop_services()

    # Exit with appropriate code
    if total_passed == len(test_results):
        print("\n🎉 All tests passed!")
        sys.exit(0)
    else:
        print("\n❌ Some tests failed!")
        sys.exit(1)


if __name__ == "__main__":
    main()
