"""
Analytics API routes.
"""

from typing import Any, Dict

from fastapi import APIRouter, Depends, HTTPException, Query

from ...core.services import AnalyticsService

router = APIRouter()


def get_analytics_service() -> AnalyticsService:
    """Dependency to get analytics service."""
    return AnalyticsService()


@router.get("/projects/{project_id}")
async def get_project_analytics(
    project_id: str,
    days: int = Query(30, description="Number of days to analyze"),
    service: AnalyticsService = Depends(get_analytics_service),
):
    """Get analytics for a specific project."""
    try:
        analytics = await service.get_project_analytics(project_id, days)
        return analytics
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/global")
async def get_global_analytics(
    tenant_id: str = Query("default", description="Tenant ID"),
    days: int = Query(30, description="Number of days to analyze"),
    service: AnalyticsService = Depends(get_analytics_service),
):
    """Get global analytics across all projects."""
    try:
        analytics = await service.get_global_analytics(tenant_id, days)
        return analytics
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/trends/success-rate")
async def get_success_rate_trends(
    project_id: str = Query(None, description="Project ID (optional)"),
    tenant_id: str = Query("default", description="Tenant ID"),
    days: int = Query(30, description="Number of days to analyze"),
    service: AnalyticsService = Depends(get_analytics_service),
):
    """Get success rate trends over time."""
    try:
        if project_id:
            analytics = await service.get_project_analytics(project_id, days)
            return {
                "project_id": project_id,
                "period_days": days,
                "success_rate_trend": analytics["success_rate_trend"],
                "current_average": analytics["success_rate"],
            }
        else:
            analytics = await service.get_global_analytics(tenant_id, days)
            return {
                "tenant_id": tenant_id,
                "period_days": days,
                "average_success_rate": analytics["average_success_rate"],
                "projects": analytics["projects"],
            }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/performance/trends")
async def get_performance_trends(
    project_id: str = Query(None, description="Project ID (optional)"),
    tenant_id: str = Query("default", description="Tenant ID"),
    days: int = Query(30, description="Number of days to analyze"),
    service: AnalyticsService = Depends(get_analytics_service),
):
    """Get performance trends over time."""
    try:
        if project_id:
            analytics = await service.get_project_analytics(project_id, days)
            return {
                "project_id": project_id,
                "period_days": days,
                "performance_trend": analytics["performance_trend"],
                "average_duration": analytics["average_duration_seconds"],
            }
        else:
            # For global trends, aggregate from all projects
            global_analytics = await service.get_global_analytics(tenant_id, days)
            projects = global_analytics["projects"]

            # Get detailed analytics for each project
            performance_data = []
            for project in projects:
                if project["completed_runs"] > 0:
                    project_analytics = await service.get_project_analytics(
                        project["project_id"], days
                    )
                    performance_data.append(
                        {
                            "project_id": project["project_id"],
                            "project_name": project["name"],
                            "average_duration": project_analytics.get(
                                "average_duration_seconds", 0
                            ),
                            "performance_trend": project_analytics.get(
                                "performance_trend", []
                            ),
                        }
                    )

            return {
                "tenant_id": tenant_id,
                "period_days": days,
                "projects": performance_data,
            }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/summary")
async def get_analytics_summary(
    tenant_id: str = Query("default", description="Tenant ID"),
    service: AnalyticsService = Depends(get_analytics_service),
):
    """Get a comprehensive analytics summary."""
    try:
        # Get analytics for different time periods
        last_7_days = await service.get_global_analytics(tenant_id, 7)
        last_30_days = await service.get_global_analytics(tenant_id, 30)
        last_90_days = await service.get_global_analytics(tenant_id, 90)

        # Calculate trends
        success_rate_change_7d = (
            last_7_days["average_success_rate"] - last_30_days["average_success_rate"]
        )
        total_runs_7d = last_7_days["total_runs"]
        total_runs_30d = last_30_days["total_runs"]

        return {
            "tenant_id": tenant_id,
            "summary": {
                "total_projects": last_30_days["total_projects"],
                "total_runs_last_30_days": total_runs_30d,
                "total_runs_last_7_days": total_runs_7d,
                "average_success_rate": last_30_days["average_success_rate"],
                "success_rate_change_7d": success_rate_change_7d,
            },
            "periods": {
                "last_7_days": last_7_days,
                "last_30_days": last_30_days,
                "last_90_days": last_90_days,
            },
            "top_projects": sorted(
                last_30_days["projects"], key=lambda p: p["success_rate"], reverse=True
            )[:5],
            "active_projects": [
                p for p in last_30_days["projects"] if p["total_runs"] > 0
            ],
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/health")
async def get_system_health(
    tenant_id: str = Query("default", description="Tenant ID"),
    service: AnalyticsService = Depends(get_analytics_service),
):
    """Get system health metrics."""
    try:
        from ...core.services import ProjectService, TestRunService

        # Get basic counts
        project_service = ProjectService()
        run_service = TestRunService()

        projects = await project_service.list_projects(tenant_id)
        recent_runs = await run_service.list_runs(tenant_id=tenant_id, limit=50)

        # Calculate health metrics
        active_projects = len([p for p in projects if p.is_active])
        recent_successful_runs = len(
            [r for r in recent_runs if r.status.value == "completed"]
        )
        recent_failed_runs = len([r for r in recent_runs if r.status.value == "failed"])

        health_score = 100
        if recent_runs:
            failure_rate = recent_failed_runs / len(recent_runs)
            health_score = max(0, 100 - (failure_rate * 100))

        status = "healthy"
        if health_score < 50:
            status = "unhealthy"
        elif health_score < 80:
            status = "degraded"

        return {
            "tenant_id": tenant_id,
            "status": status,
            "health_score": health_score,
            "metrics": {
                "total_projects": len(projects),
                "active_projects": active_projects,
                "recent_runs": len(recent_runs),
                "successful_runs": recent_successful_runs,
                "failed_runs": recent_failed_runs,
                "failure_rate": (
                    recent_failed_runs / len(recent_runs) if recent_runs else 0
                ),
            },
            "recommendations": _get_health_recommendations(
                health_score, recent_runs, projects
            ),
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


def _get_health_recommendations(
    health_score: float, recent_runs: list, projects: list
) -> list:
    """Generate health recommendations based on metrics."""
    recommendations = []

    if health_score < 80:
        recommendations.append(
            "System health is below optimal. Consider reviewing failed test runs."
        )

    if not recent_runs:
        recommendations.append(
            "No recent test activity. Consider running tests for active projects."
        )

    inactive_projects = len([p for p in projects if not p.is_active])
    if inactive_projects > len(projects) * 0.5:
        recommendations.append(
            f"Many projects ({inactive_projects}) are inactive. Consider archiving or reactivating them."
        )

    failed_runs = [r for r in recent_runs if r.status.value == "failed"]
    if len(failed_runs) > len(recent_runs) * 0.3:
        recommendations.append(
            "High failure rate detected. Review test configurations and application stability."
        )

    if len(recommendations) == 0:
        recommendations.append("System is running optimally!")

    return recommendations
