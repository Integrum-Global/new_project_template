"""
Unit tests for Nexus configuration system.
"""

import os
import tempfile

import pytest
import yaml
from nexus.core.config import ChannelConfig, FeaturesConfig, NexusConfig


class TestNexusConfig:
    """Test NexusConfig class."""

    def test_default_configuration(self):
        """Test default configuration values."""
        config = NexusConfig()

        assert config.name == "kailash-nexus"
        assert config.description == "Enterprise Multi-Channel Orchestration Platform"
        assert config.version == "1.0.0"

        # Check channel defaults
        assert config.channels.api.enabled is True
        assert config.channels.api.host == "localhost"
        assert config.channels.api.port == 8000
        assert config.channels.cli.enabled is True
        assert config.channels.mcp.enabled is True

        # Check feature defaults
        assert config.features.authentication.enabled is True
        assert config.features.multi_tenant.enabled is False
        assert config.features.marketplace.enabled is True

    def test_custom_configuration(self):
        """Test custom configuration values."""
        config = NexusConfig(
            name="Custom App",
            version="2.0.0",
            channels={"api": {"port": 9000}, "cli": {"enabled": False}},
        )

        assert config.name == "Custom App"
        assert config.version == "2.0.0"
        assert config.channels.api.port == 9000
        assert config.channels.cli.enabled is False

    def test_environment_override(self):
        """Test environment variable overrides."""
        # Set environment variables
        os.environ["NEXUS_NAME"] = "Env App"
        os.environ["NEXUS_API_PORT"] = "8080"
        os.environ["NEXUS_MULTI_TENANT_ENABLED"] = "true"

        try:
            config = NexusConfig()

            assert config.name == "Env App"
            assert config.channels.api.port == 8080
            assert config.features.multi_tenant.enabled is True
        finally:
            # Cleanup
            del os.environ["NEXUS_NAME"]
            del os.environ["NEXUS_API_PORT"]
            del os.environ["NEXUS_MULTI_TENANT_ENABLED"]

    def test_yaml_loading(self):
        """Test loading configuration from YAML."""
        yaml_content = """
name: YAML App
description: Loaded from YAML
version: 3.0.0
channels:
  api:
    port: 8888
    cors_origins:
      - http://localhost:3000
  mcp:
    enabled: false
features:
  marketplace:
    enabled: true
"""

        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            f.write(yaml_content)
            f.flush()

            try:
                config = NexusConfig.from_yaml(f.name)

                assert config.name == "YAML App"
                assert config.description == "Loaded from YAML"
                assert config.version == "3.0.0"
                assert config.channels.api.port == 8888
                assert config.channels.api.cors_origins == ["http://localhost:3000"]
                assert config.channels.mcp.enabled is False
                assert config.features.marketplace.enabled is True
            finally:
                os.unlink(f.name)

    def test_to_dict(self):
        """Test configuration serialization to dict."""
        config = NexusConfig(name="Test App", channels={"api": {"port": 7000}})

        config_dict = config.dict()

        assert config_dict["name"] == "Test App"
        assert config_dict["channels"]["api"]["port"] == 7000
        assert "description" in config_dict
        assert "features" in config_dict

    def test_channel_config_validation(self):
        """Test channel configuration validation."""
        # Valid config
        channel = ChannelConfig(enabled=True, host="localhost", port=8000)
        assert channel.enabled is True
        assert channel.host == "localhost"
        assert channel.port == 8000

        # Test CORS origins
        channel = ChannelConfig(cors_origins=["http://example.com"])
        assert channel.cors_origins == ["http://example.com"]

    def test_feature_config_defaults(self):
        """Test feature configuration defaults."""
        features = FeaturesConfig()

        # Check authentication defaults
        assert features.authentication.enabled is True
        assert features.authentication.providers == []
        assert features.authentication.mfa.required is False
        assert features.authentication.mfa.methods == ["totp"]

        # Check multi-tenant defaults
        assert features.multi_tenant.enabled is False
        assert features.multi_tenant.isolation == "strict"
        assert features.multi_tenant.default_quotas["workflows"] == 100

        # Check marketplace defaults
        assert features.marketplace.enabled is True
        assert features.marketplace.quality_gates_enabled is True

    def test_config_copy_with_updates(self):
        """Test creating config copies with updates."""
        config = NexusConfig()

        # Create a copy with updates
        config_dict = config.dict()
        config_dict.update({"name": "Updated App", "channels": {"api": {"port": 9999}}})
        new_config = NexusConfig(**config_dict)

        assert new_config.name == "Updated App"
        assert new_config.channels.api.port == 9999
        assert new_config.description == config.description  # Unchanged
