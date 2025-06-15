"""
Database infrastructure for QA Agentic Testing System.

Provides SQLite-based storage with async support and migration capabilities.
"""

import json
import sqlite3
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Type, TypeVar

import aiosqlite

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
)

T = TypeVar("T")


class QADatabase:
    """Main database interface for QA Agentic Testing System."""

    def __init__(self, db_path: str = "qa_testing.db"):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)

    @asynccontextmanager
    async def get_connection(self):
        """Get async database connection."""
        async with aiosqlite.connect(self.db_path) as conn:
            conn.row_factory = aiosqlite.Row
            yield conn

    async def initialize(self):
        """Initialize database with tables."""
        async with self.get_connection() as conn:
            await self._create_tables(conn)
            await conn.commit()

    async def _create_tables(self, conn: aiosqlite.Connection):
        """Create all required tables."""

        # Test Projects table
        await conn.execute(
            """
            CREATE TABLE IF NOT EXISTS test_projects (
                project_id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                description TEXT,
                app_path TEXT NOT NULL,
                interfaces TEXT,  -- JSON array
                test_types TEXT,  -- JSON array
                agent_config TEXT,  -- JSON object
                discovered_permissions TEXT,  -- JSON array
                discovered_endpoints TEXT,  -- JSON array
                discovered_commands TEXT,  -- JSON array
                created_at TEXT NOT NULL,
                updated_at TEXT,
                created_by TEXT,
                is_active BOOLEAN DEFAULT 1,
                tenant_id TEXT DEFAULT 'default',
                tags TEXT,  -- JSON array
                attributes TEXT,  -- JSON object
                total_test_runs INTEGER DEFAULT 0,
                last_test_run TEXT,
                average_success_rate REAL DEFAULT 0.0
            )
        """
        )

        # Test Runs table
        await conn.execute(
            """
            CREATE TABLE IF NOT EXISTS test_runs (
                run_id TEXT PRIMARY KEY,
                project_id TEXT NOT NULL,
                name TEXT NOT NULL,
                description TEXT,
                test_types TEXT,  -- JSON array
                personas_used TEXT,  -- JSON array
                agent_types TEXT,  -- JSON array
                interfaces_tested TEXT,  -- JSON array
                status TEXT NOT NULL,
                started_at TEXT,
                completed_at TEXT,
                duration_seconds REAL,
                total_scenarios INTEGER DEFAULT 0,
                passed_scenarios INTEGER DEFAULT 0,
                failed_scenarios INTEGER DEFAULT 0,
                skipped_scenarios INTEGER DEFAULT 0,
                success_rate REAL DEFAULT 0.0,
                ai_insights TEXT,  -- JSON array
                confidence_score REAL DEFAULT 0.0,
                agent_consensus TEXT,  -- JSON object
                created_at TEXT NOT NULL,
                created_by TEXT,
                tenant_id TEXT DEFAULT 'default',
                priority TEXT DEFAULT 'medium',
                html_report_path TEXT,
                json_report_path TEXT,
                error_message TEXT,
                error_details TEXT,  -- JSON object
                FOREIGN KEY (project_id) REFERENCES test_projects (project_id)
            )
        """
        )

        # Test Results table
        await conn.execute(
            """
            CREATE TABLE IF NOT EXISTS test_results (
                result_id TEXT PRIMARY KEY,
                run_id TEXT NOT NULL,
                scenario_id TEXT NOT NULL,
                scenario_name TEXT NOT NULL,
                test_type TEXT NOT NULL,
                persona TEXT NOT NULL,
                interface_type TEXT NOT NULL,
                status TEXT NOT NULL,
                started_at TEXT NOT NULL,
                completed_at TEXT,
                duration_ms INTEGER,
                passed BOOLEAN DEFAULT 0,
                expected_result TEXT,
                actual_result TEXT,
                validation_details TEXT,  -- JSON object
                ai_analysis TEXT,
                confidence_score REAL DEFAULT 0.0,
                agent_insights TEXT,  -- JSON array
                response_time_ms INTEGER,
                memory_usage_mb REAL,
                cpu_usage_percent REAL,
                error_message TEXT,
                error_traceback TEXT,
                tenant_id TEXT DEFAULT 'default',
                FOREIGN KEY (run_id) REFERENCES test_runs (run_id)
            )
        """
        )

        # Agent Sessions table
        await conn.execute(
            """
            CREATE TABLE IF NOT EXISTS agent_sessions (
                session_id TEXT PRIMARY KEY,
                run_id TEXT NOT NULL,
                agent_type TEXT NOT NULL,
                agent_name TEXT NOT NULL,
                agent_config TEXT,  -- JSON object
                specializations TEXT,  -- JSON array
                started_at TEXT NOT NULL,
                ended_at TEXT,
                is_active BOOLEAN DEFAULT 1,
                total_interactions INTEGER DEFAULT 0,
                successful_interactions INTEGER DEFAULT 0,
                failed_interactions INTEGER DEFAULT 0,
                average_response_time_ms REAL DEFAULT 0.0,
                total_tokens_used INTEGER DEFAULT 0,
                cost_estimate REAL DEFAULT 0.0,
                shared_memory_keys TEXT,  -- JSON array
                collaboration_partners TEXT,  -- JSON array
                insights_generated TEXT,  -- JSON array
                consensus_votes TEXT,  -- JSON object
                tenant_id TEXT DEFAULT 'default',
                FOREIGN KEY (run_id) REFERENCES test_runs (run_id)
            )
        """
        )

        # Test Metrics table
        await conn.execute(
            """
            CREATE TABLE IF NOT EXISTS test_metrics (
                metrics_id TEXT PRIMARY KEY,
                project_id TEXT,
                run_id TEXT,
                period_start TEXT NOT NULL,
                period_end TEXT NOT NULL,
                total_runs INTEGER DEFAULT 0,
                successful_runs INTEGER DEFAULT 0,
                failed_runs INTEGER DEFAULT 0,
                average_duration_seconds REAL DEFAULT 0.0,
                average_success_rate REAL DEFAULT 0.0,
                average_confidence_score REAL DEFAULT 0.0,
                total_scenarios_executed INTEGER DEFAULT 0,
                unique_bugs_found INTEGER DEFAULT 0,
                average_response_time_ms REAL DEFAULT 0.0,
                peak_response_time_ms REAL DEFAULT 0.0,
                total_api_calls INTEGER DEFAULT 0,
                agents_used TEXT,  -- JSON object
                total_agent_interactions INTEGER DEFAULT 0,
                total_tokens_consumed INTEGER DEFAULT 0,
                estimated_cost REAL DEFAULT 0.0,
                success_rate_trend TEXT,  -- JSON array
                performance_trend TEXT,  -- JSON array
                tenant_id TEXT DEFAULT 'default',
                created_at TEXT NOT NULL,
                FOREIGN KEY (project_id) REFERENCES test_projects (project_id),
                FOREIGN KEY (run_id) REFERENCES test_runs (run_id)
            )
        """
        )

        # Create indexes for better performance
        await conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_test_runs_project_id ON test_runs (project_id)"
        )
        await conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_test_runs_status ON test_runs (status)"
        )
        await conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_test_results_run_id ON test_results (run_id)"
        )
        await conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_test_results_status ON test_results (status)"
        )
        await conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_agent_sessions_run_id ON agent_sessions (run_id)"
        )
        await conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_test_metrics_project_id ON test_metrics (project_id)"
        )

    # TestProject operations
    async def create_project(self, project: TestProject) -> TestProject:
        """Create a new test project."""
        async with self.get_connection() as conn:
            await conn.execute(
                """
                INSERT INTO test_projects (
                    project_id, name, description, app_path, interfaces, test_types,
                    agent_config, discovered_permissions, discovered_endpoints,
                    discovered_commands, created_at, updated_at, created_by,
                    is_active, tenant_id, tags, attributes, total_test_runs,
                    last_test_run, average_success_rate
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
                (
                    project.project_id,
                    project.name,
                    project.description,
                    project.app_path,
                    json.dumps([i.value for i in project.interfaces]),
                    json.dumps([t.value for t in project.test_types]),
                    json.dumps(project.agent_config),
                    json.dumps(project.discovered_permissions),
                    json.dumps(project.discovered_endpoints),
                    json.dumps(project.discovered_commands),
                    project.created_at.isoformat(),
                    project.updated_at.isoformat() if project.updated_at else None,
                    project.created_by,
                    project.is_active,
                    project.tenant_id,
                    json.dumps(project.tags),
                    json.dumps(project.attributes),
                    project.total_test_runs,
                    (
                        project.last_test_run.isoformat()
                        if project.last_test_run
                        else None
                    ),
                    project.average_success_rate,
                ),
            )
            await conn.commit()
        return project

    async def get_project(self, project_id: str) -> Optional[TestProject]:
        """Get a test project by ID."""
        async with self.get_connection() as conn:
            cursor = await conn.execute(
                "SELECT * FROM test_projects WHERE project_id = ?", (project_id,)
            )
            row = await cursor.fetchone()
            if row:
                return self._row_to_project(row)
            return None

    async def list_projects(
        self, tenant_id: str = "default", is_active: bool = True
    ) -> List[TestProject]:
        """List all projects for a tenant."""
        async with self.get_connection() as conn:
            cursor = await conn.execute(
                "SELECT * FROM test_projects WHERE tenant_id = ? AND is_active = ? ORDER BY created_at DESC",
                (tenant_id, is_active),
            )
            rows = await cursor.fetchall()
            return [self._row_to_project(row) for row in rows]

    async def update_project(
        self, project_id: str, updates: Dict[str, Any]
    ) -> Optional[TestProject]:
        """Update a test project."""
        updates["updated_at"] = datetime.now(timezone.utc).isoformat()

        # Handle JSON fields
        json_fields = [
            "interfaces",
            "test_types",
            "agent_config",
            "discovered_permissions",
            "discovered_endpoints",
            "discovered_commands",
            "tags",
            "attributes",
        ]
        for field in json_fields:
            if field in updates and updates[field] is not None:
                updates[field] = json.dumps(updates[field])

        set_clause = ", ".join([f"{k} = ?" for k in updates.keys()])
        values = list(updates.values()) + [project_id]

        async with self.get_connection() as conn:
            await conn.execute(
                f"UPDATE test_projects SET {set_clause} WHERE project_id = ?", values
            )
            await conn.commit()

        return await self.get_project(project_id)

    # TestRun operations
    async def create_run(self, run: TestRun) -> TestRun:
        """Create a new test run."""
        async with self.get_connection() as conn:
            await conn.execute(
                """
                INSERT INTO test_runs (
                    run_id, project_id, name, description, test_types, personas_used,
                    agent_types, interfaces_tested, status, started_at, completed_at,
                    duration_seconds, total_scenarios, passed_scenarios, failed_scenarios,
                    skipped_scenarios, success_rate, ai_insights, confidence_score,
                    agent_consensus, created_at, created_by, tenant_id, priority,
                    html_report_path, json_report_path, error_message, error_details
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
                (
                    run.run_id,
                    run.project_id,
                    run.name,
                    run.description,
                    json.dumps([t.value for t in run.test_types]),
                    json.dumps(run.personas_used),
                    json.dumps([a.value for a in run.agent_types]),
                    json.dumps([i.value for i in run.interfaces_tested]),
                    run.status.value,
                    run.started_at.isoformat() if run.started_at else None,
                    run.completed_at.isoformat() if run.completed_at else None,
                    run.duration_seconds,
                    run.total_scenarios,
                    run.passed_scenarios,
                    run.failed_scenarios,
                    run.skipped_scenarios,
                    run.success_rate,
                    json.dumps(run.ai_insights),
                    run.confidence_score,
                    json.dumps(run.agent_consensus),
                    run.created_at.isoformat(),
                    run.created_by,
                    run.tenant_id,
                    run.priority.value,
                    run.html_report_path,
                    run.json_report_path,
                    run.error_message,
                    json.dumps(run.error_details),
                ),
            )
            await conn.commit()
        return run

    async def get_run(self, run_id: str) -> Optional[TestRun]:
        """Get a test run by ID."""
        async with self.get_connection() as conn:
            cursor = await conn.execute(
                "SELECT * FROM test_runs WHERE run_id = ?", (run_id,)
            )
            row = await cursor.fetchone()
            if row:
                return self._row_to_run(row)
            return None

    async def list_runs(
        self,
        project_id: Optional[str] = None,
        tenant_id: str = "default",
        limit: int = 50,
    ) -> List[TestRun]:
        """List test runs."""
        query = "SELECT * FROM test_runs WHERE tenant_id = ?"
        params = [tenant_id]

        if project_id:
            query += " AND project_id = ?"
            params.append(project_id)

        query += " ORDER BY created_at DESC LIMIT ?"
        params.append(limit)

        async with self.get_connection() as conn:
            cursor = await conn.execute(query, params)
            rows = await cursor.fetchall()
            return [self._row_to_run(row) for row in rows]

    async def update_run(
        self, run_id: str, updates: Dict[str, Any]
    ) -> Optional[TestRun]:
        """Update a test run."""
        # Handle JSON fields
        json_fields = [
            "test_types",
            "personas_used",
            "agent_types",
            "interfaces_tested",
            "ai_insights",
            "agent_consensus",
            "error_details",
        ]
        for field in json_fields:
            if field in updates and updates[field] is not None:
                if isinstance(updates[field], list) and field in [
                    "test_types",
                    "agent_types",
                    "interfaces_tested",
                ]:
                    # Handle enum lists
                    updates[field] = json.dumps(updates[field])
                elif not isinstance(updates[field], str):
                    updates[field] = json.dumps(updates[field])

        set_clause = ", ".join([f"{k} = ?" for k in updates.keys()])
        values = list(updates.values()) + [run_id]

        async with self.get_connection() as conn:
            await conn.execute(
                f"UPDATE test_runs SET {set_clause} WHERE run_id = ?", values
            )
            await conn.commit()

        return await self.get_run(run_id)

    # TestResult operations
    async def create_result(self, result: TestResult) -> TestResult:
        """Create a new test result."""
        async with self.get_connection() as conn:
            await conn.execute(
                """
                INSERT INTO test_results (
                    result_id, run_id, scenario_id, scenario_name, test_type, persona,
                    interface_type, status, started_at, completed_at, duration_ms,
                    passed, expected_result, actual_result, validation_details,
                    ai_analysis, confidence_score, agent_insights, response_time_ms,
                    memory_usage_mb, cpu_usage_percent, error_message, error_traceback,
                    tenant_id
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
                (
                    result.result_id,
                    result.run_id,
                    result.scenario_id,
                    result.scenario_name,
                    result.test_type.value,
                    result.persona,
                    result.interface_type.value,
                    result.status.value,
                    result.started_at.isoformat(),
                    result.completed_at.isoformat() if result.completed_at else None,
                    result.duration_ms,
                    result.passed,
                    result.expected_result,
                    result.actual_result,
                    json.dumps(result.validation_details),
                    result.ai_analysis,
                    result.confidence_score,
                    json.dumps(result.agent_insights),
                    result.response_time_ms,
                    result.memory_usage_mb,
                    result.cpu_usage_percent,
                    result.error_message,
                    result.error_traceback,
                    result.tenant_id,
                ),
            )
            await conn.commit()
        return result

    async def list_results(self, run_id: str) -> List[TestResult]:
        """List test results for a run."""
        async with self.get_connection() as conn:
            cursor = await conn.execute(
                "SELECT * FROM test_results WHERE run_id = ? ORDER BY started_at",
                (run_id,),
            )
            rows = await cursor.fetchall()
            return [self._row_to_result(row) for row in rows]

    # Helper methods to convert database rows to model objects
    def _row_to_project(self, row) -> TestProject:
        """Convert database row to TestProject."""
        return TestProject(
            project_id=row["project_id"],
            name=row["name"],
            description=row["description"] or "",
            app_path=row["app_path"],
            interfaces=[
                InterfaceType(i) for i in json.loads(row["interfaces"] or "[]")
            ],
            test_types=[TestType(t) for t in json.loads(row["test_types"] or "[]")],
            agent_config=json.loads(row["agent_config"] or "{}"),
            discovered_permissions=json.loads(row["discovered_permissions"] or "[]"),
            discovered_endpoints=json.loads(row["discovered_endpoints"] or "[]"),
            discovered_commands=json.loads(row["discovered_commands"] or "[]"),
            created_at=datetime.fromisoformat(row["created_at"]),
            updated_at=(
                datetime.fromisoformat(row["updated_at"]) if row["updated_at"] else None
            ),
            created_by=row["created_by"],
            is_active=bool(row["is_active"]),
            tenant_id=row["tenant_id"],
            tags=json.loads(row["tags"] or "[]"),
            attributes=json.loads(row["attributes"] or "{}"),
            total_test_runs=row["total_test_runs"],
            last_test_run=(
                datetime.fromisoformat(row["last_test_run"])
                if row["last_test_run"]
                else None
            ),
            average_success_rate=row["average_success_rate"],
        )

    def _row_to_run(self, row) -> TestRun:
        """Convert database row to TestRun."""
        return TestRun(
            run_id=row["run_id"],
            project_id=row["project_id"],
            name=row["name"],
            description=row["description"] or "",
            test_types=[TestType(t) for t in json.loads(row["test_types"] or "[]")],
            personas_used=json.loads(row["personas_used"] or "[]"),
            agent_types=[AgentType(a) for a in json.loads(row["agent_types"] or "[]")],
            interfaces_tested=[
                InterfaceType(i) for i in json.loads(row["interfaces_tested"] or "[]")
            ],
            status=TestStatus(row["status"]),
            started_at=(
                datetime.fromisoformat(row["started_at"]) if row["started_at"] else None
            ),
            completed_at=(
                datetime.fromisoformat(row["completed_at"])
                if row["completed_at"]
                else None
            ),
            duration_seconds=row["duration_seconds"],
            total_scenarios=row["total_scenarios"],
            passed_scenarios=row["passed_scenarios"],
            failed_scenarios=row["failed_scenarios"],
            skipped_scenarios=row["skipped_scenarios"],
            success_rate=row["success_rate"],
            ai_insights=json.loads(row["ai_insights"] or "[]"),
            confidence_score=row["confidence_score"],
            agent_consensus=json.loads(row["agent_consensus"] or "{}"),
            created_at=datetime.fromisoformat(row["created_at"]),
            created_by=row["created_by"],
            tenant_id=row["tenant_id"],
            priority=Priority(row["priority"]),
            html_report_path=row["html_report_path"],
            json_report_path=row["json_report_path"],
            error_message=row["error_message"],
            error_details=json.loads(row["error_details"] or "{}"),
        )

    def _row_to_result(self, row) -> TestResult:
        """Convert database row to TestResult."""
        return TestResult(
            result_id=row["result_id"],
            run_id=row["run_id"],
            scenario_id=row["scenario_id"],
            scenario_name=row["scenario_name"],
            test_type=TestType(row["test_type"]),
            persona=row["persona"],
            interface_type=InterfaceType(row["interface_type"]),
            status=TestStatus(row["status"]),
            started_at=datetime.fromisoformat(row["started_at"]),
            completed_at=(
                datetime.fromisoformat(row["completed_at"])
                if row["completed_at"]
                else None
            ),
            duration_ms=row["duration_ms"],
            passed=bool(row["passed"]),
            expected_result=row["expected_result"] or "",
            actual_result=row["actual_result"] or "",
            validation_details=json.loads(row["validation_details"] or "{}"),
            ai_analysis=row["ai_analysis"] or "",
            confidence_score=row["confidence_score"],
            agent_insights=json.loads(row["agent_insights"] or "[]"),
            response_time_ms=row["response_time_ms"],
            memory_usage_mb=row["memory_usage_mb"],
            cpu_usage_percent=row["cpu_usage_percent"],
            error_message=row["error_message"],
            error_traceback=row["error_traceback"],
            tenant_id=row["tenant_id"],
        )


# Singleton database instance
_db_instance: Optional[QADatabase] = None


def get_database(db_path: str = "qa_testing.db") -> QADatabase:
    """Get the singleton database instance."""
    global _db_instance
    if _db_instance is None:
        _db_instance = QADatabase(db_path)
    return _db_instance


async def setup_database(db_path: str = "qa_testing.db"):
    """Setup and initialize the database."""
    db = get_database(db_path)
    await db.initialize()
    return db
