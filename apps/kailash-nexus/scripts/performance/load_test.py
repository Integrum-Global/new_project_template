#!/usr/bin/env python3
"""
Performance testing and load testing for Nexus application.

Comprehensive performance validation including load testing, stress testing,
and capacity planning for production deployment.
"""

import asyncio
import concurrent.futures
import json
import logging
import statistics
import subprocess
import time
from dataclasses import asdict, dataclass
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import aiohttp
import psutil

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


@dataclass
class LoadTestConfig:
    """Configuration for load testing."""

    base_url: str = "http://localhost:8000"
    concurrent_users: int = 10
    test_duration: int = 60  # seconds
    ramp_up_time: int = 10  # seconds
    think_time: float = 1.0  # seconds between requests
    timeout: int = 30  # request timeout


@dataclass
class PerformanceMetrics:
    """Performance metrics collected during testing."""

    total_requests: int = 0
    successful_requests: int = 0
    failed_requests: int = 0
    avg_response_time: float = 0.0
    min_response_time: float = 0.0
    max_response_time: float = 0.0
    p50_response_time: float = 0.0
    p95_response_time: float = 0.0
    p99_response_time: float = 0.0
    requests_per_second: float = 0.0
    error_rate: float = 0.0
    throughput_mb: float = 0.0


@dataclass
class ResourceMetrics:
    """System resource metrics."""

    cpu_usage: float = 0.0
    memory_usage: float = 0.0
    memory_usage_mb: float = 0.0
    disk_io_read: float = 0.0
    disk_io_write: float = 0.0
    network_io_sent: float = 0.0
    network_io_recv: float = 0.0


class PerformanceTester:
    """Comprehensive performance testing suite."""

    def __init__(self, config: LoadTestConfig, output_dir: Path):
        """Initialize performance tester.

        Args:
            config: Load test configuration
            output_dir: Directory to store test results
        """
        self.config = config
        self.output_dir = output_dir
        self.output_dir.mkdir(parents=True, exist_ok=True)

        # Test data storage
        self.response_times: List[float] = []
        self.request_results: List[Dict[str, Any]] = []
        self.resource_samples: List[ResourceMetrics] = []
        self.start_time: Optional[float] = None
        self.end_time: Optional[float] = None

        # Test scenarios
        self.test_scenarios = {
            "health_check": self._test_health_endpoint,
            "workflow_list": self._test_workflow_list,
            "workflow_execute": self._test_workflow_execution,
            "session_management": self._test_session_operations,
            "marketplace_search": self._test_marketplace_search,
        }

    async def run_load_test(
        self, scenarios: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """Run comprehensive load test.

        Args:
            scenarios: List of test scenarios to run (default: all)

        Returns:
            Complete test results
        """
        logger.info(
            f"Starting load test with {self.config.concurrent_users} users for {self.config.test_duration}s"
        )

        # Use all scenarios if none specified
        if scenarios is None:
            scenarios = list(self.test_scenarios.keys())

        # Initialize metrics collection
        self.start_time = time.time()

        # Start resource monitoring
        resource_monitor_task = asyncio.create_task(self._monitor_resources())

        try:
            # Run load test scenarios
            await self._run_load_test_scenarios(scenarios)

            # Stop resource monitoring
            resource_monitor_task.cancel()
            try:
                await resource_monitor_task
            except asyncio.CancelledError:
                pass

            self.end_time = time.time()

            # Calculate metrics
            performance_metrics = self._calculate_performance_metrics()
            resource_summary = self._calculate_resource_summary()

            # Generate comprehensive report
            report = {
                "test_config": asdict(self.config),
                "test_duration": self.end_time - self.start_time,
                "scenarios_tested": scenarios,
                "performance_metrics": asdict(performance_metrics),
                "resource_metrics": asdict(resource_summary),
                "detailed_results": self.request_results,
                "recommendations": self._generate_recommendations(
                    performance_metrics, resource_summary
                ),
            }

            # Save results
            await self._save_results(report)

            return report

        except Exception as e:
            logger.error(f"Load test failed: {e}")
            raise

    async def _run_load_test_scenarios(self, scenarios: List[str]):
        """Run load test scenarios with concurrent users."""
        # Create user sessions
        connector = aiohttp.TCPConnector(limit=self.config.concurrent_users * 2)
        timeout = aiohttp.ClientTimeout(total=self.config.timeout)

        async with aiohttp.ClientSession(
            connector=connector, timeout=timeout
        ) as session:
            # Calculate ramp-up schedule
            ramp_delay = self.config.ramp_up_time / self.config.concurrent_users

            # Create user tasks
            tasks = []
            for user_id in range(self.config.concurrent_users):
                # Stagger user start times
                start_delay = user_id * ramp_delay
                task = asyncio.create_task(
                    self._simulate_user(session, user_id, scenarios, start_delay)
                )
                tasks.append(task)

            # Wait for all users to complete
            await asyncio.gather(*tasks, return_exceptions=True)

    async def _simulate_user(
        self,
        session: aiohttp.ClientSession,
        user_id: int,
        scenarios: List[str],
        start_delay: float,
    ):
        """Simulate a single user's interaction with the system."""
        # Wait for ramp-up delay
        await asyncio.sleep(start_delay)

        user_start_time = time.time()
        test_end_time = self.start_time + self.config.test_duration

        logger.info(f"User {user_id} starting test scenarios")

        try:
            while time.time() < test_end_time:
                # Cycle through scenarios
                for scenario_name in scenarios:
                    if time.time() >= test_end_time:
                        break

                    scenario_func = self.test_scenarios[scenario_name]
                    await scenario_func(session, user_id)

                    # Think time between requests
                    await asyncio.sleep(self.config.think_time)

        except Exception as e:
            logger.error(f"User {user_id} encountered error: {e}")

        user_duration = time.time() - user_start_time
        logger.info(f"User {user_id} completed after {user_duration:.2f}s")

    async def _test_health_endpoint(self, session: aiohttp.ClientSession, user_id: int):
        """Test health check endpoint."""
        await self._make_request(session, "GET", "/health", user_id, "health_check")

    async def _test_workflow_list(self, session: aiohttp.ClientSession, user_id: int):
        """Test workflow listing endpoint."""
        await self._make_request(
            session, "GET", "/api/workflows", user_id, "workflow_list"
        )

    async def _test_workflow_execution(
        self, session: aiohttp.ClientSession, user_id: int
    ):
        """Test workflow execution endpoint."""
        payload = {
            "workflow_id": "system/user-management",
            "input_data": {"operation": "list_users"},
            "context": {"user_id": f"test_user_{user_id}"},
        }

        await self._make_request(
            session,
            "POST",
            "/api/workflows/execute",
            user_id,
            "workflow_execute",
            json_data=payload,
        )

    async def _test_session_operations(
        self, session: aiohttp.ClientSession, user_id: int
    ):
        """Test session management operations."""
        # Create session
        session_data = {"channel": "api", "user_id": f"test_user_{user_id}"}
        await self._make_request(
            session,
            "POST",
            "/api/sessions",
            user_id,
            "session_create",
            json_data=session_data,
        )

        # List sessions
        await self._make_request(
            session, "GET", "/api/sessions", user_id, "session_list"
        )

    async def _test_marketplace_search(
        self, session: aiohttp.ClientSession, user_id: int
    ):
        """Test marketplace search functionality."""
        search_params = {"query": "data processing", "limit": 10}
        await self._make_request(
            session,
            "GET",
            "/api/marketplace/search",
            user_id,
            "marketplace_search",
            params=search_params,
        )

    async def _make_request(
        self,
        session: aiohttp.ClientSession,
        method: str,
        url: str,
        user_id: int,
        operation: str,
        json_data: Optional[Dict] = None,
        params: Optional[Dict] = None,
    ) -> Dict[str, Any]:
        """Make HTTP request and record metrics."""
        full_url = f"{self.config.base_url}{url}"
        start_time = time.time()

        try:
            kwargs = {}
            if json_data:
                kwargs["json"] = json_data
            if params:
                kwargs["params"] = params

            async with session.request(method, full_url, **kwargs) as response:
                response_text = await response.text()
                end_time = time.time()

                response_time = end_time - start_time
                self.response_times.append(response_time)

                result = {
                    "timestamp": start_time,
                    "user_id": user_id,
                    "operation": operation,
                    "method": method,
                    "url": url,
                    "status_code": response.status,
                    "response_time": response_time,
                    "response_size": len(response_text),
                    "success": 200 <= response.status < 400,
                }

                self.request_results.append(result)
                return result

        except Exception as e:
            end_time = time.time()
            response_time = end_time - start_time

            result = {
                "timestamp": start_time,
                "user_id": user_id,
                "operation": operation,
                "method": method,
                "url": url,
                "status_code": 0,
                "response_time": response_time,
                "response_size": 0,
                "success": False,
                "error": str(e),
            }

            self.request_results.append(result)
            return result

    async def _monitor_resources(self):
        """Monitor system resources during test."""
        while True:
            try:
                # Get current resource usage
                cpu_percent = psutil.cpu_percent(interval=1)
                memory = psutil.virtual_memory()
                disk_io = psutil.disk_io_counters()
                network_io = psutil.net_io_counters()

                metrics = ResourceMetrics(
                    cpu_usage=cpu_percent,
                    memory_usage=memory.percent,
                    memory_usage_mb=memory.used / (1024 * 1024),
                    disk_io_read=disk_io.read_bytes if disk_io else 0,
                    disk_io_write=disk_io.write_bytes if disk_io else 0,
                    network_io_sent=network_io.bytes_sent if network_io else 0,
                    network_io_recv=network_io.bytes_recv if network_io else 0,
                )

                self.resource_samples.append(metrics)

                await asyncio.sleep(1)  # Sample every second

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.warning(f"Resource monitoring error: {e}")
                await asyncio.sleep(1)

    def _calculate_performance_metrics(self) -> PerformanceMetrics:
        """Calculate performance metrics from collected data."""
        if not self.request_results:
            return PerformanceMetrics()

        successful_requests = [r for r in self.request_results if r["success"]]
        failed_requests = [r for r in self.request_results if not r["success"]]

        response_times = [r["response_time"] for r in successful_requests]

        total_requests = len(self.request_results)
        test_duration = (
            self.end_time - self.start_time if self.end_time and self.start_time else 1
        )

        metrics = PerformanceMetrics(
            total_requests=total_requests,
            successful_requests=len(successful_requests),
            failed_requests=len(failed_requests),
            requests_per_second=total_requests / test_duration,
            error_rate=(
                (len(failed_requests) / total_requests) * 100
                if total_requests > 0
                else 0
            ),
        )

        if response_times:
            metrics.avg_response_time = statistics.mean(response_times)
            metrics.min_response_time = min(response_times)
            metrics.max_response_time = max(response_times)
            metrics.p50_response_time = statistics.median(response_times)

            # Calculate percentiles
            sorted_times = sorted(response_times)
            if len(sorted_times) >= 20:  # Need sufficient data for percentiles
                p95_index = int(len(sorted_times) * 0.95)
                p99_index = int(len(sorted_times) * 0.99)
                metrics.p95_response_time = sorted_times[p95_index]
                metrics.p99_response_time = sorted_times[p99_index]

        # Calculate throughput
        total_bytes = sum(r.get("response_size", 0) for r in successful_requests)
        metrics.throughput_mb = (total_bytes / (1024 * 1024)) / test_duration

        return metrics

    def _calculate_resource_summary(self) -> ResourceMetrics:
        """Calculate resource usage summary."""
        if not self.resource_samples:
            return ResourceMetrics()

        return ResourceMetrics(
            cpu_usage=statistics.mean(s.cpu_usage for s in self.resource_samples),
            memory_usage=statistics.mean(s.memory_usage for s in self.resource_samples),
            memory_usage_mb=statistics.mean(
                s.memory_usage_mb for s in self.resource_samples
            ),
            disk_io_read=max(s.disk_io_read for s in self.resource_samples),
            disk_io_write=max(s.disk_io_write for s in self.resource_samples),
            network_io_sent=max(s.network_io_sent for s in self.resource_samples),
            network_io_recv=max(s.network_io_recv for s in self.resource_samples),
        )

    def _generate_recommendations(
        self, perf_metrics: PerformanceMetrics, resource_metrics: ResourceMetrics
    ) -> List[str]:
        """Generate performance recommendations."""
        recommendations = []

        # Response time recommendations
        if perf_metrics.avg_response_time > 1.0:
            recommendations.append(
                "Average response time exceeds 1s - consider performance optimization"
            )

        if perf_metrics.p95_response_time > 2.0:
            recommendations.append(
                "95th percentile response time exceeds 2s - investigate slow queries"
            )

        # Error rate recommendations
        if perf_metrics.error_rate > 5.0:
            recommendations.append(
                f"Error rate {perf_metrics.error_rate:.1f}% is too high - investigate failures"
            )

        # Throughput recommendations
        if perf_metrics.requests_per_second < 10:
            recommendations.append(
                "Low throughput detected - consider scaling or optimization"
            )

        # Resource recommendations
        if resource_metrics.cpu_usage > 80:
            recommendations.append(
                f"High CPU usage {resource_metrics.cpu_usage:.1f}% - consider CPU optimization"
            )

        if resource_metrics.memory_usage > 85:
            recommendations.append(
                f"High memory usage {resource_metrics.memory_usage:.1f}% - check for memory leaks"
            )

        # Success recommendations
        if not recommendations:
            recommendations.append("Performance metrics are within acceptable ranges")

            if perf_metrics.avg_response_time < 0.1:
                recommendations.append(
                    "Excellent response times - system is well optimized"
                )

            if perf_metrics.error_rate < 1.0:
                recommendations.append("Low error rate indicates good system stability")

        return recommendations

    async def _save_results(self, report: Dict[str, Any]):
        """Save test results to files."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        # Save detailed JSON report
        json_file = self.output_dir / f"load_test_report_{timestamp}.json"
        with open(json_file, "w") as f:
            json.dump(report, f, indent=2, default=str)

        # Save human-readable summary
        summary_file = self.output_dir / f"load_test_summary_{timestamp}.md"
        await self._generate_markdown_summary(report, summary_file)

        # Save raw data for analysis
        raw_data_file = self.output_dir / f"raw_results_{timestamp}.json"
        with open(raw_data_file, "w") as f:
            json.dump(
                {
                    "request_results": self.request_results,
                    "resource_samples": [asdict(s) for s in self.resource_samples],
                    "response_times": self.response_times,
                },
                f,
                indent=2,
                default=str,
            )

        logger.info(f"Performance test results saved to {self.output_dir}")

    async def _generate_markdown_summary(
        self, report: Dict[str, Any], output_file: Path
    ):
        """Generate human-readable markdown summary."""
        perf = report["performance_metrics"]
        resource = report["resource_metrics"]

        with open(output_file, "w") as f:
            f.write("# Load Test Summary\n\n")

            # Test configuration
            f.write("## Test Configuration\n")
            f.write(
                f"- **Concurrent Users**: {report['test_config']['concurrent_users']}\n"
            )
            f.write(f"- **Test Duration**: {report['test_duration']:.1f}s\n")
            f.write(f"- **Scenarios**: {', '.join(report['scenarios_tested'])}\n\n")

            # Performance metrics
            f.write("## Performance Results\n")
            f.write(f"- **Total Requests**: {perf['total_requests']}\n")
            f.write(f"- **Successful Requests**: {perf['successful_requests']}\n")
            f.write(f"- **Failed Requests**: {perf['failed_requests']}\n")
            f.write(f"- **Error Rate**: {perf['error_rate']:.2f}%\n")
            f.write(f"- **Requests per Second**: {perf['requests_per_second']:.2f}\n")
            f.write(f"- **Average Response Time**: {perf['avg_response_time']:.3f}s\n")
            f.write(f"- **95th Percentile**: {perf['p95_response_time']:.3f}s\n")
            f.write(f"- **99th Percentile**: {perf['p99_response_time']:.3f}s\n")
            f.write(f"- **Throughput**: {perf['throughput_mb']:.2f} MB/s\n\n")

            # Resource metrics
            f.write("## Resource Usage\n")
            f.write(f"- **Average CPU**: {resource['cpu_usage']:.1f}%\n")
            f.write(f"- **Average Memory**: {resource['memory_usage']:.1f}%\n")
            f.write(f"- **Memory Usage**: {resource['memory_usage_mb']:.1f} MB\n\n")

            # Recommendations
            f.write("## Recommendations\n")
            for i, rec in enumerate(report["recommendations"], 1):
                f.write(f"{i}. {rec}\n")


async def run_capacity_planning_test(
    base_config: LoadTestConfig, output_dir: Path
) -> Dict[str, Any]:
    """Run capacity planning test with increasing load."""
    logger.info("Starting capacity planning test...")

    results = {}
    user_counts = [1, 5, 10, 20, 50, 100]

    for user_count in user_counts:
        logger.info(f"Testing with {user_count} concurrent users...")

        # Create config for this test
        config = LoadTestConfig(
            base_url=base_config.base_url,
            concurrent_users=user_count,
            test_duration=30,  # Shorter duration for capacity testing
            ramp_up_time=5,
            think_time=0.5,
            timeout=base_config.timeout,
        )

        # Run test
        tester = PerformanceTester(config, output_dir / f"capacity_{user_count}_users")
        result = await tester.run_load_test(["health_check", "workflow_list"])

        results[f"{user_count}_users"] = {
            "config": asdict(config),
            "performance": result["performance_metrics"],
            "resources": result["resource_metrics"],
        }

        # Break if error rate becomes too high
        if result["performance_metrics"]["error_rate"] > 10:
            logger.warning(
                f"High error rate at {user_count} users, stopping capacity test"
            )
            break

        # Brief pause between tests
        await asyncio.sleep(5)

    # Save capacity planning results
    capacity_file = output_dir / "capacity_planning_results.json"
    with open(capacity_file, "w") as f:
        json.dump(results, f, indent=2, default=str)

    logger.info("Capacity planning test completed")
    return results


async def main():
    """Main entry point for performance testing."""
    import argparse

    parser = argparse.ArgumentParser(description="Nexus Performance Tester")
    parser.add_argument(
        "--base-url", default="http://localhost:8000", help="Base URL for testing"
    )
    parser.add_argument(
        "--users", type=int, default=10, help="Number of concurrent users"
    )
    parser.add_argument(
        "--duration", type=int, default=60, help="Test duration in seconds"
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path.cwd() / "performance-reports",
        help="Output directory for results",
    )
    parser.add_argument(
        "--scenarios",
        nargs="+",
        choices=[
            "health_check",
            "workflow_list",
            "workflow_execute",
            "session_management",
            "marketplace_search",
        ],
        help="Test scenarios to run",
    )
    parser.add_argument(
        "--capacity-planning",
        action="store_true",
        help="Run capacity planning test with increasing load",
    )

    args = parser.parse_args()

    # Create configuration
    config = LoadTestConfig(
        base_url=args.base_url, concurrent_users=args.users, test_duration=args.duration
    )

    if args.capacity_planning:
        # Run capacity planning test
        results = await run_capacity_planning_test(config, args.output_dir)
        print("\n🚀 Capacity Planning Test Complete")
        print(f"Results saved to {args.output_dir}")
    else:
        # Run standard load test
        tester = PerformanceTester(config, args.output_dir)
        results = await tester.run_load_test(args.scenarios)

        # Print summary
        perf = results["performance_metrics"]
        print("\n🚀 Load Test Complete")
        print(
            f"Requests: {perf['total_requests']} ({perf['successful_requests']} successful)"
        )
        print(f"RPS: {perf['requests_per_second']:.2f}")
        print(f"Avg Response Time: {perf['avg_response_time']:.3f}s")
        print(f"95th Percentile: {perf['p95_response_time']:.3f}s")
        print(f"Error Rate: {perf['error_rate']:.2f}%")


if __name__ == "__main__":
    asyncio.run(main())
