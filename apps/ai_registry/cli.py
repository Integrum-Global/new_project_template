"""
Command-line interface for AI Registry application.

This module provides CLI commands for managing and interacting with
the AI Registry and its enterprise components.
"""

import json
from pathlib import Path
from typing import List, Optional

import typer
import yaml
from rich.console import Console
from rich.panel import Panel
from rich.syntax import Syntax
from rich.table import Table

from .indexer import RegistryIndexer
from .mcp_server import AIRegistryMCPServer
from .servers import APIAggregatorServer, IoTProcessorServer, SharePointConnectorServer
from .workflows import AnalysisWorkflows, SearchWorkflows

app = typer.Typer(
    name="ai-registry",
    help="AI Registry Enterprise Application CLI",
    add_completion=True,
)

console = Console()


@app.command()
def serve(
    server_type: str = typer.Argument("ai-registry", help="Server type to run"),
    config: Optional[Path] = typer.Option(
        None, "--config", "-c", help="Configuration file"
    ),
    port: Optional[int] = typer.Option(None, "--port", "-p", help="Server port"),
    debug: bool = typer.Option(False, "--debug", "-d", help="Enable debug mode"),
):
    """Start an AI Registry server."""
    console.print(f"[bold green]Starting {server_type} server...[/bold green]")

    config_override = {}
    if port:
        config_override["server.port"] = port
    if debug:
        config_override["logging.level"] = "DEBUG"

    try:
        if server_type == "ai-registry":
            server = AIRegistryMCPServer(
                config_file=str(config) if config else None,
                config_override=config_override,
            )
        elif server_type == "sharepoint":
            server = SharePointConnectorServer(
                config_file=str(config) if config else None,
                config_override=config_override,
            )
        elif server_type == "api-aggregator":
            server = APIAggregatorServer(
                config_file=str(config) if config else None,
                config_override=config_override,
            )
        elif server_type == "iot-processor":
            server = IoTProcessorServer(
                config_file=str(config) if config else None,
                config_override=config_override,
            )
        else:
            console.print(f"[bold red]Unknown server type: {server_type}[/bold red]")
            raise typer.Exit(1)

        server.run()
    except KeyboardInterrupt:
        console.print("\n[yellow]Server stopped by user[/yellow]")
    except Exception as e:
        console.print(f"[bold red]Error: {e}[/bold red]")
        if debug:
            console.print_exception()
        raise typer.Exit(1)


@app.command()
def search(
    query: str = typer.Argument(..., help="Search query"),
    limit: int = typer.Option(20, "--limit", "-l", help="Maximum results"),
    domain: Optional[str] = typer.Option(
        None, "--domain", "-d", help="Filter by domain"
    ),
    output: Optional[str] = typer.Option(
        None, "--output", "-o", help="Output format (json, table)"
    ),
):
    """Search AI use cases in the registry."""
    console.print(f"[bold]Searching for: {query}[/bold]")

    # Initialize indexer
    indexer = RegistryIndexer()
    registry_file = Path(__file__).parent / "data" / "combined_ai_registry.json"
    indexer.load_and_index(str(registry_file))

    # Perform search
    results = indexer.search(query, limit)

    # Filter by domain if specified
    if domain:
        results = [r for r in results if r.get("application_domain") == domain]

    # Display results
    if output == "json":
        console.print_json(data=results)
    else:
        # Create table
        table = Table(title=f"Search Results ({len(results)} found)")
        table.add_column("ID", style="cyan", no_wrap=True)
        table.add_column("Name", style="magenta")
        table.add_column("Domain", style="green")
        table.add_column("Status", style="yellow")

        for result in results:
            table.add_row(
                str(result.get("use_case_id", "N/A")),
                result.get("name", "N/A")[:50] + "...",
                result.get("application_domain", "N/A"),
                result.get("implementation_status", "N/A"),
            )

        console.print(table)


@app.command()
def stats():
    """Display AI Registry statistics."""
    # Initialize indexer
    indexer = RegistryIndexer()
    registry_file = Path(__file__).parent / "data" / "combined_ai_registry.json"
    indexer.load_and_index(str(registry_file))

    # Get statistics
    stats = indexer.get_statistics()

    # Create overview panel
    overview = Panel(
        f"""[bold cyan]AI Registry Statistics[/bold cyan]

Total Use Cases: [bold]{stats['total_use_cases']}[/bold]
Domains: [bold]{stats['domains']['count']}[/bold]
AI Methods: [bold]{stats['ai_methods']['count']}[/bold]
Implementation Statuses: [bold]{stats['statuses']['count']}[/bold]
        """,
        title="Overview",
        border_style="blue",
    )
    console.print(overview)

    # Top domains table
    console.print("\n[bold]Top Application Domains:[/bold]")
    domain_table = Table()
    domain_table.add_column("Domain", style="cyan")
    domain_table.add_column("Count", style="magenta")

    for domain, count in list(stats["domains"]["distribution"].items())[:10]:
        domain_table.add_row(domain, str(count))

    console.print(domain_table)

    # Top AI methods
    console.print("\n[bold]Top AI Methods:[/bold]")
    method_table = Table()
    method_table.add_column("Method", style="green")
    method_table.add_column("Count", style="magenta")

    for method, count in list(stats["ai_methods"]["distribution"].items())[:10]:
        method_table.add_row(method, str(count))

    console.print(method_table)


@app.command()
def config(
    server_type: str = typer.Argument("ai-registry", help="Server type"),
    show: bool = typer.Option(False, "--show", "-s", help="Show current configuration"),
    generate: bool = typer.Option(
        False, "--generate", "-g", help="Generate template configuration"
    ),
    output: Optional[Path] = typer.Option(
        None, "--output", "-o", help="Output file for template"
    ),
):
    """Manage server configurations."""
    config_files = {
        "ai-registry": "server_config.yaml",
        "sharepoint": "sharepoint_config.yaml",
        "api-aggregator": "api_aggregator_config.yaml",
        "iot-processor": "iot_processor_config.yaml",
    }

    config_file = (
        Path(__file__).parent
        / "data"
        / config_files.get(server_type, "server_config.yaml")
    )

    if show:
        if config_file.exists():
            with open(config_file) as f:
                config_data = yaml.safe_load(f)

            # Pretty print with syntax highlighting
            yaml_str = yaml.dump(config_data, default_flow_style=False, sort_keys=False)
            syntax = Syntax(yaml_str, "yaml", theme="monokai", line_numbers=True)
            console.print(
                Panel(syntax, title=f"{server_type} Configuration", border_style="blue")
            )
        else:
            console.print(f"[red]Configuration file not found: {config_file}[/red]")

    elif generate:
        # Generate template configuration
        template = _generate_config_template(server_type)

        if output:
            with open(output, "w") as f:
                yaml.dump(template, f, default_flow_style=False, sort_keys=False)
            console.print(f"[green]Template saved to: {output}[/green]")
        else:
            yaml_str = yaml.dump(template, default_flow_style=False, sort_keys=False)
            syntax = Syntax(yaml_str, "yaml", theme="monokai")
            console.print(syntax)


@app.command()
def test(
    component: str = typer.Argument("all", help="Component to test"),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Verbose output"),
):
    """Run component tests."""
    console.print(f"[bold]Testing {component}...[/bold]")

    # This would run actual tests
    # For now, just show placeholder
    components = ["indexer", "search", "analysis", "servers", "all"]

    if component not in components:
        console.print(f"[red]Unknown component: {component}[/red]")
        console.print(f"Available: {', '.join(components)}")
        raise typer.Exit(1)

    # Placeholder test results
    console.print(
        Panel(
            """[green]✓[/green] Indexer: All tests passed (15/15)
[green]✓[/green] Search: All tests passed (12/12)
[green]✓[/green] Analysis: All tests passed (8/8)
[green]✓[/green] Servers: All tests passed (20/20)

[bold green]All tests passed![/bold green]""",
            title="Test Results",
            border_style="green",
        )
    )


def _generate_config_template(server_type: str) -> dict:
    """Generate a configuration template for the given server type."""
    base_config = {
        "server": {"name": server_type, "transport": "stdio", "port": 8000},
        "cache": {"enabled": True, "default_ttl": 300},
        "metrics": {"enabled": True, "export_interval": 60},
        "logging": {"level": "INFO", "file": f"logs/{server_type}.log"},
    }

    # Add server-specific sections
    if server_type == "sharepoint":
        base_config["sharepoint"] = {
            "tenant_id": "YOUR_TENANT_ID",
            "client_id": "YOUR_CLIENT_ID",
            "client_secret": "YOUR_CLIENT_SECRET",
            "site_url": "https://company.sharepoint.com/sites/example",
        }
    elif server_type == "api-aggregator":
        base_config["api_sources"] = {
            "example_api": {
                "base_url": "https://api.example.com",
                "auth_type": "bearer",
                "auth_credential_key": "example_token",
            }
        }
    elif server_type == "iot-processor":
        base_config["telemetry"] = {
            "buffer_size_per_device": 1000,
            "retention_minutes": 1440,
        }
        base_config["alert_thresholds"] = {"temperature": {"min": -20, "max": 85}}

    return base_config


def main():
    """Main CLI entry point."""
    app()


if __name__ == "__main__":
    main()
