#!/usr/bin/env python3
"""
User Workflow: Support Requests and Help Desk

This workflow handles support and assistance including:
- Support ticket creation and tracking
- Help and documentation access
- Self-service troubleshooting
- Escalation management
- Knowledge base integration
"""

import os
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


class SupportRequestsWorkflow:
    """
    Complete support requests workflow for end users.
    """

    def __init__(self, user_id: str = "user"):
        """
        Initialize the support requests workflow.

        Args:
            user_id: ID of the user requesting support
        """
        self.user_id = user_id
        self.runner = WorkflowRunner(
            user_type="user",
            user_id=user_id,
            enable_debug=True,
            enable_audit=False,  # Disable for testing
            enable_monitoring=True,
        )

    def create_support_ticket(self, ticket_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create a new support ticket.

        Args:
            ticket_data: Support ticket information

        Returns:
            Ticket creation results
        """
        print(f"🎫 Creating support ticket for user: {self.user_id}")

        builder = self.runner.create_workflow("support_ticket_creation")

        # Validate ticket input
        validation_rules = {
            "subject": {"required": True, "type": "str", "min_length": 10},
            "description": {"required": True, "type": "str", "min_length": 20},
            "category": {"required": True, "type": "str"},
            "priority": {"required": False, "type": "str"},
        }

        builder.add_node(
            "PythonCodeNode",
            "validate_ticket_input",
            create_validation_node(validation_rules),
        )

        # Process and create support ticket
        builder.add_node(
            "PythonCodeNode",
            "create_ticket",
            {
                "name": "create_support_ticket",
                "code": f"""
from datetime import datetime, timedelta
import random
import string
import re

def generate_id():
    return ''.join(random.choices(string.ascii_letters + string.digits, k=12))

# Process support ticket creation
ticket_info = {ticket_data}
subject = ticket_info.get("subject", "")
description = ticket_info.get("description", "")
category = ticket_info.get("category", "general")
priority = ticket_info.get("priority", "medium")

# Generate ticket ID
ticket_id = f"SUP-{{datetime.now().strftime('%Y%m%d')}}-{{generate_id()[:8].upper()}}"

# Categorize ticket
support_categories = {{
    "account": {{
        "name": "Account & Authentication",
        "keywords": ["login", "password", "access", "account", "authentication", "mfa"],
        "sla_hours": 4,
        "auto_assignee": "account_support_team"
    }},
    "technical": {{
        "name": "Technical Issues",
        "keywords": ["error", "bug", "crash", "performance", "slow", "broken"],
        "sla_hours": 8,
        "auto_assignee": "technical_support_team"
    }},
    "permissions": {{
        "name": "Permissions & Access",
        "keywords": ["permission", "access", "role", "authorization", "denied"],
        "sla_hours": 2,
        "auto_assignee": "security_team"
    }},
    "data": {{
        "name": "Data & Privacy",
        "keywords": ["data", "export", "privacy", "gdpr", "deletion", "correction"],
        "sla_hours": 24,
        "auto_assignee": "privacy_team"
    }},
    "training": {{
        "name": "Training & Documentation",
        "keywords": ["how", "tutorial", "guide", "training", "help", "documentation"],
        "sla_hours": 12,
        "auto_assignee": "training_team"
    }},
    "feature": {{
        "name": "Feature Requests",
        "keywords": ["feature", "enhancement", "improvement", "suggestion", "request"],
        "sla_hours": 72,
        "auto_assignee": "product_team"
    }},
    "general": {{
        "name": "General Support",
        "keywords": ["other", "misc", "general", "question"],
        "sla_hours": 12,
        "auto_assignee": "general_support_team"
    }}
}}

# Auto-categorize if not specified or validate specified category
if category == "auto" or category not in support_categories:
    content_lower = (subject + " " + description).lower()
    category_scores = {{}}

    for cat_key, cat_info in support_categories.items():
        score = sum(1 for keyword in cat_info["keywords"] if keyword in content_lower)
        if score > 0:
            category_scores[cat_key] = score

    if category_scores:
        category = max(category_scores, key=category_scores.get)
    else:
        category = "general"

category_info = support_categories.get(category, support_categories["general"])

# Determine priority based on keywords and category
priority_keywords = {{
    "urgent": ["urgent", "critical", "emergency", "down", "broken", "can't work"],
    "high": ["important", "asap", "soon", "blocking", "stopped"],
    "medium": ["normal", "standard", "regular"],
    "low": ["minor", "when possible", "low priority", "enhancement"]
}}

if priority == "auto":
    content_lower = (subject + " " + description).lower()
    for priority_level, keywords in priority_keywords.items():
        if any(keyword in content_lower for keyword in keywords):
            priority = priority_level
            break
    else:
        priority = "medium"

# Calculate SLA deadline
priority_multipliers = {{"urgent": 0.25, "high": 0.5, "medium": 1.0, "low": 2.0}}
sla_hours = category_info["sla_hours"] * priority_multipliers.get(priority, 1.0)
sla_deadline = (datetime.now() + timedelta(hours=sla_hours)).isoformat()

# Create comprehensive ticket record
ticket_record = {{
    "ticket_id": ticket_id,
    "user_id": "{self.user_id}",
    "created_at": datetime.now().isoformat(),
    "updated_at": datetime.now().isoformat(),
    "status": "open",
    "subject": subject,
    "description": description,
    "category": category,
    "category_name": category_info["name"],
    "priority": priority,
    "assigned_team": category_info["auto_assignee"],
    "assigned_agent": None,
    "sla_deadline": sla_deadline,
    "estimated_resolution": sla_deadline,
    "tags": [],
    "attachments": [],
    "internal_notes": [],
    "user_updates": [],
    "resolution": None,
    "satisfaction_rating": None,
    "escalation_level": 0
}}

# Auto-tag based on content
auto_tags = []
if "urgent" in (subject + description).lower():
    auto_tags.append("urgent")
if any(word in (subject + description).lower() for word in ["new", "first time", "beginner"]):
    auto_tags.append("new_user")
if any(word in (subject + description).lower() for word in ["recurring", "again", "still"]):
    auto_tags.append("recurring_issue")

ticket_record["tags"] = auto_tags

# Determine auto-responses and suggestions
auto_suggestions = []
knowledge_base_links = []

if category == "account":
    auto_suggestions.extend([
        "Try clearing your browser cache and cookies",
        "Ensure you're using the correct email address",
        "Check if Caps Lock is enabled when entering password",
        "Try accessing from an incognito/private browser window"
    ])
    knowledge_base_links.extend([
        {{"title": "Password Reset Guide", "url": "/help/password-reset"}},
        {{"title": "MFA Setup Instructions", "url": "/help/mfa-setup"}},
        {{"title": "Account Recovery", "url": "/help/account-recovery"}}
    ])

elif category == "technical":
    auto_suggestions.extend([
        "Try refreshing the page or restarting your browser",
        "Check your internet connection stability",
        "Disable browser extensions temporarily",
        "Try using a different browser or device"
    ])
    knowledge_base_links.extend([
        {{"title": "Troubleshooting Guide", "url": "/help/troubleshooting"}},
        {{"title": "Browser Compatibility", "url": "/help/browsers"}},
        {{"title": "System Requirements", "url": "/help/requirements"}}
    ])

elif category == "permissions":
    auto_suggestions.extend([
        "Check with your manager about required permissions",
        "Verify you're accessing the correct system/feature",
        "Try logging out and back in to refresh permissions"
    ])
    knowledge_base_links.extend([
        {{"title": "Permission Requests", "url": "/help/permissions"}},
        {{"title": "Role-Based Access", "url": "/help/rbac"}},
        {{"title": "Access Approval Process", "url": "/help/approvals"}}
    ])

# Create automatic response
auto_response = {{
    "message": f"Thank you for contacting support. Your ticket {{ticket_id}} has been created and assigned to our {{category_info['name']}} team.",
    "estimated_response": f"You can expect an initial response within {{int(sla_hours)}} hours.",
    "suggestions": auto_suggestions,
    "helpful_links": knowledge_base_links,
    "next_steps": [
        "Our support team will review your request",
        "You'll receive email updates on ticket progress",
        "You can track your ticket status in the support portal",
        "Feel free to add additional information if needed"
    ]
}}

result = {{
    "result": {{
        "ticket_created": True,
        "ticket_record": ticket_record,
        "auto_response": auto_response,
        "category_detected": category,
        "priority_assigned": priority,
        "sla_commitment": sla_deadline
    }}
}}
""",
            },
        )

        # Generate ticket notifications
        builder.add_node(
            "PythonCodeNode",
            "generate_notifications",
            {
                "name": "generate_ticket_notifications",
                "code": """
# Generate notifications for ticket creation
ticket_creation = ticket_creation_result

if ticket_creation.get("ticket_created"):
    ticket_record = ticket_creation.get("ticket_record", {})
    auto_response = ticket_creation.get("auto_response", {})

    # User confirmation notification
    user_notification = {
        "type": "ticket_confirmation",
        "recipient": ticket_record.get("user_id"),
        "subject": f"Support Ticket Created: {ticket_record.get('ticket_id')}",
        "message": auto_response.get("message"),
        "ticket_details": {
            "ticket_id": ticket_record.get("ticket_id"),
            "subject": ticket_record.get("subject"),
            "category": ticket_record.get("category_name"),
            "priority": ticket_record.get("priority"),
            "estimated_response": auto_response.get("estimated_response")
        },
        "helpful_resources": auto_response.get("helpful_links", []),
        "next_steps": auto_response.get("next_steps", []),
        "portal_link": f"/support/tickets/{ticket_record.get('ticket_id')}",
        "timestamp": datetime.now().isoformat()
    }

    # Support team notification
    team_notification = {
        "type": "new_ticket_assignment",
        "recipient_team": ticket_record.get("assigned_team"),
        "ticket_summary": {
            "ticket_id": ticket_record.get("ticket_id"),
            "user_id": ticket_record.get("user_id"),
            "subject": ticket_record.get("subject"),
            "category": ticket_record.get("category"),
            "priority": ticket_record.get("priority"),
            "sla_deadline": ticket_record.get("sla_deadline"),
            "created_at": ticket_record.get("created_at")
        },
        "auto_suggestions": auto_response.get("suggestions", []),
        "escalation_required": ticket_record.get("priority") in ["urgent", "high"],
        "timestamp": datetime.now().isoformat()
    }

    # Manager notification for high priority tickets
    manager_notification = None
    if ticket_record.get("priority") in ["urgent", "high"]:
        manager_notification = {
            "type": "high_priority_ticket_alert",
            "recipient": "support_manager",
            "alert_level": "attention_required",
            "ticket_summary": {
                "ticket_id": ticket_record.get("ticket_id"),
                "user_id": ticket_record.get("user_id"),
                "subject": ticket_record.get("subject"),
                "priority": ticket_record.get("priority"),
                "sla_deadline": ticket_record.get("sla_deadline")
            },
            "requires_monitoring": True,
            "timestamp": datetime.now().isoformat()
        }

    notifications_sent = 2 if manager_notification else 1

else:
    user_notification = {"error": "Ticket creation failed"}
    team_notification = {"error": "Ticket assignment failed"}
    manager_notification = None
    notifications_sent = 0

result = {
    "result": {
        "notifications_generated": notifications_sent,
        "user_notification": user_notification,
        "team_notification": team_notification,
        "manager_notification": manager_notification,
        "escalation_triggered": ticket_creation.get("ticket_record", {}).get("priority") in ["urgent", "high"]
    }
}
""",
            },
        )

        # Connect ticket creation nodes
        builder.add_connection(
            "validate_ticket_input", "result", "create_ticket", "validation_result"
        )
        builder.add_connection(
            "create_ticket",
            "result.result",
            "generate_notifications",
            "ticket_creation_result",
        )

        # Execute workflow
        workflow = builder.build()
        results, execution_id = self.runner.execute_workflow(
            workflow, ticket_data, "support_ticket_creation"
        )

        return results

    def track_ticket_status(self, ticket_id: str) -> Dict[str, Any]:
        """
        Track status and updates for a support ticket.

        Args:
            ticket_id: ID of the ticket to track

        Returns:
            Ticket tracking results
        """
        print(f"📊 Tracking ticket status: {ticket_id}")

        builder = self.runner.create_workflow("ticket_status_tracking")

        # Retrieve and analyze ticket status
        builder.add_node(
            "PythonCodeNode",
            "get_ticket_status",
            {
                "name": "retrieve_ticket_status",
                "code": f"""
# Retrieve ticket status and history
ticket_id = "{ticket_id}"

# Simulated ticket data (in production, would query database)
ticket_data = {{
    "ticket_id": ticket_id,
    "user_id": "{self.user_id}",
    "created_at": (datetime.now() - timedelta(hours=6)).isoformat(),
    "updated_at": (datetime.now() - timedelta(minutes=30)).isoformat(),
    "status": "in_progress",
    "subject": "Unable to access reports section",
    "description": "When I try to access the reports section, I get a permission denied error",
    "category": "permissions",
    "category_name": "Permissions & Access",
    "priority": "medium",
    "assigned_team": "security_team",
    "assigned_agent": "Sarah Johnson",
    "sla_deadline": (datetime.now() + timedelta(hours=2)).isoformat(),
    "estimated_resolution": (datetime.now() + timedelta(hours=1)).isoformat(),
    "escalation_level": 0,
    "satisfaction_rating": None
}}

# Status history and updates
status_history = [
    {{
        "timestamp": ticket_data["created_at"],
        "status": "open",
        "action": "Ticket created by user",
        "actor": "{self.user_id}",
        "actor_type": "user",
        "details": "Initial ticket submission"
    }},
    {{
        "timestamp": (datetime.now() - timedelta(hours=5)).isoformat(),
        "status": "assigned",
        "action": "Ticket assigned to agent",
        "actor": "system",
        "actor_type": "system",
        "details": "Auto-assigned to security team"
    }},
    {{
        "timestamp": (datetime.now() - timedelta(hours=4)).isoformat(),
        "status": "in_progress",
        "action": "Agent began investigation",
        "actor": "Sarah Johnson",
        "actor_type": "agent",
        "details": "Checking user permissions in system"
    }},
    {{
        "timestamp": (datetime.now() - timedelta(minutes=30)).isoformat(),
        "status": "in_progress",
        "action": "Internal update",
        "actor": "Sarah Johnson",
        "actor_type": "agent",
        "details": "Identified permission issue, requesting role update"
    }}
]]

# Agent communications
communications = [
    {{
        "timestamp": (datetime.now() - timedelta(hours=4)).isoformat(),
        "from": "Sarah Johnson",
        "from_type": "agent",
        "to": "{self.user_id}",
        "to_type": "user",
        "message": "Hi! I've received your ticket and I'm looking into the permissions issue. I'll check your current role assignments and get back to you shortly.",
        "communication_type": "initial_response",
        "visible_to_user": True
    }},
    {{
        "timestamp": (datetime.now() - timedelta(hours=2)).isoformat(),
        "from": "Sarah Johnson",
        "from_type": "agent",
        "to": "security_admin",
        "to_type": "internal",
        "message": "User needs 'reports_view' permission added to their role. Current role: Employee. Requesting permission update.",
        "communication_type": "internal_note",
        "visible_to_user": False
    }},
    {{
        "timestamp": (datetime.now() - timedelta(minutes=30)).isoformat(),
        "from": "Sarah Johnson",
        "from_type": "agent",
        "to": "{self.user_id}",
        "to_type": "user",
        "message": "Good news! I've identified the issue and submitted a request to add the necessary permissions to your account. This should be resolved within the next hour.",
        "communication_type": "progress_update",
        "visible_to_user": True
    }}
]]

# Calculate ticket metrics
time_since_creation = datetime.now() - datetime.fromisoformat(ticket_data["created_at"].replace('Z', '+00:00'))
time_to_sla = datetime.fromisoformat(ticket_data["sla_deadline"].replace('Z', '+00:00')) - datetime.now()
response_time = datetime.fromisoformat(communications[0]["timestamp"].replace('Z', '+00:00')) - datetime.fromisoformat(ticket_data["created_at"].replace('Z', '+00:00'))

ticket_metrics = {{
    "time_since_creation_hours": time_since_creation.total_seconds() / 3600,
    "time_to_sla_hours": time_to_sla.total_seconds() / 3600,
    "first_response_time_hours": response_time.total_seconds() / 3600,
    "total_updates": len(status_history),
    "agent_responses": len([c for c in communications if c["from_type"] == "agent" and c["visible_to_user"]]),
    "sla_status": "on_track" if time_to_sla.total_seconds() > 0 else "at_risk",
    "escalation_needed": time_to_sla.total_seconds() < 1800  # 30 minutes
}}

result = {{
    "result": {{
        "ticket_found": True,
        "ticket_data": ticket_data,
        "status_history": status_history,
        "communications": [c for c in communications if c["visible_to_user"]],
        "ticket_metrics": ticket_metrics,
        "last_update": status_history[-1]["timestamp"]
    }}
}}
""",
            },
        )

        # Generate status insights and recommendations
        builder.add_node(
            "PythonCodeNode",
            "generate_status_insights",
            {
                "name": "generate_ticket_status_insights",
                "code": """
# Generate insights and recommendations for ticket status
ticket_status = ticket_status_data

if ticket_status.get("ticket_found"):
    ticket_data = ticket_status.get("ticket_data", {})
    metrics = ticket_status.get("ticket_metrics", {})

    # Status insights
    status_insights = {
        "current_status": ticket_data.get("status"),
        "progress_assessment": "good" if metrics.get("sla_status") == "on_track" else "at_risk",
        "agent_responsiveness": "excellent" if metrics.get("first_response_time_hours", 0) < 1 else "good",
        "estimated_completion": ticket_data.get("estimated_resolution"),
        "completion_confidence": "high" if ticket_data.get("status") == "in_progress" else "medium"
    }

    # User recommendations
    user_recommendations = []

    if ticket_data.get("status") == "open":
        user_recommendations.append({
            "action": "Be patient",
            "description": "Your ticket is in queue and will be assigned soon",
            "timeline": "within SLA"
        })

    elif ticket_data.get("status") == "in_progress":
        if metrics.get("time_since_creation_hours", 0) > 24:
            user_recommendations.append({
                "action": "Follow up politely",
                "description": "It's been over 24 hours, feel free to add a comment",
                "timeline": "now"
            })
        else:
            user_recommendations.append({
                "action": "Wait for update",
                "description": "Agent is actively working on your issue",
                "timeline": "check back in 2 hours"
            })

    elif ticket_data.get("status") == "waiting_for_user":
        user_recommendations.append({
            "action": "Respond promptly",
            "description": "Your response is needed to continue progress",
            "timeline": "as soon as possible"
        })

    # Escalation information
    escalation_info = {
        "escalation_available": metrics.get("time_since_creation_hours", 0) > 8,
        "escalation_recommended": metrics.get("escalation_needed", False),
        "escalation_process": [
            "Add comment requesting escalation",
            "Manager review within 2 hours",
            "Senior agent assignment",
            "Priority SLA adjustment"
        ]
    }

    # Self-service options
    self_service_options = []
    category = ticket_data.get("category", "")

    if category == "permissions":
        self_service_options.extend([
            {"action": "Check permission requests", "url": "/permissions/requests"},
            {"action": "Review role assignments", "url": "/profile/roles"},
            {"action": "Contact your manager", "method": "internal_message"}
        ])

    elif category == "account":
        self_service_options.extend([
            {"action": "Reset password", "url": "/auth/reset-password"},
            {"action": "Update MFA settings", "url": "/settings/mfa"},
            {"action": "Review login history", "url": "/security/login-history"}
        ])

    # Next steps timeline
    next_steps = [
        {
            "step": "Agent continues investigation",
            "estimated_time": "1 hour",
            "status": "in_progress"
        },
        {
            "step": "Permission update applied",
            "estimated_time": "2 hours",
            "status": "pending"
        },
        {
            "step": "Testing and verification",
            "estimated_time": "30 minutes",
            "status": "pending"
        },
        {
            "step": "Resolution confirmation",
            "estimated_time": "15 minutes",
            "status": "pending"
        }
    ]

else:
    status_insights = {"error": "Ticket not found"}
    user_recommendations = []
    escalation_info = {}
    self_service_options = []
    next_steps = []

result = {
    "result": {
        "insights_generated": ticket_status.get("ticket_found", False),
        "status_insights": status_insights,
        "user_recommendations": user_recommendations,
        "escalation_info": escalation_info,
        "self_service_options": self_service_options,
        "next_steps": next_steps,
        "tracking_successful": True
    }
}
""",
            },
        )

        # Connect ticket tracking nodes
        builder.add_connection(
            "get_ticket_status",
            "result.result",
            "generate_status_insights",
            "ticket_status_data",
        )

        # Execute workflow
        workflow = builder.build()
        results, execution_id = self.runner.execute_workflow(
            workflow, {"ticket_id": ticket_id}, "ticket_status_tracking"
        )

        return results

    def access_knowledge_base(self, search_query: Dict[str, Any]) -> Dict[str, Any]:
        """
        Search and access knowledge base and help documentation.

        Args:
            search_query: Search parameters and query

        Returns:
            Knowledge base search results
        """
        print(f"📚 Searching knowledge base for user: {self.user_id}")

        builder = self.runner.create_workflow("knowledge_base_search")

        # Process knowledge base search
        builder.add_node(
            "PythonCodeNode",
            "search_knowledge_base",
            {
                "name": "search_help_documentation",
                "code": f"""
# Search knowledge base and documentation
search_data = {search_query}
query = search_data.get("query", "").lower()
category_filter = search_data.get("category", "all")
result_limit = search_data.get("limit", 10)

# Knowledge base articles (simulated database)
knowledge_articles = [
    {{
        "id": "kb001",
        "title": "How to Reset Your Password",
        "category": "account",
        "summary": "Step-by-step guide to reset your password using email or phone verification",
        "content_preview": "If you've forgotten your password, you can reset it in just a few steps...",
        "url": "/help/password-reset",
        "tags": ["password", "reset", "login", "authentication"],
        "difficulty": "beginner",
        "estimated_time": "2 minutes",
        "last_updated": "2024-06-01",
        "rating": 4.8,
        "view_count": 1247
    }},
    {{
        "id": "kb002",
        "title": "Setting Up Multi-Factor Authentication",
        "category": "security",
        "summary": "Comprehensive guide to enable and configure MFA for enhanced account security",
        "content_preview": "Multi-factor authentication adds an extra layer of security...",
        "url": "/help/mfa-setup",
        "tags": ["mfa", "security", "totp", "authentication", "2fa"],
        "difficulty": "intermediate",
        "estimated_time": "5 minutes",
        "last_updated": "2024-05-15",
        "rating": 4.9,
        "view_count": 892
    }},
    {{
        "id": "kb003",
        "title": "Understanding Your Permissions and Roles",
        "category": "permissions",
        "summary": "Learn about the role-based access control system and how permissions work",
        "content_preview": "Your access to different features is controlled by roles and permissions...",
        "url": "/help/permissions-guide",
        "tags": ["permissions", "roles", "access", "rbac", "authorization"],
        "difficulty": "intermediate",
        "estimated_time": "8 minutes",
        "last_updated": "2024-05-20",
        "rating": 4.7,
        "view_count": 634
    }},
    {{
        "id": "kb004",
        "title": "Requesting Data Export (GDPR)",
        "category": "privacy",
        "summary": "How to request and download your personal data in compliance with GDPR",
        "content_preview": "You have the right to access your personal data...",
        "url": "/help/data-export",
        "tags": ["gdpr", "data", "export", "privacy", "rights"],
        "difficulty": "beginner",
        "estimated_time": "3 minutes",
        "last_updated": "2024-06-10",
        "rating": 4.6,
        "view_count": 445
    }},
    {{
        "id": "kb005",
        "title": "Troubleshooting Common Login Issues",
        "category": "account",
        "summary": "Solutions for the most common login problems and error messages",
        "content_preview": "Having trouble logging in? Here are the most common issues and solutions...",
        "url": "/help/login-troubleshooting",
        "tags": ["login", "troubleshooting", "error", "browser", "cache"],
        "difficulty": "beginner",
        "estimated_time": "4 minutes",
        "last_updated": "2024-05-30",
        "rating": 4.5,
        "view_count": 1156
    }},
    {{
        "id": "kb006",
        "title": "Managing Your Profile and Preferences",
        "category": "profile",
        "summary": "Complete guide to updating your profile information and system preferences",
        "content_preview": "Keep your profile up to date and customize your experience...",
        "url": "/help/profile-management",
        "tags": ["profile", "preferences", "settings", "personal", "information"],
        "difficulty": "beginner",
        "estimated_time": "6 minutes",
        "last_updated": "2024-06-05",
        "rating": 4.4,
        "view_count": 723
    }}
]]

# Search functionality
search_results = []
if query:
    for article in knowledge_articles:
        relevance_score = 0

        # Title matching (highest weight)
        if query in article["title"].lower():
            relevance_score += 10

        # Tag matching (high weight)
        for tag in article["tags"]:
            if query in tag:
                relevance_score += 8

        # Summary matching (medium weight)
        if query in article["summary"].lower():
            relevance_score += 5

        # Content preview matching (low weight)
        if query in article["content_preview"].lower():
            relevance_score += 2

        # Category filter
        if category_filter != "all" and article["category"] != category_filter:
            relevance_score = 0

        if relevance_score > 0:
            article_result = article.copy()
            article_result["relevance_score"] = relevance_score
            search_results.append(article_result)

    # Sort by relevance and rating
    search_results.sort(key=lambda x: (x["relevance_score"], x["rating"]), reverse=True)
    search_results = search_results[:result_limit]
else:
    # No query - show popular articles
    if category_filter == "all":
        search_results = sorted(knowledge_articles, key=lambda x: x["view_count"], reverse=True)[:result_limit]
    else:
        search_results = [a for a in knowledge_articles if a["category"] == category_filter][:result_limit]

# Generate search insights
search_insights = {{
    "total_results": len(search_results),
    "search_successful": len(search_results) > 0,
    "suggested_refinements": [],
    "popular_in_category": [],
    "related_topics": []
}}

if len(search_results) == 0 and query:
    search_insights["suggested_refinements"] = [
        "Try broader search terms",
        "Check spelling of keywords",
        "Browse by category instead",
        "Contact support for specific help"
    ]

# Add popular articles in category
if category_filter != "all":
    category_articles = [a for a in knowledge_articles if a["category"] == category_filter]
    search_insights["popular_in_category"] = sorted(category_articles, key=lambda x: x["view_count"], reverse=True)[:3]

# Add related topics based on search
if search_results:
    all_tags = []
    for result in search_results[:3]:  # Top 3 results
        all_tags.extend(result["tags"])

    tag_counts = {{}}
    for tag in all_tags:
        tag_counts[tag] = tag_counts.get(tag, 0) + 1

    # Get most common tags excluding search query
    related_tags = [tag for tag, count in sorted(tag_counts.items(), key=lambda x: x[1], reverse=True)
                   if tag != query][:5]
    search_insights["related_topics"] = related_tags

result = {{
    "result": {{
        "search_completed": True,
        "query": query,
        "category_filter": category_filter,
        "search_results": search_results,
        "search_insights": search_insights,
        "search_timestamp": datetime.now().isoformat()
    }}
}}
""",
            },
        )

        # Generate personalized recommendations
        builder.add_node(
            "PythonCodeNode",
            "generate_recommendations",
            {
                "name": "generate_personalized_help_recommendations",
                "code": """
# Generate personalized help recommendations
search_data = knowledge_search_results

if search_data.get("search_completed"):
    search_results = search_data.get("search_results", [])
    search_insights = search_data.get("search_insights", {})

    # Personalized recommendations based on user context
    personalized_recommendations = []

    # New user recommendations
    user_tenure_days = 30  # Simulated - would calculate from user creation date
    if user_tenure_days < 30:
        personalized_recommendations.extend([
            {
                "title": "Getting Started Guide",
                "description": "Essential features for new users",
                "url": "/help/getting-started",
                "reason": "You're new to the system",
                "priority": "high"
            },
            {
                "title": "First Steps Checklist",
                "description": "Complete your setup for the best experience",
                "url": "/help/first-steps",
                "reason": "Recommended for new users",
                "priority": "medium"
            }
        ])

    # Role-based recommendations
    user_role = "employee"  # Would get from user context
    if user_role == "manager":
        personalized_recommendations.append({
            "title": "Manager Tools and Features",
            "description": "Team management capabilities and reports",
            "url": "/help/manager-guide",
            "reason": "Based on your manager role",
            "priority": "medium"
        })

    # Department-specific recommendations
    user_department = "engineering"  # Would get from user context
    if user_department == "engineering":
        personalized_recommendations.append({
            "title": "Developer Resources",
            "description": "API documentation and technical guides",
            "url": "/help/developer-resources",
            "reason": "Tailored for engineering team",
            "priority": "low"
        })

    # Trending help topics
    trending_topics = [
        {
            "title": "New Dashboard Features",
            "description": "Recently released dashboard improvements",
            "url": "/help/dashboard-updates",
            "trend_reason": "Popular this week",
            "views_increase": "↑ 145%"
        },
        {
            "title": "Mobile App Updates",
            "description": "Latest mobile application features",
            "url": "/help/mobile-updates",
            "trend_reason": "Recently updated",
            "views_increase": "↑ 89%"
        }
    ]

    # Quick action suggestions
    quick_actions = [
        {
            "action": "Create Support Ticket",
            "description": "Get personalized help from our support team",
            "url": "/support/new-ticket",
            "icon": "ticket"
        },
        {
            "action": "Schedule Training",
            "description": "Book a one-on-one training session",
            "url": "/training/schedule",
            "icon": "calendar"
        },
        {
            "action": "Feature Tour",
            "description": "Take an interactive tour of new features",
            "url": "/help/feature-tour",
            "icon": "tour"
        },
        {
            "action": "Video Tutorials",
            "description": "Watch step-by-step video guides",
            "url": "/help/videos",
            "icon": "video"
        }
    ]

    # Help categories overview
    help_categories = [
        {"name": "Account & Authentication", "articles": 8, "icon": "user"},
        {"name": "Permissions & Access", "articles": 12, "icon": "shield"},
        {"name": "Privacy & Data", "articles": 6, "icon": "lock"},
        {"name": "Technical Support", "articles": 15, "icon": "wrench"},
        {"name": "Training & Tutorials", "articles": 10, "icon": "book"},
        {"name": "Feature Guides", "articles": 20, "icon": "star"}
    ]

    # User help statistics
    user_help_stats = {
        "articles_viewed_this_month": 5,
        "tickets_created_this_quarter": 2,
        "average_resolution_time": "4.2 hours",
        "satisfaction_rating": 4.6,
        "preferred_help_method": "knowledge_base"
    }

else:
    personalized_recommendations = []
    trending_topics = []
    quick_actions = []
    help_categories = []
    user_help_stats = {}

result = {
    "result": {
        "recommendations_generated": len(personalized_recommendations) > 0,
        "personalized_recommendations": personalized_recommendations,
        "trending_topics": trending_topics,
        "quick_actions": quick_actions,
        "help_categories": help_categories,
        "user_help_stats": user_help_stats,
        "help_portal_ready": True
    }
}
""",
            },
        )

        # Connect knowledge base search nodes
        builder.add_connection(
            "search_knowledge_base",
            "result.result",
            "generate_recommendations",
            "knowledge_search_results",
        )

        # Execute workflow
        workflow = builder.build()
        results, execution_id = self.runner.execute_workflow(
            workflow, search_query, "knowledge_base_search"
        )

        return results

    def run_comprehensive_support_demo(self) -> Dict[str, Any]:
        """
        Run a comprehensive demonstration of all support request operations.

        Returns:
            Complete demonstration results
        """
        print("🚀 Starting Comprehensive Support Requests Demonstration...")
        print("=" * 70)

        demo_results = {}

        try:
            # 1. Create support ticket
            print("\n1. Creating Support Ticket...")
            ticket_data = {
                "subject": "Unable to access reports section - getting permission denied error",
                "description": "When I try to access the reports section from the main dashboard, I get a 'Permission Denied' error message. I need access to generate monthly reports for my team. This started happening yesterday and I haven't had any issues before.",
                "category": "permissions",
                "priority": "medium",
            }
            demo_results["ticket_creation"] = self.create_support_ticket(ticket_data)

            # Get ticket ID from creation result
            ticket_id = (
                demo_results["ticket_creation"]
                .get("create_ticket", {})
                .get("result", {})
                .get("result", {})
                .get("ticket_record", {})
                .get("ticket_id", "SUP-20240615-ABC123")
            )

            # 2. Track ticket status
            print(f"\n2. Tracking Ticket Status: {ticket_id}")
            demo_results["ticket_tracking"] = self.track_ticket_status(ticket_id)

            # 3. Search knowledge base
            print("\n3. Searching Knowledge Base...")
            search_query = {
                "query": "permissions access denied",
                "category": "permissions",
                "limit": 5,
            }
            demo_results["knowledge_search"] = self.access_knowledge_base(search_query)

            # Print comprehensive summary
            self.print_support_summary(demo_results)

            return demo_results

        except Exception as e:
            print(f"❌ Support requests demonstration failed: {str(e)}")
            raise

    def print_support_summary(self, results: Dict[str, Any]):
        """
        Print a comprehensive support requests summary.

        Args:
            results: Support requests results from all workflows
        """
        print("\n" + "=" * 70)
        print("SUPPORT REQUESTS DEMONSTRATION COMPLETE")
        print("=" * 70)

        # Ticket creation summary
        ticket_result = (
            results.get("ticket_creation", {})
            .get("create_ticket", {})
            .get("result", {})
            .get("result", {})
        )
        ticket_record = ticket_result.get("ticket_record", {})
        print(
            f"🎫 Ticket: {ticket_record.get('ticket_id', 'N/A')} ({ticket_record.get('priority', 'unknown')} priority)"
        )

        # Ticket tracking summary
        tracking_result = (
            results.get("ticket_tracking", {})
            .get("get_ticket_status", {})
            .get("result", {})
            .get("result", {})
        )
        ticket_data = tracking_result.get("ticket_data", {})
        print(
            f"📊 Status: {ticket_data.get('status', 'unknown')} - Agent: {ticket_data.get('assigned_agent', 'unassigned')}"
        )

        # Knowledge search summary
        search_result = (
            results.get("knowledge_search", {})
            .get("search_knowledge_base", {})
            .get("result", {})
            .get("result", {})
        )
        search_results = search_result.get("search_results", [])
        print(f"📚 Knowledge Base: {len(search_results)} relevant articles found")

        print("\n🎉 All support request operations completed successfully!")
        print("=" * 70)

        # Print execution statistics
        self.runner.print_stats()


def test_workflow(test_params: Optional[Dict[str, Any]] = None) -> bool:
    """
    Test the support requests workflow.

    Args:
        test_params: Optional test parameters

    Returns:
        True if test passes, False otherwise
    """
    try:
        print("🧪 Testing Support Requests Workflow...")

        # Create test workflow
        support_requests = SupportRequestsWorkflow("test_user")

        # Test ticket creation
        test_ticket = {
            "subject": "Test ticket for workflow validation",
            "description": "This is a test ticket to validate the support workflow functionality and ensure all components work correctly.",
            "category": "technical",
            "priority": "low",
        }

        result = support_requests.create_support_ticket(test_ticket)
        if (
            not result.get("create_ticket", {})
            .get("result", {})
            .get("result", {})
            .get("ticket_created")
        ):
            return False

        print("✅ Support requests workflow test passed")
        return True

    except Exception as e:
        print(f"❌ Support requests workflow test failed: {str(e)}")
        return False


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--test":
        # Run test
        success = test_workflow()
        sys.exit(0 if success else 1)
    else:
        # Run comprehensive demonstration
        support_requests = SupportRequestsWorkflow()

        try:
            results = support_requests.run_comprehensive_support_demo()
            print("🎉 Support requests demonstration completed successfully!")
        except Exception as e:
            print(f"❌ Demonstration failed: {str(e)}")
            sys.exit(1)
