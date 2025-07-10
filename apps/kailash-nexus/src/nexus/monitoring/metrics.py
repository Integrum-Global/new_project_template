"""
Production Metrics Integration for Nexus Application.

Provides comprehensive application-level metrics for Prometheus integration.
"""

import asyncio
import logging
import time
from datetime import datetime, timedelta
from typing import Any, Dict, Optional

try:
    from prometheus_client import (
        REGISTRY,
        CollectorRegistry,
        Counter,
        Gauge,
        Histogram,
        Info,
        start_http_server,
    )

    PROMETHEUS_AVAILABLE = True
except ImportError:
    PROMETHEUS_AVAILABLE = False

logger = logging.getLogger(__name__)


class MetricsCollector:
    """Production-grade metrics collector for Nexus application."""

    def __init__(self, enable_prometheus: bool = True, metrics_port: int = 9090):
        """Initialize metrics collector.

        Args:
            enable_prometheus: Enable Prometheus metrics export
            metrics_port: Port for Prometheus metrics endpoint
        """
        self.enable_prometheus = enable_prometheus and PROMETHEUS_AVAILABLE
        self.metrics_port = metrics_port
        self._metrics = {}
        self._start_time = time.time()

        if self.enable_prometheus:
            self._init_prometheus_metrics()
            logger.info(f"Prometheus metrics enabled on port {metrics_port}")
        else:
            logger.warning("Prometheus not available, using basic metrics")

    def _init_prometheus_metrics(self):
        """Initialize Prometheus metrics."""
        # Application metrics
        self._metrics["app_info"] = Info(
            "nexus_app_info",
            "Nexus application information",
            ["version", "environment", "start_time"],
        )

        # Channel metrics
        self._metrics["channel_requests_total"] = Counter(
            "nexus_channel_requests_total",
            "Total number of requests per channel",
            ["channel", "method", "status"],
        )

        self._metrics["channel_request_duration_seconds"] = Histogram(
            "nexus_channel_request_duration_seconds",
            "Channel request duration in seconds",
            ["channel", "endpoint"],
            buckets=[0.001, 0.01, 0.1, 0.5, 1.0, 2.5, 5.0, 10.0],
        )

        # Workflow metrics
        self._metrics["workflow_executions_total"] = Counter(
            "nexus_workflow_executions_total",
            "Total workflow executions",
            ["workflow_id", "status", "channel"],
        )

        self._metrics["workflow_execution_duration_seconds"] = Histogram(
            "nexus_workflow_execution_duration_seconds",
            "Workflow execution duration in seconds",
            ["workflow_id"],
            buckets=[0.1, 0.5, 1.0, 5.0, 10.0, 30.0, 60.0, 300.0],
        )

        # Session metrics
        self._metrics["active_sessions_total"] = Gauge(
            "nexus_active_sessions_total", "Number of active sessions", ["channel"]
        )

        self._metrics["session_duration_seconds"] = Histogram(
            "nexus_session_duration_seconds",
            "Session duration in seconds",
            ["channel"],
            buckets=[60, 300, 900, 1800, 3600, 7200, 14400],
        )

        # Enterprise metrics
        self._metrics["tenant_operations_total"] = Counter(
            "nexus_tenant_operations_total",
            "Total tenant operations",
            ["tenant_id", "operation", "status"],
        )

        self._metrics["marketplace_operations_total"] = Counter(
            "nexus_marketplace_operations_total",
            "Marketplace operations",
            ["operation", "status"],
        )

        # Resource metrics
        self._metrics["memory_usage_bytes"] = Gauge(
            "nexus_memory_usage_bytes", "Memory usage in bytes"
        )

        self._metrics["database_connections_active"] = Gauge(
            "nexus_database_connections_active", "Active database connections"
        )

        # Error metrics
        self._metrics["errors_total"] = Counter(
            "nexus_errors_total",
            "Total application errors",
            ["component", "error_type", "severity"],
        )

    async def start_metrics_server(self):
        """Start Prometheus metrics server."""
        if self.enable_prometheus:
            try:
                start_http_server(self.metrics_port)
                logger.info(f"Metrics server started on port {self.metrics_port}")
            except Exception as e:
                logger.error(f"Failed to start metrics server: {e}")

    def record_channel_request(
        self, channel: str, method: str, status: str, duration: float
    ):
        """Record channel request metrics."""
        if self.enable_prometheus:
            self._metrics["channel_requests_total"].labels(
                channel=channel, method=method, status=status
            ).inc()

            self._metrics["channel_request_duration_seconds"].labels(
                channel=channel, endpoint=method
            ).observe(duration)

    def record_workflow_execution(
        self, workflow_id: str, status: str, channel: str, duration: float
    ):
        """Record workflow execution metrics."""
        if self.enable_prometheus:
            self._metrics["workflow_executions_total"].labels(
                workflow_id=workflow_id, status=status, channel=channel
            ).inc()

            self._metrics["workflow_execution_duration_seconds"].labels(
                workflow_id=workflow_id
            ).observe(duration)

    def update_active_sessions(self, channel: str, count: int):
        """Update active sessions count."""
        if self.enable_prometheus:
            self._metrics["active_sessions_total"].labels(channel=channel).set(count)

    def record_session_duration(self, channel: str, duration: float):
        """Record session duration."""
        if self.enable_prometheus:
            self._metrics["session_duration_seconds"].labels(channel=channel).observe(
                duration
            )

    def record_tenant_operation(self, tenant_id: str, operation: str, status: str):
        """Record tenant operation."""
        if self.enable_prometheus:
            self._metrics["tenant_operations_total"].labels(
                tenant_id=tenant_id, operation=operation, status=status
            ).inc()

    def record_marketplace_operation(self, operation: str, status: str):
        """Record marketplace operation."""
        if self.enable_prometheus:
            self._metrics["marketplace_operations_total"].labels(
                operation=operation, status=status
            ).inc()

    def update_resource_metrics(self, memory_usage: int, db_connections: int):
        """Update resource metrics."""
        if self.enable_prometheus:
            self._metrics["memory_usage_bytes"].set(memory_usage)
            self._metrics["database_connections_active"].set(db_connections)

    def record_error(self, component: str, error_type: str, severity: str = "error"):
        """Record application error."""
        if self.enable_prometheus:
            self._metrics["errors_total"].labels(
                component=component, error_type=error_type, severity=severity
            ).inc()

    def set_app_info(self, version: str, environment: str):
        """Set application information."""
        if self.enable_prometheus:
            try:
                self._metrics["app_info"].info(
                    {
                        "version": version,
                        "environment": environment,
                        "start_time": str(datetime.fromtimestamp(self._start_time)),
                    }
                )
            except (AttributeError, TypeError) as e:
                logger.warning(f"Failed to set app info in Prometheus: {e}")
                # Store basic app info internally as fallback
                self._app_info = {
                    "version": version,
                    "environment": environment,
                    "start_time": str(datetime.fromtimestamp(self._start_time)),
                }

    def get_metrics_summary(self) -> Dict[str, Any]:
        """Get current metrics summary for health checks."""
        uptime = time.time() - self._start_time

        return {
            "uptime_seconds": uptime,
            "metrics_enabled": self.enable_prometheus,
            "metrics_port": self.metrics_port if self.enable_prometheus else None,
            "prometheus_available": PROMETHEUS_AVAILABLE,
            "start_time": datetime.fromtimestamp(self._start_time).isoformat(),
        }


class HealthMonitor:
    """Application health monitoring."""

    def __init__(self, metrics_collector: Optional[MetricsCollector] = None):
        """Initialize health monitor.

        Args:
            metrics_collector: Metrics collector instance
        """
        self.metrics = metrics_collector
        self._health_checks = {}
        self._last_health_check = None

    def register_health_check(self, name: str, check_func, interval: int = 60):
        """Register a health check function.

        Args:
            name: Health check name
            check_func: Async function that returns health status
            interval: Check interval in seconds
        """
        self._health_checks[name] = {
            "func": check_func,
            "interval": interval,
            "last_run": None,
            "last_result": None,
        }

    async def run_health_checks(self) -> Dict[str, Any]:
        """Run all health checks."""
        results = {}
        overall_healthy = True

        for name, check in self._health_checks.items():
            try:
                result = await check["func"]()
                results[name] = {
                    "status": "healthy" if result.get("healthy", True) else "unhealthy",
                    "details": result,
                    "last_checked": datetime.now().isoformat(),
                }

                if not result.get("healthy", True):
                    overall_healthy = False

                check["last_run"] = time.time()
                check["last_result"] = result

            except Exception as e:
                logger.error(f"Health check {name} failed: {e}")
                results[name] = {
                    "status": "error",
                    "error": str(e),
                    "last_checked": datetime.now().isoformat(),
                }
                overall_healthy = False

                if self.metrics:
                    self.metrics.record_error("health_monitor", "health_check_failed")

        health_summary = {
            "status": "healthy" if overall_healthy else "unhealthy",
            "checks": results,
            "timestamp": datetime.now().isoformat(),
        }

        self._last_health_check = health_summary
        return health_summary

    async def get_health_status(self) -> Dict[str, Any]:
        """Get current health status."""
        if self._last_health_check is None:
            return await self.run_health_checks()

        return self._last_health_check


# Metrics middleware for channels
class MetricsMiddleware:
    """Middleware to automatically collect metrics from channels."""

    def __init__(self, metrics_collector: MetricsCollector, channel_name: str):
        """Initialize metrics middleware.

        Args:
            metrics_collector: Metrics collector instance
            channel_name: Name of the channel
        """
        self.metrics = metrics_collector
        self.channel_name = channel_name

    async def __call__(self, request, call_next):
        """Middleware function for request processing."""
        start_time = time.time()
        status = "success"
        method = getattr(request, "method", "unknown")

        try:
            response = await call_next(request)

            if hasattr(response, "status_code"):
                status = "success" if response.status_code < 400 else "error"

            return response

        except Exception as e:
            status = "error"
            self.metrics.record_error(f"{self.channel_name}_channel", type(e).__name__)
            raise

        finally:
            duration = time.time() - start_time
            self.metrics.record_channel_request(
                self.channel_name, method, status, duration
            )
