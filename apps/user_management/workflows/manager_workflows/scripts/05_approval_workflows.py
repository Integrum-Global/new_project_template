#!/usr/bin/env python3
"""
Manager Workflow: Approval and Request Management

This workflow handles approval processes and request management including:
- Access request approvals
- Resource allocation approvals
- Time-off and leave approvals
- Expense and procurement approvals
- Escalation and delegation management
"""

import sys
import os
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
import random
import json

# Add shared utilities to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', 'shared'))

from workflow_runner import WorkflowRunner, create_user_context_node, create_validation_node


class ApprovalWorkflow:
    """
    Complete approval and request management workflow for department managers.
    """
    
    def __init__(self, manager_user_id: str = "manager@company.com"):
        """
        Initialize the approval workflow.
        
        Args:
            manager_user_id: ID of the manager handling approvals
        """
        self.manager_user_id = manager_user_id
        self.runner = WorkflowRunner(
            user_type="manager",
            user_id=manager_user_id,
            enable_debug=True,
            enable_audit=False,  # Disable for testing
            enable_monitoring=True
        )
    
    def process_access_request(self, request_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process access request approval workflow.
        
        Args:
            request_data: Access request details
            
        Returns:
            Approval workflow results
        """
        print("🔐 Processing Access Request Approval...")
        
        builder = self.runner.create_workflow("access_request_approval")
        
        # Add manager context
        builder.add_node("PythonCodeNode", "manager_context", 
                        create_user_context_node(self.manager_user_id, "manager", 
                                                ["approve_access", "delegate_approval"]))
        
        # Validate request data
        validation_rules = {
            "request_id": {"required": True, "type": str},
            "requester": {"required": True, "type": str, "pattern": "^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\\.[a-zA-Z]{2,}$"},
            "resource_type": {"required": True, "type": str},
            "access_level": {"required": True, "type": str},
            "justification": {"required": True, "type": str, "min_length": 20}
        }
        builder.add_node("PythonCodeNode", "validate_request", create_validation_node(validation_rules))
        builder.add_connection("manager_context", "result", "validate_request", "context")
        
        # Evaluate access request
        builder.add_node("PythonCodeNode", "evaluate_request", {
            "name": "evaluate_access_request",
            "code": f"""
import random
from datetime import datetime, timedelta

# Evaluate access request
request_data = {request_data}
request_id = request_data.get("request_id", "REQ-001")
requester = request_data.get("requester", "john.doe@company.com")
resource_type = request_data.get("resource_type", "system")
access_level = request_data.get("access_level", "read")
justification = request_data.get("justification", "")

# Perform evaluation checks
evaluation = {{
    "request_id": request_id,
    "evaluation_timestamp": datetime.now().isoformat(),
    "evaluated_by": "{self.manager_user_id}",
    "requester_info": {{
        "email": requester,
        "department": "Engineering",
        "current_role": "Developer",
        "tenure_months": random.randint(6, 60),
        "previous_violations": random.randint(0, 2)
    }},
    "resource_analysis": {{
        "resource_type": resource_type,
        "sensitivity_level": "high" if resource_type in ["production", "financial"] else "medium",
        "compliance_requirements": ["SOC2", "GDPR"] if resource_type == "customer_data" else ["Internal"],
        "existing_access": ["read"] if random.random() > 0.5 else [],
        "requested_access": access_level
    }},
    "risk_assessment": {{
        "risk_score": round(random.uniform(1, 10), 1),
        "risk_level": "low" if access_level == "read" else "medium" if access_level == "write" else "high",
        "risk_factors": [
            "Privileged access requested" if access_level in ["admin", "write"] else "Standard access",
            "Sensitive resource" if resource_type in ["production", "financial"] else "Regular resource",
            "First-time access" if random.random() > 0.5 else "Existing user"
        ],
        "mitigation_required": access_level in ["admin", "write"]
    }},
    "compliance_check": {{
        "policies_checked": ["Access Control Policy", "Data Classification Policy", "Separation of Duties"],
        "compliance_status": "compliant",
        "additional_approvals_needed": ["security_team"] if resource_type == "production" else [],
        "audit_requirements": "quarterly_review" if access_level == "admin" else "annual_review"
    }},
    "recommendation": {{
        "action": "approve" if random.random() > 0.3 else "approve_with_conditions",
        "conditions": [
            "Time-limited access (90 days)" if access_level == "admin" else "Standard access period",
            "Additional training required" if resource_type == "financial" else None,
            "Monitoring enabled" if access_level in ["write", "admin"] else None
        ],
        "reasoning": justification,
        "auto_expire": access_level == "admin",
        "expire_days": 90 if access_level == "admin" else 365
    }}
}}

result = {{"result": evaluation}}
"""
        })
        builder.add_connection("validate_request", "result", "evaluate_request", "validation")
        
        # Make approval decision
        builder.add_node("PythonCodeNode", "make_decision", {
            "name": "make_approval_decision",
            "code": f"""
from datetime import datetime, timedelta

# Make final approval decision
evaluation = evaluate_request.get("result", evaluate_request)
request_data = {request_data}

# Decision logic based on evaluation
recommendation = evaluation.get("recommendation", {{}}).get("action", "review")
risk_level = evaluation.get("risk_assessment", {{}}).get("risk_level", "medium")

# Manager decision override capability
manager_override = request_data.get("manager_override", False)

if manager_override:
    decision = "approved"
    decision_reason = "Manager override applied"
else:
    if recommendation == "approve" and risk_level in ["low", "medium"]:
        decision = "approved"
        decision_reason = "Request meets all criteria"
    elif recommendation == "approve_with_conditions":
        decision = "approved_conditional"
        decision_reason = "Approved with specified conditions"
    else:
        decision = "rejected"
        decision_reason = "Risk level too high or policy violation"

# Create approval record
approval_record = {{
    "approval_id": f"APR_{{datetime.now().strftime('%Y%m%d_%H%M%S')}}",
    "request_id": evaluation["request_id"],
    "decision": decision,
    "decision_timestamp": datetime.now().isoformat(),
    "decided_by": "{self.manager_user_id}",
    "decision_details": {{
        "reason": decision_reason,
        "risk_accepted": risk_level,
        "conditions": evaluation["recommendation"]["conditions"] if decision == "approved_conditional" else [],
        "valid_from": datetime.now().isoformat(),
        "valid_until": (datetime.now() + timedelta(days=evaluation["recommendation"]["expire_days"])).isoformat() if decision != "rejected" else None,
        "review_required": evaluation["compliance_check"]["audit_requirements"]
    }},
    "implementation": {{
        "auto_provision": decision in ["approved", "approved_conditional"],
        "provision_delay_hours": 0 if evaluation["risk_assessment"]["risk_level"] == "low" else 24,
        "notifications_sent_to": [
            request_data.get("requester"),
            "{self.manager_user_id}",
            "security_team@company.com" if evaluation["risk_assessment"]["risk_level"] == "high" else None
        ],
        "tracking_enabled": evaluation["risk_assessment"]["mitigation_required"]
    }},
    "audit_trail": {{
        "evaluation_score": evaluation["risk_assessment"]["risk_score"],
        "policies_validated": evaluation["compliance_check"]["policies_checked"],
        "approval_chain": ["{self.manager_user_id}"] + evaluation["compliance_check"]["additional_approvals_needed"],
        "sla_status": "met",
        "processing_time_hours": round(random.uniform(0.5, 4), 1)
    }}
}}

result = {{"result": approval_record}}
"""
        })
        builder.add_connection("evaluate_request", "result", "make_decision", "evaluate_request")
        
        # Send notifications
        builder.add_node("PythonCodeNode", "send_notifications", {
            "name": "send_approval_notifications",
            "code": """
from datetime import datetime

# Send notifications based on decision
approval_record = make_decision.get("result", make_decision)

notifications = []

# Requester notification
notifications.append({
    "recipient": approval_record["request_id"].split("-")[0] + "@company.com",  # Mock email
    "type": "email",
    "template": "access_request_decision",
    "subject": f"Access Request {approval_record['request_id']} - {approval_record['decision'].upper()}",
    "priority": "high" if approval_record["decision"] == "rejected" else "normal",
    "data": {
        "decision": approval_record["decision"],
        "reason": approval_record["decision_details"]["reason"],
        "conditions": approval_record["decision_details"]["conditions"],
        "valid_until": approval_record["decision_details"]["valid_until"]
    },
    "sent_at": datetime.now().isoformat()
})

# IT team notification for provisioning
if approval_record["implementation"]["auto_provision"]:
    notifications.append({
        "recipient": "it_provisioning@company.com",
        "type": "ticket",
        "template": "provision_access",
        "subject": f"Provision Access - {approval_record['request_id']}",
        "priority": "normal",
        "data": {
            "approval_id": approval_record["approval_id"],
            "provision_delay": approval_record["implementation"]["provision_delay_hours"],
            "tracking_required": approval_record["implementation"]["tracking_enabled"]
        },
        "sent_at": datetime.now().isoformat()
    })

# Security team notification for high-risk
if approval_record["audit_trail"]["evaluation_score"] > 7:
    notifications.append({
        "recipient": "security_team@company.com",
        "type": "alert",
        "template": "high_risk_approval",
        "subject": f"High Risk Access Approved - {approval_record['request_id']}",
        "priority": "urgent",
        "data": {
            "risk_score": approval_record["audit_trail"]["evaluation_score"],
            "monitoring_required": True
        },
        "sent_at": datetime.now().isoformat()
    })

# Final result
final_result = {
    "approval_record": approval_record,
    "notifications_sent": len(notifications),
    "notification_details": notifications,
    "workflow_complete": True,
    "next_steps": [
        "Access will be provisioned within specified timeframe",
        "Requester will receive access credentials via secure channel",
        "Periodic review scheduled as per policy"
    ]
}

result = {"result": final_result}
"""
        })
        builder.add_connection("make_decision", "result", "send_notifications", "make_decision")
        
        # Build and execute workflow
        workflow = builder.build()
        
        try:
            results, execution_id = self.runner.execute_workflow(
                workflow, 
                request_data,
                "access_request_approval"
            )
            
            print("✅ Access Request Processed Successfully!")
            if self.runner.enable_debug:
                approval = results.get("send_notifications", {})
                record = approval.get("approval_record", {})
                print(f"   Approval ID: {record.get('approval_id', 'N/A')}")
                print(f"   Decision: {record.get('decision', 'N/A').upper()}")
                print(f"   Risk Level: {record.get('decision_details', {}).get('risk_accepted', 'N/A')}")
            
            return results
            
        except Exception as e:
            print(f"❌ Failed to process access request: {str(e)}")
            return {"error": str(e)}
    
    def manage_pending_approvals(self, filter_criteria: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Manage queue of pending approvals with bulk actions.
        
        Args:
            filter_criteria: Optional filtering criteria
            
        Returns:
            Pending approvals management results
        """
        print("📋 Managing Pending Approvals Queue...")
        
        if not filter_criteria:
            filter_criteria = {
                "status": "pending",
                "priority": "all",
                "age_days": 7
            }
        
        builder = self.runner.create_workflow("manage_pending_approvals")
        
        # Add manager context
        builder.add_node("PythonCodeNode", "manager_context", 
                        create_user_context_node(self.manager_user_id, "manager", 
                                                ["view_all_requests", "bulk_approve", "delegate"]))
        
        # Fetch pending approvals
        builder.add_node("PythonCodeNode", "fetch_pending", {
            "name": "fetch_pending_approvals",
            "code": f"""
import random
from datetime import datetime, timedelta

# Fetch pending approvals based on criteria
filter_criteria = {filter_criteria}

# Generate mock pending approvals
request_types = ["access_request", "resource_allocation", "time_off", "expense", "procurement"]
priorities = ["high", "medium", "low"]

pending_approvals = []
num_pending = random.randint(5, 15)

for i in range(num_pending):
    request_type = random.choice(request_types)
    priority = random.choice(priorities)
    days_old = random.randint(0, filter_criteria.get("age_days", 7))
    
    approval = {{
        "request_id": f"REQ-{{1000 + i}}",
        "request_type": request_type,
        "requester": f"user{{random.randint(1, 50)}}@company.com",
        "submitted_date": (datetime.now() - timedelta(days=days_old)).isoformat(),
        "priority": priority,
        "status": "pending",
        "summary": {{
            "access_request": "Production database read access",
            "resource_allocation": "Additional cloud compute resources",
            "time_off": "Annual leave request - 5 days",
            "expense": "Conference attendance - $2,500",
            "procurement": "Software licenses - $10,000"
        }}.get(request_type, "General request"),
        "urgency_score": random.randint(1, 10),
        "sla_status": "at_risk" if days_old > 3 else "on_track",
        "delegated_from": "senior_manager@company.com" if random.random() > 0.8 else None,
        "requires_additional_approval": request_type in ["procurement", "expense"] and random.random() > 0.5
    }}
    
    # Apply filters
    if filter_criteria.get("priority") != "all" and approval["priority"] != filter_criteria.get("priority"):
        continue
    if filter_criteria.get("status") != "all" and approval["status"] != filter_criteria.get("status"):
        continue
        
    pending_approvals.append(approval)

# Sort by urgency and age
pending_approvals.sort(key=lambda x: (x["urgency_score"], x["submitted_date"]), reverse=True)

# Generate summary statistics
summary_stats = {{
    "total_pending": len(pending_approvals),
    "by_type": {{
        req_type: sum(1 for a in pending_approvals if a["request_type"] == req_type)
        for req_type in request_types
    }},
    "by_priority": {{
        priority: sum(1 for a in pending_approvals if a["priority"] == priority)
        for priority in priorities
    }},
    "sla_at_risk": sum(1 for a in pending_approvals if a["sla_status"] == "at_risk"),
    "average_age_days": round(sum(
        (datetime.now() - datetime.fromisoformat(a["submitted_date"])).days 
        for a in pending_approvals
    ) / max(len(pending_approvals), 1), 1),
    "delegated_requests": sum(1 for a in pending_approvals if a["delegated_from"])
}}

result = {{
    "result": {{
        "pending_approvals": pending_approvals,
        "summary_stats": summary_stats,
        "fetch_timestamp": datetime.now().isoformat()
    }}
}}
"""
        })
        builder.add_connection("manager_context", "result", "fetch_pending", "context")
        
        # Analyze and prioritize approvals
        builder.add_node("PythonCodeNode", "prioritize_approvals", {
            "name": "analyze_and_prioritize",
            "code": """
from datetime import datetime

# Analyze and prioritize pending approvals
pending_data = fetch_pending.get("result", fetch_pending)
approvals = pending_data.get("pending_approvals", [])

# Enhanced prioritization logic
prioritized_approvals = []

for approval in approvals:
    # Calculate priority score
    priority_score = 0
    
    # Priority weight
    priority_weights = {"high": 3, "medium": 2, "low": 1}
    priority_score += priority_weights.get(approval["priority"], 1) * 10
    
    # Age weight (older = higher priority)
    age_days = (datetime.now() - datetime.fromisoformat(approval["submitted_date"])).days
    priority_score += min(age_days * 5, 25)  # Cap at 25 points
    
    # SLA risk weight
    if approval["sla_status"] == "at_risk":
        priority_score += 20
    
    # Urgency weight
    priority_score += approval["urgency_score"] * 2
    
    # Delegation weight
    if approval["delegated_from"]:
        priority_score += 15
    
    # Add priority score to approval
    approval["priority_score"] = priority_score
    
    # Recommend action based on analysis
    if approval["request_type"] == "time_off" and age_days < 2:
        approval["recommended_action"] = "auto_approve"
    elif approval["request_type"] in ["expense", "procurement"] and not approval.get("requires_additional_approval"):
        approval["recommended_action"] = "review_and_approve"
    elif approval["sla_status"] == "at_risk":
        approval["recommended_action"] = "urgent_review"
    else:
        approval["recommended_action"] = "standard_review"
    
    prioritized_approvals.append(approval)

# Sort by priority score
prioritized_approvals.sort(key=lambda x: x["priority_score"], reverse=True)

# Generate action recommendations
recommendations = {
    "immediate_actions": [
        {
            "action": "Process SLA at-risk items",
            "count": sum(1 for a in prioritized_approvals if a["sla_status"] == "at_risk"),
            "request_ids": [a["request_id"] for a in prioritized_approvals if a["sla_status"] == "at_risk"][:5]
        },
        {
            "action": "Auto-approve eligible requests",
            "count": sum(1 for a in prioritized_approvals if a["recommended_action"] == "auto_approve"),
            "request_ids": [a["request_id"] for a in prioritized_approvals if a["recommended_action"] == "auto_approve"]
        }
    ],
    "bulk_actions_available": [
        "Approve all low-risk time-off requests",
        "Delegate expense approvals to finance team",
        "Request additional information for incomplete requests"
    ],
    "suggested_delegations": [
        {
            "request_type": "expense",
            "delegate_to": "finance_manager@company.com",
            "count": sum(1 for a in prioritized_approvals if a["request_type"] == "expense")
        },
        {
            "request_type": "procurement",
            "delegate_to": "procurement_team@company.com",
            "count": sum(1 for a in prioritized_approvals if a["request_type"] == "procurement")
        }
    ]
}

result = {"result": {
    "prioritized_approvals": prioritized_approvals[:10],  # Top 10 for display
    "total_approvals": len(prioritized_approvals),
    "recommendations": recommendations,
    "analysis_timestamp": datetime.now().isoformat()
}}
"""
        })
        builder.add_connection("fetch_pending", "result", "prioritize_approvals", "fetch_pending")
        
        # Process bulk actions
        builder.add_node("PythonCodeNode", "process_bulk_actions", {
            "name": "execute_bulk_approval_actions",
            "code": f"""
from datetime import datetime

# Execute bulk approval actions based on manager input
prioritized_data = prioritize_approvals.get("result", prioritize_approvals)
approvals = prioritized_data.get("prioritized_approvals", [])

# Simulate bulk action execution
bulk_actions = filter_criteria.get("bulk_actions", ["auto_approve_eligible"])

action_results = {{
    "actions_performed": [],
    "approvals_processed": 0,
    "errors": []
}}

for action in bulk_actions:
    if action == "auto_approve_eligible":
        # Auto-approve eligible requests
        auto_approved = []
        for approval in approvals:
            if approval["recommended_action"] == "auto_approve":
                auto_approved.append({{
                    "request_id": approval["request_id"],
                    "action": "approved",
                    "reason": "Auto-approved per policy",
                    "timestamp": datetime.now().isoformat()
                }})
        
        action_results["actions_performed"].append({{
            "action_type": "auto_approve",
            "count": len(auto_approved),
            "details": auto_approved
        }})
        action_results["approvals_processed"] += len(auto_approved)
    
    elif action == "delegate_expense":
        # Delegate expense approvals
        delegated = []
        for approval in approvals:
            if approval["request_type"] == "expense":
                delegated.append({{
                    "request_id": approval["request_id"],
                    "delegated_to": "finance_manager@company.com",
                    "timestamp": datetime.now().isoformat()
                }})
        
        action_results["actions_performed"].append({{
            "action_type": "delegate",
            "count": len(delegated),
            "delegate_to": "finance_manager@company.com",
            "details": delegated
        }})

# Generate summary report
summary_report = {{
    "queue_status": {{
        "total_pending_before": prioritized_data["total_approvals"],
        "processed": action_results["approvals_processed"],
        "remaining": prioritized_data["total_approvals"] - action_results["approvals_processed"],
        "sla_compliance": round(random.uniform(85, 95), 1)
    }},
    "actions_summary": action_results,
    "next_review_recommended": (datetime.now() + timedelta(hours=4)).isoformat(),
    "notifications_sent": {{
        "requesters_notified": action_results["approvals_processed"],
        "delegates_notified": sum(
            len(a.get("details", [])) 
            for a in action_results["actions_performed"] 
            if a["action_type"] == "delegate"
        ),
        "escalations": 0
    }},
    "manager_dashboard_url": f"/manager/approvals/dashboard?session={{datetime.now().timestamp()}}"
}}

result = {{"result": summary_report}}
"""
        })
        builder.add_connection("prioritize_approvals", "result", "process_bulk_actions", "prioritize_approvals")
        
        # Build and execute workflow
        workflow = builder.build()
        
        try:
            results, execution_id = self.runner.execute_workflow(
                workflow, 
                filter_criteria,
                "manage_pending_approvals"
            )
            
            print("✅ Pending Approvals Managed Successfully!")
            if self.runner.enable_debug:
                summary = results.get("process_bulk_actions", {})
                queue = summary.get("queue_status", {})
                print(f"   Total Pending: {queue.get('total_pending_before', 'N/A')}")
                print(f"   Processed: {queue.get('processed', 'N/A')}")
                print(f"   Remaining: {queue.get('remaining', 'N/A')}")
            
            return results
            
        except Exception as e:
            print(f"❌ Failed to manage pending approvals: {str(e)}")
            return {"error": str(e)}
    
    def setup_approval_delegation(self, delegation_config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Setup approval delegation rules and chains.
        
        Args:
            delegation_config: Delegation configuration
            
        Returns:
            Delegation setup results
        """
        print("🔄 Setting Up Approval Delegation...")
        
        builder = self.runner.create_workflow("setup_delegation")
        
        # Add manager context
        builder.add_node("PythonCodeNode", "manager_context", 
                        create_user_context_node(self.manager_user_id, "manager", 
                                                ["configure_delegation", "manage_approval_chains"]))
        
        # Validate delegation configuration
        validation_rules = {
            "delegation_type": {"required": True, "type": str},
            "delegate_to": {"required": True, "type": str},
            "effective_from": {"required": True, "type": str},
            "effective_until": {"required": False, "type": str}
        }
        builder.add_node("PythonCodeNode", "validate_delegation", create_validation_node(validation_rules))
        builder.add_connection("manager_context", "result", "validate_delegation", "context")
        
        # Setup delegation rules
        builder.add_node("PythonCodeNode", "setup_delegation_rules", {
            "name": "configure_delegation_rules",
            "code": f"""
import random
from datetime import datetime, timedelta

# Configure delegation rules
delegation_config = {delegation_config}

delegation_rules = {{
    "rule_id": f"DEL_{{datetime.now().strftime('%Y%m%d_%H%M%S')}}",
    "created_by": "{self.manager_user_id}",
    "created_at": datetime.now().isoformat(),
    "configuration": {{
        "delegation_type": delegation_config.get("delegation_type", "temporary"),
        "delegate_to": delegation_config.get("delegate_to", "backup_manager@company.com"),
        "delegate_details": {{
            "name": "Backup Manager",
            "role": "Senior Manager",
            "department": "Engineering",
            "delegation_level": "full" if delegation_config.get("delegation_type") == "permanent" else "limited"
        }},
        "effective_period": {{
            "from": delegation_config.get("effective_from", datetime.now().isoformat()),
            "until": delegation_config.get("effective_until", (datetime.now() + timedelta(days=7)).isoformat()),
            "timezone": "UTC"
        }},
        "scope": {{
            "request_types": delegation_config.get("request_types", ["all"]),
            "max_approval_amount": delegation_config.get("max_amount", 10000),
            "excluded_resources": delegation_config.get("excluded_resources", ["production_admin", "financial_systems"]),
            "require_notification": True
        }},
        "conditions": {{
            "auto_escalate_high_risk": True,
            "escalation_threshold": 8,  # Risk score threshold
            "require_dual_approval": delegation_config.get("delegation_type") == "permanent",
            "maintain_audit_trail": True
        }}
    }},
    "approval_chains": [
        {{
            "level": 1,
            "approver": delegation_config.get("delegate_to"),
            "backup_approver": "senior_manager@company.com",
            "timeout_hours": 24,
            "auto_escalate": True
        }},
        {{
            "level": 2,
            "approver": "{self.manager_user_id}",
            "backup_approver": "director@company.com",
            "timeout_hours": 12,
            "auto_escalate": False
        }}
    ],
    "notifications": {{
        "delegation_active": [
            delegation_config.get("delegate_to"),
            "{self.manager_user_id}",
            "admin@company.com"
        ],
        "on_approval": ["{self.manager_user_id}"],
        "on_escalation": ["{self.manager_user_id}", "director@company.com"]
    }}
}}

result = {{"result": delegation_rules}}
"""
        })
        builder.add_connection("validate_delegation", "result", "setup_delegation_rules", "validation")
        
        # Activate delegation
        builder.add_node("PythonCodeNode", "activate_delegation", {
            "name": "activate_delegation_rules",
            "code": """
from datetime import datetime, timedelta

# Activate delegation rules
delegation_rules = setup_delegation_rules.get("result", setup_delegation_rules)

activation_result = {
    "activation_status": "success",
    "activated_at": datetime.now().isoformat(),
    "rule_id": delegation_rules["rule_id"],
    "validation_results": {
        "delegate_verified": True,
        "permissions_granted": True,
        "notification_sent": True,
        "audit_logged": True
    },
    "active_delegations": {
        "primary_delegate": delegation_rules["configuration"]["delegate_to"],
        "delegation_scope": delegation_rules["configuration"]["scope"]["request_types"],
        "active_until": delegation_rules["configuration"]["effective_period"]["until"],
        "requests_delegated": 0,  # Counter for delegated requests
        "last_activity": None
    },
    "system_updates": {
        "approval_routing_updated": True,
        "notification_rules_updated": True,
        "dashboard_access_granted": True,
        "reporting_configured": True
    },
    "summary": {
        "delegation_type": delegation_rules["configuration"]["delegation_type"],
        "delegate": delegation_rules["configuration"]["delegate_to"],
        "effective_period": f"{delegation_rules['configuration']['effective_period']['from']} to {delegation_rules['configuration']['effective_period']['until']}",
        "status": "ACTIVE",
        "health_check": "PASSED"
    }
}

# Generate confirmation
confirmation = {
    "delegation_rules": delegation_rules,
    "activation_result": activation_result,
    "next_steps": [
        "Delegate has been notified via email",
        "Delegation rules are now active",
        "Monitor delegation activity via dashboard",
        "Review delegation effectiveness after 7 days"
    ],
    "dashboard_link": f"/manager/delegations/{delegation_rules['rule_id']}"
}

result = {"result": confirmation}
"""
        })
        builder.add_connection("setup_delegation_rules", "result", "activate_delegation", "setup_delegation_rules")
        
        # Build and execute workflow
        workflow = builder.build()
        
        try:
            results, execution_id = self.runner.execute_workflow(
                workflow, 
                delegation_config,
                "setup_delegation"
            )
            
            print("✅ Delegation Setup Completed Successfully!")
            if self.runner.enable_debug:
                confirmation = results.get("activate_delegation", {})
                summary = confirmation.get("activation_result", {}).get("summary", {})
                print(f"   Delegation Type: {summary.get('delegation_type', 'N/A')}")
                print(f"   Delegate: {summary.get('delegate', 'N/A')}")
                print(f"   Status: {summary.get('status', 'N/A')}")
            
            return results
            
        except Exception as e:
            print(f"❌ Failed to setup delegation: {str(e)}")
            return {"error": str(e)}


def test_workflow(test_params: Optional[Dict[str, Any]] = None) -> bool:
    """
    Test the approval workflow.
    
    Args:
        test_params: Optional test parameters
        
    Returns:
        True if tests pass, False otherwise
    """
    print("\n" + "="*60)
    print("TESTING APPROVAL WORKFLOW")
    print("="*60)
    
    workflow = ApprovalWorkflow("test_manager@company.com")
    
    # Test 1: Access Request Approval
    print("\n1️⃣ Testing Access Request Approval...")
    result = workflow.process_access_request({
        "request_id": "REQ-12345",
        "requester": "john.doe@company.com",
        "resource_type": "production",
        "access_level": "write",
        "justification": "Need write access to production database for critical bug fix deployment"
    })
    
    if "error" in result:
        print(f"❌ Access request approval test failed: {result['error']}")
        return False
    
    # Test 2: Manage Pending Approvals
    print("\n2️⃣ Testing Pending Approvals Management...")
    result = workflow.manage_pending_approvals({
        "status": "pending",
        "priority": "high",
        "age_days": 7,
        "bulk_actions": ["auto_approve_eligible"]
    })
    
    if "error" in result:
        print(f"❌ Pending approvals management test failed: {result['error']}")
        return False
    
    # Test 3: Setup Delegation
    print("\n3️⃣ Testing Delegation Setup...")
    result = workflow.setup_approval_delegation({
        "delegation_type": "temporary",
        "delegate_to": "senior.manager@company.com",
        "effective_from": datetime.now().isoformat(),
        "effective_until": (datetime.now() + timedelta(days=14)).isoformat(),
        "request_types": ["access_request", "time_off"],
        "max_amount": 5000
    })
    
    if "error" in result:
        print(f"❌ Delegation setup test failed: {result['error']}")
        return False
    
    # Print summary statistics
    workflow.runner.print_stats()
    
    print("\n✅ All approval workflow tests passed!")
    return True


if __name__ == "__main__":
    # Run tests when script is executed directly
    success = test_workflow()
    exit(0 if success else 1)