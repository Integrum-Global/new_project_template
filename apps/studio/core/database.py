"""
Studio Database Management - Using Middleware Database Layer

Studio-specific database operations extending the middleware database manager.
Delegates to middleware for common operations while adding Studio-specific features.
"""

import logging
import os
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

from sqlalchemy import and_, func, or_, select
from sqlalchemy.exc import SQLAlchemyError

# Import middleware database components
from kailash.middleware.database import Base, MiddlewareDatabaseManager
from kailash.middleware.database.repositories import (
    BaseRepository,
    MiddlewareExecutionRepository,
    MiddlewareWorkflowRepository,
)

# Import Studio models
from .models import (
    AuditLog,
    ComplianceAssessment,
    ExecutionStatus,
    SecurityEvent,
    StudioWorkflow,
    TemplateCategory,
    WorkflowExecution,
    WorkflowStatus,
    WorkflowTemplate,
)

logger = logging.getLogger(__name__)


class StudioDatabase:
    """Studio database manager using middleware components."""

    def __init__(self, database_url: str = None):
        # Database configuration
        if database_url is None:
            # Use data directory structure from SDK conventions
            app_dir = Path(__file__).parent.parent
            data_dir = app_dir / "data" / "outputs"
            data_dir.mkdir(parents=True, exist_ok=True)
            # Use SQLite with async support
            database_url = f"sqlite+aiosqlite:///{data_dir / 'studio.db'}"

        self.database_url = database_url
        self._initialized = False

        # Use middleware database manager
        self.manager = MiddlewareDatabaseManager(database_url)

        # Initialize repositories with Studio models
        self.workflow_repo = BaseRepository(StudioWorkflow)
        self.execution_repo = BaseRepository(WorkflowExecution)
        self.template_repo = BaseRepository(WorkflowTemplate)
        self.security_event_repo = BaseRepository(SecurityEvent)
        self.audit_repo = BaseRepository(AuditLog)
        self.compliance_repo = BaseRepository(ComplianceAssessment)

    async def initialize(self):
        """Initialize database using middleware manager."""
        if self._initialized:
            return

        try:
            # Create tables using middleware
            await self.manager.create_tables()

            # Verify database connection
            async with self.manager.get_session() as session:
                result = await session.execute(
                    select(func.count()).select_from(StudioWorkflow)
                )
                count = result.scalar()
                logger.info(f"Studio database initialized: {count} workflows found")

            self._initialized = True

        except Exception as e:
            logger.error(f"Failed to initialize database: {str(e)}")
            raise

    async def close(self):
        """Close database connections."""
        await self.manager.close()
        self._initialized = False

    # Workflow Operations

    async def save_workflow(self, workflow: StudioWorkflow) -> StudioWorkflow:
        """Save or update workflow using repository."""
        async with self.manager.get_session(workflow.tenant_id) as session:
            try:
                # Check if exists
                existing = await self.workflow_repo.get(session, workflow.workflow_id)

                if existing:
                    # Update existing
                    workflow_dict = workflow.to_dict()
                    workflow = await self.workflow_repo.update(
                        session, existing, **workflow_dict
                    )
                else:
                    # Create new - need to handle the object differently
                    session.add(workflow)
                    await session.flush()

                # Log audit event
                await self._log_audit_event(
                    session,
                    action="update" if existing else "create",
                    resource_type="workflow",
                    resource_id=workflow.workflow_id,
                    workflow_id=workflow.workflow_id,
                    user_id=workflow.updated_by or workflow.created_by,
                    tenant_id=workflow.tenant_id,
                    success=True,
                    changes={
                        "name": workflow.name,
                        "status": workflow.status.value if workflow.status else None,
                    },
                )

                return workflow

            except SQLAlchemyError as e:
                logger.error(f"Failed to save workflow: {str(e)}")
                raise

    async def get_workflow(
        self, workflow_id: str, tenant_id: str = "default"
    ) -> Optional[StudioWorkflow]:
        """Get workflow by ID with tenant isolation."""
        async with self.manager.get_session(tenant_id) as session:
            workflow = await self.workflow_repo.get(session, workflow_id)
            if workflow and workflow.tenant_id == tenant_id and not workflow.is_deleted:
                return workflow
            return None

    async def list_workflows(
        self,
        tenant_id: str = "default",
        status: WorkflowStatus = None,
        owner_id: str = None,
        limit: int = 100,
        offset: int = 0,
    ) -> List[StudioWorkflow]:
        """List workflows with filtering and pagination."""
        async with self.manager.get_session(tenant_id) as session:
            query = select(StudioWorkflow).where(
                and_(
                    StudioWorkflow.tenant_id == tenant_id,
                    StudioWorkflow.deleted_at.is_(None),
                )
            )

            if status:
                query = query.where(StudioWorkflow.status == status)
            if owner_id:
                query = query.where(StudioWorkflow.owner_id == owner_id)

            query = query.order_by(StudioWorkflow.created_at.desc())
            query = query.limit(limit).offset(offset)

            result = await session.execute(query)
            return result.scalars().all()

    async def delete_workflow(
        self, workflow_id: str, tenant_id: str = "default", deleted_by: str = None
    ) -> bool:
        """Soft delete workflow with audit trail."""
        async with self.manager.get_session(tenant_id) as session:
            workflow = await self.workflow_repo.get(session, workflow_id)
            if not workflow or workflow.tenant_id != tenant_id:
                return False

            # Soft delete using repository
            await self.workflow_repo.soft_delete(session, workflow, deleted_by)

            # Log audit event
            await self._log_audit_event(
                session,
                action="delete",
                resource_type="workflow",
                resource_id=workflow_id,
                workflow_id=workflow_id,
                user_id=deleted_by,
                tenant_id=tenant_id,
                success=True,
            )

            return True

    # Execution Operations

    async def save_execution(self, execution: WorkflowExecution) -> WorkflowExecution:
        """Save or update execution."""
        async with self.manager.get_session(execution.tenant_id) as session:
            try:
                existing = await self.execution_repo.get(
                    session, execution.execution_id
                )

                if existing:
                    execution_dict = execution.to_dict()
                    execution = await self.execution_repo.update(
                        session, existing, **execution_dict
                    )
                else:
                    session.add(execution)
                    await session.flush()

                return execution

            except SQLAlchemyError as e:
                logger.error(f"Failed to save execution: {str(e)}")
                raise

    async def get_execution(
        self, execution_id: str, tenant_id: str = "default"
    ) -> Optional[WorkflowExecution]:
        """Get execution by ID."""
        async with self.manager.get_session(tenant_id) as session:
            execution = await self.execution_repo.get(session, execution_id)
            if execution and execution.tenant_id == tenant_id:
                return execution
            return None

    async def list_executions(
        self,
        workflow_id: str = None,
        tenant_id: str = "default",
        status: ExecutionStatus = None,
        limit: int = 100,
        offset: int = 0,
    ) -> List[WorkflowExecution]:
        """List executions with filtering."""
        async with self.manager.get_session(tenant_id) as session:
            query = select(WorkflowExecution).where(
                WorkflowExecution.tenant_id == tenant_id
            )

            if workflow_id:
                query = query.where(WorkflowExecution.workflow_id == workflow_id)
            if status:
                query = query.where(WorkflowExecution.status == status)

            query = query.order_by(WorkflowExecution.created_at.desc())
            query = query.limit(limit).offset(offset)

            result = await session.execute(query)
            return result.scalars().all()

    # Template Operations

    async def save_template(self, template: WorkflowTemplate) -> WorkflowTemplate:
        """Save or update template."""
        async with self.manager.get_session(template.tenant_id) as session:
            try:
                existing = await self.template_repo.get(session, template.template_id)

                if existing:
                    template_dict = template.to_dict()
                    template = await self.template_repo.update(
                        session, existing, **template_dict
                    )
                else:
                    session.add(template)
                    await session.flush()

                return template

            except SQLAlchemyError as e:
                logger.error(f"Failed to save template: {str(e)}")
                raise

    async def get_template(self, template_id: str) -> Optional[WorkflowTemplate]:
        """Get template by ID."""
        async with self.manager.get_session() as session:
            return await self.template_repo.get(session, template_id)

    async def list_templates(
        self,
        category: TemplateCategory = None,
        tenant_id: str = "default",
        include_public: bool = True,
    ) -> List[WorkflowTemplate]:
        """List templates with filtering."""
        async with self.manager.get_session(tenant_id) as session:
            query = select(WorkflowTemplate)

            if include_public:
                query = query.where(
                    or_(
                        WorkflowTemplate.tenant_id == tenant_id,
                        WorkflowTemplate.is_public == True,
                    )
                )
            else:
                query = query.where(WorkflowTemplate.tenant_id == tenant_id)

            if category:
                query = query.where(WorkflowTemplate.category == category)

            query = query.where(WorkflowTemplate.deleted_at.is_(None))
            query = query.order_by(WorkflowTemplate.usage_count.desc())

            result = await session.execute(query)
            return result.scalars().all()

    # Statistics and Maintenance

    async def get_stats(self, tenant_id: str = "default") -> Dict[str, Any]:
        """Get database statistics."""
        async with self.manager.get_session(tenant_id) as session:
            # Workflow stats
            workflow_count = await session.execute(
                select(func.count())
                .select_from(StudioWorkflow)
                .where(
                    and_(
                        StudioWorkflow.tenant_id == tenant_id,
                        StudioWorkflow.deleted_at.is_(None),
                    )
                )
            )

            workflow_by_status = await session.execute(
                select(StudioWorkflow.status, func.count())
                .select_from(StudioWorkflow)
                .where(
                    and_(
                        StudioWorkflow.tenant_id == tenant_id,
                        StudioWorkflow.deleted_at.is_(None),
                    )
                )
                .group_by(StudioWorkflow.status)
            )

            # Execution stats
            execution_count = await session.execute(
                select(func.count())
                .select_from(WorkflowExecution)
                .where(WorkflowExecution.tenant_id == tenant_id)
            )

            execution_by_status = await session.execute(
                select(WorkflowExecution.status, func.count())
                .select_from(WorkflowExecution)
                .where(WorkflowExecution.tenant_id == tenant_id)
                .group_by(WorkflowExecution.status)
            )

            # Template stats
            template_count = await session.execute(
                select(func.count())
                .select_from(WorkflowTemplate)
                .where(
                    or_(
                        WorkflowTemplate.tenant_id == tenant_id,
                        WorkflowTemplate.is_public == True,
                    )
                )
            )

            template_by_category = await session.execute(
                select(WorkflowTemplate.category, func.count())
                .select_from(WorkflowTemplate)
                .where(
                    or_(
                        WorkflowTemplate.tenant_id == tenant_id,
                        WorkflowTemplate.is_public == True,
                    )
                )
                .group_by(WorkflowTemplate.category)
            )

            return {
                "workflows": {
                    "total": workflow_count.scalar() or 0,
                    "by_status": {
                        status.value: count
                        for status, count in workflow_by_status.all()
                    },
                },
                "executions": {
                    "total": execution_count.scalar() or 0,
                    "by_status": {
                        status.value: count
                        for status, count in execution_by_status.all()
                    },
                },
                "templates": {
                    "total": template_count.scalar() or 0,
                    "by_category": {
                        category.value: count
                        for category, count in template_by_category.all()
                    },
                },
            }

    async def cleanup_old_executions(
        self, days: int = 30, tenant_id: str = "default"
    ) -> int:
        """Clean up old executions."""
        cutoff_date = datetime.now(timezone.utc) - timedelta(days=days)

        async with self.manager.get_session(tenant_id) as session:
            # Delete old executions
            result = await session.execute(
                select(WorkflowExecution).where(
                    and_(
                        WorkflowExecution.tenant_id == tenant_id,
                        WorkflowExecution.created_at < cutoff_date,
                        WorkflowExecution.status.in_(
                            [
                                ExecutionStatus.COMPLETED,
                                ExecutionStatus.FAILED,
                                ExecutionStatus.CANCELLED,
                            ]
                        ),
                    )
                )
            )

            executions_to_delete = result.scalars().all()
            deleted_count = len(executions_to_delete)

            for execution in executions_to_delete:
                await session.delete(execution)

            await session.commit()

            logger.info(f"Cleaned up {deleted_count} old executions")
            return deleted_count

    # Private helper methods

    async def _log_audit_event(self, session, **kwargs):
        """Log audit event using repository."""
        try:
            audit = AuditLog(**kwargs)
            session.add(audit)
            await session.flush()
        except Exception as e:
            logger.error(f"Failed to log audit event: {e}")


# SDK Enhancement Suggestions
"""
The following database patterns from Studio should be added to middleware:

1. Soft Delete Pattern
   - Currently implemented in Studio models
   - Should be in middleware SoftDeleteMixin

2. Multi-tenant Query Filtering
   - Currently manual in each query
   - Should be automatic in middleware repositories

3. Audit Trail Creation
   - Currently manual after each operation
   - Should be automatic via middleware event listeners

4. Statistics Aggregation
   - Common pattern across all apps
   - Should be in middleware StatsRepository

5. Cleanup Operations
   - Generic pattern for old data removal
   - Should be in middleware MaintenanceRepository

By moving these to middleware, Studio's database.py would shrink
from 500+ lines to ~100 lines of app-specific logic only.
"""
