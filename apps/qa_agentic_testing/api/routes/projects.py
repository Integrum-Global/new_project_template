"""
Project management API routes.
"""

from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field

from ...core.models import InterfaceType, TestProject, TestType
from ...core.services import ProjectService

router = APIRouter()


class CreateProjectRequest(BaseModel):
    """Request model for creating a project."""

    name: str = Field(..., description="Project name")
    app_path: str = Field(..., description="Path to the application under test")
    description: str = Field("", description="Project description")
    interfaces: Optional[List[str]] = Field(None, description="Interface types to test")
    test_types: Optional[List[str]] = Field(None, description="Test types to include")
    agent_config: Optional[Dict[str, Any]] = Field(
        None, description="Agent configuration"
    )
    tags: Optional[List[str]] = Field(None, description="Project tags")
    tenant_id: str = Field("default", description="Tenant ID")


class UpdateProjectRequest(BaseModel):
    """Request model for updating a project."""

    name: Optional[str] = None
    description: Optional[str] = None
    interfaces: Optional[List[str]] = None
    test_types: Optional[List[str]] = None
    agent_config: Optional[Dict[str, Any]] = None
    tags: Optional[List[str]] = None


class ProjectResponse(BaseModel):
    """Response model for project data."""

    project_id: str
    name: str
    description: str
    app_path: str
    interfaces: List[str]
    test_types: List[str]
    agent_config: Dict[str, Any]
    discovered_permissions: List[str]
    discovered_endpoints: List[str]
    discovered_commands: List[str]
    created_at: str
    updated_at: Optional[str]
    created_by: Optional[str]
    is_active: bool
    tenant_id: str
    tags: List[str]
    attributes: Dict[str, Any]
    total_test_runs: int
    last_test_run: Optional[str]
    average_success_rate: float


def get_project_service() -> ProjectService:
    """Dependency to get project service."""
    return ProjectService()


@router.post("/", response_model=ProjectResponse)
async def create_project(
    request: CreateProjectRequest,
    service: ProjectService = Depends(get_project_service),
):
    """Create a new test project."""
    try:
        # Convert string enums to proper enums
        kwargs = {}
        if request.interfaces:
            kwargs["interfaces"] = [InterfaceType(i) for i in request.interfaces]
        if request.test_types:
            kwargs["test_types"] = [TestType(t) for t in request.test_types]
        if request.agent_config:
            kwargs["agent_config"] = request.agent_config
        if request.tags:
            kwargs["tags"] = request.tags
        kwargs["tenant_id"] = request.tenant_id

        project = await service.create_project(
            name=request.name,
            app_path=request.app_path,
            description=request.description,
            **kwargs,
        )

        return ProjectResponse(**project.to_dict())

    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/", response_model=List[ProjectResponse])
async def list_projects(
    tenant_id: str = Query("default", description="Tenant ID"),
    is_active: bool = Query(True, description="Filter by active status"),
    service: ProjectService = Depends(get_project_service),
):
    """List all projects."""
    try:
        projects = await service.list_projects(tenant_id, is_active)
        return [ProjectResponse(**p.to_dict()) for p in projects]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{project_id}", response_model=ProjectResponse)
async def get_project(
    project_id: str, service: ProjectService = Depends(get_project_service)
):
    """Get a project by ID."""
    try:
        project = await service.get_project(project_id)
        if not project:
            raise HTTPException(status_code=404, detail="Project not found")

        return ProjectResponse(**project.to_dict())
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.patch("/{project_id}", response_model=ProjectResponse)
async def update_project(
    project_id: str,
    request: UpdateProjectRequest,
    service: ProjectService = Depends(get_project_service),
):
    """Update a project."""
    try:
        # Build updates dict, excluding None values
        updates = {}
        if request.name is not None:
            updates["name"] = request.name
        if request.description is not None:
            updates["description"] = request.description
        if request.interfaces is not None:
            updates["interfaces"] = [InterfaceType(i).value for i in request.interfaces]
        if request.test_types is not None:
            updates["test_types"] = [TestType(t).value for t in request.test_types]
        if request.agent_config is not None:
            updates["agent_config"] = request.agent_config
        if request.tags is not None:
            updates["tags"] = request.tags

        project = await service.update_project(project_id, updates)
        if not project:
            raise HTTPException(status_code=404, detail="Project not found")

        return ProjectResponse(**project.to_dict())
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/{project_id}")
async def delete_project(
    project_id: str, service: ProjectService = Depends(get_project_service)
):
    """Delete (deactivate) a project."""
    try:
        success = await service.delete_project(project_id)
        if not success:
            raise HTTPException(status_code=404, detail="Project not found")

        return {"message": "Project deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{project_id}/discover", response_model=ProjectResponse)
async def rediscover_project(
    project_id: str, service: ProjectService = Depends(get_project_service)
):
    """Re-run discovery for a project."""
    try:
        project = await service.discover_project(project_id)
        if not project:
            raise HTTPException(status_code=404, detail="Project not found")

        return ProjectResponse(**project.to_dict())
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{project_id}/summary")
async def get_project_summary(
    project_id: str, service: ProjectService = Depends(get_project_service)
):
    """Get project summary with recent runs."""
    try:
        from ...core.services import AnalyticsService, TestRunService

        project = await service.get_project(project_id)
        if not project:
            raise HTTPException(status_code=404, detail="Project not found")

        # Get recent runs and analytics
        run_service = TestRunService()
        analytics_service = AnalyticsService()

        recent_runs = await run_service.list_runs(project_id=project_id, limit=5)
        analytics = await analytics_service.get_project_analytics(project_id, days=30)

        return {
            "project": project.to_dict(),
            "recent_runs": [r.to_dict() for r in recent_runs],
            "analytics": analytics,
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
