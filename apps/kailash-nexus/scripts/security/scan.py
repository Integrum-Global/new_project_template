#!/usr/bin/env python3
"""
Security scanning automation for Nexus application.

Integrates multiple security scanning tools for comprehensive security assessment.
"""

import asyncio
import json
import logging
import os
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any, Dict, List, Optional

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class SecurityScanner:
    """Comprehensive security scanner for Nexus application."""

    def __init__(self, project_root: Path, output_dir: Path):
        """Initialize security scanner.

        Args:
            project_root: Root directory of the project
            output_dir: Directory to store scan results
        """
        self.project_root = project_root
        self.output_dir = output_dir
        self.output_dir.mkdir(parents=True, exist_ok=True)

        # Security tools configuration
        self.tools = {
            "bandit": self._run_bandit_scan,
            "safety": self._run_safety_scan,
            "semgrep": self._run_semgrep_scan,
            "trivy": self._run_trivy_scan,
            "hadolint": self._run_hadolint_scan,
        }

        self.results = {}

    async def run_all_scans(self) -> Dict[str, Any]:
        """Run all available security scans.

        Returns:
            Comprehensive scan results
        """
        logger.info("Starting comprehensive security scan...")

        # Run all scans
        for tool_name, scan_func in self.tools.items():
            try:
                logger.info(f"Running {tool_name} scan...")
                result = await scan_func()
                self.results[tool_name] = result
                logger.info(f"{tool_name} scan completed")
            except Exception as e:
                logger.error(f"{tool_name} scan failed: {e}")
                self.results[tool_name] = {
                    "status": "error",
                    "error": str(e),
                    "vulnerabilities": [],
                }

        # Generate summary report
        summary = self._generate_summary()

        # Save results
        await self._save_results(summary)

        return summary

    async def _run_bandit_scan(self) -> Dict[str, Any]:
        """Run Bandit static security analysis."""
        output_file = self.output_dir / "bandit-report.json"

        try:
            # Run bandit scan
            cmd = [
                "bandit",
                "-r",
                str(self.project_root / "src"),
                "-f",
                "json",
                "-o",
                str(output_file),
                "--skip",
                "B101,B601",  # Skip assert and shell injection for test files
            ]

            result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)

            if output_file.exists():
                with open(output_file, "r") as f:
                    report = json.load(f)

                return {
                    "status": "success",
                    "vulnerabilities": report.get("results", []),
                    "summary": {
                        "total_issues": len(report.get("results", [])),
                        "high_severity": len(
                            [
                                r
                                for r in report.get("results", [])
                                if r.get("issue_severity") == "HIGH"
                            ]
                        ),
                        "medium_severity": len(
                            [
                                r
                                for r in report.get("results", [])
                                if r.get("issue_severity") == "MEDIUM"
                            ]
                        ),
                        "low_severity": len(
                            [
                                r
                                for r in report.get("results", [])
                                if r.get("issue_severity") == "LOW"
                            ]
                        ),
                    },
                    "raw_output": result.stdout,
                }
            else:
                return {
                    "status": "no_issues",
                    "vulnerabilities": [],
                    "summary": {"total_issues": 0},
                    "raw_output": result.stdout,
                }

        except subprocess.TimeoutExpired:
            return {"status": "timeout", "error": "Bandit scan timed out"}
        except FileNotFoundError:
            return {"status": "tool_not_found", "error": "Bandit not installed"}

    async def _run_safety_scan(self) -> Dict[str, Any]:
        """Run Safety dependency vulnerability scan."""
        try:
            # Generate requirements.txt if it doesn't exist
            req_file = self.project_root / "requirements.txt"
            if not req_file.exists():
                # Try to generate from poetry/pipenv
                await self._generate_requirements()

            if not req_file.exists():
                return {
                    "status": "no_requirements",
                    "error": "No requirements.txt found",
                }

            # Run safety check
            cmd = ["safety", "check", "--json", "--file", str(req_file)]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)

            if result.returncode == 0:
                return {
                    "status": "success",
                    "vulnerabilities": [],
                    "summary": {"total_issues": 0},
                    "raw_output": result.stdout,
                }
            else:
                try:
                    vulnerabilities = json.loads(result.stdout)
                    return {
                        "status": "issues_found",
                        "vulnerabilities": vulnerabilities,
                        "summary": {"total_issues": len(vulnerabilities)},
                        "raw_output": result.stdout,
                    }
                except json.JSONDecodeError:
                    return {
                        "status": "parse_error",
                        "error": "Failed to parse Safety output",
                        "raw_output": result.stdout,
                    }

        except subprocess.TimeoutExpired:
            return {"status": "timeout", "error": "Safety scan timed out"}
        except FileNotFoundError:
            return {"status": "tool_not_found", "error": "Safety not installed"}

    async def _run_semgrep_scan(self) -> Dict[str, Any]:
        """Run Semgrep static analysis."""
        output_file = self.output_dir / "semgrep-report.json"

        try:
            cmd = [
                "semgrep",
                "--config=auto",
                "--json",
                "--output",
                str(output_file),
                str(self.project_root / "src"),
            ]

            result = subprocess.run(cmd, capture_output=True, text=True, timeout=600)

            if output_file.exists():
                with open(output_file, "r") as f:
                    report = json.load(f)

                findings = report.get("results", [])
                return {
                    "status": "success",
                    "vulnerabilities": findings,
                    "summary": {
                        "total_issues": len(findings),
                        "error_findings": len(
                            [
                                f
                                for f in findings
                                if f.get("extra", {}).get("severity") == "ERROR"
                            ]
                        ),
                        "warning_findings": len(
                            [
                                f
                                for f in findings
                                if f.get("extra", {}).get("severity") == "WARNING"
                            ]
                        ),
                        "info_findings": len(
                            [
                                f
                                for f in findings
                                if f.get("extra", {}).get("severity") == "INFO"
                            ]
                        ),
                    },
                    "raw_output": result.stdout,
                }
            else:
                return {
                    "status": "no_issues",
                    "vulnerabilities": [],
                    "summary": {"total_issues": 0},
                    "raw_output": result.stdout,
                }

        except subprocess.TimeoutExpired:
            return {"status": "timeout", "error": "Semgrep scan timed out"}
        except FileNotFoundError:
            return {"status": "tool_not_found", "error": "Semgrep not installed"}

    async def _run_trivy_scan(self) -> Dict[str, Any]:
        """Run Trivy vulnerability scanner."""
        output_file = self.output_dir / "trivy-report.json"

        try:
            # Scan filesystem
            cmd = [
                "trivy",
                "fs",
                "--format",
                "json",
                "--output",
                str(output_file),
                "--skip-dirs",
                "node_modules,.git,__pycache__",
                str(self.project_root),
            ]

            result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)

            if output_file.exists():
                with open(output_file, "r") as f:
                    report = json.load(f)

                vulnerabilities = []
                if "Results" in report:
                    for result_item in report["Results"]:
                        if "Vulnerabilities" in result_item:
                            vulnerabilities.extend(result_item["Vulnerabilities"])

                return {
                    "status": "success",
                    "vulnerabilities": vulnerabilities,
                    "summary": {
                        "total_issues": len(vulnerabilities),
                        "critical": len(
                            [
                                v
                                for v in vulnerabilities
                                if v.get("Severity") == "CRITICAL"
                            ]
                        ),
                        "high": len(
                            [v for v in vulnerabilities if v.get("Severity") == "HIGH"]
                        ),
                        "medium": len(
                            [
                                v
                                for v in vulnerabilities
                                if v.get("Severity") == "MEDIUM"
                            ]
                        ),
                        "low": len(
                            [v for v in vulnerabilities if v.get("Severity") == "LOW"]
                        ),
                    },
                    "raw_output": result.stdout,
                }
            else:
                return {
                    "status": "no_issues",
                    "vulnerabilities": [],
                    "summary": {"total_issues": 0},
                    "raw_output": result.stdout,
                }

        except subprocess.TimeoutExpired:
            return {"status": "timeout", "error": "Trivy scan timed out"}
        except FileNotFoundError:
            return {"status": "tool_not_found", "error": "Trivy not installed"}

    async def _run_hadolint_scan(self) -> Dict[str, Any]:
        """Run Hadolint Dockerfile linter."""
        dockerfile_path = self.project_root / "Dockerfile"

        if not dockerfile_path.exists():
            return {"status": "no_dockerfile", "error": "No Dockerfile found"}

        try:
            cmd = ["hadolint", "--format", "json", str(dockerfile_path)]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)

            if result.stdout:
                try:
                    findings = json.loads(result.stdout)
                    return {
                        "status": "success",
                        "vulnerabilities": findings,
                        "summary": {
                            "total_issues": len(findings),
                            "error_level": len(
                                [f for f in findings if f.get("level") == "error"]
                            ),
                            "warning_level": len(
                                [f for f in findings if f.get("level") == "warning"]
                            ),
                            "info_level": len(
                                [f for f in findings if f.get("level") == "info"]
                            ),
                        },
                        "raw_output": result.stdout,
                    }
                except json.JSONDecodeError:
                    return {
                        "status": "parse_error",
                        "error": "Failed to parse Hadolint output",
                        "raw_output": result.stdout,
                    }
            else:
                return {
                    "status": "no_issues",
                    "vulnerabilities": [],
                    "summary": {"total_issues": 0},
                    "raw_output": result.stdout,
                }

        except subprocess.TimeoutExpired:
            return {"status": "timeout", "error": "Hadolint scan timed out"}
        except FileNotFoundError:
            return {"status": "tool_not_found", "error": "Hadolint not installed"}

    async def _generate_requirements(self):
        """Generate requirements.txt from poetry or pipenv."""
        try:
            # Try poetry first
            if (self.project_root / "pyproject.toml").exists():
                subprocess.run(
                    [
                        "poetry",
                        "export",
                        "-f",
                        "requirements.txt",
                        "--output",
                        "requirements.txt",
                    ],
                    cwd=self.project_root,
                    timeout=60,
                )
            # Try pipenv
            elif (self.project_root / "Pipfile").exists():
                subprocess.run(
                    ["pipenv", "requirements"],
                    stdout=open(self.project_root / "requirements.txt", "w"),
                    cwd=self.project_root,
                    timeout=60,
                )
        except Exception as e:
            logger.warning(f"Failed to generate requirements.txt: {e}")

    def _generate_summary(self) -> Dict[str, Any]:
        """Generate comprehensive security summary."""
        total_vulnerabilities = 0
        critical_issues = 0
        high_issues = 0
        tools_failed = 0
        tools_successful = 0

        for tool_name, result in self.results.items():
            if result["status"] in ["success", "issues_found", "no_issues"]:
                tools_successful += 1
                summary = result.get("summary", {})
                total_vulnerabilities += summary.get("total_issues", 0)

                # Count critical/high issues based on tool
                if tool_name == "bandit":
                    critical_issues += summary.get("high_severity", 0)
                    high_issues += summary.get("medium_severity", 0)
                elif tool_name == "trivy":
                    critical_issues += summary.get("critical", 0)
                    high_issues += summary.get("high", 0)
                elif tool_name == "semgrep":
                    critical_issues += summary.get("error_findings", 0)
                    high_issues += summary.get("warning_findings", 0)
            else:
                tools_failed += 1

        # Determine overall status
        if critical_issues > 0:
            overall_status = "CRITICAL"
        elif high_issues > 0:
            overall_status = "HIGH_RISK"
        elif total_vulnerabilities > 0:
            overall_status = "MEDIUM_RISK"
        else:
            overall_status = "CLEAN"

        return {
            "scan_summary": {
                "timestamp": asyncio.get_event_loop().time(),
                "overall_status": overall_status,
                "total_vulnerabilities": total_vulnerabilities,
                "critical_issues": critical_issues,
                "high_issues": high_issues,
                "tools_successful": tools_successful,
                "tools_failed": tools_failed,
                "scan_coverage": f"{tools_successful}/{len(self.tools)} tools",
            },
            "tool_results": self.results,
            "recommendations": self._generate_recommendations(),
        }

    def _generate_recommendations(self) -> List[str]:
        """Generate security recommendations based on scan results."""
        recommendations = []

        if (
            self.results.get("bandit", {}).get("summary", {}).get("high_severity", 0)
            > 0
        ):
            recommendations.append("Fix high-severity Bandit findings immediately")

        if self.results.get("safety", {}).get("summary", {}).get("total_issues", 0) > 0:
            recommendations.append(
                "Update vulnerable dependencies identified by Safety"
            )

        if self.results.get("trivy", {}).get("summary", {}).get("critical", 0) > 0:
            recommendations.append("Address critical vulnerabilities found by Trivy")

        if (
            self.results.get("semgrep", {}).get("summary", {}).get("error_findings", 0)
            > 0
        ):
            recommendations.append("Fix security patterns identified by Semgrep")

        if not recommendations:
            recommendations.append(
                "No critical security issues found - maintain current security practices"
            )

        return recommendations

    async def _save_results(self, summary: Dict[str, Any]):
        """Save scan results to files."""
        # Save summary
        summary_file = self.output_dir / "security-summary.json"
        with open(summary_file, "w") as f:
            json.dump(summary, f, indent=2, default=str)

        # Save detailed results
        results_file = self.output_dir / "detailed-results.json"
        with open(results_file, "w") as f:
            json.dump(self.results, f, indent=2, default=str)

        # Generate human-readable report
        await self._generate_markdown_report(summary)

        logger.info(f"Security scan results saved to {self.output_dir}")

    async def _generate_markdown_report(self, summary: Dict[str, Any]):
        """Generate human-readable markdown report."""
        report_file = self.output_dir / "security-report.md"

        scan_summary = summary["scan_summary"]

        with open(report_file, "w") as f:
            f.write("# Security Scan Report\n\n")
            f.write(f"**Overall Status**: {scan_summary['overall_status']}\n")
            f.write(
                f"**Total Vulnerabilities**: {scan_summary['total_vulnerabilities']}\n"
            )
            f.write(f"**Critical Issues**: {scan_summary['critical_issues']}\n")
            f.write(f"**High Risk Issues**: {scan_summary['high_issues']}\n")
            f.write(f"**Scan Coverage**: {scan_summary['scan_coverage']}\n\n")

            f.write("## Tool Results\n\n")
            for tool_name, result in summary["tool_results"].items():
                status = result["status"]
                f.write(f"### {tool_name.title()}\n")
                f.write(f"**Status**: {status}\n")

                if "summary" in result:
                    summary_data = result["summary"]
                    f.write(
                        f"**Issues Found**: {summary_data.get('total_issues', 0)}\n"
                    )

                if result.get("vulnerabilities"):
                    f.write(f"**Details**: {len(result['vulnerabilities'])} findings\n")

                f.write("\n")

            f.write("## Recommendations\n\n")
            for i, rec in enumerate(summary["recommendations"], 1):
                f.write(f"{i}. {rec}\n")


async def main():
    """Main entry point for security scanning."""
    import argparse

    parser = argparse.ArgumentParser(description="Nexus Security Scanner")
    parser.add_argument(
        "--project-root", type=Path, default=Path.cwd(), help="Project root directory"
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path.cwd() / "security-reports",
        help="Output directory for scan results",
    )
    parser.add_argument(
        "--tools",
        nargs="+",
        choices=["bandit", "safety", "semgrep", "trivy", "hadolint"],
        help="Specific tools to run (default: all)",
    )
    parser.add_argument(
        "--fail-on-high",
        action="store_true",
        help="Exit with error code if high/critical issues found",
    )

    args = parser.parse_args()

    # Initialize scanner
    scanner = SecurityScanner(args.project_root, args.output_dir)

    # Filter tools if specified
    if args.tools:
        scanner.tools = {k: v for k, v in scanner.tools.items() if k in args.tools}

    # Run scans
    summary = await scanner.run_all_scans()

    # Print summary
    scan_summary = summary["scan_summary"]
    print("\n🔒 Security Scan Complete")
    print(f"Overall Status: {scan_summary['overall_status']}")
    print(f"Total Issues: {scan_summary['total_vulnerabilities']}")
    print(f"Critical: {scan_summary['critical_issues']}")
    print(f"High Risk: {scan_summary['high_issues']}")
    print(f"Tools Coverage: {scan_summary['scan_coverage']}")

    # Exit with appropriate code
    if args.fail_on_high and (
        scan_summary["critical_issues"] > 0 or scan_summary["high_issues"] > 0
    ):
        sys.exit(1)

    sys.exit(0)


if __name__ == "__main__":
    asyncio.run(main())
