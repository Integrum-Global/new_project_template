"""Authentication module for Enterprise Gateway."""

from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

import jwt
import redis.asyncio as redis
import structlog
from authlib.integrations.starlette_client import OAuth
from fastapi import Depends, HTTPException, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer, OAuth2PasswordBearer
from passlib.context import CryptContext
from pydantic import BaseModel

logger = structlog.get_logger(__name__)

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Bearer token
bearer_scheme = HTTPBearer()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/token")

# JWT configuration
JWT_SECRET = "your-secret-key"  # In production, use environment variable
JWT_ALGORITHM = "HS256"
JWT_EXPIRATION_HOURS = 24


class AuthenticationMiddleware:
    """Handles authentication for the gateway."""

    def __init__(self, redis_url: Optional[str] = None):
        self.redis_client = None
        if redis_url:
            self.redis_client = redis.from_url(redis_url)

        # OAuth client for external providers
        self.oauth = OAuth()

        # Supported authentication methods
        self.auth_methods = {
            "bearer": self.authenticate_bearer,
            "api_key": self.authenticate_api_key,
            "oauth2": self.authenticate_oauth2,
            "mtls": self.authenticate_mtls,
        }

    async def authenticate(self, request: Request) -> Dict[str, Any]:
        """Authenticate the request using appropriate method."""
        # Try different authentication methods

        # 1. Bearer token
        auth_header = request.headers.get("Authorization")
        if auth_header and auth_header.startswith("Bearer "):
            return await self.authenticate_bearer(auth_header)

        # 2. API Key
        api_key = request.headers.get("X-API-Key")
        if api_key:
            return await self.authenticate_api_key(api_key)

        # 3. OAuth2
        if "oauth_token" in request.query_params:
            return await self.authenticate_oauth2(request.query_params["oauth_token"])

        # 4. mTLS (mutual TLS)
        if hasattr(request, "client") and request.client:
            return await self.authenticate_mtls(request)

        raise HTTPException(status_code=401, detail="No valid authentication provided")

    async def authenticate_bearer(self, auth_header: str) -> Dict[str, Any]:
        """Authenticate using bearer token."""
        try:
            token = auth_header.split(" ")[1]

            # Check if token is blacklisted
            if self.redis_client:
                is_blacklisted = await self.redis_client.get(f"blacklist:{token}")
                if is_blacklisted:
                    raise HTTPException(
                        status_code=401, detail="Token has been revoked"
                    )

            # Decode JWT
            payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])

            # Check expiration
            exp = payload.get("exp")
            if exp and datetime.fromtimestamp(exp) < datetime.utcnow():
                raise HTTPException(status_code=401, detail="Token has expired")

            return {
                "user_id": payload.get("sub"),
                "tenant_id": payload.get("tenant_id"),
                "roles": payload.get("roles", []),
                "permissions": payload.get("permissions", []),
                "auth_method": "bearer",
            }

        except jwt.InvalidTokenError as e:
            logger.error(f"Invalid JWT token: {e}")
            raise HTTPException(status_code=401, detail="Invalid token")

    async def authenticate_api_key(self, api_key: str) -> Dict[str, Any]:
        """Authenticate using API key."""
        # In production, look up API key in database
        # This is a simplified example

        if self.redis_client:
            key_data = await self.redis_client.get(f"api_key:{api_key}")
            if key_data:
                import json

                user_data = json.loads(key_data)

                # Check if key is active
                if not user_data.get("active", True):
                    raise HTTPException(status_code=401, detail="API key is inactive")

                # Check rate limits
                await self._check_rate_limit(api_key)

                return {
                    "user_id": user_data.get("user_id"),
                    "tenant_id": user_data.get("tenant_id"),
                    "roles": user_data.get("roles", []),
                    "permissions": user_data.get("permissions", []),
                    "auth_method": "api_key",
                }

        raise HTTPException(status_code=401, detail="Invalid API key")

    async def authenticate_oauth2(self, oauth_token: str) -> Dict[str, Any]:
        """Authenticate using OAuth2 token."""
        # Validate OAuth2 token with provider
        # This is a simplified example

        # In production, validate with OAuth2 provider
        return {
            "user_id": "oauth_user",
            "tenant_id": "default",
            "roles": ["user"],
            "permissions": ["read"],
            "auth_method": "oauth2",
        }

    async def authenticate_mtls(self, request: Request) -> Dict[str, Any]:
        """Authenticate using mutual TLS."""
        # Extract client certificate information
        # This depends on your reverse proxy configuration

        client_cert = request.headers.get("X-SSL-Client-Cert")
        if not client_cert:
            raise HTTPException(status_code=401, detail="Client certificate required")

        # Validate certificate
        # In production, implement proper certificate validation

        return {
            "user_id": "mtls_user",
            "tenant_id": "default",
            "roles": ["service"],
            "permissions": ["*"],
            "auth_method": "mtls",
        }

    async def _check_rate_limit(self, key: str):
        """Check rate limits for API key."""
        if not self.redis_client:
            return

        # Simple rate limiting
        rate_key = f"rate_limit:{key}"
        current = await self.redis_client.incr(rate_key)

        if current == 1:
            await self.redis_client.expire(rate_key, 60)  # 1 minute window

        if current > 100:  # 100 requests per minute
            raise HTTPException(status_code=429, detail="Rate limit exceeded")


class TokenManager:
    """Manages JWT tokens."""

    @staticmethod
    def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
        """Create a new access token."""
        to_encode = data.copy()

        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(hours=JWT_EXPIRATION_HOURS)

        to_encode.update({"exp": expire})
        encoded_jwt = jwt.encode(to_encode, JWT_SECRET, algorithm=JWT_ALGORITHM)

        return encoded_jwt

    @staticmethod
    def create_refresh_token(user_id: str) -> str:
        """Create a refresh token."""
        data = {
            "sub": user_id,
            "type": "refresh",
            "exp": datetime.utcnow() + timedelta(days=30),
        }

        return jwt.encode(data, JWT_SECRET, algorithm=JWT_ALGORITHM)

    @staticmethod
    async def revoke_token(token: str, redis_client: redis.Redis):
        """Revoke a token by adding it to blacklist."""
        if redis_client:
            # Add to blacklist with expiration
            await redis_client.set(f"blacklist:{token}", "1", ex=86400 * 7)  # 7 days


# Dependency for getting current user
async def get_current_user(
    request: Request, credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme)
) -> Dict[str, Any]:
    """Get the current authenticated user."""
    auth_middleware = AuthenticationMiddleware()

    try:
        user = await auth_middleware.authenticate(request)
        return user
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Authentication error: {e}")
        raise HTTPException(status_code=401, detail="Authentication failed")


# Models for authentication endpoints
class LoginRequest(BaseModel):
    username: str
    password: str
    tenant_id: Optional[str] = None


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int = JWT_EXPIRATION_HOURS * 3600


class UserCreate(BaseModel):
    username: str
    password: str
    email: str
    tenant_id: Optional[str] = None
    roles: List[str] = ["user"]


class User:
    """User model."""

    def __init__(
        self,
        user_id: str,
        username: str,
        email: str,
        password_hash: str,
        tenant_id: Optional[str] = None,
        roles: List[str] = None,
    ):
        self.user_id = user_id
        self.username = username
        self.email = email
        self.password_hash = password_hash
        self.tenant_id = tenant_id
        self.roles = roles or ["user"]
        self.created_at = datetime.utcnow()
        self.is_active = True

    def verify_password(self, password: str) -> bool:
        """Verify password against hash."""
        return pwd_context.verify(password, self.password_hash)

    @staticmethod
    def hash_password(password: str) -> str:
        """Hash a password."""
        return pwd_context.hash(password)


# Service account authentication
class ServiceAccount:
    """Service account for machine-to-machine authentication."""

    def __init__(self, account_id: str, name: str, tenant_id: Optional[str] = None):
        self.account_id = account_id
        self.name = name
        self.tenant_id = tenant_id
        self.api_keys = []
        self.created_at = datetime.utcnow()
        self.is_active = True

    def generate_api_key(self) -> str:
        """Generate a new API key."""
        import secrets

        api_key = f"sk_{secrets.token_urlsafe(32)}"
        self.api_keys.append(
            {
                "key": api_key,
                "created_at": datetime.utcnow(),
                "last_used": None,
                "is_active": True,
            }
        )
        return api_key


# OAuth2 provider configuration
class OAuth2Provider:
    """OAuth2 provider configuration."""

    def __init__(
        self,
        name: str,
        client_id: str,
        client_secret: str,
        authorize_url: str,
        token_url: str,
        userinfo_url: str,
    ):
        self.name = name
        self.client_id = client_id
        self.client_secret = client_secret
        self.authorize_url = authorize_url
        self.token_url = token_url
        self.userinfo_url = userinfo_url

    def to_authlib_config(self) -> Dict[str, Any]:
        """Convert to Authlib configuration."""
        return {
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "authorize_url": self.authorize_url,
            "access_token_url": self.token_url,
            "userinfo_url": self.userinfo_url,
            "client_kwargs": {"scope": "openid email profile"},
        }
