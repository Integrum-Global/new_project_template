"""
Unit tests for Nexus monitoring metrics components.
Tests individual components in isolation with mocking.
"""

import time
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
import pytest_asyncio

# Import the modules under test - paths handled by conftest.py
from nexus.monitoring.metrics import HealthMonitor, MetricsCollector, MetricsMiddleware


class TestMetricsCollector:
    """Unit tests for MetricsCollector class."""

    def test_init_without_prometheus(self):
        """Test MetricsCollector initialization when Prometheus is not available."""
        # Test with Prometheus disabled
        collector = MetricsCollector(enable_prometheus=False)

        assert collector.enable_prometheus is False
        assert collector.metrics_port == 9090
        assert collector._metrics == {}
        assert collector._start_time > 0

    @patch("nexus.monitoring.metrics.PROMETHEUS_AVAILABLE", True)
    @patch("nexus.monitoring.metrics.Counter")
    @patch("nexus.monitoring.metrics.Histogram")
    @patch("nexus.monitoring.metrics.Gauge")
    @patch("nexus.monitoring.metrics.Info")
    def test_init_with_prometheus(
        self, mock_info, mock_gauge, mock_histogram, mock_counter
    ):
        """Test MetricsCollector initialization when Prometheus is available."""
        collector = MetricsCollector(enable_prometheus=True, metrics_port=9091)

        assert collector.enable_prometheus is True
        assert collector.metrics_port == 9091

        # Verify that Prometheus metrics were initialized
        mock_counter.assert_called()
        mock_histogram.assert_called()
        mock_gauge.assert_called()
        mock_info.assert_called()

    @patch("nexus.monitoring.metrics.PROMETHEUS_AVAILABLE", True)
    @patch("nexus.monitoring.metrics.start_http_server")
    @pytest.mark.asyncio
    async def test_start_metrics_server_success(self, mock_start_server):
        """Test successful metrics server startup."""
        collector = MetricsCollector(enable_prometheus=True)

        await collector.start_metrics_server()

        mock_start_server.assert_called_once_with(9090)

    @patch("nexus.monitoring.metrics.PROMETHEUS_AVAILABLE", True)
    @patch(
        "nexus.monitoring.metrics.start_http_server",
        side_effect=Exception("Port in use"),
    )
    @patch(
        "nexus.monitoring.metrics.REGISTRY", create=True
    )  # Mock the registry to avoid conflicts
    @pytest.mark.asyncio
    async def test_start_metrics_server_failure(self, mock_registry, mock_start_server):
        """Test metrics server startup failure handling."""
        with (
            patch("nexus.monitoring.metrics.Counter"),
            patch("nexus.monitoring.metrics.Histogram"),
            patch("nexus.monitoring.metrics.Gauge"),
            patch("nexus.monitoring.metrics.Info"),
        ):

            collector = MetricsCollector(enable_prometheus=True)

            # Should not raise exception, just log error
            await collector.start_metrics_server()

            mock_start_server.assert_called_once_with(9090)

    def test_record_channel_request_without_prometheus(self):
        """Test recording channel request metrics when Prometheus is disabled."""
        collector = MetricsCollector(enable_prometheus=False)

        # Should not raise any exceptions
        collector.record_channel_request("api", "GET", "success", 0.123)

        # No metrics should be recorded
        assert collector._metrics == {}

    @patch("nexus.monitoring.metrics.PROMETHEUS_AVAILABLE", True)
    def test_record_channel_request_with_prometheus(self):
        """Test recording channel request metrics when Prometheus is enabled."""
        with (
            patch("nexus.monitoring.metrics.Counter") as mock_counter,
            patch("nexus.monitoring.metrics.Histogram") as mock_histogram,
            patch("nexus.monitoring.metrics.Gauge"),
            patch("nexus.monitoring.metrics.Info"),
        ):

            # Setup mocks
            mock_counter_instance = MagicMock()
            mock_histogram_instance = MagicMock()
            mock_counter.return_value = mock_counter_instance
            mock_histogram.return_value = mock_histogram_instance

            collector = MetricsCollector(enable_prometheus=True)
            collector.record_channel_request("api", "GET", "success", 0.123)

            # Verify metrics were recorded
            mock_counter_instance.labels.assert_called_with(
                channel="api", method="GET", status="success"
            )
            mock_histogram_instance.labels.assert_called_with(
                channel="api", endpoint="GET"
            )

    def test_record_workflow_execution(self):
        """Test recording workflow execution metrics."""
        collector = MetricsCollector(enable_prometheus=False)

        # Should not raise exceptions
        collector.record_workflow_execution("test-workflow", "success", "api", 1.5)

    def test_update_active_sessions(self):
        """Test updating active sessions count."""
        collector = MetricsCollector(enable_prometheus=False)

        # Should not raise exceptions
        collector.update_active_sessions("api", 25)

    def test_record_session_duration(self):
        """Test recording session duration."""
        collector = MetricsCollector(enable_prometheus=False)

        # Should not raise exceptions
        collector.record_session_duration("cli", 300.0)

    def test_record_tenant_operation(self):
        """Test recording tenant operation."""
        collector = MetricsCollector(enable_prometheus=False)

        # Should not raise exceptions
        collector.record_tenant_operation("tenant-123", "create_user", "success")

    def test_record_marketplace_operation(self):
        """Test recording marketplace operation."""
        collector = MetricsCollector(enable_prometheus=False)

        # Should not raise exceptions
        collector.record_marketplace_operation("search", "success")

    def test_update_resource_metrics(self):
        """Test updating resource metrics."""
        collector = MetricsCollector(enable_prometheus=False)

        # Should not raise exceptions
        collector.update_resource_metrics(
            512 * 1024 * 1024, 10
        )  # 512MB, 10 connections

    def test_record_error(self):
        """Test recording error metrics."""
        collector = MetricsCollector(enable_prometheus=False)

        # Should not raise exceptions
        collector.record_error("database", "connection_error", "critical")

    @patch("nexus.monitoring.metrics.PROMETHEUS_AVAILABLE", True)
    def test_set_app_info(self):
        """Test setting application information."""
        with (
            patch("nexus.monitoring.metrics.Info") as mock_info,
            patch("nexus.monitoring.metrics.Counter"),
            patch("nexus.monitoring.metrics.Histogram"),
            patch("nexus.monitoring.metrics.Gauge"),
        ):

            mock_info_instance = MagicMock()
            mock_info.return_value = mock_info_instance

            collector = MetricsCollector(enable_prometheus=True)
            collector.set_app_info("1.0.0", "production")

            # Verify app info was set
            mock_info_instance.info.assert_called_once()
            call_args = mock_info_instance.info.call_args[0][0]
            assert call_args["version"] == "1.0.0"
            assert call_args["environment"] == "production"
            assert "start_time" in call_args

    def test_get_metrics_summary(self):
        """Test getting metrics summary."""
        collector = MetricsCollector(enable_prometheus=False)

        summary = collector.get_metrics_summary()

        assert isinstance(summary, dict)
        assert "uptime_seconds" in summary
        assert "metrics_enabled" in summary
        assert "prometheus_available" in summary
        assert "start_time" in summary
        assert summary["metrics_enabled"] is False
        assert summary["metrics_port"] is None


class TestHealthMonitor:
    """Unit tests for HealthMonitor class."""

    def test_init_without_metrics(self):
        """Test HealthMonitor initialization without metrics collector."""
        monitor = HealthMonitor()

        assert monitor.metrics is None
        assert monitor._health_checks == {}
        assert monitor._last_health_check is None

    def test_init_with_metrics(self):
        """Test HealthMonitor initialization with metrics collector."""
        metrics = MagicMock()
        monitor = HealthMonitor(metrics)

        assert monitor.metrics is metrics
        assert monitor._health_checks == {}
        assert monitor._last_health_check is None

    def test_register_health_check(self):
        """Test registering a health check function."""
        monitor = HealthMonitor()
        check_func = AsyncMock()

        monitor.register_health_check("test_check", check_func, 30)

        assert "test_check" in monitor._health_checks
        check_config = monitor._health_checks["test_check"]
        assert check_config["func"] is check_func
        assert check_config["interval"] == 30
        assert check_config["last_run"] is None
        assert check_config["last_result"] is None

    @pytest.mark.asyncio
    async def test_run_health_checks_success(self):
        """Test running health checks with successful results."""
        monitor = HealthMonitor()

        # Mock health check function
        async def mock_health_check():
            return {"healthy": True, "details": "All good"}

        monitor.register_health_check("test_check", mock_health_check)

        results = await monitor.run_health_checks()

        assert results["status"] == "healthy"
        assert "test_check" in results["checks"]
        check_result = results["checks"]["test_check"]
        assert check_result["status"] == "healthy"
        assert check_result["details"]["healthy"] is True
        assert "last_checked" in check_result

    @pytest.mark.asyncio
    async def test_run_health_checks_failure(self):
        """Test running health checks with failing results."""
        monitor = HealthMonitor()

        # Mock failing health check function
        async def mock_health_check():
            return {"healthy": False, "error": "Service down"}

        monitor.register_health_check("test_check", mock_health_check)

        results = await monitor.run_health_checks()

        assert results["status"] == "unhealthy"
        assert "test_check" in results["checks"]
        check_result = results["checks"]["test_check"]
        assert check_result["status"] == "unhealthy"

    @pytest.mark.asyncio
    async def test_run_health_checks_exception(self):
        """Test running health checks with exception handling."""
        metrics = MagicMock()
        monitor = HealthMonitor(metrics)

        # Mock health check function that raises exception
        async def mock_health_check():
            raise Exception("Connection failed")

        monitor.register_health_check("test_check", mock_health_check)

        results = await monitor.run_health_checks()

        assert results["status"] == "unhealthy"
        assert "test_check" in results["checks"]
        check_result = results["checks"]["test_check"]
        assert check_result["status"] == "error"
        assert "Connection failed" in check_result["error"]

        # Verify error was recorded in metrics
        metrics.record_error.assert_called_once_with(
            "health_monitor", "health_check_failed"
        )

    @pytest.mark.asyncio
    async def test_get_health_status_first_time(self):
        """Test getting health status when no previous check exists."""
        monitor = HealthMonitor()

        # Mock health check function
        async def mock_health_check():
            return {"healthy": True}

        monitor.register_health_check("test_check", mock_health_check)

        status = await monitor.get_health_status()

        assert status["status"] == "healthy"
        assert "test_check" in status["checks"]

    @pytest.mark.asyncio
    async def test_get_health_status_cached(self):
        """Test getting health status returns cached result."""
        monitor = HealthMonitor()

        # Set a cached result
        cached_result = {
            "status": "healthy",
            "checks": {"test": {"status": "healthy"}},
            "timestamp": datetime.now().isoformat(),
        }
        monitor._last_health_check = cached_result

        status = await monitor.get_health_status()

        assert status is cached_result


class TestMetricsMiddleware:
    """Unit tests for MetricsMiddleware class."""

    def test_init(self):
        """Test MetricsMiddleware initialization."""
        metrics = MagicMock()
        middleware = MetricsMiddleware(metrics, "api")

        assert middleware.metrics is metrics
        assert middleware.channel_name == "api"

    @pytest.mark.asyncio
    async def test_middleware_success(self):
        """Test middleware handling successful request."""
        metrics = MagicMock()
        middleware = MetricsMiddleware(metrics, "api")

        # Mock request and response
        mock_request = MagicMock()
        mock_request.method = "GET"

        mock_response = MagicMock()
        mock_response.status_code = 200

        async def mock_call_next(request):
            return mock_response

        result = await middleware(mock_request, mock_call_next)

        assert result is mock_response

        # Verify metrics were recorded
        metrics.record_channel_request.assert_called_once()
        args = metrics.record_channel_request.call_args[0]
        assert args[0] == "api"  # channel
        assert args[1] == "GET"  # method
        assert args[2] == "success"  # status
        assert isinstance(args[3], float)  # duration

    @pytest.mark.asyncio
    async def test_middleware_error_response(self):
        """Test middleware handling error response."""
        metrics = MagicMock()
        middleware = MetricsMiddleware(metrics, "api")

        # Mock request and error response
        mock_request = MagicMock()
        mock_request.method = "POST"

        mock_response = MagicMock()
        mock_response.status_code = 500

        async def mock_call_next(request):
            return mock_response

        result = await middleware(mock_request, mock_call_next)

        assert result is mock_response

        # Verify error status was recorded
        args = metrics.record_channel_request.call_args[0]
        assert args[2] == "error"  # status

    @pytest.mark.asyncio
    async def test_middleware_exception(self):
        """Test middleware handling exception during request processing."""
        metrics = MagicMock()
        middleware = MetricsMiddleware(metrics, "api")

        # Mock request
        mock_request = MagicMock()
        mock_request.method = "PUT"

        # Mock call_next that raises exception
        async def mock_call_next(request):
            raise ValueError("Processing failed")

        with pytest.raises(ValueError, match="Processing failed"):
            await middleware(mock_request, mock_call_next)

        # Verify error was recorded
        metrics.record_error.assert_called_once_with("api_channel", "ValueError")

        # Verify request metrics were still recorded
        metrics.record_channel_request.assert_called_once()
        args = metrics.record_channel_request.call_args[0]
        assert args[2] == "error"  # status

    @pytest.mark.asyncio
    async def test_middleware_no_method_attribute(self):
        """Test middleware handling request without method attribute."""
        metrics = MagicMock()
        middleware = MetricsMiddleware(metrics, "cli")

        # Mock request without method attribute
        mock_request = MagicMock(spec=[])  # No method attribute

        mock_response = MagicMock()
        mock_response.status_code = 200

        async def mock_call_next(request):
            return mock_response

        result = await middleware(mock_request, mock_call_next)

        assert result is mock_response

        # Verify 'unknown' was used as method
        args = metrics.record_channel_request.call_args[0]
        assert args[1] == "unknown"  # method

    @pytest.mark.asyncio
    async def test_middleware_no_status_code(self):
        """Test middleware handling response without status_code attribute."""
        metrics = MagicMock()
        middleware = MetricsMiddleware(metrics, "mcp")

        # Mock request and response without status_code
        mock_request = MagicMock()
        mock_request.method = "GET"

        mock_response = MagicMock(spec=[])  # No status_code attribute

        async def mock_call_next(request):
            return mock_response

        result = await middleware(mock_request, mock_call_next)

        assert result is mock_response

        # Verify success status was assumed
        args = metrics.record_channel_request.call_args[0]
        assert args[2] == "success"  # status


# Integration with pytest markers
pytestmark = pytest.mark.unit
