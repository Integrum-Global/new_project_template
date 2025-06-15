"""
Business logic services for QA Agentic Testing System.

These services implement the core business logic and coordinate between
the domain models and the database layer.
"""

import asyncio
import json
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from .database import QADatabase, get_database
from .models import (
    AgentSession,
    AgentType,
    InterfaceType,
    Priority,
    TestMetrics,
    TestProject,
    TestResult,
    TestRun,
    TestStatus,
    TestType,
    create_test_project,
    create_test_result,
    create_test_run,
)
from .personas import PersonaManager
from .report_generator import ReportGenerator
from .scenario_generator import ScenarioGenerator
from .test_executor import AutonomousQATester


class ProjectService:
    """Service for managing test projects."""

    def __init__(self, db: Optional[QADatabase] = None):
        self.db = db or get_database()

    async def create_project(
        self, name: str, app_path: str, description: str = "", **kwargs
    ) -> TestProject:
        """Create a new test project."""
        project = create_test_project(name, app_path, description)

        # Apply any additional configuration
        if "interfaces" in kwargs:
            project.interfaces = kwargs["interfaces"]
        if "test_types" in kwargs:
            project.test_types = kwargs["test_types"]
        if "agent_config" in kwargs:
            project.agent_config = kwargs["agent_config"]
        if "tags" in kwargs:
            project.tags = kwargs["tags"]
        if "tenant_id" in kwargs:
            project.tenant_id = kwargs["tenant_id"]

        # Perform discovery
        await self._discover_project(project)

        return await self.db.create_project(project)

    async def get_project(self, project_id: str) -> Optional[TestProject]:
        """Get a project by ID."""
        return await self.db.get_project(project_id)

    async def list_projects(
        self, tenant_id: str = "default", is_active: bool = True
    ) -> List[TestProject]:
        """List all projects."""
        return await self.db.list_projects(tenant_id, is_active)

    async def update_project(
        self, project_id: str, updates: Dict[str, Any]
    ) -> Optional[TestProject]:
        """Update a project."""
        return await self.db.update_project(project_id, updates)

    async def delete_project(self, project_id: str) -> bool:
        """Soft delete a project."""
        updated = await self.db.update_project(project_id, {"is_active": False})
        return updated is not None

    async def discover_project(self, project_id: str) -> Optional[TestProject]:
        """Re-run discovery for a project."""
        project = await self.get_project(project_id)
        if not project:
            return None

        await self._discover_project(project)
        return await self.db.update_project(
            project_id,
            {
                "discovered_permissions": project.discovered_permissions,
                "discovered_endpoints": project.discovered_endpoints,
                "discovered_commands": project.discovered_commands,
                "updated_at": datetime.now(timezone.utc),
            },
        )

    async def _discover_project(self, project: TestProject):
        """Perform project discovery."""
        tester = AutonomousQATester()

        try:
            discovery_result = tester.discover_app(Path(project.app_path))

            # Update project with discovery results
            project.discovered_permissions = discovery_result.get("permissions", [])
            project.discovered_endpoints = discovery_result.get("endpoints", [])
            project.discovered_commands = discovery_result.get("commands", [])

        except Exception as e:
            # Log the error but don't fail project creation
            print(f"Discovery failed for project {project.name}: {e}")


class TestRunService:
    """Service for managing test runs."""

    def __init__(self, db: Optional[QADatabase] = None):
        self.db = db or get_database()
        self.project_service = ProjectService(db)

    async def create_run(
        self, project_id: str, name: str, description: str = "", **kwargs
    ) -> TestRun:
        """Create a new test run."""
        # Verify project exists
        project = await self.project_service.get_project(project_id)
        if not project:
            raise ValueError(f"Project {project_id} not found")

        run = create_test_run(project_id, name, description)

        # Apply configuration
        if "test_types" in kwargs:
            run.test_types = kwargs["test_types"]
        if "agent_types" in kwargs:
            run.agent_types = kwargs["agent_types"]
        if "personas_used" in kwargs:
            run.personas_used = kwargs["personas_used"]
        if "interfaces_tested" in kwargs:
            run.interfaces_tested = kwargs["interfaces_tested"]
        if "priority" in kwargs:
            run.priority = kwargs["priority"]
        if "tenant_id" in kwargs:
            run.tenant_id = kwargs["tenant_id"]

        return await self.db.create_run(run)

    async def get_run(self, run_id: str) -> Optional[TestRun]:
        """Get a test run by ID."""
        return await self.db.get_run(run_id)

    async def list_runs(
        self,
        project_id: Optional[str] = None,
        tenant_id: str = "default",
        limit: int = 50,
    ) -> List[TestRun]:
        """List test runs."""
        return await self.db.list_runs(project_id, tenant_id, limit)

    async def start_run(self, run_id: str) -> TestRun:
        """Start a test run."""
        run = await self.get_run(run_id)
        if not run:
            raise ValueError(f"Test run {run_id} not found")

        if run.status != TestStatus.PENDING:
            raise ValueError(f"Test run {run_id} is not in pending status")

        # Update run status
        await self.db.update_run(
            run_id,
            {
                "status": TestStatus.RUNNING.value,
                "started_at": datetime.now(timezone.utc).isoformat(),
            },
        )

        # Execute the test run asynchronously
        asyncio.create_task(self._execute_run(run_id))

        return await self.get_run(run_id)

    async def cancel_run(self, run_id: str) -> TestRun:
        """Cancel a running test run."""
        await self.db.update_run(
            run_id,
            {
                "status": TestStatus.CANCELLED.value,
                "completed_at": datetime.now(timezone.utc).isoformat(),
            },
        )
        return await self.get_run(run_id)

    async def _execute_run(self, run_id: str):
        """Execute a test run (internal method)."""
        try:
            run = await self.get_run(run_id)
            project = await self.project_service.get_project(run.project_id)

            if not project:
                raise ValueError(f"Project {run.project_id} not found")

            # Initialize testing components with target app's path
            app_path = Path(project.app_path)
            tester = AutonomousQATester(app_path=app_path)
            tester.discover_app(app_path)

            # Generate personas and scenarios
            personas = tester.generate_personas()
            scenarios = tester.generate_scenarios()

            # Update run with scenario count
            await self.db.update_run(
                run_id,
                {
                    "total_scenarios": len(scenarios),
                    "personas_used": [p.key for p in personas],
                },
            )

            # Execute tests
            results = await tester.execute_tests()

            # Generate reports
            html_report = tester.generate_report("html")
            json_report = tester.generate_report("json")

            # Calculate final metrics
            success_rate = (
                (results.passed_scenarios / results.total_scenarios * 100)
                if results.total_scenarios > 0
                else 0
            )

            # Update run with final results
            await self.db.update_run(
                run_id,
                {
                    "status": TestStatus.COMPLETED.value,
                    "completed_at": datetime.now(timezone.utc).isoformat(),
                    "duration_seconds": (
                        (datetime.now(timezone.utc) - run.started_at).total_seconds()
                        if run.started_at
                        else 0
                    ),
                    "passed_scenarios": results.passed_scenarios,
                    "failed_scenarios": results.failed_scenarios,
                    "success_rate": success_rate,
                    "confidence_score": results.confidence_score,
                    "ai_insights": results.ai_insights,
                    "agent_consensus": results.agent_consensus,
                    "html_report_path": str(html_report),
                    "json_report_path": str(json_report),
                },
            )

            # Update project statistics
            await self._update_project_stats(run.project_id)

        except Exception as e:
            # Mark run as failed
            await self.db.update_run(
                run_id,
                {
                    "status": TestStatus.FAILED.value,
                    "completed_at": datetime.now(timezone.utc).isoformat(),
                    "error_message": str(e),
                    "error_details": {"traceback": str(e)},
                },
            )

    async def _update_project_stats(self, project_id: str):
        """Update project statistics after a test run."""
        runs = await self.list_runs(project_id=project_id, limit=100)
        completed_runs = [r for r in runs if r.status == TestStatus.COMPLETED]

        if completed_runs:
            avg_success_rate = sum(r.success_rate for r in completed_runs) / len(
                completed_runs
            )
            last_run = max(completed_runs, key=lambda r: r.completed_at).completed_at

            await self.project_service.update_project(
                project_id,
                {
                    "total_test_runs": len(runs),
                    "average_success_rate": avg_success_rate,
                    "last_test_run": last_run,
                },
            )


class TestResultService:
    """Service for managing test results."""

    def __init__(self, db: Optional[QADatabase] = None):
        self.db = db or get_database()

    async def create_result(
        self,
        run_id: str,
        scenario_id: str,
        scenario_name: str,
        test_type: TestType,
        persona: str,
        interface_type: InterfaceType,
        **kwargs,
    ) -> TestResult:
        """Create a new test result."""
        result = create_test_result(
            run_id, scenario_id, scenario_name, test_type, persona, interface_type
        )

        # Apply additional data
        for key, value in kwargs.items():
            if hasattr(result, key):
                setattr(result, key, value)

        return await self.db.create_result(result)

    async def list_results(self, run_id: str) -> List[TestResult]:
        """List test results for a run."""
        return await self.db.list_results(run_id)

    async def get_run_summary(self, run_id: str) -> Dict[str, Any]:
        """Get summary statistics for a test run."""
        results = await self.list_results(run_id)

        if not results:
            return {
                "total": 0,
                "passed": 0,
                "failed": 0,
                "success_rate": 0.0,
                "average_confidence": 0.0,
                "by_test_type": {},
                "by_persona": {},
                "by_interface": {},
            }

        total = len(results)
        passed = sum(1 for r in results if r.passed)
        failed = total - passed
        success_rate = (passed / total) * 100 if total > 0 else 0
        avg_confidence = sum(r.confidence_score for r in results) / total

        # Breakdown by categories
        by_test_type = {}
        by_persona = {}
        by_interface = {}

        for result in results:
            # By test type
            test_type = result.test_type.value
            if test_type not in by_test_type:
                by_test_type[test_type] = {"total": 0, "passed": 0}
            by_test_type[test_type]["total"] += 1
            if result.passed:
                by_test_type[test_type]["passed"] += 1

            # By persona
            if result.persona not in by_persona:
                by_persona[result.persona] = {"total": 0, "passed": 0}
            by_persona[result.persona]["total"] += 1
            if result.passed:
                by_persona[result.persona]["passed"] += 1

            # By interface
            interface = result.interface_type.value
            if interface not in by_interface:
                by_interface[interface] = {"total": 0, "passed": 0}
            by_interface[interface]["total"] += 1
            if result.passed:
                by_interface[interface]["passed"] += 1

        return {
            "total": total,
            "passed": passed,
            "failed": failed,
            "success_rate": success_rate,
            "average_confidence": avg_confidence,
            "by_test_type": by_test_type,
            "by_persona": by_persona,
            "by_interface": by_interface,
        }


class AnalyticsService:
    """Service for analytics and metrics."""

    def __init__(self, db: Optional[QADatabase] = None):
        self.db = db or get_database()
        self.project_service = ProjectService(db)
        self.run_service = TestRunService(db)

    async def get_project_analytics(
        self, project_id: str, days: int = 30
    ) -> Dict[str, Any]:
        """Get analytics for a project."""
        project = await self.project_service.get_project(project_id)
        if not project:
            raise ValueError(f"Project {project_id} not found")

        # Get recent runs
        runs = await self.run_service.list_runs(project_id=project_id, limit=100)
        cutoff_date = datetime.now(timezone.utc) - timedelta(days=days)
        recent_runs = [r for r in runs if r.created_at >= cutoff_date]

        # Calculate metrics
        total_runs = len(recent_runs)
        completed_runs = [r for r in recent_runs if r.status == TestStatus.COMPLETED]
        failed_runs = [r for r in recent_runs if r.status == TestStatus.FAILED]

        avg_success_rate = (
            sum(r.success_rate for r in completed_runs) / len(completed_runs)
            if completed_runs
            else 0
        )
        avg_duration = (
            sum(r.duration_seconds for r in completed_runs if r.duration_seconds)
            / len(completed_runs)
            if completed_runs
            else 0
        )
        avg_confidence = (
            sum(r.confidence_score for r in completed_runs) / len(completed_runs)
            if completed_runs
            else 0
        )

        # Trend data
        success_trend = []
        performance_trend = []
        for run in sorted(completed_runs, key=lambda r: r.created_at):
            success_trend.append(run.success_rate)
            if run.duration_seconds:
                performance_trend.append(run.duration_seconds)

        return {
            "project": project.to_dict(),
            "period_days": days,
            "total_runs": total_runs,
            "completed_runs": len(completed_runs),
            "failed_runs": len(failed_runs),
            "success_rate": avg_success_rate,
            "average_duration_seconds": avg_duration,
            "average_confidence_score": avg_confidence,
            "success_rate_trend": success_trend,
            "performance_trend": performance_trend,
            "recent_runs": [r.to_dict() for r in recent_runs[:10]],  # Last 10 runs
        }

    async def get_global_analytics(
        self, tenant_id: str = "default", days: int = 30
    ) -> Dict[str, Any]:
        """Get global analytics across all projects."""
        projects = await self.project_service.list_projects(tenant_id)

        total_projects = len(projects)
        total_runs = 0
        total_scenarios = 0
        avg_success_rate = 0

        project_analytics = []
        for project in projects:
            analytics = await self.get_project_analytics(project.project_id, days)
            project_analytics.append(
                {
                    "project_id": project.project_id,
                    "name": project.name,
                    "success_rate": analytics["success_rate"],
                    "total_runs": analytics["total_runs"],
                    "completed_runs": analytics["completed_runs"],
                }
            )

            total_runs += analytics["total_runs"]
            if analytics["completed_runs"] > 0:
                avg_success_rate += analytics["success_rate"]

        avg_success_rate = (
            avg_success_rate
            / len([p for p in project_analytics if p["completed_runs"] > 0])
            if project_analytics
            else 0
        )

        return {
            "tenant_id": tenant_id,
            "period_days": days,
            "total_projects": total_projects,
            "total_runs": total_runs,
            "average_success_rate": avg_success_rate,
            "projects": project_analytics,
        }


class ReportService:
    """Service for generating and managing reports."""

    def __init__(self, db: Optional[QADatabase] = None):
        self.db = db or get_database()
        self.run_service = TestRunService(db)
        self.result_service = TestResultService(db)

    async def generate_run_report(self, run_id: str, format: str = "html") -> Path:
        """Generate a report for a test run."""
        run = await self.run_service.get_run(run_id)
        if not run:
            raise ValueError(f"Test run {run_id} not found")

        results = await self.result_service.list_results(run_id)
        summary = await self.result_service.get_run_summary(run_id)

        # Use the existing report generator
        report_generator = ReportGenerator()

        if format.lower() == "html":
            return report_generator.generate_html_report(run, results, summary)
        elif format.lower() == "json":
            return report_generator.generate_json_report(run, results, summary)
        else:
            raise ValueError(f"Unsupported report format: {format}")

    async def get_report_data(self, run_id: str) -> Dict[str, Any]:
        """Get structured report data for a test run."""
        run = await self.run_service.get_run(run_id)
        if not run:
            raise ValueError(f"Test run {run_id} not found")

        results = await self.result_service.list_results(run_id)
        summary = await self.result_service.get_run_summary(run_id)

        return {
            "run": run.to_dict(),
            "results": [r.to_dict() for r in results],
            "summary": summary,
            "generated_at": datetime.now(timezone.utc).isoformat(),
        }
