#!/usr/bin/env python3
"""
User Management CLI - Comprehensive Command Line Interface

Provides command-line access to all user management workflows:
- User workflows: Profile, Access, Authentication, Privacy, Support
- Manager workflows: Team Setup, User Management, Permissions, Reports, Approvals
- Admin workflows: Tenant Onboarding, Bulk Operations, Security, Monitoring, Backup

Supports both direct workflow execution and API-based execution.
"""

import asyncio
import json
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

import click
import httpx
import yaml
from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.prompt import Confirm, Prompt
from rich.syntax import Syntax
from rich.table import Table

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Import workflow implementations using dynamic imports to handle numbered files
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
ProfileSetupWorkflow = load_workflow_class(
    "workflows/user_workflows/scripts/01_profile_setup.py", "ProfileSetupWorkflow"
)
SecuritySettingsWorkflow = load_workflow_class(
    "workflows/user_workflows/scripts/02_security_settings.py",
    "SecuritySettingsWorkflow",
)
DataManagementWorkflow = load_workflow_class(
    "workflows/user_workflows/scripts/03_data_management.py", "DataManagementWorkflow"
)
PrivacyControlsWorkflow = load_workflow_class(
    "workflows/user_workflows/scripts/04_privacy_controls.py", "PrivacyControlsWorkflow"
)
SupportRequestsWorkflow = load_workflow_class(
    "workflows/user_workflows/scripts/05_support_requests.py", "SupportRequestsWorkflow"
)

TeamSetupWorkflow = load_workflow_class(
    "workflows/manager_workflows/scripts/01_team_setup.py", "TeamSetupWorkflow"
)
UserManagementWorkflow = load_workflow_class(
    "workflows/manager_workflows/scripts/02_user_management.py",
    "UserManagementWorkflow",
)
PermissionAssignmentWorkflow = load_workflow_class(
    "workflows/manager_workflows/scripts/03_permission_assignment.py",
    "PermissionAssignmentWorkflow",
)
ReportingAnalyticsWorkflow = load_workflow_class(
    "workflows/manager_workflows/scripts/04_reporting_analytics.py",
    "ReportingAnalyticsWorkflow",
)
ApprovalWorkflow = load_workflow_class(
    "workflows/manager_workflows/scripts/05_approval_workflows.py", "ApprovalWorkflow"
)

SystemSetupWorkflow = load_workflow_class(
    "workflows/admin_workflows/scripts/01_system_setup.py", "SystemSetupWorkflow"
)
UserLifecycleWorkflow = load_workflow_class(
    "workflows/admin_workflows/scripts/02_user_lifecycle.py", "UserLifecycleWorkflow"
)
SecurityManagementWorkflow = load_workflow_class(
    "workflows/admin_workflows/scripts/03_security_management.py",
    "SecurityManagementWorkflow",
)
MonitoringAnalyticsWorkflow = load_workflow_class(
    "workflows/admin_workflows/scripts/04_monitoring_analytics.py",
    "MonitoringAnalyticsWorkflow",
)
BackupRecoveryWorkflow = load_workflow_class(
    "workflows/admin_workflows/scripts/05_backup_recovery.py", "BackupRecoveryWorkflow"
)

# Rich console for beautiful output
console = Console()

# Configuration
CONFIG_FILE = Path.home() / ".kailash" / "user_management.yaml"
API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000")


class CLIConfig:
    """CLI configuration manager"""

    def __init__(self):
        self.config_file = CONFIG_FILE
        self.config_file.parent.mkdir(exist_ok=True)
        self.config = self.load_config()

    def load_config(self) -> Dict[str, Any]:
        """Load configuration from file"""
        if self.config_file.exists():
            with open(self.config_file, "r") as f:
                return yaml.safe_load(f) or {}
        return {}

    def save_config(self):
        """Save configuration to file"""
        with open(self.config_file, "w") as f:
            yaml.dump(self.config, f)

    def get_token(self) -> Optional[str]:
        """Get stored authentication token"""
        return self.config.get("auth", {}).get("token")

    def set_token(self, token: str):
        """Store authentication token"""
        if "auth" not in self.config:
            self.config["auth"] = {}
        self.config["auth"]["token"] = token
        self.config["auth"]["last_login"] = datetime.now().isoformat()
        self.save_config()

    def clear_token(self):
        """Clear authentication token"""
        if "auth" in self.config:
            self.config["auth"].pop("token", None)
            self.save_config()

    def get_user_info(self) -> Dict[str, Any]:
        """Get stored user information"""
        return self.config.get("user", {})

    def set_user_info(self, user_info: Dict[str, Any]):
        """Store user information"""
        self.config["user"] = user_info
        self.save_config()


class APIClient:
    """API client for remote workflow execution"""

    def __init__(self, base_url: str, token: Optional[str] = None):
        self.base_url = base_url
        self.token = token
        self.client = httpx.AsyncClient()

    async def close(self):
        """Close HTTP client"""
        await self.client.aclose()

    def _get_headers(self) -> Dict[str, str]:
        """Get request headers with authentication"""
        headers = {"Content-Type": "application/json"}
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"
        return headers

    async def execute_workflow(
        self, endpoint: str, data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Execute workflow via API"""
        try:
            response = await self.client.post(
                f"{self.base_url}{endpoint}", json=data, headers=self._get_headers()
            )
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 401:
                raise click.ClickException("Authentication failed. Please login first.")
            elif e.response.status_code == 403:
                raise click.ClickException(
                    "Insufficient permissions for this operation."
                )
            else:
                raise click.ClickException(f"API error: {e.response.text}")
        except Exception as e:
            raise click.ClickException(f"Request failed: {str(e)}")


# Global configuration
config = CLIConfig()


# ===== Main CLI Group =====


@click.group()
@click.option(
    "--api/--local", default=False, help="Use API mode (default: local execution)"
)
@click.pass_context
def cli(ctx, api):
    """Kailash User Management System CLI

    Comprehensive command-line interface for managing users, teams, and system administration.

    Run 'kailash-um --help' to see all available commands.
    """
    ctx.ensure_object(dict)
    ctx.obj["api_mode"] = api
    ctx.obj["config"] = config


# ===== Authentication Commands =====


@cli.group()
def auth():
    """Authentication management"""
    pass


@auth.command()
@click.option("--email", prompt=True, help="User email")
@click.option("--password", prompt=True, hide_input=True, help="User password")
@click.pass_context
async def login(ctx, email, password):
    """Login to the system"""
    if ctx.obj["api_mode"]:
        # Mock authentication - in production, this would call the actual auth endpoint
        import jwt

        token = jwt.encode(
            {
                "sub": email,
                "user_type": "user",  # Would be determined by auth
                "exp": datetime.now().timestamp() + 3600,
            },
            "your-secret-key",
            algorithm="HS256",
        )

        config.set_token(token)
        config.set_user_info({"email": email, "user_type": "user"})

        console.print("[green]✓ Login successful![/green]")
        console.print(f"Logged in as: {email}")
    else:
        console.print("[yellow]Local mode - no authentication required[/yellow]")


@auth.command()
@click.pass_context
def logout(ctx):
    """Logout from the system"""
    config.clear_token()
    console.print("[green]✓ Logged out successfully[/green]")


@auth.command()
@click.pass_context
def status(ctx):
    """Check authentication status"""
    token = config.get_token()
    user_info = config.get_user_info()

    if token:
        console.print("[green]✓ Authenticated[/green]")
        console.print(f"User: {user_info.get('email', 'Unknown')}")
        console.print(f"Type: {user_info.get('user_type', 'Unknown')}")
    else:
        console.print("[red]✗ Not authenticated[/red]")
        console.print("Run 'kailash-um auth login' to authenticate")


# ===== User Workflow Commands =====


@cli.group()
def user():
    """User workflows"""
    pass


@user.command()
@click.option("--first-name", prompt=True, help="First name")
@click.option("--last-name", prompt=True, help="Last name")
@click.option("--email", prompt=True, help="Email address")
@click.option("--phone", help="Phone number")
@click.option("--department", prompt=True, help="Department")
@click.option("--role", prompt=True, help="Role")
@click.pass_context
async def setup_profile(ctx, first_name, last_name, email, phone, department, role):
    """Setup user profile"""
    profile_data = {
        "first_name": first_name,
        "last_name": last_name,
        "email": email,
        "phone": phone,
        "department": department,
        "role": role,
        "preferences": {},
    }

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        task = progress.add_task("Setting up profile...", total=None)

        if ctx.obj["api_mode"]:
            # API mode
            api_client = APIClient(API_BASE_URL, config.get_token())
            try:
                result = await api_client.execute_workflow(
                    "/api/v1/user/profile/setup", profile_data
                )
                await api_client.close()

                if result["success"]:
                    console.print(
                        "[green]✓ Profile setup completed successfully![/green]"
                    )
                    console.print(f"Profile ID: {result['results'].get('profile_id')}")
                else:
                    console.print(
                        f"[red]✗ Profile setup failed: {result.get('error')}[/red]"
                    )
            except Exception as e:
                await api_client.close()
                raise
        else:
            # Local mode
            workflow = ProfileSetupWorkflow(email)
            results = workflow.setup_initial_profile(profile_data)

            console.print("[green]✓ Profile setup completed successfully![/green]")
            console.print(f"Profile ID: {results.get('profile_id')}")


@user.command()
@click.option("--resource-type", prompt=True, help="Resource type to access")
@click.option("--access-level", default="read", help="Access level (read/write/admin)")
@click.option("--justification", prompt=True, help="Justification for access")
@click.option("--duration-days", type=int, help="Duration in days")
@click.pass_context
async def request_access(
    ctx, resource_type, access_level, justification, duration_days
):
    """Request access to resources"""
    access_data = {
        "resource_type": resource_type,
        "access_level": access_level,
        "justification": justification,
        "duration_days": duration_days,
    }

    with console.status("Submitting access request..."):
        if ctx.obj["api_mode"]:
            api_client = APIClient(API_BASE_URL, config.get_token())
            try:
                result = await api_client.execute_workflow(
                    "/api/v1/user/access/request", access_data
                )
                await api_client.close()

                if result["success"]:
                    console.print("[green]✓ Access request submitted![/green]")
                    console.print(f"Request ID: {result['results'].get('request_id')}")
                    console.print(f"Status: {result['results'].get('status')}")
                else:
                    console.print(f"[red]✗ Request failed: {result.get('error')}[/red]")
            except Exception as e:
                await api_client.close()
                raise
        else:
            user_email = config.get_user_info().get("email", "test@example.com")
            workflow = AccessManagementWorkflow(user_email)
            access_data["requester"] = user_email
            results = workflow.request_system_access(access_data)

            console.print("[green]✓ Access request submitted![/green]")
            console.print(f"Request ID: {results.get('request_id')}")


@user.command()
@click.option(
    "--method",
    type=click.Choice(["totp", "sms", "email"]),
    prompt=True,
    help="MFA method",
)
@click.option("--phone-number", help="Phone number for SMS")
@click.pass_context
async def setup_mfa(ctx, method, phone_number):
    """Setup multi-factor authentication"""
    mfa_config = {
        "method": method,
        "phone_number": phone_number,
        "backup_codes_count": 8,
    }

    with console.status("Setting up MFA..."):
        if ctx.obj["api_mode"]:
            api_client = APIClient(API_BASE_URL, config.get_token())
            try:
                result = await api_client.execute_workflow(
                    "/api/v1/user/auth/mfa/setup", mfa_config
                )
                await api_client.close()

                if result["success"]:
                    console.print("[green]✓ MFA setup completed![/green]")
                    if result["results"].get("qr_code"):
                        console.print(
                            "\nScan this QR code with your authenticator app:"
                        )
                        console.print("[QR Code would be displayed here]")
                    if result["results"].get("backup_codes"):
                        console.print("\n[yellow]Backup codes (save these!):[/yellow]")
                        for code in result["results"]["backup_codes"]:
                            console.print(f"  • {code}")
                else:
                    console.print(
                        f"[red]✗ MFA setup failed: {result.get('error')}[/red]"
                    )
            except Exception as e:
                await api_client.close()
                raise
        else:
            user_email = config.get_user_info().get("email", "test@example.com")
            workflow = AuthenticationSetupWorkflow(user_email)
            results = workflow.setup_mfa(mfa_config)

            console.print("[green]✓ MFA setup completed![/green]")
            console.print(f"Secret: {results.get('secret')}")


@user.command()
@click.option(
    "--data-sharing/--no-data-sharing", default=False, help="Allow data sharing"
)
@click.option(
    "--marketing/--no-marketing", default=False, help="Receive marketing emails"
)
@click.option(
    "--analytics/--no-analytics", default=True, help="Allow analytics tracking"
)
@click.option(
    "--visibility", type=click.Choice(["public", "team", "private"]), default="team"
)
@click.pass_context
async def privacy_settings(ctx, data_sharing, marketing, analytics, visibility):
    """Manage privacy settings"""
    privacy_data = {
        "data_sharing": data_sharing,
        "marketing_emails": marketing,
        "analytics_tracking": analytics,
        "profile_visibility": visibility,
    }

    table = Table(title="Privacy Settings")
    table.add_column("Setting", style="cyan")
    table.add_column("Value", style="green")

    table.add_row("Data Sharing", "✓" if data_sharing else "✗")
    table.add_row("Marketing Emails", "✓" if marketing else "✗")
    table.add_row("Analytics Tracking", "✓" if analytics else "✗")
    table.add_row("Profile Visibility", visibility.title())

    console.print(table)

    if Confirm.ask("Apply these privacy settings?"):
        with console.status("Updating privacy settings..."):
            if ctx.obj["api_mode"]:
                api_client = APIClient(API_BASE_URL, config.get_token())
                try:
                    result = await api_client.execute_workflow(
                        "/api/v1/user/privacy/settings", privacy_data
                    )
                    await api_client.close()

                    if result["success"]:
                        console.print("[green]✓ Privacy settings updated![/green]")
                    else:
                        console.print(
                            f"[red]✗ Update failed: {result.get('error')}[/red]"
                        )
                except Exception as e:
                    await api_client.close()
                    raise
            else:
                user_email = config.get_user_info().get("email", "test@example.com")
                workflow = PrivacyControlsWorkflow(user_email)
                results = workflow.manage_privacy_settings(privacy_data)

                console.print("[green]✓ Privacy settings updated![/green]")


@user.command()
@click.option("--category", prompt=True, help="Support category")
@click.option(
    "--priority", type=click.Choice(["low", "medium", "high", "urgent"]), prompt=True
)
@click.option("--subject", prompt=True, help="Ticket subject")
@click.option("--description", prompt=True, help="Issue description")
@click.pass_context
async def support_ticket(ctx, category, priority, subject, description):
    """Create support ticket"""
    ticket_data = {
        "category": category,
        "priority": priority,
        "subject": subject,
        "description": description,
        "attachments": [],
    }

    with console.status("Creating support ticket..."):
        if ctx.obj["api_mode"]:
            api_client = APIClient(API_BASE_URL, config.get_token())
            try:
                result = await api_client.execute_workflow(
                    "/api/v1/user/support/ticket", ticket_data
                )
                await api_client.close()

                if result["success"]:
                    console.print("[green]✓ Support ticket created![/green]")
                    console.print(f"Ticket ID: {result['results'].get('ticket_id')}")
                    console.print(
                        f"Expected Response: {result['results'].get('expected_response')}"
                    )
                else:
                    console.print(
                        f"[red]✗ Ticket creation failed: {result.get('error')}[/red]"
                    )
            except Exception as e:
                await api_client.close()
                raise
        else:
            user_email = config.get_user_info().get("email", "test@example.com")
            workflow = SupportRequestWorkflow(user_email)
            results = workflow.create_support_ticket(ticket_data)

            console.print("[green]✓ Support ticket created![/green]")
            console.print(f"Ticket ID: {results.get('ticket_id')}")


# ===== Manager Workflow Commands =====


@cli.group()
def manager():
    """Manager workflows"""
    pass


@manager.command()
@click.option("--team-name", prompt=True, help="Team name")
@click.option("--description", prompt=True, help="Team description")
@click.option("--team-type", prompt=True, help="Team type")
@click.option("--members", multiple=True, help="Initial team members (emails)")
@click.pass_context
async def setup_team(ctx, team_name, description, team_type, members):
    """Setup new team"""
    if not members:
        members = []
        console.print("Enter team member emails (press Enter when done):")
        while True:
            email = Prompt.ask("Email", default="")
            if not email:
                break
            members.append(email)

    team_data = {
        "team_name": team_name,
        "team_description": description,
        "team_type": team_type,
        "initial_members": list(members),
        "team_goals": [],
    }

    with console.status("Creating team..."):
        if ctx.obj["api_mode"]:
            api_client = APIClient(API_BASE_URL, config.get_token())
            try:
                result = await api_client.execute_workflow(
                    "/api/v1/manager/team/setup", team_data
                )
                await api_client.close()

                if result["success"]:
                    console.print("[green]✓ Team created successfully![/green]")
                    console.print(f"Team ID: {result['results'].get('team_id')}")
                else:
                    console.print(
                        f"[red]✗ Team creation failed: {result.get('error')}[/red]"
                    )
            except Exception as e:
                await api_client.close()
                raise
        else:
            manager_email = config.get_user_info().get("email", "manager@example.com")
            workflow = TeamSetupWorkflow(manager_email)
            results = workflow.create_new_team(team_data)

            console.print("[green]✓ Team created successfully![/green]")
            console.print(f"Team ID: {results.get('team_id')}")


@manager.command()
@click.option("--action", type=click.Choice(["add", "remove", "update"]), prompt=True)
@click.option("--email", prompt=True, help="User email")
@click.option("--role", help="User role")
@click.option("--permissions", multiple=True, help="User permissions")
@click.pass_context
async def team_member(ctx, action, email, role, permissions):
    """Manage team members"""
    request_data = {
        "action": action,
        "user_email": email,
        "role": role,
        "permissions": list(permissions) if permissions else None,
    }

    with console.status(f"{action.title()}ing team member..."):
        if ctx.obj["api_mode"]:
            api_client = APIClient(API_BASE_URL, config.get_token())
            try:
                result = await api_client.execute_workflow(
                    "/api/v1/manager/team/members", request_data
                )
                await api_client.close()

                if result["success"]:
                    console.print(
                        f"[green]✓ Team member {action}ed successfully![/green]"
                    )
                else:
                    console.print(
                        f"[red]✗ Operation failed: {result.get('error')}[/red]"
                    )
            except Exception as e:
                await api_client.close()
                raise
        else:
            manager_email = config.get_user_info().get("email", "manager@example.com")
            workflow = UserManagementWorkflow(manager_email)

            if action == "add":
                member_data = {
                    "email": email,
                    "role": role,
                    "permissions": list(permissions) if permissions else [],
                    "department": "Engineering",
                }
                results = workflow.add_team_member(member_data)
            elif action == "remove":
                results = workflow.remove_team_member({"user_email": email})
            else:
                results = workflow.update_team_member(
                    {
                        "user_email": email,
                        "updates": {"role": role, "permissions": list(permissions)},
                    }
                )

            console.print(f"[green]✓ Team member {action}ed successfully![/green]")


@manager.command()
@click.option(
    "--report-type",
    type=click.Choice(["team_performance", "activity_monitoring", "custom"]),
    prompt=True,
)
@click.option("--period", default="monthly", help="Report period")
@click.option("--format", type=click.Choice(["json", "csv", "pdf"]), default="json")
@click.pass_context
async def generate_report(ctx, report_type, period, format):
    """Generate reports"""
    report_data = {
        "report_type": report_type,
        "period": period,
        "format": format,
        "include_trends": True,
    }

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        task = progress.add_task("Generating report...", total=None)

        if ctx.obj["api_mode"]:
            api_client = APIClient(API_BASE_URL, config.get_token())
            try:
                result = await api_client.execute_workflow(
                    "/api/v1/manager/reports/generate", report_data
                )
                await api_client.close()

                if result["success"]:
                    console.print("[green]✓ Report generated successfully![/green]")

                    # Display report preview
                    if format == "json" and result.get("results"):
                        console.print("\n[bold]Report Preview:[/bold]")
                        console.print(
                            Panel(
                                Syntax(json.dumps(result["results"], indent=2), "json"),
                                title=f"{report_type.replace('_', ' ').title()} Report",
                            )
                        )
                else:
                    console.print(
                        f"[red]✗ Report generation failed: {result.get('error')}[/red]"
                    )
            except Exception as e:
                await api_client.close()
                raise
        else:
            manager_email = config.get_user_info().get("email", "manager@example.com")
            workflow = ReportingAnalyticsWorkflow(manager_email)

            if report_type == "team_performance":
                results = workflow.generate_team_performance_report(
                    {
                        "department": "Engineering",
                        "period": period,
                        "include_trends": True,
                    }
                )
            else:
                results = workflow.generate_custom_report(report_data)

            console.print("[green]✓ Report generated successfully![/green]")
            console.print(f"Report saved to: {results.get('report_path')}")


@manager.command()
@click.pass_context
async def pending_approvals(ctx):
    """View pending approval requests"""
    with console.status("Fetching pending approvals..."):
        manager_email = config.get_user_info().get("email", "manager@example.com")
        workflow = ApprovalWorkflow(manager_email)

        # Get pending approvals
        results = workflow.get_pending_approvals({})
        pending = results.get("pending_approvals", [])

        if pending:
            table = Table(title="Pending Approval Requests")
            table.add_column("Request ID", style="cyan")
            table.add_column("Requester", style="yellow")
            table.add_column("Resource", style="green")
            table.add_column("Created", style="blue")

            for request in pending:
                table.add_row(
                    request["request_id"],
                    request["requester"],
                    request["resource"],
                    request["created_at"],
                )

            console.print(table)
        else:
            console.print("[yellow]No pending approval requests[/yellow]")


# ===== Admin Workflow Commands =====


@cli.group()
def admin():
    """Admin workflows"""
    pass


@admin.command()
@click.option("--company-name", prompt=True, help="Company name")
@click.option("--domain", prompt=True, help="Company domain")
@click.option("--admin-email", prompt=True, help="Admin email")
@click.option(
    "--plan", type=click.Choice(["starter", "professional", "enterprise"]), prompt=True
)
@click.option("--user-count", type=int, default=10, help="Initial user count")
@click.pass_context
async def onboard_tenant(ctx, company_name, domain, admin_email, plan, user_count):
    """Onboard new tenant"""
    tenant_data = {
        "company_name": company_name,
        "company_domain": domain,
        "admin_email": admin_email,
        "subscription_plan": plan,
        "initial_user_count": user_count,
        "features": [],
    }

    # Add features based on plan
    if plan == "enterprise":
        tenant_data["features"] = [
            "sso",
            "advanced_analytics",
            "api_access",
            "custom_branding",
        ]
    elif plan == "professional":
        tenant_data["features"] = ["advanced_analytics", "api_access"]

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        task = progress.add_task("Onboarding tenant...", total=None)

        if ctx.obj["api_mode"]:
            api_client = APIClient(API_BASE_URL, config.get_token())
            try:
                result = await api_client.execute_workflow(
                    "/api/v1/admin/tenant/onboard", tenant_data
                )
                await api_client.close()

                if result["success"]:
                    console.print("[green]✓ Tenant onboarded successfully![/green]")
                    console.print(f"Tenant ID: {result['results'].get('tenant_id')}")
                    console.print(f"Admin Credentials sent to: {admin_email}")
                else:
                    console.print(
                        f"[red]✗ Onboarding failed: {result.get('error')}[/red]"
                    )
            except Exception as e:
                await api_client.close()
                raise
        else:
            admin_user = config.get_user_info().get("email", "admin@example.com")
            workflow = SystemOnboardingWorkflow(admin_user)
            results = workflow.onboard_new_tenant(tenant_data)

            console.print("[green]✓ Tenant onboarded successfully![/green]")
            console.print(f"Tenant ID: {results.get('tenant_id')}")


@admin.command()
@click.option(
    "--action", type=click.Choice(["create", "disable", "delete"]), prompt=True
)
@click.option(
    "--csv-file", type=click.Path(exists=True), help="CSV file with user data"
)
@click.pass_context
async def bulk_users(ctx, action, csv_file):
    """Bulk user operations"""
    user_data = []

    if csv_file:
        # Read from CSV
        import csv

        with open(csv_file, "r") as f:
            reader = csv.DictReader(f)
            user_data = list(reader)
    else:
        # Interactive input
        console.print(f"Enter user details for bulk {action} (press Enter when done):")
        while True:
            email = Prompt.ask("Email", default="")
            if not email:
                break

            user = {"email": email}
            if action == "create":
                user["first_name"] = Prompt.ask("First name")
                user["last_name"] = Prompt.ask("Last name")
                user["role"] = Prompt.ask("Role", default="user")

            user_data.append(user)

    if not user_data:
        console.print("[yellow]No users specified[/yellow]")
        return

    # Confirm action
    console.print(f"\n[bold]Will {action} {len(user_data)} users:[/bold]")
    for user in user_data[:5]:  # Show first 5
        console.print(f"  • {user['email']}")
    if len(user_data) > 5:
        console.print(f"  ... and {len(user_data) - 5} more")

    if not Confirm.ask(f"\nProceed with bulk {action}?"):
        console.print("[yellow]Operation cancelled[/yellow]")
        return

    request_data = {
        "action": action,
        "user_data": user_data,
        "send_notifications": True,
    }

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        task = progress.add_task(f"Processing bulk {action}...", total=None)

        if ctx.obj["api_mode"]:
            api_client = APIClient(API_BASE_URL, config.get_token())
            try:
                result = await api_client.execute_workflow(
                    "/api/v1/admin/users/bulk", request_data
                )
                await api_client.close()

                if result["success"]:
                    console.print(f"[green]✓ Bulk {action} completed![/green]")
                    console.print(
                        f"Processed: {result['results'].get('processed_count', len(user_data))} users"
                    )
                else:
                    console.print(
                        f"[red]✗ Operation failed: {result.get('error')}[/red]"
                    )
            except Exception as e:
                await api_client.close()
                raise
        else:
            admin_user = config.get_user_info().get("email", "admin@example.com")
            workflow = UserAdministrationWorkflow(admin_user)

            if action == "create":
                results = workflow.bulk_create_users(
                    {"users": user_data, "send_invitations": True}
                )
            else:
                results = workflow.manage_user_lifecycle(
                    {
                        "action": action,
                        "users": user_data,
                        "reason": "Bulk operation via CLI",
                    }
                )

            console.print(f"[green]✓ Bulk {action} completed![/green]")
            console.print(f"Processed: {results.get('processed_count')} users")


@admin.command()
@click.option(
    "--scan/--monitor", default=True, help="Scan for threats or monitor activity"
)
@click.pass_context
async def security_check(ctx, scan):
    """Security monitoring and threat detection"""
    with console.status("Running security check..."):
        admin_user = config.get_user_info().get("email", "admin@example.com")
        workflow = SecurityManagementWorkflow(admin_user)

        if scan:
            results = workflow.monitor_security_threats({})
            threats = results.get("threats_detected", [])

            if threats:
                console.print("[red]⚠️  Security Threats Detected![/red]")

                table = Table(title="Security Threats", show_header=True)
                table.add_column("Type", style="red")
                table.add_column("Severity", style="yellow")
                table.add_column("Description")
                table.add_column("Action Required")

                for threat in threats:
                    table.add_row(
                        threat["type"],
                        threat["severity"],
                        threat["description"],
                        threat["action"],
                    )

                console.print(table)
            else:
                console.print("[green]✓ No security threats detected[/green]")
        else:
            # Monitor mode
            console.print(
                "[yellow]Starting security monitoring... (Press Ctrl+C to stop)[/yellow]"
            )
            try:
                while True:
                    await asyncio.sleep(5)
                    # Would implement real-time monitoring here
                    console.print(".", end="")
            except KeyboardInterrupt:
                console.print("\n[yellow]Monitoring stopped[/yellow]")


@admin.command()
@click.option(
    "--type", type=click.Choice(["full", "incremental", "selective"]), default="full"
)
@click.option("--encrypt/--no-encrypt", default=True, help="Enable encryption")
@click.option("--retention-days", type=int, default=30, help="Backup retention period")
@click.pass_context
async def backup(ctx, type, encrypt, retention_days):
    """Create system backup"""
    backup_config = {
        "backup_type": type,
        "include_files": True,
        "include_database": True,
        "encryption_enabled": encrypt,
        "retention_days": retention_days,
    }

    # Show backup details
    console.print("[bold]Backup Configuration:[/bold]")
    console.print(f"  Type: {type}")
    console.print(f"  Encryption: {'Enabled' if encrypt else 'Disabled'}")
    console.print(f"  Retention: {retention_days} days")

    if not Confirm.ask("\nStart backup?"):
        console.print("[yellow]Backup cancelled[/yellow]")
        return

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        task = progress.add_task("Creating backup...", total=None)

        if ctx.obj["api_mode"]:
            api_client = APIClient(API_BASE_URL, config.get_token())
            try:
                result = await api_client.execute_workflow(
                    "/api/v1/admin/backup/create", backup_config
                )
                await api_client.close()

                if result["success"]:
                    console.print("[green]✓ Backup initiated successfully![/green]")
                    console.print(
                        result["results"].get("message", "Backup in progress")
                    )
                else:
                    console.print(f"[red]✗ Backup failed: {result.get('error')}[/red]")
            except Exception as e:
                await api_client.close()
                raise
        else:
            admin_user = config.get_user_info().get("email", "admin@example.com")
            workflow = BackupRecoveryWorkflow(admin_user)
            results = workflow.manage_backup_operations(backup_config)

            console.print("[green]✓ Backup completed successfully![/green]")
            console.print(f"Backup ID: {results.get('backup_id')}")
            console.print(f"Location: {results.get('backup_location')}")


# ===== Utility Commands =====


@cli.command()
@click.pass_context
def dashboard(ctx):
    """Show system dashboard"""
    console.print(
        Panel.fit(
            "[bold cyan]Kailash User Management System[/bold cyan]\n"
            "Enterprise-grade user and team management",
            border_style="cyan",
        )
    )

    # System status
    status_table = Table(title="System Status", show_header=False)
    status_table.add_column("Metric", style="cyan")
    status_table.add_column("Value", style="green")

    if ctx.obj["api_mode"]:
        status_table.add_row("Mode", "API (Remote)")
        status_table.add_row("API Server", API_BASE_URL)
    else:
        status_table.add_row("Mode", "Local Execution")

    user_info = config.get_user_info()
    if user_info:
        status_table.add_row("Current User", user_info.get("email", "Unknown"))
        status_table.add_row("User Type", user_info.get("user_type", "Unknown").title())
    else:
        status_table.add_row("Authentication", "Not logged in")

    console.print(status_table)

    # Available commands
    console.print("\n[bold]Available Commands:[/bold]")
    console.print("  [cyan]User Workflows:[/cyan]")
    console.print("    • kailash-um user setup-profile")
    console.print("    • kailash-um user request-access")
    console.print("    • kailash-um user setup-mfa")
    console.print("    • kailash-um user privacy-settings")
    console.print("    • kailash-um user support-ticket")

    console.print("\n  [cyan]Manager Workflows:[/cyan]")
    console.print("    • kailash-um manager setup-team")
    console.print("    • kailash-um manager team-member")
    console.print("    • kailash-um manager generate-report")
    console.print("    • kailash-um manager pending-approvals")

    console.print("\n  [cyan]Admin Workflows:[/cyan]")
    console.print("    • kailash-um admin onboard-tenant")
    console.print("    • kailash-um admin bulk-users")
    console.print("    • kailash-um admin security-check")
    console.print("    • kailash-um admin backup")

    console.print(
        "\n[dim]Run 'kailash-um --help' for detailed command information[/dim]"
    )


@cli.command()
@click.option("--output", type=click.Path(), default="config.yaml", help="Output file")
@click.pass_context
def export_config(ctx, output):
    """Export configuration"""
    config_data = {
        "api_base_url": API_BASE_URL,
        "user_info": config.get_user_info(),
        "preferences": config.config.get("preferences", {}),
    }

    with open(output, "w") as f:
        yaml.dump(config_data, f)

    console.print(f"[green]✓ Configuration exported to {output}[/green]")


# ===== Main Entry Point =====


def main():
    """Main entry point with async support"""
    # Handle async commands
    import inspect

    def async_command(f):
        """Wrapper for async Click commands"""

        @click.pass_context
        def wrapper(ctx, *args, **kwargs):
            return asyncio.run(f(ctx, *args, **kwargs))

        wrapper.__name__ = f.__name__
        wrapper.__doc__ = f.__doc__

        # Copy Click decorators
        wrapper.params = getattr(f, "params", [])

        return wrapper

    # Patch async commands
    for group in [user, manager, admin, auth]:
        for name, cmd in group.commands.items():
            if inspect.iscoroutinefunction(cmd.callback):
                cmd.callback = async_command(cmd.callback)

    # Run CLI
    try:
        cli()
    except click.ClickException as e:
        console.print(f"[red]Error: {e.message}[/red]")
        sys.exit(1)
    except KeyboardInterrupt:
        console.print("\n[yellow]Operation cancelled by user[/yellow]")
        sys.exit(0)
    except Exception as e:
        console.print(f"[red]Unexpected error: {str(e)}[/red]")
        if os.getenv("DEBUG"):
            console.print_exception()
        sys.exit(1)


if __name__ == "__main__":
    main()
