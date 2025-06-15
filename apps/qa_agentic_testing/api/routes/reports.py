"""
Report generation API routes.
"""

from pathlib import Path
from typing import Any, Dict

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import FileResponse, JSONResponse

from ...core.services import ReportService

router = APIRouter()


def get_report_service() -> ReportService:
    """Dependency to get report service."""
    return ReportService()


@router.get("/run/{run_id}/html")
async def download_html_report(
    run_id: str, service: ReportService = Depends(get_report_service)
):
    """Download HTML report for a test run."""
    try:
        report_path = await service.generate_run_report(run_id, "html")

        if not report_path.exists():
            raise HTTPException(status_code=404, detail="Report not found")

        return FileResponse(
            path=str(report_path),
            filename=f"test_run_{run_id}_report.html",
            media_type="text/html",
        )

    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/run/{run_id}/json")
async def download_json_report(
    run_id: str, service: ReportService = Depends(get_report_service)
):
    """Download JSON report for a test run."""
    try:
        report_path = await service.generate_run_report(run_id, "json")

        if not report_path.exists():
            raise HTTPException(status_code=404, detail="Report not found")

        return FileResponse(
            path=str(report_path),
            filename=f"test_run_{run_id}_report.json",
            media_type="application/json",
        )

    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/run/{run_id}/data")
async def get_report_data(
    run_id: str, service: ReportService = Depends(get_report_service)
):
    """Get structured report data for a test run."""
    try:
        report_data = await service.get_report_data(run_id)
        return report_data

    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/run/{run_id}/generate")
async def generate_report(
    run_id: str,
    format: str = Query("html", description="Report format (html, json)"),
    service: ReportService = Depends(get_report_service),
):
    """Generate a new report for a test run."""
    try:
        if format not in ["html", "json"]:
            raise HTTPException(
                status_code=400, detail="Invalid format. Use 'html' or 'json'"
            )

        report_path = await service.generate_run_report(run_id, format)

        return {
            "run_id": run_id,
            "format": format,
            "report_path": str(report_path),
            "download_url": f"/api/reports/run/{run_id}/{format}",
            "size_bytes": report_path.stat().st_size if report_path.exists() else 0,
        }

    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/run/{run_id}/preview")
async def preview_report(
    run_id: str, service: ReportService = Depends(get_report_service)
):
    """Get a preview of the report data without generating the full report."""
    try:
        from ...core.services import TestResultService, TestRunService

        # Get basic data for preview
        run_service = TestRunService()
        result_service = TestResultService()

        run = await run_service.get_run(run_id)
        if not run:
            raise HTTPException(status_code=404, detail="Test run not found")

        summary = await result_service.get_run_summary(run_id)
        results = await result_service.list_results(run_id)

        # Create a preview with limited data
        preview = {
            "run_info": {
                "run_id": run.run_id,
                "name": run.name,
                "status": run.status.value,
                "created_at": run.created_at.isoformat(),
                "duration_seconds": run.duration_seconds,
            },
            "summary": summary,
            "sample_results": [r.to_dict() for r in results[:5]],  # First 5 results
            "insights_preview": (
                run.ai_insights[:3] if run.ai_insights else []
            ),  # First 3 insights
            "total_results": len(results),
        }

        return preview

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/run/{run_id}/status")
async def get_report_status(
    run_id: str, service: ReportService = Depends(get_report_service)
):
    """Get the status of reports for a test run."""
    try:
        from ...core.services import TestRunService

        run_service = TestRunService()
        run = await run_service.get_run(run_id)

        if not run:
            raise HTTPException(status_code=404, detail="Test run not found")

        # Check if reports exist
        html_exists = False
        json_exists = False
        html_size = 0
        json_size = 0

        if run.html_report_path:
            html_path = Path(run.html_report_path)
            html_exists = html_path.exists()
            if html_exists:
                html_size = html_path.stat().st_size

        if run.json_report_path:
            json_path = Path(run.json_report_path)
            json_exists = json_path.exists()
            if json_exists:
                json_size = json_path.stat().st_size

        return {
            "run_id": run_id,
            "run_status": run.status.value,
            "reports": {
                "html": {
                    "exists": html_exists,
                    "path": run.html_report_path,
                    "size_bytes": html_size,
                    "download_url": (
                        f"/api/reports/run/{run_id}/html" if html_exists else None
                    ),
                },
                "json": {
                    "exists": json_exists,
                    "path": run.json_report_path,
                    "size_bytes": json_size,
                    "download_url": (
                        f"/api/reports/run/{run_id}/json" if json_exists else None
                    ),
                },
            },
            "can_generate": run.status.value in ["completed", "failed"],
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/run/{run_id}")
async def delete_reports(
    run_id: str, service: ReportService = Depends(get_report_service)
):
    """Delete all reports for a test run."""
    try:
        from ...core.services import TestRunService

        run_service = TestRunService()
        run = await run_service.get_run(run_id)

        if not run:
            raise HTTPException(status_code=404, detail="Test run not found")

        deleted_files = []

        # Delete HTML report
        if run.html_report_path:
            html_path = Path(run.html_report_path)
            if html_path.exists():
                html_path.unlink()
                deleted_files.append("html")

        # Delete JSON report
        if run.json_report_path:
            json_path = Path(run.json_report_path)
            if json_path.exists():
                json_path.unlink()
                deleted_files.append("json")

        # Update run to clear report paths
        await run_service.update_run(
            run_id, {"html_report_path": None, "json_report_path": None}
        )

        return {
            "run_id": run_id,
            "deleted_reports": deleted_files,
            "message": f"Deleted {len(deleted_files)} report(s)",
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
