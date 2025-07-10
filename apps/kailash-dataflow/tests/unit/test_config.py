"""
Unit Tests: Configuration System

Tests DataFlow configuration with mocking.
Must be fast (< 1s per test) with no external dependencies.
"""

import os
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from dataflow.core import (
    DatabaseConfig,
    DataFlowConfig,
    Environment,
    MonitoringConfig,
    SecurityConfig,
)


class TestEnvironmentDetection:
    """Test environment detection logic."""

    def test_detect_development(self):
        """Test development environment detection."""
        test_cases = ["dev", "development", "local", "DEV", "DEVELOPMENT"]

        for env_value in test_cases:
            with patch.dict(os.environ, {"KAILASH_ENV": env_value}):
                assert Environment.detect() == Environment.DEVELOPMENT

    def test_detect_testing(self):
        """Test testing environment detection."""
        test_cases = ["test", "testing", "ci", "TEST", "TESTING"]

        for env_value in test_cases:
            with patch.dict(os.environ, {"KAILASH_ENV": env_value}):
                assert Environment.detect() == Environment.TESTING

    def test_detect_staging(self):
        """Test staging environment detection."""
        test_cases = ["stage", "staging", "pre-prod", "STAGE", "STAGING"]

        for env_value in test_cases:
            with patch.dict(os.environ, {"KAILASH_ENV": env_value}):
                assert Environment.detect() == Environment.STAGING

    def test_detect_production(self):
        """Test production environment detection."""
        test_cases = ["prod", "production", "live", "PROD", "PRODUCTION"]

        for env_value in test_cases:
            with patch.dict(os.environ, {"KAILASH_ENV": env_value}):
                assert Environment.detect() == Environment.PRODUCTION

    def test_detect_default(self):
        """Test default environment detection."""
        with patch.dict(os.environ, {}, clear=True):
            assert Environment.detect() == Environment.DEVELOPMENT

        with patch.dict(os.environ, {"KAILASH_ENV": "unknown"}):
            assert Environment.detect() == Environment.DEVELOPMENT


class TestDatabaseConfig:
    """Test database configuration."""

    def test_default_values(self):
        """Test default database configuration values."""
        config = DatabaseConfig()

        assert config.url is None
        assert config.driver is None
        assert config.host is None
        assert config.port is None
        assert config.pool_pre_ping is True
        assert config.echo is False

    def test_connection_url_explicit(self):
        """Test explicit connection URL."""
        config = DatabaseConfig(url="postgresql://user:pass@host:5432/db")

        assert (
            config.get_connection_url(Environment.PRODUCTION)
            == "postgresql://user:pass@host:5432/db"
        )

    def test_connection_url_from_env(self):
        """Test connection URL from environment variable."""
        with patch.dict(os.environ, {"DATABASE_URL": "mysql://localhost/test"}):
            config = DatabaseConfig()
            assert (
                config.get_connection_url(Environment.PRODUCTION)
                == "mysql://localhost/test"
            )

    def test_connection_url_from_components(self):
        """Test building connection URL from components."""
        config = DatabaseConfig(
            driver="postgresql",
            host="db.example.com",
            port=5432,
            database="myapp",
            username="user",
            password="secret",
        )

        expected = "postgresql://user:secret@db.example.com:5432/myapp"
        assert config.get_connection_url(Environment.PRODUCTION) == expected

    def test_connection_url_development_default(self):
        """Test development environment default."""
        config = DatabaseConfig()

        with patch.dict(os.environ, {}, clear=True):
            assert (
                config.get_connection_url(Environment.DEVELOPMENT)
                == "sqlite:///:memory:"
            )

    def test_connection_url_testing_default(self):
        """Test testing environment default."""
        config = DatabaseConfig()

        with patch.dict(os.environ, {}, clear=True):
            url = config.get_connection_url(Environment.TESTING)
            assert url.startswith("sqlite:///")
            assert "test_database.db" in url

    def test_connection_url_production_required(self):
        """Test production requires explicit configuration."""
        config = DatabaseConfig()

        with patch.dict(os.environ, {}, clear=True):
            with pytest.raises(
                ValueError, match="Production database configuration required"
            ):
                config.get_connection_url(Environment.PRODUCTION)

    @patch("multiprocessing.cpu_count", return_value=4)
    def test_pool_size_calculation(self, mock_cpu):
        """Test pool size calculation based on environment."""
        config = DatabaseConfig()

        assert config.get_pool_size(Environment.DEVELOPMENT) == 4  # min(5, 4)
        assert config.get_pool_size(Environment.TESTING) == 8  # min(10, 4*2)
        assert config.get_pool_size(Environment.STAGING) == 12  # min(20, 4*3)
        assert config.get_pool_size(Environment.PRODUCTION) == 16  # min(50, 4*4)

    def test_pool_size_explicit(self):
        """Test explicit pool size."""
        config = DatabaseConfig(pool_size=100)

        assert config.get_pool_size(Environment.DEVELOPMENT) == 100
        assert config.get_pool_size(Environment.PRODUCTION) == 100

    def test_max_overflow_calculation(self):
        """Test max overflow calculation."""
        config = DatabaseConfig()

        # Should be 2x pool size
        with patch.object(config, "get_pool_size", return_value=20):
            assert config.get_max_overflow(Environment.PRODUCTION) == 40

    def test_max_overflow_explicit(self):
        """Test explicit max overflow."""
        config = DatabaseConfig(max_overflow=50)

        assert config.get_max_overflow(Environment.PRODUCTION) == 50


class TestMonitoringConfig:
    """Test monitoring configuration."""

    def test_default_values(self):
        """Test default monitoring configuration."""
        config = MonitoringConfig()

        assert config.enabled is None
        assert config.slow_query_threshold == 1.0
        assert config.query_insights is True
        assert config.alert_on_slow_queries is True
        assert config.metrics_export_interval == 60
        assert config.metrics_export_format == "prometheus"

    def test_enabled_by_environment(self):
        """Test monitoring enabled based on environment."""
        config = MonitoringConfig()

        assert config.is_enabled(Environment.DEVELOPMENT) is False
        assert config.is_enabled(Environment.TESTING) is False
        assert config.is_enabled(Environment.STAGING) is True
        assert config.is_enabled(Environment.PRODUCTION) is True

    def test_enabled_explicit(self):
        """Test explicit monitoring enabled."""
        config = MonitoringConfig(enabled=True)

        assert config.is_enabled(Environment.DEVELOPMENT) is True

        config = MonitoringConfig(enabled=False)

        assert config.is_enabled(Environment.PRODUCTION) is False


class TestSecurityConfig:
    """Test security configuration."""

    def test_default_values(self):
        """Test default security configuration."""
        config = SecurityConfig()

        assert config.access_control_enabled is True
        assert config.access_control_strategy == "rbac"
        assert config.encrypt_at_rest is True
        assert config.encrypt_in_transit is True
        assert config.sql_injection_protection is True
        assert config.multi_tenant is False
        assert config.tenant_isolation_strategy == "schema"
        assert config.audit_enabled is True
        assert config.gdpr_mode is False

    def test_multi_tenant_config(self):
        """Test multi-tenant configuration."""
        config = SecurityConfig(multi_tenant=True, tenant_isolation_strategy="row")

        assert config.multi_tenant is True
        assert config.tenant_isolation_strategy == "row"


class TestDataFlowConfig:
    """Test main DataFlow configuration."""

    def test_default_values(self):
        """Test default DataFlow configuration."""
        config = DataFlowConfig()

        # Environment is auto-detected, so it won't be None
        assert config.environment in [
            Environment.DEVELOPMENT,
            Environment.TESTING,
            Environment.STAGING,
            Environment.PRODUCTION,
        ]
        assert isinstance(config.database, DatabaseConfig)
        assert isinstance(config.monitoring, MonitoringConfig)
        assert isinstance(config.security, SecurityConfig)
        assert config.auto_generate_nodes is True
        assert config.auto_migrate is True
        assert config.enable_query_cache is True
        assert config.cache_ttl == 300

    def test_post_init_environment(self):
        """Test environment detection in post_init."""
        with patch.dict(os.environ, {"KAILASH_ENV": "production"}):
            config = DataFlowConfig()
            assert config.environment == Environment.PRODUCTION

    def test_from_env(self):
        """Test configuration from environment variables."""
        env_vars = {
            "DATABASE_URL": "postgresql://localhost/test",
            "DB_POOL_SIZE": "50",
            "DATAFLOW_MONITORING": "true",
            "DATAFLOW_MULTI_TENANT": "true",
        }

        with patch.dict(os.environ, env_vars):
            config = DataFlowConfig.from_env()

            assert config.database.url == "postgresql://localhost/test"
            assert config.database.pool_size == 50
            assert config.monitoring.enabled is True
            assert config.security.multi_tenant is True

    def test_validation_production_database(self):
        """Test validation requires production database."""
        config = DataFlowConfig(environment=Environment.PRODUCTION)

        with patch.dict(os.environ, {}, clear=True):
            issues = config.validate()
            assert len(issues) == 1
            assert "Production database configuration required" in issues[0]

    def test_validation_multi_tenant_sqlite(self):
        """Test validation prevents multi-tenant with SQLite."""
        config = DataFlowConfig(
            environment=Environment.DEVELOPMENT,
            security=SecurityConfig(multi_tenant=True),
        )

        issues = config.validate()
        assert len(issues) == 1
        assert "Multi-tenant mode not supported with SQLite" in issues[0]

    def test_to_dict(self):
        """Test configuration serialization."""
        config = DataFlowConfig(
            environment=Environment.PRODUCTION,
            database=DatabaseConfig(url="postgresql://localhost/db"),
        )

        data = config.to_dict()

        assert data["environment"] == "production"
        assert data["database"]["url"] == "postgresql://localhost/db"
        assert "monitoring" in data
        assert "security" in data


class TestConfigurationIntegration:
    """Test configuration component integration."""

    def test_progressive_disclosure(self):
        """Test progressive configuration disclosure."""
        # Level 1: Zero config
        config1 = DataFlowConfig()
        assert config1.environment is not None

        # Level 2: Basic config
        config2 = DataFlowConfig(
            database=DatabaseConfig(url="postgresql://localhost/myapp")
        )
        assert config2.database.url == "postgresql://localhost/myapp"

        # Level 3: Advanced config
        config3 = DataFlowConfig(
            database=DatabaseConfig(pool_size=100),
            monitoring=MonitoringConfig(enabled=True),
            security=SecurityConfig(multi_tenant=True),
        )
        assert config3.database.pool_size == 100
        assert config3.monitoring.enabled is True
        assert config3.security.multi_tenant is True

    def test_environment_appropriate_defaults(self):
        """Test environment-appropriate configuration defaults."""
        # Development
        dev_config = DataFlowConfig(environment=Environment.DEVELOPMENT)
        assert dev_config.database.get_pool_size(dev_config.environment) <= 5
        assert dev_config.monitoring.is_enabled(dev_config.environment) is False

        # Production
        prod_config = DataFlowConfig(environment=Environment.PRODUCTION)
        with patch("multiprocessing.cpu_count", return_value=8):
            assert prod_config.database.get_pool_size(prod_config.environment) == 32
        assert prod_config.monitoring.is_enabled(prod_config.environment) is True
