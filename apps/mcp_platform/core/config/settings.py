"""
MCP Application Settings

Configuration settings for the MCP management application.
"""

import os
from pathlib import Path
from typing import Any, Dict, List, Optional


class MCPConfig:
    """MCP application configuration."""

    def __init__(self):
        """Initialize configuration from environment and defaults."""
        # Application settings
        self.APP_NAME = os.getenv("MCP_APP_NAME", "MCP Management System")
        self.VERSION = "1.0.0"
        self.DEBUG = os.getenv("MCP_DEBUG", "false").lower() == "true"

        # Server settings
        self.HOST = os.getenv("MCP_HOST", "0.0.0.0")
        self.PORT = int(os.getenv("MCP_PORT", "8000"))

        # Database settings
        self.DATABASE_URL = os.getenv(
            "MCP_DATABASE_URL", "postgresql://mcp_user:mcp_pass@localhost:5432/mcp_db"
        )

        # Redis settings
        self.REDIS_HOST = os.getenv("MCP_REDIS_HOST", "localhost")
        self.REDIS_PORT = int(os.getenv("MCP_REDIS_PORT", "6379"))
        self.REDIS_DB = int(os.getenv("MCP_REDIS_DB", "0"))
        self.ENABLE_CACHE = os.getenv("MCP_ENABLE_CACHE", "true").lower() == "true"

        # Security settings
        self.JWT_SECRET_KEY = os.getenv(
            "MCP_JWT_SECRET", "your-secret-key-change-in-production"
        )
        self.JWT_ALGORITHM = os.getenv("MCP_JWT_ALGORITHM", "HS256")
        self.JWT_EXPIRY_HOURS = int(os.getenv("MCP_JWT_EXPIRY_HOURS", "24"))
        self.ACCESS_STRATEGY = os.getenv("MCP_ACCESS_STRATEGY", "rbac")

        # CORS settings
        self.ALLOWED_ORIGINS = os.getenv(
            "MCP_ALLOWED_ORIGINS", "http://localhost:3000,http://localhost:8080"
        ).split(",")

        # MCP server defaults
        self.DEFAULT_TIMEOUT = int(os.getenv("MCP_DEFAULT_TIMEOUT", "30"))
        self.MAX_CONCURRENT_SERVERS = int(os.getenv("MCP_MAX_SERVERS", "50"))
        self.AUTO_START_SERVERS = os.getenv("MCP_AUTO_START", "true").lower() == "true"

        # Transport settings
        self.STDIO_BUFFER_SIZE = int(os.getenv("MCP_STDIO_BUFFER", "8192"))
        self.HTTP_CONNECTION_POOL_SIZE = int(os.getenv("MCP_HTTP_POOL_SIZE", "100"))
        self.HTTP_TIMEOUT = int(os.getenv("MCP_HTTP_TIMEOUT", "60"))

        # Security policies
        self.REQUIRE_AUTHENTICATION = (
            os.getenv("MCP_REQUIRE_AUTH", "true").lower() == "true"
        )
        self.ALLOWED_COMMANDS = os.getenv(
            "MCP_ALLOWED_COMMANDS", "mcp-server,python,node,npx"
        ).split(",")

        # Caching settings
        self.CACHE_TTL = int(os.getenv("MCP_CACHE_TTL", "3600"))
        self.CACHE_MAX_SIZE = int(os.getenv("MCP_CACHE_MAX_SIZE", "1000"))

        # Monitoring settings
        self.ENABLE_MONITORING = (
            os.getenv("MCP_ENABLE_MONITORING", "true").lower() == "true"
        )
        self.MONITOR_INTERVAL = int(os.getenv("MCP_MONITOR_INTERVAL", "60"))
        self.METRICS_ENABLED = (
            os.getenv("MCP_METRICS_ENABLED", "true").lower() == "true"
        )
        self.METRICS_INTERVAL = int(os.getenv("MCP_METRICS_INTERVAL", "60"))

        # Rate limiting
        self.RATE_LIMITS = {
            "default": int(os.getenv("MCP_RATE_LIMIT_DEFAULT", "100")),
            "tool_execution": int(os.getenv("MCP_RATE_LIMIT_TOOLS", "50")),
            "server_management": int(os.getenv("MCP_RATE_LIMIT_SERVERS", "20")),
        }

        # Initial servers to load
        self.INITIAL_SERVERS = self._load_initial_servers()

        # Node configurations for Kailash SDK
        self.NODE_CONFIGS = self._get_node_configs()

    def _load_initial_servers(self) -> List[Dict[str, Any]]:
        """Load initial server configurations."""
        # Check for servers config file
        config_file = Path("config/mcp_servers.yaml")
        if config_file.exists():
            import yaml

            with open(config_file) as f:
                config = yaml.safe_load(f)
                return config.get("servers", [])

        # Default servers
        return [
            {
                "name": "filesystem",
                "transport": "stdio",
                "command": "npx",
                "args": ["@modelcontextprotocol/server-filesystem", "/tmp"],
                "auto_start": True,
                "tags": ["default", "filesystem"],
            }
        ]

    def _get_node_configs(self) -> Dict[str, Dict[str, Any]]:
        """Get Kailash node configurations."""
        return {
            "EnterpriseAuditLogNode": {
                "connection_string": self.DATABASE_URL,
                "table_name": "mcp_audit_logs",
            },
            "EnterpriseSecurityEventNode": {
                "connection_string": self.DATABASE_URL,
                "table_name": "mcp_security_events",
            },
            "CacheNode": {
                "backend": "redis",
                "redis_host": self.REDIS_HOST,
                "redis_port": self.REDIS_PORT,
                "redis_db": self.REDIS_DB,
                "default_ttl": self.CACHE_TTL,
            },
        }

    def get_redis_config(self) -> Dict[str, Any]:
        """Get Redis configuration."""
        return {"host": self.REDIS_HOST, "port": self.REDIS_PORT, "db": self.REDIS_DB}

    def get_database_config(self) -> Dict[str, Any]:
        """Get database configuration."""
        # Parse database URL
        # Format: postgresql://user:pass@host:port/db
        if "postgresql://" in self.DATABASE_URL:
            parts = self.DATABASE_URL.replace("postgresql://", "").split("@")
            if len(parts) == 2:
                user_pass = parts[0].split(":")
                host_port_db = parts[1].split("/")
                host_port = host_port_db[0].split(":")

                return {
                    "driver": "postgresql",
                    "user": user_pass[0] if user_pass else "postgres",
                    "password": user_pass[1] if len(user_pass) > 1 else "",
                    "host": host_port[0] if host_port else "localhost",
                    "port": int(host_port[1]) if len(host_port) > 1 else 5432,
                    "database": host_port_db[1] if len(host_port_db) > 1 else "mcp_db",
                }

        return {"url": self.DATABASE_URL}

    def get_security_config(self) -> Dict[str, Any]:
        """Get security configuration."""
        return {
            "jwt_secret": self.JWT_SECRET_KEY,
            "jwt_algorithm": self.JWT_ALGORITHM,
            "token_expiry_hours": self.JWT_EXPIRY_HOURS,
            "access_strategy": self.ACCESS_STRATEGY,
            "require_authentication": self.REQUIRE_AUTHENTICATION,
            "rate_limits": self.RATE_LIMITS,
        }

    def validate(self):
        """Validate configuration."""
        errors = []

        # Check required settings
        if self.JWT_SECRET_KEY == "your-secret-key-change-in-production":
            errors.append("JWT_SECRET_KEY must be set for production")

        if not self.DATABASE_URL:
            errors.append("DATABASE_URL is required")

        if self.PORT < 1 or self.PORT > 65535:
            errors.append("PORT must be between 1 and 65535")

        if errors:
            raise ValueError(f"Configuration errors: {', '.join(errors)}")

        return True
