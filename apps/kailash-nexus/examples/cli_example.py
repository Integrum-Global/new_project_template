#!/usr/bin/env python3
"""
Nexus CLI Example

Demonstrates using the enhanced CLI channel with enterprise features.
"""

import asyncio

from kailash_nexus import create_application

from kailash.workflow.builder import WorkflowBuilder


async def main():
    """Run CLI example."""

    # Create application
    app = create_application(
        name="Nexus CLI Demo",
        channels={
            "cli": {"enabled": True},
            "api": {"enabled": False},
            "mcp": {"enabled": False},
        },
        features={
            "authentication": {"enabled": True},
            "multi_tenant": {"enabled": True},
        },
    )

    await app.start()

    # Get CLI channel wrapper
    cli = app.cli_channel

    # Create some test workflows
    hello_workflow = WorkflowBuilder()
    hello_workflow.add_node(
        "PythonCodeNode",
        "greet",
        {
            "code": """
result = f"Hello, {name}! Welcome to Nexus."
"""
        },
    )

    cli.register_workflow_command("hello", hello_workflow.build(), "Greet a user")

    # Demo commands
    print("Nexus CLI Demo")
    print("=" * 50)

    # Show available commands
    commands = cli.get_commands()
    print("\nAvailable commands:")
    for cmd in commands:
        print(f"  {cmd['name']}: {cmd['description']}")

    # Process some commands
    demo_commands = [
        "help",
        "auth login demo_user demo_pass",
        "auth status",
        "tenant list",
        "tenant set tenant_123",
        "hello name=World",
        "alias h hello",
        "h name=Alias",
        "history list",
    ]

    print("\nExecuting demo commands:")
    print("-" * 50)

    for cmd in demo_commands:
        print(f"\n> {cmd}")
        result = await cli.process_input(cmd)
        if result.get("output"):
            print(result["output"])

    await app.stop()


if __name__ == "__main__":
    asyncio.run(main())
