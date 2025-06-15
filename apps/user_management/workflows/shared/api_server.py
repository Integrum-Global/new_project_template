#!/usr/bin/env python3
"""
User Management System - API Server

This module provides REST API endpoints for all user management workflows,
integrating with the Kailash SDK middleware for enterprise-grade features.
"""

import os
import sys
from datetime import datetime
from typing import Dict, Any, Optional, List
import logging
import asyncio
from contextlib import asynccontextmanager

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import Kailash middleware components
from kailash.middleware import create_gateway, APIGateway
from kailash.middleware.auth.jwt_auth import JWTAuthManager as KailashJWTAuthManager
from kailash.middleware.auth.access_control import MiddlewareAccessControlManager
from kailash.tracking import MetricsCollector
from kailash.middleware.database import MiddlewareDatabaseManager
from kailash.middleware.database.base_models import BaseWorkflowModel
from kailash.middleware.communication.realtime import RealtimeMiddleware

# FastAPI imports
from fastapi import HTTPException, Depends, Request, status, BackgroundTasks
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, Field, validator
from sqlalchemy.ext.asyncio import AsyncSession

# Import workflow implementations using dynamic imports
import importlib.util

def load_workflow_class(module_path: str, class_name: str):
    """Dynamically load a workflow class from a file path"""
    try:
        spec = importlib.util.spec_from_file_location("workflow_module", module_path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return getattr(module, class_name)
    except Exception as e:
        print(f"Warning: Could not load {class_name} from {module_path}: {e}")
        return None

# Load workflow classes
ProfileSetupWorkflow = load_workflow_class("../user_workflows/scripts/01_profile_setup.py", "ProfileSetupWorkflow")
SecuritySettingsWorkflow = load_workflow_class("../user_workflows/scripts/02_security_settings.py", "SecuritySettingsWorkflow")
DataManagementWorkflow = load_workflow_class("../user_workflows/scripts/03_data_management.py", "DataManagementWorkflow")
PrivacyControlsWorkflow = load_workflow_class("../user_workflows/scripts/04_privacy_controls.py", "PrivacyControlsWorkflow")
SupportRequestsWorkflow = load_workflow_class("../user_workflows/scripts/05_support_requests.py", "SupportRequestsWorkflow")

TeamSetupWorkflow = load_workflow_class("../manager_workflows/scripts/01_team_setup.py", "TeamSetupWorkflow")
UserManagementWorkflow = load_workflow_class("../manager_workflows/scripts/02_user_management.py", "UserManagementWorkflow")
PermissionAssignmentWorkflow = load_workflow_class("../manager_workflows/scripts/03_permission_assignment.py", "PermissionAssignmentWorkflow")
ReportingAnalyticsWorkflow = load_workflow_class("../manager_workflows/scripts/04_reporting_analytics.py", "ReportingAnalyticsWorkflow")
ApprovalWorkflow = load_workflow_class("../manager_workflows/scripts/05_approval_workflows.py", "ApprovalWorkflow")

SystemSetupWorkflow = load_workflow_class("../admin_workflows/scripts/01_system_setup.py", "SystemSetupWorkflow")
UserLifecycleWorkflow = load_workflow_class("../admin_workflows/scripts/02_user_lifecycle.py", "UserLifecycleWorkflow")
SecurityManagementWorkflow = load_workflow_class("../admin_workflows/scripts/03_security_management.py", "SecurityManagementWorkflow")
MonitoringAnalyticsWorkflow = load_workflow_class("../admin_workflows/scripts/04_monitoring_analytics.py", "MonitoringAnalyticsWorkflow")
BackupRecoveryWorkflow = load_workflow_class("../admin_workflows/scripts/05_backup_recovery.py", "BackupRecoveryWorkflow")

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Security scheme
security = HTTPBearer()

# ===== Request/Response Models =====

class UserContext(BaseModel):
    """User context for authentication"""
    user_id: str
    user_type: str
    permissions: List[str]
    department: Optional[str] = None


class WorkflowResponse(BaseModel):
    """Standard workflow response"""
    success: bool
    workflow_id: str
    execution_id: str
    results: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    timestamp: str = Field(default_factory=lambda: datetime.now().isoformat())


# ===== User Workflow Models =====

class ProfileSetupRequest(BaseModel):
    """Profile setup request model"""
    first_name: str
    last_name: str
    email: str
    phone: Optional[str] = None
    department: str
    role: str
    preferences: Optional[Dict[str, Any]] = None


class AccessRequest(BaseModel):
    """Access request model"""
    resource_type: str
    access_level: str = "read"
    justification: str
    duration_days: Optional[int] = None


class MFASetupRequest(BaseModel):
    """MFA setup request model"""
    method: str = Field(..., pattern="^(totp|sms|email)$")
    phone_number: Optional[str] = None
    backup_codes_count: int = 8


class PrivacySettingsRequest(BaseModel):
    """Privacy settings request model"""
    data_sharing: bool = False
    marketing_emails: bool = False
    analytics_tracking: bool = True
    profile_visibility: str = "team"


class SupportTicketRequest(BaseModel):
    """Support ticket request model"""
    category: str
    priority: str = Field(..., pattern="^(low|medium|high|urgent)$")
    subject: str
    description: str
    attachments: Optional[List[str]] = None


# ===== Manager Workflow Models =====

class TeamSetupRequest(BaseModel):
    """Team setup request model"""
    team_name: str
    team_description: str
    team_type: str
    initial_members: List[str]
    team_goals: Optional[List[str]] = None


class TeamMemberRequest(BaseModel):
    """Team member management request"""
    action: str = Field(..., pattern="^(add|remove|update)$")
    user_email: str
    role: Optional[str] = None
    permissions: Optional[List[str]] = None


class PermissionUpdateRequest(BaseModel):
    """Permission update request"""
    user_email: str
    permissions_to_add: Optional[List[str]] = None
    permissions_to_remove: Optional[List[str]] = None
    roles_to_assign: Optional[List[str]] = None


class ReportRequest(BaseModel):
    """Report generation request"""
    report_type: str
    period: Optional[str] = "monthly"
    metrics: Optional[List[str]] = None
    format: str = "json"
    include_trends: bool = True


class ApprovalActionRequest(BaseModel):
    """Approval action request"""
    request_id: str
    action: str = Field(..., pattern="^(approve|reject|delegate)$")
    comments: Optional[str] = None
    conditions: Optional[List[str]] = None
    delegate_to: Optional[str] = None


# ===== Admin Workflow Models =====

class TenantOnboardingRequest(BaseModel):
    """Tenant onboarding request"""
    company_name: str
    company_domain: str
    admin_email: str
    subscription_plan: str
    initial_user_count: int = 10
    features: Optional[List[str]] = None


class UserBulkActionRequest(BaseModel):
    """Bulk user action request"""
    action: str = Field(..., pattern="^(create|update|disable|delete)$")
    user_data: List[Dict[str, Any]]
    send_notifications: bool = True


class SecurityPolicyRequest(BaseModel):
    """Security policy configuration"""
    policy_type: str
    enabled: bool = True
    configuration: Dict[str, Any]
    apply_to: Optional[List[str]] = None  # User groups or departments


class BackupRequest(BaseModel):
    """Backup operation request"""
    backup_type: str = Field(..., pattern="^(full|incremental|selective)$")
    include_files: bool = True
    include_database: bool = True
    encryption_enabled: bool = True
    retention_days: int = 30


# ===== Lifespan Management =====

@asynccontextmanager
async def lifespan(app: APIGateway):
    """Application lifespan manager"""
    # Startup
    logger.info("Starting User Management API Server...")
    
    # Initialize database
    await app.state.db_manager.init_db()
    
    # Initialize realtime connections
    app.state.realtime = RealtimeMiddleware()
    await app.state.realtime.start()
    
    # Initialize workflow instances
    app.state.workflows = {
        "user": {
            "profile": ProfileSetupWorkflow,
            "access": AccessManagementWorkflow,
            "auth": AuthenticationSetupWorkflow,
            "privacy": PrivacyControlsWorkflow,
            "support": SupportRequestWorkflow
        },
        "manager": {
            "team": TeamSetupWorkflow,
            "users": UserManagementWorkflow,
            "permissions": PermissionAssignmentWorkflow,
            "reports": ReportingAnalyticsWorkflow,
            "approvals": ApprovalWorkflow
        },
        "admin": {
            "onboarding": SystemOnboardingWorkflow,
            "users": UserAdministrationWorkflow,
            "security": SecurityManagementWorkflow,
            "monitoring": MonitoringAnalyticsWorkflow,
            "backup": BackupRecoveryWorkflow
        }
    }
    
    logger.info("API Server initialized successfully")
    
    yield
    
    # Shutdown
    logger.info("Shutting down User Management API Server...")
    await app.state.realtime.stop()
    await app.state.db_manager.close()


# ===== Create Application =====

# Create the enterprise API gateway
app = create_gateway(
    title="Kailash User Management API",
    description="Enterprise-grade user management system with comprehensive workflow support",
    version="1.0.0"
)

# Add middleware
# Initialize metrics collector
metrics_collector = MetricsCollector()
# Note: APIGateway might not have state attribute - store in global scope if needed
app.add_middleware(MiddlewareAccessControlManager)

# Database manager
db_manager = MiddlewareDatabaseManager(database_url=os.getenv("DATABASE_URL", "sqlite+aiosqlite:///user_management.db"))
app.state.db_manager = db_manager

# JWT Authentication
jwt_auth = KailashJWTAuthManager(secret_key=os.getenv("JWT_SECRET_KEY", "your-secret-key"))


# ===== Authentication Dependencies =====

async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(db_manager.get_session)
) -> UserContext:
    """Get current authenticated user"""
    token = credentials.credentials
    
    try:
        payload = jwt_auth.decode_token(token)
        user_id = payload.get("sub")
        
        if not user_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication credentials"
            )
        
        # Get user permissions from database (mock for now)
        user_context = UserContext(
            user_id=user_id,
            user_type=payload.get("user_type", "user"),
            permissions=payload.get("permissions", []),
            department=payload.get("department")
        )
        
        return user_context
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Could not validate credentials: {str(e)}"
        )


async def require_user_type(required_type: str):
    """Dependency to require specific user type"""
    async def _require_user_type(user: UserContext = Depends(get_current_user)):
        if user.user_type not in [required_type, "admin"]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access restricted to {required_type} users"
            )
        return user
    return _require_user_type


# ===== Health Check =====

@app.get("/health", tags=["System"])
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "service": "user-management-api",
        "version": "1.0.0"
    }


# ===== User Workflow Endpoints =====

@app.post("/api/v1/user/profile/setup", response_model=WorkflowResponse, tags=["User Workflows"])
async def setup_user_profile(
    request: ProfileSetupRequest,
    background_tasks: BackgroundTasks,
    user: UserContext = Depends(get_current_user)
):
    """Setup user profile"""
    try:
        workflow = ProfileSetupWorkflow(user.user_id)
        
        profile_data = {
            "first_name": request.first_name,
            "last_name": request.last_name,
            "email": request.email,
            "phone": request.phone,
            "department": request.department,
            "role": request.role,
            "preferences": request.preferences or {}
        }
        
        results = workflow.setup_initial_profile(profile_data)
        
        # Send real-time notification
        if hasattr(app.state, 'realtime'):
            await app.state.realtime.send_event(
                user.user_id,
                "profile_updated",
                {"message": "Profile setup completed successfully"}
            )
        
        return WorkflowResponse(
            success=True,
            workflow_id="profile_setup",
            execution_id=f"exec_{int(datetime.now().timestamp())}",
            results=results
        )
        
    except Exception as e:
        logger.error(f"Profile setup failed: {str(e)}")
        return WorkflowResponse(
            success=False,
            workflow_id="profile_setup",
            execution_id=f"exec_{int(datetime.now().timestamp())}",
            error=str(e)
        )


@app.post("/api/v1/user/access/request", response_model=WorkflowResponse, tags=["User Workflows"])
async def request_access(
    request: AccessRequest,
    user: UserContext = Depends(get_current_user)
):
    """Request access to resources"""
    try:
        workflow = AccessManagementWorkflow(user.user_id)
        
        access_data = {
            "requester": user.user_id,
            "resource_type": request.resource_type,
            "access_level": request.access_level,
            "justification": request.justification,
            "duration_days": request.duration_days
        }
        
        results = workflow.request_system_access(access_data)
        
        return WorkflowResponse(
            success=True,
            workflow_id="access_request",
            execution_id=f"exec_{int(datetime.now().timestamp())}",
            results=results
        )
        
    except Exception as e:
        logger.error(f"Access request failed: {str(e)}")
        return WorkflowResponse(
            success=False,
            workflow_id="access_request",
            execution_id=f"exec_{int(datetime.now().timestamp())}",
            error=str(e)
        )


@app.post("/api/v1/user/auth/mfa/setup", response_model=WorkflowResponse, tags=["User Workflows"])
async def setup_mfa(
    request: MFASetupRequest,
    user: UserContext = Depends(get_current_user)
):
    """Setup multi-factor authentication"""
    try:
        workflow = AuthenticationSetupWorkflow(user.user_id)
        
        mfa_config = {
            "method": request.method,
            "phone_number": request.phone_number,
            "backup_codes_count": request.backup_codes_count
        }
        
        results = workflow.setup_mfa(mfa_config)
        
        return WorkflowResponse(
            success=True,
            workflow_id="mfa_setup",
            execution_id=f"exec_{int(datetime.now().timestamp())}",
            results=results
        )
        
    except Exception as e:
        logger.error(f"MFA setup failed: {str(e)}")
        return WorkflowResponse(
            success=False,
            workflow_id="mfa_setup",
            execution_id=f"exec_{int(datetime.now().timestamp())}",
            error=str(e)
        )


@app.post("/api/v1/user/privacy/settings", response_model=WorkflowResponse, tags=["User Workflows"])
async def update_privacy_settings(
    request: PrivacySettingsRequest,
    user: UserContext = Depends(get_current_user)
):
    """Update privacy settings"""
    try:
        workflow = PrivacyControlsWorkflow(user.user_id)
        
        privacy_data = {
            "data_sharing": request.data_sharing,
            "marketing_emails": request.marketing_emails,
            "analytics_tracking": request.analytics_tracking,
            "profile_visibility": request.profile_visibility
        }
        
        results = workflow.manage_privacy_settings(privacy_data)
        
        return WorkflowResponse(
            success=True,
            workflow_id="privacy_settings",
            execution_id=f"exec_{int(datetime.now().timestamp())}",
            results=results
        )
        
    except Exception as e:
        logger.error(f"Privacy settings update failed: {str(e)}")
        return WorkflowResponse(
            success=False,
            workflow_id="privacy_settings",
            execution_id=f"exec_{int(datetime.now().timestamp())}",
            error=str(e)
        )


@app.post("/api/v1/user/support/ticket", response_model=WorkflowResponse, tags=["User Workflows"])
async def create_support_ticket(
    request: SupportTicketRequest,
    user: UserContext = Depends(get_current_user)
):
    """Create support ticket"""
    try:
        workflow = SupportRequestWorkflow(user.user_id)
        
        ticket_data = {
            "category": request.category,
            "priority": request.priority,
            "subject": request.subject,
            "description": request.description,
            "attachments": request.attachments or []
        }
        
        results = workflow.create_support_ticket(ticket_data)
        
        return WorkflowResponse(
            success=True,
            workflow_id="support_ticket",
            execution_id=f"exec_{int(datetime.now().timestamp())}",
            results=results
        )
        
    except Exception as e:
        logger.error(f"Support ticket creation failed: {str(e)}")
        return WorkflowResponse(
            success=False,
            workflow_id="support_ticket",
            execution_id=f"exec_{int(datetime.now().timestamp())}",
            error=str(e)
        )


# ===== Manager Workflow Endpoints =====

@app.post("/api/v1/manager/team/setup", response_model=WorkflowResponse, tags=["Manager Workflows"])
async def setup_team(
    request: TeamSetupRequest,
    user: UserContext = Depends(require_user_type("manager"))
):
    """Setup new team"""
    try:
        workflow = TeamSetupWorkflow(user.user_id)
        
        team_data = {
            "team_name": request.team_name,
            "team_description": request.team_description,
            "team_type": request.team_type,
            "initial_members": request.initial_members,
            "team_goals": request.team_goals or []
        }
        
        results = workflow.create_new_team(team_data)
        
        return WorkflowResponse(
            success=True,
            workflow_id="team_setup",
            execution_id=f"exec_{int(datetime.now().timestamp())}",
            results=results
        )
        
    except Exception as e:
        logger.error(f"Team setup failed: {str(e)}")
        return WorkflowResponse(
            success=False,
            workflow_id="team_setup",
            execution_id=f"exec_{int(datetime.now().timestamp())}",
            error=str(e)
        )


@app.post("/api/v1/manager/team/members", response_model=WorkflowResponse, tags=["Manager Workflows"])
async def manage_team_member(
    request: TeamMemberRequest,
    user: UserContext = Depends(require_user_type("manager"))
):
    """Manage team members"""
    try:
        workflow = UserManagementWorkflow(user.user_id)
        
        if request.action == "add":
            member_data = {
                "email": request.user_email,
                "role": request.role,
                "permissions": request.permissions or [],
                "department": user.department
            }
            results = workflow.add_team_member(member_data)
        elif request.action == "remove":
            results = workflow.remove_team_member({"user_email": request.user_email})
        else:
            results = workflow.update_team_member({
                "user_email": request.user_email,
                "updates": {
                    "role": request.role,
                    "permissions": request.permissions
                }
            })
        
        return WorkflowResponse(
            success=True,
            workflow_id=f"team_member_{request.action}",
            execution_id=f"exec_{int(datetime.now().timestamp())}",
            results=results
        )
        
    except Exception as e:
        logger.error(f"Team member management failed: {str(e)}")
        return WorkflowResponse(
            success=False,
            workflow_id=f"team_member_{request.action}",
            execution_id=f"exec_{int(datetime.now().timestamp())}",
            error=str(e)
        )


@app.post("/api/v1/manager/permissions/update", response_model=WorkflowResponse, tags=["Manager Workflows"])
async def update_permissions(
    request: PermissionUpdateRequest,
    user: UserContext = Depends(require_user_type("manager"))
):
    """Update user permissions"""
    try:
        workflow = PermissionAssignmentWorkflow(user.user_id)
        
        permission_data = {
            "user_email": request.user_email,
            "permissions_to_add": request.permissions_to_add or [],
            "permissions_to_remove": request.permissions_to_remove or [],
            "roles_to_assign": request.roles_to_assign or []
        }
        
        results = workflow.assign_permissions(permission_data)
        
        return WorkflowResponse(
            success=True,
            workflow_id="permission_update",
            execution_id=f"exec_{int(datetime.now().timestamp())}",
            results=results
        )
        
    except Exception as e:
        logger.error(f"Permission update failed: {str(e)}")
        return WorkflowResponse(
            success=False,
            workflow_id="permission_update",
            execution_id=f"exec_{int(datetime.now().timestamp())}",
            error=str(e)
        )


@app.post("/api/v1/manager/reports/generate", response_model=WorkflowResponse, tags=["Manager Workflows"])
async def generate_report(
    request: ReportRequest,
    user: UserContext = Depends(require_user_type("manager"))
):
    """Generate reports"""
    try:
        workflow = ReportingAnalyticsWorkflow(user.user_id)
        
        if request.report_type == "team_performance":
            results = workflow.generate_team_performance_report({
                "department": user.department,
                "period": request.period,
                "include_trends": request.include_trends
            })
        elif request.report_type == "activity_monitoring":
            results = workflow.generate_activity_monitoring_report({
                "department": user.department,
                "time_range": f"last_30_days",
                "include_anomalies": True,
                "include_compliance": True
            })
        else:
            results = workflow.generate_custom_report({
                "report_type": request.report_type,
                "metrics": request.metrics or [],
                "format": request.format
            })
        
        return WorkflowResponse(
            success=True,
            workflow_id=f"report_{request.report_type}",
            execution_id=f"exec_{int(datetime.now().timestamp())}",
            results=results
        )
        
    except Exception as e:
        logger.error(f"Report generation failed: {str(e)}")
        return WorkflowResponse(
            success=False,
            workflow_id=f"report_{request.report_type}",
            execution_id=f"exec_{int(datetime.now().timestamp())}",
            error=str(e)
        )


@app.post("/api/v1/manager/approvals/process", response_model=WorkflowResponse, tags=["Manager Workflows"])
async def process_approval(
    request: ApprovalActionRequest,
    user: UserContext = Depends(require_user_type("manager"))
):
    """Process approval request"""
    try:
        workflow = ApprovalWorkflow(user.user_id)
        
        approval_data = {
            "request_id": request.request_id,
            "action": request.action,
            "comments": request.comments,
            "conditions": request.conditions,
            "delegate_to": request.delegate_to,
            "manager_override": user.user_type == "admin"
        }
        
        results = workflow.process_access_request(approval_data)
        
        return WorkflowResponse(
            success=True,
            workflow_id="approval_process",
            execution_id=f"exec_{int(datetime.now().timestamp())}",
            results=results
        )
        
    except Exception as e:
        logger.error(f"Approval processing failed: {str(e)}")
        return WorkflowResponse(
            success=False,
            workflow_id="approval_process",
            execution_id=f"exec_{int(datetime.now().timestamp())}",
            error=str(e)
        )


# ===== Admin Workflow Endpoints =====

@app.post("/api/v1/admin/tenant/onboard", response_model=WorkflowResponse, tags=["Admin Workflows"])
async def onboard_tenant(
    request: TenantOnboardingRequest,
    user: UserContext = Depends(require_user_type("admin"))
):
    """Onboard new tenant"""
    try:
        workflow = SystemOnboardingWorkflow(user.user_id)
        
        tenant_data = {
            "company_name": request.company_name,
            "company_domain": request.company_domain,
            "admin_email": request.admin_email,
            "subscription_plan": request.subscription_plan,
            "initial_user_count": request.initial_user_count,
            "features": request.features or []
        }
        
        results = workflow.onboard_new_tenant(tenant_data)
        
        return WorkflowResponse(
            success=True,
            workflow_id="tenant_onboarding",
            execution_id=f"exec_{int(datetime.now().timestamp())}",
            results=results
        )
        
    except Exception as e:
        logger.error(f"Tenant onboarding failed: {str(e)}")
        return WorkflowResponse(
            success=False,
            workflow_id="tenant_onboarding",
            execution_id=f"exec_{int(datetime.now().timestamp())}",
            error=str(e)
        )


@app.post("/api/v1/admin/users/bulk", response_model=WorkflowResponse, tags=["Admin Workflows"])
async def bulk_user_action(
    request: UserBulkActionRequest,
    user: UserContext = Depends(require_user_type("admin"))
):
    """Perform bulk user actions"""
    try:
        workflow = UserAdministrationWorkflow(user.user_id)
        
        if request.action == "create":
            results = workflow.bulk_create_users({
                "users": request.user_data,
                "send_invitations": request.send_notifications
            })
        else:
            results = workflow.manage_user_lifecycle({
                "action": request.action,
                "users": request.user_data,
                "reason": "Bulk action via API"
            })
        
        return WorkflowResponse(
            success=True,
            workflow_id=f"bulk_user_{request.action}",
            execution_id=f"exec_{int(datetime.now().timestamp())}",
            results=results
        )
        
    except Exception as e:
        logger.error(f"Bulk user action failed: {str(e)}")
        return WorkflowResponse(
            success=False,
            workflow_id=f"bulk_user_{request.action}",
            execution_id=f"exec_{int(datetime.now().timestamp())}",
            error=str(e)
        )


@app.post("/api/v1/admin/security/policy", response_model=WorkflowResponse, tags=["Admin Workflows"])
async def update_security_policy(
    request: SecurityPolicyRequest,
    user: UserContext = Depends(require_user_type("admin"))
):
    """Update security policies"""
    try:
        workflow = SecurityManagementWorkflow(user.user_id)
        
        # This would map to specific security workflow methods
        results = workflow.monitor_security_threats({
            "policy_type": request.policy_type,
            "enabled": request.enabled,
            "configuration": request.configuration
        })
        
        return WorkflowResponse(
            success=True,
            workflow_id="security_policy_update",
            execution_id=f"exec_{int(datetime.now().timestamp())}",
            results=results
        )
        
    except Exception as e:
        logger.error(f"Security policy update failed: {str(e)}")
        return WorkflowResponse(
            success=False,
            workflow_id="security_policy_update",
            execution_id=f"exec_{int(datetime.now().timestamp())}",
            error=str(e)
        )


@app.post("/api/v1/admin/backup/create", response_model=WorkflowResponse, tags=["Admin Workflows"])
async def create_backup(
    request: BackupRequest,
    background_tasks: BackgroundTasks,
    user: UserContext = Depends(require_user_type("admin"))
):
    """Create system backup"""
    try:
        workflow = BackupRecoveryWorkflow(user.user_id)
        
        backup_config = {
            "backup_type": request.backup_type,
            "include_files": request.include_files,
            "include_database": request.include_database,
            "encryption_enabled": request.encryption_enabled,
            "retention_days": request.retention_days
        }
        
        # Run backup in background
        background_tasks.add_task(
            workflow.manage_backup_operations,
            backup_config
        )
        
        return WorkflowResponse(
            success=True,
            workflow_id="backup_create",
            execution_id=f"exec_{int(datetime.now().timestamp())}",
            results={"message": "Backup operation started in background"}
        )
        
    except Exception as e:
        logger.error(f"Backup creation failed: {str(e)}")
        return WorkflowResponse(
            success=False,
            workflow_id="backup_create",
            execution_id=f"exec_{int(datetime.now().timestamp())}",
            error=str(e)
        )


# ===== Real-time Endpoints =====

@app.websocket("/ws/{user_id}")
async def websocket_endpoint(websocket, user_id: str):
    """WebSocket endpoint for real-time updates"""
    await app.state.realtime.connect_websocket(websocket, user_id)
    try:
        while True:
            data = await websocket.receive_text()
            # Process incoming messages if needed
    except Exception as e:
        logger.error(f"WebSocket error: {str(e)}")
    finally:
        await app.state.realtime.disconnect_websocket(user_id)


# ===== Monitoring Endpoints =====

@app.get("/metrics", tags=["Monitoring"])
async def get_metrics():
    """Get application metrics"""
    # This would integrate with Prometheus or similar
    return {
        "active_users": 0,  # Would query from database
        "total_requests": 0,
        "error_rate": 0.0,
        "average_response_time": 0.0
    }


# ===== Main Entry Point =====

if __name__ == "__main__":
    import uvicorn
    
    # Get configuration from environment
    host = os.getenv("API_HOST", "0.0.0.0")
    port = int(os.getenv("API_PORT", "8000"))
    workers = int(os.getenv("WORKERS", "4"))
    
    # Run the server
    uvicorn.run(
        "api_server:app",
        host=host,
        port=port,
        workers=workers,
        reload=True if os.getenv("ENVIRONMENT") == "development" else False,
        log_level="info"
    )