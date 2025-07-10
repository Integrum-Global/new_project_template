#!/usr/bin/env python3
"""
Performance Baseline Validation for Nexus Production Hardening.

Runs performance tests to establish baseline metrics and SLAs for TODO-108.
"""

import asyncio
import json
import logging
import subprocess
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Dict

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class BaselineValidator:
    """Validates performance baselines for production deployment."""

    def __init__(self, output_dir: Path):
        """Initialize baseline validator."""
        self.output_dir = output_dir
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.results = {}
        self.start_time = datetime.now()

    def test_import_performance(self) -> Dict[str, Any]:
        """Test Python import performance."""
        logger.info("Testing Python import performance...")

        start_time = time.time()
        try:
            # Test importing core Nexus modules
            import sys

            nexus_src = Path(__file__).parent.parent.parent / "src"
            sys.path.insert(0, str(nexus_src))

            # Time critical imports
            import_start = time.time()
            from nexus.core.application import NexusApplication
            from nexus.core.config import NexusConfig
            from nexus.monitoring.metrics import HealthMonitor, MetricsCollector

            import_end = time.time()

            import_time = import_end - import_start

            return {
                "status": "success",
                "import_time_ms": round(import_time * 1000, 2),
                "baseline_target_ms": 500,  # Target: <500ms
                "meets_target": import_time < 0.5,
                "timestamp": datetime.now().isoformat(),
            }

        except Exception as e:
            return {
                "status": "error",
                "error": str(e),
                "timestamp": datetime.now().isoformat(),
            }

    def test_config_performance(self) -> Dict[str, Any]:
        """Test configuration loading performance."""
        logger.info("Testing configuration performance...")

        try:
            import sys

            nexus_src = Path(__file__).parent.parent.parent / "src"
            sys.path.insert(0, str(nexus_src))

            from nexus.core.config import MonitoringConfig, NexusConfig

            # Time configuration creation
            start_time = time.time()
            for _ in range(100):  # Create 100 configs to test performance
                config = NexusConfig(name="PerformanceTest", version="1.0.0")
                # Configure monitoring
                config.features.monitoring = MonitoringConfig(
                    enabled=True,
                    prometheus_enabled=False,
                    health_checks=True,
                    metrics_port=9090,
                )
            end_time = time.time()

            avg_time_per_config = (end_time - start_time) / 100

            return {
                "status": "success",
                "avg_config_time_ms": round(avg_time_per_config * 1000, 2),
                "baseline_target_ms": 10,  # Target: <10ms per config
                "meets_target": avg_time_per_config < 0.01,
                "configs_created": 100,
                "timestamp": datetime.now().isoformat(),
            }

        except Exception as e:
            return {
                "status": "error",
                "error": str(e),
                "timestamp": datetime.now().isoformat(),
            }

    def test_monitoring_performance(self) -> Dict[str, Any]:
        """Test monitoring system performance."""
        logger.info("Testing monitoring performance...")

        try:
            import sys

            nexus_src = Path(__file__).parent.parent.parent / "src"
            sys.path.insert(0, str(nexus_src))

            from nexus.monitoring.metrics import HealthMonitor, MetricsCollector

            # Test metrics collector performance
            collector = MetricsCollector(enable_prometheus=False)

            # Time metric operations
            start_time = time.time()
            for i in range(1000):  # 1000 metric operations
                collector.record_channel_request("api", "GET", "success", 0.1)
                collector.record_workflow_execution(
                    f"workflow-{i % 10}", "success", "api", 1.0
                )
                collector.update_active_sessions("api", 25)
                collector.record_session_duration("api", 300.0)
                collector.record_error("test", "test_error", "warning")
            end_time = time.time()

            total_time = end_time - start_time
            ops_per_second = (
                5000 / total_time
            )  # 5 operations per iteration × 1000 iterations

            # Test health monitor
            health_monitor = HealthMonitor(collector)

            # Time health check registration and execution
            health_start = time.time()

            async def test_health():
                return {"healthy": True, "details": "Test health check"}

            health_monitor.register_health_check("test_check", test_health)
            health_end = time.time()

            health_registration_time = health_end - health_start

            return {
                "status": "success",
                "metrics_ops_per_second": round(ops_per_second, 2),
                "baseline_target_ops": 10000,  # Target: >10k ops/sec
                "meets_ops_target": ops_per_second > 10000,
                "health_registration_ms": round(health_registration_time * 1000, 2),
                "baseline_target_health_ms": 50,  # Target: <50ms
                "meets_health_target": health_registration_time < 0.05,
                "total_operations": 5000,
                "timestamp": datetime.now().isoformat(),
            }

        except Exception as e:
            return {
                "status": "error",
                "error": str(e),
                "timestamp": datetime.now().isoformat(),
            }

    async def test_async_performance(self) -> Dict[str, Any]:
        """Test async operation performance."""
        logger.info("Testing async performance...")

        try:
            import sys

            nexus_src = Path(__file__).parent.parent.parent / "src"
            sys.path.insert(0, str(nexus_src))

            from nexus.monitoring.metrics import HealthMonitor

            # Test async health checks
            health_monitor = HealthMonitor()

            async def fast_health_check():
                await asyncio.sleep(0.001)  # Simulate 1ms operation
                return {"healthy": True, "response_time": 1}

            # Register multiple health checks
            for i in range(10):
                health_monitor.register_health_check(f"check_{i}", fast_health_check)

            # Time concurrent health check execution
            start_time = time.time()
            results = await health_monitor.run_health_checks()
            end_time = time.time()

            execution_time = end_time - start_time

            return {
                "status": "success",
                "async_execution_time_ms": round(execution_time * 1000, 2),
                "baseline_target_ms": 100,  # Target: <100ms for 10 health checks
                "meets_target": execution_time < 0.1,
                "health_checks_count": 10,
                "overall_status": results.get("status", "unknown"),
                "timestamp": datetime.now().isoformat(),
            }

        except Exception as e:
            return {
                "status": "error",
                "error": str(e),
                "timestamp": datetime.now().isoformat(),
            }

    def test_memory_usage(self) -> Dict[str, Any]:
        """Test memory usage patterns."""
        logger.info("Testing memory usage...")

        try:
            import sys

            import psutil

            nexus_src = Path(__file__).parent.parent.parent / "src"
            sys.path.insert(0, str(nexus_src))

            # Get initial memory
            process = psutil.Process()
            initial_memory = process.memory_info().rss / 1024 / 1024  # MB

            # Import and initialize components
            from nexus.core.config import NexusConfig
            from nexus.monitoring.metrics import HealthMonitor, MetricsCollector

            # Create multiple instances to test memory usage
            configs = []
            collectors = []

            for i in range(50):  # Create 50 instances
                config = NexusConfig(name=f"Test-{i}")
                collector = MetricsCollector(enable_prometheus=False)
                configs.append(config)
                collectors.append(collector)

            # Get final memory
            final_memory = process.memory_info().rss / 1024 / 1024  # MB
            memory_increase = final_memory - initial_memory

            return {
                "status": "success",
                "initial_memory_mb": round(initial_memory, 2),
                "final_memory_mb": round(final_memory, 2),
                "memory_increase_mb": round(memory_increase, 2),
                "baseline_target_mb": 100,  # Target: <100MB increase for 50 instances
                "meets_target": memory_increase < 100,
                "instances_created": 50,
                "avg_memory_per_instance_mb": round(memory_increase / 50, 2),
                "timestamp": datetime.now().isoformat(),
            }

        except Exception as e:
            return {
                "status": "error",
                "error": str(e),
                "timestamp": datetime.now().isoformat(),
            }

    def test_concurrent_operations(self) -> Dict[str, Any]:
        """Test concurrent operation performance."""
        logger.info("Testing concurrent operations...")

        try:
            import sys
            import threading

            nexus_src = Path(__file__).parent.parent.parent / "src"
            sys.path.insert(0, str(nexus_src))

            from nexus.monitoring.metrics import MetricsCollector

            # Create a shared metrics collector
            collector = MetricsCollector(enable_prometheus=False)

            # Concurrent operation function
            def worker_function(worker_id: int, operations: int):
                for i in range(operations):
                    collector.record_channel_request("api", "GET", "success", 0.1)
                    collector.record_workflow_execution(
                        f"workflow-{worker_id}-{i}", "success", "api", 1.0
                    )

            # Run concurrent workers
            num_workers = 10
            operations_per_worker = 100

            start_time = time.time()

            threads = []
            for worker_id in range(num_workers):
                thread = threading.Thread(
                    target=worker_function, args=(worker_id, operations_per_worker)
                )
                threads.append(thread)
                thread.start()

            # Wait for all threads to complete
            for thread in threads:
                thread.join()

            end_time = time.time()

            total_time = end_time - start_time
            total_operations = (
                num_workers * operations_per_worker * 2
            )  # 2 operations per iteration
            ops_per_second = total_operations / total_time

            return {
                "status": "success",
                "concurrent_workers": num_workers,
                "operations_per_worker": operations_per_worker * 2,
                "total_operations": total_operations,
                "execution_time_seconds": round(total_time, 2),
                "ops_per_second": round(ops_per_second, 2),
                "baseline_target_ops": 5000,  # Target: >5k ops/sec
                "meets_target": ops_per_second > 5000,
                "timestamp": datetime.now().isoformat(),
            }

        except Exception as e:
            return {
                "status": "error",
                "error": str(e),
                "timestamp": datetime.now().isoformat(),
            }

    async def run_all_tests(self) -> Dict[str, Any]:
        """Run all performance baseline tests."""
        logger.info("Starting comprehensive performance baseline validation...")

        all_results = {
            "test_session": {
                "start_time": self.start_time.isoformat(),
                "test_type": "performance_baseline_validation",
                "purpose": "TODO-108 Nexus Production Hardening - Performance SLA Establishment",
            },
            "tests": {},
        }

        # Run synchronous tests
        sync_tests = [
            ("import_performance", self.test_import_performance),
            ("config_performance", self.test_config_performance),
            ("monitoring_performance", self.test_monitoring_performance),
            ("memory_usage", self.test_memory_usage),
            ("concurrent_operations", self.test_concurrent_operations),
        ]

        for test_name, test_func in sync_tests:
            logger.info(f"Running {test_name}...")
            try:
                result = test_func()
                all_results["tests"][test_name] = result
                logger.info(
                    f"✅ {test_name}: {'PASS' if result.get('meets_target', False) else 'FAIL'}"
                )
            except Exception as e:
                logger.error(f"❌ {test_name}: ERROR - {e}")
                all_results["tests"][test_name] = {
                    "status": "error",
                    "error": str(e),
                    "timestamp": datetime.now().isoformat(),
                }

        # Run async tests
        logger.info("Running async_performance...")
        try:
            async_result = await self.test_async_performance()
            all_results["tests"]["async_performance"] = async_result
            logger.info(
                f"✅ async_performance: {'PASS' if async_result.get('meets_target', False) else 'FAIL'}"
            )
        except Exception as e:
            logger.error(f"❌ async_performance: ERROR - {e}")
            all_results["tests"]["async_performance"] = {
                "status": "error",
                "error": str(e),
                "timestamp": datetime.now().isoformat(),
            }

        # Calculate overall results
        end_time = datetime.now()
        all_results["test_session"]["end_time"] = end_time.isoformat()
        all_results["test_session"]["duration_seconds"] = (
            end_time - self.start_time
        ).total_seconds()

        # Analyze results
        total_tests = len(all_results["tests"])
        successful_tests = sum(
            1
            for test in all_results["tests"].values()
            if test.get("status") == "success"
        )
        passing_tests = sum(
            1
            for test in all_results["tests"].values()
            if test.get("meets_target", False)
        )

        all_results["summary"] = {
            "total_tests": total_tests,
            "successful_tests": successful_tests,
            "passing_tests": passing_tests,
            "success_rate": round((successful_tests / total_tests) * 100, 2),
            "baseline_compliance_rate": round((passing_tests / total_tests) * 100, 2),
            "overall_status": "PASS" if passing_tests == total_tests else "FAIL",
            "production_ready": passing_tests >= total_tests * 0.8,  # 80% threshold
        }

        return all_results

    def save_results(self, results: Dict[str, Any]) -> Path:
        """Save test results to file."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"performance_baseline_{timestamp}.json"
        filepath = self.output_dir / filename

        with open(filepath, "w") as f:
            json.dump(results, f, indent=2)

        logger.info(f"Results saved to: {filepath}")
        return filepath

    def print_summary(self, results: Dict[str, Any]):
        """Print test summary."""
        summary = results.get("summary", {})

        print("\n" + "=" * 60)
        print("NEXUS PERFORMANCE BASELINE VALIDATION SUMMARY")
        print("=" * 60)
        print(
            f"Test Duration: {results['test_session'].get('duration_seconds', 0):.2f} seconds"
        )
        print(f"Total Tests: {summary.get('total_tests', 0)}")
        print(f"Successful: {summary.get('successful_tests', 0)}")
        print(f"Meeting Baselines: {summary.get('passing_tests', 0)}")
        print(f"Success Rate: {summary.get('success_rate', 0):.1f}%")
        print(f"Baseline Compliance: {summary.get('baseline_compliance_rate', 0):.1f}%")
        print(f"Overall Status: {summary.get('overall_status', 'UNKNOWN')}")
        print(
            f"Production Ready: {'YES' if summary.get('production_ready', False) else 'NO'}"
        )

        print("\nDETAILED RESULTS:")
        print("-" * 60)
        for test_name, test_result in results.get("tests", {}).items():
            status = test_result.get("status", "unknown")
            meets_target = test_result.get("meets_target", False)
            status_icon = (
                "✅"
                if status == "success" and meets_target
                else "❌" if status == "error" else "⚠️"
            )
            print(
                f"{status_icon} {test_name:<25} {status.upper():<8} {'PASS' if meets_target else 'FAIL'}"
            )

        print("\n" + "=" * 60)


async def main():
    """Main function to run performance baseline validation."""
    # Set up output directory
    output_dir = Path(__file__).parent / "results"

    # Create validator
    validator = BaselineValidator(output_dir)

    try:
        # Run all tests
        results = await validator.run_all_tests()

        # Save results
        filepath = validator.save_results(results)

        # Print summary
        validator.print_summary(results)

        # Return appropriate exit code
        return 0 if results["summary"]["production_ready"] else 1

    except Exception as e:
        logger.error(f"Performance validation failed: {e}")
        return 1


if __name__ == "__main__":
    import sys

    try:
        exit_code = asyncio.run(main())
        sys.exit(exit_code)
    except KeyboardInterrupt:
        logger.info("Performance validation interrupted by user")
        sys.exit(130)
