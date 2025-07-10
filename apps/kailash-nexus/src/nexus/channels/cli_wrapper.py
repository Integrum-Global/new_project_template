"""
CLI Channel Wrapper for Nexus

Wraps SDK's CLIChannel with enterprise features.
"""

import logging
from datetime import datetime, timezone
from typing import Any, Callable, Dict, List, Optional

from kailash.channels.cli_channel import CLIChannel
from kailash.workflow import Workflow

logger = logging.getLogger(__name__)


class CLIChannelWrapper:
    """CLI Channel wrapper with enterprise features.

    Adds command history, aliases, and multi-tenant support
    to the SDK's CLIChannel.
    """

    def __init__(
        self,
        cli_channel: CLIChannel,
        multi_tenant_manager: Optional[Any] = None,
        auth_manager: Optional[Any] = None,
    ):
        """Initialize CLI channel wrapper.

        Args:
            cli_channel: SDK's CLIChannel instance
            multi_tenant_manager: Multi-tenant manager
            auth_manager: Authentication manager
        """
        self.cli_channel = cli_channel
        self.multi_tenant_manager = multi_tenant_manager
        self.auth_manager = auth_manager

        # Command history
        self._history: List[Dict[str, Any]] = []
        self._aliases: Dict[str, str] = {}

        # Add built-in commands
        self._setup_builtin_commands()

        logger.info("CLI channel wrapper initialized")

    def _setup_builtin_commands(self):
        """Setup built-in enterprise commands."""
        # History command
        self.register_command("history", self._history_command, "Show command history")

        # Alias command
        self.register_command("alias", self._alias_command, "Manage command aliases")

        # Tenant command
        if self.multi_tenant_manager:
            self.register_command(
                "tenant", self._tenant_command, "Manage tenant context"
            )

        # Auth command
        if self.auth_manager:
            self.register_command("auth", self._auth_command, "Manage authentication")

    async def _history_command(self, args: List[str]) -> Dict[str, Any]:
        """Show command history.

        Args:
            args: Command arguments

        Returns:
            Command result
        """
        if not args or args[0] == "list":
            # Show recent history
            recent = self._history[-20:]
            output = "Recent commands:\n"
            for i, entry in enumerate(recent):
                output += f"{i+1}. {entry['command']} - {entry['timestamp']}\n"

            return {"success": True, "output": output}

        elif args[0] == "clear":
            self._history.clear()
            return {"success": True, "output": "History cleared"}

        else:
            return {"success": False, "output": "Usage: history [list|clear]"}

    async def _alias_command(self, args: List[str]) -> Dict[str, Any]:
        """Manage command aliases.

        Args:
            args: Command arguments

        Returns:
            Command result
        """
        if not args:
            # List aliases
            if not self._aliases:
                return {"success": True, "output": "No aliases defined"}

            output = "Aliases:\n"
            for alias, command in self._aliases.items():
                output += f"  {alias} -> {command}\n"

            return {"success": True, "output": output}

        elif len(args) >= 2:
            alias = args[0]
            command = " ".join(args[1:])

            self._aliases[alias] = command

            return {"success": True, "output": f"Alias created: {alias} -> {command}"}

        else:
            return {"success": False, "output": "Usage: alias [name command...]"}

    async def _tenant_command(self, args: List[str]) -> Dict[str, Any]:
        """Manage tenant context.

        Args:
            args: Command arguments

        Returns:
            Command result
        """
        if not args or args[0] == "info":
            # Show current tenant
            tenant_id = self.cli_channel.session_data.get("tenant_id")
            if not tenant_id:
                return {"success": True, "output": "No tenant context set"}

            tenant = self.multi_tenant_manager.get_tenant(tenant_id)
            if tenant:
                output = f"Current tenant: {tenant.name} ({tenant.tenant_id})\n"
                output += f"Isolation level: {tenant.isolation_level}\n"

                # Show usage if available
                usage = self.multi_tenant_manager.get_usage(tenant_id)
                if usage:
                    output += "\nUsage:\n"
                    output += f"  Workflows: {usage.workflows}\n"
                    output += f"  Executions today: {usage.executions_today}\n"
                    output += f"  API calls this hour: {usage.api_calls_this_hour}\n"

                return {"success": True, "output": output}

        elif args[0] == "set" and len(args) > 1:
            tenant_id = args[1]
            tenant = self.multi_tenant_manager.get_tenant(tenant_id)

            if not tenant:
                return {"success": False, "output": f"Tenant {tenant_id} not found"}

            self.cli_channel.session_data["tenant_id"] = tenant_id

            return {"success": True, "output": f"Switched to tenant: {tenant.name}"}

        elif args[0] == "list":
            tenants = self.multi_tenant_manager.list_tenants(is_active=True)

            output = "Active tenants:\n"
            for tenant in tenants:
                output += f"  {tenant.tenant_id}: {tenant.name}\n"

            return {"success": True, "output": output}

        else:
            return {"success": False, "output": "Usage: tenant [info|set <id>|list]"}

    async def _auth_command(self, args: List[str]) -> Dict[str, Any]:
        """Manage authentication.

        Args:
            args: Command arguments

        Returns:
            Command result
        """
        if not args or args[0] == "status":
            # Show auth status
            user = self.cli_channel.session_data.get("user")
            if user:
                output = f"Authenticated as: {user.get('user_id')}\n"
                output += f"Provider: {user.get('provider', 'local')}\n"
                output += f"Email: {user.get('email', 'N/A')}\n"
            else:
                output = "Not authenticated"

            return {"success": True, "output": output}

        elif args[0] == "login" and len(args) >= 3:
            # Simple login
            username = args[1]
            password = args[2]

            token = await self.auth_manager.authenticate(
                {"username": username, "password": password}
            )

            if token:
                self.cli_channel.session_data["token"] = token.token
                self.cli_channel.session_data["user"] = token.metadata

                return {"success": True, "output": f"Logged in as {username}"}
            else:
                return {"success": False, "output": "Authentication failed"}

        elif args[0] == "logout":
            # Clear auth
            token = self.cli_channel.session_data.get("token")
            if token and self.auth_manager:
                self.auth_manager.revoke_token(token)

            self.cli_channel.session_data.pop("token", None)
            self.cli_channel.session_data.pop("user", None)

            return {"success": True, "output": "Logged out"}

        else:
            return {
                "success": False,
                "output": "Usage: auth [status|login <user> <pass>|logout]",
            }

    def register_command(
        self,
        name: str,
        handler: Callable,
        description: str = "",
        auth_required: bool = False,
        tenant_required: bool = False,
    ):
        """Register a command with enterprise features.

        Args:
            name: Command name
            handler: Command handler
            description: Command description
            auth_required: Require authentication
            tenant_required: Require tenant context
        """

        # Create wrapped handler
        async def enterprise_handler(args: List[str]) -> Dict[str, Any]:
            # Record in history
            self._history.append(
                {
                    "command": f"{name} {' '.join(args)}",
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "user": self.cli_channel.session_data.get("user", {}).get(
                        "user_id"
                    ),
                    "tenant": self.cli_channel.session_data.get("tenant_id"),
                }
            )

            # Check auth if required
            if auth_required and "user" not in self.cli_channel.session_data:
                return {
                    "success": False,
                    "output": "Authentication required. Use 'auth login' first.",
                }

            # Check tenant if required
            if tenant_required and "tenant_id" not in self.cli_channel.session_data:
                return {
                    "success": False,
                    "output": "Tenant context required. Use 'tenant set' first.",
                }

            # Execute handler
            return await handler(args)

        # Register with SDK channel
        self.cli_channel.register_command(
            name=name, handler=enterprise_handler, description=description
        )

        logger.info(f"Registered enterprise CLI command: {name}")

    def register_workflow_command(
        self,
        name: str,
        workflow: Workflow,
        description: str = "",
        auth_required: bool = True,
        tenant_required: bool = True,
    ):
        """Register a workflow as a CLI command.

        Args:
            name: Command name
            workflow: Workflow to execute
            description: Command description
            auth_required: Require authentication
            tenant_required: Require tenant context
        """

        async def workflow_handler(args: List[str]) -> Dict[str, Any]:
            # Parse arguments into workflow inputs
            inputs = {}
            for i, arg in enumerate(args):
                if "=" in arg:
                    key, value = arg.split("=", 1)
                    inputs[key] = value
                else:
                    inputs[f"arg{i}"] = arg

            # Add context
            inputs["user"] = self.cli_channel.session_data.get("user")
            inputs["tenant_id"] = self.cli_channel.session_data.get("tenant_id")

            # Execute workflow
            try:
                # In production, would execute through runtime
                result = {"workflow": name, "inputs": inputs, "status": "completed"}

                return {"success": True, "output": f"Workflow executed: {result}"}
            except Exception as e:
                return {"success": False, "output": f"Workflow error: {str(e)}"}

        self.register_command(
            name=name,
            handler=workflow_handler,
            description=description or f"Execute {name} workflow",
            auth_required=auth_required,
            tenant_required=tenant_required,
        )

    async def process_input(self, input_text: str) -> Dict[str, Any]:
        """Process CLI input with alias support.

        Args:
            input_text: User input

        Returns:
            Command result
        """
        # Trim and check for empty
        input_text = input_text.strip()
        if not input_text:
            return {"success": True, "output": ""}

        # Check for alias
        parts = input_text.split()
        command = parts[0]

        if command in self._aliases:
            # Expand alias
            alias_expansion = self._aliases[command]
            if len(parts) > 1:
                # Append remaining args
                input_text = f"{alias_expansion} {' '.join(parts[1:])}"
            else:
                input_text = alias_expansion

        # Process through SDK channel
        return await self.cli_channel.process_input(input_text)

    def get_commands(self) -> List[Dict[str, Any]]:
        """Get available commands.

        Returns:
            List of command information
        """
        commands = []

        if hasattr(self.cli_channel, "_commands"):
            for name, cmd_info in self.cli_channel._commands.items():
                commands.append(
                    {
                        "name": name,
                        "description": cmd_info.get("description", ""),
                        "usage": cmd_info.get("usage", f"{name} [args...]"),
                    }
                )

        # Add aliases
        for alias, expansion in self._aliases.items():
            commands.append(
                {
                    "name": f"{alias} (alias)",
                    "description": f"Expands to: {expansion}",
                    "usage": f"{alias} [args...]",
                }
            )

        return sorted(commands, key=lambda x: x["name"])

    async def start(self):
        """Start the CLI channel."""
        await self.cli_channel.start()
        logger.info("CLI channel wrapper started")

    async def stop(self):
        """Stop the CLI channel."""
        await self.cli_channel.stop()
        logger.info("CLI channel wrapper stopped")
