"""
Configuration for the User Management Application
"""

from typing import List

try:
    from pydantic_settings import BaseSettings
except ImportError:
    from pydantic import BaseSettings


class Settings(BaseSettings):
    """Application settings with environment variable support."""

    # Server Configuration
    HOST: str = "0.0.0.0"
    PORT: int = 8000

    # CORS Configuration
    CORS_ORIGINS: List[str] = [
        "http://localhost:3000",
        "http://localhost:8080",
        "https://admin.company.com",
    ]

    # Database Configuration
    DATABASE_URL: str = "postgresql://kailash:kailash@localhost:5433/kailash"
    DATABASE_POOL_SIZE: int = 20
    DATABASE_MAX_OVERFLOW: int = 10

    # Session Configuration
    MAX_SESSIONS: int = 1000
    SESSION_TIMEOUT_MINUTES: int = 120

    # Authentication Configuration
    JWT_SECRET_KEY: str = "your-secret-key-change-in-production"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    # SSO Configuration
    SSO_PROVIDERS: List[str] = ["saml", "oauth2", "azure", "google", "okta"]
    SAML_ENTITY_ID: str = "kailash-user-mgmt"
    SAML_SSO_URL: str = "https://company.okta.com/app/kailash/sso/saml"

    # LDAP Configuration
    LDAP_SERVER: str = "ldap://company.com:389"
    LDAP_BASE_DN: str = "DC=company,DC=com"
    LDAP_AUTO_PROVISIONING: bool = True

    # Security Configuration
    ENABLE_RISK_ASSESSMENT: bool = True
    ENABLE_ADAPTIVE_AUTH: bool = True
    ENABLE_FRAUD_DETECTION: bool = True
    COMPLIANCE_MODE: str = "strict"

    # Performance Configuration
    ENABLE_CACHING: bool = True
    CACHE_TTL: int = 300
    ENABLE_METRICS: bool = True
    ENABLE_AUDIT_LOGGING: bool = True

    # WebSocket Configuration
    WS_HEARTBEAT_INTERVAL: int = 30
    WS_MAX_CONNECTIONS: int = 1000

    class Config:
        env_file = ".env"
        env_prefix = "USER_MGMT_"


# Create settings instance
settings = Settings()
