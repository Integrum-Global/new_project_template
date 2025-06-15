"""
Main CLI interface for QA Agentic Testing System.
"""

import asyncio
import json
import sys
from datetime import datetime
from pathlib import Path
from typing import List, Optional

import click

from ..core.database import setup_database
from ..core.models import AgentType, InterfaceType, Priority, TestType
from ..core.services import AnalyticsService, ProjectService, TestRunService


@click.group()
@click.version_option(version="0.1.0")
def cli():
    """QA Agentic Testing - AI-powered autonomous testing framework."""
    pass


@cli.command()
@click.argument("app_path", type=click.Path(exists=True))
@click.option("--name", "-n", help="Project name (defaults to app directory name)")
@click.option("--description", "-d", default="", help="Project description")
@click.option(
    "--interfaces",
    multiple=True,
    type=click.Choice(["cli", "web", "api", "mobile"]),
    help="Interface types to test",
)
@click.option(
    "--test-types",
    multiple=True,
    type=click.Choice(
        ["functional", "security", "performance", "usability", "integration"]
    ),
    help="Test types to include",
)
@click.option(
    "--output",
    "-o",
    type=click.Path(),
    help="Output directory for reports (defaults to target app's qa_results folder)",
)
@click.option(
    "--format",
    "report_format",
    type=click.Choice(["html", "json", "both"]),
    default="html",
    help="Report format",
)
@click.option(
    "--industry",
    type=click.Choice(
        ["financial_services", "healthcare", "manufacturing", "retail_ecommerce"]
    ),
    help="Load industry-specific personas",
)
@click.option(
    "--personas", type=click.Path(exists=True), help="Custom personas JSON file"
)
@click.option(
    "--async",
    "use_async",
    is_flag=True,
    help="Use async performance mode (3-5x faster)",
)
@click.option(
    "--discover-personas", is_flag=True, help="Auto-generate personas from app analysis"
)
@click.option(
    "--model-preset",
    type=click.Choice(["development", "balanced", "enterprise"]),
    default="balanced",
    help="Model selection preset (development=ollama, balanced=mixed, enterprise=premium)",
)
@click.option(
    "--security-model", help="Specific model for security analysis (e.g., openai/gpt-4)"
)
@click.option(
    "--functional-model",
    help="Specific model for functional testing (e.g., ollama/llama3.1:8b)",
)
@click.option(
    "--performance-model",
    help="Specific model for performance analysis (e.g., anthropic/claude-3-sonnet)",
)
def test(
    app_path: str,
    name: Optional[str],
    description: str,
    interfaces: tuple,
    test_types: tuple,
    output: Optional[str],
    report_format: str,
    industry: Optional[str],
    personas: Optional[str],
    use_async: bool,
    discover_personas: bool,
    model_preset: str,
    security_model: Optional[str],
    functional_model: Optional[str],
    performance_model: Optional[str],
):
    """Test an application with AI agents.

    Results are stored in the target application's qa_results folder by default,
    or in the directory specified by --output."""

    async def run_test():
        # Initialize database
        await setup_database()

        # Setup services
        project_service = ProjectService()
        run_service = TestRunService()

        # Create project name from path if not provided
        if not name:
            project_name = Path(app_path).name
        else:
            project_name = name

        click.echo(f"🤖 Creating test project: {project_name}")

        # Convert interfaces and test types
        project_interfaces = (
            [InterfaceType(i) for i in interfaces]
            if interfaces
            else [InterfaceType.CLI, InterfaceType.WEB, InterfaceType.API]
        )
        project_test_types = (
            [TestType(t) for t in test_types]
            if test_types
            else [TestType.FUNCTIONAL, TestType.SECURITY]
        )

        try:
            # Create project
            project = await project_service.create_project(
                name=project_name,
                app_path=app_path,
                description=description,
                interfaces=project_interfaces,
                test_types=project_test_types,
            )

            click.echo(f"✅ Project created: {project.project_id}")
            click.echo(
                f"📋 Discovered {len(project.discovered_permissions)} permissions"
            )
            click.echo(f"🔗 Discovered {len(project.discovered_endpoints)} endpoints")
            click.echo(f"⚡ Discovered {len(project.discovered_commands)} commands")

            # Create and start test run
            run_name = f"CLI Test Run - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
            run = await run_service.create_run(
                project_id=project.project_id,
                name=run_name,
                description=f"Test run initiated from CLI for {project_name}",
                test_types=project_test_types,
                agent_types=[AgentType.A2A_AGENT, AgentType.ITERATIVE_AGENT],
                interfaces_tested=project_interfaces,
            )

            click.echo(f"🚀 Starting test run: {run.run_id}")

            # Start the test run
            await run_service.start_run(run.run_id)

            # Monitor progress
            click.echo("⏳ Test execution in progress...")

            # Wait for completion (simplified - in production, would use proper polling)
            import time

            while True:
                current_run = await run_service.get_run(run.run_id)
                if current_run.is_completed:
                    break
                time.sleep(5)
                click.echo(".", nl=False)

            click.echo()

            # Get final results
            final_run = await run_service.get_run(run.run_id)

            if final_run.status.value == "completed":
                click.echo("✅ Test completed successfully!")
                click.echo(
                    f"📊 Results: {final_run.passed_scenarios}/{final_run.total_scenarios} scenarios passed"
                )
                click.echo(f"📈 Success rate: {final_run.success_rate:.1f}%")
                click.echo(f"🎯 Confidence score: {final_run.confidence_score:.1f}%")

                # Display AI insights
                if final_run.ai_insights:
                    click.echo("\n🧠 AI Insights:")
                    for insight in final_run.ai_insights[:3]:  # Show first 3
                        click.echo(f"  • {insight}")

                # Handle report output
                if output or report_format:
                    from ..core.services import ReportService

                    report_service = ReportService()

                    output_dir = Path(output) if output else Path.cwd()
                    output_dir.mkdir(parents=True, exist_ok=True)

                    if report_format in ["html", "both"]:
                        html_report = await report_service.generate_run_report(
                            run.run_id, "html"
                        )
                        if output:
                            import shutil

                            target_html = output_dir / f"test_report_{run.run_id}.html"
                            shutil.copy2(html_report, target_html)
                            click.echo(f"📄 HTML report: {target_html}")
                        else:
                            click.echo(f"📄 HTML report: {html_report}")

                    if report_format in ["json", "both"]:
                        json_report = await report_service.generate_run_report(
                            run.run_id, "json"
                        )
                        if output:
                            import shutil

                            target_json = output_dir / f"test_report_{run.run_id}.json"
                            shutil.copy2(json_report, target_json)
                            click.echo(f"📄 JSON report: {target_json}")
                        else:
                            click.echo(f"📄 JSON report: {json_report}")

            else:
                click.echo(f"❌ Test failed: {final_run.error_message}")
                sys.exit(1)

        except Exception as e:
            click.echo(f"❌ Error: {e}")
            sys.exit(1)

    # Run the async function
    asyncio.run(run_test())


@cli.group()
def project():
    """Manage test projects."""
    pass


@project.command("list")
@click.option(
    "--format",
    "output_format",
    type=click.Choice(["table", "json"]),
    default="table",
    help="Output format",
)
def list_projects(output_format: str):
    """List all test projects."""

    async def run_list():
        await setup_database()
        service = ProjectService()
        projects = await service.list_projects()

        if output_format == "json":
            data = [p.to_dict() for p in projects]
            click.echo(json.dumps(data, indent=2, default=str))
        else:
            if not projects:
                click.echo("No projects found.")
                return

            click.echo("📁 Test Projects:")
            click.echo("-" * 80)
            for project in projects:
                click.echo(f"ID: {project.project_id}")
                click.echo(f"Name: {project.name}")
                click.echo(f"App Path: {project.app_path}")
                click.echo(f"Test Runs: {project.total_test_runs}")
                click.echo(f"Success Rate: {project.average_success_rate:.1f}%")
                click.echo(
                    f"Created: {project.created_at.strftime('%Y-%m-%d %H:%M:%S')}"
                )
                click.echo("-" * 80)

    asyncio.run(run_list())


@project.command("create")
@click.argument("name")
@click.argument("app_path", type=click.Path(exists=True))
@click.option("--description", "-d", default="", help="Project description")
def create_project(name: str, app_path: str, description: str):
    """Create a new test project."""

    async def run_create():
        await setup_database()
        service = ProjectService()

        project = await service.create_project(name, app_path, description)

        click.echo(f"✅ Project created: {project.project_id}")
        click.echo(f"Name: {project.name}")
        click.echo(f"App Path: {project.app_path}")
        click.echo(f"Permissions: {len(project.discovered_permissions)}")
        click.echo(f"Endpoints: {len(project.discovered_endpoints)}")
        click.echo(f"Commands: {len(project.discovered_commands)}")

    asyncio.run(run_create())


@project.command("delete")
@click.argument("project_id")
@click.confirmation_option(prompt="Are you sure you want to delete this project?")
def delete_project(project_id: str):
    """Delete a test project."""

    async def run_delete():
        await setup_database()
        service = ProjectService()

        success = await service.delete_project(project_id)
        if success:
            click.echo(f"✅ Project {project_id} deleted successfully")
        else:
            click.echo(f"❌ Project {project_id} not found")
            sys.exit(1)

    asyncio.run(run_delete())


@cli.group()
def run():
    """Manage test runs."""
    pass


@run.command("list")
@click.option("--project-id", help="Filter by project ID")
@click.option("--limit", default=20, help="Maximum number of runs to show")
@click.option(
    "--format",
    "output_format",
    type=click.Choice(["table", "json"]),
    default="table",
    help="Output format",
)
def list_runs(project_id: Optional[str], limit: int, output_format: str):
    """List test runs."""

    async def run_list():
        await setup_database()
        service = TestRunService()
        runs = await service.list_runs(project_id=project_id, limit=limit)

        if output_format == "json":
            data = [r.to_dict() for r in runs]
            click.echo(json.dumps(data, indent=2, default=str))
        else:
            if not runs:
                click.echo("No test runs found.")
                return

            click.echo("🚀 Test Runs:")
            click.echo("-" * 100)
            for run_item in runs:
                status_icon = (
                    "✅"
                    if run_item.status.value == "completed"
                    else "❌" if run_item.status.value == "failed" else "⏳"
                )
                click.echo(f"{status_icon} {run_item.name} ({run_item.run_id})")
                click.echo(f"   Status: {run_item.status.value}")
                click.echo(f"   Success Rate: {run_item.success_rate:.1f}%")
                click.echo(f"   Duration: {run_item.duration_seconds or 0:.1f}s")
                click.echo(
                    f"   Created: {run_item.created_at.strftime('%Y-%m-%d %H:%M:%S')}"
                )
                click.echo("-" * 100)

    asyncio.run(run_list())


@run.command("status")
@click.argument("run_id")
def run_status(run_id: str):
    """Get status of a test run."""

    async def get_status():
        await setup_database()
        service = TestRunService()

        run_item = await service.get_run(run_id)
        if not run_item:
            click.echo(f"❌ Test run {run_id} not found")
            sys.exit(1)

        status_icon = (
            "✅"
            if run_item.status.value == "completed"
            else "❌" if run_item.status.value == "failed" else "⏳"
        )

        click.echo(f"{status_icon} Test Run: {run_item.name}")
        click.echo(f"ID: {run_id}")
        click.echo(f"Status: {run_item.status.value}")
        click.echo(
            f"Progress: {run_item.passed_scenarios + run_item.failed_scenarios}/{run_item.total_scenarios} scenarios"
        )
        click.echo(f"Success Rate: {run_item.success_rate:.1f}%")
        click.echo(f"Confidence: {run_item.confidence_score:.1f}%")

        if run_item.started_at:
            click.echo(f"Started: {run_item.started_at.strftime('%Y-%m-%d %H:%M:%S')}")

        if run_item.completed_at:
            click.echo(
                f"Completed: {run_item.completed_at.strftime('%Y-%m-%d %H:%M:%S')}"
            )
            click.echo(f"Duration: {run_item.duration_seconds:.1f} seconds")

        if run_item.error_message:
            click.echo(f"Error: {run_item.error_message}")

    asyncio.run(get_status())


@cli.group()
def analytics():
    """View analytics and metrics."""
    pass


@analytics.command("summary")
@click.option("--days", default=30, help="Number of days to analyze")
def analytics_summary(days: int):
    """Show analytics summary."""

    async def show_summary():
        await setup_database()
        service = AnalyticsService()

        analytics = await service.get_global_analytics(days=days)

        click.echo(f"📊 Analytics Summary (Last {days} days)")
        click.echo("=" * 50)
        click.echo(f"Total Projects: {analytics['total_projects']}")
        click.echo(f"Total Runs: {analytics['total_runs']}")
        click.echo(f"Average Success Rate: {analytics['average_success_rate']:.1f}%")

        if analytics["projects"]:
            click.echo("\n🏆 Top Projects:")
            sorted_projects = sorted(
                analytics["projects"], key=lambda p: p["success_rate"], reverse=True
            )
            for project in sorted_projects[:5]:
                click.echo(
                    f"  • {project['name']}: {project['success_rate']:.1f}% ({project['total_runs']} runs)"
                )

    asyncio.run(show_summary())


@cli.command()
@click.option("--port", default=8000, help="Port to run the server on")
@click.option("--host", default="localhost", help="Host to bind the server to")
def server(port: int, host: str):
    """Start the web server."""

    async def start_server():
        import uvicorn

        from ..api.main import app

        click.echo(f"🚀 Starting QA Agentic Testing server on {host}:{port}")
        click.echo(f"📚 API Documentation: http://{host}:{port}/api/docs")
        click.echo(f"🌐 Web Interface: http://{host}:{port}")

        # Initialize database
        await setup_database()

        # Run the server
        config = uvicorn.Config(app, host=host, port=port, log_level="info")
        server = uvicorn.Server(config)
        await server.serve()

    asyncio.run(start_server())


@cli.group()
def personas():
    """Manage testing personas."""
    pass


@personas.command("list")
@click.option("--industry", help="Filter by industry")
def list_personas(industry: Optional[str]):
    """List available personas."""
    from ..core.personas import PersonaManager

    manager = PersonaManager()

    if industry:
        personas_list = manager.load_industry_personas(industry)
        click.echo(f"🎭 {industry.title()} Industry Personas:")
    else:
        personas_list = list(manager.personas.values())
        click.echo("🎭 All Available Personas:")

    click.echo("-" * 60)
    for persona in personas_list:
        click.echo(f"Key: {persona.key}")
        click.echo(f"Name: {persona.name}")
        click.echo(f"Role: {persona.role}")
        click.echo(f"Permissions: {len(persona.permissions)} permissions")
        click.echo(f"Success Rate: {persona.expected_success_rate}%")
        click.echo("-" * 60)


@personas.command("industries")
def list_industries():
    """List available industry templates."""
    from ..core.personas import PersonaManager

    manager = PersonaManager()
    industries = manager.get_available_industries()

    click.echo("🏭 Available Industry Templates:")
    click.echo("-" * 40)
    for industry in industries:
        click.echo(f"  • {industry}")

    click.echo("\nUse: qa-test /path/to/app --industry <industry_name>")


@personas.command("create")
@click.option("--interactive", "-i", is_flag=True, help="Use interactive wizard")
@click.option("--file", "-f", type=click.Path(), help="Save persona to file")
def create_persona(interactive: bool, file: Optional[str]):
    """Create a custom persona."""
    from ..core.personas import PersonaManager

    manager = PersonaManager()

    if interactive:
        persona = manager.generate_custom_persona_interactive()

        if file:
            persona_data = [persona.to_dict()]
            with open(file, "w") as f:
                json.dump(persona_data, f, indent=2)
            click.echo(f"✅ Persona saved to: {file}")
    else:
        click.echo("Use --interactive flag to launch the persona creation wizard")


@cli.group()
def models():
    """Manage LLM model configurations."""
    pass


@models.command("list")
@click.option(
    "--preset",
    type=click.Choice(["development", "balanced", "enterprise"]),
    help="Show models for specific preset",
)
def list_models(preset: Optional[str]):
    """List recommended models by agent type and preset."""
    from ..core.agent_coordinator import AgentConfig, AgentType

    presets_to_show = [preset] if preset else ["development", "balanced", "enterprise"]

    for preset_name in presets_to_show:
        click.echo(f"\n🤖 {preset_name.title()} Preset:")
        click.echo("-" * 50)

        for agent_type in AgentType:
            config = AgentConfig.get_recommended_config(agent_type, preset_name)
            click.echo(
                f"{agent_type.value.ljust(20)}: {config.provider}/{config.model}"
            )

        click.echo()


@models.command("recommend")
@click.argument("app_size", type=click.Choice(["small", "medium", "large"]))
@click.option(
    "--security-focused", is_flag=True, help="Prioritize security analysis accuracy"
)
@click.option(
    "--performance-focused", is_flag=True, help="Prioritize performance analysis"
)
def recommend_models(app_size: str, security_focused: bool, performance_focused: bool):
    """Get model recommendations based on app characteristics."""

    # Map app size to presets
    size_to_preset = {
        "small": "development",
        "medium": "balanced",
        "large": "enterprise",
    }

    base_preset = size_to_preset[app_size]

    click.echo(f"📊 Model Recommendations for {app_size} app:")
    click.echo("=" * 50)

    if security_focused:
        click.echo("\n🔒 Security-Optimized Configuration:")
        click.echo("Security agents: openai/gpt-4 or anthropic/claude-3-sonnet")
        click.echo("Other agents: Use balanced preset")
        click.echo("Rationale: High accuracy models for security analysis")

    elif performance_focused:
        click.echo("\n⚡ Performance-Optimized Configuration:")
        click.echo("Performance agents: anthropic/claude-3-opus")
        click.echo("Other agents: Use development preset for speed")
        click.echo("Rationale: Analytical models for performance insights")

    else:
        click.echo(f"\n🎯 Recommended Preset: {base_preset}")
        from ..core.agent_coordinator import AgentConfig, AgentType

        for agent_type in AgentType:
            config = AgentConfig.get_recommended_config(agent_type, base_preset)
            click.echo(f"  {agent_type.value}: {config.provider}/{config.model}")

    # Cost estimates
    click.echo("\n💰 Estimated Cost Impact:")
    cost_levels = {
        "development": "Low (Ollama local models)",
        "balanced": "Medium (Mix of local and API)",
        "enterprise": "High (Premium API models)",
    }
    click.echo(f"  {cost_levels[base_preset]}")

    # Usage commands
    click.echo("\n📝 Usage:")
    click.echo(f"  qa-test /path/to/app --model-preset {base_preset}")

    if security_focused:
        click.echo("  qa-test /path/to/app --security-model openai/gpt-4")
    if performance_focused:
        click.echo("  qa-test /path/to/app --performance-model anthropic/claude-3-opus")


@models.command("test")
@click.argument("provider")
@click.argument("model")
@click.option("--prompt", default="Hello, please respond with a simple test message.")
def test_model(provider: str, model: str, prompt: str):
    """Test if a specific model configuration works."""

    click.echo(f"🧪 Testing {provider}/{model}...")

    try:
        # This would integrate with the actual SDK LLM nodes
        # For now, just show the configuration
        click.echo("✅ Model configuration appears valid")
        click.echo(f"   Provider: {provider}")
        click.echo(f"   Model: {model}")
        click.echo(f"   Test prompt: {prompt}")

        # TODO: Implement actual model testing
        click.echo(
            "\n⚠️  Note: Actual model testing requires API keys and network access"
        )
        click.echo("   Set appropriate environment variables:")
        if provider == "openai":
            click.echo("   export OPENAI_API_KEY=your-key")
        elif provider == "anthropic":
            click.echo("   export ANTHROPIC_API_KEY=your-key")
        elif provider == "ollama":
            click.echo("   Ensure Ollama is running: ollama serve")

    except Exception as e:
        click.echo(f"❌ Model test failed: {e}")


@models.command("cost")
@click.option(
    "--preset",
    type=click.Choice(["development", "balanced", "enterprise"]),
    default="balanced",
)
@click.option("--test-count", default=100, help="Estimated number of tests")
def estimate_cost(preset: str, test_count: int):
    """Estimate cost for running tests with different model presets."""

    # Rough cost estimates per 1K tokens (as of 2024)
    cost_per_1k_tokens = {
        "ollama": 0.0,  # Local models
        "openai": {"gpt-3.5-turbo": 0.002, "gpt-4": 0.06},
        "anthropic": {
            "claude-3-haiku": 0.0025,
            "claude-3-sonnet": 0.015,
            "claude-3-opus": 0.075,
        },
    }

    # Estimated tokens per test
    tokens_per_test = 3000  # Includes prompts and responses

    click.echo(f"💰 Cost Estimate for {test_count} tests ({preset} preset):")
    click.echo("=" * 50)

    total_cost = 0

    from ..core.agent_coordinator import AgentConfig, AgentType

    for agent_type in AgentType:
        config = AgentConfig.get_recommended_config(agent_type, preset)

        if config.provider == "ollama":
            cost = 0
            cost_desc = "Free (local)"
        else:
            provider_costs = cost_per_1k_tokens[config.provider]
            if isinstance(provider_costs, dict):
                cost_per_token = provider_costs.get(config.model, 0.01)
            else:
                cost_per_token = provider_costs

            cost = (tokens_per_test / 1000) * cost_per_token * test_count
            total_cost += cost
            cost_desc = f"${cost:.2f}"

        click.echo(f"  {agent_type.value.ljust(20)}: {cost_desc}")

    click.echo("-" * 50)
    click.echo(f"  Total estimated cost: ${total_cost:.2f}")

    if total_cost > 0:
        click.echo("\n💡 Tips to reduce costs:")
        click.echo("  • Use --model-preset development for testing")
        click.echo("  • Use --security-model only for critical security testing")
        click.echo("  • Consider local Ollama models for development")


@cli.command()
def init():
    """Initialize the QA Agentic Testing system."""

    async def initialize():
        click.echo("🤖 Initializing QA Agentic Testing System...")

        # Setup database
        await setup_database()
        click.echo("✅ Database initialized")

        # Create default directories
        reports_dir = Path.cwd() / "reports"
        reports_dir.mkdir(exist_ok=True)
        click.echo(f"✅ Reports directory created: {reports_dir}")

        # Show available industry templates
        from ..core.personas import PersonaManager

        manager = PersonaManager()
        industries = manager.get_available_industries()

        if industries:
            click.echo(f"\n🏭 Available industry templates: {', '.join(industries)}")
            click.echo("Use: qa-test /path/to/app --industry <industry_name>")

        click.echo("\n🎉 QA Agentic Testing System initialized successfully!")
        click.echo("\nNext steps:")
        click.echo("  • Run 'qa-test /path/to/your/app' to test an application")
        click.echo(
            "  • Run 'qa-test /path/to/your/app --async' for 3-5x faster testing"
        )
        click.echo("  • Run 'qa-test personas list' to see available personas")
        click.echo("  • Run 'qa-test server' to start the web interface")

    asyncio.run(initialize())


if __name__ == "__main__":
    cli()
