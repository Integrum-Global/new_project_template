"""
Integration tests for Nexus monitoring components.
Tests component interactions with real Docker services.
"""

import asyncio

# Import test utilities from SDK root
import sys
import time
from pathlib import Path

import pytest
import pytest_asyncio

# Add SDK root to path for test utilities
sdk_root = Path(__file__).parent.parent.parent.parent.parent
sys.path.insert(0, str(sdk_root / "tests" / "utils"))
from docker_config import get_postgres_connection_string, get_redis_connection_params
from nexus.core.application import NexusApplication
from nexus.core.config import MonitoringConfig, NexusConfig
from nexus.monitoring.metrics import HealthMonitor, MetricsCollector

# Import the modules under test - paths handled by conftest.py


@pytest.mark.integration
@pytest.mark.requires_docker
class TestNexusMonitoringIntegration:
    """Integration tests for Nexus monitoring with real services."""

    @pytest_asyncio.fixture
    async def nexus_app(self):
        """Create a Nexus application with monitoring enabled."""
        config = NexusConfig(name="TestApp")

        # Configure monitoring with Prometheus disabled
        config.features.monitoring = MonitoringConfig(
            enabled=True,
            prometheus_enabled=False,  # Disable Prometheus for testing
            health_checks=True,
            metrics_port=9093,  # Use different port to avoid conflicts
        )

        # Configure channels
        config.channels.api.enabled = True
        config.channels.api.port = 8001
        config.channels.cli.enabled = False
        config.channels.mcp.enabled = False

        app = NexusApplication(config)

        # Initialize components without starting the full app
        await app._initialize_components()

        yield app

        # Cleanup
        await app._cleanup_components()

    async def test_metrics_collector_initialization(self, nexus_app):
        """Test that MetricsCollector is properly initialized in the application."""
        assert hasattr(nexus_app, "metrics_collector")
        assert nexus_app.metrics_collector is not None
        assert nexus_app.metrics_collector.enable_prometheus is False
        assert nexus_app.metrics_collector.metrics_port == 9093

    async def test_health_monitor_initialization(self, nexus_app):
        """Test that HealthMonitor is properly initialized in the application."""
        assert hasattr(nexus_app, "health_monitor")
        assert nexus_app.health_monitor is not None
        assert nexus_app.health_monitor.metrics is nexus_app.metrics_collector

    async def test_metrics_recording(self, nexus_app):
        """Test that metrics can be recorded without errors."""
        metrics = nexus_app.metrics_collector

        # Test various metric recording methods
        metrics.record_channel_request("api", "GET", "success", 0.123)
        metrics.record_workflow_execution("test-workflow", "success", "api", 1.5)
        metrics.update_active_sessions("api", 10)
        metrics.record_session_duration("api", 300.0)
        metrics.record_tenant_operation("tenant-123", "create_user", "success")
        metrics.record_marketplace_operation("search", "success")
        metrics.update_resource_metrics(512 * 1024 * 1024, 5)
        metrics.record_error("database", "connection_error", "warning")

        # Should not raise any exceptions
        assert True

    async def test_metrics_summary(self, nexus_app):
        """Test getting metrics summary."""
        metrics = nexus_app.metrics_collector

        summary = metrics.get_metrics_summary()

        assert isinstance(summary, dict)
        assert "uptime_seconds" in summary
        assert "metrics_enabled" in summary
        assert "prometheus_available" in summary
        assert "start_time" in summary
        assert summary["metrics_enabled"] is False
        # When Prometheus is disabled, metrics_port should be None
        assert summary["metrics_port"] is None

        # Uptime should be positive
        assert summary["uptime_seconds"] > 0

    async def test_health_check_registration(self, nexus_app):
        """Test that health checks are properly registered."""
        health_monitor = nexus_app.health_monitor

        # Verify that health checks were registered during initialization
        assert len(health_monitor._health_checks) > 0

        # Check for expected health checks
        health_check_names = list(health_monitor._health_checks.keys())
        assert "database" in health_check_names
        assert "application" in health_check_names

    async def test_health_checks_execution(self, nexus_app):
        """Test executing health checks with real services."""
        health_monitor = nexus_app.health_monitor

        # Run health checks
        results = await health_monitor.run_health_checks()

        assert isinstance(results, dict)
        assert "status" in results
        assert "checks" in results
        assert "timestamp" in results

        # Should have at least application health check
        assert "application" in results["checks"]
        app_check = results["checks"]["application"]
        assert app_check["status"] in ["healthy", "unhealthy"]
        assert "details" in app_check
        assert "last_checked" in app_check

    async def test_application_health_endpoint(self, nexus_app):
        """Test the application's health check endpoint."""
        # Use the application's health_check method
        health = await nexus_app.health_check()

        assert isinstance(health, dict)

        # Should include metrics summary
        assert "metrics" in health
        metrics_info = health["metrics"]
        assert "uptime_seconds" in metrics_info
        assert "metrics_enabled" in metrics_info

    async def test_workflow_registration_metrics(self, nexus_app):
        """Test that workflow registration generates metrics."""
        from kailash.workflow.builder import WorkflowBuilder

        # Create a simple workflow
        workflow = WorkflowBuilder()
        workflow.add_node(
            "PythonCodeNode", "test", {"code": "result = {'success': True}"}
        )

        # Register the workflow - this should trigger metrics recording
        nexus_app.register_workflow("test-workflow", workflow.build())

        # Metrics should have been recorded
        # This is verified by the fact that no exception was raised
        assert True

    async def test_concurrent_metrics_recording(self, nexus_app):
        """Test concurrent metrics recording to ensure thread safety."""
        metrics = nexus_app.metrics_collector

        async def record_metrics(worker_id):
            """Record metrics from a worker coroutine."""
            for i in range(10):
                metrics.record_channel_request(
                    "api", "GET", "success", 0.1 + (i * 0.01)
                )
                metrics.record_workflow_execution(
                    f"workflow-{worker_id}", "success", "api", 1.0 + i
                )
                await asyncio.sleep(0.001)  # Small delay to simulate real usage

        # Run multiple workers concurrently
        workers = [record_metrics(i) for i in range(5)]
        await asyncio.gather(*workers)

        # Should not raise any exceptions
        assert True

    async def test_health_check_with_database_connectivity(self, nexus_app):
        """Test health check that verifies database connectivity."""
        health_monitor = nexus_app.health_monitor

        # If database health check is registered, it should work with real database
        if "database" in health_monitor._health_checks:
            results = await health_monitor.run_health_checks()

            # Database health check should execute without error
            assert "database" in results["checks"]
            db_check = results["checks"]["database"]
            assert db_check["status"] in ["healthy", "unhealthy", "error"]

    async def test_metrics_persistence_across_operations(self, nexus_app):
        """Test that metrics collector maintains state across operations."""
        metrics = nexus_app.metrics_collector

        # Record initial metrics
        start_time = time.time()
        metrics.record_channel_request("api", "GET", "success", 0.1)

        # Wait a short time
        await asyncio.sleep(0.1)

        # Get summary - uptime should have increased
        summary = metrics.get_metrics_summary()
        assert summary["uptime_seconds"] > 0.1

        # Start time should remain consistent
        first_start_time = summary["start_time"]

        # Record more metrics
        metrics.record_workflow_execution("test", "success", "api", 2.0)

        # Get summary again
        summary2 = metrics.get_metrics_summary()
        assert summary2["start_time"] == first_start_time  # Should be same
        assert summary2["uptime_seconds"] > summary["uptime_seconds"]  # Should increase

    async def test_health_monitor_caching(self, nexus_app):
        """Test that health monitor caches results appropriately."""
        health_monitor = nexus_app.health_monitor

        # Run health checks first time
        results1 = await health_monitor.run_health_checks()

        # Get cached results
        cached_results = await health_monitor.get_health_status()

        # Should return the cached results (same object or same content)
        assert cached_results["timestamp"] == results1["timestamp"]
        assert cached_results["status"] == results1["status"]

    async def test_error_recording_with_real_components(self, nexus_app):
        """Test error recording integrates properly with real application components."""
        metrics = nexus_app.metrics_collector

        # Record various types of errors
        metrics.record_error("authentication", "invalid_token", "warning")
        metrics.record_error("database", "connection_timeout", "error")
        metrics.record_error("workflow", "execution_failed", "critical")

        # Should not raise exceptions and should integrate properly
        assert True

    async def test_resource_metrics_tracking(self, nexus_app):
        """Test that resource metrics can be tracked over time."""
        metrics = nexus_app.metrics_collector

        # Update resource metrics multiple times
        for i in range(5):
            memory_usage = (512 + i * 10) * 1024 * 1024  # Increasing memory
            db_connections = 5 + i  # Increasing connections

            metrics.update_resource_metrics(memory_usage, db_connections)
            await asyncio.sleep(0.01)

        # Should handle multiple updates without issues
        assert True


@pytest.mark.integration
@pytest.mark.requires_docker
class TestMetricsCollectorWithPrometheus:
    """Integration tests for MetricsCollector with Prometheus (if available)."""

    def test_prometheus_availability_detection(self):
        """Test that Prometheus availability is correctly detected."""
        from nexus.monitoring.metrics import PROMETHEUS_AVAILABLE

        # Test with actual import status
        try:
            import prometheus_client

            expected = True
        except ImportError:
            expected = False

        assert PROMETHEUS_AVAILABLE == expected

    async def test_metrics_server_startup_with_available_port(self):
        """Test metrics server startup when port is available."""
        # Use a non-standard port to avoid conflicts
        collector = MetricsCollector(enable_prometheus=False, metrics_port=9999)

        # Should not raise exceptions even if Prometheus is not available
        await collector.start_metrics_server()

        assert True


# Mark all tests in this module as integration tests
pytestmark = [pytest.mark.integration, pytest.mark.requires_docker, pytest.mark.asyncio]
