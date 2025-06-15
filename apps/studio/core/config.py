"""
Enterprise Studio Configuration Management

Comprehensive configuration system for Kailash Studio with enterprise features:
- Environment-based configuration with validation
- Security configuration with secrets management
- Middleware integration settings
- Performance and monitoring configuration
- SDK integration and feature flags
- Multi-tenant and compliance settings
"""

import os
import logging
import uuid
from dataclasses import dataclass, field
from datetime import timedelta
from pathlib import Path
from typing import Optional, List, Dict, Any, Union
from enum import Enum


logger = logging.getLogger(__name__)


class Environment(Enum):
    """Application environment types."""
    DEVELOPMENT = "development"
    STAGING = "staging"
    PRODUCTION = "production"
    TESTING = "testing"


class LogLevel(Enum):
    """Logging levels."""
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


class SecurityLevel(Enum):
    """Security configuration levels."""
    BASIC = "basic"
    ENHANCED = "enhanced"
    ENTERPRISE = "enterprise"


@dataclass
class DatabaseConfig:
    """Database configuration settings."""
    url: Optional[str] = None
    pool_size: int = 20
    max_overflow: int = 50
    pool_timeout: int = 30
    pool_recycle: int = 3600
    echo: bool = False
    enable_migrations: bool = True
    backup_enabled: bool = True
    backup_interval_hours: int = 24
    
    def __post_init__(self):
        """Initialize database configuration from environment."""
        self.url = os.getenv("STUDIO_DATABASE_URL", self.url)
        self.pool_size = int(os.getenv("STUDIO_DB_POOL_SIZE", self.pool_size))
        self.max_overflow = int(os.getenv("STUDIO_DB_MAX_OVERFLOW", self.max_overflow))
        self.pool_timeout = int(os.getenv("STUDIO_DB_POOL_TIMEOUT", self.pool_timeout))
        self.pool_recycle = int(os.getenv("STUDIO_DB_POOL_RECYCLE", self.pool_recycle))
        self.echo = os.getenv("STUDIO_DB_ECHO", "false").lower() == "true"
        self.enable_migrations = os.getenv("STUDIO_DB_MIGRATIONS", "true").lower() == "true"
        self.backup_enabled = os.getenv("STUDIO_DB_BACKUP", "true").lower() == "true"
        self.backup_interval_hours = int(os.getenv("STUDIO_DB_BACKUP_INTERVAL", self.backup_interval_hours))


@dataclass
class SecurityConfig:
    """Security configuration settings."""
    level: SecurityLevel = SecurityLevel.ENTERPRISE
    jwt_secret_key: str = field(default_factory=lambda: str(uuid.uuid4()))
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 1440  # 24 hours
    jwt_refresh_expire_days: int = 30
    api_key_enabled: bool = True
    api_key_header: str = "X-API-Key"
    session_timeout_minutes: int = 60
    max_login_attempts: int = 5
    lockout_duration_minutes: int = 30
    password_min_length: int = 12
    password_require_special: bool = True
    mfa_enabled: bool = False
    mfa_issuer: str = "Kailash Studio"
    encryption_key: Optional[str] = None
    enable_audit_logging: bool = True
    enable_threat_detection: bool = True
    enable_behavior_analysis: bool = True
    abac_evaluation_timeout_ms: int = 15
    compliance_frameworks: List[str] = field(default_factory=lambda: ["gdpr", "soc2", "iso27001"])
    data_retention_days: int = 2555  # 7 years
    
    def __post_init__(self):
        """Initialize security configuration from environment."""
        # Security level
        level_str = os.getenv("STUDIO_SECURITY_LEVEL", self.level.value)
        self.level = SecurityLevel(level_str)
        
        # JWT configuration
        self.jwt_secret_key = os.getenv("STUDIO_JWT_SECRET", self.jwt_secret_key)
        self.jwt_algorithm = os.getenv("STUDIO_JWT_ALGORITHM", self.jwt_algorithm)
        self.jwt_expire_minutes = int(os.getenv("STUDIO_JWT_EXPIRE_MINUTES", self.jwt_expire_minutes))
        self.jwt_refresh_expire_days = int(os.getenv("STUDIO_JWT_REFRESH_DAYS", self.jwt_refresh_expire_days))
        
        # API key configuration
        self.api_key_enabled = os.getenv("STUDIO_API_KEY_ENABLED", "true").lower() == "true"
        self.api_key_header = os.getenv("STUDIO_API_KEY_HEADER", self.api_key_header)
        
        # Session and authentication
        self.session_timeout_minutes = int(os.getenv("STUDIO_SESSION_TIMEOUT", self.session_timeout_minutes))
        self.max_login_attempts = int(os.getenv("STUDIO_MAX_LOGIN_ATTEMPTS", self.max_login_attempts))
        self.lockout_duration_minutes = int(os.getenv("STUDIO_LOCKOUT_DURATION", self.lockout_duration_minutes))
        
        # Password policy
        self.password_min_length = int(os.getenv("STUDIO_PASSWORD_MIN_LENGTH", self.password_min_length))
        self.password_require_special = os.getenv("STUDIO_PASSWORD_SPECIAL", "true").lower() == "true"
        
        # MFA configuration
        self.mfa_enabled = os.getenv("STUDIO_MFA_ENABLED", "false").lower() == "true"
        self.mfa_issuer = os.getenv("STUDIO_MFA_ISSUER", self.mfa_issuer)
        
        # Encryption
        self.encryption_key = os.getenv("STUDIO_ENCRYPTION_KEY", self.encryption_key)
        
        # Security features
        self.enable_audit_logging = os.getenv("STUDIO_AUDIT_LOGGING", "true").lower() == "true"
        self.enable_threat_detection = os.getenv("STUDIO_THREAT_DETECTION", "true").lower() == "true"
        self.enable_behavior_analysis = os.getenv("STUDIO_BEHAVIOR_ANALYSIS", "true").lower() == "true"
        self.abac_evaluation_timeout_ms = int(os.getenv("STUDIO_ABAC_TIMEOUT", self.abac_evaluation_timeout_ms))
        
        # Compliance
        frameworks_env = os.getenv("STUDIO_COMPLIANCE_FRAMEWORKS", ",".join(self.compliance_frameworks))
        self.compliance_frameworks = [f.strip() for f in frameworks_env.split(",")]
        self.data_retention_days = int(os.getenv("STUDIO_DATA_RETENTION_DAYS", self.data_retention_days))


@dataclass
class MiddlewareConfig:
    """Middleware integration configuration."""
    enabled: bool = True
    agent_ui_enabled: bool = True
    realtime_enabled: bool = True
    api_gateway_enabled: bool = True
    ai_chat_enabled: bool = True
    session_management_enabled: bool = True
    event_streaming_enabled: bool = True
    workflow_repository_cache_ttl: int = 300
    execution_repository_cache_ttl: int = 60
    max_concurrent_sessions: int = 1000
    websocket_heartbeat_interval: int = 30
    sse_retry_timeout: int = 3000
    middleware_timeout_seconds: int = 30
    
    def __post_init__(self):
        """Initialize middleware configuration from environment."""
        self.enabled = os.getenv("STUDIO_MIDDLEWARE_ENABLED", "true").lower() == "true"
        self.agent_ui_enabled = os.getenv("STUDIO_AGENT_UI_ENABLED", "true").lower() == "true"
        self.realtime_enabled = os.getenv("STUDIO_REALTIME_ENABLED", "true").lower() == "true"
        self.api_gateway_enabled = os.getenv("STUDIO_API_GATEWAY_ENABLED", "true").lower() == "true"
        self.ai_chat_enabled = os.getenv("STUDIO_AI_CHAT_ENABLED", "true").lower() == "true"
        self.session_management_enabled = os.getenv("STUDIO_SESSION_MGMT_ENABLED", "true").lower() == "true"
        self.event_streaming_enabled = os.getenv("STUDIO_EVENT_STREAMING_ENABLED", "true").lower() == "true"
        
        # Cache configuration
        self.workflow_repository_cache_ttl = int(os.getenv("STUDIO_WORKFLOW_CACHE_TTL", self.workflow_repository_cache_ttl))
        self.execution_repository_cache_ttl = int(os.getenv("STUDIO_EXECUTION_CACHE_TTL", self.execution_repository_cache_ttl))
        
        # Performance settings
        self.max_concurrent_sessions = int(os.getenv("STUDIO_MAX_CONCURRENT_SESSIONS", self.max_concurrent_sessions))
        self.websocket_heartbeat_interval = int(os.getenv("STUDIO_WS_HEARTBEAT_INTERVAL", self.websocket_heartbeat_interval))
        self.sse_retry_timeout = int(os.getenv("STUDIO_SSE_RETRY_TIMEOUT", self.sse_retry_timeout))
        self.middleware_timeout_seconds = int(os.getenv("STUDIO_MIDDLEWARE_TIMEOUT", self.middleware_timeout_seconds))


@dataclass
class ExecutionConfig:
    """Workflow execution configuration."""
    max_concurrent_executions: int = 10
    max_concurrent_per_tenant: int = 5
    default_timeout_seconds: int = 3600  # 1 hour
    max_timeout_seconds: int = 14400  # 4 hours
    cleanup_interval_minutes: int = 60
    retain_completed_days: int = 30
    retain_failed_days: int = 90
    enable_resource_monitoring: bool = True
    max_memory_mb: int = 1024
    max_cpu_percent: int = 80
    enable_auto_scaling: bool = False
    auto_scale_threshold: float = 0.8
    enable_execution_queue: bool = True
    queue_max_size: int = 1000
    priority_levels: List[str] = field(default_factory=lambda: ["low", "normal", "high", "critical"])
    
    def __post_init__(self):
        """Initialize execution configuration from environment."""
        self.max_concurrent_executions = int(os.getenv("STUDIO_MAX_EXECUTIONS", self.max_concurrent_executions))
        self.max_concurrent_per_tenant = int(os.getenv("STUDIO_MAX_EXECUTIONS_PER_TENANT", self.max_concurrent_per_tenant))
        self.default_timeout_seconds = int(os.getenv("STUDIO_EXECUTION_TIMEOUT", self.default_timeout_seconds))
        self.max_timeout_seconds = int(os.getenv("STUDIO_MAX_EXECUTION_TIMEOUT", self.max_timeout_seconds))
        self.cleanup_interval_minutes = int(os.getenv("STUDIO_CLEANUP_INTERVAL", self.cleanup_interval_minutes))
        self.retain_completed_days = int(os.getenv("STUDIO_RETAIN_COMPLETED_DAYS", self.retain_completed_days))
        self.retain_failed_days = int(os.getenv("STUDIO_RETAIN_FAILED_DAYS", self.retain_failed_days))
        
        # Resource monitoring
        self.enable_resource_monitoring = os.getenv("STUDIO_RESOURCE_MONITORING", "true").lower() == "true"
        self.max_memory_mb = int(os.getenv("STUDIO_MAX_MEMORY_MB", self.max_memory_mb))
        self.max_cpu_percent = int(os.getenv("STUDIO_MAX_CPU_PERCENT", self.max_cpu_percent))
        
        # Auto-scaling
        self.enable_auto_scaling = os.getenv("STUDIO_AUTO_SCALING", "false").lower() == "true"
        self.auto_scale_threshold = float(os.getenv("STUDIO_AUTO_SCALE_THRESHOLD", self.auto_scale_threshold))
        
        # Execution queue
        self.enable_execution_queue = os.getenv("STUDIO_EXECUTION_QUEUE", "true").lower() == "true"
        self.queue_max_size = int(os.getenv("STUDIO_QUEUE_MAX_SIZE", self.queue_max_size))
        
        # Priority levels
        priority_env = os.getenv("STUDIO_PRIORITY_LEVELS", ",".join(self.priority_levels))
        self.priority_levels = [p.strip() for p in priority_env.split(",")]


@dataclass
class AIConfig:
    """AI and LLM configuration."""
    default_provider: str = "ollama"
    default_model: str = "llama3.2:3b"
    providers: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    enable_ai_generation: bool = True
    enable_ai_chat: bool = True
    enable_ai_recommendations: bool = True
    enable_ai_troubleshooting: bool = True
    ai_timeout_seconds: int = 30
    max_tokens: int = 4096
    temperature: float = 0.7
    top_p: float = 0.9
    frequency_penalty: float = 0.0
    presence_penalty: float = 0.0
    enable_streaming: bool = True
    enable_function_calling: bool = True
    enable_embeddings: bool = True
    embedding_model: str = "all-MiniLM-L6-v2"
    vector_db_enabled: bool = False
    vector_db_url: Optional[str] = None
    
    def __post_init__(self):
        """Initialize AI configuration from environment."""
        self.default_provider = os.getenv("STUDIO_AI_PROVIDER", self.default_provider)
        self.default_model = os.getenv("STUDIO_AI_MODEL", self.default_model)
        
        # AI features
        self.enable_ai_generation = os.getenv("STUDIO_AI_GENERATION", "true").lower() == "true"
        self.enable_ai_chat = os.getenv("STUDIO_AI_CHAT", "true").lower() == "true"
        self.enable_ai_recommendations = os.getenv("STUDIO_AI_RECOMMENDATIONS", "true").lower() == "true"
        self.enable_ai_troubleshooting = os.getenv("STUDIO_AI_TROUBLESHOOTING", "true").lower() == "true"
        
        # AI parameters
        self.ai_timeout_seconds = int(os.getenv("STUDIO_AI_TIMEOUT", self.ai_timeout_seconds))
        self.max_tokens = int(os.getenv("STUDIO_AI_MAX_TOKENS", self.max_tokens))
        self.temperature = float(os.getenv("STUDIO_AI_TEMPERATURE", self.temperature))
        self.top_p = float(os.getenv("STUDIO_AI_TOP_P", self.top_p))
        self.frequency_penalty = float(os.getenv("STUDIO_AI_FREQUENCY_PENALTY", self.frequency_penalty))
        self.presence_penalty = float(os.getenv("STUDIO_AI_PRESENCE_PENALTY", self.presence_penalty))
        
        # Advanced AI features
        self.enable_streaming = os.getenv("STUDIO_AI_STREAMING", "true").lower() == "true"
        self.enable_function_calling = os.getenv("STUDIO_AI_FUNCTION_CALLING", "true").lower() == "true"
        self.enable_embeddings = os.getenv("STUDIO_AI_EMBEDDINGS", "true").lower() == "true"
        self.embedding_model = os.getenv("STUDIO_AI_EMBEDDING_MODEL", self.embedding_model)
        
        # Vector database
        self.vector_db_enabled = os.getenv("STUDIO_VECTOR_DB_ENABLED", "false").lower() == "true"
        self.vector_db_url = os.getenv("STUDIO_VECTOR_DB_URL", self.vector_db_url)
        
        # Initialize provider configurations
        self._initialize_providers()
    
    def _initialize_providers(self):
        """Initialize AI provider configurations."""
        # OpenAI configuration
        if os.getenv("OPENAI_API_KEY"):
            self.providers["openai"] = {
                "api_key": os.getenv("OPENAI_API_KEY"),
                "organization": os.getenv("OPENAI_ORGANIZATION"),
                "base_url": os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1"),
                "models": ["gpt-4", "gpt-4-turbo", "gpt-3.5-turbo"]
            }
        
        # Anthropic configuration
        if os.getenv("ANTHROPIC_API_KEY"):
            self.providers["anthropic"] = {
                "api_key": os.getenv("ANTHROPIC_API_KEY"),
                "base_url": os.getenv("ANTHROPIC_BASE_URL"),
                "models": ["claude-3-opus", "claude-3-sonnet", "claude-3-haiku"]
            }
        
        # Ollama configuration
        self.providers["ollama"] = {
            "base_url": os.getenv("OLLAMA_BASE_URL", "http://localhost:11434"),
            "models": ["llama3.2:3b", "llama3.2:7b", "llama3.2:70b", "mistral:7b"]
        }
        
        # Azure OpenAI configuration
        if os.getenv("AZURE_OPENAI_API_KEY"):
            self.providers["azure"] = {
                "api_key": os.getenv("AZURE_OPENAI_API_KEY"),
                "endpoint": os.getenv("AZURE_OPENAI_ENDPOINT"),
                "api_version": os.getenv("AZURE_OPENAI_API_VERSION", "2024-02-01"),
                "deployment": os.getenv("AZURE_OPENAI_DEPLOYMENT")
            }


@dataclass
class MonitoringConfig:
    """Monitoring and observability configuration."""
    enabled: bool = True
    metrics_enabled: bool = True
    health_check_enabled: bool = True
    performance_monitoring_enabled: bool = True
    log_level: LogLevel = LogLevel.INFO
    log_format: str = "json"
    enable_structured_logging: bool = True
    enable_request_logging: bool = True
    enable_error_tracking: bool = True
    enable_performance_profiling: bool = False
    metrics_port: int = 8001
    health_check_path: str = "/health"
    metrics_path: str = "/metrics"
    prometheus_enabled: bool = False
    grafana_dashboard_enabled: bool = False
    alert_webhooks: List[str] = field(default_factory=list)
    error_threshold_rate: float = 0.05  # 5% error rate threshold
    response_time_threshold_ms: int = 1000
    
    def __post_init__(self):
        """Initialize monitoring configuration from environment."""
        self.enabled = os.getenv("STUDIO_MONITORING_ENABLED", "true").lower() == "true"
        self.metrics_enabled = os.getenv("STUDIO_METRICS_ENABLED", "true").lower() == "true"
        self.health_check_enabled = os.getenv("STUDIO_HEALTH_CHECK_ENABLED", "true").lower() == "true"
        self.performance_monitoring_enabled = os.getenv("STUDIO_PERFORMANCE_MONITORING", "true").lower() == "true"
        
        # Logging configuration
        log_level_str = os.getenv("STUDIO_LOG_LEVEL", self.log_level.value)
        self.log_level = LogLevel(log_level_str)
        self.log_format = os.getenv("STUDIO_LOG_FORMAT", self.log_format)
        self.enable_structured_logging = os.getenv("STUDIO_STRUCTURED_LOGGING", "true").lower() == "true"
        self.enable_request_logging = os.getenv("STUDIO_REQUEST_LOGGING", "true").lower() == "true"
        self.enable_error_tracking = os.getenv("STUDIO_ERROR_TRACKING", "true").lower() == "true"
        self.enable_performance_profiling = os.getenv("STUDIO_PERFORMANCE_PROFILING", "false").lower() == "true"
        
        # Metrics configuration
        self.metrics_port = int(os.getenv("STUDIO_METRICS_PORT", self.metrics_port))
        self.health_check_path = os.getenv("STUDIO_HEALTH_CHECK_PATH", self.health_check_path)
        self.metrics_path = os.getenv("STUDIO_METRICS_PATH", self.metrics_path)
        self.prometheus_enabled = os.getenv("STUDIO_PROMETHEUS_ENABLED", "false").lower() == "true"
        self.grafana_dashboard_enabled = os.getenv("STUDIO_GRAFANA_ENABLED", "false").lower() == "true"
        
        # Alerting
        alert_webhooks_env = os.getenv("STUDIO_ALERT_WEBHOOKS", "")
        if alert_webhooks_env:
            self.alert_webhooks = [url.strip() for url in alert_webhooks_env.split(",")]
        
        self.error_threshold_rate = float(os.getenv("STUDIO_ERROR_THRESHOLD", self.error_threshold_rate))
        self.response_time_threshold_ms = int(os.getenv("STUDIO_RESPONSE_TIME_THRESHOLD", self.response_time_threshold_ms))


@dataclass
class SDKConfig:
    """Kailash SDK integration configuration."""
    enabled: bool = True
    use_database_nodes: bool = True
    use_security_nodes: bool = True
    use_ai_nodes: bool = True
    use_workflow_builder: bool = True
    use_async_runtime: bool = True
    use_business_templates: bool = True
    node_discovery_enabled: bool = True
    dynamic_node_loading: bool = True
    custom_node_paths: List[str] = field(default_factory=list)
    workflow_validation_enabled: bool = True
    execution_tracking_enabled: bool = True
    performance_optimization_enabled: bool = True
    sdk_cache_enabled: bool = True
    sdk_cache_ttl_seconds: int = 300
    
    def __post_init__(self):
        """Initialize SDK configuration from environment."""
        self.enabled = os.getenv("STUDIO_SDK_ENABLED", "true").lower() == "true"
        self.use_database_nodes = os.getenv("STUDIO_SDK_DATABASE_NODES", "true").lower() == "true"
        self.use_security_nodes = os.getenv("STUDIO_SDK_SECURITY_NODES", "true").lower() == "true"
        self.use_ai_nodes = os.getenv("STUDIO_SDK_AI_NODES", "true").lower() == "true"
        self.use_workflow_builder = os.getenv("STUDIO_SDK_WORKFLOW_BUILDER", "true").lower() == "true"
        self.use_async_runtime = os.getenv("STUDIO_SDK_ASYNC_RUNTIME", "true").lower() == "true"
        self.use_business_templates = os.getenv("STUDIO_SDK_BUSINESS_TEMPLATES", "true").lower() == "true"
        
        # Node configuration
        self.node_discovery_enabled = os.getenv("STUDIO_SDK_NODE_DISCOVERY", "true").lower() == "true"
        self.dynamic_node_loading = os.getenv("STUDIO_SDK_DYNAMIC_LOADING", "true").lower() == "true"
        
        # Custom node paths
        custom_paths_env = os.getenv("STUDIO_SDK_CUSTOM_NODE_PATHS", "")
        if custom_paths_env:
            self.custom_node_paths = [path.strip() for path in custom_paths_env.split(",")]
        
        # Workflow features
        self.workflow_validation_enabled = os.getenv("STUDIO_SDK_WORKFLOW_VALIDATION", "true").lower() == "true"
        self.execution_tracking_enabled = os.getenv("STUDIO_SDK_EXECUTION_TRACKING", "true").lower() == "true"
        self.performance_optimization_enabled = os.getenv("STUDIO_SDK_PERFORMANCE_OPT", "true").lower() == "true"
        
        # SDK caching
        self.sdk_cache_enabled = os.getenv("STUDIO_SDK_CACHE_ENABLED", "true").lower() == "true"
        self.sdk_cache_ttl_seconds = int(os.getenv("STUDIO_SDK_CACHE_TTL", self.sdk_cache_ttl_seconds))


@dataclass
class StudioConfig:
    """Main Studio configuration combining all sub-configurations."""
    
    # Environment and server
    environment: Environment = Environment.DEVELOPMENT
    host: str = "0.0.0.0"
    port: int = 8000
    debug: bool = False
    reload: bool = False
    workers: int = 1
    
    # CORS configuration
    cors_origins: List[str] = field(default_factory=lambda: ["http://localhost:3000", "http://localhost:5173"])
    cors_allow_credentials: bool = True
    cors_allow_methods: List[str] = field(default_factory=lambda: ["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"])
    cors_allow_headers: List[str] = field(default_factory=lambda: ["*"])
    
    # Multi-tenant configuration
    default_tenant_id: str = "default"
    multi_tenant_enabled: bool = True
    tenant_isolation_enabled: bool = True
    
    # Feature flags
    enable_auth: bool = True
    enable_api_docs: bool = True
    enable_admin_interface: bool = True
    enable_webhooks: bool = True
    enable_export: bool = True
    enable_import: bool = True
    enable_collaboration: bool = True
    
    # Sub-configurations
    database: DatabaseConfig = field(default_factory=DatabaseConfig)
    security: SecurityConfig = field(default_factory=SecurityConfig)
    middleware: MiddlewareConfig = field(default_factory=MiddlewareConfig)
    execution: ExecutionConfig = field(default_factory=ExecutionConfig)
    ai: AIConfig = field(default_factory=AIConfig)
    monitoring: MonitoringConfig = field(default_factory=MonitoringConfig)
    sdk: SDKConfig = field(default_factory=SDKConfig)
    
    def __post_init__(self):
        """Initialize configuration from environment variables."""
        # Environment and server
        env_str = os.getenv("STUDIO_ENVIRONMENT", self.environment.value)
        self.environment = Environment(env_str)
        
        self.host = os.getenv("STUDIO_HOST", self.host)
        self.port = int(os.getenv("STUDIO_PORT", self.port))
        self.debug = os.getenv("STUDIO_DEBUG", "false").lower() == "true"
        self.reload = os.getenv("STUDIO_RELOAD", "false").lower() == "true"
        self.workers = int(os.getenv("STUDIO_WORKERS", self.workers))
        
        # CORS configuration
        origins_env = os.getenv("STUDIO_CORS_ORIGINS", ",".join(self.cors_origins))
        self.cors_origins = [origin.strip() for origin in origins_env.split(",")]
        
        methods_env = os.getenv("STUDIO_CORS_METHODS", ",".join(self.cors_allow_methods))
        self.cors_allow_methods = [method.strip() for method in methods_env.split(",")]
        
        headers_env = os.getenv("STUDIO_CORS_HEADERS", ",".join(self.cors_allow_headers))
        self.cors_allow_headers = [header.strip() for header in headers_env.split(",")]
        
        self.cors_allow_credentials = os.getenv("STUDIO_CORS_CREDENTIALS", "true").lower() == "true"
        
        # Multi-tenant configuration
        self.default_tenant_id = os.getenv("STUDIO_DEFAULT_TENANT", self.default_tenant_id)
        self.multi_tenant_enabled = os.getenv("STUDIO_MULTI_TENANT", "true").lower() == "true"
        self.tenant_isolation_enabled = os.getenv("STUDIO_TENANT_ISOLATION", "true").lower() == "true"
        
        # Feature flags
        self.enable_auth = os.getenv("STUDIO_ENABLE_AUTH", "true").lower() == "true"
        self.enable_api_docs = os.getenv("STUDIO_ENABLE_API_DOCS", "true").lower() == "true"
        self.enable_admin_interface = os.getenv("STUDIO_ENABLE_ADMIN", "true").lower() == "true"
        self.enable_webhooks = os.getenv("STUDIO_ENABLE_WEBHOOKS", "true").lower() == "true"
        self.enable_export = os.getenv("STUDIO_ENABLE_EXPORT", "true").lower() == "true"
        self.enable_import = os.getenv("STUDIO_ENABLE_IMPORT", "true").lower() == "true"
        self.enable_collaboration = os.getenv("STUDIO_ENABLE_COLLABORATION", "true").lower() == "true"
        
        # Apply environment-specific defaults
        self._apply_environment_defaults()
        
        # Validate configuration
        self._validate_configuration()
    
    def _apply_environment_defaults(self):
        """Apply environment-specific configuration defaults."""
        if self.environment == Environment.PRODUCTION:
            # Production defaults
            self.debug = False
            self.reload = False
            self.security.level = SecurityLevel.ENTERPRISE
            self.security.mfa_enabled = True
            self.monitoring.enable_performance_profiling = True
            self.monitoring.prometheus_enabled = True
            self.database.backup_enabled = True
            self.execution.enable_resource_monitoring = True
            
        elif self.environment == Environment.STAGING:
            # Staging defaults
            self.debug = False
            self.reload = False
            self.security.level = SecurityLevel.ENHANCED
            self.monitoring.enable_performance_profiling = True
            
        elif self.environment == Environment.DEVELOPMENT:
            # Development defaults
            self.debug = True
            self.reload = True
            self.security.level = SecurityLevel.BASIC
            self.security.mfa_enabled = False
            self.database.echo = True
            
        elif self.environment == Environment.TESTING:
            # Testing defaults
            self.debug = True
            self.reload = False
            self.security.level = SecurityLevel.BASIC
            self.database.url = "sqlite:///test.db"
            self.monitoring.enabled = False
    
    def _validate_configuration(self):
        """Validate configuration settings."""
        errors = []
        
        # Validate port range
        if not (1 <= self.port <= 65535):
            errors.append(f"Invalid port number: {self.port}")
        
        # Validate JWT secret key in production
        if self.environment == Environment.PRODUCTION:
            if self.security.jwt_secret_key == "default-secret-key-change-in-production":
                errors.append("JWT secret key must be changed in production")
            
            if len(self.security.jwt_secret_key) < 32:
                errors.append("JWT secret key must be at least 32 characters in production")
        
        # Validate database URL for production
        if self.environment == Environment.PRODUCTION and not self.database.url:
            errors.append("Database URL must be configured for production")
        
        # Validate AI provider configuration
        if self.ai.enable_ai_generation and not self.ai.providers:
            logger.warning("AI generation enabled but no AI providers configured")
        
        # Log validation errors
        if errors:
            for error in errors:
                logger.error(f"Configuration validation error: {error}")
            if self.environment == Environment.PRODUCTION:
                raise ValueError(f"Configuration validation failed: {', '.join(errors)}")
    
    def get_database_url(self) -> str:
        """Get the database URL with fallback defaults."""
        if self.database.url:
            return self.database.url
        
        # Default SQLite database
        app_dir = Path(__file__).parent.parent
        data_dir = app_dir / "data" / "outputs"
        data_dir.mkdir(parents=True, exist_ok=True)
        
        db_name = f"studio_{self.environment.value}.db"
        return f"sqlite+aiosqlite:///{data_dir / db_name}"
    
    def is_development(self) -> bool:
        """Check if running in development environment."""
        return self.environment == Environment.DEVELOPMENT
    
    def is_production(self) -> bool:
        """Check if running in production environment."""
        return self.environment == Environment.PRODUCTION
    
    def is_testing(self) -> bool:
        """Check if running in testing environment."""
        return self.environment == Environment.TESTING
    
    def get_log_config(self) -> Dict[str, Any]:
        """Get logging configuration."""
        return {
            "version": 1,
            "disable_existing_loggers": False,
            "formatters": {
                "default": {
                    "format": "[%(asctime)s] %(levelname)s in %(module)s: %(message)s"
                },
                "json": {
                    "format": "%(asctime)s %(name)s %(levelname)s %(message)s",
                    "class": "pythonjsonlogger.jsonlogger.JsonFormatter"
                }
            },
            "handlers": {
                "console": {
                    "class": "logging.StreamHandler",
                    "formatter": "json" if self.monitoring.log_format == "json" else "default",
                    "level": self.monitoring.log_level.value
                }
            },
            "root": {
                "level": self.monitoring.log_level.value,
                "handlers": ["console"]
            }
        }
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert configuration to dictionary (excluding sensitive data)."""
        config_dict = {}
        
        # Basic settings
        config_dict.update({
            "environment": self.environment.value,
            "host": self.host,
            "port": self.port,
            "debug": self.debug,
            "workers": self.workers,
            "multi_tenant_enabled": self.multi_tenant_enabled,
            "default_tenant_id": self.default_tenant_id
        })
        
        # Feature flags
        config_dict["features"] = {
            "auth": self.enable_auth,
            "api_docs": self.enable_api_docs,
            "admin_interface": self.enable_admin_interface,
            "webhooks": self.enable_webhooks,
            "export": self.enable_export,
            "import": self.enable_import,
            "collaboration": self.enable_collaboration
        }
        
        # Sub-configurations (excluding sensitive data)
        config_dict["database"] = {
            "pool_size": self.database.pool_size,
            "max_overflow": self.database.max_overflow,
            "echo": self.database.echo,
            "enable_migrations": self.database.enable_migrations,
            "backup_enabled": self.database.backup_enabled
        }
        
        config_dict["security"] = {
            "level": self.security.level.value,
            "mfa_enabled": self.security.mfa_enabled,
            "enable_audit_logging": self.security.enable_audit_logging,
            "enable_threat_detection": self.security.enable_threat_detection,
            "compliance_frameworks": self.security.compliance_frameworks
        }
        
        config_dict["middleware"] = {
            "enabled": self.middleware.enabled,
            "agent_ui_enabled": self.middleware.agent_ui_enabled,
            "realtime_enabled": self.middleware.realtime_enabled,
            "ai_chat_enabled": self.middleware.ai_chat_enabled
        }
        
        config_dict["execution"] = {
            "max_concurrent_executions": self.execution.max_concurrent_executions,
            "default_timeout_seconds": self.execution.default_timeout_seconds,
            "enable_resource_monitoring": self.execution.enable_resource_monitoring,
            "enable_auto_scaling": self.execution.enable_auto_scaling
        }
        
        config_dict["ai"] = {
            "default_provider": self.ai.default_provider,
            "default_model": self.ai.default_model,
            "enable_ai_generation": self.ai.enable_ai_generation,
            "enable_ai_chat": self.ai.enable_ai_chat,
            "available_providers": list(self.ai.providers.keys())
        }
        
        config_dict["monitoring"] = {
            "enabled": self.monitoring.enabled,
            "log_level": self.monitoring.log_level.value,
            "metrics_enabled": self.monitoring.metrics_enabled,
            "health_check_enabled": self.monitoring.health_check_enabled
        }
        
        config_dict["sdk"] = {
            "enabled": self.sdk.enabled,
            "use_database_nodes": self.sdk.use_database_nodes,
            "use_security_nodes": self.sdk.use_security_nodes,
            "use_ai_nodes": self.sdk.use_ai_nodes
        }
        
        return config_dict


# Global configuration instance
config = StudioConfig()

# Configuration validation on module import
try:
    config._validate_configuration()
    logger.info(f"Studio configuration loaded successfully (Environment: {config.environment.value})")
except Exception as e:
    logger.error(f"Configuration validation failed: {e}")
    if config.environment == Environment.PRODUCTION:
        raise


def get_config() -> StudioConfig:
    """Get the global configuration instance."""
    return config


def reload_config() -> StudioConfig:
    """Reload configuration from environment variables."""
    global config
    config = StudioConfig()
    logger.info("Configuration reloaded from environment variables")
    return config