"""
Configuration settings for AI Registry MCP Server.

This module provides configuration management for the AI Registry server,
including paths, caching settings, and server parameters.
"""

import os
from pathlib import Path
from typing import Any, Dict, Optional

import yaml


class Config:
    """Configuration management for AI Registry MCP Server."""

    def __init__(self, config_file: Optional[str] = None):
        """
        Initialize configuration.

        Args:
            config_file: Path to YAML configuration file (optional)
        """
        # Default configuration
        self.defaults = {
            "registry_file": "apps/ai_registry/data/combined_ai_registry.json",
            "server": {
                "name": "ai-registry",
                "version": "1.0.0",
                "transport": "stdio",  # or "http"
                "http_port": 8080,
                "http_host": "localhost",
            },
            "cache": {
                "enabled": True,
                "ttl": 3600,  # 1 hour
                "max_size": 100,  # Maximum number of cached queries
                "strategy": "lru",  # Least Recently Used
            },
            "indexing": {
                "enabled": True,
                "index_fields": [
                    "name",
                    "description",
                    "narrative",
                    "application_domain",
                    "ai_methods",
                    "tasks",
                ],
                "fuzzy_matching": True,
                "similarity_threshold": 0.7,
            },
            "logging": {
                "level": "INFO",
                "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
                "file": "logs/ai_registry_server.log",
            },
            "performance": {
                "max_results": 50,  # Maximum results per query
                "timeout": 30,  # Query timeout in seconds
                "parallel_processing": True,
            },
        }

        # Load configuration
        self.config = self._load_config(config_file)

        # Resolve paths
        self._resolve_paths()

    def _load_config(self, config_file: Optional[str]) -> Dict[str, Any]:
        """Load configuration from file or use defaults."""
        config = self.defaults.copy()

        # Check for config file in standard locations
        if not config_file:
            possible_paths = [
                "apps/ai_registry/data/server_config.yaml",
                "config/ai_registry.yaml",
                ".ai_registry_config.yaml",
            ]
            for path in possible_paths:
                if os.path.exists(path):
                    config_file = path
                    break

        # Load from file if exists
        if config_file and os.path.exists(config_file):
            with open(config_file, "r") as f:
                file_config = yaml.safe_load(f)
                if file_config:
                    self._deep_merge(config, file_config)

        # Override with environment variables
        self._apply_env_overrides(config)

        return config

    def _deep_merge(self, base: Dict[str, Any], update: Dict[str, Any]) -> None:
        """Deep merge update dictionary into base dictionary."""
        for key, value in update.items():
            if key in base and isinstance(base[key], dict) and isinstance(value, dict):
                self._deep_merge(base[key], value)
            else:
                base[key] = value

    def _apply_env_overrides(self, config: Dict[str, Any]) -> None:
        """Apply environment variable overrides."""
        # Registry file path
        if env_registry := os.getenv("AI_REGISTRY_FILE"):
            config["registry_file"] = env_registry

        # Server settings
        if env_transport := os.getenv("AI_REGISTRY_TRANSPORT"):
            config["server"]["transport"] = env_transport
        if env_port := os.getenv("AI_REGISTRY_PORT"):
            config["server"]["http_port"] = int(env_port)

        # Cache settings
        if env_cache := os.getenv("AI_REGISTRY_CACHE_ENABLED"):
            config["cache"]["enabled"] = env_cache.lower() == "true"

        # Logging level
        if env_log_level := os.getenv("AI_REGISTRY_LOG_LEVEL"):
            config["logging"]["level"] = env_log_level

    def _resolve_paths(self) -> None:
        """Resolve relative paths to absolute paths."""
        # Get project root (assuming we're in src/solutions/ai_registry/)
        module_dir = Path(__file__).parent
        project_root = module_dir.parent.parent.parent

        # Resolve registry file path
        registry_path = Path(self.config["registry_file"])
        if not registry_path.is_absolute():
            self.config["registry_file"] = str(project_root / registry_path)

        # Ensure log directory exists
        if "file" in self.config["logging"]:
            log_path = Path(self.config["logging"]["file"])
            if not log_path.is_absolute():
                log_path = project_root / log_path
            log_path.parent.mkdir(parents=True, exist_ok=True)
            self.config["logging"]["file"] = str(log_path)

    def get(self, key: str, default: Any = None) -> Any:
        """Get configuration value using dot notation."""
        keys = key.split(".")
        value = self.config

        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default

        return value

    def set(self, key: str, value: Any) -> None:
        """Set configuration value using dot notation."""
        keys = key.split(".")
        config = self.config

        for k in keys[:-1]:
            if k not in config:
                config[k] = {}
            config = config[k]

        config[keys[-1]] = value

    def save(self, config_file: str) -> None:
        """Save current configuration to file."""
        os.makedirs(os.path.dirname(config_file), exist_ok=True)
        with open(config_file, "w") as f:
            yaml.dump(self.config, f, default_flow_style=False, sort_keys=True)

    def __getitem__(self, key: str) -> Any:
        """Allow dictionary-style access."""
        return self.get(key)

    def __setitem__(self, key: str, value: Any) -> None:
        """Allow dictionary-style setting."""
        self.set(key, value)


# Global configuration instance
config = Config()
