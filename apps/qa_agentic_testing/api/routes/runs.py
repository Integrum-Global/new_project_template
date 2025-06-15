"""
Test run management API routes.
"""

from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field

from ...core.models import AgentType, InterfaceType, Priority, TestRun, TestType
from ...core.services import TestRunService

router = APIRouter()


class CreateRunRequest(BaseModel):
    """Request model for creating a test run."""

    project_id: str = Field(..., description="Project ID")
    name: str = Field(..., description="Test run name")
    description: str = Field("", description="Test run description")
    test_types: Optional[List[str]] = Field(None, description="Test types to include")
    agent_types: Optional[List[str]] = Field(None, description="Agent types to use")
    personas_used: Optional[List[str]] = Field(None, description="Personas to use")
    interfaces_tested: Optional[List[str]] = Field(
        None, description="Interfaces to test"
    )
    priority: str = Field("medium", description="Test run priority")
    tenant_id: str = Field("default", description="Tenant ID")


class TestRunResponse(BaseModel):
    """Response model for test run data."""

    run_id: str
    project_id: str
    name: str
    description: str
    test_types: List[str]
    personas_used: List[str]
    agent_types: List[str]
    interfaces_tested: List[str]
    status: str
    started_at: Optional[str]
    completed_at: Optional[str]
    duration_seconds: Optional[float]
    total_scenarios: int
    passed_scenarios: int
    failed_scenarios: int
    skipped_scenarios: int
    success_rate: float
    ai_insights: List[str]
    confidence_score: float
    agent_consensus: Dict[str, Any]
    created_at: str
    created_by: Optional[str]
    tenant_id: str
    priority: str
    html_report_path: Optional[str]
    json_report_path: Optional[str]
    error_message: Optional[str]
    error_details: Dict[str, Any]


def get_run_service() -> TestRunService:
    """Dependency to get test run service."""
    return TestRunService()


@router.post("/", response_model=TestRunResponse)
async def create_run(
    request: CreateRunRequest, service: TestRunService = Depends(get_run_service)
):
    """Create a new test run."""
    try:
        # Convert string enums to proper enums
        kwargs = {}
        if request.test_types:
            kwargs["test_types"] = [TestType(t) for t in request.test_types]
        if request.agent_types:
            kwargs["agent_types"] = [AgentType(a) for a in request.agent_types]
        if request.personas_used:
            kwargs["personas_used"] = request.personas_used
        if request.interfaces_tested:
            kwargs["interfaces_tested"] = [
                InterfaceType(i) for i in request.interfaces_tested
            ]
        kwargs["priority"] = Priority(request.priority)
        kwargs["tenant_id"] = request.tenant_id

        run = await service.create_run(
            project_id=request.project_id,
            name=request.name,
            description=request.description,
            **kwargs,
        )

        return TestRunResponse(**run.to_dict())

    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/", response_model=List[TestRunResponse])
async def list_runs(
    project_id: Optional[str] = Query(None, description="Filter by project ID"),
    tenant_id: str = Query("default", description="Tenant ID"),
    limit: int = Query(50, description="Maximum number of runs to return"),
    service: TestRunService = Depends(get_run_service),
):
    """List test runs."""
    try:
        runs = await service.list_runs(project_id, tenant_id, limit)
        return [TestRunResponse(**r.to_dict()) for r in runs]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{run_id}", response_model=TestRunResponse)
async def get_run(run_id: str, service: TestRunService = Depends(get_run_service)):
    """Get a test run by ID."""
    try:
        run = await service.get_run(run_id)
        if not run:
            raise HTTPException(status_code=404, detail="Test run not found")

        return TestRunResponse(**run.to_dict())
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{run_id}/start", response_model=TestRunResponse)
async def start_run(run_id: str, service: TestRunService = Depends(get_run_service)):
    """Start a test run.

    Test results will be stored in the target application's qa_results folder
    based on the project's app_path. Reports and logs will be saved as:
    - <app_path>/qa_results/test_report_{run_id}.html
    - <app_path>/qa_results/test_report_{run_id}.json
    """
    try:
        run = await service.start_run(run_id)
        return TestRunResponse(**run.to_dict())
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/{run_id}/cancel", response_model=TestRunResponse)
async def cancel_run(run_id: str, service: TestRunService = Depends(get_run_service)):
    """Cancel a running test run."""
    try:
        run = await service.cancel_run(run_id)
        return TestRunResponse(**run.to_dict())
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/{run_id}/status")
async def get_run_status(
    run_id: str, service: TestRunService = Depends(get_run_service)
):
    """Get the current status of a test run."""
    try:
        run = await service.get_run(run_id)
        if not run:
            raise HTTPException(status_code=404, detail="Test run not found")

        return {
            "run_id": run.run_id,
            "status": run.status.value,
            "progress": {
                "total_scenarios": run.total_scenarios,
                "completed_scenarios": run.passed_scenarios + run.failed_scenarios,
                "passed_scenarios": run.passed_scenarios,
                "failed_scenarios": run.failed_scenarios,
                "success_rate": run.success_rate,
            },
            "timing": {
                "started_at": run.started_at.isoformat() if run.started_at else None,
                "completed_at": (
                    run.completed_at.isoformat() if run.completed_at else None
                ),
                "duration_seconds": run.duration_seconds,
            },
            "error": (
                {"message": run.error_message, "details": run.error_details}
                if run.error_message
                else None
            ),
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{run_id}/logs")
async def get_run_logs(run_id: str, service: TestRunService = Depends(get_run_service)):
    """Get logs for a test run."""
    try:
        # In a real implementation, you would fetch logs from a logging system
        # For now, return basic information
        run = await service.get_run(run_id)
        if not run:
            raise HTTPException(status_code=404, detail="Test run not found")

        # Mock log entries - in production, integrate with actual logging
        logs = [
            {
                "timestamp": run.created_at.isoformat(),
                "level": "INFO",
                "message": f"Test run '{run.name}' created",
            }
        ]

        if run.started_at:
            logs.append(
                {
                    "timestamp": run.started_at.isoformat(),
                    "level": "INFO",
                    "message": f"Test run '{run.name}' started",
                }
            )

        if run.completed_at:
            logs.append(
                {
                    "timestamp": run.completed_at.isoformat(),
                    "level": "INFO" if run.status.value == "completed" else "ERROR",
                    "message": f"Test run '{run.name}' {run.status.value}",
                }
            )

        if run.error_message:
            logs.append(
                {
                    "timestamp": (
                        run.completed_at.isoformat()
                        if run.completed_at
                        else run.created_at.isoformat()
                    ),
                    "level": "ERROR",
                    "message": run.error_message,
                }
            )

        return {
            "run_id": run.run_id,
            "logs": sorted(logs, key=lambda x: x["timestamp"]),
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
