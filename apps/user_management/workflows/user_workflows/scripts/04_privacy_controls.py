#!/usr/bin/env python3
"""
User Workflow: Privacy Controls and Data Rights

This workflow handles privacy management including:
- Privacy settings configuration
- Data consent management
- GDPR rights exercise
- Privacy impact assessments
- Data sharing controls
"""

import sys
import os
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional

# Add shared utilities to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', 'shared'))

from workflow_runner import WorkflowRunner, create_user_context_node, create_validation_node


class PrivacyControlsWorkflow:
    """
    Complete privacy controls workflow for end users.
    """
    
    def __init__(self, user_id: str = "user"):
        """
        Initialize the privacy controls workflow.
        
        Args:
            user_id: ID of the user managing privacy settings
        """
        self.user_id = user_id
        self.runner = WorkflowRunner(
            user_type="user",
            user_id=user_id,
            enable_debug=True,
            enable_audit=False,  # Disable for testing
            enable_monitoring=True
        )
    
    def configure_privacy_settings(self, privacy_config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Configure comprehensive privacy settings.
        
        Args:
            privacy_config: Privacy configuration parameters
            
        Returns:
            Privacy configuration results
        """
        print(f"🔒 Configuring privacy settings for user: {self.user_id}")
        
        builder = self.runner.create_workflow("privacy_settings_configuration")
        
        # Validate privacy settings input
        validation_rules = {
            "data_collection_consent": {"required": True, "type": "str"},
            "marketing_consent": {"required": False, "type": "str"},
            "analytics_consent": {"required": False, "type": "str"},
            "profile_visibility": {"required": False, "type": "str"}
        }
        
        builder.add_node("PythonCodeNode", "validate_privacy_input", 
                        create_validation_node(validation_rules))
        
        # Configure comprehensive privacy controls
        builder.add_node("PythonCodeNode", "configure_privacy", {
            "name": "configure_user_privacy_settings",
            "code": f"""
from datetime import datetime, timedelta

# Configure comprehensive privacy settings
privacy_settings = {privacy_config}

# Data collection and processing consent
data_consent = {{
    "essential_data": {{
        "consent": "required",  # Cannot be disabled for system function
        "description": "Account information, authentication, security",
        "legal_basis": "legitimate_interest",
        "retention_period": "account_lifetime",
        "can_withdraw": False
    }},
    "functional_data": {{
        "consent": privacy_settings.get("data_collection_consent", "granted"),
        "description": "User preferences, settings, usage patterns",
        "legal_basis": "consent",
        "retention_period": "2_years",
        "can_withdraw": True
    }},
    "analytics_data": {{
        "consent": privacy_settings.get("analytics_consent", "denied"),
        "description": "Anonymized usage analytics, performance metrics",
        "legal_basis": "consent",
        "retention_period": "1_year",
        "can_withdraw": True
    }},
    "marketing_data": {{
        "consent": privacy_settings.get("marketing_consent", "denied"),
        "description": "Product updates, feature announcements",
        "legal_basis": "consent",
        "retention_period": "until_withdrawal",
        "can_withdraw": True
    }}
}}

# Profile and data sharing controls
sharing_controls = {{
    "profile_visibility": {{
        "setting": privacy_settings.get("profile_visibility", "team_only"),
        "options": ["private", "team_only", "department", "company"],
        "description": "Who can view your profile information"
    }},
    "contact_sharing": {{
        "setting": privacy_settings.get("contact_sharing", False),
        "description": "Allow other users to see your contact information"
    }},
    "activity_sharing": {{
        "setting": privacy_settings.get("activity_sharing", False),
        "description": "Share your activity status and availability"
    }},
    "directory_listing": {{
        "setting": privacy_settings.get("directory_listing", True),
        "description": "Include profile in company directory searches"
    }}
}}

# Data processing transparency
processing_transparency = {{
    "data_categories": [
        {{
            "category": "Identity Data",
            "examples": ["Name", "Email", "Employee ID"],
            "purpose": "Account management and authentication",
            "automated_decisions": False
        }},
        {{
            "category": "Usage Data", 
            "examples": ["Login times", "Feature usage", "Preferences"],
            "purpose": "Service improvement and personalization",
            "automated_decisions": True
        }},
        {{
            "category": "Technical Data",
            "examples": ["IP address", "Browser info", "Device info"],
            "purpose": "Security and technical functionality",
            "automated_decisions": True
        }}
    ],
    "third_party_sharing": {{
        "analytics_providers": data_consent["analytics_data"]["consent"] == "granted",
        "security_services": True,  # Required for system security
        "backup_services": True,   # Required for data protection
        "marketing_platforms": data_consent["marketing_data"]["consent"] == "granted"
    }},
    "international_transfers": {{
        "enabled": True,
        "safeguards": ["Standard Contractual Clauses", "Adequacy Decisions"],
        "countries": ["EU", "UK", "Canada"]
    }}
}}

# Privacy rights information
privacy_rights = {{
    "available_rights": [
        {{
            "right": "Access",
            "description": "Request copy of your personal data",
            "exercise_method": "Self-service dashboard",
            "response_time": "Immediate"
        }},
        {{
            "right": "Rectification",
            "description": "Correct inaccurate personal data",
            "exercise_method": "Profile settings or contact support",
            "response_time": "24 hours"
        }},
        {{
            "right": "Erasure",
            "description": "Request deletion of personal data",
            "exercise_method": "Contact support with verification",
            "response_time": "30 days"
        }},
        {{
            "right": "Portability",
            "description": "Export your data in machine-readable format",
            "exercise_method": "Data export tool",
            "response_time": "Immediate"
        }},
        {{
            "right": "Restriction",
            "description": "Limit processing of your personal data",
            "exercise_method": "Privacy settings or support request",
            "response_time": "48 hours"
        }},
        {{
            "right": "Objection",
            "description": "Object to processing based on legitimate interests",
            "exercise_method": "Privacy settings or support request",
            "response_time": "72 hours"
        }}
    ],
    "complaint_procedure": {{
        "internal_contact": "privacy@company.com",
        "dpo_contact": "dpo@company.com",
        "supervisory_authority": "Data Protection Commission",
        "response_timeline": "30 days"
    }}
}}

result = {{
    "result": {{
        "privacy_configured": True,
        "user_id": "{self.user_id}",
        "data_consent": data_consent,
        "sharing_controls": sharing_controls,
        "processing_transparency": processing_transparency,
        "privacy_rights": privacy_rights,
        "configuration_timestamp": datetime.now().isoformat(),
        "next_review_date": (datetime.now() + timedelta(days=365)).isoformat()
    }}
}}
"""
        })
        
        # Generate privacy dashboard
        builder.add_node("PythonCodeNode", "generate_privacy_dashboard", {
            "name": "generate_user_privacy_dashboard",
            "code": """
# Generate user privacy dashboard
privacy_config = privacy_configuration

# Privacy score calculation
privacy_score = 0
consent_settings = privacy_config.get("data_consent", {})
sharing_settings = privacy_config.get("sharing_controls", {})

# Score based on restrictive settings (higher = more private)
if consent_settings.get("analytics_data", {}).get("consent") == "denied":
    privacy_score += 20
if consent_settings.get("marketing_data", {}).get("consent") == "denied":
    privacy_score += 20
if sharing_settings.get("profile_visibility", {}).get("setting") == "private":
    privacy_score += 25
elif sharing_settings.get("profile_visibility", {}).get("setting") == "team_only":
    privacy_score += 15
if not sharing_settings.get("contact_sharing", {}).get("setting", False):
    privacy_score += 15
if not sharing_settings.get("activity_sharing", {}).get("setting", False):
    privacy_score += 20

# Privacy recommendations
recommendations = []
if privacy_score < 50:
    recommendations.append({
        "priority": "medium",
        "action": "Review data sharing settings",
        "description": "Consider limiting profile visibility and contact sharing",
        "impact": "Increased privacy protection"
    })

if consent_settings.get("analytics_data", {}).get("consent") == "granted":
    recommendations.append({
        "priority": "low",
        "action": "Consider disabling analytics",
        "description": "You can opt out of usage analytics while maintaining full functionality",
        "impact": "Reduced data collection"
    })

if consent_settings.get("marketing_data", {}).get("consent") == "granted":
    recommendations.append({
        "priority": "low", 
        "action": "Review marketing preferences",
        "description": "Fine-tune which communications you receive",
        "impact": "Reduced communication volume"
    })

# Data minimization status
data_minimization = {
    "status": "good" if privacy_score >= 70 else "moderate" if privacy_score >= 40 else "needs_improvement",
    "score": privacy_score,
    "collected_data_types": 4,  # Based on consent settings
    "shared_data_points": sum(1 for setting in sharing_settings.values() if isinstance(setting, dict) and setting.get("setting")),
    "retention_compliance": "full",
    "purpose_limitation": "enforced"
}

# Recent privacy activity
recent_activity = [
    {
        "timestamp": datetime.now().isoformat(),
        "action": "Privacy settings updated",
        "category": "configuration",
        "details": "User updated privacy preferences"
    },
    {
        "timestamp": (datetime.now() - timedelta(days=30)).isoformat(),
        "action": "Data export requested",
        "category": "rights_exercise",
        "details": "Personal data export completed"
    },
    {
        "timestamp": (datetime.now() - timedelta(days=60)).isoformat(),
        "action": "Consent reviewed",
        "category": "consent_management",
        "details": "Annual privacy review completed"
    }
]

# Privacy dashboard
dashboard = {
    "privacy_score": privacy_score,
    "privacy_level": "high" if privacy_score >= 80 else "medium" if privacy_score >= 50 else "low",
    "data_minimization": data_minimization,
    "active_consents": len([c for c in consent_settings.values() if isinstance(c, dict) and c.get("consent") == "granted"]),
    "exercised_rights_count": 2,  # Based on recent activity
    "recommendations": recommendations,
    "recent_activity": recent_activity,
    "last_review": datetime.now().isoformat(),
    "next_review": (datetime.now() + timedelta(days=365)).isoformat()
}

result = {
    "result": {
        "dashboard_generated": True,
        "privacy_dashboard": dashboard,
        "actionable_insights": len(recommendations),
        "privacy_health": "good" if privacy_score >= 60 else "needs_attention"
    }
}
"""
        })
        
        # Connect privacy configuration nodes
        builder.add_connection("validate_privacy_input", "result", "configure_privacy", "validation_result")
        builder.add_connection("configure_privacy", "result.result", "generate_privacy_dashboard", "privacy_configuration")
        
        # Execute workflow
        workflow = builder.build()
        results, execution_id = self.runner.execute_workflow(
            workflow, privacy_config, "privacy_settings_configuration"
        )
        
        return results
    
    def manage_data_rights(self, rights_request: Dict[str, Any]) -> Dict[str, Any]:
        """
        Manage GDPR and privacy rights requests.
        
        Args:
            rights_request: Rights request parameters
            
        Returns:
            Rights management results
        """
        print(f"⚖️ Processing data rights request for user: {self.user_id}")
        
        builder = self.runner.create_workflow("data_rights_management")
        
        # Process rights request
        builder.add_node("PythonCodeNode", "process_rights_request", {
            "name": "process_user_rights_request",
            "code": f"""
# Process user data rights request
request_data = {rights_request}
right_type = request_data.get("right_type", "access")
request_reason = request_data.get("reason", "")

# Define available rights and their processing
available_rights = {{
    "access": {{
        "description": "Right to access personal data",
        "processing_time": "immediate",
        "automated": True,
        "requires_verification": False,
        "fee": None
    }},
    "rectification": {{
        "description": "Right to correct inaccurate data",
        "processing_time": "24_hours",
        "automated": False,
        "requires_verification": True,
        "fee": None
    }},
    "erasure": {{
        "description": "Right to deletion (right to be forgotten)",
        "processing_time": "30_days",
        "automated": False,
        "requires_verification": True,
        "fee": None
    }},
    "portability": {{
        "description": "Right to data portability",
        "processing_time": "immediate",
        "automated": True,
        "requires_verification": False,
        "fee": None
    }},
    "restriction": {{
        "description": "Right to restrict processing",
        "processing_time": "48_hours",
        "automated": False,
        "requires_verification": True,
        "fee": None
    }},
    "objection": {{
        "description": "Right to object to processing",
        "processing_time": "72_hours",
        "automated": False,
        "requires_verification": True,
        "fee": None
    }}
}}

# Validate rights request
if right_type not in available_rights:
    rights_processing = {{
        "status": "invalid",
        "message": f"Unknown right type: {{right_type}}",
        "available_rights": list(available_rights.keys())
    }}
else:
    right_info = available_rights[right_type]
    
    # Create rights request record
    request_record = {{
        "request_id": f"DR-{{datetime.now().strftime('%Y%m%d')}}-{{"{self.user_id}"[:8]}}",
        "user_id": "{self.user_id}",
        "right_type": right_type,
        "description": right_info["description"],
        "reason": request_reason,
        "submitted_at": datetime.now().isoformat(),
        "status": "submitted",
        "processing_time": right_info["processing_time"],
        "requires_verification": right_info["requires_verification"],
        "automated_processing": right_info["automated"],
        "estimated_completion": (
            datetime.now() + timedelta(days=30) if right_info["processing_time"] == "30_days"
            else datetime.now() + timedelta(hours=72) if right_info["processing_time"] == "72_hours"
            else datetime.now() + timedelta(hours=48) if right_info["processing_time"] == "48_hours"
            else datetime.now() + timedelta(hours=24) if right_info["processing_time"] == "24_hours"
            else datetime.now()
        ).isoformat()
    }}
    
    # Process specific rights
    if right_type == "access":
        # Data access - immediate processing
        access_data = {{
            "personal_data": {{
                "identity": {{"name": "User Name", "email": "{self.user_id}@company.com"}},
                "profile": {{"department": "Engineering", "position": "Developer"}},
                "usage": {{"last_login": datetime.now().isoformat(), "login_count": 245}},
                "preferences": {{"theme": "dark", "language": "en", "notifications": True}}
            }},
            "processing_activities": [
                {{"purpose": "Account management", "legal_basis": "contract", "retention": "account_lifetime"}},
                {{"purpose": "Service provision", "legal_basis": "legitimate_interest", "retention": "2_years"}},
                {{"purpose": "Security monitoring", "legal_basis": "legitimate_interest", "retention": "1_year"}}
            ],
            "data_sources": ["User registration", "Profile updates", "System logs"],
            "data_recipients": ["Internal systems", "Security providers", "Backup services"],
            "export_format": "JSON",
            "export_timestamp": datetime.now().isoformat()
        }}
        request_record["access_data"] = access_data
        request_record["status"] = "completed"
    
    elif right_type == "portability":
        # Data portability - immediate processing
        portable_data = {{
            "user_data": {{
                "profile_information": {{"name": "User Name", "email": "{self.user_id}@company.com"}},
                "preferences": {{"theme": "dark", "language": "en"}},
                "created_content": {{"documents": 15, "comments": 42}},
                "activity_history": {{"logins": 245, "features_used": 28}}
            }},
            "export_format": "JSON",
            "machine_readable": True,
            "structured_format": True,
            "includes_metadata": True,
            "export_timestamp": datetime.now().isoformat()
        }}
        request_record["portable_data"] = portable_data
        request_record["status"] = "completed"
    
    elif right_type in ["rectification", "erasure", "restriction", "objection"]:
        # Rights requiring manual review
        request_record["status"] = "under_review"
        request_record["review_process"] = {{
            "verification_required": True,
            "legal_assessment": True,
            "technical_feasibility": True,
            "impact_assessment": True
        }}
    
    rights_processing = {{
        "status": "processed",
        "request_record": request_record,
        "message": f"{{right_info['description']}} request has been {{request_record['status']}}"
    }}

result = {{
    "result": {{
        "rights_request_processed": rights_processing["status"] == "processed",
        "request_details": rights_processing,
        "estimated_completion": request_record.get("estimated_completion"),
        "immediate_fulfillment": right_type in ["access", "portability"],
        "requires_follow_up": right_type in ["rectification", "erasure", "restriction", "objection"]
    }}
}}
"""
        })
        
        # Generate rights fulfillment
        builder.add_node("PythonCodeNode", "fulfill_rights_request", {
            "name": "fulfill_data_rights_request",
            "code": """
# Fulfill the data rights request
rights_processing = rights_request_processing

if rights_processing.get("rights_request_processed"):
    request_details = rights_processing.get("request_details", {})
    request_record = request_details.get("request_record", {})
    right_type = request_record.get("right_type")
    
    # Generate fulfillment documentation
    fulfillment = {
        "request_id": request_record.get("request_id"),
        "fulfillment_timestamp": datetime.now().isoformat(),
        "fulfillment_method": "automated" if request_record.get("automated_processing") else "manual",
        "compliance_status": "fulfilled",
        "legal_basis_review": "completed",
        "data_subject_notified": True
    }
    
    # Type-specific fulfillment
    if right_type == "access":
        fulfillment.update({
            "data_provided": True,
            "format": "structured_json",
            "completeness": "full",
            "delivery_method": "secure_download"
        })
    
    elif right_type == "portability":
        fulfillment.update({
            "data_exported": True,
            "format": "machine_readable_json",
            "portability_compliant": True,
            "delivery_method": "secure_download"
        })
    
    elif right_type in ["rectification", "erasure", "restriction", "objection"]:
        fulfillment.update({
            "review_completed": True,
            "legal_assessment": "approved",
            "technical_implementation": "scheduled",
            "timeline": request_record.get("estimated_completion")
        })
    
    # Audit trail
    audit_trail = {
        "request_received": request_record.get("submitted_at"),
        "initial_assessment": datetime.now().isoformat(),
        "verification_completed": datetime.now().isoformat() if not request_record.get("requires_verification") else None,
        "processing_started": datetime.now().isoformat(),
        "fulfillment_completed": datetime.now().isoformat() if right_type in ["access", "portability"] else None,
        "data_subject_notification": datetime.now().isoformat()
    }
    
    # Follow-up actions
    follow_up_actions = []
    if right_type == "erasure":
        follow_up_actions.extend([
            "Schedule data deletion across all systems",
            "Verify deletion completion",
            "Update data retention records",
            "Notify third parties if applicable"
        ])
    elif right_type == "restriction":
        follow_up_actions.extend([
            "Flag data for processing restriction",
            "Update system access controls",
            "Notify relevant departments"
        ])
    
else:
    fulfillment = {"error": "Rights request could not be processed"}
    audit_trail = {}
    follow_up_actions = []

result = {
    "result": {
        "fulfillment_completed": rights_processing.get("rights_request_processed", False),
        "fulfillment_details": fulfillment,
        "audit_trail": audit_trail,
        "follow_up_actions": follow_up_actions,
        "compliance_confirmed": True
    }
}
"""
        })
        
        # Connect rights management nodes
        builder.add_connection("process_rights_request", "result.result", "fulfill_rights_request", "rights_request_processing")
        
        # Execute workflow
        workflow = builder.build()
        results, execution_id = self.runner.execute_workflow(
            workflow, rights_request, "data_rights_management"
        )
        
        return results
    
    def conduct_privacy_impact_assessment(self, assessment_trigger: Dict[str, Any]) -> Dict[str, Any]:
        """
        Conduct privacy impact assessment for user activities.
        
        Args:
            assessment_trigger: Assessment trigger parameters
            
        Returns:
            Privacy impact assessment results
        """
        print(f"📊 Conducting privacy impact assessment for user: {self.user_id}")
        
        builder = self.runner.create_workflow("privacy_impact_assessment")
        
        # Assess privacy impact
        builder.add_node("PythonCodeNode", "assess_privacy_impact", {
            "name": "conduct_privacy_impact_assessment",
            "code": f"""
# Conduct comprehensive privacy impact assessment
trigger_data = {assessment_trigger}
assessment_type = trigger_data.get("type", "routine")
trigger_event = trigger_data.get("event", "profile_update")

# Privacy impact factors
impact_factors = {{
    "data_volume": {{
        "current_data_points": 45,
        "new_data_points": trigger_data.get("new_data_points", 0),
        "total_after_change": 45 + trigger_data.get("new_data_points", 0),
        "sensitivity_level": "medium"
    }},
    "processing_purposes": {{
        "current_purposes": ["account_management", "service_provision", "security"],
        "new_purposes": trigger_data.get("new_purposes", []),
        "purpose_expansion": len(trigger_data.get("new_purposes", [])) > 0
    }},
    "data_sharing": {{
        "current_recipients": ["internal_systems", "security_providers"],
        "new_recipients": trigger_data.get("new_recipients", []),
        "external_sharing_increase": any("external" in r for r in trigger_data.get("new_recipients", []))
    }},
    "retention_changes": {{
        "current_retention": "2_years",
        "new_retention": trigger_data.get("new_retention"),
        "retention_extended": trigger_data.get("new_retention") == "extended"
    }},
    "automation_level": {{
        "current_automation": "medium",
        "new_automation": trigger_data.get("automation_level", "medium"),
        "increased_automation": trigger_data.get("automation_level") == "high"
    }}
}}

# Risk assessment
risk_assessment = {{
    "data_protection_risks": [],
    "privacy_risks": [],
    "compliance_risks": [],
    "mitigation_measures": []
}}

# Assess specific risks
if impact_factors["data_volume"]["total_after_change"] > 100:
    risk_assessment["data_protection_risks"].append({{
        "risk": "Large data volume processing",
        "severity": "medium",
        "likelihood": "high",
        "impact": "Data breach exposure increased"
    }})
    risk_assessment["mitigation_measures"].append("Implement additional encryption")

if impact_factors["data_sharing"]["external_sharing_increase"]:
    risk_assessment["privacy_risks"].append({{
        "risk": "Increased external data sharing",
        "severity": "high",
        "likelihood": "medium",
        "impact": "Reduced user control over data"
    }})
    risk_assessment["mitigation_measures"].append("Obtain explicit consent for external sharing")

if impact_factors["automation_level"]["increased_automation"]:
    risk_assessment["compliance_risks"].append({{
        "risk": "Automated decision making without human oversight",
        "severity": "medium",
        "likelihood": "high",
        "impact": "GDPR Article 22 compliance issues"
    }})
    risk_assessment["mitigation_measures"].append("Implement human review process")

# Calculate overall risk score
risk_score = 0
risk_score += len(risk_assessment["data_protection_risks"]) * 20
risk_score += len(risk_assessment["privacy_risks"]) * 25
risk_score += len(risk_assessment["compliance_risks"]) * 30
risk_score = min(risk_score, 100)

# Assessment outcome
assessment_outcome = {{
    "overall_risk_level": "high" if risk_score >= 70 else "medium" if risk_score >= 40 else "low",
    "risk_score": risk_score,
    "requires_dpo_review": risk_score >= 60,
    "requires_consultation": risk_score >= 80,
    "acceptable_risk": risk_score < 40,
    "recommended_actions": risk_assessment["mitigation_measures"]
}}

# Legal basis validation
legal_basis_check = {{
    "current_basis": "consent_and_legitimate_interest",
    "basis_adequate": True,
    "requires_new_consent": impact_factors["processing_purposes"]["purpose_expansion"],
    "consent_mechanism": "granular_opt_in" if impact_factors["processing_purposes"]["purpose_expansion"] else "existing_sufficient"
}}

# Data subject impact
data_subject_impact = {{
    "transparency_affected": impact_factors["processing_purposes"]["purpose_expansion"],
    "control_reduced": impact_factors["data_sharing"]["external_sharing_increase"],
    "notification_required": risk_score >= 50,
    "consent_renewal_needed": legal_basis_check["requires_new_consent"],
    "rights_affected": ["information", "access"] if impact_factors["processing_purposes"]["purpose_expansion"] else []
}}

result = {{
    "result": {{
        "assessment_completed": True,
        "user_id": "{self.user_id}",
        "assessment_timestamp": datetime.now().isoformat(),
        "trigger_event": trigger_event,
        "impact_factors": impact_factors,
        "risk_assessment": risk_assessment,
        "assessment_outcome": assessment_outcome,
        "legal_basis_check": legal_basis_check,
        "data_subject_impact": data_subject_impact,
        "next_review_date": (datetime.now() + timedelta(days=180)).isoformat()
    }}
}}
"""
        })
        
        # Generate compliance recommendations
        builder.add_node("PythonCodeNode", "generate_compliance_recommendations", {
            "name": "generate_privacy_compliance_recommendations",
            "code": """
# Generate privacy compliance recommendations
pia_results = privacy_impact_assessment

if pia_results.get("assessment_completed"):
    assessment_outcome = pia_results.get("assessment_outcome", {})
    risk_level = assessment_outcome.get("overall_risk_level")
    data_subject_impact = pia_results.get("data_subject_impact", {})
    
    # Generate recommendations based on risk level
    recommendations = []
    
    if risk_level == "high":
        recommendations.extend([
            {
                "priority": "critical",
                "action": "Conduct DPO consultation",
                "description": "High risk identified, Data Protection Officer review required",
                "timeline": "immediate",
                "compliance_requirement": "GDPR Article 35"
            },
            {
                "priority": "critical",
                "action": "Implement additional safeguards",
                "description": "Deploy enhanced technical and organizational measures",
                "timeline": "7_days",
                "compliance_requirement": "GDPR Article 32"
            }
        ])
    
    if risk_level in ["high", "medium"]:
        recommendations.extend([
            {
                "priority": "high",
                "action": "Update privacy notice",
                "description": "Inform data subjects of processing changes",
                "timeline": "14_days",
                "compliance_requirement": "GDPR Article 13-14"
            },
            {
                "priority": "high",
                "action": "Document compliance measures",
                "description": "Record all implemented privacy protection measures",
                "timeline": "30_days",
                "compliance_requirement": "GDPR Article 5(2)"
            }
        ])
    
    # Consent management recommendations
    if data_subject_impact.get("consent_renewal_needed"):
        recommendations.append({
            "priority": "high",
            "action": "Obtain renewed consent",
            "description": "New processing purposes require explicit consent",
            "timeline": "before_implementation",
            "compliance_requirement": "GDPR Article 6-7"
        })
    
    # Rights management recommendations  
    if data_subject_impact.get("rights_affected"):
        recommendations.append({
            "priority": "medium",
            "action": "Update rights procedures",
            "description": "Ensure data subject rights remain exercisable",
            "timeline": "14_days",
            "compliance_requirement": "GDPR Chapter 3"
        })
    
    # Compliance monitoring
    monitoring_plan = {
        "regular_reviews": {
            "frequency": "quarterly" if risk_level == "high" else "annually",
            "scope": "full_privacy_impact",
            "responsibility": "privacy_team"
        },
        "key_metrics": [
            "Data volume growth",
            "Purpose creep incidents", 
            "Rights request volume",
            "Consent withdrawal rate",
            "Security incident frequency"
        ],
        "alert_thresholds": {
            "data_volume_increase": "25%",
            "rights_requests_increase": "50%",
            "consent_withdrawal_rate": "10%"
        }
    }
    
    # Implementation roadmap
    implementation_roadmap = [
        {
            "phase": "immediate",
            "actions": [r for r in recommendations if r["priority"] == "critical"],
            "duration": "1-7 days"
        },
        {
            "phase": "short_term", 
            "actions": [r for r in recommendations if r["priority"] == "high"],
            "duration": "1-4 weeks"
        },
        {
            "phase": "medium_term",
            "actions": [r for r in recommendations if r["priority"] == "medium"],
            "duration": "1-3 months"
        }
    ]

else:
    recommendations = []
    monitoring_plan = {}
    implementation_roadmap = []

result = {
    "result": {
        "recommendations_generated": len(recommendations) > 0,
        "total_recommendations": len(recommendations),
        "critical_actions": len([r for r in recommendations if r["priority"] == "critical"]),
        "compliance_recommendations": recommendations,
        "monitoring_plan": monitoring_plan,
        "implementation_roadmap": implementation_roadmap,
        "compliance_status": "requires_action" if len(recommendations) > 0 else "compliant"
    }
}
"""
        })
        
        # Connect privacy assessment nodes
        builder.add_connection("assess_privacy_impact", "result.result", "generate_compliance_recommendations", "privacy_impact_assessment")
        
        # Execute workflow
        workflow = builder.build()
        results, execution_id = self.runner.execute_workflow(
            workflow, assessment_trigger, "privacy_impact_assessment"
        )
        
        return results
    
    def run_comprehensive_privacy_demo(self) -> Dict[str, Any]:
        """
        Run a comprehensive demonstration of all privacy control operations.
        
        Returns:
            Complete demonstration results
        """
        print("🚀 Starting Comprehensive Privacy Controls Demonstration...")
        print("=" * 70)
        
        demo_results = {}
        
        try:
            # 1. Configure privacy settings
            print("\n1. Configuring Privacy Settings...")
            privacy_config = {
                "data_collection_consent": "granted",
                "marketing_consent": "denied",
                "analytics_consent": "denied",
                "profile_visibility": "team_only",
                "contact_sharing": False,
                "activity_sharing": False
            }
            demo_results["privacy_configuration"] = self.configure_privacy_settings(privacy_config)
            
            # 2. Process data rights request
            print("\n2. Processing Data Rights Request...")
            rights_request = {
                "right_type": "access",
                "reason": "Want to review my personal data"
            }
            demo_results["rights_management"] = self.manage_data_rights(rights_request)
            
            # 3. Conduct privacy impact assessment
            print("\n3. Conducting Privacy Impact Assessment...")
            assessment_trigger = {
                "type": "profile_update",
                "event": "new_feature_adoption",
                "new_data_points": 5,
                "new_purposes": ["personalization"],
                "automation_level": "medium"
            }
            demo_results["privacy_assessment"] = self.conduct_privacy_impact_assessment(assessment_trigger)
            
            # Print comprehensive summary
            self.print_privacy_summary(demo_results)
            
            return demo_results
            
        except Exception as e:
            print(f"❌ Privacy controls demonstration failed: {str(e)}")
            raise
    
    def print_privacy_summary(self, results: Dict[str, Any]):
        """
        Print a comprehensive privacy controls summary.
        
        Args:
            results: Privacy controls results from all workflows
        """
        print("\n" + "=" * 70)
        print("PRIVACY CONTROLS DEMONSTRATION COMPLETE")
        print("=" * 70)
        
        # Privacy configuration summary
        config_result = results.get("privacy_configuration", {}).get("generate_privacy_dashboard", {}).get("result", {}).get("result", {})
        privacy_dashboard = config_result.get("privacy_dashboard", {})
        print(f"🔒 Privacy Score: {privacy_dashboard.get('privacy_score', 0)}/100 ({privacy_dashboard.get('privacy_level', 'unknown')})")
        
        # Rights management summary
        rights_result = results.get("rights_management", {}).get("process_rights_request", {}).get("result", {}).get("result", {})
        print(f"⚖️ Rights Request: {rights_result.get('request_details', {}).get('request_record', {}).get('status', 'unknown')}")
        
        # Privacy assessment summary
        assessment_result = results.get("privacy_assessment", {}).get("assess_privacy_impact", {}).get("result", {}).get("result", {})
        risk_level = assessment_result.get("assessment_outcome", {}).get("overall_risk_level", "unknown")
        print(f"📊 Privacy Risk: {risk_level} risk level identified")
        
        print("\n🎉 All privacy control operations completed successfully!")
        print("=" * 70)
        
        # Print execution statistics
        self.runner.print_stats()


def test_workflow(test_params: Optional[Dict[str, Any]] = None) -> bool:
    """
    Test the privacy controls workflow.
    
    Args:
        test_params: Optional test parameters
        
    Returns:
        True if test passes, False otherwise
    """
    try:
        print("🧪 Testing Privacy Controls Workflow...")
        
        # Create test workflow
        privacy_controls = PrivacyControlsWorkflow("test_user")
        
        # Test privacy configuration
        test_privacy_config = {
            "data_collection_consent": "granted",
            "marketing_consent": "denied",
            "analytics_consent": "denied",
            "profile_visibility": "private"
        }
        
        result = privacy_controls.configure_privacy_settings(test_privacy_config)
        if not result.get("configure_privacy", {}).get("result", {}).get("result", {}).get("privacy_configured"):
            return False
        
        print("✅ Privacy controls workflow test passed")
        return True
        
    except Exception as e:
        print(f"❌ Privacy controls workflow test failed: {str(e)}")
        return False


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--test":
        # Run test
        success = test_workflow()
        sys.exit(0 if success else 1)
    else:
        # Run comprehensive demonstration
        privacy_controls = PrivacyControlsWorkflow()
        
        try:
            results = privacy_controls.run_comprehensive_privacy_demo()
            print("🎉 Privacy controls demonstration completed successfully!")
        except Exception as e:
            print(f"❌ Demonstration failed: {str(e)}")
            sys.exit(1)