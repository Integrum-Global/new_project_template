"""
Monitor Node

Custom Kailash node for monitoring MCP operations and performance.
"""

import asyncio
import logging
import statistics
from collections import defaultdict
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from kailash.node import Node
from kailash.node.parameter import NodeParameter, ParameterType

logger = logging.getLogger(__name__)


class MonitorNode(Node):
    """
    Node for monitoring MCP operations, performance, and health.

    Features:
    - Real-time metrics collection
    - Performance analysis
    - Anomaly detection
    - Alert generation
    - Trend analysis
    - Resource usage tracking
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize the monitor node."""
        self.config = config or {}

        # Monitoring settings
        self.metric_window = self.config.get("metric_window", 300)  # 5 minutes
        self.alert_thresholds = self.config.get(
            "alert_thresholds",
            {
                "error_rate": 0.1,  # 10% error rate
                "response_time_ms": 1000,  # 1 second
                "cpu_percent": 80,
                "memory_percent": 85,
            },
        )

        # Metrics storage
        self._metrics_buffer = defaultdict(list)
        self._alerts = []

        super().__init__()

    def get_parameters(self) -> Dict[str, NodeParameter]:
        """Define node parameters."""
        return {
            "operation": NodeParameter(
                name="operation",
                type=ParameterType.STRING,
                required=True,
                description="Monitoring operation to perform",
                allowed_values=[
                    "collect_metrics",
                    "analyze_performance",
                    "detect_anomalies",
                    "generate_alerts",
                    "get_trends",
                    "get_summary",
                ],
            ),
            "metrics": NodeParameter(
                name="metrics",
                type=ParameterType.DICT,
                required=False,
                description="Metrics data to process",
            ),
            "time_range": NodeParameter(
                name="time_range",
                type=ParameterType.DICT,
                required=False,
                description="Time range for analysis",
            ),
            "metric_types": NodeParameter(
                name="metric_types",
                type=ParameterType.LIST,
                required=False,
                description="Types of metrics to analyze",
            ),
            "server_id": NodeParameter(
                name="server_id",
                type=ParameterType.STRING,
                required=False,
                description="Specific server to monitor",
            ),
        }

    async def execute(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute the monitoring operation."""
        operation = context.get("operation")

        try:
            if operation == "collect_metrics":
                return await self._collect_metrics(context)
            elif operation == "analyze_performance":
                return await self._analyze_performance(context)
            elif operation == "detect_anomalies":
                return await self._detect_anomalies(context)
            elif operation == "generate_alerts":
                return await self._generate_alerts(context)
            elif operation == "get_trends":
                return await self._get_trends(context)
            elif operation == "get_summary":
                return await self._get_summary(context)
            else:
                return {"success": False, "error": f"Unknown operation: {operation}"}

        except Exception as e:
            logger.error(f"Error in monitoring operation: {e}")
            return {"success": False, "error": str(e), "operation": operation}

    async def _collect_metrics(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Collect and store metrics."""
        metrics = context.get("metrics", {})

        # Store metrics with timestamp
        timestamp = datetime.utcnow()

        for metric_type, value in metrics.items():
            self._metrics_buffer[metric_type].append(
                {
                    "value": value,
                    "timestamp": timestamp,
                    "server_id": context.get("server_id"),
                }
            )

        # Clean old metrics
        self._clean_old_metrics()

        # Calculate current stats
        current_stats = {}
        for metric_type, values in self._metrics_buffer.items():
            if values:
                current_stats[metric_type] = {
                    "current": values[-1]["value"],
                    "count": len(values),
                    "window_seconds": self.metric_window,
                }

        return {
            "success": True,
            "metrics_collected": len(metrics),
            "timestamp": timestamp.isoformat(),
            "current_stats": current_stats,
        }

    async def _analyze_performance(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze performance metrics."""
        time_range = context.get("time_range", {})
        metric_types = context.get(
            "metric_types",
            [
                "response_time_ms",
                "throughput",
                "error_rate",
                "cpu_percent",
                "memory_percent",
            ],
        )

        analysis = {}

        for metric_type in metric_types:
            if metric_type in self._metrics_buffer:
                values = self._get_values_in_range(metric_type, time_range)

                if values:
                    numeric_values = [
                        v["value"]
                        for v in values
                        if isinstance(v["value"], (int, float))
                    ]

                    if numeric_values:
                        analysis[metric_type] = {
                            "min": min(numeric_values),
                            "max": max(numeric_values),
                            "avg": statistics.mean(numeric_values),
                            "median": statistics.median(numeric_values),
                            "std_dev": (
                                statistics.stdev(numeric_values)
                                if len(numeric_values) > 1
                                else 0
                            ),
                            "percentiles": {
                                "p50": statistics.median(numeric_values),
                                "p95": self._percentile(numeric_values, 95),
                                "p99": self._percentile(numeric_values, 99),
                            },
                            "sample_count": len(numeric_values),
                        }

        # Performance score calculation
        performance_score = self._calculate_performance_score(analysis)

        return {
            "success": True,
            "analysis": analysis,
            "performance_score": performance_score,
            "analysis_time": datetime.utcnow().isoformat(),
        }

    async def _detect_anomalies(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Detect anomalies in metrics."""
        anomalies = []

        # Simple anomaly detection based on statistical methods
        for metric_type, values in self._metrics_buffer.items():
            if len(values) < 10:  # Need enough data points
                continue

            numeric_values = [
                v["value"] for v in values if isinstance(v["value"], (int, float))
            ]

            if numeric_values:
                mean = statistics.mean(numeric_values)
                std_dev = (
                    statistics.stdev(numeric_values) if len(numeric_values) > 1 else 0
                )

                # Detect outliers (values beyond 3 standard deviations)
                for value_entry in values[-10:]:  # Check recent values
                    value = value_entry["value"]
                    if isinstance(value, (int, float)):
                        z_score = abs((value - mean) / std_dev) if std_dev > 0 else 0

                        if z_score > 3:
                            anomalies.append(
                                {
                                    "metric_type": metric_type,
                                    "value": value,
                                    "z_score": z_score,
                                    "timestamp": value_entry["timestamp"].isoformat(),
                                    "server_id": value_entry.get("server_id"),
                                    "severity": "high" if z_score > 4 else "medium",
                                }
                            )

        # Pattern-based anomaly detection
        pattern_anomalies = await self._detect_pattern_anomalies()
        anomalies.extend(pattern_anomalies)

        return {
            "success": True,
            "anomaly_count": len(anomalies),
            "anomalies": anomalies,
            "detection_time": datetime.utcnow().isoformat(),
        }

    async def _detect_pattern_anomalies(self) -> List[Dict[str, Any]]:
        """Detect anomalies based on patterns."""
        anomalies = []

        # Detect sudden spikes or drops
        for metric_type, values in self._metrics_buffer.items():
            if len(values) < 3:
                continue

            numeric_values = [
                v["value"] for v in values if isinstance(v["value"], (int, float))
            ]

            if len(numeric_values) >= 3:
                # Check for sudden changes
                for i in range(1, len(numeric_values)):
                    if numeric_values[i - 1] > 0:
                        change_ratio = (
                            abs(numeric_values[i] - numeric_values[i - 1])
                            / numeric_values[i - 1]
                        )

                        if change_ratio > 2.0:  # 200% change
                            anomalies.append(
                                {
                                    "metric_type": metric_type,
                                    "pattern": "sudden_change",
                                    "change_ratio": change_ratio,
                                    "from_value": numeric_values[i - 1],
                                    "to_value": numeric_values[i],
                                    "timestamp": values[i]["timestamp"].isoformat(),
                                    "severity": "medium",
                                }
                            )

        return anomalies

    async def _generate_alerts(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Generate alerts based on thresholds and conditions."""
        new_alerts = []

        # Check thresholds
        for metric_type, threshold in self.alert_thresholds.items():
            if metric_type in self._metrics_buffer:
                recent_values = self._metrics_buffer[metric_type][-5:]  # Last 5 values

                for value_entry in recent_values:
                    value = value_entry["value"]
                    if isinstance(value, (int, float)) and value > threshold:
                        alert = {
                            "id": f"alert_{datetime.utcnow().timestamp()}",
                            "type": "threshold_exceeded",
                            "metric_type": metric_type,
                            "value": value,
                            "threshold": threshold,
                            "timestamp": value_entry["timestamp"].isoformat(),
                            "server_id": value_entry.get("server_id"),
                            "severity": self._get_alert_severity(
                                metric_type, value, threshold
                            ),
                            "message": f"{metric_type} exceeded threshold: {value} > {threshold}",
                        }

                        # Check if similar alert was recently generated
                        if not self._is_duplicate_alert(alert):
                            new_alerts.append(alert)
                            self._alerts.append(alert)

        # Check for anomaly-based alerts
        anomalies = await self._detect_anomalies(context)
        for anomaly in anomalies["anomalies"]:
            if anomaly["severity"] == "high":
                alert = {
                    "id": f"alert_{datetime.utcnow().timestamp()}",
                    "type": "anomaly_detected",
                    "metric_type": anomaly["metric_type"],
                    "anomaly": anomaly,
                    "timestamp": datetime.utcnow().isoformat(),
                    "severity": "high",
                    "message": f"Anomaly detected in {anomaly['metric_type']}",
                }
                new_alerts.append(alert)
                self._alerts.append(alert)

        # Clean old alerts
        self._clean_old_alerts()

        return {
            "success": True,
            "new_alerts": len(new_alerts),
            "alerts": new_alerts,
            "total_active_alerts": len(self._alerts),
        }

    async def _get_trends(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze trends in metrics."""
        time_range = context.get("time_range", {})
        metric_types = context.get("metric_types", list(self._metrics_buffer.keys()))

        trends = {}

        for metric_type in metric_types:
            if metric_type in self._metrics_buffer:
                values = self._get_values_in_range(metric_type, time_range)

                if len(values) >= 2:
                    numeric_values = [
                        (v["timestamp"], v["value"])
                        for v in values
                        if isinstance(v["value"], (int, float))
                    ]

                    if numeric_values:
                        # Calculate trend direction
                        first_value = numeric_values[0][1]
                        last_value = numeric_values[-1][1]

                        if first_value != 0:
                            change_percent = (
                                (last_value - first_value) / first_value
                            ) * 100
                        else:
                            change_percent = 0

                        # Simple linear regression for trend
                        slope = self._calculate_trend_slope(numeric_values)

                        trends[metric_type] = {
                            "direction": (
                                "increasing"
                                if slope > 0
                                else "decreasing" if slope < 0 else "stable"
                            ),
                            "change_percent": change_percent,
                            "slope": slope,
                            "start_value": first_value,
                            "end_value": last_value,
                            "data_points": len(numeric_values),
                        }

        return {
            "success": True,
            "trends": trends,
            "analysis_period": time_range,
            "trend_time": datetime.utcnow().isoformat(),
        }

    async def _get_summary(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Get monitoring summary."""
        server_id = context.get("server_id")

        # Overall system health
        health_score = self._calculate_health_score()

        # Current metrics summary
        current_metrics = {}
        for metric_type, values in self._metrics_buffer.items():
            if values:
                # Filter by server if specified
                if server_id:
                    values = [v for v in values if v.get("server_id") == server_id]

                if values:
                    latest = values[-1]
                    current_metrics[metric_type] = {
                        "current_value": latest["value"],
                        "timestamp": latest["timestamp"].isoformat(),
                    }

        # Active alerts
        active_alerts = len(self._alerts)
        critical_alerts = sum(
            1 for a in self._alerts if a.get("severity") == "critical"
        )

        # Performance analysis
        perf_analysis = await self._analyze_performance(context)

        return {
            "success": True,
            "summary": {
                "health_score": health_score,
                "status": self._get_status_from_score(health_score),
                "current_metrics": current_metrics,
                "active_alerts": active_alerts,
                "critical_alerts": critical_alerts,
                "performance_analysis": perf_analysis.get("analysis", {}),
                "monitoring_window_seconds": self.metric_window,
                "summary_time": datetime.utcnow().isoformat(),
            },
        }

    def _get_values_in_range(
        self, metric_type: str, time_range: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Get metric values within a time range."""
        if metric_type not in self._metrics_buffer:
            return []

        values = self._metrics_buffer[metric_type]

        if not time_range:
            return values

        start_time = time_range.get("start")
        end_time = time_range.get("end", datetime.utcnow())

        if start_time:
            values = [v for v in values if v["timestamp"] >= start_time]
        if end_time:
            values = [v for v in values if v["timestamp"] <= end_time]

        return values

    def _clean_old_metrics(self):
        """Remove metrics older than the metric window."""
        cutoff_time = datetime.utcnow() - timedelta(seconds=self.metric_window)

        for metric_type in self._metrics_buffer:
            self._metrics_buffer[metric_type] = [
                v
                for v in self._metrics_buffer[metric_type]
                if v["timestamp"] > cutoff_time
            ]

    def _clean_old_alerts(self):
        """Remove old alerts."""
        # Keep alerts for 1 hour
        cutoff_time = datetime.utcnow() - timedelta(hours=1)

        self._alerts = [
            a
            for a in self._alerts
            if datetime.fromisoformat(a["timestamp"]) > cutoff_time
        ]

    def _percentile(self, values: List[float], percentile: float) -> float:
        """Calculate percentile value."""
        if not values:
            return 0

        sorted_values = sorted(values)
        index = int(len(sorted_values) * percentile / 100)

        if index >= len(sorted_values):
            index = len(sorted_values) - 1

        return sorted_values[index]

    def _calculate_performance_score(self, analysis: Dict[str, Any]) -> float:
        """Calculate overall performance score (0-100)."""
        score = 100.0

        # Deduct points for poor metrics
        if "response_time_ms" in analysis:
            avg_response = analysis["response_time_ms"]["avg"]
            if avg_response > 1000:
                score -= 20
            elif avg_response > 500:
                score -= 10

        if "error_rate" in analysis:
            error_rate = analysis["error_rate"]["avg"]
            if error_rate > 0.1:
                score -= 30
            elif error_rate > 0.05:
                score -= 15

        if "cpu_percent" in analysis:
            avg_cpu = analysis["cpu_percent"]["avg"]
            if avg_cpu > 80:
                score -= 15
            elif avg_cpu > 60:
                score -= 5

        return max(0, score)

    def _calculate_health_score(self) -> float:
        """Calculate overall health score."""
        score = 100.0

        # Deduct for active alerts
        score -= len(self._alerts) * 5
        score -= sum(1 for a in self._alerts if a.get("severity") == "critical") * 10

        # Deduct for poor recent metrics
        for metric_type, values in self._metrics_buffer.items():
            if values and metric_type in self.alert_thresholds:
                recent_values = values[-5:]
                threshold = self.alert_thresholds[metric_type]

                violations = sum(
                    1
                    for v in recent_values
                    if isinstance(v["value"], (int, float)) and v["value"] > threshold
                )

                if violations > 2:
                    score -= 10

        return max(0, score)

    def _get_status_from_score(self, score: float) -> str:
        """Get status description from health score."""
        if score >= 90:
            return "excellent"
        elif score >= 70:
            return "good"
        elif score >= 50:
            return "fair"
        elif score >= 30:
            return "poor"
        else:
            return "critical"

    def _get_alert_severity(
        self, metric_type: str, value: float, threshold: float
    ) -> str:
        """Determine alert severity."""
        ratio = value / threshold if threshold > 0 else 1

        if ratio > 2.0:
            return "critical"
        elif ratio > 1.5:
            return "high"
        elif ratio > 1.2:
            return "medium"
        else:
            return "low"

    def _is_duplicate_alert(self, alert: Dict[str, Any]) -> bool:
        """Check if alert is duplicate of recent alert."""
        # Check last 10 alerts
        for existing_alert in self._alerts[-10:]:
            if (
                existing_alert["type"] == alert["type"]
                and existing_alert["metric_type"] == alert["metric_type"]
                and existing_alert.get("server_id") == alert.get("server_id")
            ):

                # Check if alerts are within 5 minutes
                existing_time = datetime.fromisoformat(existing_alert["timestamp"])
                new_time = datetime.fromisoformat(alert["timestamp"])

                if abs((new_time - existing_time).total_seconds()) < 300:
                    return True

        return False

    def _calculate_trend_slope(self, values: List[tuple]) -> float:
        """Calculate trend slope using simple linear regression."""
        if len(values) < 2:
            return 0

        # Convert timestamps to numeric values (seconds since first point)
        first_time = values[0][0]
        x_values = [(v[0] - first_time).total_seconds() for v in values]
        y_values = [v[1] for v in values]

        # Calculate slope
        n = len(values)
        x_mean = sum(x_values) / n
        y_mean = sum(y_values) / n

        numerator = sum((x - x_mean) * (y - y_mean) for x, y in zip(x_values, y_values))
        denominator = sum((x - x_mean) ** 2 for x in x_values)

        if denominator == 0:
            return 0

        return numerator / denominator
