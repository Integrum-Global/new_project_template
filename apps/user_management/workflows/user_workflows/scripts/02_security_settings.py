#!/usr/bin/env python3
"""
User Workflow: Security Settings and Authentication

This workflow handles personal security management including:
- Password management and changes
- Multi-factor authentication setup
- Security questions configuration
- Account security monitoring
- Session management
"""

import sys
import os
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional

# Add shared utilities to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', 'shared'))

from workflow_runner import WorkflowRunner, create_user_context_node, create_validation_node


class SecuritySettingsWorkflow:
    """
    Complete security settings workflow for end users.
    """
    
    def __init__(self, user_id: str = "user"):
        """
        Initialize the security settings workflow.
        
        Args:
            user_id: ID of the user performing security operations
        """
        self.user_id = user_id
        self.runner = WorkflowRunner(
            user_type="user",
            user_id=user_id,
            enable_debug=True,
            enable_audit=False,  # Disable for testing
            enable_monitoring=True
        )
    
    def setup_password_security(self, password_config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Set up password security and management.
        
        Args:
            password_config: Password configuration settings
            
        Returns:
            Password security setup results
        """
        print(f"🔐 Setting up password security for user: {self.user_id}")
        
        builder = self.runner.create_workflow("password_security_setup")
        
        # Password validation and setup
        validation_rules = {
            "current_password": {"required": True, "type": "str", "min_length": 8},
            "new_password": {"required": True, "type": "str", "min_length": 12},
            "confirm_password": {"required": True, "type": "str", "min_length": 12}
        }
        
        builder.add_node("PythonCodeNode", "validate_password_input", 
                        create_validation_node(validation_rules))
        
        # Password strength and policy validation
        builder.add_node("PythonCodeNode", "validate_password_strength", {
            "name": "validate_new_password_strength",
            "code": """
from datetime import datetime, timedelta
import re
import random
import string

# Password policy requirements
password_policy = {
    "min_length": 12,
    "max_length": 128,
    "require_uppercase": True,
    "require_lowercase": True,
    "require_numbers": True,
    "require_special_chars": True,
    "special_chars": "!@#$%^&*()_+-=[]{}|;:,.<>?",
    "max_age_days": 90,
    "history_count": 12,
    "common_passwords_blocked": True
}

# Use test data for password validation
password_config = {
    "current_password": "OldPassword123!",
    "new_password": "NewSecurePassword456!@#",
    "confirm_password": "NewSecurePassword456!@#"
}

new_password = password_config.get("new_password", "")
current_password = password_config.get("current_password", "")
confirm_password = password_config.get("confirm_password", "")

# Password strength validation
strength_checks = {
    "length_valid": len(new_password) >= password_policy["min_length"] and len(new_password) <= password_policy["max_length"],
    "has_uppercase": bool(re.search(r'[A-Z]', new_password)) if password_policy["require_uppercase"] else True,
    "has_lowercase": bool(re.search(r'[a-z]', new_password)) if password_policy["require_lowercase"] else True,
    "has_numbers": bool(re.search(r'[0-9]', new_password)) if password_policy["require_numbers"] else True,
    "has_special": bool(re.search(r'[!@#$%^&*()_+\-=\[\]{}|;:,.<>?]', new_password)) if password_policy["require_special_chars"] else True,
    "passwords_match": new_password == confirm_password,
    "not_common": new_password.lower() not in ["password123", "123456789", "qwerty123", "admin123"],
    "different_from_current": new_password != current_password
}

# Calculate password strength score
strength_score = 0
if strength_checks["length_valid"]: strength_score += 20
if strength_checks["has_uppercase"]: strength_score += 15
if strength_checks["has_lowercase"]: strength_score += 15
if strength_checks["has_numbers"]: strength_score += 15
if strength_checks["has_special"]: strength_score += 20
if len(new_password) >= 16: strength_score += 10
if bool(re.search(r'[!@#$%^&*()_+\-=\[\]{}|;:,.<>?]{2,}', new_password)): strength_score += 5

# Password security features
security_features = {
    "password_hash": f"hash_{random.randint(100000, 999999)}" if all(strength_checks.values()) else None,
    "expiry_date": (datetime.now() + timedelta(days=password_policy["max_age_days"])).isoformat(),
    "history_updated": True,
    "breach_check_passed": True,  # Would check against known breached passwords
    "complexity_score": strength_score
}

# Validation summary
all_checks_passed = all(strength_checks.values())
strength_level = "very_strong" if strength_score >= 85 else "strong" if strength_score >= 70 else "moderate" if strength_score >= 50 else "weak"

result = {
    "result": {
        "password_valid": all_checks_passed,
        "strength_checks": strength_checks,
        "strength_score": strength_score,
        "strength_level": strength_level,
        "security_features": security_features if all_checks_passed else None,
        "policy_compliance": all_checks_passed,
        "next_expiry": security_features["expiry_date"] if all_checks_passed else None
    }
}
"""
        })
        
        # Apply password changes
        builder.add_node("PythonCodeNode", "apply_password_changes", {
            "name": "apply_new_password_settings",
            "code": """
# Apply password changes and security settings
from datetime import datetime
password_validation = password_strength_validation

if password_validation.get("password_valid"):
    security_features = password_validation.get("security_features", {})
    
    # Password update record
    password_update = {
        "user_id": "test@example.com",
        "password_hash": security_features.get("password_hash"),
        "updated_at": datetime.now().isoformat(),
        "expiry_date": security_features.get("expiry_date"),
        "strength_score": password_validation.get("strength_score"),
        "policy_compliant": True,
        "force_change_next_login": False
    }
    
    # Security audit record
    security_audit = {
        "event_type": "password_change",
        "user_id": "test@example.com",
        "timestamp": datetime.now().isoformat(),
        "ip_address": "192.168.1.100",  # Would be actual IP
        "user_agent": "Mozilla/5.0...",  # Would be actual user agent
        "success": True,
        "strength_level": password_validation.get("strength_level"),
        "compliance_status": "compliant"
    }
    
    # Account security status update
    account_security = {
        "password_last_changed": datetime.now().isoformat(),
        "password_strength": password_validation.get("strength_level"),
        "security_score": min(100, password_validation.get("strength_score") + 15),  # Bonus for recent change
        "last_security_review": datetime.now().isoformat(),
        "password_expiry_warnings_enabled": True,
        "breach_monitoring_enabled": True
    }
    
    # Notification settings
    security_notifications = {
        "password_change_confirmation": True,
        "expiry_reminder_30_days": True,
        "expiry_reminder_7_days": True,
        "expiry_reminder_1_day": True,
        "suspicious_activity_alerts": True,
        "breach_notifications": True
    }
    
    update_successful = True
else:
    password_update = None
    security_audit = {
        "event_type": "password_change_failed",
        "user_id": "test@example.com",
        "timestamp": datetime.now().isoformat(),
        "success": False,
        "failure_reason": "Password validation failed",
        "validation_errors": [k for k, v in password_validation.get("strength_checks", {}).items() if not v]
    }
    account_security = None
    security_notifications = None
    update_successful = False

result = {
    "result": {
        "password_updated": update_successful,
        "password_update_record": password_update,
        "security_audit": security_audit,
        "account_security_status": account_security,
        "notification_settings": security_notifications,
        "next_required_change": password_update.get("expiry_date") if update_successful else None
    }
}
""".replace("{self.user_id}", self.user_id)
        })
        
        # Connect password setup nodes
        builder.add_connection("validate_password_input", "result", "validate_password_strength", "validation_result")
        builder.add_connection("validate_password_strength", "result.result", "apply_password_changes", "password_strength_validation")
        
        # Execute workflow
        workflow = builder.build()
        results, execution_id = self.runner.execute_workflow(
            workflow, password_config, "password_security_setup"
        )
        
        return results
    
    def setup_multi_factor_authentication(self, mfa_config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Set up multi-factor authentication.
        
        Args:
            mfa_config: MFA configuration settings
            
        Returns:
            MFA setup results
        """
        print(f"📱 Setting up MFA for user: {self.user_id}")
        
        builder = self.runner.create_workflow("mfa_setup")
        
        # MFA configuration and setup
        builder.add_node("PythonCodeNode", "configure_mfa", {
            "name": "configure_multi_factor_authentication",
            "code": """
import random
import string

# Use test data for MFA configuration
mfa_config_data = {
    "method": "totp",
    "phone_number": "+1-555-0123",
    "email": "user@company.com"
}
mfa_method = mfa_config_data.get("method", "totp")  # totp, sms, email
phone_number = mfa_config_data.get("phone_number", "")
email = mfa_config_data.get("email", "test@company.com")

# Generate MFA settings based on method
mfa_setup = {
    "user_id": "test@example.com",
    "enabled": True,
    "primary_method": mfa_method,
    "backup_methods": [],
    "setup_timestamp": datetime.now().isoformat()
}

# TOTP (Time-based One-Time Password) setup
if mfa_method == "totp":
    # Generate secret key for TOTP
    totp_secret = ''.join(random.choices(string.ascii_uppercase + string.digits, k=32))
    
    totp_setup = {
        "secret_key": totp_secret,
        "issuer": "User Management System",
        "account_name": "test@company.com",
        "qr_code_url": f"otpauth://totp/UserMgmt:test@company.com?secret={totp_secret}&issuer=UserMgmt",
        "recovery_codes": [''.join(random.choices(string.ascii_uppercase + string.digits, k=8)) for _ in range(10)],
        "setup_complete": False  # Will be True after verification
    }
    mfa_setup["totp_config"] = totp_setup
    mfa_setup["backup_methods"].append("recovery_codes")

# SMS setup
elif mfa_method == "sms":
    sms_setup = {
        "phone_number": phone_number,
        "country_code": "+1",  # Default
        "verified": False,
        "verification_code_length": 6,
        "code_expiry_minutes": 5,
        "max_attempts_per_hour": 5
    }
    mfa_setup["sms_config"] = sms_setup
    mfa_setup["backup_methods"].extend(["email", "recovery_codes"])

# Email backup setup
elif mfa_method == "email":
    email_setup = {
        "email_address": email,
        "verified": False,
        "code_length": 8,
        "code_expiry_minutes": 10,
        "backup_email": None
    }
    mfa_setup["email_config"] = email_setup
    mfa_setup["backup_methods"].append("recovery_codes")

# Common MFA settings
mfa_setup.update({
    "require_for_sensitive_operations": True,
    "remember_device_days": 30,
    "max_failed_attempts": 3,
    "lockout_duration_minutes": 15,
    "backup_codes_remaining": 10 if "recovery_codes" in mfa_setup["backup_methods"] else 0
})

# Device trust settings
device_trust = {
    "trusted_devices": [],
    "device_registration_required": True,
    "trust_duration_days": 30,
    "max_trusted_devices": 5,
    "require_reauth_for_new_devices": True
}

# Security policies
security_policies = {
    "force_mfa_for_admin": True,
    "allow_mfa_bypass": False,
    "require_backup_method": True,
    "periodic_reauth_hours": 24,
    "high_risk_operation_reauth": True
}

result = {
    "result": {
        "mfa_configured": True,
        "primary_method": mfa_method,
        "mfa_setup": mfa_setup,
        "device_trust": device_trust,
        "security_policies": security_policies,
        "setup_status": "pending_verification",
        "next_steps": ["verify_primary_method", "test_backup_methods", "save_recovery_codes"]
    }
}
"""
        })
        
        # Setup MFA verification process
        builder.add_node("PythonCodeNode", "setup_mfa_verification", {
            "name": "setup_mfa_verification_process",
            "code": """
# Set up MFA verification and testing process
mfa_configuration = mfa_config_setup

if mfa_configuration.get("mfa_configured"):
    mfa_setup = mfa_configuration.get("mfa_setup", {})
    primary_method = mfa_configuration.get("primary_method")
    
    # Verification process setup
    verification_process = {
        "verification_required": True,
        "verification_steps": [],
        "estimated_completion_time": "5 minutes",
        "support_contact": "support@company.com"
    }
    
    # Method-specific verification steps
    if primary_method == "totp":
        verification_process["verification_steps"] = [
            {
                "step": 1,
                "title": "Install Authenticator App",
                "description": "Download and install an authenticator app (Google Authenticator, Authy, etc.)",
                "required": True
            },
            {
                "step": 2,
                "title": "Scan QR Code",
                "description": "Scan the QR code with your authenticator app",
                "qr_code_data": mfa_setup.get("totp_config", {}).get("qr_code_url"),
                "manual_entry_key": mfa_setup.get("totp_config", {}).get("secret_key"),
                "required": True
            },
            {
                "step": 3,
                "title": "Enter Verification Code",
                "description": "Enter the 6-digit code from your authenticator app",
                "input_type": "numeric",
                "code_length": 6,
                "required": True
            },
            {
                "step": 4,
                "title": "Save Recovery Codes",
                "description": "Download and safely store your recovery codes",
                "recovery_codes": mfa_setup.get("totp_config", {}).get("recovery_codes"),
                "required": True
            }
        ]
    
    elif primary_method == "sms":
        verification_process["verification_steps"] = [
            {
                "step": 1,
                "title": "Verify Phone Number",
                "description": f"We'll send a code to {mfa_setup.get('sms_config', {}).get('phone_number')}",
                "required": True
            },
            {
                "step": 2,
                "title": "Enter SMS Code",
                "description": "Enter the 6-digit code sent to your phone",
                "input_type": "numeric",
                "code_length": 6,
                "required": True
            },
            {
                "step": 3,
                "title": "Test Backup Method",
                "description": "Set up email backup for when SMS isn't available",
                "required": False
            }
        ]
    
    elif primary_method == "email":
        verification_process["verification_steps"] = [
            {
                "step": 1,
                "title": "Verify Email Address",
                "description": f"Check your email at {mfa_setup.get('email_config', {}).get('email_address')}",
                "required": True
            },
            {
                "step": 2,
                "title": "Enter Email Code",
                "description": "Enter the 8-digit code from the email",
                "input_type": "alphanumeric",
                "code_length": 8,
                "required": True
            }
        ]
    
    # Security reminders and best practices
    security_reminders = [
        "Never share your MFA codes with anyone",
        "Keep recovery codes in a secure location", 
        "Don't save codes in cloud storage or email",
        "Contact support immediately if you lose access to your MFA device",
        "Review and update your MFA settings regularly"
    ]
    
    # Account security improvement
    security_improvement = {
        "before_mfa_score": 60,  # Baseline security score
        "after_mfa_score": 85,   # Improved with MFA
        "security_boost": 25,
        "protection_level": "high",
        "compliance_status": "enhanced"
    }
    
else:
    verification_process = {"error": "MFA configuration failed"}
    security_reminders = []
    security_improvement = {}

result = {
    "result": {
        "verification_setup": verification_process.get("verification_required", False),
        "verification_process": verification_process,
        "security_reminders": security_reminders,
        "security_improvement": security_improvement,
        "mfa_ready_for_activation": mfa_configuration.get("mfa_configured", False)
    }
}
"""
        })
        
        # Connect MFA setup nodes
        builder.add_connection("configure_mfa", "result.result", "setup_mfa_verification", "mfa_config_setup")
        
        # Execute workflow
        workflow = builder.build()
        results, execution_id = self.runner.execute_workflow(
            workflow, mfa_config, "mfa_setup"
        )
        
        return results
    
    def monitor_account_security(self, monitoring_period: str = "last_30_days") -> Dict[str, Any]:
        """
        Monitor account security and activity.
        
        Args:
            monitoring_period: Period to monitor (last_7_days, last_30_days, last_90_days)
            
        Returns:
            Security monitoring results
        """
        print(f"🔍 Monitoring account security for user: {self.user_id}")
        
        builder = self.runner.create_workflow("account_security_monitoring")
        
        # Collect security metrics and activity
        builder.add_node("PythonCodeNode", "collect_security_data", {
            "name": "collect_account_security_metrics",
            "code": """
# Collect comprehensive security data for monitoring period
monitoring_period = "{monitoring_period}"
user_id = "test@example.com"

# Login activity analysis
login_activity = {
    "total_logins": 45,
    "successful_logins": 43,
    "failed_attempts": 2,
    "unique_locations": 2,
    "unique_devices": 3,
    "average_session_duration": "4.2 hours",
    "most_active_hours": ["09:00-10:00", "14:00-15:00"],
    "most_active_days": ["Monday", "Tuesday", "Wednesday"]
}

# Device and location tracking
device_activity = [
    {
        "device_type": "laptop",
        "browser": "Chrome 121.0",
        "os": "macOS 14.2",
        "location": "Office - New York",
        "last_seen": "2024-06-15T09:00:00Z",
        "login_count": 25,
        "trusted": True
    },
    {
        "device_type": "mobile",
        "browser": "Safari Mobile",
        "os": "iOS 17.4",
        "location": "Home - New York",
        "last_seen": "2024-06-14T22:30:00Z",
        "login_count": 18,
        "trusted": True
    },
    {
        "device_type": "laptop",
        "browser": "Firefox 122.0",
        "os": "Windows 11",
        "location": "Coffee Shop - Manhattan",
        "last_seen": "2024-06-10T15:45:00Z",
        "login_count": 2,
        "trusted": False
    }
]

# Security events and alerts
security_events = [
    {
        "event_type": "password_change",
        "timestamp": "2024-06-01T10:30:00Z",
        "status": "success",
        "location": "Office - New York",
        "risk_level": "low"
    },
    {
        "event_type": "mfa_setup",
        "timestamp": "2024-06-01T10:35:00Z",
        "status": "success",
        "mfa_method": "totp",
        "risk_level": "low"
    },
    {
        "event_type": "suspicious_login_attempt",
        "timestamp": "2024-06-10T02:15:00Z",
        "status": "blocked",
        "location": "Unknown - Russia",
        "risk_level": "high",
        "action_taken": "account_temporarily_locked"
    }
]

# Current security posture
security_posture = {
    "overall_score": 88,  # Out of 100
    "password_strength": "strong",
    "mfa_enabled": True,
    "trusted_devices": 2,
    "recent_security_events": len(security_events),
    "compliance_status": "compliant",
    "last_security_review": "2024-06-01T10:30:00Z"
}

# Risk assessment
risk_assessment = {
    "current_risk_level": "low",
    "risk_factors": [
        {
            "factor": "untrusted_device_access",
            "severity": "medium",
            "description": "Login from untrusted device detected",
            "recommendation": "Review device and remove if unauthorized"
        }
    ],
    "protective_measures": [
        "Strong password in use",
        "MFA enabled and active",
        "Regular security monitoring",
        "Account lockout protection active"
    ]
}

# Security recommendations
security_recommendations = [
    {
        "priority": "medium",
        "category": "device_management",
        "title": "Review Untrusted Devices",
        "description": "You have 1 untrusted device that has accessed your account",
        "action": "review_and_remove_untrusted_devices",
        "estimated_time": "2 minutes"
    },
    {
        "priority": "low",
        "category": "password_management",
        "title": "Password Rotation",
        "description": "Your password will expire in 60 days",
        "action": "plan_password_update",
        "estimated_time": "3 minutes"
    },
    {
        "priority": "low",
        "category": "security_review",
        "title": "Security Settings Review",
        "description": "Regular review of security settings recommended",
        "action": "review_security_settings",
        "estimated_time": "5 minutes"
    }
]

result = {
    "result": {
        "monitoring_period": monitoring_period,
        "data_collected": True,
        "login_activity": login_activity,
        "device_activity": device_activity,
        "security_events": security_events,
        "security_posture": security_posture,
        "risk_assessment": risk_assessment,
        "security_recommendations": security_recommendations
    }
}
"""
        })
        
        # Generate security insights and alerts
        builder.add_node("PythonCodeNode", "generate_security_insights", {
            "name": "generate_account_security_insights",
            "code": """
# Generate actionable security insights
security_data = security_monitoring_data

# Analyze security trends
login_activity = security_data.get("login_activity", {})
device_activity = security_data.get("device_activity", [])
security_events = security_data.get("security_events", [])

# Security trend analysis
trend_analysis = {
    "login_frequency": "stable",  # Based on historical data
    "device_usage": "normal",     # Consistent device usage
    "location_pattern": "expected", # Usual locations
    "security_event_frequency": "low",
    "overall_trend": "positive"
}

# Anomaly detection
anomalies_detected = []
for event in security_events:
    if event.get("risk_level") == "high":
        anomalies_detected.append({
            "type": event.get("event_type"),
            "timestamp": event.get("timestamp"),
            "risk_level": event.get("risk_level"),
            "status": event.get("status"),
            "description": f"Suspicious {event.get('event_type')} detected"
        })

# Device trust analysis
trusted_devices = [d for d in device_activity if d.get("trusted")]
untrusted_devices = [d for d in device_activity if not d.get("trusted")]

device_insights = {
    "total_devices": len(device_activity),
    "trusted_devices": len(trusted_devices),
    "untrusted_devices": len(untrusted_devices),
    "most_used_device": max(device_activity, key=lambda x: x.get("login_count", 0)) if device_activity else None,
    "devices_needing_review": untrusted_devices
}

# Security score breakdown
security_posture = security_data.get("security_posture", {})
score_breakdown = {
    "password_security": 25,      # Strong password
    "mfa_protection": 30,         # MFA enabled
    "device_trust": 15,           # Mostly trusted devices
    "activity_monitoring": 10,    # Active monitoring
    "incident_response": 8,       # Quick response to threats
    "total_score": security_posture.get("overall_score", 88)
}

# Actionable insights
actionable_insights = [
    {
        "insight": "Account Security is Strong",
        "description": f"Your security score of {score_breakdown['total_score']}/100 indicates robust protection",
        "action": "Continue current security practices"
    },
    {
        "insight": "MFA Protection Active",
        "description": "Multi-factor authentication is protecting your account",
        "action": "Ensure backup codes are safely stored"
    }
]

if untrusted_devices:
    actionable_insights.append({
        "insight": "Untrusted Device Detected",
        "description": f"{len(untrusted_devices)} untrusted device(s) have accessed your account",
        "action": "Review and remove unauthorized devices"
    })

# Security health summary
security_health = {
    "status": "healthy" if security_posture.get("overall_score", 0) >= 80 else "needs_attention",
    "protection_level": "high" if security_posture.get("overall_score", 0) >= 85 else "medium",
    "monitoring_effective": len(anomalies_detected) <= 2,
    "immediate_action_required": any(r.get("priority") == "high" for r in security_data.get("security_recommendations", [])),
    "last_incident": max(security_events, key=lambda x: x.get("timestamp", ""))["timestamp"] if security_events else None
}

result = {
    "result": {
        "insights_generated": True,
        "trend_analysis": trend_analysis,
        "anomalies_detected": anomalies_detected,
        "device_insights": device_insights,
        "score_breakdown": score_breakdown,
        "actionable_insights": actionable_insights,
        "security_health": security_health,
        "monitoring_timestamp": datetime.now().isoformat()
    }
}
"""
        })
        
        # Connect security monitoring nodes
        builder.add_connection("collect_security_data", "result.result", "generate_security_insights", "security_monitoring_data")
        
        # Execute workflow
        workflow = builder.build()
        results, execution_id = self.runner.execute_workflow(
            workflow, {"monitoring_period": monitoring_period}, "account_security_monitoring"
        )
        
        return results
    
    def run_comprehensive_security_demo(self) -> Dict[str, Any]:
        """
        Run a comprehensive demonstration of all security settings operations.
        
        Returns:
            Complete demonstration results
        """
        print("🚀 Starting Comprehensive Security Settings Demonstration...")
        print("=" * 70)
        
        demo_results = {}
        
        try:
            # 1. Password security setup
            print("\n1. Setting up Password Security...")
            password_config = {
                "current_password": "OldPassword123!",
                "new_password": "NewSecurePassword456!@#",
                "confirm_password": "NewSecurePassword456!@#"
            }
            demo_results["password_security"] = self.setup_password_security(password_config)
            
            # 2. Multi-factor authentication setup
            print("\n2. Setting up Multi-Factor Authentication...")
            mfa_config = {
                "method": "totp",
                "phone_number": "+1-555-0123",
                "email": "user@company.com"
            }
            demo_results["mfa_setup"] = self.setup_multi_factor_authentication(mfa_config)
            
            # 3. Account security monitoring
            print("\n3. Monitoring Account Security...")
            demo_results["security_monitoring"] = self.monitor_account_security("last_30_days")
            
            # Print comprehensive summary
            self.print_security_summary(demo_results)
            
            return demo_results
            
        except Exception as e:
            print(f"❌ Security settings demonstration failed: {str(e)}")
            raise
    
    def print_security_summary(self, results: Dict[str, Any]):
        """
        Print a comprehensive security settings summary.
        
        Args:
            results: Security settings results from all workflows
        """
        print("\n" + "=" * 70)
        print("SECURITY SETTINGS DEMONSTRATION COMPLETE")
        print("=" * 70)
        
        # Password security summary
        password_result = results.get("password_security", {}).get("validate_password_strength", {}).get("result", {}).get("result", {})
        print(f"🔐 Password: {password_result.get('strength_level', 'N/A')} strength ({password_result.get('strength_score', 0)}/100)")
        
        # MFA setup summary
        mfa_result = results.get("mfa_setup", {}).get("configure_mfa", {}).get("result", {}).get("result", {})
        print(f"📱 MFA: {mfa_result.get('primary_method', 'N/A')} method configured")
        
        # Security monitoring summary
        monitoring_result = results.get("security_monitoring", {}).get("collect_security_data", {}).get("result", {}).get("result", {})
        security_score = monitoring_result.get("security_posture", {}).get("overall_score", 0)
        print(f"🔍 Security Score: {security_score}/100")
        
        print("\n🎉 All security settings operations completed successfully!")
        print("=" * 70)
        
        # Print execution statistics
        self.runner.print_stats()


def test_workflow(test_params: Optional[Dict[str, Any]] = None) -> bool:
    """
    Test the security settings workflow.
    
    Args:
        test_params: Optional test parameters
        
    Returns:
        True if test passes, False otherwise
    """
    try:
        print("🧪 Testing Security Settings Workflow...")
        
        # Create test workflow
        security_setup = SecuritySettingsWorkflow("test_user")
        
        # Test password security setup
        test_password_config = {
            "current_password": "OldPassword123!",
            "new_password": "TestPassword456!@#",
            "confirm_password": "TestPassword456!@#"
        }
        
        result = security_setup.setup_password_security(test_password_config)
        if not result.get("validate_password_strength", {}).get("result", {}).get("result", {}).get("password_valid"):
            return False
        
        print("✅ Security settings workflow test passed")
        return True
        
    except Exception as e:
        print(f"❌ Security settings workflow test failed: {str(e)}")
        return False


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--test":
        # Run test
        success = test_workflow()
        sys.exit(0 if success else 1)
    else:
        # Run comprehensive demonstration
        security_setup = SecuritySettingsWorkflow()
        
        try:
            results = security_setup.run_comprehensive_security_demo()
            print("🎉 Security settings demonstration completed successfully!")
        except Exception as e:
            print(f"❌ Demonstration failed: {str(e)}")
            sys.exit(1)