#!/usr/bin/env python3
"""
Admin Workflow: Security Management and Threat Detection

This workflow handles comprehensive security operations including:
- Security policy enforcement
- Threat detection and analysis
- Access control auditing
- Security incident response
- Compliance monitoring
"""

import os
import sys
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

# Add shared utilities to path
sys.path.append(os.path.join(os.path.dirname(__file__), "..", "..", "shared"))

from workflow_runner import WorkflowRunner, create_user_context_node


class SecurityManagementWorkflow:
    """
    Complete security management workflow for administrators.
    """

    def __init__(self, admin_user_id: str = "admin"):
        """
        Initialize the security management workflow.

        Args:
            admin_user_id: ID of the administrator performing security operations
        """
        self.admin_user_id = admin_user_id
        self.runner = WorkflowRunner(
            user_type="admin",
            user_id=admin_user_id,
            enable_debug=True,
            enable_audit=False,  # Disable for testing
            enable_monitoring=True,
        )

    def monitor_security_threats(
        self, monitoring_config: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """
        Monitor and analyze security threats across the system.

        Args:
            monitoring_config: Optional monitoring configuration

        Returns:
            Security monitoring results
        """
        print("🛡️ Monitoring Security Threats...")

        if not monitoring_config:
            monitoring_config = {
                "time_range": "last_24_hours",
                "threat_levels": ["high", "critical"],
                "include_analysis": True,
            }

        builder = self.runner.create_workflow("security_threat_monitoring")

        # Add user context for admin operations
        builder.add_node(
            "PythonCodeNode",
            "admin_context",
            create_user_context_node(
                self.admin_user_id, "admin", ["security_admin", "system_admin"]
            ),
        )

        # Collect security events and threats
        builder.add_node(
            "PythonCodeNode",
            "collect_security_events",
            {
                "name": "collect_security_threat_data",
                "code": f"""
from datetime import datetime, timedelta

# Collect comprehensive security threat data
monitoring_config = {monitoring_config}
time_range = monitoring_config.get("time_range", "last_24_hours")

# Security events from last 24 hours (simulated data)
security_events = [
    {{
        "event_id": "SEC-001",
        "timestamp": (datetime.now() - timedelta(hours=2)).isoformat(),
        "event_type": "failed_login_attempts",
        "severity": "medium",
        "source_ip": "192.168.1.150",
        "target_user": "john.doe@company.com",
        "details": "5 consecutive failed login attempts",
        "status": "active",
        "auto_actions": ["account_locked"],
        "investigation_required": True
    }},
    {{
        "event_id": "SEC-002",
        "timestamp": (datetime.now() - timedelta(hours=6)).isoformat(),
        "event_type": "suspicious_permission_escalation",
        "severity": "high",
        "source_user": "temp.contractor@company.com",
        "target_resource": "admin_panel",
        "details": "Attempted access to admin functions without proper role",
        "status": "blocked",
        "auto_actions": ["access_denied", "alert_sent"],
        "investigation_required": True
    }},
    {{
        "event_id": "SEC-003",
        "timestamp": (datetime.now() - timedelta(hours=8)).isoformat(),
        "event_type": "unusual_login_location",
        "severity": "medium",
        "source_ip": "89.45.234.12",
        "source_location": "Unknown - Russia",
        "target_user": "alice.manager@company.com",
        "details": "Login from unusual geographic location",
        "status": "flagged",
        "auto_actions": ["mfa_required", "notification_sent"],
        "investigation_required": False
    }},
    {{
        "event_id": "SEC-004",
        "timestamp": (datetime.now() - timedelta(hours=12)).isoformat(),
        "event_type": "data_export_anomaly",
        "severity": "high",
        "source_user": "finance.user@company.com",
        "details": "Large volume data export outside normal hours",
        "export_size": "2.3GB",
        "export_type": "user_data",
        "status": "under_review",
        "auto_actions": ["export_quarantined", "manager_notified"],
        "investigation_required": True
    }},
    {{
        "event_id": "SEC-005",
        "timestamp": (datetime.now() - timedelta(hours=18)).isoformat(),
        "event_type": "brute_force_attack",
        "severity": "critical",
        "source_ip": "45.123.67.89",
        "attack_vector": "API_endpoint",
        "target_endpoint": "/api/auth/login",
        "attempt_count": 247,
        "status": "mitigated",
        "auto_actions": ["ip_blocked", "rate_limit_enforced"],
        "investigation_required": False
    }}
]

# Threat analysis and categorization
threat_categories = {{
    "authentication_attacks": {{
        "events": [e for e in security_events if e["event_type"] in ["failed_login_attempts", "brute_force_attack"]],
        "risk_level": "high",
        "mitigation_status": "active"
    }},
    "authorization_violations": {{
        "events": [e for e in security_events if e["event_type"] in ["suspicious_permission_escalation"]],
        "risk_level": "high",
        "mitigation_status": "blocked"
    }},
    "behavioral_anomalies": {{
        "events": [e for e in security_events if e["event_type"] in ["unusual_login_location", "data_export_anomaly"]],
        "risk_level": "medium",
        "mitigation_status": "monitoring"
    }},
    "infrastructure_attacks": {{
        "events": [e for e in security_events if e["event_type"] in ["brute_force_attack"]],
        "risk_level": "critical",
        "mitigation_status": "mitigated"
    }}
}}

# Security metrics
security_metrics = {{
    "total_events": len(security_events),
    "critical_events": len([e for e in security_events if e["severity"] == "critical"]),
    "high_severity_events": len([e for e in security_events if e["severity"] == "high"]),
    "events_requiring_investigation": len([e for e in security_events if e["investigation_required"]]),
    "auto_mitigated_events": len([e for e in security_events if e["status"] in ["blocked", "mitigated"]]),
    "active_threats": len([e for e in security_events if e["status"] == "active"]),
    "average_response_time": "4.2 minutes"
}}

# System security posture
security_posture = {{
    "overall_status": "secure_with_alerts",
    "threat_level": "elevated",
    "defensive_measures": {{
        "firewall_status": "active",
        "intrusion_detection": "active",
        "rate_limiting": "enforced",
        "geo_blocking": "enabled",
        "mfa_enforcement": "active"
    }},
    "security_score": 85,  # Out of 100
    "last_assessment": datetime.now().isoformat()
}}

result = {{
    "result": {{
        "monitoring_successful": True,
        "time_range": time_range,
        "security_events": security_events,
        "threat_categories": threat_categories,
        "security_metrics": security_metrics,
        "security_posture": security_posture,
        "analysis_timestamp": datetime.now().isoformat()
    }}
}}
""",
            },
        )

        # Analyze threats and generate recommendations
        builder.add_node(
            "PythonCodeNode",
            "analyze_threats",
            {
                "name": "analyze_security_threats",
                "code": """
# Analyze security threats and generate actionable recommendations
security_data = security_monitoring_data

if security_data.get("monitoring_successful"):
    security_events = security_data.get("security_events", [])
    threat_categories = security_data.get("threat_categories", {})
    security_metrics = security_data.get("security_metrics", {})

    # Threat analysis
    threat_analysis = {
        "immediate_threats": [],
        "emerging_patterns": [],
        "risk_assessment": {},
        "recommended_actions": []
    }

    # Identify immediate threats
    for event in security_events:
        if event.get("severity") == "critical" or event.get("status") == "active":
            threat_analysis["immediate_threats"].append({
                "event_id": event["event_id"],
                "type": event["event_type"],
                "severity": event["severity"],
                "requires_action": event.get("investigation_required", False),
                "priority": "immediate" if event["severity"] == "critical" else "high"
            })

    # Pattern analysis
    ip_attempts = {}
    user_violations = {}
    for event in security_events:
        # Track IP-based attacks
        if "source_ip" in event:
            ip = event["source_ip"]
            ip_attempts[ip] = ip_attempts.get(ip, 0) + 1

        # Track user-based violations
        if "target_user" in event or "source_user" in event:
            user = event.get("target_user") or event.get("source_user")
            if user:
                user_violations[user] = user_violations.get(user, 0) + 1

    # Identify concerning patterns
    if any(count >= 3 for count in ip_attempts.values()):
        threat_analysis["emerging_patterns"].append({
            "pattern": "repeated_ip_attacks",
            "description": "Multiple security events from same IP addresses",
            "affected_ips": [ip for ip, count in ip_attempts.items() if count >= 3],
            "recommendation": "Consider extended IP blocking"
        })

    if any(count >= 2 for count in user_violations.values()):
        threat_analysis["emerging_patterns"].append({
            "pattern": "user_security_violations",
            "description": "Multiple security events involving same users",
            "affected_users": [user for user, count in user_violations.items() if count >= 2],
            "recommendation": "Review user access and provide security training"
        })

    # Risk assessment
    total_events = security_metrics.get("total_events", 0)
    critical_events = security_metrics.get("critical_events", 0)
    active_threats = security_metrics.get("active_threats", 0)

    risk_score = 0
    if critical_events > 0:
        risk_score += critical_events * 30
    if active_threats > 0:
        risk_score += active_threats * 20
    if total_events > 10:
        risk_score += 15

    risk_score = min(risk_score, 100)

    threat_analysis["risk_assessment"] = {
        "current_risk_score": risk_score,
        "risk_level": "critical" if risk_score >= 80 else "high" if risk_score >= 60 else "medium" if risk_score >= 30 else "low",
        "factors": {
            "critical_events": critical_events,
            "active_threats": active_threats,
            "total_events": total_events
        },
        "trend": "increasing" if active_threats > 0 else "stable"
    }

    # Generate recommendations
    recommendations = []

    if critical_events > 0:
        recommendations.append({
            "priority": "immediate",
            "category": "incident_response",
            "action": "Activate incident response team",
            "description": f"{critical_events} critical security events require immediate attention",
            "timeline": "within 30 minutes"
        })

    if active_threats > 0:
        recommendations.append({
            "priority": "high",
            "category": "threat_mitigation",
            "action": "Implement additional security controls",
            "description": f"{active_threats} active threats need immediate containment",
            "timeline": "within 2 hours"
        })

    if len(threat_analysis["emerging_patterns"]) > 0:
        recommendations.append({
            "priority": "medium",
            "category": "pattern_analysis",
            "action": "Investigate security patterns",
            "description": "Emerging threat patterns detected requiring investigation",
            "timeline": "within 24 hours"
        })

    if risk_score >= 60:
        recommendations.append({
            "priority": "high",
            "category": "security_posture",
            "action": "Enhance security measures",
            "description": "Current risk level requires additional security controls",
            "timeline": "within 48 hours"
        })

    threat_analysis["recommended_actions"] = recommendations

else:
    threat_analysis = {"error": "Security monitoring failed"}

result = {
    "result": {
        "analysis_completed": security_data.get("monitoring_successful", False),
        "threat_analysis": threat_analysis,
        "analysis_confidence": "high",
        "next_analysis_due": (datetime.now() + timedelta(hours=4)).isoformat()
    }
}
""",
            },
        )

        # Connect security monitoring nodes
        builder.add_connection(
            "admin_context", "result", "collect_security_events", "context"
        )
        builder.add_connection(
            "collect_security_events",
            "result.result",
            "analyze_threats",
            "security_monitoring_data",
        )

        # Execute workflow
        workflow = builder.build()
        results, execution_id = self.runner.execute_workflow(
            workflow, monitoring_config, "security_threat_monitoring"
        )

        return results

    def manage_access_controls(
        self, access_config: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """
        Manage and audit access controls across the system.

        Args:
            access_config: Access control configuration

        Returns:
            Access control management results
        """
        print("🔐 Managing Access Controls...")

        if not access_config:
            access_config = {
                "audit_scope": "all_users",
                "check_compliance": True,
                "generate_recommendations": True,
            }

        builder = self.runner.create_workflow("access_control_management")

        # Audit current access controls
        builder.add_node(
            "PythonCodeNode",
            "audit_access_controls",
            {
                "name": "audit_system_access_controls",
                "code": f"""
# Comprehensive access control audit
audit_config = {access_config}

# User access audit (simulated data)
user_access_audit = [
    {{
        "user_id": "john.doe@company.com",
        "roles": ["employee", "team_lead"],
        "permissions": ["user_read", "team_manage", "report_generate"],
        "last_access": (datetime.now() - timedelta(hours=3)).isoformat(),
        "access_anomalies": [],
        "compliance_status": "compliant",
        "risk_score": 15
    }},
    {{
        "user_id": "alice.manager@company.com",
        "roles": ["manager", "department_admin"],
        "permissions": ["user_read", "user_create", "dept_manage", "budget_approve"],
        "last_access": (datetime.now() - timedelta(hours=1)).isoformat(),
        "access_anomalies": ["excessive_permissions"],
        "compliance_status": "review_required",
        "risk_score": 45
    }},
    {{
        "user_id": "temp.contractor@company.com",
        "roles": ["contractor", "temporary"],
        "permissions": ["limited_read"],
        "last_access": (datetime.now() - timedelta(days=30)).isoformat(),
        "access_anomalies": ["stale_account", "unused_access"],
        "compliance_status": "non_compliant",
        "risk_score": 75
    }},
    {{
        "user_id": "admin@company.com",
        "roles": ["super_admin", "system_admin"],
        "permissions": ["*"],  # All permissions
        "last_access": (datetime.now() - timedelta(minutes=15)).isoformat(),
        "access_anomalies": [],
        "compliance_status": "compliant",
        "risk_score": 30  # Higher due to privileged access
    }}
]

# Role and permission analysis
role_analysis = {{
    "total_roles": 8,
    "system_roles": ["super_admin", "system_admin", "department_admin", "manager"],
    "business_roles": ["employee", "team_lead", "contractor", "temporary"],
    "orphaned_roles": ["old_intern_role"],  # Roles with no users
    "overprivileged_roles": ["department_admin"],  # Roles with excessive permissions
    "role_hierarchy_issues": []
}}

# Permission matrix analysis
permission_analysis = {{
    "total_permissions": 45,
    "critical_permissions": ["user_delete", "system_config", "security_admin"],
    "unused_permissions": ["legacy_feature_access"],
    "permission_conflicts": [],
    "segregation_violations": [
        {{
            "violation": "user_create_and_audit",
            "description": "Users with both create and audit permissions",
            "affected_users": ["alice.manager@company.com"]
        }}
    ]
}}

# Compliance analysis
compliance_analysis = {{
    "compliant_users": len([u for u in user_access_audit if u["compliance_status"] == "compliant"]),
    "non_compliant_users": len([u for u in user_access_audit if u["compliance_status"] == "non_compliant"]),
    "users_requiring_review": len([u for u in user_access_audit if u["compliance_status"] == "review_required"]),
    "compliance_percentage": (len([u for u in user_access_audit if u["compliance_status"] == "compliant"]) / len(user_access_audit)) * 100,
    "major_violations": [
        {{
            "violation_type": "stale_accounts",
            "count": 1,
            "severity": "high",
            "description": "Accounts unused for >30 days"
        }},
        {{
            "violation_type": "excessive_permissions",
            "count": 1,
            "severity": "medium",
            "description": "Users with more permissions than role requires"
        }}
    ]
}}

# Access patterns and risks
access_patterns = {{
    "unusual_access_times": [
        {{
            "user": "finance.user@company.com",
            "pattern": "weekend_access",
            "risk_level": "medium",
            "description": "Accessing sensitive data outside business hours"
        }}
    ],
    "permission_escalations": [
        {{
            "user": "temp.contractor@company.com",
            "escalation": "attempted_admin_access",
            "timestamp": (datetime.now() - timedelta(hours=6)).isoformat(),
            "blocked": True
        }}
    ],
    "cross_department_access": [
        {{
            "user": "hr.specialist@company.com",
            "accessed_department": "finance",
            "justification": "salary_review_process",
            "approved": True
        }}
    ]
}}

result = {{
    "result": {{
        "audit_completed": True,
        "audit_timestamp": datetime.now().isoformat(),
        "user_access_audit": user_access_audit,
        "role_analysis": role_analysis,
        "permission_analysis": permission_analysis,
        "compliance_analysis": compliance_analysis,
        "access_patterns": access_patterns,
        "total_users_audited": len(user_access_audit)
    }}
}}
""",
            },
        )

        # Generate access control recommendations
        builder.add_node(
            "PythonCodeNode",
            "generate_access_recommendations",
            {
                "name": "generate_access_control_recommendations",
                "code": """
# Generate comprehensive access control recommendations
access_audit = access_control_audit

if access_audit.get("audit_completed"):
    user_audit = access_audit.get("user_access_audit", [])
    compliance_analysis = access_audit.get("compliance_analysis", {})
    role_analysis = access_audit.get("role_analysis", {})
    permission_analysis = access_audit.get("permission_analysis", {})
    access_patterns = access_audit.get("access_patterns", {})

    # Priority recommendations
    recommendations = []

    # Critical security recommendations
    non_compliant_count = compliance_analysis.get("non_compliant_users", 0)
    if non_compliant_count > 0:
        recommendations.append({
            "priority": "critical",
            "category": "compliance",
            "title": "Address Non-Compliant User Accounts",
            "description": f"{non_compliant_count} user accounts are non-compliant with security policies",
            "actions": [
                "Review and disable stale accounts",
                "Validate contractor access permissions",
                "Update role assignments based on current responsibilities"
            ],
            "timeline": "immediate",
            "risk_reduction": 60
        })

    # Role management recommendations
    if role_analysis.get("orphaned_roles"):
        recommendations.append({
            "priority": "medium",
            "category": "role_management",
            "title": "Clean Up Orphaned Roles",
            "description": f"Found {len(role_analysis.get('orphaned_roles', []))} roles with no assigned users",
            "actions": [
                "Archive unused roles",
                "Document role lifecycle management",
                "Implement role usage monitoring"
            ],
            "timeline": "within_week",
            "risk_reduction": 20
        })

    # Permission optimization
    if permission_analysis.get("segregation_violations"):
        recommendations.append({
            "priority": "high",
            "category": "permission_segregation",
            "title": "Resolve Segregation of Duties Violations",
            "description": "Users have conflicting permissions that violate segregation principles",
            "actions": [
                "Split conflicting permissions into separate roles",
                "Implement approval workflows for sensitive operations",
                "Regular review of permission combinations"
            ],
            "timeline": "within_month",
            "risk_reduction": 40
        })

    # Behavioral monitoring
    if access_patterns.get("unusual_access_times"):
        recommendations.append({
            "priority": "medium",
            "category": "behavioral_monitoring",
            "title": "Monitor Unusual Access Patterns",
            "description": "Users accessing systems outside normal business hours",
            "actions": [
                "Implement time-based access controls",
                "Require justification for off-hours access",
                "Enhanced monitoring for weekend/holiday access"
            ],
            "timeline": "within_month",
            "risk_reduction": 25
        })

    # Compliance improvements
    compliance_percentage = compliance_analysis.get("compliance_percentage", 0)
    if compliance_percentage < 90:
        recommendations.append({
            "priority": "high",
            "category": "compliance_improvement",
            "title": "Improve Overall Compliance Rate",
            "description": f"Current compliance rate is {compliance_percentage:.1f}%, target is 95%+",
            "actions": [
                "Implement automated compliance checking",
                "Regular access reviews and certifications",
                "Enhanced user training on security policies"
            ],
            "timeline": "ongoing",
            "risk_reduction": 35
        })

    # Implementation plan
    implementation_plan = {
        "immediate_actions": [r for r in recommendations if r["priority"] == "critical"],
        "short_term_actions": [r for r in recommendations if r["priority"] == "high"],
        "medium_term_actions": [r for r in recommendations if r["priority"] == "medium"],
        "total_risk_reduction": sum(r.get("risk_reduction", 0) for r in recommendations)
    }

    # Monitoring and measurement
    monitoring_plan = {
        "key_metrics": [
            "Compliance percentage",
            "Average user risk score",
            "Number of segregation violations",
            "Stale account count",
            "Permission escalation attempts"
        ],
        "review_frequency": "weekly",
        "automated_alerts": [
            "New segregation violations",
            "Accounts inactive >30 days",
            "Failed permission escalations",
            "Compliance drops below 90%"
        ],
        "reporting_schedule": {
            "weekly": "Compliance summary",
            "monthly": "Full access review",
            "quarterly": "Risk assessment update"
        }
    }

else:
    recommendations = []
    implementation_plan = {}
    monitoring_plan = {}

result = {
    "result": {
        "recommendations_generated": len(recommendations) > 0,
        "total_recommendations": len(recommendations),
        "critical_actions": len([r for r in recommendations if r["priority"] == "critical"]),
        "access_recommendations": recommendations,
        "implementation_plan": implementation_plan,
        "monitoring_plan": monitoring_plan,
        "estimated_risk_reduction": implementation_plan.get("total_risk_reduction", 0)
    }
}
""",
            },
        )

        # Connect access control management nodes
        builder.add_connection(
            "audit_access_controls",
            "result.result",
            "generate_access_recommendations",
            "access_control_audit",
        )

        # Execute workflow
        workflow = builder.build()
        results, execution_id = self.runner.execute_workflow(
            workflow, access_config, "access_control_management"
        )

        return results

    def conduct_security_assessment(
        self, assessment_scope: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """
        Conduct comprehensive security assessment of the system.

        Args:
            assessment_scope: Assessment configuration and scope

        Returns:
            Security assessment results
        """
        print("📋 Conducting Security Assessment...")

        if not assessment_scope:
            assessment_scope = {
                "assessment_type": "comprehensive",
                "include_penetration_testing": False,
                "compliance_frameworks": ["GDPR", "SOC2"],
            }

        builder = self.runner.create_workflow("security_assessment")

        # Comprehensive security assessment
        builder.add_node(
            "PythonCodeNode",
            "assess_security_posture",
            {
                "name": "conduct_comprehensive_security_assessment",
                "code": f"""
# Conduct comprehensive security assessment
assessment_config = {assessment_scope}
assessment_type = assessment_config.get("assessment_type", "comprehensive")

# Infrastructure security assessment
infrastructure_assessment = {{
    "network_security": {{
        "firewall_configuration": "properly_configured",
        "intrusion_detection": "active_and_monitoring",
        "network_segmentation": "implemented",
        "vpn_security": "strong_encryption",
        "score": 85
    }},
    "server_security": {{
        "operating_system_hardening": "completed",
        "patch_management": "up_to_date",
        "service_configuration": "secure_defaults",
        "access_controls": "properly_configured",
        "score": 90
    }},
    "database_security": {{
        "encryption_at_rest": "enabled",
        "encryption_in_transit": "enabled",
        "access_controls": "role_based",
        "backup_security": "encrypted_and_tested",
        "score": 92
    }},
    "application_security": {{
        "secure_coding_practices": "followed",
        "vulnerability_scanning": "regular",
        "dependency_management": "automated",
        "security_headers": "implemented",
        "score": 88
    }}
}}

# Identity and access management assessment
iam_assessment = {{
    "authentication": {{
        "password_policy": "strong_requirements",
        "multi_factor_auth": "enforced_for_admin",
        "account_lockout": "configured",
        "session_management": "secure",
        "score": 87
    }},
    "authorization": {{
        "role_based_access": "implemented",
        "principle_least_privilege": "enforced",
        "segregation_duties": "partial_compliance",
        "access_reviews": "quarterly",
        "score": 82
    }},
    "user_lifecycle": {{
        "onboarding_process": "documented",
        "offboarding_process": "automated",
        "access_provisioning": "workflow_based",
        "periodic_reviews": "scheduled",
        "score": 85
    }}
}}

# Data protection assessment
data_protection_assessment = {{
    "data_classification": {{
        "classification_scheme": "implemented",
        "data_labeling": "partial",
        "handling_procedures": "documented",
        "retention_policies": "defined",
        "score": 80
    }},
    "privacy_controls": {{
        "consent_management": "implemented",
        "data_subject_rights": "supported",
        "privacy_by_design": "adopted",
        "cross_border_transfers": "compliant",
        "score": 88
    }},
    "backup_recovery": {{
        "backup_encryption": "enabled",
        "recovery_testing": "regular",
        "offsite_storage": "implemented",
        "rpo_rto_defined": True,
        "score": 90
    }}
}}

# Compliance assessment
compliance_frameworks = assessment_config.get("compliance_frameworks", ["GDPR"])
compliance_assessment = {{}}

for framework in compliance_frameworks:
    if framework == "GDPR":
        compliance_assessment["GDPR"] = {{
            "lawful_basis": "documented",
            "consent_mechanisms": "implemented",
            "data_subject_rights": "supported",
            "breach_notification": "procedures_in_place",
            "dpo_appointment": "completed",
            "privacy_impact_assessments": "conducted",
            "compliance_score": 85
        }}
    elif framework == "SOC2":
        compliance_assessment["SOC2"] = {{
            "security": "type_2_compliant",
            "availability": "monitoring_in_place",
            "processing_integrity": "controls_implemented",
            "confidentiality": "encryption_enforced",
            "privacy": "policies_documented",
            "compliance_score": 82
        }}

# Incident response assessment
incident_response_assessment = {{
    "incident_response_plan": {{
        "plan_documented": True,
        "roles_defined": True,
        "communication_procedures": "established",
        "escalation_matrix": "defined",
        "score": 85
    }},
    "incident_detection": {{
        "monitoring_tools": "deployed",
        "alerting_mechanisms": "configured",
        "log_analysis": "automated",
        "threat_intelligence": "integrated",
        "score": 88
    }},
    "incident_response": {{
        "response_team": "trained",
        "containment_procedures": "documented",
        "forensic_capabilities": "available",
        "recovery_procedures": "tested",
        "score": 83
    }}
}}

# Calculate overall security score
category_scores = [
    infrastructure_assessment["network_security"]["score"],
    infrastructure_assessment["server_security"]["score"],
    infrastructure_assessment["database_security"]["score"],
    infrastructure_assessment["application_security"]["score"],
    iam_assessment["authentication"]["score"],
    iam_assessment["authorization"]["score"],
    iam_assessment["user_lifecycle"]["score"],
    data_protection_assessment["data_classification"]["score"],
    data_protection_assessment["privacy_controls"]["score"],
    data_protection_assessment["backup_recovery"]["score"],
    incident_response_assessment["incident_response_plan"]["score"],
    incident_response_assessment["incident_detection"]["score"],
    incident_response_assessment["incident_response"]["score"]
]

overall_security_score = sum(category_scores) / len(category_scores)

# Security maturity level
if overall_security_score >= 90:
    maturity_level = "optimized"
elif overall_security_score >= 80:
    maturity_level = "managed"
elif overall_security_score >= 70:
    maturity_level = "defined"
elif overall_security_score >= 60:
    maturity_level = "repeatable"
else:
    maturity_level = "initial"

result = {{
    "result": {{
        "assessment_completed": True,
        "assessment_timestamp": datetime.now().isoformat(),
        "assessment_type": assessment_type,
        "overall_security_score": round(overall_security_score, 1),
        "security_maturity_level": maturity_level,
        "infrastructure_assessment": infrastructure_assessment,
        "iam_assessment": iam_assessment,
        "data_protection_assessment": data_protection_assessment,
        "compliance_assessment": compliance_assessment,
        "incident_response_assessment": incident_response_assessment,
        "next_assessment_due": (datetime.now() + timedelta(days=90)).isoformat()
    }}
}}
""",
            },
        )

        # Generate security improvement roadmap
        builder.add_node(
            "PythonCodeNode",
            "generate_security_roadmap",
            {
                "name": "generate_security_improvement_roadmap",
                "code": """
# Generate comprehensive security improvement roadmap
security_assessment = security_assessment_results

if security_assessment.get("assessment_completed"):
    overall_score = security_assessment.get("overall_security_score", 0)
    maturity_level = security_assessment.get("security_maturity_level", "initial")

    # Identify improvement areas
    improvement_areas = []

    # Infrastructure improvements
    infra = security_assessment.get("infrastructure_assessment", {})
    for category, details in infra.items():
        if details.get("score", 0) < 85:
            improvement_areas.append({
                "category": "infrastructure",
                "subcategory": category,
                "current_score": details.get("score", 0),
                "target_score": 90,
                "priority": "high" if details.get("score", 0) < 75 else "medium"
            })

    # IAM improvements
    iam = security_assessment.get("iam_assessment", {})
    for category, details in iam.items():
        if details.get("score", 0) < 85:
            improvement_areas.append({
                "category": "identity_access_management",
                "subcategory": category,
                "current_score": details.get("score", 0),
                "target_score": 90,
                "priority": "high" if details.get("score", 0) < 75 else "medium"
            })

    # Data protection improvements
    data_protection = security_assessment.get("data_protection_assessment", {})
    for category, details in data_protection.items():
        if details.get("score", 0) < 85:
            improvement_areas.append({
                "category": "data_protection",
                "subcategory": category,
                "current_score": details.get("score", 0),
                "target_score": 90,
                "priority": "high" if details.get("score", 0) < 75 else "medium"
            })

    # Generate specific recommendations
    security_recommendations = []

    # High priority recommendations
    if overall_score < 85:
        security_recommendations.append({
            "priority": "high",
            "category": "overall_security",
            "title": "Improve Overall Security Posture",
            "description": f"Current security score ({overall_score:.1f}) is below target (85+)",
            "specific_actions": [
                "Address all identified vulnerabilities",
                "Implement missing security controls",
                "Enhance monitoring and detection capabilities",
                "Conduct security training for all staff"
            ],
            "timeline": "3 months",
            "expected_improvement": 10
        })

    # Compliance-specific recommendations
    compliance_assessment = security_assessment.get("compliance_assessment", {})
    for framework, details in compliance_assessment.items():
        compliance_score = details.get("compliance_score", 0)
        if compliance_score < 90:
            security_recommendations.append({
                "priority": "high",
                "category": "compliance",
                "title": f"Improve {framework} Compliance",
                "description": f"{framework} compliance score ({compliance_score}) needs improvement",
                "specific_actions": [
                    f"Address {framework} compliance gaps",
                    "Update policies and procedures",
                    "Implement additional controls",
                    "Conduct compliance training"
                ],
                "timeline": "2 months",
                "expected_improvement": 15
            })

    # Incident response improvements
    ir_assessment = security_assessment.get("incident_response_assessment", {})
    ir_scores = [details.get("score", 0) for details in ir_assessment.values()]
    avg_ir_score = sum(ir_scores) / len(ir_scores) if ir_scores else 0

    if avg_ir_score < 85:
        security_recommendations.append({
            "priority": "medium",
            "category": "incident_response",
            "title": "Enhance Incident Response Capabilities",
            "description": "Incident response maturity needs improvement",
            "specific_actions": [
                "Update incident response procedures",
                "Conduct tabletop exercises",
                "Enhance detection capabilities",
                "Improve forensic tools and training"
            ],
            "timeline": "4 months",
            "expected_improvement": 8
        })

    # Implementation roadmap
    roadmap = {
        "phase_1": {
            "duration": "0-3 months",
            "focus": "Critical security gaps",
            "actions": [r for r in security_recommendations if r["priority"] == "high"],
            "success_metrics": ["Security score >85", "Zero critical vulnerabilities"]
        },
        "phase_2": {
            "duration": "3-6 months",
            "focus": "Process improvements",
            "actions": [r for r in security_recommendations if r["priority"] == "medium"],
            "success_metrics": ["Security score >90", "Full compliance achieved"]
        },
        "phase_3": {
            "duration": "6-12 months",
            "focus": "Optimization and automation",
            "actions": [r for r in security_recommendations if r["priority"] == "low"],
            "success_metrics": ["Optimized maturity level", "Automated security processes"]
        }
    }

    # Investment analysis
    investment_analysis = {
        "estimated_budget": {
            "technology_investments": "$75,000",
            "training_and_certification": "$25,000",
            "external_consulting": "$50,000",
            "total": "$150,000"
        },
        "expected_roi": {
            "risk_reduction": "60%",
            "incident_cost_savings": "$200,000/year",
            "compliance_cost_avoidance": "$100,000/year",
            "productivity_gains": "$50,000/year"
        },
        "payback_period": "6 months"
    }

else:
    improvement_areas = []
    security_recommendations = []
    roadmap = {}
    investment_analysis = {}

result = {
    "result": {
        "roadmap_generated": security_assessment.get("assessment_completed", False),
        "improvement_areas": improvement_areas,
        "security_recommendations": security_recommendations,
        "implementation_roadmap": roadmap,
        "investment_analysis": investment_analysis,
        "total_recommendations": len(security_recommendations),
        "estimated_improvement": sum(r.get("expected_improvement", 0) for r in security_recommendations)
    }
}
""",
            },
        )

        # Connect security assessment nodes
        builder.add_connection(
            "assess_security_posture",
            "result.result",
            "generate_security_roadmap",
            "security_assessment_results",
        )

        # Execute workflow
        workflow = builder.build()
        results, execution_id = self.runner.execute_workflow(
            workflow, assessment_scope, "security_assessment"
        )

        return results

    def run_comprehensive_security_demo(self) -> Dict[str, Any]:
        """
        Run a comprehensive demonstration of all security management operations.

        Returns:
            Complete demonstration results
        """
        print("🚀 Starting Comprehensive Security Management Demonstration...")
        print("=" * 70)

        demo_results = {}

        try:
            # 1. Monitor security threats
            print("\n1. Monitoring Security Threats...")
            monitoring_config = {
                "time_range": "last_24_hours",
                "threat_levels": ["high", "critical"],
                "include_analysis": True,
            }
            demo_results["threat_monitoring"] = self.monitor_security_threats(
                monitoring_config
            )

            # 2. Manage access controls
            print("\n2. Managing Access Controls...")
            access_config = {
                "audit_scope": "all_users",
                "check_compliance": True,
                "generate_recommendations": True,
            }
            demo_results["access_control"] = self.manage_access_controls(access_config)

            # 3. Conduct security assessment
            print("\n3. Conducting Security Assessment...")
            assessment_scope = {
                "assessment_type": "comprehensive",
                "include_penetration_testing": False,
                "compliance_frameworks": ["GDPR", "SOC2"],
            }
            demo_results["security_assessment"] = self.conduct_security_assessment(
                assessment_scope
            )

            # Print comprehensive summary
            self.print_security_summary(demo_results)

            return demo_results

        except Exception as e:
            print(f"❌ Security management demonstration failed: {str(e)}")
            raise

    def print_security_summary(self, results: Dict[str, Any]):
        """
        Print a comprehensive security management summary.

        Args:
            results: Security management results from all workflows
        """
        print("\n" + "=" * 70)
        print("SECURITY MANAGEMENT DEMONSTRATION COMPLETE")
        print("=" * 70)

        # Threat monitoring summary
        threat_result = (
            results.get("threat_monitoring", {})
            .get("collect_security_events", {})
            .get("result", {})
            .get("result", {})
        )
        security_metrics = threat_result.get("security_metrics", {})
        print(
            f"🛡️ Threats: {security_metrics.get('total_events', 0)} events, {security_metrics.get('critical_events', 0)} critical"
        )

        # Access control summary
        access_result = (
            results.get("access_control", {})
            .get("audit_access_controls", {})
            .get("result", {})
            .get("result", {})
        )
        compliance_analysis = access_result.get("compliance_analysis", {})
        print(
            f"🔐 Access: {compliance_analysis.get('compliance_percentage', 0):.1f}% compliant users"
        )

        # Security assessment summary
        assessment_result = (
            results.get("security_assessment", {})
            .get("assess_security_posture", {})
            .get("result", {})
            .get("result", {})
        )
        overall_score = assessment_result.get("overall_security_score", 0)
        maturity_level = assessment_result.get("security_maturity_level", "unknown")
        print(
            f"📋 Assessment: {overall_score}/100 security score ({maturity_level} maturity)"
        )

        print("\n🎉 All security management operations completed successfully!")
        print("=" * 70)

        # Print execution statistics
        self.runner.print_stats()


def test_workflow(test_params: Optional[Dict[str, Any]] = None) -> bool:
    """
    Test the security management workflow.

    Args:
        test_params: Optional test parameters

    Returns:
        True if test passes, False otherwise
    """
    try:
        print("🧪 Testing Security Management Workflow...")

        # Create test workflow
        security_mgmt = SecurityManagementWorkflow("test_admin")

        # Test threat monitoring
        result = security_mgmt.monitor_security_threats()
        if (
            not result.get("collect_security_events", {})
            .get("result", {})
            .get("result", {})
            .get("monitoring_successful")
        ):
            return False

        print("✅ Security management workflow test passed")
        return True

    except Exception as e:
        print(f"❌ Security management workflow test failed: {str(e)}")
        return False


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--test":
        # Run test
        success = test_workflow()
        sys.exit(0 if success else 1)
    else:
        # Run comprehensive demonstration
        security_mgmt = SecurityManagementWorkflow()

        try:
            results = security_mgmt.run_comprehensive_security_demo()
            print("🎉 Security management demonstration completed successfully!")
        except Exception as e:
            print(f"❌ Demonstration failed: {str(e)}")
            sys.exit(1)
