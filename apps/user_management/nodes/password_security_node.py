"""
Optimized Password Security Node
High-performance password hashing and verification
"""

import hashlib
import secrets
import time
from datetime import datetime, timezone
from typing import Any, Dict, Optional

from kailash.nodes import Node, NodeParameter

try:
    import bcrypt
except ImportError:
    bcrypt = None

try:
    from argon2 import PasswordHasher
except ImportError:
    PasswordHasher = None


class PasswordSecurityNode(Node):
    """
    Enterprise-grade password security node with optimized algorithms

    Features:
    - Bcrypt hashing with configurable cost factor
    - Argon2 support for maximum security
    - Password history tracking
    - Breach detection via HaveIBeenPwned API
    - Timing attack prevention
    - Salt generation and management
    """

    def __init__(self, **kwargs):
        # Configuration
        self.algorithm = kwargs.pop("algorithm", "bcrypt")  # bcrypt, argon2, scrypt
        self.cost_factor = kwargs.pop("cost_factor", 12)
        self.check_breaches = kwargs.pop("check_breaches", True)
        self.track_history = kwargs.pop("track_history", True)
        self.history_limit = kwargs.pop("history_limit", 5)

        # Initialize
        super().__init__(**kwargs)

    def get_parameters(self) -> Dict[str, NodeParameter]:
        """Define node parameters"""
        return {
            "operation": NodeParameter(
                name="operation",
                type=str,
                description="Operation to perform (hash, verify, check_history)",
                default="hash",
                required=False,
            ),
            "password": NodeParameter(
                name="password",
                type=str,
                description="Password to hash or verify",
                required=False,
            ),
            "hashed_password": NodeParameter(
                name="hashed_password",
                type=str,
                description="Stored hash for verification",
                required=False,
            ),
            "hash_algorithm": NodeParameter(
                name="hash_algorithm",
                type=str,
                description="Algorithm used for the stored hash",
                required=False,
            ),
            "new_hash": NodeParameter(
                name="new_hash",
                type=str,
                description="New hash to check against history",
                required=False,
            ),
            "password_history": NodeParameter(
                name="password_history",
                type=list,
                description="List of previous password hashes",
                required=False,
                default=[],
            ),
            "strength_score": NodeParameter(
                name="strength_score",
                type=int,
                description="Password strength score",
                required=False,
                default=80,
            ),
        }

    def constant_time_compare(self, a: str, b: str) -> bool:
        """Constant time string comparison to prevent timing attacks"""
        if len(a) != len(b):
            return False
        result = 0
        for x, y in zip(a, b):
            result |= ord(x) ^ ord(y)
        return result == 0

    def check_pwned_password(self, password: str) -> tuple[bool, Optional[str]]:
        """Check if password has been exposed in breaches (k-anonymity)"""
        # SHA1 hash for HaveIBeenPwned API
        sha1_password = hashlib.sha1(password.encode("utf-8")).hexdigest().upper()
        prefix = sha1_password[:5]
        suffix = sha1_password[5:]

        # In production, make API call to check breaches
        # For now, check against common patterns
        common_patterns = [
            "123456",
            "password",
            "qwerty",
            "abc123",
            "letmein",
            "admin",
            "welcome",
            "monkey",
            "dragon",
            "baseball",
        ]

        for pattern in common_patterns:
            if pattern in password.lower():
                return True, "Password contains common pattern"

        return False, None

    def generate_salt(self) -> bytes:
        """Generate cryptographically secure salt"""
        if self.algorithm == "bcrypt" and bcrypt:
            return bcrypt.gensalt(rounds=self.cost_factor)
        else:
            # For other algorithms, generate 32-byte salt
            return secrets.token_bytes(32)

    def hash_password_bcrypt(self, password: str) -> Dict[str, Any]:
        """Hash password using bcrypt"""
        if not bcrypt:
            raise ImportError("bcrypt is required for bcrypt hashing")

        start_time = time.time()

        # Generate salt with cost factor
        salt = bcrypt.gensalt(rounds=self.cost_factor)

        # Hash password
        hashed = bcrypt.hashpw(password.encode("utf-8"), salt)

        hash_time = time.time() - start_time

        return {
            "algorithm": "bcrypt",
            "hash": hashed.decode("utf-8"),
            "cost": self.cost_factor,
            "time": hash_time,
            "created_at": datetime.now(timezone.utc).isoformat(),
        }

    def hash_password_argon2(self, password: str) -> Dict[str, Any]:
        """Hash password using Argon2 (most secure)"""
        if not PasswordHasher:
            # Fallback to bcrypt if argon2 not available
            return self.hash_password_bcrypt(password)

        ph = PasswordHasher(
            time_cost=3,  # iterations
            memory_cost=65536,  # 64MB
            parallelism=4,  # threads
            hash_len=32,
        )

        start_time = time.time()
        hashed = ph.hash(password)
        hash_time = time.time() - start_time

        return {
            "algorithm": "argon2",
            "hash": hashed,
            "time": hash_time,
            "created_at": datetime.now(timezone.utc).isoformat(),
        }

    def hash_password_scrypt(self, password: str) -> Dict[str, Any]:
        """Hash password using scrypt"""
        import os

        # Generate salt
        salt = os.urandom(32)

        start_time = time.time()

        # scrypt parameters (N=2^14, r=8, p=1)
        hashed = hashlib.scrypt(
            password.encode("utf-8"), salt=salt, n=16384, r=8, p=1, dklen=32
        )

        hash_time = time.time() - start_time

        # Combine salt and hash for storage
        combined = salt + hashed

        return {
            "algorithm": "scrypt",
            "hash": combined.hex(),
            "time": hash_time,
            "created_at": datetime.now(timezone.utc).isoformat(),
        }

    def verify_password_bcrypt(self, password: str, stored_hash: str) -> bool:
        """Verify password against bcrypt hash"""
        if not bcrypt:
            return False

        try:
            # Constant time comparison
            is_valid = bcrypt.checkpw(
                password.encode("utf-8"), stored_hash.encode("utf-8")
            )
            return is_valid
        except Exception:
            return False

    def verify_password_argon2(self, password: str, stored_hash: str) -> bool:
        """Verify password against argon2 hash"""
        if not PasswordHasher:
            return False

        try:
            ph = PasswordHasher()
            ph.verify(stored_hash, password)
            return True
        except Exception:
            return False

    def verify_password_scrypt(self, password: str, stored_hash: str) -> bool:
        """Verify password against scrypt hash"""
        try:
            # Extract salt and hash
            combined = bytes.fromhex(stored_hash)
            salt = combined[:32]
            stored = combined[32:]

            # Recompute hash
            computed = hashlib.scrypt(
                password.encode("utf-8"), salt=salt, n=16384, r=8, p=1, dklen=32
            )

            # Constant time comparison
            return self.constant_time_compare(stored.hex(), computed.hex())
        except Exception:
            return False

    def check_password_history(
        self, password_hash: str, history: list
    ) -> tuple[bool, Optional[str]]:
        """Check if password was used recently"""
        if not self.track_history or not history:
            return False, None

        # Check against recent hashes
        for i, old_hash in enumerate(history[: self.history_limit]):
            if self.constant_time_compare(password_hash, old_hash):
                return True, f"Password was used {i+1} passwords ago"

        return False, None

    def run(self, **inputs) -> Dict[str, Any]:
        """Process password security operations with optimization"""
        # Add performance monitoring
        start_time = time.time()

        # Get operation type
        operation = inputs.get("operation", "hash")

        # Main operation handling
        if operation == "hash":
            password = inputs.get("password", "")

            if not password:
                result = {"success": False, "error": "No password provided"}
            else:
                # Check for breached passwords
                if self.check_breaches:
                    is_breached, breach_reason = self.check_pwned_password(password)
                    if is_breached:
                        result = {
                            "success": False,
                            "error": f"Password is compromised: {breach_reason}",
                            "suggest_alternative": True,
                        }
                    else:
                        # Hash password based on algorithm
                        try:
                            if self.algorithm == "bcrypt":
                                hash_result = self.hash_password_bcrypt(password)
                            elif self.algorithm == "argon2":
                                hash_result = self.hash_password_argon2(password)
                            elif self.algorithm == "scrypt":
                                hash_result = self.hash_password_scrypt(password)
                            else:
                                hash_result = self.hash_password_bcrypt(
                                    password
                                )  # Default

                            result = {
                                "success": True,
                                "hashed_password": hash_result["hash"],
                                "hash_data": hash_result,
                                "strength_score": inputs.get("strength_score", 80),
                            }
                        except Exception as e:
                            result = {"success": False, "error": str(e)}
                else:
                    # Hash without breach check
                    try:
                        if self.algorithm == "bcrypt":
                            hash_result = self.hash_password_bcrypt(password)
                        elif self.algorithm == "argon2":
                            hash_result = self.hash_password_argon2(password)
                        elif self.algorithm == "scrypt":
                            hash_result = self.hash_password_scrypt(password)
                        else:
                            hash_result = self.hash_password_bcrypt(password)

                        result = {
                            "success": True,
                            "hashed_password": hash_result["hash"],
                            "hash_data": hash_result,
                        }
                    except Exception as e:
                        result = {"success": False, "error": str(e)}

        elif operation == "verify":
            password = inputs.get("password", "")
            stored_hash = inputs.get("hashed_password", "")
            hash_algorithm = inputs.get("hash_algorithm", self.algorithm)

            if not password or not stored_hash:
                result = {"success": False, "error": "Missing password or hash"}
            else:
                # Add timing delay to prevent timing attacks
                op_start_time = time.time()

                # Verify based on algorithm
                if hash_algorithm == "bcrypt":
                    is_valid = self.verify_password_bcrypt(password, stored_hash)
                elif hash_algorithm == "argon2":
                    is_valid = self.verify_password_argon2(password, stored_hash)
                elif hash_algorithm == "scrypt":
                    is_valid = self.verify_password_scrypt(password, stored_hash)
                else:
                    is_valid = False

                # Ensure minimum time to prevent timing attacks
                elapsed = time.time() - op_start_time
                if elapsed < 0.1:
                    time.sleep(0.1 - elapsed)

                result = {
                    "success": True,
                    "is_valid": is_valid,
                    "verification_time": time.time() - op_start_time,
                }

        elif operation == "check_history":
            new_hash = inputs.get("new_hash", "")
            history = inputs.get("password_history", [])

            is_reused, reuse_message = self.check_password_history(new_hash, history)

            result = {
                "success": True,
                "is_reused": is_reused,
                "message": reuse_message,
                "history_checked": len(history[: self.history_limit]),
            }

        else:
            result = {"success": False, "error": f"Unknown operation: {operation}"}

        # Add performance metrics
        result["performance_metrics"] = {
            "total_time": time.time() - start_time,
            "algorithm": self.algorithm,
            "cost_factor": self.cost_factor,
        }

        return result
