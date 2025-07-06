"""
User Management System Configuration
"""

import os
from datetime import timedelta
from typing import Any, Dict


class UserManagementConfig:
    """Configuration for the user management system"""

    # Database settings - Use test database for E2E tests
    DATABASE_URL = os.getenv(
        "USER_MANAGEMENT_DB_URL",
        "postgresql://test_user:test_password@localhost:5434/kailash_test",
    )

    # JWT settings
    JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "your-secret-key-change-in-production")
    JWT_ALGORITHM = "HS256"
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(hours=1)
    JWT_REFRESH_TOKEN_EXPIRES = timedelta(days=30)

    # Password settings
    PASSWORD_MIN_LENGTH = 8
    PASSWORD_REQUIRE_UPPERCASE = True
    PASSWORD_REQUIRE_LOWERCASE = True
    PASSWORD_REQUIRE_NUMBERS = True
    PASSWORD_REQUIRE_SPECIAL = True
    PASSWORD_RESET_TOKEN_EXPIRES = timedelta(hours=24)

    # Session settings
    SESSION_TIMEOUT = timedelta(minutes=30)
    MAX_SESSIONS_PER_USER = 5

    # Email settings
    EMAIL_VERIFICATION_REQUIRED = True
    EMAIL_VERIFICATION_TOKEN_EXPIRES = timedelta(days=7)

    # Security settings
    MAX_LOGIN_ATTEMPTS = 5
    LOCKOUT_DURATION = timedelta(minutes=30)
    ENABLE_2FA = True

    # Audit settings
    AUDIT_LOG_RETENTION_DAYS = 365
    AUDIT_LOG_EXPORT_FORMATS = ["json", "csv"]

    # API settings
    API_RATE_LIMIT = 1000  # requests per hour
    API_VERSION = "v1"

    # Node configurations
    NODE_CONFIGS: Dict[str, Any] = {
        "UserManagementNode": {
            "database_url": DATABASE_URL,
            "tenant_isolation": True,
            "batch_size": 100,
        },
        "RoleManagementNode": {
            "database_url": DATABASE_URL,
            "enable_hierarchy": True,
            "max_hierarchy_depth": 5,
        },
        "PermissionCheckNode": {
            "database_url": DATABASE_URL,
            "cache_ttl": 300,
            "enable_abac": True,
        },
        "EnterpriseAuditLogNode": {
            "database_url": DATABASE_URL,
            "retention_days": AUDIT_LOG_RETENTION_DAYS,
            "async_processing": True,
        },
        "EnterpriseSecurityEventNode": {
            "database_url": DATABASE_URL,
            "enable_ml_detection": True,
            "alert_threshold": "high",
        },
    }

    # Default roles
    DEFAULT_ROLES = [
        {
            "name": "admin",
            "description": "System administrator with full access",
            "permissions": ["*"],
            "is_system": True,
        },
        {
            "name": "user",
            "description": "Standard user role",
            "permissions": ["profile:read", "profile:update"],
            "is_system": True,
        },
        {
            "name": "moderator",
            "description": "Content moderator role",
            "permissions": ["user:read", "user:update", "content:*"],
            "is_system": True,
        },
    ]

    # CORS settings
    ALLOWED_ORIGINS = ["http://localhost:3000", "http://localhost:8000"]

    @classmethod
    def get_config(cls) -> Dict[str, Any]:
        """Get configuration as dictionary"""
        return {
            key: value
            for key, value in cls.__dict__.items()
            if not key.startswith("_") and not callable(value)
        }
