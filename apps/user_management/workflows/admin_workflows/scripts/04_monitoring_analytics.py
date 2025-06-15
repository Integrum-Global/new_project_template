#!/usr/bin/env python3
"""
Admin Workflow: Monitoring and Analytics

This workflow handles system monitoring and analytics including:
- System performance monitoring
- User activity analytics
- Business intelligence reporting
- Capacity planning
- Trend analysis and forecasting
"""

import os
import sys
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

# Add shared utilities to path
sys.path.append(os.path.join(os.path.dirname(__file__), "..", "..", "shared"))

from workflow_runner import WorkflowRunner, create_user_context_node


class MonitoringAnalyticsWorkflow:
    """
    Complete monitoring and analytics workflow for administrators.
    """

    def __init__(self, admin_user_id: str = "admin"):
        """
        Initialize the monitoring and analytics workflow.

        Args:
            admin_user_id: ID of the administrator performing monitoring operations
        """
        self.admin_user_id = admin_user_id
        self.runner = WorkflowRunner(
            user_type="admin",
            user_id=admin_user_id,
            enable_debug=True,
            enable_audit=False,  # Disable for testing
            enable_monitoring=True,
        )

    def monitor_system_performance(
        self, monitoring_config: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """
        Monitor comprehensive system performance metrics.

        Args:
            monitoring_config: Monitoring configuration parameters

        Returns:
            System performance monitoring results
        """
        print("📊 Monitoring System Performance...")

        if not monitoring_config:
            monitoring_config = {
                "time_range": "last_24_hours",
                "include_predictions": True,
                "alert_thresholds": True,
            }

        builder = self.runner.create_workflow("system_performance_monitoring")

        # Add admin context for monitoring operations
        builder.add_node(
            "PythonCodeNode",
            "admin_context",
            create_user_context_node(
                self.admin_user_id, "admin", ["system_admin", "monitoring_admin"]
            ),
        )

        # Collect comprehensive system metrics
        builder.add_node(
            "PythonCodeNode",
            "collect_system_metrics",
            {
                "name": "collect_comprehensive_system_metrics",
                "code": f"""
from datetime import datetime, timedelta
import random
import math

# Collect comprehensive system performance metrics
monitoring_config = {monitoring_config}
time_range = monitoring_config.get("time_range", "last_24_hours")

# Generate realistic performance data for last 24 hours
hours = 24
current_time = datetime.now()
base_cpu = 45  # Base CPU usage
base_memory = 65  # Base memory usage
base_response = 85  # Base response time

# System resource metrics
system_metrics = {{
    "cpu_usage": [],
    "memory_usage": [],
    "disk_usage": [],
    "network_io": [],
    "response_times": [],
    "error_rates": [],
    "concurrent_users": [],
    "api_calls_per_minute": []
}}

# Generate hourly metrics for last 24 hours
for hour in range(hours):
    timestamp = (current_time - timedelta(hours=hours-hour)).replace(minute=0, second=0, microsecond=0)

    # Add realistic variations (business hours vs off-hours)
    hour_of_day = timestamp.hour
    is_business_hours = 9 <= hour_of_day <= 17
    business_multiplier = 1.5 if is_business_hours else 0.6

    # Weekly patterns (weekdays vs weekends)
    is_weekend = timestamp.weekday() >= 5
    weekend_multiplier = 0.4 if is_weekend else 1.0

    # Combined load factor
    load_factor = business_multiplier * weekend_multiplier

    # CPU usage with realistic patterns
    cpu_variation = random.uniform(-10, 15) * load_factor
    cpu_usage = max(5, min(95, base_cpu + cpu_variation))

    # Memory usage (more stable than CPU)
    memory_variation = random.uniform(-5, 10) * load_factor
    memory_usage = max(20, min(90, base_memory + memory_variation))

    # Disk usage (gradual increase)
    disk_base = 72 + (hour * 0.1)  # Gradual growth
    disk_variation = random.uniform(-2, 3)
    disk_usage = max(60, min(85, disk_base + disk_variation))

    # Network I/O (correlated with user activity)
    network_base = 150 * load_factor
    network_variation = random.uniform(-30, 50)
    network_io = max(10, network_base + network_variation)

    # Response times (inversely correlated with load)
    response_base = base_response + (cpu_usage * 0.5)
    response_variation = random.uniform(-10, 20)
    response_time = max(20, response_base + response_variation)

    # Error rates (higher under load)
    error_base = 0.1 + (cpu_usage * 0.01)
    error_variation = random.uniform(-0.05, 0.1)
    error_rate = max(0, error_base + error_variation)

    # Concurrent users
    users_base = 200 * load_factor
    users_variation = random.uniform(-50, 100)
    concurrent_users = max(10, int(users_base + users_variation))

    # API calls per minute
    api_base = 1500 * load_factor
    api_variation = random.uniform(-300, 500)
    api_calls = max(100, int(api_base + api_variation))

    # Store metrics
    system_metrics["cpu_usage"].append({{"timestamp": timestamp.isoformat(), "value": round(cpu_usage, 2)}})
    system_metrics["memory_usage"].append({{"timestamp": timestamp.isoformat(), "value": round(memory_usage, 2)}})
    system_metrics["disk_usage"].append({{"timestamp": timestamp.isoformat(), "value": round(disk_usage, 2)}})
    system_metrics["network_io"].append({{"timestamp": timestamp.isoformat(), "value": round(network_io, 2)}})
    system_metrics["response_times"].append({{"timestamp": timestamp.isoformat(), "value": round(response_time, 2)}})
    system_metrics["error_rates"].append({{"timestamp": timestamp.isoformat(), "value": round(error_rate, 4)}})
    system_metrics["concurrent_users"].append({{"timestamp": timestamp.isoformat(), "value": concurrent_users}})
    system_metrics["api_calls_per_minute"].append({{"timestamp": timestamp.isoformat(), "value": api_calls}})

# Calculate current performance summary
current_metrics = {{
    "cpu_usage": system_metrics["cpu_usage"][-1]["value"],
    "memory_usage": system_metrics["memory_usage"][-1]["value"],
    "disk_usage": system_metrics["disk_usage"][-1]["value"],
    "network_io": system_metrics["network_io"][-1]["value"],
    "response_time": system_metrics["response_times"][-1]["value"],
    "error_rate": system_metrics["error_rates"][-1]["value"],
    "concurrent_users": system_metrics["concurrent_users"][-1]["value"],
    "api_calls_per_minute": system_metrics["api_calls_per_minute"][-1]["value"]
}}

# Performance thresholds and alerts
performance_thresholds = {{
    "cpu_usage": {{"warning": 70, "critical": 85}},
    "memory_usage": {{"warning": 75, "critical": 90}},
    "disk_usage": {{"warning": 80, "critical": 95}},
    "response_time": {{"warning": 200, "critical": 500}},
    "error_rate": {{"warning": 0.5, "critical": 1.0}},
    "concurrent_users": {{"warning": 400, "critical": 500}}
}}

# Check for threshold violations
active_alerts = []
for metric, thresholds in performance_thresholds.items():
    if metric in current_metrics:
        value = current_metrics[metric]
        if value >= thresholds["critical"]:
            active_alerts.append({{
                "metric": metric,
                "level": "critical",
                "current_value": value,
                "threshold": thresholds["critical"],
                "message": f"{{metric}} is at critical level: {{value}}"
            }})
        elif value >= thresholds["warning"]:
            active_alerts.append({{
                "metric": metric,
                "level": "warning",
                "current_value": value,
                "threshold": thresholds["warning"],
                "message": f"{{metric}} is at warning level: {{value}}"
            }})

# Calculate averages for the monitoring period
avg_metrics = {{}}
for metric_name, metric_data in system_metrics.items():
    values = [m["value"] for m in metric_data]
    avg_metrics[metric_name] = {{
        "average": round(sum(values) / len(values), 2),
        "min": round(min(values), 2),
        "max": round(max(values), 2),
        "trend": "increasing" if values[-1] > values[0] else "decreasing" if values[-1] < values[0] else "stable"
    }}

# System health assessment
health_score = 100
if current_metrics["cpu_usage"] > 80:
    health_score -= 20
elif current_metrics["cpu_usage"] > 70:
    health_score -= 10

if current_metrics["memory_usage"] > 85:
    health_score -= 15
elif current_metrics["memory_usage"] > 75:
    health_score -= 8

if current_metrics["response_time"] > 300:
    health_score -= 15
elif current_metrics["response_time"] > 200:
    health_score -= 8

if current_metrics["error_rate"] > 0.5:
    health_score -= 20
elif current_metrics["error_rate"] > 0.1:
    health_score -= 10

health_status = "excellent" if health_score >= 90 else "good" if health_score >= 75 else "fair" if health_score >= 60 else "poor"

result = {{
    "result": {{
        "monitoring_successful": True,
        "monitoring_timestamp": datetime.now().isoformat(),
        "time_range": time_range,
        "system_metrics": system_metrics,
        "current_metrics": current_metrics,
        "average_metrics": avg_metrics,
        "performance_thresholds": performance_thresholds,
        "active_alerts": active_alerts,
        "health_score": health_score,
        "health_status": health_status
    }}
}}
""",
            },
        )

        # Analyze performance trends and predictions
        builder.add_node(
            "PythonCodeNode",
            "analyze_performance_trends",
            {
                "name": "analyze_system_performance_trends",
                "code": """
# Analyze performance trends and generate predictions
performance_data = system_performance_data

if performance_data.get("monitoring_successful"):
    system_metrics = performance_data.get("system_metrics", {})
    current_metrics = performance_data.get("current_metrics", {})
    active_alerts = performance_data.get("active_alerts", [])

    # Trend analysis
    trend_analysis = {}

    for metric_name, metric_data in system_metrics.items():
        values = [m["value"] for m in metric_data]
        timestamps = [datetime.fromisoformat(m["timestamp"]) for m in metric_data]

        # Calculate trend direction and rate
        if len(values) >= 2:
            # Simple linear regression for trend
            n = len(values)
            x_values = list(range(n))

            # Calculate slope (trend direction)
            x_mean = sum(x_values) / n
            y_mean = sum(values) / n

            numerator = sum((x_values[i] - x_mean) * (values[i] - y_mean) for i in range(n))
            denominator = sum((x_values[i] - x_mean) ** 2 for i in range(n))

            if denominator != 0:
                slope = numerator / denominator
                trend_direction = "increasing" if slope > 0.1 else "decreasing" if slope < -0.1 else "stable"
                trend_rate = abs(slope)
            else:
                trend_direction = "stable"
                trend_rate = 0

            # Volatility (standard deviation)
            variance = sum((v - y_mean) ** 2 for v in values) / n
            volatility = variance ** 0.5

            # Prediction for next 4 hours (simple linear extrapolation)
            prediction_points = 4
            predictions = []
            for i in range(1, prediction_points + 1):
                predicted_value = values[-1] + (slope * i)
                predicted_time = timestamps[-1] + timedelta(hours=i)
                predictions.append({
                    "timestamp": predicted_time.isoformat(),
                    "predicted_value": round(max(0, predicted_value), 2),
                    "confidence": max(0.5, 1.0 - (volatility / y_mean)) if y_mean > 0 else 0.5
                })

            trend_analysis[metric_name] = {
                "trend_direction": trend_direction,
                "trend_rate": round(trend_rate, 4),
                "volatility": round(volatility, 2),
                "current_value": values[-1],
                "average_value": round(y_mean, 2),
                "predictions": predictions,
                "stability": "high" if volatility < y_mean * 0.1 else "medium" if volatility < y_mean * 0.2 else "low"
            }

    # Capacity planning analysis
    capacity_analysis = {}

    # CPU capacity
    cpu_values = [m["value"] for m in system_metrics.get("cpu_usage", [])]
    cpu_avg = sum(cpu_values) / len(cpu_values) if cpu_values else 0
    cpu_max = max(cpu_values) if cpu_values else 0
    cpu_capacity_remaining = 100 - cpu_max
    cpu_trend = trend_analysis.get("cpu_usage", {}).get("trend_direction", "stable")

    capacity_analysis["cpu"] = {
        "current_usage": cpu_values[-1] if cpu_values else 0,
        "average_usage": round(cpu_avg, 2),
        "peak_usage": cpu_max,
        "capacity_remaining": round(cpu_capacity_remaining, 2),
        "trend": cpu_trend,
        "estimated_time_to_capacity": "6 months" if cpu_trend == "increasing" else "not_applicable",
        "recommendation": "Monitor closely" if cpu_avg > 70 else "Adequate capacity"
    }

    # Memory capacity
    memory_values = [m["value"] for m in system_metrics.get("memory_usage", [])]
    memory_avg = sum(memory_values) / len(memory_values) if memory_values else 0
    memory_max = max(memory_values) if memory_values else 0
    memory_capacity_remaining = 100 - memory_max
    memory_trend = trend_analysis.get("memory_usage", {}).get("trend_direction", "stable")

    capacity_analysis["memory"] = {
        "current_usage": memory_values[-1] if memory_values else 0,
        "average_usage": round(memory_avg, 2),
        "peak_usage": memory_max,
        "capacity_remaining": round(memory_capacity_remaining, 2),
        "trend": memory_trend,
        "estimated_time_to_capacity": "3 months" if memory_trend == "increasing" else "not_applicable",
        "recommendation": "Plan upgrade" if memory_avg > 80 else "Adequate capacity"
    }

    # Performance optimization recommendations
    optimization_recommendations = []

    # CPU optimization
    if cpu_avg > 75:
        optimization_recommendations.append({
            "category": "cpu_optimization",
            "priority": "high" if cpu_avg > 85 else "medium",
            "recommendation": "Optimize CPU-intensive processes",
            "specific_actions": [
                "Profile application performance",
                "Optimize database queries",
                "Implement caching strategies",
                "Consider horizontal scaling"
            ],
            "expected_improvement": "15-25% CPU reduction"
        })

    # Memory optimization
    if memory_avg > 80:
        optimization_recommendations.append({
            "category": "memory_optimization",
            "priority": "high" if memory_avg > 90 else "medium",
            "recommendation": "Optimize memory usage",
            "specific_actions": [
                "Identify memory leaks",
                "Optimize data structures",
                "Implement memory caching",
                "Consider memory upgrade"
            ],
            "expected_improvement": "10-20% memory reduction"
        })

    # Response time optimization
    response_values = [m["value"] for m in system_metrics.get("response_times", [])]
    response_avg = sum(response_values) / len(response_values) if response_values else 0

    if response_avg > 150:
        optimization_recommendations.append({
            "category": "response_time_optimization",
            "priority": "high" if response_avg > 300 else "medium",
            "recommendation": "Improve response times",
            "specific_actions": [
                "Optimize database connections",
                "Implement response caching",
                "Optimize network latency",
                "Review application architecture"
            ],
            "expected_improvement": "20-40% response time improvement"
        })

    # Alert recommendations
    alert_recommendations = []

    if len(active_alerts) > 0:
        alert_recommendations.append({
            "priority": "immediate",
            "category": "active_alerts",
            "recommendation": f"Address {len(active_alerts)} active performance alerts",
            "actions": ["Investigate root causes", "Implement immediate fixes", "Monitor for recurrence"]
        })

    # Predictive alerts
    for metric_name, analysis in trend_analysis.items():
        predictions = analysis.get("predictions", [])
        if predictions:
            # Check if any predictions exceed thresholds
            thresholds = performance_data.get("performance_thresholds", {}).get(metric_name, {})
            warning_threshold = thresholds.get("warning")
            critical_threshold = thresholds.get("critical")

            for pred in predictions:
                pred_value = pred.get("predicted_value", 0)
                if critical_threshold and pred_value >= critical_threshold:
                    alert_recommendations.append({
                        "priority": "high",
                        "category": "predictive_alert",
                        "recommendation": f"{metric_name} predicted to reach critical levels",
                        "timeframe": pred.get("timestamp"),
                        "actions": ["Proactive capacity planning", "Performance optimization", "Alert stakeholders"]
                    })
                elif warning_threshold and pred_value >= warning_threshold:
                    alert_recommendations.append({
                        "priority": "medium",
                        "category": "predictive_warning",
                        "recommendation": f"{metric_name} predicted to reach warning levels",
                        "timeframe": pred.get("timestamp"),
                        "actions": ["Monitor trend", "Prepare mitigation plans"]
                    })

else:
    trend_analysis = {}
    capacity_analysis = {}
    optimization_recommendations = []
    alert_recommendations = []

result = {
    "result": {
        "analysis_completed": performance_data.get("monitoring_successful", False),
        "trend_analysis": trend_analysis,
        "capacity_analysis": capacity_analysis,
        "optimization_recommendations": optimization_recommendations,
        "alert_recommendations": alert_recommendations,
        "analysis_timestamp": datetime.now().isoformat()
    }
}
""",
            },
        )

        # Connect monitoring nodes
        builder.add_connection(
            "admin_context", "result", "collect_system_metrics", "context"
        )
        builder.add_connection(
            "collect_system_metrics",
            "result.result",
            "analyze_performance_trends",
            "system_performance_data",
        )

        # Execute workflow
        workflow = builder.build()
        results, execution_id = self.runner.execute_workflow(
            workflow, monitoring_config, "system_performance_monitoring"
        )

        return results

    def analyze_user_activity(
        self, analysis_config: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """
        Analyze user activity patterns and generate insights.

        Args:
            analysis_config: Analysis configuration parameters

        Returns:
            User activity analysis results
        """
        print("👥 Analyzing User Activity...")

        if not analysis_config:
            analysis_config = {
                "time_range": "last_30_days",
                "include_demographics": True,
                "include_behavior_analysis": True,
            }

        builder = self.runner.create_workflow("user_activity_analysis")

        # Collect user activity data
        builder.add_node(
            "PythonCodeNode",
            "collect_user_activity",
            {
                "name": "collect_comprehensive_user_activity",
                "code": f"""
import random

# Collect comprehensive user activity data
analysis_config = {analysis_config}
time_range = analysis_config.get("time_range", "last_30_days")

# Generate realistic user activity data
total_users = 347
active_users_last_30_days = 312
active_users_last_7_days = 285
active_users_today = 156

# User engagement metrics
user_engagement = {{
    "total_registered_users": total_users,
    "active_users_30_days": active_users_last_30_days,
    "active_users_7_days": active_users_last_7_days,
    "active_users_today": active_users_today,
    "monthly_active_rate": round((active_users_last_30_days / total_users) * 100, 1),
    "weekly_active_rate": round((active_users_last_7_days / total_users) * 100, 1),
    "daily_active_rate": round((active_users_today / total_users) * 100, 1),
    "user_retention_rate": 89.2,
    "new_user_signups_30_days": 23,
    "user_churn_rate": 2.1
}}

# Feature usage analytics
feature_usage = {{
    "dashboard_views": {{"total": 15420, "unique_users": 289, "avg_per_user": 53.4}},
    "profile_updates": {{"total": 2156, "unique_users": 201, "avg_per_user": 10.7}},
    "report_generation": {{"total": 834, "unique_users": 127, "avg_per_user": 6.6}},
    "data_exports": {{"total": 445, "unique_users": 89, "avg_per_user": 5.0}},
    "support_tickets": {{"total": 67, "unique_users": 54, "avg_per_user": 1.2}},
    "security_settings": {{"total": 312, "unique_users": 178, "avg_per_user": 1.8}},
    "admin_functions": {{"total": 1289, "unique_users": 12, "avg_per_user": 107.4}}
}}

# User demographics and segmentation
user_demographics = {{
    "by_department": {{
        "Engineering": {{"count": 142, "percentage": 40.9, "activity_level": "high"}},
        "Sales": {{"count": 89, "percentage": 25.6, "activity_level": "high"}},
        "Marketing": {{"count": 56, "percentage": 16.1, "activity_level": "medium"}},
        "HR": {{"count": 34, "percentage": 9.8, "activity_level": "medium"}},
        "Finance": {{"count": 26, "percentage": 7.5, "activity_level": "low"}}
    }},
    "by_role": {{
        "Employee": {{"count": 267, "percentage": 77.0, "avg_session_duration": "2.3 hours"}},
        "Manager": {{"count": 58, "percentage": 16.7, "avg_session_duration": "3.1 hours"}},
        "Admin": {{"count": 22, "percentage": 6.3, "avg_session_duration": "4.2 hours"}}
    }},
    "by_tenure": {{
        "New (0-3 months)": {{"count": 45, "percentage": 13.0, "activity_level": "learning"}},
        "Established (3-12 months)": {{"count": 128, "percentage": 36.9, "activity_level": "high"}},
        "Veteran (1+ years)": {{"count": 174, "percentage": 50.1, "activity_level": "stable"}}
    }}
}}

# Session analytics
session_analytics = {{
    "average_session_duration": "2.8 hours",
    "total_sessions_30_days": 4567,
    "average_sessions_per_user": 14.6,
    "peak_usage_hours": ["09:00-10:00", "14:00-15:00", "16:00-17:00"],
    "lowest_usage_hours": ["22:00-06:00"],
    "weekend_usage_percentage": 12.3,
    "mobile_usage_percentage": 23.7,
    "browser_breakdown": {{
        "Chrome": 67.2,
        "Safari": 18.9,
        "Firefox": 9.1,
        "Edge": 4.8
    }}
}}

# Generate daily activity patterns for last 30 days
daily_activity = []
base_daily_users = 180
for day in range(30):
    date = (datetime.now() - timedelta(days=30-day)).date()

    # Weekend pattern
    is_weekend = date.weekday() >= 5
    weekend_factor = 0.3 if is_weekend else 1.0

    # Random variation
    variation = random.uniform(0.8, 1.2)

    # Calculate daily active users
    daily_users = int(base_daily_users * weekend_factor * variation)

    # Calculate other metrics
    daily_sessions = int(daily_users * random.uniform(2.5, 4.2))
    daily_logins = int(daily_users * random.uniform(1.0, 1.8))
    daily_features_used = int(daily_users * random.uniform(8.2, 15.6))

    daily_activity.append({{
        "date": date.isoformat(),
        "active_users": daily_users,
        "total_sessions": daily_sessions,
        "total_logins": daily_logins,
        "features_used": daily_features_used,
        "avg_session_duration": round(random.uniform(2.1, 3.8), 1)
    }})

# User behavior patterns
behavior_patterns = {{
    "power_users": {{
        "count": 34,
        "criteria": "90+ percentile usage",
        "characteristics": ["Daily active", "Uses multiple features", "Long sessions", "Admin/Manager roles"],
        "average_weekly_sessions": 18.3
    }},
    "regular_users": {{
        "count": 198,
        "criteria": "25-90 percentile usage",
        "characteristics": ["Regular weekly activity", "Core feature usage", "Standard sessions"],
        "average_weekly_sessions": 8.7
    }},
    "occasional_users": {{
        "count": 80,
        "criteria": "5-25 percentile usage",
        "characteristics": ["Sporadic usage", "Limited features", "Short sessions"],
        "average_weekly_sessions": 2.1
    }},
    "inactive_users": {{
        "count": 35,
        "criteria": "Bottom 5 percentile",
        "characteristics": ["Rare or no recent activity", "May need re-engagement"],
        "average_weekly_sessions": 0.3
    }}
}}

result = {{
    "result": {{
        "analysis_successful": True,
        "analysis_timestamp": datetime.now().isoformat(),
        "time_range": time_range,
        "user_engagement": user_engagement,
        "feature_usage": feature_usage,
        "user_demographics": user_demographics,
        "session_analytics": session_analytics,
        "daily_activity": daily_activity,
        "behavior_patterns": behavior_patterns
    }}
}}
""",
            },
        )

        # Generate user insights and recommendations
        builder.add_node(
            "PythonCodeNode",
            "generate_user_insights",
            {
                "name": "generate_user_activity_insights",
                "code": """
# Generate actionable insights from user activity analysis
activity_data = user_activity_data

if activity_data.get("analysis_successful"):
    user_engagement = activity_data.get("user_engagement", {})
    feature_usage = activity_data.get("feature_usage", {})
    user_demographics = activity_data.get("user_demographics", {})
    session_analytics = activity_data.get("session_analytics", {})
    behavior_patterns = activity_data.get("behavior_patterns", {})
    daily_activity = activity_data.get("daily_activity", [])

    # Engagement insights
    engagement_insights = {
        "overall_health": "good",  # Based on 90%+ monthly active rate
        "key_metrics": {
            "monthly_active_rate": user_engagement.get("monthly_active_rate", 0),
            "user_retention": user_engagement.get("user_retention_rate", 0),
            "churn_rate": user_engagement.get("user_churn_rate", 0)
        }
    }

    # Determine engagement health
    monthly_rate = user_engagement.get("monthly_active_rate", 0)
    if monthly_rate >= 85:
        engagement_insights["overall_health"] = "excellent"
    elif monthly_rate >= 70:
        engagement_insights["overall_health"] = "good"
    elif monthly_rate >= 50:
        engagement_insights["overall_health"] = "fair"
    else:
        engagement_insights["overall_health"] = "poor"

    # Feature adoption insights
    feature_insights = {}
    total_users = user_engagement.get("total_registered_users", 1)

    for feature, usage in feature_usage.items():
        unique_users = usage.get("unique_users", 0)
        adoption_rate = (unique_users / total_users) * 100

        feature_insights[feature] = {
            "adoption_rate": round(adoption_rate, 1),
            "usage_intensity": usage.get("avg_per_user", 0),
            "status": "high_adoption" if adoption_rate >= 60 else "medium_adoption" if adoption_rate >= 30 else "low_adoption"
        }

    # User segment insights
    segment_insights = {}

    # Department analysis
    dept_data = user_demographics.get("by_department", {})
    most_active_dept = max(dept_data.items(), key=lambda x: x[1].get("count", 0) if x[1].get("activity_level") == "high" else 0)
    least_active_dept = min(dept_data.items(), key=lambda x: x[1].get("count", 0) if x[1].get("activity_level") == "low" else float('inf'))

    segment_insights["departments"] = {
        "most_active": most_active_dept[0] if most_active_dept else "N/A",
        "least_active": least_active_dept[0] if least_active_dept else "N/A",
        "opportunities": [dept for dept, info in dept_data.items() if info.get("activity_level") == "low"]
    }

    # Behavioral insights
    power_users = behavior_patterns.get("power_users", {}).get("count", 0)
    inactive_users = behavior_patterns.get("inactive_users", {}).get("count", 0)

    behavioral_insights = {
        "power_user_percentage": round((power_users / total_users) * 100, 1),
        "inactive_user_percentage": round((inactive_users / total_users) * 100, 1),
        "engagement_distribution": "healthy" if power_users > inactive_users else "needs_attention"
    }

    # Trend analysis from daily activity
    if len(daily_activity) >= 7:
        recent_week = daily_activity[-7:]
        previous_week = daily_activity[-14:-7] if len(daily_activity) >= 14 else daily_activity[:7]

        recent_avg = sum(day["active_users"] for day in recent_week) / len(recent_week)
        previous_avg = sum(day["active_users"] for day in previous_week) / len(previous_week)

        trend_direction = "increasing" if recent_avg > previous_avg * 1.05 else "decreasing" if recent_avg < previous_avg * 0.95 else "stable"
        trend_magnitude = abs(recent_avg - previous_avg) / previous_avg * 100 if previous_avg > 0 else 0

        trend_insights = {
            "direction": trend_direction,
            "magnitude": round(trend_magnitude, 1),
            "recent_average": round(recent_avg, 1),
            "previous_average": round(previous_avg, 1)
        }
    else:
        trend_insights = {"direction": "insufficient_data"}

    # Generate recommendations
    recommendations = []

    # Engagement recommendations
    if monthly_rate < 80:
        recommendations.append({
            "category": "user_engagement",
            "priority": "high",
            "title": "Improve User Engagement",
            "description": f"Monthly active rate ({monthly_rate}%) below target (80%)",
            "actions": [
                "Implement user onboarding program",
                "Create feature adoption campaigns",
                "Send re-engagement emails to inactive users",
                "Analyze user feedback for improvement opportunities"
            ],
            "expected_impact": "10-15% increase in engagement"
        })

    # Feature adoption recommendations
    low_adoption_features = [f for f, i in feature_insights.items() if i["status"] == "low_adoption"]
    if low_adoption_features:
        recommendations.append({
            "category": "feature_adoption",
            "priority": "medium",
            "title": "Improve Feature Adoption",
            "description": f"{len(low_adoption_features)} features have low adoption rates",
            "actions": [
                "Create feature tutorials and guides",
                "Implement in-app feature discovery",
                "Analyze user workflows for feature placement",
                "Consider feature simplification or removal"
            ],
            "affected_features": low_adoption_features,
            "expected_impact": "20-30% improvement in feature usage"
        })

    # Inactive user recommendations
    inactive_percentage = behavioral_insights.get("inactive_user_percentage", 0)
    if inactive_percentage > 10:
        recommendations.append({
            "category": "user_retention",
            "priority": "high",
            "title": "Re-engage Inactive Users",
            "description": f"{inactive_percentage}% of users are inactive",
            "actions": [
                "Identify reasons for inactivity",
                "Design targeted re-engagement campaigns",
                "Provide personalized onboarding",
                "Consider user experience improvements"
            ],
            "expected_impact": "25-40% reduction in inactive users"
        })

    # Department-specific recommendations
    low_activity_depts = segment_insights.get("departments", {}).get("opportunities", [])
    if low_activity_depts:
        recommendations.append({
            "category": "department_engagement",
            "priority": "medium",
            "title": "Target Low-Activity Departments",
            "description": f"Departments with low engagement: {', '.join(low_activity_depts)}",
            "actions": [
                "Conduct department-specific needs analysis",
                "Provide tailored training sessions",
                "Assign department champions",
                "Customize features for department workflows"
            ],
            "target_departments": low_activity_depts,
            "expected_impact": "30-50% increase in department engagement"
        })

    # Success metrics and KPIs
    success_metrics = {
        "primary_kpis": [
            {"metric": "Monthly Active Users", "current": f"{monthly_rate}%", "target": "85%+"},
            {"metric": "User Retention Rate", "current": f"{user_engagement.get('user_retention_rate', 0)}%", "target": "90%+"},
            {"metric": "Feature Adoption Rate", "current": "Variable", "target": "60%+ per feature"},
            {"metric": "Session Duration", "current": session_analytics.get("average_session_duration", "N/A"), "target": "3+ hours"}
        ],
        "secondary_kpis": [
            {"metric": "Power User Ratio", "current": f"{behavioral_insights.get('power_user_percentage', 0)}%", "target": "15%+"},
            {"metric": "Support Ticket Rate", "current": "Low", "target": "Maintain low"},
            {"metric": "Mobile Usage", "current": f"{session_analytics.get('mobile_usage_percentage', 0)}%", "target": "30%+"}
        ]
    }

else:
    engagement_insights = {}
    feature_insights = {}
    segment_insights = {}
    behavioral_insights = {}
    trend_insights = {}
    recommendations = []
    success_metrics = {}

result = {
    "result": {
        "insights_generated": activity_data.get("analysis_successful", False),
        "engagement_insights": engagement_insights,
        "feature_insights": feature_insights,
        "segment_insights": segment_insights,
        "behavioral_insights": behavioral_insights,
        "trend_insights": trend_insights,
        "recommendations": recommendations,
        "success_metrics": success_metrics,
        "total_recommendations": len(recommendations)
    }
}
""",
            },
        )

        # Connect user activity analysis nodes
        builder.add_connection(
            "collect_user_activity",
            "result.result",
            "generate_user_insights",
            "user_activity_data",
        )

        # Execute workflow
        workflow = builder.build()
        results, execution_id = self.runner.execute_workflow(
            workflow, analysis_config, "user_activity_analysis"
        )

        return results

    def generate_business_reports(
        self, report_config: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """
        Generate comprehensive business intelligence reports.

        Args:
            report_config: Report configuration parameters

        Returns:
            Business reporting results
        """
        print("📈 Generating Business Reports...")

        if not report_config:
            report_config = {
                "report_types": [
                    "executive_summary",
                    "operational_metrics",
                    "security_overview",
                ],
                "time_period": "monthly",
                "include_forecasts": True,
            }

        builder = self.runner.create_workflow("business_intelligence_reporting")

        # Generate comprehensive business reports
        builder.add_node(
            "PythonCodeNode",
            "generate_reports",
            {
                "name": "generate_comprehensive_business_reports",
                "code": f"""
# Generate comprehensive business intelligence reports
report_config = {report_config}
report_types = report_config.get("report_types", ["executive_summary"])
time_period = report_config.get("time_period", "monthly")

# Executive Summary Report
executive_summary = {{
    "report_type": "executive_summary",
    "period": time_period,
    "generated_at": datetime.now().isoformat(),
    "key_metrics": {{
        "total_users": 347,
        "active_users": 312,
        "user_growth": "+6.8%",
        "system_uptime": "99.94%",
        "security_incidents": 2,
        "customer_satisfaction": 4.6
    }},
    "highlights": [
        "User engagement increased by 12% this month",
        "Zero critical security incidents",
        "System performance improved by 8%",
        "Successfully completed GDPR compliance audit"
    ],
    "concerns": [
        "2 medium-priority security alerts",
        "Feature adoption rate below target for 3 features",
        "Disk usage approaching 75% capacity"
    ],
    "recommendations": [
        "Implement feature adoption campaign",
        "Plan infrastructure capacity upgrade",
        "Enhance security monitoring protocols"
    ]
}}

# Operational Metrics Report
operational_metrics = {{
    "report_type": "operational_metrics",
    "period": time_period,
    "system_performance": {{
        "average_response_time": "87ms",
        "uptime_percentage": 99.94,
        "error_rate": 0.12,
        "concurrent_users_peak": 428,
        "api_calls_total": 1847562,
        "data_processed": "14.7TB"
    }},
    "user_metrics": {{
        "new_registrations": 23,
        "active_users_daily_avg": 186,
        "session_duration_avg": "2.8 hours",
        "feature_usage_growth": "+15%",
        "support_tickets": 67,
        "user_satisfaction": 4.6
    }},
    "business_metrics": {{
        "productivity_index": 94.2,
        "cost_per_user": "$12.34",
        "roi_improvement": "+8.5%",
        "automation_rate": 78.6,
        "compliance_score": 96.8
    }},
    "trends": {{
        "user_engagement": "increasing",
        "system_performance": "stable",
        "security_posture": "improving",
        "cost_efficiency": "optimizing"
    }}
}}

# Security Overview Report
security_overview = {{
    "report_type": "security_overview",
    "period": time_period,
    "security_score": 85,
    "threat_landscape": {{
        "total_threats_detected": 127,
        "threats_mitigated": 125,
        "false_positives": 12,
        "critical_incidents": 0,
        "high_severity_incidents": 2,
        "medium_severity_incidents": 8
    }},
    "access_control": {{
        "compliance_rate": 94.3,
        "failed_login_attempts": 234,
        "successful_logins": 15678,
        "mfa_adoption_rate": 87.2,
        "privileged_access_reviews": 12
    }},
    "vulnerability_management": {{
        "vulnerabilities_identified": 15,
        "vulnerabilities_patched": 13,
        "critical_vulnerabilities": 0,
        "high_vulnerabilities": 2,
        "medium_vulnerabilities": 8,
        "low_vulnerabilities": 5
    }},
    "compliance_status": {{
        "gdpr_compliance": 96.8,
        "soc2_compliance": 94.2,
        "iso27001_compliance": 91.5,
        "audit_findings": 3,
        "remediation_progress": 78.6
    }}
}}

# Performance Analytics Report
performance_analytics = {{
    "report_type": "performance_analytics",
    "period": time_period,
    "system_health": {{
        "overall_score": 88.5,
        "cpu_utilization": 56.7,
        "memory_utilization": 68.3,
        "disk_utilization": 74.2,
        "network_throughput": "850 Mbps avg"
    }},
    "application_performance": {{
        "response_time_p50": "65ms",
        "response_time_p95": "180ms",
        "response_time_p99": "450ms",
        "error_rate": 0.12,
        "throughput": "2,847 req/min avg"
    }},
    "capacity_planning": {{
        "projected_growth": "+15% over 6 months",
        "infrastructure_runway": "8 months",
        "scaling_recommendations": [
            "Add 2 application servers by Q3",
            "Upgrade database storage by Q4",
            "Implement CDN for static assets"
        ]
    }}
}}

# User Analytics Report
user_analytics = {{
    "report_type": "user_analytics",
    "period": time_period,
    "engagement_metrics": {{
        "monthly_active_users": 312,
        "weekly_active_users": 285,
        "daily_active_users": 186,
        "user_retention_rate": 89.2,
        "churn_rate": 2.1
    }},
    "feature_adoption": {{
        "top_features": [
            {{"name": "Dashboard", "adoption": 93.4}},
            {{"name": "Reports", "adoption": 78.9}},
            {{"name": "Profile Management", "adoption": 67.2}},
            {{"name": "Data Export", "adoption": 34.7}},
            {{"name": "Admin Panel", "adoption": 12.3}}
        ],
        "emerging_features": [
            {{"name": "Mobile App", "growth": "+45%"}},
            {{"name": "API Access", "growth": "+32%"}},
            {{"name": "Automation", "growth": "+28%"}}
        ]
    }},
    "user_satisfaction": {{
        "overall_rating": 4.6,
        "nps_score": 67,
        "support_satisfaction": 4.8,
        "feature_satisfaction": 4.4,
        "performance_satisfaction": 4.5
    }}
}}

# Compile reports based on requested types
generated_reports = {{}}

for report_type in report_types:
    if report_type == "executive_summary":
        generated_reports["executive_summary"] = executive_summary
    elif report_type == "operational_metrics":
        generated_reports["operational_metrics"] = operational_metrics
    elif report_type == "security_overview":
        generated_reports["security_overview"] = security_overview
    elif report_type == "performance_analytics":
        generated_reports["performance_analytics"] = performance_analytics
    elif report_type == "user_analytics":
        generated_reports["user_analytics"] = user_analytics

# Generate forecasts if requested
forecasts = {{}}
if report_config.get("include_forecasts", False):
    forecasts = {{
        "user_growth_forecast": {{
            "next_month": "+5-8%",
            "next_quarter": "+18-25%",
            "confidence": "high"
        }},
        "system_load_forecast": {{
            "next_month": "+12%",
            "next_quarter": "+38%",
            "confidence": "medium"
        }},
        "security_threat_forecast": {{
            "threat_level": "stable",
            "emerging_risks": ["AI-based attacks", "Supply chain vulnerabilities"],
            "confidence": "medium"
        }}
    }}

# Report distribution and scheduling
distribution_info = {{
    "auto_generated": True,
    "recipients": ["executives", "operations_team", "security_team"],
    "formats": ["pdf", "email_summary", "dashboard"],
    "next_generation": (datetime.now() + timedelta(days=30)).isoformat(),
    "retention_period": "2 years"
}}

result = {{
    "result": {{
        "reports_generated": True,
        "generation_timestamp": datetime.now().isoformat(),
        "report_period": time_period,
        "total_reports": len(generated_reports),
        "generated_reports": generated_reports,
        "forecasts": forecasts,
        "distribution_info": distribution_info
    }}
}}
""",
            },
        )

        # Execute workflow
        workflow = builder.build()
        results, execution_id = self.runner.execute_workflow(
            workflow, report_config, "business_intelligence_reporting"
        )

        return results

    def run_comprehensive_monitoring_demo(self) -> Dict[str, Any]:
        """
        Run a comprehensive demonstration of all monitoring and analytics operations.

        Returns:
            Complete demonstration results
        """
        print("🚀 Starting Comprehensive Monitoring and Analytics Demonstration...")
        print("=" * 70)

        demo_results = {}

        try:
            # 1. Monitor system performance
            print("\n1. Monitoring System Performance...")
            monitoring_config = {
                "time_range": "last_24_hours",
                "include_predictions": True,
                "alert_thresholds": True,
            }
            demo_results["performance_monitoring"] = self.monitor_system_performance(
                monitoring_config
            )

            # 2. Analyze user activity
            print("\n2. Analyzing User Activity...")
            analysis_config = {
                "time_range": "last_30_days",
                "include_demographics": True,
                "include_behavior_analysis": True,
            }
            demo_results["user_analysis"] = self.analyze_user_activity(analysis_config)

            # 3. Generate business reports
            print("\n3. Generating Business Reports...")
            report_config = {
                "report_types": [
                    "executive_summary",
                    "operational_metrics",
                    "security_overview",
                ],
                "time_period": "monthly",
                "include_forecasts": True,
            }
            demo_results["business_reports"] = self.generate_business_reports(
                report_config
            )

            # Print comprehensive summary
            self.print_monitoring_summary(demo_results)

            return demo_results

        except Exception as e:
            print(f"❌ Monitoring and analytics demonstration failed: {str(e)}")
            raise

    def print_monitoring_summary(self, results: Dict[str, Any]):
        """
        Print a comprehensive monitoring and analytics summary.

        Args:
            results: Monitoring and analytics results from all workflows
        """
        print("\n" + "=" * 70)
        print("MONITORING AND ANALYTICS DEMONSTRATION COMPLETE")
        print("=" * 70)

        # Performance monitoring summary
        perf_result = (
            results.get("performance_monitoring", {})
            .get("collect_system_metrics", {})
            .get("result", {})
            .get("result", {})
        )
        health_score = perf_result.get("health_score", 0)
        active_alerts = len(perf_result.get("active_alerts", []))
        print(
            f"📊 Performance: {health_score}/100 health score, {active_alerts} active alerts"
        )

        # User analysis summary
        user_result = (
            results.get("user_analysis", {})
            .get("collect_user_activity", {})
            .get("result", {})
            .get("result", {})
        )
        user_engagement = user_result.get("user_engagement", {})
        monthly_active = user_engagement.get("monthly_active_rate", 0)
        print(
            f"👥 Users: {monthly_active}% monthly active rate, {user_engagement.get('active_users_30_days', 0)} active users"
        )

        # Business reports summary
        reports_result = (
            results.get("business_reports", {})
            .get("generate_reports", {})
            .get("result", {})
            .get("result", {})
        )
        total_reports = reports_result.get("total_reports", 0)
        print(f"📈 Reports: {total_reports} business reports generated")

        print("\n🎉 All monitoring and analytics operations completed successfully!")
        print("=" * 70)

        # Print execution statistics
        self.runner.print_stats()


def test_workflow(test_params: Optional[Dict[str, Any]] = None) -> bool:
    """
    Test the monitoring and analytics workflow.

    Args:
        test_params: Optional test parameters

    Returns:
        True if test passes, False otherwise
    """
    try:
        print("🧪 Testing Monitoring and Analytics Workflow...")

        # Create test workflow
        monitoring = MonitoringAnalyticsWorkflow("test_admin")

        # Test system performance monitoring
        result = monitoring.monitor_system_performance()
        if (
            not result.get("collect_system_metrics", {})
            .get("result", {})
            .get("result", {})
            .get("monitoring_successful")
        ):
            return False

        print("✅ Monitoring and analytics workflow test passed")
        return True

    except Exception as e:
        print(f"❌ Monitoring and analytics workflow test failed: {str(e)}")
        return False


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--test":
        # Run test
        success = test_workflow()
        sys.exit(0 if success else 1)
    else:
        # Run comprehensive demonstration
        monitoring = MonitoringAnalyticsWorkflow()

        try:
            results = monitoring.run_comprehensive_monitoring_demo()
            print("🎉 Monitoring and analytics demonstration completed successfully!")
        except Exception as e:
            print(f"❌ Demonstration failed: {str(e)}")
            sys.exit(1)
