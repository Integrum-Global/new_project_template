"""
IoT Processor MCP Server using Kailash SDK.

This server provides MCP tools for processing IoT data streams,
including telemetry analysis, anomaly detection, and real-time monitoring.
"""

import json
import logging
import statistics
from collections import defaultdict, deque
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Union

from kailash import NodeParameter
from kailash.middleware.mcp import MiddlewareMCPServer as MCPServer
from kailash.nodes.ai import LLMAgentNode
from kailash.nodes.data import StreamingDataNode
from kailash.nodes.transform import DataTransformer
from kailash.runtime import LocalRuntime
from kailash.workflow import Workflow

logger = logging.getLogger(__name__)


class IoTProcessorServer:
    """
    MCP Server for IoT data processing using Kailash SDK.

    Features:
    - Real-time telemetry processing
    - Anomaly detection using AI
    - Time-series data aggregation
    - Device fleet management
    - Alert generation and routing
    - Data transformation pipelines
    """

    def __init__(
        self,
        config_file: Optional[str] = None,
        config_override: Optional[Dict[str, Any]] = None,
    ):
        """
        Initialize IoT Processor Server.

        Args:
            config_file: Path to YAML configuration file
            config_override: Optional configuration overrides
        """
        # Initialize Enhanced MCP Server
        self.server = MCPServer(
            name="iot-processor",
            config_file=config_file,
            enable_cache=True,
            cache_ttl=30,  # 30 second default for IoT data
            enable_metrics=True,
            enable_formatting=True,
        )

        # Initialize runtime with streaming support
        self.runtime = LocalRuntime(
            enable_async=True,
            max_concurrency=20,  # Handle many concurrent device streams
        )

        # Store config
        self.config = config_override or {}

        # Initialize data stores
        self.telemetry_buffer = defaultdict(lambda: deque(maxlen=1000))
        self.device_registry = {}
        self.alert_thresholds = self.config.get("alert_thresholds", {})

        # Initialize AI agent for anomaly detection
        self.anomaly_detector = LLMAgentNode(
            name="anomaly_detector",
            model="gpt-4o-mini",
            system_prompt=self._get_anomaly_detection_prompt(),
        )

        # Set up tools and resources
        self._setup_tools()
        self._setup_resources()
        self._setup_processing_workflows()

    def _get_anomaly_detection_prompt(self) -> str:
        """Get the system prompt for anomaly detection."""
        return """You are an IoT anomaly detection expert. Analyze telemetry data for:
        1. Unusual patterns or deviations from normal behavior
        2. Potential equipment failures or degradation
        3. Security anomalies or unauthorized access
        4. Environmental conditions outside safe operating ranges

        Provide structured analysis with:
        - Anomaly type and severity (low/medium/high/critical)
        - Affected devices or systems
        - Recommended actions
        - Confidence score (0-100)"""

    def _setup_tools(self):
        """Set up IoT processing MCP tools."""

        @self.server.tool(format_response="json")
        def ingest_telemetry(
            device_id: str,
            timestamp: str,
            data: Dict[str, Any],
            metadata: Optional[Dict[str, Any]] = None,
        ) -> dict:
            """
            Ingest telemetry data from an IoT device.

            Args:
                device_id: Unique device identifier
                timestamp: ISO format timestamp
                data: Telemetry data (temperature, humidity, pressure, etc.)
                metadata: Optional device metadata
            """
            try:
                # Store in buffer
                telemetry_point = {
                    "timestamp": timestamp,
                    "data": data,
                    "metadata": metadata or {},
                }

                self.telemetry_buffer[device_id].append(telemetry_point)

                # Check thresholds
                alerts = self._check_thresholds(device_id, data)

                return {
                    "success": True,
                    "device_id": device_id,
                    "timestamp": timestamp,
                    "data_points": len(data),
                    "buffer_size": len(self.telemetry_buffer[device_id]),
                    "alerts": alerts,
                }

            except Exception as e:
                logger.error(f"Error ingesting telemetry: {e}")
                return {"success": False, "error": str(e), "device_id": device_id}

        @self.server.tool(
            cache_key="device_status",
            cache_ttl=10,  # 10 second cache
            format_response="markdown",
        )
        def get_device_status(device_id: str) -> dict:
            """Get current status and recent telemetry for a device."""
            try:
                # Get recent telemetry
                recent_data = list(self.telemetry_buffer.get(device_id, []))[-10:]

                if not recent_data:
                    return {
                        "success": False,
                        "error": "No data available for device",
                        "device_id": device_id,
                    }

                # Calculate statistics
                latest = recent_data[-1]
                stats = self._calculate_statistics(recent_data)

                return {
                    "success": True,
                    "device_id": device_id,
                    "status": "online" if recent_data else "offline",
                    "last_seen": latest["timestamp"],
                    "latest_data": latest["data"],
                    "statistics": stats,
                    "data_points": len(recent_data),
                }

            except Exception as e:
                logger.error(f"Error getting device status: {e}")
                return {"success": False, "error": str(e), "device_id": device_id}

        @self.server.tool(
            cache_key="fleet_overview", cache_ttl=30, format_response="markdown"
        )
        def get_fleet_overview(
            device_type: Optional[str] = None, include_offline: bool = True
        ) -> dict:
            """Get overview of all IoT devices in the fleet."""
            try:
                fleet_status = {
                    "total_devices": len(self.device_registry),
                    "online_devices": 0,
                    "offline_devices": 0,
                    "devices_with_alerts": 0,
                    "device_summary": [],
                }

                # Check each device
                for device_id, device_info in self.device_registry.items():
                    if device_type and device_info.get("type") != device_type:
                        continue

                    recent_data = list(self.telemetry_buffer.get(device_id, []))
                    is_online = False

                    if recent_data:
                        # Check if last data is within 5 minutes
                        last_timestamp = datetime.fromisoformat(
                            recent_data[-1]["timestamp"]
                        )
                        is_online = (datetime.now() - last_timestamp) < timedelta(
                            minutes=5
                        )

                    if is_online:
                        fleet_status["online_devices"] += 1
                    else:
                        fleet_status["offline_devices"] += 1

                    if is_online or include_offline:
                        device_summary = {
                            "device_id": device_id,
                            "type": device_info.get("type", "unknown"),
                            "status": "online" if is_online else "offline",
                            "last_seen": (
                                recent_data[-1]["timestamp"] if recent_data else "never"
                            ),
                        }
                        fleet_status["device_summary"].append(device_summary)

                return {
                    "success": True,
                    "fleet_status": fleet_status,
                    "timestamp": datetime.now().isoformat(),
                }

            except Exception as e:
                logger.error(f"Error getting fleet overview: {e}")
                return {"success": False, "error": str(e)}

        @self.server.tool(format_response="json")
        def detect_anomalies(
            device_id: str, time_window_minutes: int = 60, use_ai: bool = True
        ) -> dict:
            """
            Detect anomalies in device telemetry data.

            Args:
                device_id: Device to analyze
                time_window_minutes: Time window for analysis
                use_ai: Use AI for advanced anomaly detection
            """
            try:
                # Get telemetry data for time window
                recent_data = list(self.telemetry_buffer.get(device_id, []))

                if not recent_data:
                    return {
                        "success": False,
                        "error": "No data available for analysis",
                        "device_id": device_id,
                    }

                # Filter by time window
                cutoff_time = datetime.now() - timedelta(minutes=time_window_minutes)
                window_data = [
                    d
                    for d in recent_data
                    if datetime.fromisoformat(d["timestamp"]) > cutoff_time
                ]

                anomalies = []

                # Statistical anomaly detection
                stats_anomalies = self._detect_statistical_anomalies(window_data)
                anomalies.extend(stats_anomalies)

                # AI-based anomaly detection
                if use_ai and len(window_data) > 5:
                    workflow = Workflow(
                        "anomaly_detection", "Detect anomalies using AI"
                    )
                    workflow.add_node("detector", self.anomaly_detector)

                    # Prepare data for AI analysis
                    telemetry_summary = {
                        "device_id": device_id,
                        "time_window": f"{time_window_minutes} minutes",
                        "data_points": len(window_data),
                        "telemetry": window_data[-20:],  # Last 20 points
                        "statistics": self._calculate_statistics(window_data),
                    }

                    parameters = {
                        "detector": {"input": json.dumps(telemetry_summary, indent=2)}
                    }

                    result, _ = self.runtime.execute(workflow, parameters=parameters)

                    if result.get("detector", {}).get("response"):
                        ai_anomalies = self._parse_ai_anomalies(
                            result["detector"]["response"]
                        )
                        anomalies.extend(ai_anomalies)

                return {
                    "success": True,
                    "device_id": device_id,
                    "time_window_minutes": time_window_minutes,
                    "data_points_analyzed": len(window_data),
                    "anomalies_detected": len(anomalies),
                    "anomalies": anomalies,
                }

            except Exception as e:
                logger.error(f"Error detecting anomalies: {e}")
                return {"success": False, "error": str(e), "device_id": device_id}

        @self.server.tool(
            cache_key="aggregate_telemetry", cache_ttl=60, format_response="json"
        )
        def aggregate_telemetry(
            device_ids: List[str],
            metric: str,
            aggregation: str = "average",
            time_window_minutes: int = 60,
        ) -> dict:
            """
            Aggregate telemetry data across multiple devices.

            Args:
                device_ids: List of devices to aggregate
                metric: Telemetry metric to aggregate (e.g., "temperature")
                aggregation: Type of aggregation (average, sum, min, max, count)
                time_window_minutes: Time window for aggregation
            """
            try:
                cutoff_time = datetime.now() - timedelta(minutes=time_window_minutes)
                all_values = []
                device_values = {}

                for device_id in device_ids:
                    device_data = list(self.telemetry_buffer.get(device_id, []))

                    # Filter by time window and extract metric
                    values = []
                    for point in device_data:
                        if datetime.fromisoformat(point["timestamp"]) > cutoff_time:
                            if metric in point["data"]:
                                values.append(point["data"][metric])

                    if values:
                        device_values[device_id] = values
                        all_values.extend(values)

                if not all_values:
                    return {
                        "success": False,
                        "error": f"No data available for metric '{metric}'",
                        "devices_checked": len(device_ids),
                    }

                # Calculate aggregation
                if aggregation == "average":
                    result_value = statistics.mean(all_values)
                elif aggregation == "sum":
                    result_value = sum(all_values)
                elif aggregation == "min":
                    result_value = min(all_values)
                elif aggregation == "max":
                    result_value = max(all_values)
                elif aggregation == "count":
                    result_value = len(all_values)
                else:
                    result_value = all_values

                return {
                    "success": True,
                    "metric": metric,
                    "aggregation": aggregation,
                    "result": result_value,
                    "devices_included": len(device_values),
                    "total_data_points": len(all_values),
                    "time_window_minutes": time_window_minutes,
                    "device_breakdown": {
                        device_id: {
                            "count": len(values),
                            "average": statistics.mean(values) if values else 0,
                        }
                        for device_id, values in device_values.items()
                    },
                }

            except Exception as e:
                logger.error(f"Error aggregating telemetry: {e}")
                return {"success": False, "error": str(e), "metric": metric}

        @self.server.tool(format_response="markdown")
        def configure_alert_threshold(
            metric: str,
            min_value: Optional[float] = None,
            max_value: Optional[float] = None,
            device_type: Optional[str] = None,
        ) -> dict:
            """Configure alert thresholds for telemetry metrics."""
            try:
                threshold_config = {
                    "metric": metric,
                    "min": min_value,
                    "max": max_value,
                    "device_type": device_type,
                }

                # Store threshold configuration
                threshold_key = f"{device_type or 'all'}_{metric}"
                self.alert_thresholds[threshold_key] = threshold_config

                return {
                    "success": True,
                    "message": f"Alert threshold configured for {metric}",
                    "configuration": threshold_config,
                }

            except Exception as e:
                return {"success": False, "error": str(e), "metric": metric}

        @self.server.tool(format_response="markdown")
        def register_device(
            device_id: str,
            device_type: str,
            location: Optional[str] = None,
            metadata: Optional[Dict[str, Any]] = None,
        ) -> dict:
            """Register a new IoT device."""
            try:
                device_info = {
                    "device_id": device_id,
                    "type": device_type,
                    "location": location,
                    "metadata": metadata or {},
                    "registered_at": datetime.now().isoformat(),
                }

                self.device_registry[device_id] = device_info

                return {
                    "success": True,
                    "message": f"Device {device_id} registered successfully",
                    "device_info": device_info,
                }

            except Exception as e:
                return {"success": False, "error": str(e), "device_id": device_id}

    def _setup_resources(self):
        """Set up IoT processor MCP resources."""

        @self.server.resource(uri="iot://devices")
        def list_devices() -> dict:
            """List all registered IoT devices."""
            return {
                "total_devices": len(self.device_registry),
                "devices": list(self.device_registry.values()),
            }

        @self.server.resource(uri="iot://thresholds")
        def list_alert_thresholds() -> dict:
            """List configured alert thresholds."""
            return {"thresholds": self.alert_thresholds}

        @self.server.resource(uri="iot://statistics")
        def get_iot_statistics() -> dict:
            """Get IoT system statistics."""
            total_data_points = sum(
                len(buffer) for buffer in self.telemetry_buffer.values()
            )

            return {
                "total_devices": len(self.device_registry),
                "active_devices": len(self.telemetry_buffer),
                "total_data_points": total_data_points,
                "alert_thresholds_configured": len(self.alert_thresholds),
            }

    def _setup_processing_workflows(self):
        """Set up pre-defined IoT processing workflows."""

        @self.server.tool(format_response="markdown")
        def create_monitoring_dashboard(
            device_ids: List[str],
            metrics: List[str],
            refresh_interval_seconds: int = 30,
        ) -> dict:
            """Create a monitoring dashboard for devices."""
            # This would create a real-time monitoring workflow
            return {
                "success": True,
                "dashboard_config": {
                    "devices": device_ids,
                    "metrics": metrics,
                    "refresh_interval": refresh_interval_seconds,
                },
                "message": "Dashboard created (placeholder implementation)",
            }

        @self.server.tool(format_response="markdown")
        def export_telemetry_data(
            device_ids: List[str], start_time: str, end_time: str, format: str = "csv"
        ) -> dict:
            """Export historical telemetry data."""
            # This would export data in requested format
            return {
                "success": True,
                "devices": device_ids,
                "time_range": f"{start_time} to {end_time}",
                "format": format,
                "message": "Export initiated (placeholder implementation)",
            }

    def _check_thresholds(
        self, device_id: str, data: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Check data against configured thresholds."""
        alerts = []

        # Get device info
        device_info = self.device_registry.get(device_id, {})
        device_type = device_info.get("type", "unknown")

        for metric, value in data.items():
            # Check device-specific thresholds
            threshold_key = f"{device_type}_{metric}"
            if threshold_key not in self.alert_thresholds:
                # Check general thresholds
                threshold_key = f"all_{metric}"

            if threshold_key in self.alert_thresholds:
                threshold = self.alert_thresholds[threshold_key]

                if threshold["min"] is not None and value < threshold["min"]:
                    alerts.append(
                        {
                            "type": "threshold_violation",
                            "severity": "high",
                            "metric": metric,
                            "value": value,
                            "threshold": threshold["min"],
                            "direction": "below",
                        }
                    )

                if threshold["max"] is not None and value > threshold["max"]:
                    alerts.append(
                        {
                            "type": "threshold_violation",
                            "severity": "high",
                            "metric": metric,
                            "value": value,
                            "threshold": threshold["max"],
                            "direction": "above",
                        }
                    )

        return alerts

    def _calculate_statistics(
        self, data_points: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Calculate statistics for telemetry data."""
        if not data_points:
            return {}

        # Extract all numeric metrics
        metrics = defaultdict(list)
        for point in data_points:
            for key, value in point["data"].items():
                if isinstance(value, (int, float)):
                    metrics[key].append(value)

        # Calculate stats for each metric
        stats = {}
        for metric, values in metrics.items():
            if values:
                stats[metric] = {
                    "min": min(values),
                    "max": max(values),
                    "average": statistics.mean(values),
                    "std_dev": statistics.stdev(values) if len(values) > 1 else 0,
                    "count": len(values),
                }

        return stats

    def _detect_statistical_anomalies(
        self, data_points: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Detect anomalies using statistical methods."""
        anomalies = []

        if len(data_points) < 10:
            return anomalies

        # Calculate statistics for each metric
        metrics = defaultdict(list)
        for point in data_points:
            for key, value in point["data"].items():
                if isinstance(value, (int, float)):
                    metrics[key].append((point["timestamp"], value))

        # Check for statistical anomalies
        for metric, time_values in metrics.items():
            values = [v[1] for v in time_values]

            if len(values) > 3:
                mean = statistics.mean(values)
                std_dev = statistics.stdev(values)

                # Check for values outside 3 standard deviations
                for timestamp, value in time_values:
                    z_score = abs((value - mean) / std_dev) if std_dev > 0 else 0

                    if z_score > 3:
                        anomalies.append(
                            {
                                "type": "statistical",
                                "metric": metric,
                                "timestamp": timestamp,
                                "value": value,
                                "z_score": z_score,
                                "severity": "high" if z_score > 4 else "medium",
                            }
                        )

        return anomalies

    def _parse_ai_anomalies(self, ai_response: str) -> List[Dict[str, Any]]:
        """Parse anomalies from AI response."""
        # In production, this would parse structured AI output
        # For now, return placeholder
        return []

    def run(self):
        """Start the IoT Processor MCP server."""
        logger.info("Starting IoT Processor MCP Server...")
        self.server.run()
