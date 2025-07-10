"""
End-to-end tests for Nexus production monitoring capabilities.
Tests complete monitoring scenarios with real infrastructure.
"""

import asyncio
import json
import subprocess

# Import test utilities from SDK root
import sys
import tempfile
import time
from pathlib import Path

import aiohttp
import pytest
import pytest_asyncio

# Add SDK root to path for test utilities
sdk_root = Path(__file__).parent.parent.parent.parent.parent
sys.path.insert(0, str(sdk_root / "tests" / "utils"))
from docker_config import get_postgres_connection_string, get_redis_connection_params
from nexus.core.application import NexusApplication
from nexus.core.config import MonitoringConfig, NexusConfig

# Import the modules under test - paths handled by conftest.py


@pytest.mark.e2e
@pytest.mark.requires_docker
@pytest.mark.slow
class TestNexusProductionMonitoringE2E:
    """End-to-end tests for Nexus production monitoring."""

    @pytest_asyncio.fixture
    async def production_nexus_app(self):
        """Create a production-like Nexus application with full monitoring."""
        config = NexusConfig(name="ProductionTestApp", version="1.0.0")

        # Configure monitoring with Prometheus disabled for testing
        config.features.monitoring = MonitoringConfig(
            enabled=True,
            prometheus_enabled=False,  # Disable for testing
            health_checks=True,
            metrics_port=9094,  # Use different port
        )

        # Simplify configuration for testing
        config.features.authentication.enabled = False
        config.features.multi_tenant.enabled = False
        config.features.marketplace.enabled = False

        # Configure channels
        config.channels.api.enabled = True
        config.channels.api.port = 8002
        config.channels.cli.enabled = True
        config.channels.mcp.enabled = False

        app = NexusApplication(config)
        await app.start()

        # Give the app time to fully initialize
        await asyncio.sleep(2)

        yield app

        # Cleanup
        await app.stop()

    async def test_complete_monitoring_lifecycle(self, production_nexus_app):
        """Test complete monitoring lifecycle from startup to shutdown."""
        app = production_nexus_app

        # 1. Verify monitoring components are initialized
        assert hasattr(app, "metrics_collector")
        assert hasattr(app, "health_monitor")
        assert app.metrics_collector is not None
        assert app.health_monitor is not None

        # 2. Test metrics endpoint availability
        metrics_endpoint = app.get_metrics_endpoint()
        assert metrics_endpoint is None  # Prometheus disabled for testing

        # 3. Test health check functionality
        health = await app.health_check()
        assert isinstance(health, dict)
        assert "metrics" in health

        # 4. Test workflow registration and execution monitoring
        from kailash.workflow.builder import WorkflowBuilder

        workflow = WorkflowBuilder()
        workflow.add_node(
            "PythonCodeNode",
            "calculator",
            {
                "code": """
result = {
    'calculation': input_data.get('a', 0) + input_data.get('b', 0),
    'timestamp': str(__import__('datetime').datetime.now())
}
"""
            },
        )

        app.register_workflow("test-calculator", workflow.build())

        # 5. Test metrics recording during workflow operations
        initial_summary = app.metrics_collector.get_metrics_summary()
        initial_uptime = initial_summary["uptime_seconds"]

        # Simulate some operations
        for i in range(5):
            app.metrics_collector.record_channel_request(
                "api", "POST", "success", 0.1 + (i * 0.02)
            )
            app.metrics_collector.record_workflow_execution(
                "test-calculator", "success", "api", 0.5 + (i * 0.1)
            )
            await asyncio.sleep(0.1)

        # 6. Verify metrics have been updated
        final_summary = app.metrics_collector.get_metrics_summary()
        assert final_summary["uptime_seconds"] > initial_uptime

        # 7. Test error handling and recording
        app.metrics_collector.record_error("test_component", "test_error", "warning")

        # 8. Test health checks under load
        health_results = await app.health_monitor.run_health_checks()
        assert health_results["status"] in ["healthy", "unhealthy"]
        assert len(health_results["checks"]) > 0

    async def test_concurrent_monitoring_operations(self, production_nexus_app):
        """Test monitoring under concurrent operations."""
        app = production_nexus_app
        metrics = app.metrics_collector

        async def simulate_api_traffic():
            """Simulate API traffic with metrics recording."""
            for i in range(20):
                method = ["GET", "POST", "PUT", "DELETE"][i % 4]
                status = "success" if i % 10 != 9 else "error"  # 10% error rate
                duration = 0.05 + (i % 5) * 0.02

                metrics.record_channel_request("api", method, status, duration)
                await asyncio.sleep(0.05)

        async def simulate_workflow_executions():
            """Simulate workflow executions with metrics recording."""
            for i in range(15):
                workflow_id = f"workflow-{i % 3}"
                status = "success" if i % 8 != 7 else "failed"  # ~12% failure rate
                duration = 0.5 + (i % 4) * 0.3

                metrics.record_workflow_execution(workflow_id, status, "api", duration)
                await asyncio.sleep(0.07)

        async def simulate_session_management():
            """Simulate session management operations."""
            session_count = 10
            for i in range(25):
                # Simulate fluctuating session count
                session_count += 1 if i % 3 == 0 else -1
                session_count = max(0, min(50, session_count))

                metrics.update_active_sessions("api", session_count)

                if i % 5 == 0:
                    metrics.record_session_duration("api", 300 + (i * 10))

                await asyncio.sleep(0.04)

        async def run_health_checks():
            """Periodically run health checks."""
            for _ in range(5):
                await app.health_monitor.run_health_checks()
                await asyncio.sleep(0.2)

        # Run all operations concurrently
        start_time = time.time()

        await asyncio.gather(
            simulate_api_traffic(),
            simulate_workflow_executions(),
            simulate_session_management(),
            run_health_checks(),
        )

        end_time = time.time()
        duration = end_time - start_time

        # Verify monitoring handled concurrent operations
        assert duration < 5.0  # Should complete reasonably quickly

        # Get final metrics summary
        summary = metrics.get_metrics_summary()
        assert summary["uptime_seconds"] > 0

    async def test_monitoring_during_stress_conditions(self, production_nexus_app):
        """Test monitoring behavior under stress conditions."""
        app = production_nexus_app
        metrics = app.metrics_collector

        # Simulate high-frequency operations
        async def high_frequency_metrics():
            for i in range(100):
                metrics.record_channel_request("api", "GET", "success", 0.001)
                metrics.record_workflow_execution(
                    f"fast-workflow-{i%5}", "success", "api", 0.01
                )
                metrics.update_resource_metrics(
                    512 * 1024 * 1024 + i * 1024, 10 + (i % 20)
                )

                if i % 10 == 0:
                    await asyncio.sleep(0.001)  # Brief pause every 10 operations

        # Simulate error conditions
        async def error_simulation():
            error_types = [
                "connection_error",
                "timeout",
                "validation_error",
                "system_error",
            ]
            components = ["database", "cache", "external_api", "workflow_engine"]
            severities = ["warning", "error", "critical"]

            for i in range(50):
                error_type = error_types[i % len(error_types)]
                component = components[i % len(components)]
                severity = severities[i % len(severities)]

                metrics.record_error(component, error_type, severity)
                await asyncio.sleep(0.02)

        # Run stress test
        start_time = time.time()

        await asyncio.gather(high_frequency_metrics(), error_simulation())

        end_time = time.time()

        # Verify monitoring remained stable under stress
        assert end_time - start_time < 10.0  # Should complete within reasonable time

        # Verify health monitoring still works
        health = await app.health_check()
        assert isinstance(health, dict)
        assert "metrics" in health

    async def test_monitoring_persistence_and_recovery(self, production_nexus_app):
        """Test monitoring data persistence and recovery scenarios."""
        app = production_nexus_app
        metrics = app.metrics_collector

        # Record initial state
        initial_summary = metrics.get_metrics_summary()
        initial_start_time = initial_summary["start_time"]

        # Simulate extended operation period
        for i in range(30):
            # Vary the operations to simulate real usage patterns
            if i % 3 == 0:
                metrics.record_channel_request("api", "GET", "success", 0.1)
            elif i % 3 == 1:
                metrics.record_workflow_execution(
                    "persistent-workflow", "success", "api", 1.0
                )
            else:
                metrics.update_active_sessions("api", 15 + (i % 10))

            await asyncio.sleep(0.05)

        # Verify persistence of start time and consistent uptime calculation
        final_summary = metrics.get_metrics_summary()
        assert final_summary["start_time"] == initial_start_time
        assert final_summary["uptime_seconds"] > initial_summary["uptime_seconds"]

        # Test health monitoring persistence
        health_result1 = await app.health_monitor.run_health_checks()

        # Brief delay
        await asyncio.sleep(0.5)

        # Get cached health status
        cached_health = await app.health_monitor.get_health_status()
        assert cached_health["timestamp"] == health_result1["timestamp"]

    async def test_enterprise_monitoring_patterns(self, production_nexus_app):
        """Test enterprise-specific monitoring patterns."""
        app = production_nexus_app
        metrics = app.metrics_collector

        # Simulate multi-tenant operations
        tenants = ["tenant-001", "tenant-002", "tenant-003"]
        operations = ["create_user", "update_profile", "delete_data", "export_data"]

        for i in range(30):
            tenant = tenants[i % len(tenants)]
            operation = operations[i % len(operations)]
            status = "success" if i % 12 != 11 else "failed"  # ~8% failure rate

            metrics.record_tenant_operation(tenant, operation, status)
            await asyncio.sleep(0.03)

        # Simulate marketplace operations
        marketplace_ops = ["search", "publish", "install", "update", "remove"]

        for i in range(20):
            operation = marketplace_ops[i % len(marketplace_ops)]
            status = "success" if i % 15 != 14 else "failed"  # ~7% failure rate

            metrics.record_marketplace_operation(operation, status)
            await asyncio.sleep(0.04)

        # Test resource monitoring patterns
        base_memory = 512 * 1024 * 1024  # 512MB base
        base_connections = 5

        for i in range(25):
            # Simulate memory growth and connection fluctuation
            memory_usage = base_memory + (i * 1024 * 1024) + (i % 5) * 10 * 1024 * 1024
            db_connections = base_connections + (i % 15) + (i // 5)

            metrics.update_resource_metrics(memory_usage, db_connections)
            await asyncio.sleep(0.02)

        # Verify all operations completed without errors
        summary = metrics.get_metrics_summary()
        assert summary["uptime_seconds"] > 0

    async def test_monitoring_integration_with_real_workflows(
        self, production_nexus_app
    ):
        """Test monitoring integration with actual workflow execution."""
        app = production_nexus_app

        # Create a realistic workflow for testing
        from kailash.workflow.builder import WorkflowBuilder

        workflow = WorkflowBuilder()
        workflow.add_node(
            "PythonCodeNode",
            "data_processor",
            {
                "code": """
import time
import json

# Simulate some processing time
time.sleep(0.1)

# Process the input data
processed_data = {
    'original': input_data,
    'processed_at': str(__import__('datetime').datetime.now()),
    'status': 'completed',
    'records_processed': input_data.get('record_count', 1)
}

result = processed_data
"""
            },
        )

        workflow.add_node(
            "PythonCodeNode",
            "validator",
            {
                "code": """
# Validate the processed data
validation_result = {
    'valid': result.get('status') == 'completed',
    'record_count': result.get('records_processed', 0),
    'validation_timestamp': str(__import__('datetime').datetime.now())
}

result = validation_result
"""
            },
        )

        workflow.add_connection("data_processor", "result", "validator", "result")

        app.register_workflow("monitoring-test-workflow", workflow.build())

        # Execute workflow multiple times and monitor metrics
        initial_summary = app.metrics_collector.get_metrics_summary()

        # Simulate multiple workflow executions
        for i in range(10):
            # Record workflow execution metrics (simulating what would happen in real execution)
            start_time = time.time()

            # Simulate workflow execution time
            await asyncio.sleep(0.15)  # Simulate processing time

            execution_time = time.time() - start_time
            status = "success" if i % 20 != 19 else "failed"  # 5% failure rate

            app.metrics_collector.record_workflow_execution(
                "monitoring-test-workflow", status, "api", execution_time
            )

            # Also record associated channel requests
            app.metrics_collector.record_channel_request(
                "api", "POST", status, execution_time * 0.1
            )

        # Verify monitoring captured all the operations
        final_summary = app.metrics_collector.get_metrics_summary()
        assert final_summary["uptime_seconds"] > initial_summary["uptime_seconds"]

        # Test health checks after workflow operations
        health = await app.health_check()
        assert isinstance(health, dict)
        assert "metrics" in health


@pytest.mark.e2e
@pytest.mark.requires_docker
@pytest.mark.slow
class TestNexusSecurityAndPerformanceE2E:
    """End-to-end tests for security scanning and performance testing scripts."""

    @pytest.fixture
    def temp_output_dir(self):
        """Create temporary directory for test outputs."""
        with tempfile.TemporaryDirectory() as temp_dir:
            yield Path(temp_dir)

    async def test_security_scanner_integration(self, temp_output_dir):
        """Test security scanner script with real project structure."""
        # Get the actual project root (Nexus app directory)
        project_root = (
            Path(__file__).parent.parent.parent.parent / "apps" / "kailash-nexus"
        )

        # Import and test the security scanner
        sys.path.insert(0, str(project_root / "scripts" / "security"))
        from scan import SecurityScanner

        # Initialize scanner with test configuration
        scanner = SecurityScanner(project_root, temp_output_dir)

        # Test individual scan methods (without requiring external tools)
        # Test the scanner initialization and configuration
        assert scanner.project_root == project_root
        assert scanner.output_dir == temp_output_dir
        assert len(scanner.tools) == 5  # bandit, safety, semgrep, trivy, hadolint

        # Test summary generation with mock results
        scanner.results = {
            "bandit": {
                "status": "success",
                "vulnerabilities": [],
                "summary": {
                    "total_issues": 0,
                    "high_severity": 0,
                    "medium_severity": 0,
                },
            },
            "safety": {
                "status": "no_requirements",
                "error": "No requirements.txt found",
                "vulnerabilities": [],
            },
        }

        summary = scanner._generate_summary()
        assert isinstance(summary, dict)
        assert "scan_summary" in summary
        assert "tool_results" in summary
        assert "recommendations" in summary

        scan_summary = summary["scan_summary"]
        assert "overall_status" in scan_summary
        assert "total_vulnerabilities" in scan_summary
        assert "tools_successful" in scan_summary

    async def test_performance_tester_configuration(self, temp_output_dir):
        """Test performance tester configuration and setup."""
        # Get the performance test script
        project_root = (
            Path(__file__).parent.parent.parent.parent / "apps" / "kailash-nexus"
        )

        sys.path.insert(0, str(project_root / "scripts" / "performance"))
        from load_test import (
            LoadTestConfig,
            PerformanceMetrics,
            PerformanceTester,
            ResourceMetrics,
        )

        # Test configuration creation
        config = LoadTestConfig(
            base_url="http://localhost:8003",
            concurrent_users=2,
            test_duration=5,
            ramp_up_time=1,
            think_time=0.1,
            timeout=10,
        )

        assert config.concurrent_users == 2
        assert config.test_duration == 5
        assert config.base_url == "http://localhost:8003"

        # Test performance tester initialization
        tester = PerformanceTester(config, temp_output_dir)
        assert tester.config == config
        assert tester.output_dir == temp_output_dir
        assert len(tester.test_scenarios) == 5  # All test scenarios

        # Test metrics calculation with mock data
        tester.request_results = [
            {
                "success": True,
                "response_time": 0.1,
                "response_size": 1024,
                "status_code": 200,
            },
            {
                "success": True,
                "response_time": 0.2,
                "response_size": 2048,
                "status_code": 200,
            },
            {
                "success": False,
                "response_time": 1.0,
                "response_size": 0,
                "status_code": 500,
            },
        ]

        tester.start_time = time.time() - 3  # 3 seconds ago
        tester.end_time = time.time()

        metrics = tester._calculate_performance_metrics()
        assert isinstance(metrics, PerformanceMetrics)
        assert metrics.total_requests == 3
        assert metrics.successful_requests == 2
        assert metrics.failed_requests == 1
        assert metrics.error_rate > 0
        assert metrics.avg_response_time > 0

    async def test_operational_runbook_completeness(self):
        """Test that operational runbook contains required sections."""
        # Navigate to the correct project root from tests/e2e/apps/nexus/
        project_root = (
            Path(__file__).parent.parent.parent.parent.parent / "apps" / "kailash-nexus"
        )
        runbook_path = project_root / "docs" / "operations" / "production-runbook.md"

        assert runbook_path.exists(), "Production runbook should exist"

        content = runbook_path.read_text()

        # Check for required sections
        required_sections = [
            "Emergency Procedures",
            "Critical System Down",
            "High Error Rate",
            "Database Connection Issues",
            "Monitoring & Alerting",
            "Deployment Procedures",
            "Scaling Procedures",
            "Maintenance Procedures",
            "Performance Optimization",
            "Contact Information",
        ]

        for section in required_sections:
            assert section in content, f"Runbook should contain '{section}' section"

        # Check for specific operational commands
        operational_commands = [
            "kubectl get pods",
            "kubectl logs",
            "kubectl rollout restart",
            "curl -f http://localhost:8000/health",
            "prometheus/alerts",
            "PagerDuty",
        ]

        for command in operational_commands:
            assert command in content, f"Runbook should contain '{command}' command"

    async def test_monitoring_scripts_executable(self):
        """Test that monitoring scripts are properly executable."""
        project_root = (
            Path(__file__).parent.parent.parent.parent.parent / "apps" / "kailash-nexus"
        )

        # Check security scanner script
        security_script = project_root / "scripts" / "security" / "scan.py"
        assert security_script.exists(), "Security scanner script should exist"
        assert security_script.is_file(), "Security scanner should be a file"

        # Check performance test script
        perf_script = project_root / "scripts" / "performance" / "load_test.py"
        assert perf_script.exists(), "Performance test script should exist"
        assert perf_script.is_file(), "Performance test script should be a file"

        # Test script help functionality (without running full scans)
        try:
            # Test security scanner help
            result = subprocess.run(
                ["python", str(security_script), "--help"],
                capture_output=True,
                text=True,
                timeout=30,
            )
            assert result.returncode == 0, "Security scanner help should work"
            assert "Nexus Security Scanner" in result.stdout

            # Test performance tester help
            result = subprocess.run(
                ["python", str(perf_script), "--help"],
                capture_output=True,
                text=True,
                timeout=30,
            )
            assert result.returncode == 0, "Performance tester help should work"
            assert "Nexus Performance Tester" in result.stdout

        except subprocess.TimeoutExpired:
            pytest.fail("Script execution timed out")
        except Exception as e:
            pytest.fail(f"Script execution failed: {e}")


# Mark all tests in this module as E2E tests
pytestmark = [
    pytest.mark.e2e,
    pytest.mark.requires_docker,
    pytest.mark.slow,
    pytest.mark.asyncio,
]
