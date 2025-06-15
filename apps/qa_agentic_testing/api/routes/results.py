"""
Test results API routes.
"""

from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel

from ...core.services import TestResultService

router = APIRouter()


class TestResultResponse(BaseModel):
    """Response model for test result data."""

    result_id: str
    run_id: str
    scenario_id: str
    scenario_name: str
    test_type: str
    persona: str
    interface_type: str
    status: str
    started_at: str
    completed_at: Optional[str]
    duration_ms: Optional[int]
    passed: bool
    expected_result: str
    actual_result: str
    validation_details: Dict[str, Any]
    ai_analysis: str
    confidence_score: float
    agent_insights: List[str]
    response_time_ms: Optional[int]
    memory_usage_mb: Optional[float]
    cpu_usage_percent: Optional[float]
    error_message: Optional[str]
    error_traceback: Optional[str]
    tenant_id: str


def get_result_service() -> TestResultService:
    """Dependency to get test result service."""
    return TestResultService()


@router.get("/run/{run_id}", response_model=List[TestResultResponse])
async def list_results_for_run(
    run_id: str, service: TestResultService = Depends(get_result_service)
):
    """List all test results for a specific run."""
    try:
        results = await service.list_results(run_id)
        return [TestResultResponse(**r.to_dict()) for r in results]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/run/{run_id}/summary")
async def get_run_results_summary(
    run_id: str, service: TestResultService = Depends(get_result_service)
):
    """Get summary of test results for a run."""
    try:
        summary = await service.get_run_summary(run_id)
        return summary
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/run/{run_id}/failed", response_model=List[TestResultResponse])
async def get_failed_results(
    run_id: str, service: TestResultService = Depends(get_result_service)
):
    """Get only failed test results for a run."""
    try:
        results = await service.list_results(run_id)
        failed_results = [r for r in results if not r.passed]
        return [TestResultResponse(**r.to_dict()) for r in failed_results]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/run/{run_id}/by-type")
async def get_results_by_type(
    run_id: str, service: TestResultService = Depends(get_result_service)
):
    """Get test results grouped by test type."""
    try:
        results = await service.list_results(run_id)

        # Group results by test type
        by_type = {}
        for result in results:
            test_type = result.test_type.value
            if test_type not in by_type:
                by_type[test_type] = {
                    "test_type": test_type,
                    "total": 0,
                    "passed": 0,
                    "failed": 0,
                    "success_rate": 0.0,
                    "average_confidence": 0.0,
                    "results": [],
                }

            by_type[test_type]["total"] += 1
            by_type[test_type]["results"].append(result.to_dict())

            if result.passed:
                by_type[test_type]["passed"] += 1
            else:
                by_type[test_type]["failed"] += 1

        # Calculate metrics for each type
        for test_type, data in by_type.items():
            if data["total"] > 0:
                data["success_rate"] = (data["passed"] / data["total"]) * 100
                data["average_confidence"] = (
                    sum(r["confidence_score"] for r in data["results"]) / data["total"]
                )

        return list(by_type.values())

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/run/{run_id}/by-persona")
async def get_results_by_persona(
    run_id: str, service: TestResultService = Depends(get_result_service)
):
    """Get test results grouped by persona."""
    try:
        results = await service.list_results(run_id)

        # Group results by persona
        by_persona = {}
        for result in results:
            persona = result.persona
            if persona not in by_persona:
                by_persona[persona] = {
                    "persona": persona,
                    "total": 0,
                    "passed": 0,
                    "failed": 0,
                    "success_rate": 0.0,
                    "average_confidence": 0.0,
                    "results": [],
                }

            by_persona[persona]["total"] += 1
            by_persona[persona]["results"].append(result.to_dict())

            if result.passed:
                by_persona[persona]["passed"] += 1
            else:
                by_persona[persona]["failed"] += 1

        # Calculate metrics for each persona
        for persona, data in by_persona.items():
            if data["total"] > 0:
                data["success_rate"] = (data["passed"] / data["total"]) * 100
                data["average_confidence"] = (
                    sum(r["confidence_score"] for r in data["results"]) / data["total"]
                )

        return list(by_persona.values())

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/run/{run_id}/performance")
async def get_performance_metrics(
    run_id: str, service: TestResultService = Depends(get_result_service)
):
    """Get performance metrics for a test run."""
    try:
        results = await service.list_results(run_id)

        # Calculate performance metrics
        response_times = [
            r.response_time_ms for r in results if r.response_time_ms is not None
        ]
        memory_usage = [
            r.memory_usage_mb for r in results if r.memory_usage_mb is not None
        ]
        cpu_usage = [
            r.cpu_usage_percent for r in results if r.cpu_usage_percent is not None
        ]

        metrics = {
            "response_time": {
                "count": len(response_times),
                "average_ms": (
                    sum(response_times) / len(response_times) if response_times else 0
                ),
                "min_ms": min(response_times) if response_times else 0,
                "max_ms": max(response_times) if response_times else 0,
                "p95_ms": (
                    sorted(response_times)[int(len(response_times) * 0.95)]
                    if response_times
                    else 0
                ),
            },
            "memory_usage": {
                "count": len(memory_usage),
                "average_mb": (
                    sum(memory_usage) / len(memory_usage) if memory_usage else 0
                ),
                "min_mb": min(memory_usage) if memory_usage else 0,
                "max_mb": max(memory_usage) if memory_usage else 0,
            },
            "cpu_usage": {
                "count": len(cpu_usage),
                "average_percent": sum(cpu_usage) / len(cpu_usage) if cpu_usage else 0,
                "min_percent": min(cpu_usage) if cpu_usage else 0,
                "max_percent": max(cpu_usage) if cpu_usage else 0,
            },
        }

        return metrics

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/run/{run_id}/insights")
async def get_ai_insights(
    run_id: str, service: TestResultService = Depends(get_result_service)
):
    """Get AI insights and analysis for a test run."""
    try:
        results = await service.list_results(run_id)

        # Aggregate AI insights
        all_insights = []
        confidence_scores = []

        for result in results:
            if result.ai_analysis:
                all_insights.append(
                    {
                        "scenario": result.scenario_name,
                        "test_type": result.test_type.value,
                        "persona": result.persona,
                        "analysis": result.ai_analysis,
                        "confidence": result.confidence_score,
                        "passed": result.passed,
                    }
                )

            confidence_scores.append(result.confidence_score)
            all_insights.extend(
                [
                    {
                        "type": "agent_insight",
                        "content": insight,
                        "scenario": result.scenario_name,
                    }
                    for insight in result.agent_insights
                ]
            )

        # Calculate overall confidence
        avg_confidence = (
            sum(confidence_scores) / len(confidence_scores) if confidence_scores else 0
        )

        return {
            "overall_confidence": avg_confidence,
            "total_insights": len(all_insights),
            "insights": all_insights,
            "confidence_distribution": {
                "high": len([c for c in confidence_scores if c >= 80]),
                "medium": len([c for c in confidence_scores if 50 <= c < 80]),
                "low": len([c for c in confidence_scores if c < 50]),
            },
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
