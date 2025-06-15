#!/usr/bin/env python3
"""
Manager Workflow: Reporting and Analytics

This workflow handles comprehensive reporting and analytics for department managers including:
- Team performance dashboards
- Activity monitoring and trends
- Resource utilization reports
- Compliance and security analytics
- Custom report generation
"""

import os
import random
import sys
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

# Add shared utilities to path
sys.path.append(os.path.join(os.path.dirname(__file__), "..", "..", "shared"))

from workflow_runner import (
    WorkflowRunner,
    create_user_context_node,
    create_validation_node,
)


class ReportingAnalyticsWorkflow:
    """
    Complete reporting and analytics workflow for department managers.
    """

    def __init__(self, manager_user_id: str = "manager@company.com"):
        """
        Initialize the reporting and analytics workflow.

        Args:
            manager_user_id: ID of the manager generating reports
        """
        self.manager_user_id = manager_user_id
        self.runner = WorkflowRunner(
            user_type="manager",
            user_id=manager_user_id,
            enable_debug=True,
            enable_audit=False,  # Disable for testing
            enable_monitoring=True,
        )

    def generate_team_performance_report(
        self, report_config: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """
        Generate comprehensive team performance report.

        Args:
            report_config: Report configuration parameters

        Returns:
            Team performance report results
        """
        print("📊 Generating Team Performance Report...")

        if not report_config:
            report_config = {
                "department": "Engineering",
                "period": "monthly",
                "include_trends": True,
                "include_comparisons": True,
            }

        builder = self.runner.create_workflow("team_performance_report")

        # Add manager context
        builder.add_node(
            "PythonCodeNode",
            "manager_context",
            create_user_context_node(
                self.manager_user_id,
                "manager",
                ["view_team_reports", "export_analytics"],
            ),
        )

        # Validate report parameters
        validation_rules = {
            "department": {"required": True, "type": str},
            "period": {
                "required": True,
                "type": str,
                "pattern": "^(daily|weekly|monthly|quarterly|yearly)$",
            },
        }
        builder.add_node(
            "PythonCodeNode",
            "validate_params",
            create_validation_node(validation_rules),
        )
        builder.add_connection(
            "manager_context", "result", "validate_params", "context"
        )

        # Collect team performance metrics
        builder.add_node(
            "PythonCodeNode",
            "collect_performance_metrics",
            {
                "name": "collect_team_performance_data",
                "code": f"""
import random
from datetime import datetime, timedelta

# Collect team performance metrics
report_config = {report_config}
department = report_config.get("department", "Engineering")
period = report_config.get("period", "monthly")

# Generate realistic performance data
team_size = random.randint(15, 25)
days = 30 if period == "monthly" else 90 if period == "quarterly" else 7

performance_metrics = {{
    "report_metadata": {{
        "report_id": f"PERF_{{datetime.now().strftime('%Y%m%d_%H%M%S')}}",
        "generated_at": datetime.now().isoformat(),
        "generated_by": "{self.manager_user_id}",
        "department": department,
        "period": period,
        "date_range": {{
            "start": (datetime.now() - timedelta(days=days)).isoformat(),
            "end": datetime.now().isoformat()
        }}
    }},
    "team_overview": {{
        "total_members": team_size,
        "active_members": team_size - random.randint(0, 2),
        "on_leave": random.randint(0, 2),
        "new_hires": random.randint(0, 3),
        "departures": random.randint(0, 1)
    }},
    "productivity_metrics": {{
        "average_login_time": f"{{random.randint(8, 10)}}:{{random.randint(0, 59):02d}} AM",
        "average_logout_time": f"{{random.randint(5, 7)}}:{{random.randint(0, 59):02d}} PM",
        "average_active_hours": round(random.uniform(7.5, 8.5), 1),
        "system_utilization": round(random.uniform(75, 95), 1),
        "feature_adoption_rate": round(random.uniform(80, 98), 1)
    }},
    "goal_achievement": {{
        "team_goals_completed": random.randint(8, 12),
        "team_goals_total": 12,
        "completion_rate": round(random.uniform(75, 95), 1),
        "on_track_projects": random.randint(15, 20),
        "delayed_projects": random.randint(1, 3),
        "completed_projects": random.randint(10, 15)
    }},
    "training_metrics": {{
        "courses_completed": random.randint(30, 50),
        "avg_training_hours": round(random.uniform(2, 4), 1),
        "certification_rate": round(random.uniform(60, 85), 1),
        "skill_improvement_score": round(random.uniform(3.5, 4.5), 1)
    }}
}}

result = {{"result": performance_metrics}}
""",
            },
        )
        builder.add_connection(
            "validate_params", "result", "collect_performance_metrics", "validation"
        )

        # Generate trend analysis
        builder.add_node(
            "PythonCodeNode",
            "analyze_trends",
            {
                "name": "analyze_performance_trends",
                "code": """
import random
from datetime import datetime

# Analyze performance trends
# The input comes wrapped in 'result' from previous node
performance_data = collect_performance_metrics.get("result", collect_performance_metrics)

# Generate trend data for the past 6 periods
trend_analysis = {
    "productivity_trend": {
        "direction": "increasing" if random.random() > 0.3 else "stable",
        "change_percentage": round(random.uniform(-5, 15), 1),
        "forecast_next_period": round(random.uniform(85, 95), 1),
        "historical_data": [
            {"period": f"Period {i}", "value": round(random.uniform(75, 95), 1)}
            for i in range(6, 0, -1)
        ]
    },
    "team_growth_trend": {
        "growth_rate": round(random.uniform(5, 15), 1),
        "attrition_rate": round(random.uniform(2, 8), 1),
        "projected_team_size": performance_data.get("team_overview", {}).get("total_members", 20) + random.randint(1, 3),
        "hiring_recommendation": "maintain" if random.random() > 0.5 else "increase"
    },
    "skill_development_trend": {
        "overall_improvement": round(random.uniform(10, 25), 1),
        "top_skills_gained": ["Cloud Architecture", "Machine Learning", "DevOps", "Security"],
        "training_roi": round(random.uniform(150, 300), 1),
        "certification_trend": "increasing"
    },
    "engagement_trend": {
        "satisfaction_score": round(random.uniform(4.0, 4.8), 1),
        "engagement_index": round(random.uniform(75, 90), 1),
        "retention_probability": round(random.uniform(85, 95), 1),
        "morale_indicator": "positive"
    }
}

result = {"result": {
    "performance_metrics": performance_data,
    "trend_analysis": trend_analysis,
    "analysis_timestamp": datetime.now().isoformat()
}}
""",
            },
        )
        builder.add_connection(
            "collect_performance_metrics",
            "result",
            "analyze_trends",
            "collect_performance_metrics",
        )

        # Generate recommendations
        builder.add_node(
            "PythonCodeNode",
            "generate_recommendations",
            {
                "name": "generate_performance_recommendations",
                "code": """
from datetime import datetime, timedelta

# Generate actionable recommendations based on analysis
analysis_data = analyze_trends.get("result", analyze_trends)

recommendations = {
    "immediate_actions": [
        {
            "priority": "high",
            "category": "productivity",
            "recommendation": "Schedule team productivity workshop",
            "expected_impact": "10-15% productivity increase",
            "timeline": "Next 2 weeks"
        },
        {
            "priority": "medium",
            "category": "training",
            "recommendation": "Implement peer mentoring program",
            "expected_impact": "Faster skill development",
            "timeline": "Next month"
        }
    ],
    "long_term_strategies": [
        {
            "strategy": "Talent Development Pipeline",
            "description": "Create structured career paths for high performers",
            "expected_outcome": "Reduced attrition by 20%",
            "implementation_period": "6 months"
        },
        {
            "strategy": "Process Optimization",
            "description": "Automate routine tasks and workflows",
            "expected_outcome": "15% efficiency gain",
            "implementation_period": "3 months"
        }
    ],
    "risk_mitigation": [
        {
            "risk": "Key person dependency",
            "mitigation": "Cross-training on critical systems",
            "urgency": "high"
        },
        {
            "risk": "Skill gaps in emerging technologies",
            "mitigation": "Quarterly skill assessment and training",
            "urgency": "medium"
        }
    ]
}

# Compile final report
final_report = {
    **analysis_data,
    "recommendations": recommendations,
    "executive_summary": {
        "overall_health": "good" if analysis_data["trend_analysis"]["productivity_trend"]["direction"] == "increasing" else "moderate",
        "key_achievements": [
            "Team productivity above target",
            "High feature adoption rate",
            "Strong skill development progress"
        ],
        "areas_for_improvement": [
            "Project deadline adherence",
            "Cross-team collaboration",
            "Documentation quality"
        ],
        "next_review_date": (datetime.now() + timedelta(days=30)).isoformat()
    }
}

result = {"result": final_report}
""",
            },
        )
        builder.add_connection(
            "analyze_trends", "result", "generate_recommendations", "analyze_trends"
        )

        # Build and execute workflow
        workflow = builder.build()

        try:
            results, execution_id = self.runner.execute_workflow(
                workflow, report_config, "team_performance_report"
            )

            print("✅ Team Performance Report Generated Successfully!")
            if self.runner.enable_debug:
                report = results.get("generate_recommendations", {})
                print(
                    f"   Report ID: {report.get('performance_metrics', {}).get('report_metadata', {}).get('report_id', 'N/A')}"
                )
                print(
                    f"   Team Size: {report.get('performance_metrics', {}).get('team_overview', {}).get('total_members', 'N/A')}"
                )
                print(
                    f"   Overall Health: {report.get('executive_summary', {}).get('overall_health', 'N/A')}"
                )

            return results

        except Exception as e:
            print(f"❌ Failed to generate team performance report: {str(e)}")
            return {"error": str(e)}

    def generate_activity_monitoring_report(
        self, monitoring_config: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """
        Generate activity monitoring and compliance report.

        Args:
            monitoring_config: Monitoring configuration parameters

        Returns:
            Activity monitoring report results
        """
        print("🔍 Generating Activity Monitoring Report...")

        if not monitoring_config:
            monitoring_config = {
                "department": "Engineering",
                "time_range": "last_7_days",
                "include_anomalies": True,
                "include_compliance": True,
            }

        builder = self.runner.create_workflow("activity_monitoring_report")

        # Add manager context
        builder.add_node(
            "PythonCodeNode",
            "manager_context",
            create_user_context_node(
                self.manager_user_id,
                "manager",
                ["view_activity_logs", "monitor_compliance"],
            ),
        )

        # Collect activity data
        builder.add_node(
            "PythonCodeNode",
            "collect_activity_data",
            {
                "name": "collect_team_activity_data",
                "code": f"""
import random
from datetime import datetime, timedelta

# Collect team activity data
monitoring_config = {monitoring_config}
department = monitoring_config.get("department", "Engineering")
time_range = monitoring_config.get("time_range", "last_7_days")

# Generate activity data
team_members = [f"user{{i}}@company.com" for i in range(1, random.randint(15, 25))]

activity_data = {{
    "report_metadata": {{
        "report_id": f"ACT_{{datetime.now().strftime('%Y%m%d_%H%M%S')}}",
        "generated_at": datetime.now().isoformat(),
        "generated_by": "{self.manager_user_id}",
        "department": department,
        "time_range": time_range
    }},
    "access_patterns": {{
        "total_logins": random.randint(500, 800),
        "unique_users": len(team_members),
        "average_session_duration": f"{{random.randint(6, 8)}}h {{random.randint(0, 59)}}m",
        "peak_usage_hours": ["9:00-11:00 AM", "2:00-4:00 PM"],
        "weekend_activity": random.randint(20, 50)
    }},
    "system_usage": {{
        "most_used_features": [
            {{"feature": "Dashboard", "usage_count": random.randint(1000, 2000)}},
            {{"feature": "Reports", "usage_count": random.randint(500, 1000)}},
            {{"feature": "Team Management", "usage_count": random.randint(300, 600)}},
            {{"feature": "Analytics", "usage_count": random.randint(200, 400)}}
        ],
        "api_calls": random.randint(10000, 20000),
        "data_accessed_gb": round(random.uniform(50, 150), 2),
        "files_downloaded": random.randint(100, 300)
    }},
    "security_events": {{
        "failed_login_attempts": random.randint(5, 20),
        "password_resets": random.randint(2, 8),
        "mfa_challenges": random.randint(50, 100),
        "suspicious_activities": random.randint(0, 3)
    }},
    "compliance_metrics": {{
        "policy_violations": random.randint(0, 5),
        "access_reviews_completed": random.randint(10, 15),
        "training_compliance": round(random.uniform(85, 98), 1),
        "audit_readiness_score": round(random.uniform(90, 98), 1)
    }}
}}

# Identify anomalies
anomalies = []
if monitoring_config.get("include_anomalies", True):
    if random.random() > 0.7:
        anomalies.append({{
            "type": "unusual_access_pattern",
            "severity": "medium",
            "user": random.choice(team_members),
            "description": "Access from unusual location",
            "timestamp": (datetime.now() - timedelta(hours=random.randint(1, 48))).isoformat(),
            "action_taken": "MFA challenge issued"
        }})

    if random.random() > 0.8:
        anomalies.append({{
            "type": "high_data_access",
            "severity": "low",
            "user": random.choice(team_members),
            "description": "Above average data downloads",
            "timestamp": (datetime.now() - timedelta(hours=random.randint(1, 72))).isoformat(),
            "action_taken": "Monitoring increased"
        }})

activity_data["anomalies"] = anomalies

result = {{"result": activity_data}}
""",
            },
        )
        builder.add_connection(
            "manager_context", "result", "collect_activity_data", "context"
        )

        # Analyze compliance status
        builder.add_node(
            "PythonCodeNode",
            "analyze_compliance",
            {
                "name": "analyze_compliance_status",
                "code": """
import random
from datetime import datetime

# Analyze compliance and generate recommendations
activity_data = collect_activity_data.get("result", collect_activity_data)

compliance_analysis = {
    "overall_compliance_score": activity_data["compliance_metrics"]["audit_readiness_score"],
    "compliance_status": "compliant" if activity_data["compliance_metrics"]["audit_readiness_score"] > 90 else "needs_attention",
    "detailed_analysis": {
        "access_control": {
            "status": "good",
            "score": round(random.uniform(92, 98), 1),
            "findings": [
                "All access reviews completed on schedule",
                "Privileged access properly managed",
                "Regular permission audits conducted"
            ]
        },
        "data_protection": {
            "status": "good",
            "score": round(random.uniform(90, 96), 1),
            "findings": [
                "Data classification properly maintained",
                "Encryption standards met",
                "No unauthorized data exports detected"
            ]
        },
        "policy_adherence": {
            "status": "moderate" if activity_data["compliance_metrics"]["policy_violations"] > 2 else "good",
            "score": round(random.uniform(85, 95), 1),
            "findings": [
                f"{activity_data['compliance_metrics']['policy_violations']} minor policy violations detected",
                "All violations addressed within SLA",
                "Corrective training provided"
            ]
        },
        "audit_trail": {
            "status": "excellent",
            "score": round(random.uniform(95, 99), 1),
            "findings": [
                "Complete audit logs maintained",
                "No gaps in activity tracking",
                "Logs properly secured and retained"
            ]
        }
    },
    "recommendations": [
        {
            "area": "training",
            "recommendation": "Quarterly security awareness refresher",
            "priority": "medium",
            "impact": "Reduce policy violations by 50%"
        },
        {
            "area": "monitoring",
            "recommendation": "Implement automated anomaly detection",
            "priority": "high",
            "impact": "Faster threat detection and response"
        }
    ]
}

# Generate final report
final_report = {
    "activity_data": activity_data,
    "compliance_analysis": compliance_analysis,
    "executive_insights": {
        "key_findings": [
            "Team activity patterns remain consistent",
            "Compliance scores above industry benchmark",
            f"{len(activity_data['anomalies'])} anomalies detected and addressed"
        ],
        "risk_assessment": "low" if len(activity_data["anomalies"]) < 2 else "medium",
        "action_items": [
            "Review anomaly detection thresholds",
            "Update security training materials",
            "Schedule quarterly compliance review"
        ]
    },
    "report_generated": datetime.now().isoformat()
}

result = {"result": final_report}
""",
            },
        )
        builder.add_connection(
            "collect_activity_data",
            "result",
            "analyze_compliance",
            "collect_activity_data",
        )

        # Build and execute workflow
        workflow = builder.build()

        try:
            results, execution_id = self.runner.execute_workflow(
                workflow, monitoring_config, "activity_monitoring_report"
            )

            print("✅ Activity Monitoring Report Generated Successfully!")
            if self.runner.enable_debug:
                report = results.get("analyze_compliance", {})
                print(
                    f"   Compliance Score: {report.get('compliance_analysis', {}).get('overall_compliance_score', 'N/A')}%"
                )
                print(
                    f"   Anomalies Detected: {len(report.get('activity_data', {}).get('anomalies', []))}"
                )
                print(
                    f"   Risk Assessment: {report.get('executive_insights', {}).get('risk_assessment', 'N/A')}"
                )

            return results

        except Exception as e:
            print(f"❌ Failed to generate activity monitoring report: {str(e)}")
            return {"error": str(e)}

    def generate_custom_report(self, custom_config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate custom report based on manager specifications.

        Args:
            custom_config: Custom report configuration

        Returns:
            Custom report results
        """
        print("📈 Generating Custom Report...")

        builder = self.runner.create_workflow("custom_report")

        # Add manager context
        builder.add_node(
            "PythonCodeNode",
            "manager_context",
            create_user_context_node(
                self.manager_user_id,
                "manager",
                ["generate_custom_reports", "export_data"],
            ),
        )

        # Validate custom report parameters
        validation_rules = {
            "report_type": {"required": True, "type": str},
            "metrics": {"required": True, "type": list, "min_length": 1},
            "format": {"required": False, "type": str},
        }
        builder.add_node(
            "PythonCodeNode",
            "validate_custom",
            create_validation_node(validation_rules),
        )
        builder.add_connection(
            "manager_context", "result", "validate_custom", "context"
        )

        # Generate custom report
        builder.add_node(
            "PythonCodeNode",
            "generate_custom",
            {
                "name": "generate_custom_report_data",
                "code": f"""
import random
from datetime import datetime, timedelta

# Generate custom report based on configuration
custom_config = {custom_config}
report_type = custom_config.get("report_type", "custom")
metrics = custom_config.get("metrics", [])
export_format = custom_config.get("format", "json")

# Generate data for requested metrics
report_data = {{
    "report_metadata": {{
        "report_id": f"CUSTOM_{{datetime.now().strftime('%Y%m%d_%H%M%S')}}",
        "report_type": report_type,
        "generated_at": datetime.now().isoformat(),
        "generated_by": "{self.manager_user_id}",
        "export_format": export_format,
        "metrics_included": metrics
    }},
    "custom_metrics": {{}}
}}

# Generate data for each requested metric
for metric in metrics:
    if metric == "user_productivity":
        report_data["custom_metrics"]["user_productivity"] = {{
            "average_tasks_completed": random.randint(15, 25),
            "average_response_time": f"{{random.randint(1, 4)}}h",
            "efficiency_score": round(random.uniform(85, 95), 1),
            "top_performers": [f"user{{i}}@company.com" for i in range(1, 6)]
        }}
    elif metric == "system_performance":
        report_data["custom_metrics"]["system_performance"] = {{
            "uptime_percentage": round(random.uniform(99.5, 99.99), 2),
            "average_response_time_ms": random.randint(50, 200),
            "peak_concurrent_users": random.randint(100, 500),
            "resource_utilization": round(random.uniform(60, 85), 1)
        }}
    elif metric == "cost_analysis":
        report_data["custom_metrics"]["cost_analysis"] = {{
            "total_cost": round(random.uniform(10000, 50000), 2),
            "cost_per_user": round(random.uniform(50, 150), 2),
            "cost_trend": "decreasing" if random.random() > 0.5 else "stable",
            "roi_percentage": round(random.uniform(150, 300), 1)
        }}
    elif metric == "security_summary":
        report_data["custom_metrics"]["security_summary"] = {{
            "security_score": round(random.uniform(90, 98), 1),
            "vulnerabilities_found": random.randint(0, 5),
            "patches_applied": random.randint(10, 30),
            "incidents_resolved": random.randint(0, 3)
        }}
    else:
        # Generic metric data
        report_data["custom_metrics"][metric] = {{
            "value": round(random.uniform(50, 100), 1),
            "trend": "improving",
            "benchmark": "above_average",
            "data_points": [round(random.uniform(40, 100), 1) for _ in range(7)]
        }}

# Add export information
report_data["export_info"] = {{
    "format": export_format,
    "file_size_kb": random.randint(10, 100),
    "download_url": f"/api/v1/reports/download/{{report_data['report_metadata']['report_id']}}",
    "expiry": (datetime.now() + timedelta(days=7)).isoformat()
}}

result = {{"result": report_data}}
""",
            },
        )
        builder.add_connection(
            "validate_custom", "result", "generate_custom", "validation"
        )

        # Build and execute workflow
        workflow = builder.build()

        try:
            results, execution_id = self.runner.execute_workflow(
                workflow, custom_config, "custom_report"
            )

            print("✅ Custom Report Generated Successfully!")
            if self.runner.enable_debug:
                report = results.get("generate_custom", {})
                print(
                    f"   Report ID: {report.get('report_metadata', {}).get('report_id', 'N/A')}"
                )
                print(f"   Metrics Included: {len(report.get('custom_metrics', {}))}")
                print(
                    f"   Export Format: {report.get('export_info', {}).get('format', 'N/A')}"
                )

            return results

        except Exception as e:
            print(f"❌ Failed to generate custom report: {str(e)}")
            return {"error": str(e)}


def test_workflow(test_params: Optional[Dict[str, Any]] = None) -> bool:
    """
    Test the reporting and analytics workflow.

    Args:
        test_params: Optional test parameters

    Returns:
        True if tests pass, False otherwise
    """
    print("\n" + "=" * 60)
    print("TESTING REPORTING & ANALYTICS WORKFLOW")
    print("=" * 60)

    workflow = ReportingAnalyticsWorkflow("test_manager@company.com")

    # Test 1: Team Performance Report
    print("\n1️⃣ Testing Team Performance Report...")
    result = workflow.generate_team_performance_report(
        {"department": "Engineering", "period": "monthly", "include_trends": True}
    )

    if "error" in result:
        print(f"❌ Team performance report test failed: {result['error']}")
        return False

    # Test 2: Activity Monitoring Report
    print("\n2️⃣ Testing Activity Monitoring Report...")
    result = workflow.generate_activity_monitoring_report(
        {
            "department": "Engineering",
            "time_range": "last_7_days",
            "include_anomalies": True,
        }
    )

    if "error" in result:
        print(f"❌ Activity monitoring report test failed: {result['error']}")
        return False

    # Test 3: Custom Report
    print("\n3️⃣ Testing Custom Report Generation...")
    result = workflow.generate_custom_report(
        {
            "report_type": "quarterly_review",
            "metrics": ["user_productivity", "system_performance", "cost_analysis"],
            "format": "pdf",
        }
    )

    if "error" in result:
        print(f"❌ Custom report test failed: {result['error']}")
        return False

    # Print summary statistics
    workflow.runner.print_stats()

    print("\n✅ All reporting & analytics workflow tests passed!")
    return True


if __name__ == "__main__":
    # Run tests when script is executed directly
    success = test_workflow()
    exit(0 if success else 1)
