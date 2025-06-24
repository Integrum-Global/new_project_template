"""
Performance and Load Testing for User Management System
Tests system performance under various load conditions
"""

import asyncio
import gc
import random
import statistics
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timedelta
from typing import Any, Dict, List, Tuple

import psutil
import pytest

from apps.user_management.config.settings import UserManagementConfig
from apps.user_management.main import UserManagementApp
from kailash.runtime.local import LocalRuntime


class TestPerformanceLoad:
    """Comprehensive performance and load testing"""

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

    def measure_performance(self, operation_name: str):
        """Decorator to measure operation performance"""

        def decorator(func):
            async def wrapper(*args, **kwargs):
                start_time = time.time()
                start_memory = psutil.Process().memory_info().rss / 1024 / 1024  # MB

                result = await func(*args, **kwargs)

                end_time = time.time()
                end_memory = psutil.Process().memory_info().rss / 1024 / 1024  # MB

                duration = end_time - start_time
                memory_used = end_memory - start_memory

                return {
                    "result": result,
                    "performance": {
                        "operation": operation_name,
                        "duration": duration,
                        "memory_used": memory_used,
                        "timestamp": datetime.utcnow().isoformat(),
                    },
                }

            return wrapper

        return decorator

    @pytest.mark.asyncio
    async def test_user_registration_performance(self, app, runtime):
        """Test performance of user registration under load"""

        reg_workflow = app.user_api.create_user_registration_workflow()

        # Test single operation performance
        @self.measure_performance("single_registration")
        async def single_registration():
            return await runtime.execute_async(
                reg_workflow,
                {
                    "email": "perf_single@example.com",
                    "username": "perf_single",
                    "password": "PerfPass123!",
                },
            )

        single_result = await single_registration()
        single_perf = single_result["performance"]

        # Should complete in under 50ms (target from Phase 1)
        assert single_perf["duration"] < 0.05

        # Test concurrent registrations
        async def register_user(index: int):
            start = time.time()
            result = await runtime.execute_async(
                reg_workflow,
                {
                    "email": f"perf{index}@example.com",
                    "username": f"perfuser{index}",
                    "password": "PerfPass123!",
                },
            )
            return time.time() - start, result.get("success", False)

        # Test with increasing concurrency levels
        concurrency_levels = [10, 50, 100, 200]
        performance_results = []

        for level in concurrency_levels:
            gc.collect()  # Clean up before test

            start_time = time.time()
            tasks = [register_user(i + level * 1000) for i in range(level)]
            results = await asyncio.gather(*tasks)
            total_time = time.time() - start_time

            durations = [r[0] for r in results]
            successes = sum(1 for r in results if r[1])

            perf_data = {
                "concurrency": level,
                "total_time": total_time,
                "throughput": successes / total_time,
                "success_rate": successes / level,
                "avg_duration": statistics.mean(durations),
                "p95_duration": sorted(durations)[int(0.95 * len(durations))],
                "p99_duration": sorted(durations)[int(0.99 * len(durations))],
            }

            performance_results.append(perf_data)

            # Performance assertions
            assert perf_data["success_rate"] >= 0.95  # 95% success rate
            assert perf_data["avg_duration"] < 0.1  # Under 100ms average
            assert perf_data["p99_duration"] < 0.5  # Under 500ms for 99th percentile

        # Verify throughput scales appropriately
        for i in range(1, len(performance_results)):
            prev = performance_results[i - 1]
            curr = performance_results[i]

            # Throughput should scale sub-linearly but positively
            assert curr["throughput"] > prev["throughput"] * 0.7

    @pytest.mark.asyncio
    async def test_authentication_performance(self, app, runtime):
        """Test login and session management performance"""

        # Create test users
        reg_workflow = app.user_api.create_user_registration_workflow()
        test_users = []

        for i in range(100):
            result = await runtime.execute_async(
                reg_workflow,
                {
                    "email": f"authperf{i}@example.com",
                    "username": f"authperf{i}",
                    "password": "AuthPerf123!",
                },
            )
            if result.get("success"):
                test_users.append(
                    {"email": f"authperf{i}@example.com", "password": "AuthPerf123!"}
                )

        # Test login performance
        login_workflow = app.user_api.create_login_workflow()

        async def perform_login(user_data):
            start = time.time()
            result = await runtime.execute_async(login_workflow, user_data)
            return time.time() - start, result.get("success", False)

        # Sequential logins
        sequential_start = time.time()
        sequential_durations = []

        for user in test_users[:20]:
            duration, success = await perform_login(user)
            sequential_durations.append(duration)

        sequential_total = time.time() - sequential_start

        # Concurrent logins
        concurrent_start = time.time()
        tasks = [perform_login(user) for user in test_users[:20]]
        concurrent_results = await asyncio.gather(*tasks)
        concurrent_total = time.time() - concurrent_start

        concurrent_durations = [r[0] for r in concurrent_results]

        # Performance assertions
        assert statistics.mean(sequential_durations) < 0.03  # Under 30ms average
        assert (
            statistics.mean(concurrent_durations) < 0.05
        )  # Under 50ms with concurrency
        assert (
            concurrent_total < sequential_total * 0.5
        )  # Concurrent is at least 2x faster

        # Test session validation performance
        session_workflow = app.auth_workflows.create_session_management_workflow()

        # Get a valid token
        login_result = await runtime.execute_async(login_workflow, test_users[0])

        if login_result.get("success"):
            token = login_result["tokens"]["access"]

            # Test repeated session validations (simulating API requests)
            validation_times = []

            for _ in range(100):
                start = time.time()
                await runtime.execute_async(session_workflow, {"access_token": token})
                validation_times.append(time.time() - start)

            # Session validation should be very fast (cached)
            assert statistics.mean(validation_times) < 0.002  # Under 2ms average
            assert max(validation_times) < 0.01  # No outliers over 10ms

    @pytest.mark.asyncio
    async def test_permission_check_performance(self, app, runtime):
        """Test permission checking performance with caching"""

        # Create test setup with roles and permissions
        role_workflow = app.role_api.create_role_management_workflow()

        # Create complex role hierarchy
        roles = [
            {"name": "super_admin", "permissions": ["*"]},
            {"name": "admin", "permissions": ["users:*", "roles:*", "audit:*"]},
            {
                "name": "manager",
                "permissions": ["users:read", "users:update", "reports:*"],
            },
            {"name": "employee", "permissions": ["profile:*", "reports:read"]},
        ]

        for role_data in roles:
            await runtime.execute_async(
                role_workflow,
                {
                    "user_id": "system",
                    "action": "create",
                    "operation": "create_role",
                    "role_data": role_data,
                },
            )

        # Create test user with multiple roles
        reg_workflow = app.user_api.create_user_registration_workflow()
        user_result = await runtime.execute_async(
            reg_workflow,
            {
                "email": "permtest@example.com",
                "username": "permtest",
                "password": "PermTest123!",
            },
        )

        test_user_id = user_result["user"]["id"]

        # Assign roles
        for role in ["employee", "manager"]:
            await runtime.execute_async(
                role_workflow,
                {
                    "user_id": "system",
                    "action": "manage",
                    "operation": "assign_role_to_user",
                    "data": {"user_id": test_user_id, "role_name": role},
                },
            )

        # Test permission check performance
        perm_node = runtime.create_node(
            "PermissionCheckNode", app.config.NODE_CONFIGS["PermissionCheckNode"]
        )

        # Different permission check scenarios
        test_cases = [
            ("users", "read"),  # Should be allowed (manager role)
            ("users", "delete"),  # Should be denied
            ("reports", "write"),  # Should be allowed (manager role)
            ("admin", "access"),  # Should be denied
            ("profile", "update"),  # Should be allowed (employee role)
        ]

        # Cold cache performance
        cold_cache_times = []

        for resource, action in test_cases:
            start = time.time()
            result = await runtime.execute_node_async(
                perm_node,
                {"user_id": test_user_id, "resource": resource, "action": action},
            )
            cold_cache_times.append(time.time() - start)

        # Warm cache performance (repeat same checks)
        warm_cache_times = []

        for resource, action in test_cases:
            start = time.time()
            result = await runtime.execute_node_async(
                perm_node,
                {"user_id": test_user_id, "resource": resource, "action": action},
            )
            warm_cache_times.append(time.time() - start)

        # Assert performance targets
        assert statistics.mean(cold_cache_times) < 0.01  # Under 10ms cold
        assert statistics.mean(warm_cache_times) < 0.002  # Under 2ms warm
        assert (
            statistics.mean(warm_cache_times) < statistics.mean(cold_cache_times) * 0.3
        )  # 70% improvement

        # Test concurrent permission checks
        concurrent_checks = []

        async def check_permission(index):
            resource, action = test_cases[index % len(test_cases)]
            start = time.time()
            result = await runtime.execute_node_async(
                perm_node,
                {"user_id": test_user_id, "resource": resource, "action": action},
            )
            return time.time() - start

        # 1000 concurrent permission checks
        tasks = [check_permission(i) for i in range(1000)]
        check_times = await asyncio.gather(*tasks)

        # Should maintain performance under load
        assert statistics.mean(check_times) < 0.005  # Under 5ms average
        assert sorted(check_times)[990] < 0.02  # 99th percentile under 20ms

    @pytest.mark.asyncio
    async def test_search_performance(self, app, runtime):
        """Test search and filtering performance with large datasets"""

        # Create large dataset
        bulk_workflow = app.bulk_api.create_bulk_import_workflow()

        # Generate test data
        departments = ["sales", "marketing", "engineering", "hr", "finance"]
        statuses = ["active", "inactive", "pending"]

        batch_size = 100
        total_users = 1000

        for batch in range(0, total_users, batch_size):
            users_data = []
            for i in range(batch_size):
                user_idx = batch + i
                users_data.append(
                    {
                        "email": f"search{user_idx}@example.com",
                        "username": f"searchuser{user_idx}",
                        "first_name": f"First{user_idx}",
                        "last_name": f"Last{user_idx}",
                        "department": random.choice(departments),
                        "status": random.choice(statuses),
                        "created_at": (
                            datetime.utcnow() - timedelta(days=random.randint(0, 365))
                        ).isoformat(),
                    }
                )

            await runtime.execute_async(
                bulk_workflow, {"admin_id": "system", "users": users_data}
            )

        # Test search performance
        search_workflow = app.search_api.create_user_search_workflow()

        # Different search scenarios
        search_tests = [
            # Simple text search
            {"query": "search", "limit": 20},
            # Department filter
            {"department": "engineering", "limit": 50},
            # Status filter with sorting
            {
                "status": "active",
                "sort_by": "created_at",
                "sort_order": "desc",
                "limit": 100,
            },
            # Complex query
            {"query": "First", "department": "sales", "status": "active", "limit": 20},
            # Date range
            {
                "created_after": (datetime.utcnow() - timedelta(days=30)).isoformat(),
                "limit": 50,
            },
        ]

        search_performance = []

        for filters in search_tests:
            start = time.time()
            result = await runtime.execute_async(
                search_workflow, {"user_id": "system", "filters": filters}
            )
            duration = time.time() - start

            search_performance.append(
                {
                    "filters": filters,
                    "duration": duration,
                    "result_count": len(result.get("data", [])),
                    "total_matches": result.get("pagination", {}).get("total", 0),
                }
            )

            # Performance assertions
            assert duration < 0.1  # Under 100ms for any search
            assert result.get("success") is True

        # Test pagination performance
        # Large result set with pagination
        page_times = []

        for offset in range(0, 200, 20):
            start = time.time()
            result = await runtime.execute_async(
                search_workflow,
                {
                    "user_id": "system",
                    "filters": {"status": "active", "limit": 20, "offset": offset},
                },
            )
            page_times.append(time.time() - start)

        # Pagination should be consistent
        assert max(page_times) < min(page_times) * 2  # No huge variations
        assert statistics.mean(page_times) < 0.05  # Under 50ms average

    @pytest.mark.asyncio
    async def test_bulk_operations_performance(self, app, runtime):
        """Test performance of bulk operations"""

        # Test bulk import performance
        import_workflow = app.bulk_api.create_bulk_import_workflow()

        bulk_sizes = [10, 50, 100, 500]
        import_performance = []

        for size in bulk_sizes:
            users_data = []
            for i in range(size):
                users_data.append(
                    {
                        "email": f"bulk{size}_{i}@example.com",
                        "username": f"bulk{size}_{i}",
                        "first_name": f"Bulk{i}",
                        "last_name": "User",
                    }
                )

            gc.collect()
            start = time.time()
            result = await runtime.execute_async(
                import_workflow, {"admin_id": "system", "users": users_data}
            )
            duration = time.time() - start

            import_performance.append(
                {
                    "size": size,
                    "duration": duration,
                    "throughput": size / duration,
                    "per_user_time": duration / size,
                    "success_count": result.get("summary", {}).get("successful", 0),
                }
            )

            # Performance assertions
            assert result.get("summary", {}).get("successful") >= size * 0.95
            assert duration < size * 0.01  # Less than 10ms per user

        # Verify scaling efficiency
        for i in range(1, len(import_performance)):
            prev = import_performance[i - 1]
            curr = import_performance[i]

            # Per-user time should decrease with larger batches
            assert curr["per_user_time"] <= prev["per_user_time"] * 1.1

        # Test bulk update performance
        update_workflow = app.bulk_api.create_bulk_update_workflow()

        # Get user IDs for update
        search_workflow = app.search_api.create_user_search_workflow()
        search_result = await runtime.execute_async(
            search_workflow,
            {"user_id": "system", "filters": {"query": "bulk", "limit": 200}},
        )

        user_ids = [u["id"] for u in search_result.get("data", [])]

        # Test different bulk update sizes
        update_sizes = [10, 50, 100]
        update_performance = []

        for size in update_sizes:
            if len(user_ids) >= size:
                start = time.time()
                result = await runtime.execute_async(
                    update_workflow,
                    {
                        "user_id": "system",
                        "updates": [
                            {
                                "user_ids": user_ids[:size],
                                "changes": {
                                    "status": "updated",
                                    "attributes": {"bulk_updated": True},
                                },
                            }
                        ],
                    },
                )
                duration = time.time() - start

                update_performance.append(
                    {
                        "size": size,
                        "duration": duration,
                        "per_user_time": duration / size,
                    }
                )

                # Should scale well
                assert duration < size * 0.005  # Less than 5ms per user

    @pytest.mark.asyncio
    async def test_memory_usage_under_load(self, app, runtime):
        """Test memory usage patterns under sustained load"""

        initial_memory = psutil.Process().memory_info().rss / 1024 / 1024  # MB

        # Sustained load test
        async def continuous_operations(duration_seconds: int):
            """Run continuous operations for specified duration"""
            end_time = time.time() + duration_seconds
            operations_count = 0
            memory_samples = []

            workflows = [
                app.user_api.create_user_registration_workflow(),
                app.user_api.create_login_workflow(),
                app.search_api.create_user_search_workflow(),
            ]

            while time.time() < end_time:
                # Random operation
                workflow = random.choice(workflows)

                if workflow == workflows[0]:  # Registration
                    data = {
                        "email": f"mem{operations_count}@example.com",
                        "username": f"memuser{operations_count}",
                        "password": "MemTest123!",
                    }
                elif workflow == workflows[1]:  # Login
                    data = {"email": "memtest@example.com", "password": "MemTest123!"}
                else:  # Search
                    data = {
                        "user_id": "system",
                        "filters": {"query": "mem", "limit": 10},
                    }

                await runtime.execute_async(workflow, data)
                operations_count += 1

                # Sample memory every 10 operations
                if operations_count % 10 == 0:
                    current_memory = psutil.Process().memory_info().rss / 1024 / 1024
                    memory_samples.append(current_memory)

                # Small delay to prevent overwhelming
                await asyncio.sleep(0.01)

            return operations_count, memory_samples

        # Run for 30 seconds
        ops_count, memory_samples = await continuous_operations(30)

        final_memory = psutil.Process().memory_info().rss / 1024 / 1024
        memory_growth = final_memory - initial_memory

        # Analyze memory pattern
        avg_memory = statistics.mean(memory_samples)
        max_memory = max(memory_samples)
        memory_variance = (
            statistics.variance(memory_samples) if len(memory_samples) > 1 else 0
        )

        # Memory assertions
        assert memory_growth < 100  # Less than 100MB growth
        assert max_memory < initial_memory + 150  # Peak within 150MB
        assert memory_variance < 1000  # Stable memory usage (low variance)

        # Force garbage collection and check recovery
        gc.collect()
        await asyncio.sleep(1)

        recovered_memory = psutil.Process().memory_info().rss / 1024 / 1024
        recovery_amount = final_memory - recovered_memory

        # Should recover significant memory
        assert recovery_amount > memory_growth * 0.3  # Recover at least 30%

    @pytest.mark.asyncio
    async def test_database_connection_pooling(self, app, runtime):
        """Test database connection pool performance"""

        # Test connection pool under concurrent load
        user_node = runtime.create_node(
            "UserManagementNode", app.config.NODE_CONFIGS["UserManagementNode"]
        )

        async def db_operation(index):
            """Perform a database operation"""
            start = time.time()
            try:
                result = await runtime.execute_node_async(
                    user_node, {"operation": "list_users", "limit": 1, "offset": index}
                )
                return time.time() - start, True
            except Exception:
                return time.time() - start, False

        # Test with increasing concurrency
        concurrency_levels = [10, 50, 100, 200, 500]
        pool_performance = []

        for level in concurrency_levels:
            start = time.time()
            tasks = [db_operation(i) for i in range(level)]
            results = await asyncio.gather(*tasks)
            total_time = time.time() - start

            durations = [r[0] for r in results]
            successes = sum(1 for r in results if r[1])

            pool_performance.append(
                {
                    "concurrency": level,
                    "total_time": total_time,
                    "success_rate": successes / level,
                    "avg_duration": statistics.mean(durations),
                    "max_duration": max(durations),
                }
            )

            # Should handle high concurrency
            assert successes / level > 0.95  # 95% success rate
            assert max(durations) < 1.0  # No operation takes more than 1 second

        # Connection pool should scale efficiently
        for i in range(1, len(pool_performance)):
            prev = pool_performance[i - 1]
            curr = pool_performance[i]

            # Total time should not scale linearly with concurrency
            assert curr["total_time"] < prev["total_time"] * 2

    def generate_performance_report(self, results: Dict[str, Any]) -> str:
        """Generate a performance test report"""
        report = []
        report.append("# Performance Test Report")
        report.append(f"Generated at: {datetime.utcnow().isoformat()}")
        report.append("")

        for test_name, test_results in results.items():
            report.append(f"## {test_name}")
            report.append("")

            if isinstance(test_results, list):
                # Table format for list results
                if test_results:
                    headers = list(test_results[0].keys())
                    report.append("| " + " | ".join(headers) + " |")
                    report.append("| " + " | ".join(["---"] * len(headers)) + " |")

                    for row in test_results:
                        values = [str(row.get(h, "")) for h in headers]
                        report.append("| " + " | ".join(values) + " |")
            else:
                # Key-value format
                for key, value in test_results.items():
                    report.append(f"- {key}: {value}")

            report.append("")

        return "\n".join(report)
