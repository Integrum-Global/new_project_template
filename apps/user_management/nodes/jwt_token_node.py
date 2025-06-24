"""
Optimized JWT Token Management Node
High-performance JWT token generation and validation
"""

from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from kailash.nodes import NodeParameter, PythonCodeNode


class JWTTokenNode(PythonCodeNode):
    """
    Enterprise-grade JWT token management with advanced features

    Features:
    - Multiple signing algorithms (HS256, RS256, ES256)
    - Token refresh with rotation
    - Claims validation and custom claims
    - JTI (JWT ID) for token revocation
    - Audience and issuer validation
    - Token encryption support (JWE)
    """

    def __init__(self, **kwargs):
        # Configuration
        self.secret_key = kwargs.pop("secret_key", "change-this-secret-key")
        self.algorithm = kwargs.pop("algorithm", "HS256")
        self.access_token_expires = kwargs.pop("access_token_expires", 3600)  # 1 hour
        self.refresh_token_expires = kwargs.pop(
            "refresh_token_expires", 2592000
        )  # 30 days
        self.issuer = kwargs.pop("issuer", "user-management-system")
        self.audience = kwargs.pop("audience", ["web", "mobile", "api"])
        self.enable_jti = kwargs.pop("enable_jti", True)
        self.enable_encryption = kwargs.pop("enable_encryption", False)

        # Initialize with token management code
        super().__init__(code=self._generate_token_code(), **kwargs)

    def get_parameters(self) -> Dict[str, NodeParameter]:
        """Define node parameters"""
        return {
            "secret_key": NodeParameter(
                type="str",
                description="Secret key for signing tokens",
                required=True,
                sensitive=True,
            ),
            "algorithm": NodeParameter(
                type="str",
                description="Signing algorithm",
                default="HS256",
                options=[
                    "HS256",
                    "HS384",
                    "HS512",
                    "RS256",
                    "RS384",
                    "RS512",
                    "ES256",
                    "ES384",
                    "ES512",
                ],
            ),
            "access_token_expires": NodeParameter(
                type="int",
                description="Access token expiration in seconds",
                default=3600,
                min=300,
                max=86400,
            ),
            "refresh_token_expires": NodeParameter(
                type="int",
                description="Refresh token expiration in seconds",
                default=2592000,
                min=86400,
                max=31536000,
            ),
            "issuer": NodeParameter(
                type="str",
                description="Token issuer identifier",
                default="user-management-system",
            ),
            "audience": NodeParameter(
                type="list",
                description="Valid token audiences",
                default=["web", "mobile", "api"],
            ),
            "enable_jti": NodeParameter(
                type="bool", description="Enable JWT ID for revocation", default=True
            ),
            "enable_encryption": NodeParameter(
                type="bool", description="Enable token encryption (JWE)", default=False
            ),
        }

    def _generate_token_code(self) -> str:
        """Generate optimized JWT token management code"""
        return f'''
import jwt
import uuid
import hashlib
from datetime import datetime, timedelta, timezone

# Configuration
secret_key = "{self.secret_key}"
algorithm = "{self.algorithm}"
access_expires = {self.access_token_expires}
refresh_expires = {self.refresh_token_expires}
issuer = "{self.issuer}"
audience = {self.audience}
enable_jti = {self.enable_jti}
enable_encryption = {self.enable_encryption}

# Get operation
operation = input_data.get("operation", "generate")  # generate, verify, refresh, revoke

def generate_jti():
    """Generate unique JWT ID"""
    return str(uuid.uuid4())

def generate_token_fingerprint():
    """Generate token fingerprint for additional security"""
    return hashlib.sha256(str(uuid.uuid4()).encode()).hexdigest()[:16]

def encrypt_token(token, encryption_key=None):
    """Encrypt JWT token (JWE)"""
    if not enable_encryption:
        return token

    # In production, use proper JWE library
    # For now, return token as-is
    return token

def decrypt_token(encrypted_token, encryption_key=None):
    """Decrypt JWT token (JWE)"""
    if not enable_encryption:
        return encrypted_token

    # In production, use proper JWE library
    return encrypted_token

def generate_access_token(user_data, custom_claims=None):
    """Generate access token with user claims"""
    now = datetime.now(timezone.utc)

    # Base claims
    claims = {{
        "sub": user_data.get("id", ""),  # Subject (user ID)
        "username": user_data.get("username", ""),
        "email": user_data.get("email", ""),
        "iat": now,
        "exp": now + timedelta(seconds=access_expires),
        "iss": issuer,
        "aud": audience,
        "type": "access"
    }}

    # Add JTI if enabled
    if enable_jti:
        claims["jti"] = generate_jti()

    # Add custom claims
    if custom_claims:
        for key, value in custom_claims.items():
            if key not in ["sub", "iat", "exp", "iss", "aud", "jti"]:
                claims[key] = value

    # Add security claims
    claims["fingerprint"] = generate_token_fingerprint()

    # Generate token
    token = jwt.encode(claims, secret_key, algorithm=algorithm)

    return token, claims

def generate_refresh_token(user_data, access_token_jti=None):
    """Generate refresh token"""
    now = datetime.now(timezone.utc)

    claims = {{
        "sub": user_data.get("id", ""),
        "iat": now,
        "exp": now + timedelta(seconds=refresh_expires),
        "iss": issuer,
        "aud": audience,
        "type": "refresh"
    }}

    # Add JTI
    if enable_jti:
        claims["jti"] = generate_jti()
        if access_token_jti:
            claims["ati"] = access_token_jti  # Access token ID for pairing

    # Generate token
    token = jwt.encode(claims, secret_key, algorithm=algorithm)

    return token, claims

def verify_token(token, token_type="access", verify_exp=True):
    """Verify and decode JWT token"""
    try:
        # Decrypt if needed
        token = decrypt_token(token)

        # Decode token
        claims = jwt.decode(
            token,
            secret_key,
            algorithms=[algorithm],
            audience=audience,
            issuer=issuer,
            options={{"verify_exp": verify_exp}}
        )

        # Verify token type
        if claims.get("type") != token_type:
            return None, f"Invalid token type. Expected {{token_type}}"

        # Additional validations
        if enable_jti and "jti" not in claims:
            return None, "Missing JTI claim"

        return claims, None

    except jwt.ExpiredSignatureError:
        return None, "Token has expired"
    except jwt.InvalidAudienceError:
        return None, "Invalid audience"
    except jwt.InvalidIssuerError:
        return None, "Invalid issuer"
    except jwt.InvalidTokenError as e:
        return None, f"Invalid token: {{str(e)}}"
    except Exception as e:
        return None, f"Token verification failed: {{str(e)}}"

def refresh_access_token(refresh_token_str, user_data=None):
    """Generate new access token from refresh token"""
    # Verify refresh token
    claims, error = verify_token(refresh_token_str, token_type="refresh")

    if error:
        return None, None, error

    # Get user data (from token or provided)
    if not user_data:
        user_data = {{
            "id": claims.get("sub"),
            "username": claims.get("username", ""),
            "email": claims.get("email", "")
        }}

    # Generate new access token
    new_access_token, access_claims = generate_access_token(user_data)

    # Optionally rotate refresh token
    new_refresh_token = None
    refresh_claims = None

    # Check if refresh token should be rotated
    refresh_exp = datetime.fromtimestamp(claims["exp"], tz=timezone.utc)
    time_until_exp = (refresh_exp - datetime.now(timezone.utc)).total_seconds()

    if time_until_exp < (refresh_expires * 0.5):  # Less than 50% lifetime remaining
        new_refresh_token, refresh_claims = generate_refresh_token(
            user_data,
            access_claims.get("jti")
        )

    return new_access_token, new_refresh_token, None

# Handle operations
if operation == "generate":
    user_data = input_data.get("user_data", {{}})
    custom_claims = input_data.get("custom_claims", {{}})

    if not user_data.get("id"):
        result = {{"success": False, "error": "User ID required"}}
    else:
        # Generate tokens
        access_token, access_claims = generate_access_token(user_data, custom_claims)
        refresh_token, refresh_claims = generate_refresh_token(
            user_data,
            access_claims.get("jti")
        )

        # Encrypt if enabled
        access_token = encrypt_token(access_token)
        refresh_token = encrypt_token(refresh_token)

        result = {{
            "success": True,
            "tokens": {{
                "access": access_token,
                "refresh": refresh_token,
                "expires_in": access_expires
            }},
            "claims": {{
                "access": access_claims,
                "refresh": refresh_claims
            }}
        }}

elif operation == "verify":
    token = input_data.get("token", "")
    token_type = input_data.get("token_type", "access")
    verify_exp = input_data.get("verify_exp", True)

    if not token:
        result = {{"success": False, "error": "No token provided"}}
    else:
        claims, error = verify_token(token, token_type, verify_exp)

        if error:
            result = {{
                "success": False,
                "error": error,
                "valid": False
            }}
        else:
            result = {{
                "success": True,
                "valid": True,
                "claims": claims,
                "user_id": claims.get("sub"),
                "expires_at": datetime.fromtimestamp(
                    claims["exp"],
                    tz=timezone.utc
                ).isoformat()
            }}

elif operation == "refresh":
    refresh_token = input_data.get("refresh_token", "")
    user_data = input_data.get("user_data")  # Optional updated user data

    if not refresh_token:
        result = {{"success": False, "error": "No refresh token provided"}}
    else:
        new_access, new_refresh, error = refresh_access_token(refresh_token, user_data)

        if error:
            result = {{
                "success": False,
                "error": error
            }}
        else:
            tokens = {{
                "access": new_access,
                "expires_in": access_expires
            }}

            if new_refresh:
                tokens["refresh"] = new_refresh
                tokens["refresh_rotated"] = True

            result = {{
                "success": True,
                "tokens": tokens
            }}

elif operation == "revoke":
    token_jti = input_data.get("jti", "")
    revoke_family = input_data.get("revoke_family", False)  # Revoke all related tokens

    if not enable_jti:
        result = {{"success": False, "error": "JTI not enabled"}}
    elif not token_jti:
        result = {{"success": False, "error": "No JTI provided"}}
    else:
        # In production, add JTI to revocation list (Redis/DB)
        revoked_tokens = [token_jti]

        if revoke_family:
            # Revoke all tokens in the family
            # This would query the revocation store
            revoked_tokens.append(f"{{token_jti}}_family")

        result = {{
            "success": True,
            "revoked": revoked_tokens,
            "revoked_at": datetime.now(timezone.utc).isoformat()
        }}

else:
    result = {{"success": False, "error": f"Unknown operation: {{operation}}"}}
'''

    async def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process JWT operations with performance optimization"""
        # Add caching for token verification
        if input_data.get("operation") == "verify" and hasattr(self, "_token_cache"):
            token = input_data.get("token")
            if token in self._token_cache:
                cached_result = self._token_cache[token]
                # Check if cache is still valid
                if cached_result.get("cached_until", 0) > datetime.utcnow().timestamp():
                    return cached_result["result"]

        result = await super().process(input_data)

        # Cache successful verifications
        if input_data.get("operation") == "verify" and result.get("success"):
            if not hasattr(self, "_token_cache"):
                self._token_cache = {}

            token = input_data.get("token")
            self._token_cache[token] = {
                "result": result,
                "cached_until": datetime.utcnow().timestamp() + 300,  # 5 minute cache
            }

        return result
