"""
Studio CLI Interface - SDK Gateway Integration

Command-line interface for Kailash Studio using the SDK gateway client.
Uses enterprise middleware instead of manual orchestration.
"""

import asyncio
import logging
import sys

import click
import httpx
import uvicorn

from ..core.config import config

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class StudioGatewayClient:
    """Client for interacting with the Studio API gateway."""

    def __init__(self, base_url: str = None):
        self.base_url = base_url or f"http://{config.host}:{config.port}"
        self.client = httpx.AsyncClient(base_url=self.base_url)

    async def close(self):
        await self.client.aclose()

    async def get_workflows(
        self, tenant: str = "default", status: str = None, owner: str = None
    ):
        """Get workflows via SDK gateway."""
        params = {"tenant_id": tenant}
        if status:
            params["status"] = status
        if owner:
            params["owner_id"] = owner

        response = await self.client.get("/api/workflows", params=params)
        response.raise_for_status()
        return response.json()

    async def create_workflow(
        self, name: str, description: str = "", tenant: str = "default"
    ):
        """Create workflow via SDK gateway."""
        data = {"name": name, "description": description, "tenant_id": tenant}
        response = await self.client.post("/api/workflows", json=data)
        response.raise_for_status()
        return response.json()

    async def delete_workflow(self, workflow_id: str, tenant: str = "default"):
        """Delete workflow via SDK gateway."""
        response = await self.client.delete(
            f"/api/workflows/{workflow_id}?tenant_id={tenant}"
        )
        return response.status_code == 200

    async def get_executions(
        self,
        workflow_id: str = None,
        tenant: str = "default",
        status: str = None,
        limit: int = 10,
    ):
        """Get executions via SDK gateway."""
        params = {"tenant_id": tenant, "limit": limit}
        if workflow_id:
            params["workflow_id"] = workflow_id
        if status:
            params["status"] = status

        response = await self.client.get("/api/executions", params=params)
        response.raise_for_status()
        return response.json()

    async def cancel_execution(self, execution_id: str, tenant: str = "default"):
        """Cancel execution via SDK gateway."""
        response = await self.client.post(
            f"/api/executions/{execution_id}/cancel?tenant_id={tenant}"
        )
        return response.status_code == 200

    async def get_templates(self, category: str = None):
        """Get templates via SDK gateway."""
        params = {}
        if category:
            params["category"] = category

        response = await self.client.get("/api/templates", params=params)
        response.raise_for_status()
        return response.json()

    async def get_stats(self, tenant: str = "default"):
        """Get stats via SDK gateway."""
        response = await self.client.get(f"/api/stats?tenant_id={tenant}")
        response.raise_for_status()
        return response.json()

    async def cleanup_executions(self, days: int = 30, tenant: str = "default"):
        """Cleanup old executions via SDK gateway."""
        response = await self.client.post(
            f"/api/cleanup?days={days}&tenant_id={tenant}"
        )
        response.raise_for_status()
        return response.json()


@click.group()
@click.version_option(version="1.0.0")
def cli():
    """Kailash Studio - Visual Workflow Builder CLI."""
    pass


@cli.command()
@click.option("--host", default=config.host, help="Host to bind to")
@click.option("--port", default=config.port, help="Port to bind to")
@click.option("--reload", is_flag=True, help="Enable auto-reload")
@click.option("--debug", is_flag=True, help="Enable debug mode")
def server(host, port, reload, debug):
    """Start the Studio API server."""
    click.echo(f"🚀 Starting Kailash Studio API on {host}:{port}")

    # Update config
    config.host = host
    config.port = port
    config.reload = reload
    config.debug = debug

    uvicorn.run(
        "apps.studio.api.main:app",
        host=host,
        port=port,
        reload=reload,
        log_level="debug" if debug else "info",
    )


@cli.command()
def init():
    """Initialize the Studio database via gateway."""

    async def init_db():
        try:
            client = StudioGatewayClient()
            # The SDK gateway handles database initialization automatically
            # Just verify the server is running and accessible
            stats = await client.get_stats()
            await client.close()

            click.echo("✅ Studio gateway connection verified")
            click.echo(f"📊 System stats: {stats}")

        except Exception as e:
            click.echo(f"❌ Failed to connect to Studio gateway: {str(e)}")
            click.echo("💡 Make sure the Studio server is running: studio server")
            sys.exit(1)

    asyncio.run(init_db())


@cli.group()
def workflows():
    """Workflow management commands."""
    pass


@workflows.command("list")
@click.option("--tenant", default="default", help="Tenant ID")
@click.option("--status", help="Filter by status")
@click.option("--owner", help="Filter by owner")
def list_workflows(tenant, status, owner):
    """List workflows via SDK gateway."""

    async def list_wf():
        try:
            client = StudioGatewayClient()
            workflows_data = await client.get_workflows(tenant, status, owner)
            await client.close()

            workflows = workflows_data.get("workflows", [])

            if not workflows:
                click.echo("No workflows found")
                return

            click.echo(f"\n📋 Found {len(workflows)} workflows:")
            click.echo("-" * 80)

            for wf in workflows:
                status_emoji = {
                    "draft": "📝",
                    "active": "✅",
                    "archived": "📦",
                    "template": "📋",
                }.get(wf.get("status", "draft"), "❓")

                click.echo(f"{status_emoji} {wf.get('name', 'Unnamed')}")
                click.echo(f"   ID: {wf.get('workflow_id', 'N/A')}")
                click.echo(f"   Status: {wf.get('status', 'N/A')}")
                nodes_count = len(wf.get("nodes", []))
                connections_count = len(wf.get("connections", []))
                click.echo(f"   Nodes: {nodes_count}, Connections: {connections_count}")
                if wf.get("created_at"):
                    click.echo(f"   Created: {wf['created_at'][:16]}")
                if wf.get("description"):
                    click.echo(f"   Description: {wf['description']}")
                click.echo()

        except Exception as e:
            click.echo(f"❌ Failed to list workflows: {str(e)}")
            sys.exit(1)

    asyncio.run(list_wf())


@workflows.command("create")
@click.argument("name")
@click.option("--description", help="Workflow description")
@click.option("--tenant", default="default", help="Tenant ID")
def create_workflow(name, description, tenant):
    """Create a new workflow via SDK gateway."""

    async def create_wf():
        try:
            client = StudioGatewayClient()
            workflow = await client.create_workflow(name, description or "", tenant)
            await client.close()

            click.echo(f"✅ Created workflow: {workflow.get('workflow_id', 'N/A')}")
            click.echo(f"   Name: {workflow.get('name', 'N/A')}")
            click.echo(f"   Description: {workflow.get('description', 'N/A')}")

        except Exception as e:
            click.echo(f"❌ Failed to create workflow: {str(e)}")
            sys.exit(1)

    asyncio.run(create_wf())


@workflows.command("delete")
@click.argument("workflow_id")
@click.option("--tenant", default="default", help="Tenant ID")
@click.confirmation_option(prompt="Are you sure you want to delete this workflow?")
def delete_workflow(workflow_id, tenant):
    """Delete a workflow via SDK gateway."""

    async def delete_wf():
        try:
            client = StudioGatewayClient()
            success = await client.delete_workflow(workflow_id, tenant)
            await client.close()

            if success:
                click.echo(f"✅ Deleted workflow: {workflow_id}")
            else:
                click.echo(f"❌ Workflow not found: {workflow_id}")
                sys.exit(1)

        except Exception as e:
            click.echo(f"❌ Failed to delete workflow: {str(e)}")
            sys.exit(1)

    asyncio.run(delete_wf())


@cli.group()
def executions():
    """Execution management commands."""
    pass


@executions.command("list")
@click.option("--workflow-id", help="Filter by workflow ID")
@click.option("--tenant", default="default", help="Tenant ID")
@click.option("--status", help="Filter by status")
@click.option("--limit", default=10, help="Number of executions to show")
def list_executions(workflow_id, tenant, status, limit):
    """List workflow executions via SDK gateway."""

    async def list_exec():
        try:
            client = StudioGatewayClient()
            executions_data = await client.get_executions(
                workflow_id, tenant, status, limit
            )
            await client.close()

            executions = executions_data.get("executions", [])

            if not executions:
                click.echo("No executions found")
                return

            click.echo(f"\n🔄 Found {len(executions)} executions:")
            click.echo("-" * 80)

            for exec_data in executions:
                status_emoji = {
                    "pending": "⏳",
                    "running": "🔄",
                    "completed": "✅",
                    "failed": "❌",
                    "cancelled": "🚫",
                }.get(exec_data.get("status", "pending"), "❓")

                click.echo(f"{status_emoji} {exec_data.get('execution_id', 'N/A')}")
                click.echo(f"   Workflow: {exec_data.get('workflow_id', 'N/A')}")
                click.echo(f"   Status: {exec_data.get('status', 'N/A')}")
                progress = exec_data.get("progress", {}).get("progress_percentage", 0)
                click.echo(f"   Progress: {progress:.1f}%")
                if exec_data.get("started_at"):
                    click.echo(f"   Started: {exec_data['started_at'][:19]}")
                if exec_data.get("runtime_seconds"):
                    click.echo(f"   Runtime: {exec_data['runtime_seconds']:.2f}s")
                if exec_data.get("error_message"):
                    click.echo(f"   Error: {exec_data['error_message']}")
                click.echo()

        except Exception as e:
            click.echo(f"❌ Failed to list executions: {str(e)}")
            sys.exit(1)

    asyncio.run(list_exec())


@executions.command("cancel")
@click.argument("execution_id")
@click.option("--tenant", default="default", help="Tenant ID")
def cancel_execution(execution_id, tenant):
    """Cancel a running execution via SDK gateway."""

    async def cancel_exec():
        try:
            client = StudioGatewayClient()
            success = await client.cancel_execution(execution_id, tenant)
            await client.close()

            if success:
                click.echo(f"✅ Cancelled execution: {execution_id}")
            else:
                click.echo(f"❌ Could not cancel execution: {execution_id}")
                sys.exit(1)

        except Exception as e:
            click.echo(f"❌ Failed to cancel execution: {str(e)}")
            sys.exit(1)

    asyncio.run(cancel_exec())


@cli.group()
def templates():
    """Template management commands."""
    pass


@templates.command("list")
@click.option("--category", help="Filter by category")
def list_templates(category):
    """List workflow templates via SDK gateway."""

    async def list_tmpl():
        try:
            client = StudioGatewayClient()
            templates_data = await client.get_templates(category)
            await client.close()

            templates = templates_data.get("templates", [])

            if not templates:
                click.echo("No templates found")
                return

            click.echo(f"\n📋 Found {len(templates)} templates:")
            click.echo("-" * 80)

            for tmpl in templates:
                category_emoji = {
                    "business": "💼",
                    "data_processing": "📊",
                    "ai_orchestration": "🤖",
                    "api_integration": "🔌",
                    "enterprise_automation": "🏢",
                    "quality_assurance": "✅",
                }.get(tmpl.get("category", "business"), "📄")

                click.echo(f"{category_emoji} {tmpl.get('name', 'Unnamed')}")
                click.echo(f"   ID: {tmpl.get('template_id', 'N/A')}")
                click.echo(f"   Category: {tmpl.get('category', 'N/A')}")
                click.echo(f"   Difficulty: {tmpl.get('difficulty_level', 'N/A')}")
                click.echo(f"   Usage: {tmpl.get('usage_count', 0)} times")
                nodes_count = len(tmpl.get("workflow_definition", {}).get("nodes", []))
                click.echo(f"   Nodes: {nodes_count}")
                if tmpl.get("description"):
                    click.echo(f"   Description: {tmpl['description']}")
                click.echo()

        except Exception as e:
            click.echo(f"❌ Failed to list templates: {str(e)}")
            sys.exit(1)

    asyncio.run(list_tmpl())


@cli.command()
@click.option("--tenant", default="default", help="Tenant ID")
def stats(tenant):
    """Show Studio statistics via SDK gateway."""

    async def show_stats():
        try:
            client = StudioGatewayClient()
            stats_data = await client.get_stats(tenant)
            await client.close()

            click.echo("\n📊 Kailash Studio Statistics")
            click.echo("=" * 40)

            # Workflows
            wf_stats = stats_data.get("workflows", {})
            click.echo(f"\n📋 Workflows: {wf_stats.get('total', 0)} total")
            for status, count in wf_stats.get("by_status", {}).items():
                click.echo(f"   {status}: {count}")

            # Executions
            exec_stats = stats_data.get("executions", {})
            click.echo(f"\n🔄 Executions: {exec_stats.get('total', 0)} total")
            for status, count in exec_stats.get("by_status", {}).items():
                click.echo(f"   {status}: {count}")

            # Templates
            tmpl_stats = stats_data.get("templates", {})
            click.echo(f"\n📄 Templates: {tmpl_stats.get('total', 0)} total")
            for category, count in tmpl_stats.get("by_category", {}).items():
                click.echo(f"   {category}: {count}")

        except Exception as e:
            click.echo(f"❌ Failed to get stats: {str(e)}")
            sys.exit(1)

    asyncio.run(show_stats())


@cli.command()
@click.option("--days", default=30, help="Clean executions older than N days")
@click.option("--tenant", default="default", help="Tenant ID")
def cleanup(days, tenant):
    """Clean up old executions and data via SDK gateway."""

    async def cleanup_data():
        try:
            client = StudioGatewayClient()
            result = await client.cleanup_executions(days, tenant)
            await client.close()

            deleted = result.get("deleted_count", 0)
            click.echo(
                f"✅ Cleaned up {deleted} old executions (older than {days} days)"
            )

        except Exception as e:
            click.echo(f"❌ Failed to cleanup: {str(e)}")
            sys.exit(1)

    asyncio.run(cleanup_data())


@cli.command()
def version():
    """Show version information."""
    click.echo("Kailash Studio CLI v1.0.0")
    click.echo("Part of the Kailash Python SDK")
    click.echo("https://github.com/kailash-sdk/kailash-python-sdk")


if __name__ == "__main__":
    cli()
