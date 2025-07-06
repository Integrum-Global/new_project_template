"""Tenant management service for multi-tenancy support."""

import asyncio
import uuid
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

import redis.asyncio as redis
import structlog
from sqlalchemy import JSON, Boolean, Column, DateTime, Integer, String
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

logger = structlog.get_logger(__name__)

Base = declarative_base()


class TenantStatus(str, Enum):
    """Tenant status."""

    ACTIVE = "active"
    SUSPENDED = "suspended"
    TRIAL = "trial"
    DELETED = "deleted"


class TenantTier(str, Enum):
    """Tenant subscription tier."""

    FREE = "free"
    STARTER = "starter"
    PROFESSIONAL = "professional"
    ENTERPRISE = "enterprise"


class Tenant(Base):
    """Tenant model."""

    __tablename__ = "tenants"

    tenant_id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String, nullable=False)
    display_name = Column(String)
    status = Column(String, default=TenantStatus.TRIAL)
    tier = Column(String, default=TenantTier.FREE)

    # Metadata
    metadata = Column(JSON, default={})
    settings = Column(JSON, default={})

    # Limits
    max_users = Column(Integer, default=10)
    max_api_calls_per_day = Column(Integer, default=10000)
    max_storage_gb = Column(Integer, default=10)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    trial_ends_at = Column(DateTime)

    # Billing
    billing_email = Column(String)
    billing_info = Column(JSON, default={})

    # Features
    enabled_features = Column(JSON, default=[])
    custom_domain = Column(String)

    # Security
    allowed_ip_ranges = Column(JSON, default=[])
    require_mfa = Column(Boolean, default=False)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "tenant_id": self.tenant_id,
            "name": self.name,
            "display_name": self.display_name,
            "status": self.status,
            "tier": self.tier,
            "metadata": self.metadata,
            "settings": self.settings,
            "limits": {
                "max_users": self.max_users,
                "max_api_calls_per_day": self.max_api_calls_per_day,
                "max_storage_gb": self.max_storage_gb,
            },
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "trial_ends_at": (
                self.trial_ends_at.isoformat() if self.trial_ends_at else None
            ),
            "enabled_features": self.enabled_features,
        }


class TenantManager:
    """Manages tenants and multi-tenancy."""

    def __init__(self, database_url: str = None, redis_url: str = None):
        self.database_url = (
            database_url or "postgresql+asyncpg://user:pass@localhost/gateway"
        )
        self.redis_url = redis_url
        self.engine = None
        self.session_factory = None
        self.redis_client = None
        self.tier_limits = self._get_tier_limits()

    async def initialize(self):
        """Initialize the tenant manager."""
        # Create database engine
        self.engine = create_async_engine(self.database_url, echo=False)
        self.session_factory = sessionmaker(
            self.engine, class_=AsyncSession, expire_on_commit=False
        )

        # Create tables
        async with self.engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

        # Initialize Redis
        if self.redis_url:
            self.redis_client = redis.from_url(self.redis_url)

        logger.info("Tenant manager initialized")

    async def cleanup(self):
        """Cleanup resources."""
        if self.engine:
            await self.engine.dispose()

        if self.redis_client:
            await self.redis_client.close()

    async def create_tenant(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new tenant."""
        async with self.session_factory() as session:
            # Create tenant
            tenant = Tenant(
                name=data["name"],
                display_name=data.get("display_name", data["name"]),
                tier=data.get("tier", TenantTier.TRIAL),
                billing_email=data.get("billing_email"),
                metadata=data.get("metadata", {}),
            )

            # Set trial period
            if tenant.tier == TenantTier.TRIAL:
                from datetime import timedelta

                tenant.trial_ends_at = datetime.utcnow() + timedelta(days=30)

            # Apply tier limits
            tier_limits = self.tier_limits.get(tenant.tier, {})
            tenant.max_users = tier_limits.get("max_users", 10)
            tenant.max_api_calls_per_day = tier_limits.get("max_api_calls", 10000)
            tenant.max_storage_gb = tier_limits.get("max_storage", 10)
            tenant.enabled_features = tier_limits.get("features", [])

            session.add(tenant)
            await session.commit()

            # Cache tenant info
            if self.redis_client:
                await self._cache_tenant(tenant)

            # Create tenant resources
            await self._create_tenant_resources(tenant)

            logger.info(f"Created tenant: {tenant.tenant_id}")

            return tenant.to_dict()

    async def get_tenant(self, tenant_id: str) -> Optional[Dict[str, Any]]:
        """Get tenant by ID."""
        # Check cache first
        if self.redis_client:
            cached = await self._get_cached_tenant(tenant_id)
            if cached:
                return cached

        # Query database
        async with self.session_factory() as session:
            tenant = await session.get(Tenant, tenant_id)

            if not tenant:
                return None

            tenant_dict = tenant.to_dict()

            # Cache result
            if self.redis_client:
                await self._cache_tenant(tenant)

            return tenant_dict

    async def update_tenant(
        self, tenant_id: str, updates: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Update tenant information."""
        async with self.session_factory() as session:
            tenant = await session.get(Tenant, tenant_id)

            if not tenant:
                raise ValueError(f"Tenant {tenant_id} not found")

            # Update fields
            for key, value in updates.items():
                if hasattr(tenant, key):
                    setattr(tenant, key, value)

            tenant.updated_at = datetime.utcnow()

            await session.commit()

            # Update cache
            if self.redis_client:
                await self._cache_tenant(tenant)

            return tenant.to_dict()

    async def delete_tenant(self, tenant_id: str):
        """Delete a tenant (soft delete)."""
        async with self.session_factory() as session:
            tenant = await session.get(Tenant, tenant_id)

            if not tenant:
                raise ValueError(f"Tenant {tenant_id} not found")

            # Soft delete
            tenant.status = TenantStatus.DELETED
            tenant.updated_at = datetime.utcnow()

            await session.commit()

            # Remove from cache
            if self.redis_client:
                await self._remove_cached_tenant(tenant_id)

            # Cleanup tenant resources
            await self._cleanup_tenant_resources(tenant)

    async def list_tenants(
        self, filters: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """List all tenants with optional filters."""
        async with self.session_factory() as session:
            query = session.query(Tenant)

            # Apply filters
            if filters:
                if "status" in filters:
                    query = query.filter(Tenant.status == filters["status"])
                if "tier" in filters:
                    query = query.filter(Tenant.tier == filters["tier"])

            # Exclude deleted tenants by default
            query = query.filter(Tenant.status != TenantStatus.DELETED)

            result = await session.execute(query)
            tenants = result.scalars().all()

            return [tenant.to_dict() for tenant in tenants]

    async def check_tenant_limits(
        self, tenant_id: str, resource: str, amount: int = 1
    ) -> bool:
        """Check if tenant has exceeded resource limits."""
        tenant = await self.get_tenant(tenant_id)

        if not tenant:
            return False

        # Check status
        if tenant["status"] != TenantStatus.ACTIVE:
            if tenant["status"] == TenantStatus.TRIAL:
                # Check trial expiration
                if tenant.get("trial_ends_at"):
                    trial_end = datetime.fromisoformat(tenant["trial_ends_at"])
                    if datetime.utcnow() > trial_end:
                        return False
            else:
                return False

        # Check resource limits
        if resource == "api_calls":
            current_usage = await self._get_api_usage(tenant_id)
            return current_usage + amount <= tenant["limits"]["max_api_calls_per_day"]

        elif resource == "users":
            current_count = await self._get_user_count(tenant_id)
            return current_count + amount <= tenant["limits"]["max_users"]

        elif resource == "storage":
            current_usage = await self._get_storage_usage(tenant_id)
            return (
                current_usage + amount
                <= tenant["limits"]["max_storage_gb"] * 1024 * 1024 * 1024
            )

        return True

    async def record_usage(self, tenant_id: str, resource: str, amount: int = 1):
        """Record resource usage for a tenant."""
        if not self.redis_client:
            return

        # Record in Redis with daily expiration
        today = datetime.utcnow().strftime("%Y-%m-%d")
        key = f"usage:{tenant_id}:{resource}:{today}"

        await self.redis_client.incr(key, amount)
        await self.redis_client.expire(key, 86400 * 2)  # Keep for 2 days

    async def get_tenant_usage(self, tenant_id: str, days: int = 30) -> Dict[str, Any]:
        """Get tenant usage statistics."""
        usage = {
            "tenant_id": tenant_id,
            "period_days": days,
            "api_calls": {},
            "storage": {},
            "users": {},
        }

        if not self.redis_client:
            return usage

        # Get daily API usage
        for i in range(days):
            date = (datetime.utcnow() - timedelta(days=i)).strftime("%Y-%m-%d")

            # API calls
            api_key = f"usage:{tenant_id}:api_calls:{date}"
            api_usage = await self.redis_client.get(api_key)
            if api_usage:
                usage["api_calls"][date] = int(api_usage)

        # Get current counts
        usage["users"]["current"] = await self._get_user_count(tenant_id)
        usage["storage"]["current_bytes"] = await self._get_storage_usage(tenant_id)

        return usage

    def _get_tier_limits(self) -> Dict[str, Dict[str, Any]]:
        """Get limits for each tier."""
        return {
            TenantTier.FREE: {
                "max_users": 5,
                "max_api_calls": 1000,
                "max_storage": 1,  # GB
                "features": ["basic_tools"],
            },
            TenantTier.STARTER: {
                "max_users": 20,
                "max_api_calls": 50000,
                "max_storage": 10,
                "features": ["basic_tools", "api_access", "webhooks"],
            },
            TenantTier.PROFESSIONAL: {
                "max_users": 100,
                "max_api_calls": 500000,
                "max_storage": 100,
                "features": [
                    "basic_tools",
                    "api_access",
                    "webhooks",
                    "advanced_analytics",
                    "custom_workflows",
                ],
            },
            TenantTier.ENTERPRISE: {
                "max_users": -1,  # Unlimited
                "max_api_calls": -1,
                "max_storage": -1,
                "features": ["*"],  # All features
            },
        }

    async def _cache_tenant(self, tenant: Tenant):
        """Cache tenant information."""
        if not self.redis_client:
            return

        import json

        await self.redis_client.set(
            f"tenant:{tenant.tenant_id}",
            json.dumps(tenant.to_dict()),
            ex=3600,  # 1 hour cache
        )

    async def _get_cached_tenant(self, tenant_id: str) -> Optional[Dict[str, Any]]:
        """Get cached tenant information."""
        if not self.redis_client:
            return None

        cached = await self.redis_client.get(f"tenant:{tenant_id}")
        if cached:
            import json

            return json.loads(cached)

        return None

    async def _remove_cached_tenant(self, tenant_id: str):
        """Remove tenant from cache."""
        if not self.redis_client:
            return

        await self.redis_client.delete(f"tenant:{tenant_id}")

    async def _create_tenant_resources(self, tenant: Tenant):
        """Create resources for a new tenant."""
        # Create tenant-specific database schema
        # Create tenant-specific storage
        # Create tenant-specific queues
        # etc.
        logger.info(f"Created resources for tenant: {tenant.tenant_id}")

    async def _cleanup_tenant_resources(self, tenant: Tenant):
        """Cleanup resources for a deleted tenant."""
        # Archive tenant data
        # Remove tenant-specific resources
        # etc.
        logger.info(f"Cleaned up resources for tenant: {tenant.tenant_id}")

    async def _get_api_usage(self, tenant_id: str) -> int:
        """Get current API usage for today."""
        if not self.redis_client:
            return 0

        today = datetime.utcnow().strftime("%Y-%m-%d")
        key = f"usage:{tenant_id}:api_calls:{today}"

        usage = await self.redis_client.get(key)
        return int(usage) if usage else 0

    async def _get_user_count(self, tenant_id: str) -> int:
        """Get current user count for tenant."""
        # In production, query from user table
        return 0

    async def _get_storage_usage(self, tenant_id: str) -> int:
        """Get current storage usage in bytes."""
        # In production, calculate from storage system
        return 0


class TenantContext:
    """Context manager for tenant-specific operations."""

    def __init__(self, tenant_id: str):
        self.tenant_id = tenant_id
        self.previous_tenant = None

    async def __aenter__(self):
        """Enter tenant context."""
        # Store current tenant
        self.previous_tenant = getattr(asyncio.current_task(), "tenant_id", None)

        # Set new tenant
        asyncio.current_task().tenant_id = self.tenant_id

        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Exit tenant context."""
        # Restore previous tenant
        if self.previous_tenant:
            asyncio.current_task().tenant_id = self.previous_tenant
        else:
            delattr(asyncio.current_task(), "tenant_id")
