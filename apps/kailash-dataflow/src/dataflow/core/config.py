"""
DataFlow Configuration System

Provides zero-configuration defaults with progressive disclosure for advanced users.
Automatically detects environment and configures optimal settings.
"""

import multiprocessing
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional

from .models import Environment


@dataclass
class DatabaseConfig:
    """Database configuration with intelligent defaults"""

    url: Optional[str] = None
    driver: Optional[str] = None
    host: Optional[str] = None
    port: Optional[int] = None
    database: Optional[str] = None
    username: Optional[str] = None
    password: Optional[str] = None

    # Connection pool settings
    pool_size: Optional[int] = None
    max_overflow: Optional[int] = None
    pool_timeout: Optional[float] = None
    pool_recycle: Optional[int] = None
    pool_pre_ping: bool = True

    # Advanced settings
    echo: bool = False
    echo_pool: bool = False
    connect_args: Dict[str, Any] = field(default_factory=dict)

    def get_connection_url(self, environment: Environment) -> str:
        """Generate connection URL based on configuration and environment"""
        # Check for explicit URL first
        if self.url:
            return self.url

        # Check environment variables
        env_url = os.getenv("DATABASE_URL")
        if env_url:
            return env_url

        # Build URL from components
        if all([self.driver, self.host, self.database]):
            auth = ""
            if self.username:
                auth = self.username
                if self.password:
                    auth += f":{self.password}"
                auth += "@"

            port = f":{self.port}" if self.port else ""
            return f"{self.driver}://{auth}{self.host}{port}/{self.database}"

        # Default based on environment
        if environment == Environment.DEVELOPMENT:
            # Use in-memory SQLite for instant development
            return "sqlite:///:memory:"
        elif environment == Environment.TESTING:
            # Use file-based SQLite for testing
            test_db = Path("test_database.db")
            return f"sqlite:///{test_db.absolute()}"
        else:
            # Production environments require explicit configuration
            raise ValueError(
                "Production database configuration required. "
                "Set DATABASE_URL environment variable or provide database configuration."
            )

    def get_pool_size(self, environment: Environment) -> int:
        """Calculate optimal pool size based on environment and resources"""
        if self.pool_size is not None:
            return self.pool_size

        # Calculate based on CPU cores and environment
        cpu_count = multiprocessing.cpu_count()

        if environment == Environment.DEVELOPMENT:
            return min(5, cpu_count)
        elif environment == Environment.TESTING:
            return min(10, cpu_count * 2)
        elif environment == Environment.STAGING:
            return min(20, cpu_count * 3)
        else:  # Production
            return min(50, cpu_count * 4)

    def get_max_overflow(self, environment: Environment) -> int:
        """Calculate max overflow based on pool size"""
        if self.max_overflow is not None:
            return self.max_overflow

        pool_size = self.get_pool_size(environment)
        return pool_size * 2  # Allow 2x overflow


@dataclass
class MonitoringConfig:
    """Monitoring configuration with production defaults"""

    enabled: Optional[bool] = None
    slow_query_threshold: float = 1.0  # seconds
    query_insights: bool = True
    connection_metrics: bool = True
    transaction_tracking: bool = True

    # Alerting
    alert_on_connection_exhaustion: bool = True
    alert_on_slow_queries: bool = True
    alert_on_failed_transactions: bool = True

    # Export settings
    metrics_export_interval: int = 60  # seconds
    metrics_export_format: str = "prometheus"  # prometheus, json, statsd

    def is_enabled(self, environment: Environment) -> bool:
        """Determine if monitoring should be enabled"""
        if self.enabled is not None:
            return self.enabled

        # Enable for staging and production by default
        return environment in [Environment.STAGING, Environment.PRODUCTION]

    def get_enabled_for_environment(self, environment: Environment) -> bool:
        """Get the effective enabled state for the given environment"""
        return self.is_enabled(environment)


@dataclass
class SecurityConfig:
    """Security configuration with enterprise defaults"""

    # Access control
    access_control_enabled: bool = True
    access_control_strategy: str = "rbac"  # rbac, abac, hybrid

    # Encryption
    encrypt_at_rest: bool = True
    encrypt_in_transit: bool = True

    # Query security
    sql_injection_protection: bool = True
    query_parameter_validation: bool = True

    # Multi-tenancy
    multi_tenant: bool = False
    tenant_isolation_strategy: str = "schema"  # schema, row, database

    # Audit
    audit_enabled: bool = True
    audit_log_retention_days: int = 90

    # Compliance
    gdpr_mode: bool = False
    pii_detection: bool = True
    data_masking: bool = True


@dataclass
class DataFlowConfig:
    """Main configuration object with intelligent defaults"""

    # Environment
    environment: Optional[Environment] = None

    # Core configurations
    database: DatabaseConfig = field(default_factory=DatabaseConfig)
    monitoring: MonitoringConfig = field(default_factory=MonitoringConfig)
    security: SecurityConfig = field(default_factory=SecurityConfig)

    # Node generation
    auto_generate_nodes: bool = True
    node_prefix: str = ""
    node_suffix: str = "Node"

    # Migration settings
    auto_migrate: bool = True
    migration_directory: Path = Path("migrations")

    # Cache settings
    enable_query_cache: bool = True
    cache_ttl: int = 300  # seconds
    redis_host: str = "localhost"
    redis_port: int = 6379
    redis_db: int = 0
    redis_password: Optional[str] = None
    cache_invalidation_strategy: str = (
        "pattern_based"  # ttl, manual, pattern_based, event_based
    )
    cache_key_prefix: str = "dataflow:query"

    # Development settings
    debug: bool = False
    hot_reload: bool = True

    # Advanced settings
    custom_node_templates: Optional[Path] = None
    plugin_directory: Optional[Path] = None

    def __post_init__(self):
        """Post-initialization configuration"""
        # Auto-detect environment if not set
        if self.environment is None:
            self.environment = Environment.detect()

        # Set debug based on environment
        if self.debug is None:
            self.debug = self.environment == Environment.DEVELOPMENT

        # Set monitoring defaults based on environment
        if self.monitoring.enabled is None:
            self.monitoring.enabled = self.monitoring.is_enabled(self.environment)

    @classmethod
    def from_env(cls) -> "DataFlowConfig":
        """Create configuration from environment variables"""
        config = cls()

        # Database configuration from env
        if db_url := os.getenv("DATABASE_URL"):
            config.database.url = db_url

        # Pool settings from env
        if pool_size := os.getenv("DATAFLOW_POOL_SIZE", os.getenv("DB_POOL_SIZE")):
            config.database.pool_size = int(pool_size)

        if max_overflow := os.getenv(
            "DATAFLOW_MAX_OVERFLOW", os.getenv("DB_MAX_OVERFLOW")
        ):
            config.database.max_overflow = int(max_overflow)

        # Monitoring from env
        if monitoring := os.getenv(
            "DATAFLOW_ENABLE_MONITORING", os.getenv("DATAFLOW_MONITORING")
        ):
            config.monitoring.enabled = monitoring.lower() == "true"

        # Security from env
        if multi_tenant := os.getenv(
            "DATAFLOW_ENABLE_MULTI_TENANT", os.getenv("DATAFLOW_MULTI_TENANT")
        ):
            config.security.multi_tenant = multi_tenant.lower() == "true"

        # Cache settings from env
        if cache_enabled := os.getenv("DATAFLOW_QUERY_CACHE"):
            config.enable_query_cache = cache_enabled.lower() == "true"

        if redis_host := os.getenv("REDIS_HOST"):
            config.redis_host = redis_host

        if redis_port := os.getenv("REDIS_PORT"):
            config.redis_port = int(redis_port)

        if cache_strategy := os.getenv("DATAFLOW_CACHE_STRATEGY"):
            config.cache_invalidation_strategy = cache_strategy

        if cache_ttl := os.getenv("DATAFLOW_CACHE_TTL"):
            config.cache_ttl = int(cache_ttl)

        return config

    def validate(self) -> List[str]:
        """Validate configuration and return any issues"""
        issues = []

        # Production requires explicit database configuration
        if self.environment == Environment.PRODUCTION:
            try:
                db_url = self.database.get_connection_url(self.environment)
                # SQLite not recommended for production
                if "sqlite" in db_url:
                    issues.append(
                        "SQLite database not recommended for production environment"
                    )
            except ValueError as e:
                issues.append(str(e))

        # Multi-tenant requires specific database support
        if self.security.multi_tenant:
            db_url = self.database.get_connection_url(self.environment)
            if "sqlite" in db_url:
                issues.append("Multi-tenant mode not supported with SQLite")

        # Validate database URL format
        if self.database.url:
            valid_schemes = ["sqlite", "postgresql", "mysql", "oracle", "mssql"]
            if not any(
                self.database.url.startswith(f"{scheme}://") for scheme in valid_schemes
            ):
                issues.append("Invalid database URL format")

        # Validate pool size
        if self.database.pool_size is not None and self.database.pool_size <= 0:
            issues.append("Pool size must be positive")

        # Validate pool size vs max overflow relationship
        if (
            self.database.pool_size is not None
            and self.database.max_overflow is not None
            and self.database.max_overflow < self.database.pool_size
        ):
            issues.append("Max overflow should be >= pool size")

        return issues

    def to_dict(self) -> Dict[str, Any]:
        """Convert configuration to dictionary for serialization"""
        return {
            "environment": self.environment.value,
            "database": {
                "url": self.database.url,
                "pool_size": self.database.get_pool_size(self.environment),
                "max_overflow": self.database.get_max_overflow(self.environment),
            },
            "monitoring": {
                "enabled": self.monitoring.is_enabled(self.environment),
                "slow_query_threshold": self.monitoring.slow_query_threshold,
            },
            "security": {
                "access_control_enabled": self.security.access_control_enabled,
                "multi_tenant": self.security.multi_tenant,
            },
        }
