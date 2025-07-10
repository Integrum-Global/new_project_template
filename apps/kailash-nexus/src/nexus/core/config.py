"""
Nexus Application Configuration

Enterprise configuration built on top of SDK configuration.
"""

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional

import yaml


@dataclass
class ChannelConfig:
    """Configuration for a single channel."""

    enabled: bool = True
    host: str = "localhost"
    port: int = 8000
    authentication_required: bool = False
    rate_limiting: Optional[Dict[str, Any]] = None
    cors_origins: List[str] = field(default_factory=lambda: ["*"])


@dataclass
class APIChannelConfig(ChannelConfig):
    """API-specific channel configuration."""

    port: int = 8000
    enable_docs: bool = True
    enable_playground: bool = True
    max_request_size: int = 10 * 1024 * 1024  # 10MB


@dataclass
class CLIChannelConfig(ChannelConfig):
    """CLI-specific channel configuration."""

    interactive: bool = False
    prompt_template: str = "nexus> "
    history_file: str = "~/.nexus_history"
    completions_enabled: bool = True


@dataclass
class MCPChannelConfig(ChannelConfig):
    """MCP-specific channel configuration."""

    port: int = 3001
    server_name: str = "kailash-nexus-mcp"
    max_connections: int = 1000
    tool_discovery_cache_ttl: int = 300


@dataclass
class ChannelsConfig:
    """Configuration for all channels."""

    api: APIChannelConfig = field(default_factory=APIChannelConfig)
    cli: CLIChannelConfig = field(default_factory=CLIChannelConfig)
    mcp: MCPChannelConfig = field(default_factory=MCPChannelConfig)


@dataclass
class MultiTenantConfig:
    """Multi-tenant configuration."""

    enabled: bool = False
    isolation: str = "strict"  # strict, moderate, basic
    default_quotas: Dict[str, Any] = field(
        default_factory=lambda: {
            "workflows": 100,
            "executions_per_day": 10000,
            "storage_mb": 1024,
            "api_calls_per_hour": 1000,
        }
    )
    custom_domains_enabled: bool = False
    data_residency_enabled: bool = False


@dataclass
class AuthProvider:
    """Authentication provider configuration."""

    type: str  # ldap, oauth2, saml
    enabled: bool = True
    config: Dict[str, Any] = field(default_factory=dict)


@dataclass
class MFAConfig:
    """Multi-factor authentication configuration."""

    required: bool = False
    methods: List[str] = field(default_factory=lambda: ["totp"])
    grace_period_seconds: int = 300


@dataclass
class AuthenticationConfig:
    """Authentication configuration."""

    enabled: bool = True
    providers: List[AuthProvider] = field(default_factory=list)
    mfa: MFAConfig = field(default_factory=MFAConfig)
    session_timeout: int = 3600
    api_key_enabled: bool = True
    jwt_secret: Optional[str] = None


@dataclass
class RBACConfig:
    """Role-based access control configuration."""

    enabled: bool = True
    default_roles: List[str] = field(
        default_factory=lambda: ["viewer", "developer", "admin"]
    )
    custom_roles_enabled: bool = True
    inheritance_enabled: bool = True


@dataclass
class AuditConfig:
    """Audit logging configuration."""

    enabled: bool = True
    retention_days: int = 2557  # 7 years
    storage_backend: str = "database"  # database, s3, filesystem
    storage_config: Dict[str, Any] = field(default_factory=dict)
    compliance_mode: str = "standard"  # standard, gdpr, hipaa, sox


@dataclass
class MonitoringConfig:
    """Monitoring configuration."""

    enabled: bool = True
    health_checks: bool = True
    metrics_enabled: bool = True
    prometheus_enabled: bool = True
    metrics_port: int = 9090
    tracing_enabled: bool = True
    tracing_backend: str = "jaeger"
    logging_level: str = "INFO"


@dataclass
class MarketplaceConfig:
    """Workflow marketplace configuration."""

    enabled: bool = True
    private_registry: bool = True
    public_sharing_enabled: bool = False
    quality_gates_enabled: bool = True
    version_control_enabled: bool = True


@dataclass
class SessionConfig:
    """Session management configuration."""

    timeout: int = 3600
    cleanup_interval: int = 300
    cross_channel_sync: bool = True
    persistence_enabled: bool = True
    persistence_backend: str = "redis"


@dataclass
class FeaturesConfig:
    """Enterprise features configuration."""

    multi_tenant: MultiTenantConfig = field(default_factory=MultiTenantConfig)
    authentication: AuthenticationConfig = field(default_factory=AuthenticationConfig)
    rbac: RBACConfig = field(default_factory=RBACConfig)
    audit: AuditConfig = field(default_factory=AuditConfig)
    monitoring: MonitoringConfig = field(default_factory=MonitoringConfig)
    marketplace: MarketplaceConfig = field(default_factory=MarketplaceConfig)
    session: SessionConfig = field(default_factory=SessionConfig)


@dataclass
class DeploymentConfig:
    """Deployment configuration."""

    environment: str = "development"  # development, staging, production
    cluster_enabled: bool = False
    cluster_nodes: int = 1
    auto_scaling_enabled: bool = False
    backup_enabled: bool = False
    backup_schedule: str = "0 2 * * *"  # 2 AM daily


@dataclass
class NexusConfig:
    """Complete Nexus application configuration."""

    # Basic settings
    name: str = "kailash-nexus"
    description: str = "Enterprise Multi-Channel Orchestration Platform"
    version: str = "1.0.0"

    # Channels
    channels: ChannelsConfig = field(default_factory=ChannelsConfig)

    # Enterprise features
    features: FeaturesConfig = field(default_factory=FeaturesConfig)

    # Deployment
    deployment: DeploymentConfig = field(default_factory=DeploymentConfig)

    # Advanced settings
    config_file: Optional[str] = None

    def __post_init__(self):
        """Load configuration from file if specified."""
        # Handle dictionary inputs for channels and features
        if isinstance(self.channels, dict):
            channels_data = self.channels
            self.channels = ChannelsConfig()  # Create default config first
            self._update_channels(channels_data)
        if isinstance(self.features, dict):
            features_data = self.features
            self.features = FeaturesConfig()  # Create default config first
            self._update_features(features_data)
        if isinstance(self.deployment, dict):
            deployment_data = self.deployment
            self.deployment = DeploymentConfig()  # Create default config first
            self._update_deployment(deployment_data)

        # Load environment variables
        self._load_from_env()

        if self.config_file:
            self.load_from_file(self.config_file)
        else:
            # Check for environment variable
            config_path = os.environ.get("NEXUS_CONFIG")
            if config_path:
                self.load_from_file(config_path)

    def load_from_file(self, filepath: str):
        """Load configuration from YAML file.

        Args:
            filepath: Path to configuration file
        """
        path = Path(filepath).expanduser()
        if not path.exists():
            raise FileNotFoundError(f"Configuration file not found: {filepath}")

        with open(path, "r") as f:
            data = yaml.safe_load(f)

        # Update configuration from file
        self._update_from_dict(data)

    def _update_from_dict(self, data: Dict[str, Any]):
        """Update configuration from dictionary.

        Args:
            data: Configuration dictionary
        """
        # Update basic settings
        self.name = data.get("name", self.name)
        self.description = data.get("description", self.description)
        self.version = data.get("version", self.version)

        # Update channels
        if "channels" in data:
            self._update_channels(data["channels"])

        # Update features
        if "features" in data:
            self._update_features(data["features"])

        # Update deployment
        if "deployment" in data:
            self._update_deployment(data["deployment"])

    def _update_channels(self, channels_data: Dict[str, Any]):
        """Update channel configuration."""
        if "api" in channels_data:
            api_data = channels_data["api"]
            self.channels.api.enabled = api_data.get("enabled", True)
            self.channels.api.port = api_data.get("port", 8000)
            self.channels.api.cors_origins = api_data.get(
                "cors_origins", api_data.get("cors", ["*"])
            )

        if "cli" in channels_data:
            cli_data = channels_data["cli"]
            self.channels.cli.enabled = cli_data.get("enabled", True)
            self.channels.cli.interactive = cli_data.get("interactive", False)

        if "mcp" in channels_data:
            mcp_data = channels_data["mcp"]
            self.channels.mcp.enabled = mcp_data.get("enabled", True)
            self.channels.mcp.port = mcp_data.get("port", 3001)

    def _update_features(self, features_data: Dict[str, Any]):
        """Update features configuration."""
        # Multi-tenant
        if "multi_tenant" in features_data:
            mt_data = features_data["multi_tenant"]
            self.features.multi_tenant.enabled = mt_data.get("enabled", False)
            self.features.multi_tenant.isolation = mt_data.get("isolation", "strict")
            if "default_quotas" in mt_data:
                self.features.multi_tenant.default_quotas.update(
                    mt_data["default_quotas"]
                )

        # Authentication
        if "authentication" in features_data:
            auth_data = features_data["authentication"]
            self.features.authentication.enabled = auth_data.get("enabled", True)

            # Providers
            if "providers" in auth_data:
                self.features.authentication.providers = [
                    AuthProvider(**p) for p in auth_data["providers"]
                ]

            # MFA
            if "mfa" in auth_data:
                mfa_data = auth_data["mfa"]
                self.features.authentication.mfa.required = mfa_data.get(
                    "required", False
                )
                self.features.authentication.mfa.methods = mfa_data.get(
                    "methods", ["totp"]
                )

        # Marketplace
        if "marketplace" in features_data:
            marketplace_data = features_data["marketplace"]
            self.features.marketplace.enabled = marketplace_data.get("enabled", True)
            self.features.marketplace.private_registry = marketplace_data.get(
                "private_registry", True
            )
            self.features.marketplace.public_sharing_enabled = marketplace_data.get(
                "public_sharing_enabled", False
            )

    def _update_deployment(self, deployment_data: Dict[str, Any]):
        """Update deployment configuration."""
        self.deployment.environment = deployment_data.get("environment", "development")
        self.deployment.cluster_enabled = deployment_data.get("cluster_enabled", False)
        self.deployment.cluster_nodes = deployment_data.get("cluster_nodes", 1)

    def to_dict(self) -> Dict[str, Any]:
        """Convert configuration to dictionary.

        Returns:
            Configuration dictionary
        """
        return {
            "name": self.name,
            "description": self.description,
            "version": self.version,
            "channels": {
                "api": {
                    "enabled": self.channels.api.enabled,
                    "port": self.channels.api.port,
                    "cors": self.channels.api.cors_origins,
                },
                "cli": {
                    "enabled": self.channels.cli.enabled,
                    "interactive": self.channels.cli.interactive,
                },
                "mcp": {
                    "enabled": self.channels.mcp.enabled,
                    "port": self.channels.mcp.port,
                },
            },
            "features": {
                "multi_tenant": {
                    "enabled": self.features.multi_tenant.enabled,
                    "isolation": self.features.multi_tenant.isolation,
                },
                "authentication": {
                    "enabled": self.features.authentication.enabled,
                    "session_timeout": self.features.authentication.session_timeout,
                },
                "monitoring": {
                    "enabled": self.features.monitoring.enabled,
                    "metrics_port": self.features.monitoring.metrics_port,
                },
            },
            "deployment": {
                "environment": self.deployment.environment,
                "cluster_enabled": self.deployment.cluster_enabled,
            },
        }

    def validate(self) -> List[str]:
        """Validate configuration.

        Returns:
            List of validation errors, empty if valid
        """
        errors = []

        # Validate ports don't conflict
        ports = []
        if self.channels.api.enabled:
            ports.append(("api", self.channels.api.port))
        if self.channels.mcp.enabled:
            ports.append(("mcp", self.channels.mcp.port))
        if self.features.monitoring.metrics_enabled:
            ports.append(("metrics", self.features.monitoring.metrics_port))

        # Check for duplicates
        seen_ports = {}
        for name, port in ports:
            if port in seen_ports:
                errors.append(
                    f"Port conflict: {name} and {seen_ports[port]} both use port {port}"
                )
            seen_ports[port] = name

        # Validate authentication
        if (
            self.features.authentication.enabled
            and not self.features.authentication.providers
        ):
            errors.append("Authentication enabled but no providers configured")

        # Validate multi-tenant settings
        if self.features.multi_tenant.enabled:
            if self.features.multi_tenant.isolation not in [
                "strict",
                "moderate",
                "basic",
            ]:
                errors.append(
                    f"Invalid isolation level: {self.features.multi_tenant.isolation}"
                )

        return errors

    def _load_from_env(self):
        """Load configuration from environment variables."""
        # Basic settings
        if "NEXUS_NAME" in os.environ:
            self.name = os.environ["NEXUS_NAME"]
        if "NEXUS_DESCRIPTION" in os.environ:
            self.description = os.environ["NEXUS_DESCRIPTION"]
        if "NEXUS_VERSION" in os.environ:
            self.version = os.environ["NEXUS_VERSION"]

        # Channel settings
        if "NEXUS_API_PORT" in os.environ:
            self.channels.api.port = int(os.environ["NEXUS_API_PORT"])
        if "NEXUS_API_HOST" in os.environ:
            self.channels.api.host = os.environ["NEXUS_API_HOST"]
        if "NEXUS_MCP_PORT" in os.environ:
            self.channels.mcp.port = int(os.environ["NEXUS_MCP_PORT"])

        # Feature settings
        if "NEXUS_MULTI_TENANT_ENABLED" in os.environ:
            self.features.multi_tenant.enabled = (
                os.environ["NEXUS_MULTI_TENANT_ENABLED"].lower() == "true"
            )
        if "NEXUS_AUTH_ENABLED" in os.environ:
            self.features.authentication.enabled = (
                os.environ["NEXUS_AUTH_ENABLED"].lower() == "true"
            )
        if "NEXUS_MARKETPLACE_ENABLED" in os.environ:
            self.features.marketplace.enabled = (
                os.environ["NEXUS_MARKETPLACE_ENABLED"].lower() == "true"
            )

    @classmethod
    def from_yaml(cls, filepath: str) -> "NexusConfig":
        """Create config from YAML file.

        Args:
            filepath: Path to YAML configuration file

        Returns:
            NexusConfig instance
        """
        config = cls()
        config.load_from_file(filepath)
        return config

    def dict(self) -> Dict[str, Any]:
        """Convert to dictionary (alias for to_dict for compatibility)."""
        return self.to_dict()


# Convenience functions for common configurations
def create_development_config() -> NexusConfig:
    """Create a development configuration."""
    config = NexusConfig()
    config.deployment.environment = "development"
    config.features.authentication.enabled = False
    config.features.monitoring.logging_level = "DEBUG"
    config.channels.api.enable_playground = True
    return config


def create_production_config() -> NexusConfig:
    """Create a production configuration."""
    config = NexusConfig()
    config.deployment.environment = "production"
    config.deployment.cluster_enabled = True
    config.deployment.cluster_nodes = 3
    config.deployment.backup_enabled = True
    config.features.authentication.enabled = True
    config.features.authentication.mfa.required = True
    config.features.audit.enabled = True
    config.features.monitoring.enabled = True
    config.channels.api.enable_playground = False
    return config
