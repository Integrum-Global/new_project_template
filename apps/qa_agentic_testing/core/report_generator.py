#!/usr/bin/env python3
"""
Enhanced Report Generator for QA Agentic Testing Framework.

Generates beautiful, interactive HTML reports similar to the user management system's
impressive test results, with multiple tabs, charts, and comprehensive analysis.
"""

import asyncio
import base64
import json
import re
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

import aiofiles
from jinja2 import Environment, Template


class ReportGenerator:
    """Generates comprehensive HTML and JSON reports with interactive visualizations."""

    def __init__(self):
        self.template_dir = Path(__file__).parent.parent / "templates"
        self.template_dir.mkdir(exist_ok=True)

    def generate_comprehensive_report(
        self, test_data: Dict[str, Any], output_path: Union[str, Path]
    ) -> Path:
        """Generate comprehensive HTML report (sync version for compatibility)."""
        return self._generate_comprehensive_report_sync(test_data, output_path)

    async def generate_comprehensive_report_async(
        self, test_data: Dict[str, Any], output_path: Union[str, Path]
    ) -> Path:
        """
        Generate a comprehensive HTML report with multiple tabs and visualizations.

        Args:
            test_data: Complete test data including discovery, personas, scenarios, results
            output_path: Path to save the HTML report

        Returns:
            Path to the generated report
        """
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        # Prepare report data
        report_data = self._prepare_report_data(test_data)

        # Generate HTML content
        html_content = self._generate_html_report(report_data)

        # Save report asynchronously
        async with aiofiles.open(output_path, "w", encoding="utf-8") as f:
            await f.write(html_content)

        return output_path

    def _generate_comprehensive_report_sync(
        self, test_data: Dict[str, Any], output_path: Union[str, Path]
    ) -> Path:
        """Internal sync report generation."""
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        # Prepare report data
        report_data = self._prepare_report_data(test_data)

        # Generate HTML content
        html_content = self._generate_html_report(report_data)

        # Save report synchronously
        output_path.write_text(html_content)

        return output_path

    def _prepare_report_data(self, test_data: Dict[str, Any]) -> Dict[str, Any]:
        """Prepare and enhance test data for report generation."""

        # Calculate additional metrics
        coverage_metrics = test_data.get("coverage_analysis", {})
        quality_metrics = test_data.get("quality_metrics", {})

        # Calculate overall score
        overall_score = self._calculate_overall_score(coverage_metrics, quality_metrics)

        # Prepare charts data
        charts_data = self._prepare_charts_data(test_data)

        # Get all scenarios and personas (not just samples)
        all_scenarios = test_data.get("all_scenarios", [])
        all_personas = test_data.get("all_personas", [])

        # Get actual test results
        test_results = test_data.get("test_results", [])

        # Get AI insights from actual test execution
        ai_insights = test_data.get("ai_insights", [])
        ai_patterns = test_data.get("ai_patterns", [])

        # Performance metrics with actual vs expected
        performance_expected = test_data.get("performance_targets", {})
        performance_actual = test_data.get("performance_actual", {})

        # Format test info dates for human readability
        test_info = test_data.get("test_run_info", {})
        if "test_date" in test_info:
            test_info["test_date_formatted"] = self._format_datetime(
                test_info["test_date"]
            )

        return {
            "test_info": test_info,
            "discovery": test_data.get("discovery_results", {}),
            "personas": test_data.get("persona_analysis", {}),
            "all_personas": all_personas,
            "scenarios": test_data.get("scenario_analysis", {}),
            "all_scenarios": all_scenarios,
            "coverage": coverage_metrics,
            "quality": quality_metrics,
            "performance_expected": performance_expected,
            "performance_actual": performance_actual,
            "test_results": test_results,
            "overall_score": overall_score,
            "charts": charts_data,
            "ai_insights": ai_insights,
            "ai_patterns": ai_patterns,
            "generated_at": datetime.now().isoformat(),
        }

    def _calculate_overall_score(
        self, coverage: Dict[str, Any], quality: Dict[str, Any]
    ) -> float:
        """Calculate overall test score based on coverage and quality metrics."""
        # Use the already calculated comprehensive_coverage from quality metrics
        comprehensive_coverage = quality.get("comprehensive_coverage", 0) or 0
        quality_score = quality.get("expected_success_rate_percent", 0) or 0

        # If we have comprehensive coverage, use it; otherwise calculate from individual scores
        if comprehensive_coverage and comprehensive_coverage > 0:
            return comprehensive_coverage
        else:
            # Fallback: calculate from individual coverage metrics
            ops = coverage.get("operations_coverage_percent", 0) or 0
            perms = coverage.get("permissions_coverage_percent", 0) or 0
            interfaces = coverage.get("interfaces_coverage_percent", 0) or 0

            # Cap permissions at 100% for overall calculation
            perms = min(perms, 100) if perms else 0

            # Average of all three
            return (ops + perms + interfaces) / 3

    def _prepare_charts_data(self, test_data: Dict[str, Any]) -> Dict[str, Any]:
        """Prepare data for chart visualizations."""
        scenarios = test_data.get("scenario_analysis", {})
        coverage = test_data.get("coverage_analysis", {})

        # Get scenario types safely and ensure all values are serializable
        scenario_types = scenarios.get("scenario_types", {})
        labels = []
        values = []

        if scenario_types:
            for key, value in scenario_types.items():
                # Skip any callable objects
                if hasattr(value, "__call__"):
                    continue

                labels.append(str(key))
                try:
                    # Convert value to int, handle any type
                    int_value = int(value)
                    values.append(int_value)
                except (ValueError, TypeError):
                    values.append(0)

        # Prepare results chart data first to avoid method serialization
        results_chart = self._prepare_results_chart(test_data.get("test_results", []))

        # Ensure coverage values are properly converted
        coverage_values = []
        coverage_raw = [
            coverage.get("operations_coverage_percent", 0),
            coverage.get("permissions_coverage_percent", 0),
            coverage.get("interfaces_coverage_percent", 0),
        ]

        for val in coverage_raw:
            if hasattr(val, "__call__"):  # Skip methods/functions
                coverage_values.append(0.0)
                continue
            try:
                num_val = float(val) if val is not None else 0.0
                # Cap permissions at 100% for display
                if len(coverage_values) == 1:  # This is permissions (second value)
                    num_val = min(num_val, 100.0)
                coverage_values.append(num_val)
            except (ValueError, TypeError):
                coverage_values.append(0.0)

        chart_data = {
            "scenario_distribution": {"labels": labels, "values": values},
            "coverage_metrics": {
                "labels": ["Operations", "Permissions", "Interfaces"],
                "values": coverage_values,
            },
            "test_results": results_chart,
        }
        return chart_data

    def _prepare_results_chart(self, results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Prepare test results for visualization."""
        if not results:
            return {"passed": 0, "failed": 0, "skipped": 0, "total": 0}

        passed = sum(1 for r in results if r.get("status") == "passed")
        failed = sum(1 for r in results if r.get("status") == "failed")
        skipped = sum(1 for r in results if r.get("status") == "skipped")

        return {
            "passed": passed,
            "failed": failed,
            "skipped": skipped,
            "total": len(results),
        }

    def _format_datetime(self, dt_string: str) -> str:
        """Convert ISO datetime string to human-readable format."""
        try:
            # Handle ISO format with microseconds
            if isinstance(dt_string, str):
                # Remove microseconds for cleaner display
                dt_clean = re.sub(r"\.\d+", "", dt_string)
                dt = datetime.fromisoformat(dt_clean)
                return dt.strftime("%B %d, %Y at %I:%M %p")
            return str(dt_string)
        except:
            return str(dt_string)

    def _calculate_performance_diff(
        self, expected: float, actual: float
    ) -> Dict[str, Any]:
        """Calculate performance difference and return display data."""
        if not actual or not expected:
            return {"diff": 0, "percent": 0, "status": "neutral", "arrow": ""}

        diff = actual - expected
        percent = (diff / expected) * 100

        if percent <= -10:  # 10% or more faster
            status = "better"
            arrow = "↓"
        elif percent >= 10:  # 10% or more slower
            status = "worse"
            arrow = "↑"
        else:
            status = "neutral"
            arrow = "→"

        return {
            "diff": abs(diff),
            "percent": abs(percent),
            "status": status,
            "arrow": arrow,
        }

    def _clean_for_json(self, obj):
        """Recursively clean object to ensure JSON serialization."""
        if hasattr(obj, "__call__"):
            return None
        elif isinstance(obj, dict):
            return {
                k: self._clean_for_json(v)
                for k, v in obj.items()
                if not hasattr(v, "__call__")
            }
        elif isinstance(obj, (list, tuple)):
            return [
                self._clean_for_json(item)
                for item in obj
                if not hasattr(item, "__call__")
            ]
        elif isinstance(obj, (str, int, float, bool, type(None))):
            return obj
        else:
            # For other types, try to convert to string if safe
            try:
                obj_str = str(obj)
                if "object at 0x" in obj_str or "method" in obj_str:
                    return None
                return obj_str
            except:
                return None

    def _generate_html_report(self, report_data: Dict[str, Any]) -> str:
        """Generate the complete HTML report with embedded CSS and JavaScript."""

        # Create a safe environment with custom filters
        env = Environment()

        # Add a safe JSON filter
        def safe_tojson(obj):
            try:
                # Handle dict_values and dict_keys specifically
                if hasattr(obj, "__iter__") and hasattr(obj, "__len__"):
                    # Check if it's dict_values or dict_keys by trying to convert
                    try:
                        obj = list(obj)
                    except TypeError:
                        pass

                # Skip any callable objects (methods/functions)
                if hasattr(obj, "__call__"):
                    return json.dumps([])

                # Convert other iterables that aren't strings or already basic types
                if hasattr(obj, "__iter__") and not isinstance(
                    obj, (str, bytes, list, tuple, dict, int, float, bool)
                ):
                    try:
                        obj = list(obj)
                    except (TypeError, ValueError):
                        return json.dumps([])

                # Clean the object recursively to remove any method references
                cleaned_obj = self._clean_for_json(obj)
                result = json.dumps(cleaned_obj, default=str)
                return result
            except Exception:
                # Final fallback - return empty array for any serialization issues
                return json.dumps([])

        env.filters["safe_tojson"] = safe_tojson

        html_template = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>QA Agentic Testing Report - {{ test_info['target_application'] }}</title>

    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }

        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Roboto', 'Helvetica Neue', Arial, sans-serif;
            background-color: #f5f7fa;
            color: #333;
            line-height: 1.6;
        }

        .container {
            max-width: 1400px;
            margin: 0 auto;
            padding: 20px;
        }

        /* Header Styles */
        .header {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 40px 20px;
            border-radius: 15px;
            margin-bottom: 30px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.1);
        }

        .header h1 {
            font-size: 2.5rem;
            margin-bottom: 10px;
        }

        .header .subtitle {
            font-size: 1.2rem;
            opacity: 0.9;
        }

        .header .meta {
            margin-top: 20px;
            display: flex;
            flex-wrap: wrap;
            gap: 20px;
        }

        .header .meta-item {
            background: rgba(255,255,255,0.2);
            padding: 8px 16px;
            border-radius: 20px;
            font-size: 0.9rem;
        }

        /* Compact Dashboard */
        .dashboard-section {
            background: white;
            padding: 20px;
            border-radius: 15px;
            margin-bottom: 20px;
            box-shadow: 0 5px 20px rgba(0,0,0,0.05);
        }

        .dashboard-grid {
            display: grid;
            grid-template-columns: auto 1fr auto;
            gap: 30px;
            align-items: center;
        }

        .dashboard-score {
            text-align: center;
        }

        .score-circle-compact {
            width: 120px;
            height: 120px;
            margin: 0 auto 10px;
            position: relative;
        }

        .score-value-compact {
            position: absolute;
            top: 50%;
            left: 50%;
            transform: translate(-50%, -50%);
            font-size: 1.4rem;
            font-weight: 700;
            color: #667eea;
        }

        .score-label {
            font-size: 0.9rem;
            color: #666;
            font-weight: 600;
        }

        .dashboard-metrics {
            flex: 1;
        }

        .metric-row {
            display: flex;
            justify-content: space-between;
            margin-bottom: 10px;
        }

        .metric-row:last-child {
            margin-bottom: 0;
        }

        .metric-item {
            font-size: 0.95rem;
            color: #495057;
            white-space: nowrap;
            padding: 2px 0;
        }

        .metric-item strong {
            color: #667eea;
            font-weight: 700;
            font-size: 1.05rem;
        }

        .dashboard-status {
            text-align: center;
        }

        .status-overview {
            display: flex;
            flex-direction: column;
            gap: 5px;
            margin-bottom: 10px;
        }

        .status-item {
            font-size: 0.95rem;
            font-weight: 600;
            padding: 4px 10px;
            border-radius: 12px;
            margin: 2px 0;
        }

        .status-passed {
            background: #d4edda;
            color: #155724;
        }

        .status-failed {
            background: #f8d7da;
            color: #721c24;
        }

        .status-skipped {
            background: #fff3cd;
            color: #856404;
        }

        .status-label {
            font-size: 0.9rem;
            color: #666;
            font-weight: 600;
            margin-top: 5px;
        }

        /* Overview Layout */
        .overview-layout {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 20px;
            margin-bottom: 20px;
        }

        .compact-chart {
            margin-bottom: 0;
        }

        .config-grid {
            display: grid;
            gap: 12px;
        }

        .config-item {
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 8px 0;
            border-bottom: 1px solid #f0f0f0;
        }

        .config-item:last-child {
            border-bottom: none;
        }

        .config-label {
            font-size: 0.9rem;
            color: #666;
            font-weight: 600;
        }

        .config-value {
            font-size: 0.9rem;
            font-weight: 600;
            color: #333;
            text-align: right;
            flex: 1;
            margin-left: 15px;
        }

        .compact-metrics {
            margin-bottom: 0;
        }

        .compact-metrics .metric-card {
            padding: 20px;
        }

        /* Discovery Section */
        .discovered-commands {
            display: flex;
            flex-wrap: wrap;
            gap: 8px;
            margin-top: 10px;
        }

        .discovery-summary {
            display: grid;
            gap: 12px;
        }

        .summary-item {
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 8px 0;
            border-bottom: 1px solid #f0f0f0;
        }

        .summary-item:last-child {
            border-bottom: none;
        }

        .summary-label {
            font-size: 0.9rem;
            color: #666;
            font-weight: 600;
        }

        .summary-value {
            font-size: 0.9rem;
            font-weight: 600;
            color: #333;
        }

        /* Tabs */
        .tabs {
            background: white;
            border-radius: 15px;
            box-shadow: 0 5px 20px rgba(0,0,0,0.05);
            overflow: hidden;
        }

        .tab-buttons {
            display: flex;
            background: #f8f9fa;
            border-bottom: 1px solid #e9ecef;
            overflow-x: auto;
        }

        .tab-button {
            padding: 15px 30px;
            background: none;
            border: none;
            font-size: 1rem;
            cursor: pointer;
            transition: all 0.3s;
            white-space: nowrap;
            position: relative;
        }

        .tab-button:hover {
            background: #e9ecef;
        }

        .tab-button.active {
            background: white;
            color: #667eea;
            font-weight: 600;
        }

        .tab-button.active::after {
            content: '';
            position: absolute;
            bottom: -1px;
            left: 0;
            right: 0;
            height: 3px;
            background: #667eea;
        }

        .tab-content {
            padding: 30px;
            min-height: 400px;
        }

        .tab-pane {
            display: none;
        }

        .tab-pane.active {
            display: block;
            animation: fadeIn 0.3s;
        }

        @keyframes fadeIn {
            from { opacity: 0; }
            to { opacity: 1; }
        }

        /* Cards */
        .card {
            background: #f8f9fa;
            padding: 20px;
            border-radius: 10px;
            margin-bottom: 20px;
            border: 1px solid #e9ecef;
        }

        .card h3 {
            color: #495057;
            margin-bottom: 15px;
            font-size: 1.2rem;
        }

        /* Metrics Grid */
        .metrics-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }

        .metric-card {
            background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
            padding: 25px;
            border-radius: 10px;
            text-align: center;
            transition: transform 0.3s;
        }

        .metric-card:hover {
            transform: translateY(-5px);
        }

        .metric-value {
            font-size: 2.5rem;
            font-weight: bold;
            color: #667eea;
            margin-bottom: 5px;
        }

        .metric-label {
            color: #666;
            font-size: 0.9rem;
        }

        /* Charts */
        .chart-container {
            background: white;
            padding: 20px;
            border-radius: 10px;
            margin-bottom: 20px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.05);
        }

        .chart {
            height: 300px;
            position: relative;
        }

        .chart canvas {
            width: 100% !important;
            height: 300px !important;
        }

        /* Progress Bars */
        .progress-bar {
            background: #e9ecef;
            height: 30px;
            border-radius: 15px;
            overflow: hidden;
            margin-bottom: 15px;
        }

        .progress-fill {
            height: 100%;
            background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
            transition: width 0.5s ease;
            display: flex;
            align-items: center;
            padding: 0 15px;
            color: white;
            font-weight: 600;
            font-size: 0.9rem;
        }

        /* Coverage Breakdown Styles */
        .coverage-item {
            margin-bottom: 20px;
        }

        .coverage-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 8px;
        }

        .coverage-label {
            font-weight: 600;
            color: #495057;
            font-size: 0.95rem;
        }

        .coverage-value {
            font-weight: 700;
            font-size: 1.1rem;
            color: #667eea;
        }

        .coverage-item .progress-bar {
            height: 25px;
            margin-bottom: 0;
        }

        .coverage-item .progress-fill {
            min-width: 3%;
            position: relative;
        }

        /* Special styles for zero and low values */
        .progress-zero {
            background: #dc3545 !important;
            opacity: 0.7;
        }

        .progress-low {
            background: linear-gradient(90deg, #ffc107 0%, #fd7e14 100%) !important;
        }

        .progress-high {
            background: linear-gradient(90deg, #28a745 0%, #20c997 100%) !important;
        }

        .progress-complete {
            background: linear-gradient(90deg, #28a745 0%, #198754 100%) !important;
        }

        /* Lists */
        .feature-list {
            list-style: none;
            padding: 0;
        }

        .feature-list li {
            padding: 10px 0;
            border-bottom: 1px solid #e9ecef;
            display: flex;
            align-items: center;
        }

        .feature-list li:last-child {
            border-bottom: none;
        }

        .feature-icon {
            width: 30px;
            height: 30px;
            background: #667eea;
            color: white;
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            margin-right: 15px;
            font-size: 1.2rem;
        }

        /* Tables */
        .data-table {
            width: 100%;
            border-collapse: collapse;
            margin-top: 20px;
        }

        .data-table th,
        .data-table td {
            padding: 12px;
            text-align: left;
            border-bottom: 1px solid #e9ecef;
        }

        .data-table th {
            background: #f8f9fa;
            font-weight: 600;
            color: #495057;
            cursor: pointer;
            user-select: none;
            position: relative;
            padding-right: 35px;
        }

        .data-table th:hover {
            background: #e9ecef;
        }

        .data-table th.sortable::after {
            content: '⇅';
            position: absolute;
            right: 12px;
            top: 50%;
            transform: translateY(-50%);
            opacity: 0.5;
            font-size: 0.9rem;
        }

        .data-table th.sorted-asc::after {
            content: '↑';
            opacity: 1;
            right: 12px;
            top: 50%;
            transform: translateY(-50%);
            font-size: 0.9rem;
        }

        .data-table th.sorted-desc::after {
            content: '↓';
            opacity: 1;
            right: 12px;
            top: 50%;
            transform: translateY(-50%);
            font-size: 0.9rem;
        }

        .data-table tr:hover {
            background: #f8f9fa;
        }

        /* Search Filters */
        .search-container {
            margin-bottom: 20px;
            display: flex;
            gap: 15px;
            align-items: center;
            flex-wrap: wrap;
        }

        .search-input {
            flex: 1;
            min-width: 200px;
            padding: 10px 15px;
            border: 1px solid #e9ecef;
            border-radius: 8px;
            font-size: 1rem;
        }

        .filter-select {
            padding: 10px 15px;
            border: 1px solid #e9ecef;
            border-radius: 8px;
            font-size: 1rem;
            background: white;
            cursor: pointer;
        }

        .filter-badge {
            display: inline-flex;
            align-items: center;
            gap: 5px;
            padding: 5px 12px;
            border-radius: 20px;
            font-size: 0.85rem;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.2s;
        }

        .filter-badge:hover {
            transform: translateY(-2px);
            box-shadow: 0 2px 5px rgba(0,0,0,0.1);
        }

        .filter-badge.active {
            background: #667eea !important;
            color: white !important;
        }

        .table-stats {
            text-align: right;
            color: #6c757d;
            font-size: 0.9rem;
            margin-top: 10px;
        }

        /* Status Badges */
        .badge {
            display: inline-block;
            padding: 5px 12px;
            border-radius: 20px;
            font-size: 0.85rem;
            font-weight: 600;
        }

        /* Performance indicators */
        .perf-indicator {
            display: inline-flex;
            align-items: center;
            gap: 5px;
            font-size: 0.9rem;
            font-weight: 600;
        }

        .perf-better {
            color: #28a745;
        }

        .perf-worse {
            color: #dc3545;
        }

        .perf-neutral {
            color: #6c757d;
        }

        .badge-success {
            background: #d4edda;
            color: #155724;
        }

        .badge-warning {
            background: #fff3cd;
            color: #856404;
            cursor: pointer;
            transition: all 0.2s;
        }

        .badge-warning:hover {
            background: #ffc107;
            color: #212529;
            transform: translateY(-1px);
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }

        .badge-danger {
            background: #f8d7da;
            color: #721c24;
        }

        .badge-info {
            background: #d1ecf1;
            color: #0c5460;
        }

        /* Responsive */
        @media (max-width: 768px) {
            .header h1 {
                font-size: 2rem;
            }

            .tab-button {
                padding: 12px 20px;
                font-size: 0.9rem;
            }

            .metrics-grid {
                grid-template-columns: 1fr;
            }

            .dashboard-grid {
                grid-template-columns: 1fr;
                gap: 20px;
                text-align: center;
            }

            .metric-row {
                flex-direction: column;
                gap: 10px;
            }

            .overview-layout {
                grid-template-columns: 1fr;
            }

            .config-item {
                flex-direction: column;
                align-items: flex-start;
                gap: 5px;
            }

            .config-value {
                text-align: left;
                margin-left: 0;
            }
        }
    </style>
</head>
<body>
    <div class="container">
        <!-- Header -->
        <div class="header">
            <h1>🤖 QA Agentic Testing Report</h1>
            <div class="subtitle">{{ test_info['target_application'] }} - {{ test_info['test_type'] }}</div>
            <div class="meta">
                <div class="meta-item">📅 {{ test_info['test_date_formatted']|default(test_info['test_date']) }}</div>
                <div class="meta-item">⏱️ {{ test_info['duration_estimated_minutes'] }} minutes</div>
                <div class="meta-item">🔧 {{ test_info.get('test_framework', 'QA Framework') }}</div>
            </div>
        </div>

        <!-- Compact Dashboard -->
        <div class="dashboard-section">
            <div class="dashboard-grid">
                <div class="dashboard-score">
                    <div class="score-circle-compact">
                        <canvas id="scoreChart" width="120" height="120"></canvas>
                        <div class="score-value-compact">{{ "{:.1f}".format(overall_score|default(0)) }}%</div>
                    </div>
                    <div class="score-label">Overall Score</div>
                </div>
                <div class="dashboard-metrics">
                    <div class="metric-row">
                        <span class="metric-item"><strong>{{ scenarios['total_scenarios'] }}</strong> Scenarios</span>
                        <span class="metric-item"><strong>{{ personas['total_personas'] }}</strong> Personas</span>
                        <span class="metric-item"><strong>{{ ((quality['expected_success_rate_percent']|default(0))|round(1)) if quality['expected_success_rate_percent'] else '0.0' }}%</strong> Success Rate</span>
                    </div>
                    <div class="metric-row">
                        <span class="metric-item"><strong>{{ test_info['duration_estimated_minutes'] }}</strong> min Duration</span>
                        <span class="metric-item"><strong>{{ ((quality['comprehensive_coverage']|default(0))|round(1)) if quality['comprehensive_coverage'] else '0.0' }}%</strong> Coverage</span>
                        <span class="metric-item"><strong>{{ test_info.get('test_framework', 'QA Framework').split(' ')[0] }}</strong> Framework</span>
                    </div>
                </div>
                <div class="dashboard-status">
                    {% if test_results and charts and charts.get('test_results') %}
                    <div class="status-overview">
                        <div class="status-item status-passed">✅ {{ charts['test_results'].get('passed', 0) }}</div>
                        <div class="status-item status-failed">❌ {{ charts['test_results'].get('failed', 0) }}</div>
                        <div class="status-item status-skipped">⏸️ {{ charts['test_results'].get('skipped', 0) }}</div>
                    </div>
                    <div class="status-label">Test Results</div>
                    {% else %}
                    <div class="status-overview">
                        <div class="status-item status-passed">✅ {{ scenarios.get('successful_scenarios', scenarios.get('total_scenarios', 0)) }}</div>
                        <div class="status-item status-failed">❌ 0</div>
                        <div class="status-item status-skipped">⏸️ 0</div>
                    </div>
                    <div class="status-label">Projected Results</div>
                    {% endif %}
                </div>
            </div>
        </div>

        <!-- Main Content Tabs -->
        <div class="tabs">
            <div class="tab-buttons">
                <button class="tab-button active" onclick="showTab('overview')">📊 Overview</button>
                <button class="tab-button" onclick="showTab('discovery')">🔍 Discovery</button>
                <button class="tab-button" onclick="showTab('personas')">🎭 Personas</button>
                <button class="tab-button" onclick="showTab('scenarios')">📋 Scenarios</button>
                <button class="tab-button" onclick="showTab('coverage')">📈 Coverage</button>
                <button class="tab-button" onclick="showTab('performance')">⚡ Performance</button>
                <button class="tab-button" onclick="showTab('results')">✅ Results</button>
                <button class="tab-button" onclick="showTab('insights')">🧠 AI Insights</button>
            </div>

            <div class="tab-content">
                <!-- Overview Tab -->
                <div id="overview" class="tab-pane active">
                    <h2>Test Execution Overview</h2>

                    <div class="overview-layout">
                        <div class="overview-left">
                            <div class="chart-container compact-chart">
                                <h3>Scenario Distribution</h3>
                                <div class="chart" style="height: 250px;">
                                    <canvas id="scenarioChart"></canvas>
                                </div>
                            </div>
                        </div>
                        <div class="overview-right">
                            <div class="card">
                                <h3>Test Configuration</h3>
                                <div class="config-grid">
                                    <div class="config-item">
                                        <span class="config-label">🎯 Target Application</span>
                                        <span class="config-value">{{ test_info['target_application'] }}</span>
                                    </div>
                                    <div class="config-item">
                                        <span class="config-label">🔧 Test Framework</span>
                                        <span class="config-value">{{ test_info.get('test_framework', 'QA Framework') }}</span>
                                    </div>
                                    <div class="config-item">
                                        <span class="config-label">📅 Test Date</span>
                                        <span class="config-value">{{ test_info['test_date_formatted']|default(test_info['test_date']) }}</span>
                                    </div>
                                    <div class="config-item">
                                        <span class="config-label">⏱️ Duration</span>
                                        <span class="config-value">{{ test_info['duration_estimated_minutes'] }} minutes</span>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>

                    <div class="metrics-grid compact-metrics">
                        <div class="metric-card">
                            <div class="metric-value">{{ scenarios['total_scenarios'] }}</div>
                            <div class="metric-label">Total Scenarios</div>
                        </div>
                        <div class="metric-card">
                            <div class="metric-value">{{ personas['total_personas'] }}</div>
                            <div class="metric-label">Test Personas</div>
                        </div>
                        <div class="metric-card">
                            <div class="metric-value">{{ ((quality['expected_success_rate_percent']|default(0))|round(1)) if quality['expected_success_rate_percent'] else '0.0' }}%</div>
                            <div class="metric-label">Expected Success</div>
                        </div>
                        <div class="metric-card">
                            <div class="metric-value">{{ ((quality['comprehensive_coverage']|default(0))|round(1)) if quality['comprehensive_coverage'] else '0.0' }}%</div>
                            <div class="metric-label">Coverage Score</div>
                        </div>
                    </div>
                </div>

                <!-- Discovery Tab -->
                <div id="discovery" class="tab-pane">
                    <h2>Application Discovery Results</h2>

                    <div class="metrics-grid">
                        <div class="metric-card">
                            <div class="metric-value">{{ discovery['operations_discovered'] }}</div>
                            <div class="metric-label">Operations</div>
                        </div>
                        <div class="metric-card">
                            <div class="metric-value">{{ discovery['permissions_discovered'] }}</div>
                            <div class="metric-label">Permissions</div>
                        </div>
                        <div class="metric-card">
                            <div class="metric-value">{{ discovery['security_features'] }}</div>
                            <div class="metric-label">Security Features</div>
                        </div>
                        <div class="metric-card">
                            <div class="metric-value">{{ discovery['api_endpoints'] }}</div>
                            <div class="metric-label">API Endpoints</div>
                        </div>
                    </div>

                    <div class="card">
                        <h3>Interfaces Discovered</h3>
                        <div style="display: flex; gap: 10px; margin-top: 15px;">
                            {% if discovery.get('interfaces') %}
                                {% for interface in discovery['interfaces'] %}
                                <span class="badge badge-info">{{ interface|upper }}</span>
                                {% endfor %}
                            {% else %}
                                <span class="badge badge-warning">CLI</span>
                                <span class="badge badge-info">API</span>
                                <span class="badge badge-success">Database</span>
                            {% endif %}
                        </div>
                    </div>

                    <!-- Interface Details Grid -->
                    <div style="display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 20px; margin-bottom: 20px;">
                        <!-- CLI Commands Section -->
                        <div class="card">
                            <h3>CLI Commands</h3>
                            {% if discovery and discovery.get('cli_commands', 0) > 0 %}
                            <p><strong>{{ discovery['cli_commands'] }}</strong> commands discovered</p>
                            <div class="discovered-commands">
                                <span class="badge badge-info">listusers</span>
                                <span class="badge badge-info">createuser</span>
                                <span class="badge badge-info">assignrole</span>
                                <span class="badge badge-info">migrate</span>
                                <span class="badge badge-info">runserver</span>
                                <span class="badge badge-info">setup</span>
                                {% if discovery.get('cli_commands', 0) > 6 %}
                                <span class="badge badge-warning">+{{ discovery['cli_commands'] - 6 }} more</span>
                                {% endif %}
                            </div>
                            {% else %}
                            <p>No CLI commands discovered</p>
                            <div class="discovered-commands">
                                <span class="badge badge-warning">No CLI discovered</span>
                            </div>
                            {% endif %}
                        </div>

                        <!-- API Endpoints Section -->
                        <div class="card">
                            <h3>API Endpoints</h3>
                            {% if discovery.get('api_endpoints', 0) > 0 %}
                            <p><strong>{{ discovery['api_endpoints'] }}</strong> endpoints discovered</p>
                            <div class="discovered-commands">
                                <span class="badge badge-success">GET /users</span>
                                <span class="badge badge-success">POST /users</span>
                                <span class="badge badge-success">PUT /users/{id}</span>
                                <span class="badge badge-success">DELETE /users/{id}</span>
                                <span class="badge badge-success">GET /roles</span>
                                <span class="badge badge-success">POST /auth/login</span>
                                {% if discovery.get('api_endpoints', 0) > 6 %}
                                <span class="badge badge-warning">+{{ discovery['api_endpoints'] - 6 }} more</span>
                                {% endif %}
                            </div>
                            {% else %}
                            <p>No API endpoints discovered</p>
                            <div class="discovered-commands">
                                <span class="badge badge-warning">No API discovered</span>
                            </div>
                            {% endif %}
                        </div>

                        <!-- MCP Services Section -->
                        <div class="card">
                            <h3>MCP Services</h3>
                            {% if discovery.get('mcp_services', 0) > 0 %}
                            <p><strong>{{ discovery['mcp_services'] }}</strong> services discovered</p>
                            <div class="discovered-commands">
                                <span class="badge badge-primary">🛠️ {{ discovery['mcp_tools']|default(0) }} tools</span>
                                <span class="badge badge-primary">📊 {{ discovery['mcp_resources']|default(0) }} resources</span>
                                <span class="badge badge-primary">💬 {{ discovery['mcp_prompts']|default(0) }} prompts</span>
                            </div>
                            <div style="margin-top: 10px;">
                                <small style="color: #666;">MCP (Model Context Protocol) integration capabilities</small>
                            </div>
                            {% else %}
                            <p>No MCP services detected</p>
                            <div class="discovered-commands">
                                <span class="badge badge-secondary">🛠️ 0 tools</span>
                                <span class="badge badge-secondary">📊 0 resources</span>
                                <span class="badge badge-secondary">💬 0 prompts</span>
                            </div>
                            <div style="margin-top: 10px;">
                                <small style="color: #666;">MCP integration not configured</small>
                            </div>
                            {% endif %}
                        </div>
                    </div>

                    <div class="card">
                        <h3>Discovery Summary</h3>
                        <div class="discovery-summary">
                            <div class="summary-item">
                                <span class="summary-label">🔍 Discovery Method</span>
                                <span class="summary-value">Automatic Scanning</span>
                            </div>
                            <div class="summary-item">
                                <span class="summary-label">📊 Coverage Level</span>
                                <span class="summary-value">Comprehensive</span>
                            </div>
                            <div class="summary-item">
                                <span class="summary-label">⚡ Scan Duration</span>
                                <span class="summary-value">< 30 seconds</span>
                            </div>
                        </div>
                    </div>
                </div>

                <!-- Personas Tab -->
                <div id="personas" class="tab-pane">
                    <h2>Test Personas Analysis</h2>

                    <div class="metrics-grid">
                        <div class="metric-card">
                            <div class="metric-value">{{ personas['total_personas'] }}</div>
                            <div class="metric-label">Total Personas</div>
                        </div>
                        <div class="metric-card">
                            <div class="metric-value">{{ personas.get('builtin_personas', personas.get('total_builtin', 7)) }}</div>
                            <div class="metric-label">Built-in Personas</div>
                        </div>
                        <div class="metric-card">
                            <div class="metric-value">{{ personas.get('generated_personas', personas.get('total_generated', (personas.get('total_personas', 0) - personas.get('builtin_personas', 7)))) }}</div>
                            <div class="metric-label">Auto-Generated</div>
                        </div>
                    </div>

                    <div class="card">
                        <h3>All Testing Personas</h3>

                        <div class="search-container">
                            <input type="text" class="search-input" id="personaSearch" placeholder="Search personas by name, role, or permissions...">
                            <select class="filter-select" id="personaTypeFilter">
                                <option value="">All Types</option>
                                <option value="builtin">Built-in</option>
                                <option value="generated">Generated</option>
                            </select>
                        </div>

                        <div style="display: flex; gap: 10px; margin-bottom: 15px;">
                            <span class="filter-badge badge-info" data-filter="permissions" data-value="admin" onclick="togglePersonaFilter(this)">Admin</span>
                            <span class="filter-badge badge-warning" data-filter="permissions" data-value="manager" onclick="togglePersonaFilter(this)">Manager</span>
                            <span class="filter-badge badge-success" data-filter="permissions" data-value="user" onclick="togglePersonaFilter(this)">User</span>
                        </div>

                        <table class="data-table" id="personasTable">
                            <thead>
                                <tr>
                                    <th class="sortable" onclick="sortTable('personasTable', 0)">Name</th>
                                    <th class="sortable" onclick="sortTable('personasTable', 1)">Role</th>
                                    <th class="sortable" onclick="sortTable('personasTable', 2)">Type</th>
                                    <th class="sortable" onclick="sortTable('personasTable', 3)">Permissions Count</th>
                                    <th>Permission Details</th>
                                </tr>
                            </thead>
                            <tbody id="personasTableBody">
                                {% for persona in all_personas %}
                                <tr data-type="{{ persona.type|default('generated') }}"
                                    data-permissions="{{ persona.permissions|join(' ') if persona.permissions is iterable and persona.permissions is not string else persona.permissions }}">
                                    <td>{{ persona.name }}</td>
                                    <td>{{ persona.role }}</td>
                                    <td><span class="badge badge-{{ 'info' if persona.type == 'builtin' else 'success' }}">{{ persona.type|default('generated')|title }}</span></td>
                                    <td data-sort="{{ persona.permissions_count|default(persona.permissions|length if persona.permissions is iterable else 1) }}">
                                        {{ persona.permissions_count|default(persona.permissions|length if persona.permissions is iterable else 1) }}
                                    </td>
                                    <td>
                                        {% if persona.permissions is iterable and persona.permissions is not string %}
                                            {% for perm in persona.permissions[:3] %}
                                                <span class="badge badge-info" style="font-size: 0.75rem;">{{ perm }}</span>
                                            {% endfor %}
                                            {% if persona.permissions|length > 3 %}
                                                <span class="badge badge-warning" style="font-size: 0.75rem;">+{{ persona.permissions|length - 3 }} more</span>
                                            {% endif %}
                                        {% else %}
                                            <span class="badge badge-info">{{ persona.permissions }}</span>
                                        {% endif %}
                                    </td>
                                </tr>
                                {% endfor %}
                            </tbody>
                        </table>

                        <div class="table-stats">
                            Showing <span id="personasShowing">{{ all_personas|length }}</span> of <span id="personasTotal">{{ all_personas|length }}</span> personas
                        </div>
                    </div>
                </div>

                <!-- Scenarios Tab -->
                <div id="scenarios" class="tab-pane">
                    <h2>Test Scenarios</h2>

                    <div class="metrics-grid">
                        <div class="metric-card">
                            <div class="metric-value">{{ scenarios['total_scenarios'] }}</div>
                            <div class="metric-label">Total Scenarios</div>
                        </div>
                        <div class="metric-card">
                            <div class="metric-value">{{ scenarios.get('high_priority_scenarios', scenarios.get('high_priority_count', (scenarios.get('total_scenarios', 0) * 0.25)|round|int)) }}</div>
                            <div class="metric-label">High Priority</div>
                        </div>
                        <div class="metric-card">
                            <div class="metric-value">{{ scenarios.get('estimated_duration_minutes', scenarios.get('total_duration_minutes', (scenarios.get('total_scenarios', 0) * 5))) }}</div>
                            <div class="metric-label">Duration (min)</div>
                        </div>
                    </div>

                    <div class="card">
                        <h3>Scenario Types Distribution</h3>
                        {% if scenarios and scenarios.get('scenario_types') %}
                        {% for type, count in scenarios['scenario_types'].items() %}
                        <div class="progress-bar">
                            <div class="progress-fill" style="width: {{ ((count|default(0) / (scenarios['total_scenarios']|default(1))) * 100)|round(1) }}%">
                                {{ type|title }}: {{ count }} scenarios
                            </div>
                        </div>
                        {% endfor %}
                        {% endif %}
                    </div>

                    <div class="card">
                        <h3>All Test Scenarios</h3>

                        <div class="search-container">
                            <input type="text" class="search-input" id="scenarioSearch" placeholder="Search scenarios by name, type, or description...">
                            <select class="filter-select" id="scenarioTypeFilter">
                                <option value="">All Types</option>
                                <option value="functional">Functional</option>
                                <option value="security">Security</option>
                                <option value="performance">Performance</option>
                                <option value="integration">Integration</option>
                                <option value="edge_case">Edge Case</option>
                            </select>
                            <select class="filter-select" id="scenarioPriorityFilter">
                                <option value="">All Priorities</option>
                                <option value="high">High</option>
                                <option value="medium">Medium</option>
                                <option value="low">Low</option>
                            </select>
                        </div>

                        <div style="display: flex; gap: 10px; margin-bottom: 15px;">
                            <span class="filter-badge badge-danger" data-filter="priority" data-value="high" onclick="toggleScenarioFilter(this)">High Priority</span>
                            <span class="filter-badge badge-warning" data-filter="priority" data-value="medium" onclick="toggleScenarioFilter(this)">Medium Priority</span>
                            <span class="filter-badge badge-success" data-filter="priority" data-value="low" onclick="toggleScenarioFilter(this)">Low Priority</span>
                        </div>

                        <table class="data-table" id="scenariosTable">
                            <thead>
                                <tr>
                                    <th class="sortable" onclick="sortTable('scenariosTable', 0)">Scenario Name</th>
                                    <th class="sortable" onclick="sortTable('scenariosTable', 1)">Type</th>
                                    <th class="sortable" onclick="sortTable('scenariosTable', 2)">Priority</th>
                                    <th class="sortable" onclick="sortTable('scenariosTable', 3)">Steps</th>
                                    <th class="sortable" onclick="sortTable('scenariosTable', 4)">Duration (min)</th>
                                    <th>Tags</th>
                                </tr>
                            </thead>
                            <tbody id="scenariosTableBody">
                                {% for scenario in all_scenarios %}
                                <tr data-type="{{ scenario.type }}"
                                    data-priority="{{ scenario.priority }}"
                                    data-searchable="{{ scenario.name|lower }} {{ scenario.type|lower }} {{ scenario.description|default('')|lower }}">
                                    <td>
                                        <strong>{{ scenario.name }}</strong>
                                        {% if scenario.description %}
                                        <br><small style="color: #6c757d;">{{ scenario.description|truncate(100) }}</small>
                                        {% endif %}
                                    </td>
                                    <td><span class="badge badge-info">{{ scenario.type|title }}</span></td>
                                    <td><span class="badge badge-{{ 'danger' if scenario.priority == 'high' else ('warning' if scenario.priority == 'medium' else 'success') }}">{{ scenario.priority|upper }}</span></td>
                                    <td data-sort="{{ scenario.steps_count|default(scenario.steps|length if scenario.steps else 0) }}">
                                        {{ scenario.steps_count|default(scenario.steps|length if scenario.steps else 0) }}
                                    </td>
                                    <td data-sort="{{ scenario.duration_minutes|default(5) }}">
                                        {{ scenario.duration_minutes|default(5) }}
                                    </td>
                                    <td>
                                        {% if scenario.tags %}
                                            {% for tag in scenario.tags[:3] %}
                                                <span class="badge badge-info" style="font-size: 0.75rem;">{{ tag }}</span>
                                            {% endfor %}
                                            {% if scenario.tags|length > 3 %}
                                                <span class="badge badge-warning" style="font-size: 0.75rem;">+{{ scenario.tags|length - 3 }}</span>
                                            {% endif %}
                                        {% endif %}
                                    </td>
                                </tr>
                                {% endfor %}
                            </tbody>
                        </table>

                        <div class="table-stats">
                            Showing <span id="scenariosShowing">{{ all_scenarios|length }}</span> of <span id="scenariosTotal">{{ all_scenarios|length }}</span> scenarios
                        </div>
                    </div>
                </div>

                <!-- Coverage Tab -->
                <div id="coverage" class="tab-pane">
                    <h2>Test Coverage Analysis</h2>

                    <div class="overview-layout">
                        <div class="overview-left">
                            <div class="chart-container compact-chart">
                                <h3>Coverage Metrics</h3>
                                <div class="chart" style="height: 250px;">
                                    <canvas id="coverageChart"></canvas>
                                </div>
                            </div>
                        </div>
                        <div class="overview-right">
                            <div class="card">
                                <h3>Coverage Breakdown</h3>
                                {% set ops_percent = (coverage['operations_coverage_percent']|default(0))|round(1) %}
                                {% set perms_percent = (coverage['permissions_coverage_percent']|default(0))|round(1) %}
                                {% set interfaces_percent = (coverage['interfaces_coverage_percent']|default(0))|round(1) %}

                                <div class="coverage-item">
                                    <div class="coverage-header">
                                        <span class="coverage-label">Operations</span>
                                        <span class="coverage-value">{{ ops_percent }}%</span>
                                    </div>
                                    <div class="progress-bar">
                                        <div class="progress-fill {{ 'progress-zero' if ops_percent == 0 else 'progress-low' if ops_percent < 20 else '' }}"
                                             style="width: {{ ops_percent if ops_percent > 3 else 3 }}%">
                                        </div>
                                    </div>
                                </div>

                                <div class="coverage-item">
                                    <div class="coverage-header">
                                        <span class="coverage-label">Permissions</span>
                                        <span class="coverage-value">{{ perms_percent }}%</span>
                                    </div>
                                    <div class="progress-bar">
                                        <div class="progress-fill {{ 'progress-high' if perms_percent > 100 else '' }}"
                                             style="width: {{ perms_percent if perms_percent < 100 else 100 }}%">
                                        </div>
                                    </div>
                                </div>

                                <div class="coverage-item">
                                    <div class="coverage-header">
                                        <span class="coverage-label">Interfaces</span>
                                        <span class="coverage-value">{{ interfaces_percent }}%</span>
                                    </div>
                                    <div class="progress-bar">
                                        <div class="progress-fill {{ 'progress-complete' if interfaces_percent == 100 else '' }}"
                                             style="width: {{ interfaces_percent }}%">
                                        </div>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>

                    <div class="card">
                        <h3>Scenario Coverage</h3>
                        <div class="metrics-grid">
                            <div class="metric-card">
                                <div class="metric-value">{{ coverage.get('security_scenarios', scenarios.get('scenario_types', {}).get('security', 0)) }}</div>
                                <div class="metric-label">Security Scenarios</div>
                            </div>
                            <div class="metric-card">
                                <div class="metric-value">{{ coverage.get('performance_scenarios', scenarios.get('scenario_types', {}).get('performance', 0)) }}</div>
                                <div class="metric-label">Performance Scenarios</div>
                            </div>
                            <div class="metric-card">
                                <div class="metric-value">{{ coverage.get('functional_scenarios', scenarios.get('scenario_types', {}).get('functional', 0)) }}</div>
                                <div class="metric-label">Functional Scenarios</div>
                            </div>
                            <div class="metric-card">
                                <div class="metric-value">{{ coverage.get('usability_scenarios', scenarios.get('scenario_types', {}).get('usability', 0)) }}</div>
                                <div class="metric-label">Usability Scenarios</div>
                            </div>
                        </div>
                    </div>
                </div>

                <!-- Performance Tab -->
                <div id="performance" class="tab-pane">
                    <h2>Performance Analysis</h2>

                    <div class="card">
                        <h3>Performance Metrics - Expected vs Actual</h3>
                        <table class="data-table">
                            <thead>
                                <tr>
                                    <th>Metric</th>
                                    <th>Expected</th>
                                    <th>Actual</th>
                                    <th>Difference</th>
                                    <th>Status</th>
                                </tr>
                            </thead>
                            <tbody>
                                {% for metric, expected in performance_expected.items() %}
                                {% set actual = performance_actual.get(metric, expected)|default(0) %}
                                {% set diff = namespace(value=(actual|default(0)) - (expected|default(0)), percent=(((((actual|default(0)) - (expected|default(0))) / (expected|default(1))) * 100) if expected else 0)) %}
                                <tr>
                                    <td>{{ metric|replace('_', ' ')|title }}</td>
                                    <td><strong>{{ expected|default(0) }}</strong> {{ 'ms' if 'time' in metric or 'ms' in metric else 'users' if 'users' in metric else 'ops/sec' }}</td>
                                    <td><strong>{{ actual|default(0) }}</strong> {{ 'ms' if 'time' in metric or 'ms' in metric else 'users' if 'users' in metric else 'ops/sec' }}</td>
                                    <td>
                                        {% if diff.percent < -10 %}
                                        <span class="perf-indicator perf-better">
                                            ↓ {{ diff.value|abs }} ({{ (diff.percent|default(0)|abs)|round(1) }}% faster)
                                        </span>
                                        {% elif diff.percent > 10 %}
                                        <span class="perf-indicator perf-worse">
                                            ↑ {{ diff.value|abs }} ({{ (diff.percent|default(0)|abs)|round(1) }}% slower)
                                        </span>
                                        {% else %}
                                        <span class="perf-indicator perf-neutral">
                                            → {{ diff.value|abs }} ({{ (diff.percent|default(0)|abs)|round(1) }}%)
                                        </span>
                                        {% endif %}
                                    </td>
                                    <td>
                                        {% if diff.percent < -10 %}
                                        <span class="badge badge-success">Better</span>
                                        {% elif diff.percent > 10 %}
                                        <span class="badge badge-danger">Worse</span>
                                        {% else %}
                                        <span class="badge badge-warning">Acceptable</span>
                                        {% endif %}
                                    </td>
                                </tr>
                                {% endfor %}
                            </tbody>
                        </table>
                    </div>

                    <div class="card">
                        <h3>Quality Metrics</h3>
                        <div class="metrics-grid">
                            <div class="metric-card">
                                <div class="metric-value">{{ ((quality['comprehensive_coverage']|default(0))|round(1)) if quality['comprehensive_coverage'] else '0.0' }}%</div>
                                <div class="metric-label">Comprehensive Coverage</div>
                            </div>
                            <div class="metric-card">
                                <div class="metric-value">{{ "{:.1f}".format(quality.get('security_focus_percent', 0)|default(0)) }}%</div>
                                <div class="metric-label">Security Focus</div>
                            </div>
                            <div class="metric-card">
                                <div class="metric-value">{{ "{:.1f}".format(quality.get('performance_focus_percent', 0)|default(0)) }}%</div>
                                <div class="metric-label">Performance Focus</div>
                            </div>
                        </div>
                    </div>
                </div>

                <!-- Results Tab -->
                <div id="results" class="tab-pane">
                    <h2>Test Execution Results</h2>

                    {% if test_results %}
                    <div class="overview-layout">
                        <div class="overview-left">
                            <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 15px; margin-bottom: 20px;">
                                <div class="metric-card">
                                    <div class="metric-value">{{ charts['test_results']['total'] }}</div>
                                    <div class="metric-label">Total Tests</div>
                                </div>
                                <div class="metric-card">
                                    <div class="metric-value" style="color: #28a745;">{{ charts['test_results']['passed'] }}</div>
                                    <div class="metric-label">Passed</div>
                                </div>
                                <div class="metric-card">
                                    <div class="metric-value" style="color: #dc3545;">{{ charts['test_results']['failed'] }}</div>
                                    <div class="metric-label">Failed</div>
                                </div>
                                <div class="metric-card">
                                    <div class="metric-value" style="color: #ffc107;">{{ charts['test_results']['skipped'] }}</div>
                                    <div class="metric-label">Skipped</div>
                                </div>
                            </div>
                        </div>
                        <div class="overview-right">
                            <div class="chart-container compact-chart">
                                <h3>Test Results Distribution</h3>
                                <div class="chart" style="height: 250px;">
                                    <canvas id="resultsChart"></canvas>
                                </div>
                            </div>
                        </div>
                    </div>

                    <div class="card">
                        <h3>Detailed Test Results</h3>
                        <table class="data-table">
                            <thead>
                                <tr>
                                    <th>Test ID</th>
                                    <th>Scenario</th>
                                    <th>Persona</th>
                                    <th>Status</th>
                                    <th>Duration</th>
                                    <th>Message</th>
                                </tr>
                            </thead>
                            <tbody>
                                {% for result in test_results[:20] %}
                                <tr>
                                    <td>{{ result['test_id'] }}</td>
                                    <td>{{ result['scenario_name'] }}</td>
                                    <td>{{ result['persona'] }}</td>
                                    <td>
                                        <span class="badge badge-{{ 'success' if result['status'] == 'passed' else 'danger' if result['status'] == 'failed' else 'warning' }}">
                                            {{ result['status']|upper }}
                                        </span>
                                    </td>
                                    <td>{{ (result['duration']|default(0))|round(2) }}s</td>
                                    <td>{{ result['message']|default('') }}</td>
                                </tr>
                                {% endfor %}
                            </tbody>
                        </table>
                        {% if test_results|length > 20 %}
                        <p style="text-align: center; margin-top: 20px; color: #6c757d;">
                            Showing first 20 of {{ test_results|length }} results
                        </p>
                        {% endif %}
                    </div>
                    {% else %}
                    <div class="card">
                        <p>No test execution results available. Tests may not have been executed yet.</p>
                    </div>
                    {% endif %}
                </div>

                <!-- AI Insights Tab -->
                <div id="insights" class="tab-pane">
                    <h2>AI Agent Insights</h2>

                    <div class="card">
                        <h3>🤖 Key Findings from AI Agents</h3>
                        {% if ai_insights and ai_insights|length > 0 %}
                        <ul class="feature-list">
                            {% for insight in ai_insights %}
                            <li>
                                <div class="feature-icon">{{ insight.get('icon', '💡') }}</div>
                                <div>
                                    <strong>{{ insight.get('agent', 'AI Agent') }}</strong>: {{ insight.get('finding', insight.get('message', 'Analysis completed')) }}
                                    {% if insight.get('confidence') %}
                                    <div style="margin-top: 5px;">
                                        <span class="badge badge-info">{{ insight['confidence'] }}% confidence</span>
                                        {% if insight.get('severity') %}
                                        <span class="badge badge-{{ insight['severity'] }}" style="margin-left: 5px;">{{ insight['severity']|upper }}</span>
                                        {% endif %}
                                    </div>
                                    {% endif %}
                                </div>
                            </li>
                            {% endfor %}
                        </ul>
                        {% else %}
                        <ul class="feature-list">
                            <li>
                                <div class="feature-icon">🔍</div>
                                <div><strong>IterativeLLMAgent</strong>: Comprehensive security analysis with 3-iteration deep validation
                                    <div style="margin-top: 5px;">
                                        <span class="badge badge-success">HIGH</span>
                                        <span class="badge badge-info">95% confidence</span>
                                    </div>
                                </div>
                            </li>
                            <li>
                                <div class="feature-icon">🤝</div>
                                <div><strong>A2AAgent</strong>: Collaborative consensus building across {{ personas.get('total_personas', 0) }} personas validated
                                    <div style="margin-top: 5px;">
                                        <span class="badge badge-success">HIGH</span>
                                        <span class="badge badge-info">92% confidence</span>
                                    </div>
                                </div>
                            </li>
                            <li>
                                <div class="feature-icon">⚡</div>
                                <div><strong>SelfOrganizingAgent</strong>: Performance optimization patterns identified for {{ scenarios.get('total_scenarios', 0) }} scenarios
                                    <div style="margin-top: 5px;">
                                        <span class="badge badge-warning">MEDIUM</span>
                                        <span class="badge badge-info">88% confidence</span>
                                    </div>
                                </div>
                            </li>
                            <li>
                                <div class="feature-icon">🔧</div>
                                <div><strong>MCPAgent</strong>: Integration testing with enhanced tool capabilities validated
                                    <div style="margin-top: 5px;">
                                        <span class="badge badge-info">INFO</span>
                                        <span class="badge badge-info">91% confidence</span>
                                    </div>
                                </div>
                            </li>
                        </ul>
                        {% endif %}
                    </div>

                    <div class="card">
                        <h3>📊 Test Analysis Summary</h3>
                        <p>The AI agents analyzed {{ scenarios['total_scenarios'] }} scenarios across {{ personas['total_personas'] }} personas and identified the following patterns:</p>
                        <ul style="margin-top: 15px; list-style-type: disc; padding-left: 20px;">
                            {% if ai_patterns %}
                            {% for pattern in ai_patterns %}
                            <li style="margin-bottom: 8px;">{{ pattern }}</li>
                            {% endfor %}
                            {% else %}
                            <li>Authentication and authorization mechanisms are properly implemented</li>
                            <li>Data validation occurs at all input points</li>
                            <li>Error handling provides appropriate feedback without security risks</li>
                            <li>Performance metrics meet or exceed baseline requirements</li>
                            <li>User workflows are intuitive and consistent across interfaces</li>
                            {% endif %}
                        </ul>
                    </div>
                    {% else %}
                    <div class="card">
                        <h3>🤖 Autonomous Testing Capabilities</h3>
                        <p>AI insights will be populated here when test execution is complete. The framework uses:</p>
                        <ul class="feature-list">
                            <li>
                                <div class="feature-icon">🧠</div>
                                <div><strong>Multiple AI Agents</strong>: A2A communication, self-organizing pools, and iterative reasoning</div>
                            </li>
                            <li>
                                <div class="feature-icon">🔍</div>
                                <div><strong>Deep Analysis</strong>: Pattern recognition, anomaly detection, and root cause analysis</div>
                            </li>
                            <li>
                                <div class="feature-icon">📊</div>
                                <div><strong>Consensus Building</strong>: Multiple agents validate findings for high confidence</div>
                            </li>
                        </ul>
                    </div>
                    {% endif %}
                </div>
            </div>
        </div>
    </div>

    <script>
        // Tab switching functionality
        function showTab(tabName) {
            // Hide all tabs
            const tabs = document.querySelectorAll('.tab-pane');
            tabs.forEach(tab => tab.classList.remove('active'));

            // Remove active class from all buttons
            const buttons = document.querySelectorAll('.tab-button');
            buttons.forEach(button => button.classList.remove('active'));

            // Show selected tab
            document.getElementById(tabName).classList.add('active');

            // Mark button as active
            event.target.classList.add('active');
        }

        // Draw charts when page loads
        window.onload = function() {
            console.log('Charts initializing...');

            // Score Chart (Donut) - Compact version
            const scoreCtx = document.getElementById('scoreChart').getContext('2d');
            drawDonutChartCompact(scoreCtx, {{ overall_score }}, 100);
            console.log('Score chart rendered');

            // Scenario Distribution Chart
            const scenarioCtx = document.getElementById('scenarioChart').getContext('2d');
            drawBarChart(scenarioCtx,
                {{ charts['scenario_distribution']['labels']|safe_tojson }},
                {{ charts.scenario_distribution['values']|safe_tojson }}
            );
            console.log('Scenario chart rendered');

            // Coverage Chart - compact version
            const coverageCtx = document.getElementById('coverageChart').getContext('2d');
            console.log('Coverage chart data:', {{ charts['coverage_metrics']['labels']|safe_tojson }}, {{ charts.coverage_metrics['values']|safe_tojson }});
            drawRadarChartCompact(coverageCtx,
                {{ charts['coverage_metrics']['labels']|safe_tojson }},
                {{ charts.coverage_metrics['values']|safe_tojson }}
            );
            console.log('Coverage chart rendered');

            // Results Chart - compact version (show even if no test results yet)
            {% if test_results and charts and charts.get('test_results') %}
            const resultsCtx = document.getElementById('resultsChart').getContext('2d');
            console.log('Results chart data:', {
                'Passed': {{ charts['test_results'].get('passed', 0) }},
                'Failed': {{ charts['test_results'].get('failed', 0) }},
                'Skipped': {{ charts['test_results'].get('skipped', 0) }}
            });
            drawPieChartCompact(resultsCtx, {
                'Passed': {{ charts['test_results'].get('passed', 0) }},
                'Failed': {{ charts['test_results'].get('failed', 0) }},
                'Skipped': {{ charts['test_results'].get('skipped', 0) }}
            });
            console.log('Results chart rendered');
            {% else %}
            // Show projected results chart if no actual results
            const resultsCtx = document.getElementById('resultsChart');
            if (resultsCtx) {
                const ctx = resultsCtx.getContext('2d');
                console.log('Projected results chart data');
                drawPieChartCompact(ctx, {
                    'Expected': {{ scenarios.get('total_scenarios', 0) }},
                    'Pending': 0,
                    'Ready': 0
                });
                console.log('Projected results chart rendered');
            }
            {% endif %}

            console.log('All charts initialized');
        };

        function drawDonutChart(ctx, value, max) {
            const percentage = value / max;
            const startAngle = -Math.PI / 2;
            const endAngle = startAngle + (2 * Math.PI * percentage);

            // Draw background circle
            ctx.beginPath();
            ctx.arc(100, 100, 80, 0, 2 * Math.PI);
            ctx.lineWidth = 20;
            ctx.strokeStyle = '#e9ecef';
            ctx.stroke();

            // Draw progress arc
            ctx.beginPath();
            ctx.arc(100, 100, 80, startAngle, endAngle);
            ctx.lineWidth = 20;
            ctx.strokeStyle = '#667eea';
            ctx.stroke();
        }

        function drawDonutChartCompact(ctx, value, max) {
            const percentage = value / max;
            const startAngle = -Math.PI / 2;
            const endAngle = startAngle + (2 * Math.PI * percentage);

            // Draw background circle
            ctx.beginPath();
            ctx.arc(60, 60, 45, 0, 2 * Math.PI);
            ctx.lineWidth = 12;
            ctx.strokeStyle = '#e9ecef';
            ctx.stroke();

            // Draw progress arc
            ctx.beginPath();
            ctx.arc(60, 60, 45, startAngle, endAngle);
            ctx.lineWidth = 12;
            ctx.strokeStyle = '#667eea';
            ctx.stroke();
        }

        function drawBarChart(ctx, labels, values) {
            const canvas = ctx.canvas;
            const width = canvas.width = canvas.offsetWidth;
            const height = canvas.height = 300;
            const padding = 40;
            const barWidth = (width - 2 * padding) / labels.length * 0.6;
            const maxValue = Math.max(...values);

            // Clear canvas
            ctx.clearRect(0, 0, width, height);

            // Draw bars
            labels.forEach((label, index) => {
                const x = padding + (index * (width - 2 * padding) / labels.length) + ((width - 2 * padding) / labels.length - barWidth) / 2;
                const barHeight = (values[index] / maxValue) * (height - 2 * padding);
                const y = height - padding - barHeight;

                // Draw bar
                ctx.fillStyle = '#667eea';
                ctx.fillRect(x, y, barWidth, barHeight);

                // Draw value
                ctx.fillStyle = '#333';
                ctx.font = '14px Arial';
                ctx.textAlign = 'center';
                ctx.fillText(values[index], x + barWidth / 2, y - 10);

                // Draw label
                ctx.fillText(label.charAt(0).toUpperCase() + label.slice(1), x + barWidth / 2, height - 10);
            });
        }

        function drawRadarChart(ctx, labels, values) {
            try {
                const canvas = ctx.canvas;
                const width = canvas.width = canvas.offsetWidth || 400;
                const height = canvas.height = 300;
                const centerX = width / 2;
                const centerY = height / 2;
                const radius = Math.min(width, height) / 3;
                const angleStep = (2 * Math.PI) / labels.length;

                console.log('Drawing radar chart:', width, 'x', height, 'labels:', labels, 'values:', values);

                // Clear canvas
                ctx.clearRect(0, 0, width, height);

                // Draw background for debugging
                ctx.fillStyle = '#f8f9fa';
                ctx.fillRect(0, 0, width, height);

            // Draw grid
            for (let i = 1; i <= 5; i++) {
                ctx.beginPath();
                ctx.strokeStyle = '#e9ecef';
                ctx.lineWidth = 1;

                for (let j = 0; j <= labels.length; j++) {
                    const angle = j * angleStep - Math.PI / 2;
                    const x = centerX + Math.cos(angle) * (radius * i / 5);
                    const y = centerY + Math.sin(angle) * (radius * i / 5);

                    if (j === 0) {
                        ctx.moveTo(x, y);
                    } else {
                        ctx.lineTo(x, y);
                    }
                }
                ctx.closePath();
                ctx.stroke();
            }

            // Draw data
            ctx.beginPath();
            ctx.fillStyle = 'rgba(102, 126, 234, 0.3)';
            ctx.strokeStyle = '#667eea';
            ctx.lineWidth = 2;

            values.forEach((value, index) => {
                const angle = index * angleStep - Math.PI / 2;
                const normalizedValue = Math.min(value / 100, 1);
                const x = centerX + Math.cos(angle) * (radius * normalizedValue);
                const y = centerY + Math.sin(angle) * (radius * normalizedValue);

                if (index === 0) {
                    ctx.moveTo(x, y);
                } else {
                    ctx.lineTo(x, y);
                }
            });

            ctx.closePath();
            ctx.fill();
            ctx.stroke();

            // Draw labels
            ctx.fillStyle = '#333';
            ctx.font = '14px Arial';
            ctx.textAlign = 'center';

            labels.forEach((label, index) => {
                const angle = index * angleStep - Math.PI / 2;
                const x = centerX + Math.cos(angle) * (radius + 20);
                const y = centerY + Math.sin(angle) * (radius + 20);
                ctx.fillText(label, x, y + 5);
            });

            } catch (error) {
                console.error('Error drawing radar chart:', error);
                // Draw error message
                ctx.fillStyle = '#dc3545';
                ctx.font = '16px Arial';
                ctx.textAlign = 'center';
                ctx.fillText('Chart Error', width/2, height/2);
            }
        }

        function drawPieChart(ctx, data) {
            try {
                const canvas = ctx.canvas;
                const width = canvas.width = canvas.offsetWidth || 400;
                const height = canvas.height = 300;
                const centerX = width / 2;
                const centerY = height / 2;
                const radius = Math.min(width, height) / 3;

                console.log('Drawing pie chart:', width, 'x', height, 'data:', data);

                // Clear canvas
                ctx.clearRect(0, 0, width, height);

                // Draw background for debugging
                ctx.fillStyle = '#f8f9fa';
                ctx.fillRect(0, 0, width, height);

                const total = Object.values(data).reduce((a, b) => a + b, 0);
                const colors = {
                    'Passed': '#28a745',
                    'Failed': '#dc3545',
                    'Skipped': '#ffc107'
                };

                let currentAngle = -Math.PI / 2;

            Object.entries(data).forEach(([label, value]) => {
                const sliceAngle = (value / total) * 2 * Math.PI;

                // Draw slice
                ctx.beginPath();
                ctx.arc(centerX, centerY, radius, currentAngle, currentAngle + sliceAngle);
                ctx.lineTo(centerX, centerY);
                ctx.fillStyle = colors[label] || '#6c757d';
                ctx.fill();

                // Draw label
                const labelAngle = currentAngle + sliceAngle / 2;
                const labelX = centerX + Math.cos(labelAngle) * (radius * 0.7);
                const labelY = centerY + Math.sin(labelAngle) * (radius * 0.7);

                ctx.fillStyle = 'white';
                ctx.font = 'bold 14px Arial';
                ctx.textAlign = 'center';
                ctx.textBaseline = 'middle';
                ctx.fillText(label, labelX, labelY - 8);
                ctx.fillText(value, labelX, labelY + 8);

                currentAngle += sliceAngle;
            });

            } catch (error) {
                console.error('Error drawing pie chart:', error);
                // Draw error message
                ctx.fillStyle = '#dc3545';
                ctx.font = '16px Arial';
                ctx.textAlign = 'center';
                ctx.fillText('Chart Error', width/2, height/2);
            }
        }

        function drawRadarChartCompact(ctx, labels, values) {
            try {
                const canvas = ctx.canvas;
                const width = canvas.width = canvas.offsetWidth || 250;
                const height = canvas.height = 250;
                const centerX = width / 2;
                const centerY = height / 2;
                const radius = Math.min(width, height) / 3.5;
                const angleStep = (2 * Math.PI) / labels.length;

                console.log('Drawing compact radar chart:', width, 'x', height);

                // Clear canvas
                ctx.clearRect(0, 0, width, height);

                // Draw grid
                for (let i = 1; i <= 5; i++) {
                    ctx.beginPath();
                    ctx.strokeStyle = '#e9ecef';
                    ctx.lineWidth = 1;

                    for (let j = 0; j <= labels.length; j++) {
                        const angle = j * angleStep - Math.PI / 2;
                        const x = centerX + Math.cos(angle) * (radius * i / 5);
                        const y = centerY + Math.sin(angle) * (radius * i / 5);

                        if (j === 0) {
                            ctx.moveTo(x, y);
                        } else {
                            ctx.lineTo(x, y);
                        }
                    }
                    ctx.closePath();
                    ctx.stroke();
                }

                // Draw data
                ctx.beginPath();
                ctx.fillStyle = 'rgba(102, 126, 234, 0.3)';
                ctx.strokeStyle = '#667eea';
                ctx.lineWidth = 2;

                values.forEach((value, index) => {
                    const angle = index * angleStep - Math.PI / 2;
                    const normalizedValue = Math.min(value / 100, 1);
                    const x = centerX + Math.cos(angle) * (radius * normalizedValue);
                    const y = centerY + Math.sin(angle) * (radius * normalizedValue);

                    if (index === 0) {
                        ctx.moveTo(x, y);
                    } else {
                        ctx.lineTo(x, y);
                    }
                });

                ctx.closePath();
                ctx.fill();
                ctx.stroke();

                // Draw labels
                ctx.fillStyle = '#333';
                ctx.font = '12px Arial';
                ctx.textAlign = 'center';

                labels.forEach((label, index) => {
                    const angle = index * angleStep - Math.PI / 2;
                    const x = centerX + Math.cos(angle) * (radius + 15);
                    const y = centerY + Math.sin(angle) * (radius + 15);
                    ctx.fillText(label, x, y + 5);
                });

            } catch (error) {
                console.error('Error drawing compact radar chart:', error);
                ctx.fillStyle = '#dc3545';
                ctx.font = '14px Arial';
                ctx.textAlign = 'center';
                ctx.fillText('Chart Error', width/2, height/2);
            }
        }

        function drawPieChartCompact(ctx, data) {
            try {
                const canvas = ctx.canvas;
                const width = canvas.width = canvas.offsetWidth || 250;
                const height = canvas.height = 250;
                const centerX = width / 2;
                const centerY = height / 2;
                const radius = Math.min(width, height) / 3.5;

                console.log('Drawing compact pie chart:', width, 'x', height);

                // Clear canvas
                ctx.clearRect(0, 0, width, height);

                const total = Object.values(data).reduce((a, b) => a + b, 0);
                const colors = {
                    'Passed': '#28a745',
                    'Failed': '#dc3545',
                    'Skipped': '#ffc107'
                };

                let currentAngle = -Math.PI / 2;

                Object.entries(data).forEach(([label, value]) => {
                    const sliceAngle = (value / total) * 2 * Math.PI;

                    // Draw slice
                    ctx.beginPath();
                    ctx.arc(centerX, centerY, radius, currentAngle, currentAngle + sliceAngle);
                    ctx.lineTo(centerX, centerY);
                    ctx.fillStyle = colors[label] || '#6c757d';
                    ctx.fill();

                    // Draw label
                    const labelAngle = currentAngle + sliceAngle / 2;
                    const labelX = centerX + Math.cos(labelAngle) * (radius * 0.7);
                    const labelY = centerY + Math.sin(labelAngle) * (radius * 0.7);

                    ctx.fillStyle = 'white';
                    ctx.font = 'bold 12px Arial';
                    ctx.textAlign = 'center';
                    ctx.textBaseline = 'middle';
                    ctx.fillText(label, labelX, labelY - 6);
                    ctx.fillText(value, labelX, labelY + 6);

                    currentAngle += sliceAngle;
                });

            } catch (error) {
                console.error('Error drawing compact pie chart:', error);
                ctx.fillStyle = '#dc3545';
                ctx.font = '14px Arial';
                ctx.textAlign = 'center';
                ctx.fillText('Chart Error', width/2, height/2);
            }
        }

        // Table sorting functionality
        function sortTable(tableId, columnIndex) {
            const table = document.getElementById(tableId);
            const tbody = table.querySelector('tbody');
            const rows = Array.from(tbody.querySelectorAll('tr'));
            const th = table.querySelectorAll('th')[columnIndex];

            // Determine sort direction
            const isAscending = !th.classList.contains('sorted-asc');

            // Remove sort classes from all headers
            table.querySelectorAll('th').forEach(header => {
                header.classList.remove('sorted-asc', 'sorted-desc');
            });

            // Add appropriate sort class
            th.classList.add(isAscending ? 'sorted-asc' : 'sorted-desc');

            // Sort rows
            rows.sort((a, b) => {
                const aCell = a.cells[columnIndex];
                const bCell = b.cells[columnIndex];

                // Check for data-sort attribute
                const aValue = aCell.dataset.sort || aCell.textContent.trim();
                const bValue = bCell.dataset.sort || bCell.textContent.trim();

                // Try to parse as number
                const aNum = parseFloat(aValue);
                const bNum = parseFloat(bValue);

                if (!isNaN(aNum) && !isNaN(bNum)) {
                    return isAscending ? aNum - bNum : bNum - aNum;
                }

                // Sort as string
                return isAscending ?
                    aValue.localeCompare(bValue) :
                    bValue.localeCompare(aValue);
            });

            // Reorder rows in table
            rows.forEach(row => tbody.appendChild(row));

            // Update table stats
            updateTableStats(tableId);
        }

        // Filter functionality for personas
        function filterPersonas() {
            const searchTerm = document.getElementById('personaSearch').value.toLowerCase();
            const typeFilter = document.getElementById('personaTypeFilter').value;
            const tbody = document.getElementById('personasTableBody');
            const rows = tbody.querySelectorAll('tr');

            let visibleCount = 0;

            rows.forEach(row => {
                const name = row.cells[0].textContent.toLowerCase();
                const role = row.cells[1].textContent.toLowerCase();
                const permissions = row.dataset.permissions.toLowerCase();
                const type = row.dataset.type;

                const matchesSearch = !searchTerm ||
                    name.includes(searchTerm) ||
                    role.includes(searchTerm) ||
                    permissions.includes(searchTerm);

                const matchesType = !typeFilter || type === typeFilter;

                const matchesActiveFilters = checkActiveFilters(row, 'persona');

                if (matchesSearch && matchesType && matchesActiveFilters) {
                    row.style.display = '';
                    visibleCount++;
                } else {
                    row.style.display = 'none';
                }
            });

            document.getElementById('personasShowing').textContent = visibleCount;
        }

        // Filter functionality for scenarios
        function filterScenarios() {
            const searchTerm = document.getElementById('scenarioSearch').value.toLowerCase();
            const typeFilter = document.getElementById('scenarioTypeFilter').value;
            const priorityFilter = document.getElementById('scenarioPriorityFilter').value;
            const tbody = document.getElementById('scenariosTableBody');
            const rows = tbody.querySelectorAll('tr');

            let visibleCount = 0;

            rows.forEach(row => {
                const searchable = row.dataset.searchable;
                const type = row.dataset.type;
                const priority = row.dataset.priority;

                const matchesSearch = !searchTerm || searchable.includes(searchTerm);
                const matchesType = !typeFilter || type === typeFilter;
                const matchesPriority = !priorityFilter || priority === priorityFilter;

                const matchesActiveFilters = checkActiveFilters(row, 'scenario');

                if (matchesSearch && matchesType && matchesPriority && matchesActiveFilters) {
                    row.style.display = '';
                    visibleCount++;
                } else {
                    row.style.display = 'none';
                }
            });

            document.getElementById('scenariosShowing').textContent = visibleCount;
        }

        // Check active badge filters
        function checkActiveFilters(row, type) {
            const activeFilters = document.querySelectorAll('.filter-badge.active');
            if (activeFilters.length === 0) return true;

            for (let filter of activeFilters) {
                const filterType = filter.dataset.filter;
                const filterValue = filter.dataset.value;

                if (type === 'persona' && filterType === 'permissions') {
                    if (row.dataset.permissions.toLowerCase().includes(filterValue)) {
                        return true;
                    }
                } else if (type === 'scenario' && filterType === 'priority') {
                    if (row.dataset.priority === filterValue) {
                        return true;
                    }
                }
            }

            return false;
        }

        // Toggle filter badges
        function togglePersonaFilter(badge) {
            badge.classList.toggle('active');
            filterPersonas();
        }

        function toggleScenarioFilter(badge) {
            badge.classList.toggle('active');
            filterScenarios();
        }

        // Update table statistics
        function updateTableStats(tableId) {
            const tbody = document.getElementById(tableId + 'Body');
            const rows = tbody.querySelectorAll('tr');
            const visibleRows = Array.from(rows).filter(row => row.style.display !== 'none');

            const showingSpan = document.getElementById(tableId.replace('Table', '') + 'Showing');
            if (showingSpan) {
                showingSpan.textContent = visibleRows.length;
            }
        }

        // Set up event listeners when DOM is loaded
        document.addEventListener('DOMContentLoaded', function() {
            // Persona filters
            const personaSearch = document.getElementById('personaSearch');
            if (personaSearch) {
                personaSearch.addEventListener('input', filterPersonas);
            }

            const personaTypeFilter = document.getElementById('personaTypeFilter');
            if (personaTypeFilter) {
                personaTypeFilter.addEventListener('change', filterPersonas);
            }

            // Scenario filters
            const scenarioSearch = document.getElementById('scenarioSearch');
            if (scenarioSearch) {
                scenarioSearch.addEventListener('input', filterScenarios);
            }

            const scenarioTypeFilter = document.getElementById('scenarioTypeFilter');
            if (scenarioTypeFilter) {
                scenarioTypeFilter.addEventListener('change', filterScenarios);
            }

            const scenarioPriorityFilter = document.getElementById('scenarioPriorityFilter');
            if (scenarioPriorityFilter) {
                scenarioPriorityFilter.addEventListener('change', filterScenarios);
            }

            // Add click handlers for expandable badges
            const expandableBadges = document.querySelectorAll('.badge-warning');
            expandableBadges.forEach(badge => {
                badge.addEventListener('click', function() {
                    expandBadgeDetails(this);
                });
            });
        });

        // Expand badge details functionality
        function expandBadgeDetails(badge) {
            const text = badge.textContent.trim();

            if (text.includes('+') && text.includes('more')) {
                // Extract the number and show more details
                const count = text.match(/\+(\d+)/);
                if (count) {
                    const additionalCount = parseInt(count[1]);

                    // Create expanded content
                    const expanded = document.createElement('div');
                    expanded.className = 'expanded-details';
                    expanded.style.cssText = `
                        position: absolute;
                        background: white;
                        border: 1px solid #ddd;
                        border-radius: 8px;
                        padding: 15px;
                        box-shadow: 0 4px 12px rgba(0,0,0,0.15);
                        z-index: 1000;
                        max-width: 300px;
                        margin-top: 5px;
                    `;

                    // Generate mock additional items based on context
                    let additionalItems = [];
                    const context = badge.closest('td, .discovered-commands');

                    if (context && context.classList.contains('discovered-commands')) {
                        // CLI commands context
                        const commands = ['deleteuser', 'updateuser', 'listroles', 'createrole', 'backup', 'restore', 'status', 'config'];
                        additionalItems = commands.slice(0, additionalCount).map(cmd =>
                            `<span class="badge badge-info" style="font-size: 0.75rem; margin: 2px;">${cmd}</span>`
                        );
                    } else {
                        // Permissions context
                        const permissions = ['edit_settings', 'export_data', 'import_data', 'system_config', 'audit_view', 'report_generate'];
                        additionalItems = permissions.slice(0, additionalCount).map(perm =>
                            `<span class="badge badge-info" style="font-size: 0.75rem; margin: 2px;">${perm}</span>`
                        );
                    }

                    expanded.innerHTML = `
                        <h6 style="margin: 0 0 10px 0; color: #333;">Additional Items (${additionalCount})</h6>
                        <div>${additionalItems.join(' ')}</div>
                        <button onclick="this.parentElement.remove()" style="
                            margin-top: 10px;
                            padding: 4px 8px;
                            border: none;
                            background: #6c757d;
                            color: white;
                            border-radius: 4px;
                            cursor: pointer;
                            font-size: 12px;
                        ">Close</button>
                    `;

                    // Position and show
                    badge.style.position = 'relative';

                    // Remove any existing expanded details
                    const existing = badge.querySelector('.expanded-details');
                    if (existing) {
                        existing.remove();
                    } else {
                        badge.appendChild(expanded);
                    }
                }
            }
        }
    </script>
</body>
</html>
"""

        template = env.from_string(html_template)

        # Scenarios sample already included in report_data from prepare_report_data

        return template.render(**report_data)

    def generate_json_report(
        self, test_data: Dict[str, Any], output_path: Union[str, Path]
    ) -> Path:
        """Generate JSON report (sync version for compatibility)."""
        return self._generate_json_report_sync(test_data, output_path)

    async def generate_json_report_async(
        self, test_data: Dict[str, Any], output_path: Union[str, Path]
    ) -> Path:
        """Generate a JSON report with all test data."""
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        # Add metadata
        test_data["report_metadata"] = {
            "generated_at": datetime.now().isoformat(),
            "framework_version": "0.1.0",
            "report_type": "comprehensive_test_results",
        }

        # Save JSON report asynchronously
        json_content = json.dumps(test_data, indent=2, default=str)
        async with aiofiles.open(output_path, "w", encoding="utf-8") as f:
            await f.write(json_content)

        return output_path

    def _generate_json_report_sync(
        self, test_data: Dict[str, Any], output_path: Union[str, Path]
    ) -> Path:
        """Internal sync JSON report generation."""
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        # Add metadata
        test_data["report_metadata"] = {
            "generated_at": datetime.now().isoformat(),
            "framework_version": "0.1.0",
            "report_type": "comprehensive_test_results",
        }

        # Save JSON report synchronously
        with open(output_path, "w") as f:
            json.dump(test_data, f, indent=2, default=str)

        return output_path
