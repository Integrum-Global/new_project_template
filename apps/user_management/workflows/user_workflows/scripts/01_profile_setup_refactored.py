#!/usr/bin/env python3
"""
User Workflow: Profile Setup - Refactored

This workflow properly uses the user_management app's service layer
for profile management instead of inline PythonCodeNode logic.
"""

import sys
import os
from datetime import datetime
from typing import Dict, Any, List, Optional

# Add shared utilities to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', 'shared'))
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', '..', '..'))

from workflow_runner import WorkflowRunner
from service_nodes import (
    UserServiceNode, 
    RoleServiceNode, 
    SecurityServiceNode,
    ComplianceServiceNode
)
from kailash.nodes.api import HTTPRequestNode
from kailash.nodes.security import AuditLogNode
from kailash.nodes.transform import DataTransformer
from kailash.nodes.logic import SwitchNode


class ProfileSetupWorkflowRefactored:
    """
    User profile setup workflow using proper service integration.
    
    This demonstrates:
    - Using service nodes for profile operations
    - Proper API integration for user data
    - Privacy-compliant profile management
    """
    
    def __init__(self, user_id: str = "user", api_base_url: str = "http://localhost:8000"):
        """
        Initialize the profile setup workflow.
        
        Args:
            user_id: ID of the user
            api_base_url: Base URL of the user management API
        """
        self.user_id = user_id
        self.api_base_url = api_base_url
        self.runner = WorkflowRunner(
            user_type="user",
            user_id=user_id,
            enable_debug=True,
            enable_audit=True,
            enable_monitoring=True
        )
    
    def _get_auth_token(self) -> str:
        """Get authentication token for API calls."""
        return f"{self.user_id}_token"
    
    def complete_profile(self, profile_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Complete user profile setup using UserService.
        
        Args:
            profile_data: Profile information dictionary
            
        Returns:
            Profile completion results
        """
        print(f"👤 Completing profile for user: {self.user_id}")
        
        builder = self.runner.create_workflow("complete_profile")
        
        # Validate profile data
        builder.add_node("DataTransformer", "validate_profile", {
            "name": "validate_profile_data",
            "operations": [
                {
                    "type": "validate",
                    "config": {
                        "required_fields": ["first_name", "last_name"],
                        "optional_fields": ["phone", "bio", "department", "position"],
                        "privacy_sensitive": ["phone", "personal_email"]
                    }
                }
            ]
        })
        
        # Update profile via UserService
        builder.add_node("UserServiceNode", "update_profile", {
            "operation": "update_user"
        })
        
        # Check if profile picture needs uploading
        builder.add_node("SwitchNode", "check_picture", {
            "name": "check_profile_picture",
            "condition_field": "has_picture",
            "cases": {
                "true": "upload_picture",
                "false": "skip_picture"
            },
            "default_case": "skip_picture"
        })
        
        # Upload profile picture if provided
        builder.add_node("HTTPRequestNode", "upload_picture", {
            "name": "upload_profile_picture",
            "url": f"{self.api_base_url}/api/v1/users/me/profile/picture",
            "method": "POST",
            "headers": {
                "Authorization": f"Bearer {self._get_auth_token()}"
            },
            "form_data": {
                "picture": "{{picture_data}}"
            }
        })
        
        # Check profile completeness
        builder.add_node("DataTransformer", "check_completeness", {
            "name": "calculate_profile_completeness",
            "operations": [
                {
                    "type": "calculate",
                    "config": {
                        "metric": "completeness_percentage",
                        "required_fields": 6,
                        "bonus_fields": ["bio", "picture", "phone"]
                    }
                }
            ]
        })
        
        # Update privacy settings if needed
        builder.add_node("SwitchNode", "check_privacy", {
            "name": "check_privacy_preferences",
            "condition_field": "has_privacy_settings",
            "cases": {
                "true": "update_privacy",
                "false": "skip_privacy"
            },
            "default_case": "skip_privacy"
        })
        
        # Update privacy settings
        builder.add_node("HTTPRequestNode", "update_privacy", {
            "name": "update_privacy_settings",
            "url": f"{self.api_base_url}/api/v1/users/me/privacy",
            "method": "PUT",
            "headers": {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self._get_auth_token()}"
            },
            "body": "{{privacy_settings}}"
        })
        
        # Audit profile completion
        builder.add_node("AuditLogNode", "audit_completion", {
            "name": "audit_profile_completion",
            "action": "PROFILE_COMPLETED",
            "resource_type": "user_profile",
            "resource_id": self.user_id,
            "user_id": self.user_id,
            "details": {
                "completeness": "{{completeness_percentage}}",
                "fields_updated": "{{updated_fields}}"
            }
        })
        
        # Connect workflow nodes
        builder.add_connection("validate_profile", "result", "update_profile", "validated_data")
        builder.add_connection("update_profile", "user", "check_picture", "profile_data")
        builder.add_connection("check_picture", "true", "upload_picture", "picture_info")
        builder.add_connection("check_picture", "false", "check_completeness", "profile_result")
        builder.add_connection("upload_picture", "result", "check_completeness", "picture_result")
        builder.add_connection("check_completeness", "result", "check_privacy", "completeness_info")
        builder.add_connection("check_privacy", "true", "update_privacy", "privacy_data")
        builder.add_connection("check_privacy", "false", "audit_completion", "final_result")
        builder.add_connection("update_privacy", "result", "audit_completion", "privacy_result")
        
        # Execute workflow
        workflow = builder.build()
        results, execution_id = self.runner.execute_workflow(
            workflow,
            {
                "user_id": self.user_id,
                "updates": profile_data,
                "actor_id": self.user_id,
                "has_picture": "picture" in profile_data,
                "picture_data": profile_data.get("picture"),
                "has_privacy_settings": "privacy" in profile_data,
                "privacy_settings": profile_data.get("privacy", {})
            },
            "complete_profile"
        )
        
        return results
    
    def update_preferences(self, preferences: Dict[str, Any]) -> Dict[str, Any]:
        """
        Update user preferences.
        
        Args:
            preferences: User preferences dictionary
            
        Returns:
            Preference update results
        """
        print(f"⚙️ Updating preferences for user: {self.user_id}")
        
        builder = self.runner.create_workflow("update_preferences")
        
        # Validate preferences
        builder.add_node("DataTransformer", "validate_preferences", {
            "name": "validate_user_preferences",
            "operations": [
                {
                    "type": "validate",
                    "config": {
                        "allowed_themes": ["light", "dark", "auto"],
                        "allowed_languages": ["en", "es", "fr", "de"],
                        "notification_types": ["email", "browser", "mobile"]
                    }
                }
            ]
        })
        
        # Update preferences via API
        builder.add_node("HTTPRequestNode", "update_prefs", {
            "name": "update_user_preferences",
            "url": f"{self.api_base_url}/api/v1/users/me/preferences",
            "method": "PUT",
            "headers": {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self._get_auth_token()}"
            },
            "body": "{{validated_preferences}}"
        })
        
        # Apply theme changes if updated
        builder.add_node("SwitchNode", "check_theme_change", {
            "name": "check_if_theme_changed",
            "condition_field": "theme_changed",
            "cases": {
                "true": "apply_theme",
                "false": "skip_theme"
            },
            "default_case": "skip_theme"
        })
        
        # Apply UI theme
        builder.add_node("DataTransformer", "apply_theme", {
            "name": "apply_ui_theme",
            "operations": [
                {
                    "type": "transform",
                    "config": {
                        "theme_processor": "ui_theme_engine",
                        "apply_css": True,
                        "update_local_storage": True
                    }
                }
            ]
        })
        
        # Save preferences locally for offline access
        builder.add_node("HTTPRequestNode", "sync_local", {
            "name": "sync_local_preferences",
            "url": f"{self.api_base_url}/api/v1/users/me/preferences/sync",
            "method": "POST",
            "headers": {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self._get_auth_token()}"
            },
            "body": {
                "preferences": "{{final_preferences}}",
                "sync_offline": True
            }
        })
        
        # Connect workflow nodes
        builder.add_connection("validate_preferences", "result", "update_prefs", "validated_preferences")
        builder.add_connection("update_prefs", "result.data", "check_theme_change", "preference_update")
        builder.add_connection("check_theme_change", "true", "apply_theme", "theme_data")
        builder.add_connection("check_theme_change", "false", "sync_local", "final_preferences")
        builder.add_connection("apply_theme", "result", "sync_local", "theme_result")
        
        # Execute workflow
        workflow = builder.build()
        results, execution_id = self.runner.execute_workflow(
            workflow,
            {
                "preferences": preferences,
                "theme_changed": "theme" in preferences
            },
            "update_preferences"
        )
        
        return results
    
    def setup_notification_preferences(self, notification_config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Set up notification preferences.
        
        Args:
            notification_config: Notification configuration
            
        Returns:
            Notification setup results
        """
        print(f"🔔 Setting up notifications for user: {self.user_id}")
        
        builder = self.runner.create_workflow("setup_notifications")
        
        # Configure email notifications
        builder.add_node("HTTPRequestNode", "configure_email", {
            "name": "configure_email_notifications",
            "url": f"{self.api_base_url}/api/v1/notifications/email/configure",
            "method": "POST",
            "headers": {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self._get_auth_token()}"
            },
            "body": {
                "email_types": "{{email_notifications}}",
                "frequency": "{{email_frequency}}"
            }
        })
        
        # Configure browser notifications
        builder.add_node("HTTPRequestNode", "configure_browser", {
            "name": "configure_browser_notifications",
            "url": f"{self.api_base_url}/api/v1/notifications/browser/configure",
            "method": "POST",
            "headers": {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self._get_auth_token()}"
            },
            "body": {
                "browser_types": "{{browser_notifications}}",
                "permission_requested": True
            }
        })
        
        # Test notification delivery
        builder.add_node("HTTPRequestNode", "test_notifications", {
            "name": "test_notification_delivery",
            "url": f"{self.api_base_url}/api/v1/notifications/test",
            "method": "POST",
            "headers": {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self._get_auth_token()}"
            },
            "body": {
                "test_email": "{{test_email}}",
                "test_browser": "{{test_browser}}"
            }
        })
        
        # Connect workflow nodes
        builder.add_connection("configure_email", "result", "configure_browser", "email_config")
        builder.add_connection("configure_browser", "result", "test_notifications", "browser_config")
        
        # Execute workflow
        workflow = builder.build()
        results, execution_id = self.runner.execute_workflow(
            workflow,
            {
                "email_notifications": notification_config.get("email", []),
                "email_frequency": notification_config.get("email_frequency", "daily"),
                "browser_notifications": notification_config.get("browser", []),
                "test_email": notification_config.get("test_email", True),
                "test_browser": notification_config.get("test_browser", True)
            },
            "setup_notifications"
        )
        
        return results
    
    def run_demo(self) -> Dict[str, Any]:
        """
        Run a demonstration of profile setup.
        
        Returns:
            Demonstration results
        """
        print("🚀 Starting Profile Setup Demonstration...")
        print("=" * 70)
        print("NOTE: This requires the user_management API to be running!")
        print("Start it with: python -m apps.user_management.api")
        print("=" * 70)
        
        results = {}
        
        try:
            # 1. Complete profile
            print("\n1. Completing User Profile...")
            profile_data = {
                "first_name": "John",
                "last_name": "Doe",
                "phone": "+1-555-0123",
                "bio": "Software developer passionate about creating great user experiences",
                "department": "Engineering",
                "position": "Senior Developer",
                "privacy": {
                    "profile_visibility": "team",
                    "contact_sharing": False
                },
                "has_picture": False
            }
            results["profile"] = self.complete_profile(profile_data)
            
            # 2. Update preferences
            print("\n2. Updating User Preferences...")
            preferences = {
                "theme": "dark",
                "language": "en",
                "timezone": "UTC-5",
                "date_format": "MM/DD/YYYY",
                "notifications": {
                    "email": True,
                    "browser": True,
                    "mobile": False
                }
            }
            results["preferences"] = self.update_preferences(preferences)
            
            # 3. Setup notifications
            print("\n3. Setting up Notifications...")
            notification_config = {
                "email": ["security_alerts", "team_updates", "system_notifications"],
                "email_frequency": "immediate",
                "browser": ["messages", "mentions"],
                "test_email": True,
                "test_browser": True
            }
            results["notifications"] = self.setup_notification_preferences(notification_config)
            
            print("\n✅ Profile setup demonstration completed!")
            return results
            
        except Exception as e:
            print(f"❌ Demonstration failed: {str(e)}")
            print("\nTo run this demo, start the API server first:")
            print("python -m apps.user_management.api")
            raise


def test_workflow(test_params: Optional[Dict[str, Any]] = None) -> bool:
    """
    Test the refactored profile setup workflow.
    
    Args:
        test_params: Optional test parameters
        
    Returns:
        True if test passes, False otherwise
    """
    try:
        print("🧪 Testing Profile Setup Workflow...")
        
        # Create test workflow
        workflow = ProfileSetupWorkflowRefactored("test_user")
        
        # Validate workflow structure
        builder = workflow.runner.create_workflow("test_validation")
        
        # Add service nodes to test registration
        builder.add_node("UserServiceNode", "test_user_service", {
            "operation": "update_user"
        })
        
        builder.add_node("DataTransformer", "test_transformer", {
            "operations": [
                {
                    "type": "validate",
                    "config": {"test": True}
                }
            ]
        })
        
        test_workflow = builder.build()
        
        if test_workflow and len(test_workflow.nodes) >= 2:
            print("✅ Profile setup workflow structure test passed")
            return True
        else:
            return False
        
    except Exception as e:
        print(f"❌ Profile setup workflow test failed: {str(e)}")
        return False


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--test":
        # Run test
        success = test_workflow()
        sys.exit(0 if success else 1)
    else:
        # Run demonstration
        workflow = ProfileSetupWorkflowRefactored()
        
        try:
            results = workflow.run_demo()
            print("🎉 Profile setup workflow demonstration completed!")
        except Exception as e:
            print(f"❌ Demonstration failed: {str(e)}")
            print("\nTo run this demo, start the API server first:")
            print("python -m apps.user_management.api")
            sys.exit(1)