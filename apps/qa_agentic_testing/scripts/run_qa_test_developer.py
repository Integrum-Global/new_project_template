#!/usr/bin/env python3
"""
QA Agentic Testing - Developer Configuration Script
Comprehensive control over all testing parameters for developers who want fine-grained control.
"""

import asyncio
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

# ============================================================================
# DEVELOPER CONFIGURATION - FULL CONTROL
# ============================================================================

# ===== TARGET APPLICATION =====
TARGET_APP_PATH = (
    "../../../apps/user_management"  # Path to app to test (relative or absolute)
)
TEST_NAME = "User Management QA Report - Developer Mode"  # Name for this test run

# ===== PERSONA CONFIGURATION =====
MAX_PERSONAS = None  # None = use all, int = limit number of personas
CUSTOM_PERSONAS = None  # None = auto-generate, or list of custom persona dicts
PERSONA_FILTERS = {
    "include_roles": [],  # Only include personas with these roles (empty = all)
    "exclude_roles": [],  # Exclude personas with these roles
    "min_permissions": 0,  # Minimum permission count for persona
    "max_permissions": 999,  # Maximum permission count for persona
}

# ===== SCENARIO CONFIGURATION =====
SCENARIO_TYPES = [
    "functional",
    "security",
    "performance",
    "usability",
]  # Types to generate
# Available: functional, security, performance, usability, integration, accessibility, regression

SCENARIO_FILTERS = {
    "max_scenarios": None,  # None = no limit, int = maximum scenarios to run
    "priority_filter": [],  # Only run scenarios with these priorities: high, medium, low
    "interface_filter": [],  # Only test these interfaces: cli, api, web, mobile
    "include_patterns": [],  # Only scenarios matching these name patterns (regex)
    "exclude_patterns": [],  # Exclude scenarios matching these patterns (regex)
}

# ===== EXECUTION CONFIGURATION =====
EXECUTION_CONFIG = {
    "max_concurrent_tests": 5,  # Parallel test execution (1-20 recommended)
    "timeout_per_test": 60,  # Seconds before individual test times out
    "total_timeout": 600,  # Seconds before entire test run times out
    "retry_failed_tests": False,  # Whether to retry failed tests once
    "fail_fast": False,  # Stop on first failure
    "dry_run": False,  # Generate tests but don't execute them
}

# ===== OUTPUT CONFIGURATION =====
OUTPUT_CONFIG = {
    "custom_output_dir": None,  # None = use target app's qa_results, or custom Path
    "generate_html": True,  # Generate HTML report
    "generate_json": True,  # Generate JSON report
    "generate_csv": False,  # Generate CSV summary (basic)
    "include_debug_logs": False,  # Include detailed debug information
    "compress_results": False,  # Compress large JSON files
    "save_screenshots": False,  # Save screenshots (if applicable)
    "custom_filename": None,  # None = auto-generate, or custom filename prefix
}

# ===== DISCOVERY CONFIGURATION =====
DISCOVERY_CONFIG = {
    "deep_scan": True,  # Perform deep analysis of codebase
    "scan_test_files": True,  # Include test files in analysis
    "scan_config_files": True,  # Include config files in analysis
    "detect_frameworks": True,  # Auto-detect frameworks used
    "analyze_dependencies": True,  # Analyze package dependencies
    "security_scan": True,  # Look for security patterns
    "performance_hints": True,  # Look for performance bottlenecks
    "ignore_patterns": [  # Patterns to ignore during discovery
        "*.pyc",
        "__pycache__",
        ".git",
        "node_modules",
        ".env",
    ],
}

# ===== AI/LLM CONFIGURATION =====
AI_CONFIG = {
    "use_advanced_ai": True,  # Use advanced AI analysis (slower but better)
    "confidence_threshold": 70,  # Minimum confidence for test results (0-100)
    "enable_mcp": True,  # Enable MCP agent analysis
    "ai_creativity": "balanced",  # conservative, balanced, creative
    "language_complexity": "standard",  # simple, standard, advanced
    "explanation_detail": "normal",  # minimal, normal, verbose
}

# ===== AGENT MODEL CONFIGURATION =====
# Configure different LLM models for different agent types
AGENT_MODEL_CONFIG = {
    "preset": "balanced",  # development, balanced, enterprise
    # Custom model assignments per agent type
    "custom_models": {
        "basic_llm": {
            "provider": "ollama",  # ollama, openai, anthropic
            "model": "llama3.2:latest",  # Model identifier
            "temperature": 0.1,  # Creativity level (0.0-1.0)
            "max_tokens": 2000,  # Response length
            "timeout_seconds": 20,  # Request timeout
        },
        "iterative_agent": {
            "provider": "ollama",
            "model": "llama3.1:8b",
            "temperature": 0.2,
            "max_tokens": 3000,
            "timeout_seconds": 45,
        },
        "a2a_agent": {
            "provider": "ollama",
            "model": "llama3.2:latest",
            "temperature": 0.1,
            "max_tokens": 4000,
            "timeout_seconds": 30,
        },
        "self_organizing": {
            "provider": "ollama",
            "model": "codellama:13b",
            "temperature": 0.3,
            "max_tokens": 4000,
            "timeout_seconds": 60,
        },
        "mcp_agent": {
            "provider": "ollama",
            "model": "llama3.1:8b",
            "temperature": 0.1,
            "max_tokens": 3000,
            "timeout_seconds": 25,
        },
        "orchestration_manager": {
            "provider": "ollama",
            "model": "llama3.2:latest",
            "temperature": 0.2,
            "max_tokens": 4000,
            "timeout_seconds": 35,
        },
    },
    # Agent specializations (which agents focus on which analysis types)
    "agent_specializations": {
        "security_analysis": ["iterative_agent", "a2a_agent"],
        "performance_analysis": ["self_organizing", "mcp_agent"],
        "functional_analysis": ["basic_llm", "iterative_agent"],
        "consensus_analysis": ["a2a_agent", "orchestration_manager"],
    },
    # Agent team configurations
    "team_configurations": {
        "enable_agent_pools": True,  # Use AgentPoolManagerNode for team formation
        "enable_a2a_communication": True,  # Enable Agent-to-Agent communication
        "enable_iterative_analysis": True,  # Use IterativeLLMAgentNode for deep analysis
        "max_team_size": 3,  # Maximum agents per team
        "collaboration_mode": "consensus",  # independent, collaborative, consensus
        "consensus_threshold": 0.8,  # Agreement threshold for consensus
    },
}

# ===== PERFORMANCE TESTING =====
PERFORMANCE_CONFIG = {
    "enable_benchmarks": True,  # Run performance benchmarks
    "load_test_scenarios": False,  # Include load testing
    "memory_profiling": False,  # Profile memory usage
    "response_time_targets": {  # Expected response times (ms)
        "api_endpoints": 200,
        "cli_commands": 1000,
        "web_pages": 2000,
    },
    "throughput_targets": {  # Expected throughput (ops/sec)
        "api_calls": 100,
        "cli_operations": 10,
    },
}

# ===== SECURITY TESTING =====
SECURITY_CONFIG = {
    "enable_security_tests": True,  # Run security-focused tests
    "check_authentication": True,  # Test auth mechanisms
    "check_authorization": True,  # Test permission systems
    "check_input_validation": True,  # Test input sanitization
    "check_session_management": True,  # Test session handling
    "vulnerability_scan": False,  # Deep vulnerability scanning (slow)
    "compliance_checks": [],  # Compliance standards to check: GDPR, HIPAA, SOX
}

# ===== REPORTING CONFIGURATION =====
REPORTING_CONFIG = {
    "include_executive_summary": True,  # High-level summary for managers
    "include_technical_details": True,  # Detailed technical information
    "include_recommendations": True,  # AI-generated recommendations
    "include_code_samples": False,  # Include relevant code snippets
    "include_performance_graphs": True,  # Generate performance charts
    "include_security_analysis": True,  # Detailed security findings
    "risk_assessment": True,  # Generate risk assessment
    "compliance_report": False,  # Generate compliance report
    "custom_branding": {  # Custom branding for reports
        "company_name": None,
        "logo_path": None,
        "color_scheme": "default",  # default, blue, green, corporate
    },
}

# ===== INTEGRATION CONFIGURATION =====
INTEGRATION_CONFIG = {
    "webhook_url": None,  # POST results to webhook
    "slack_webhook": None,  # Send summary to Slack
    "email_recipients": [],  # Email results to these addresses
    "jira_integration": False,  # Create JIRA tickets for failures
    "github_integration": False,  # Create GitHub issues for failures
    "ci_cd_integration": True,  # Output CI/CD friendly format
    "metrics_endpoint": None,  # Send metrics to monitoring system
}

# ===== DEVELOPMENT FEATURES =====
DEV_CONFIG = {
    "verbose_output": True,  # Show detailed progress
    "debug_mode": False,  # Enable debug logging
    "save_intermediate_results": False,  # Save results after each phase
    "profile_execution": False,  # Profile test execution performance
    "cache_discovery": False,  # Cache discovery results
    "experimental_features": False,  # Enable experimental features
    "developer_notes": True,  # Include developer-oriented insights
}

# ============================================================================
# IMPLEMENTATION - DEVELOPER-GRADE TESTING ENGINE
# ============================================================================

sys.path.insert(0, str(Path(__file__).parent))

# Configure logging based on dev settings
import logging

if not DEV_CONFIG["verbose_output"]:
    logging.getLogger("qa_agentic_testing.core.agent_coordinator").setLevel(
        logging.CRITICAL
    )
if DEV_CONFIG["debug_mode"]:
    logging.basicConfig(level=logging.DEBUG)

from qa_agentic_testing.core.agent_coordinator import (
    AgentConfig,
    AgentType,
    AnalysisType,
)
from qa_agentic_testing.core.scenario_generator import ScenarioType
from qa_agentic_testing.core.test_executor import AutonomousQATester


def log(msg: str, level: str = "INFO"):
    """Enhanced logging with levels."""
    if level == "DEBUG" and not DEV_CONFIG["debug_mode"]:
        return
    if not DEV_CONFIG["verbose_output"] and level == "DEBUG":
        return

    timestamp = datetime.now().strftime("%H:%M:%S")
    prefix = {
        "INFO": "ℹ️ ",
        "SUCCESS": "✅",
        "WARNING": "⚠️ ",
        "ERROR": "❌",
        "DEBUG": "🔍",
        "CONFIG": "⚙️ ",
    }.get(level, "")
    print(f"[{timestamp}] {prefix} {msg}")


def validate_config():
    """Validate developer configuration."""
    errors = []
    warnings = []

    # Validate paths
    app_path = (
        Path(TARGET_APP_PATH)
        if not Path(TARGET_APP_PATH).is_absolute()
        else Path(TARGET_APP_PATH)
    )
    if not app_path.exists():
        errors.append(f"Target app not found: {app_path}")

    # Validate numeric ranges
    if EXECUTION_CONFIG["max_concurrent_tests"] not in range(1, 21):
        warnings.append("max_concurrent_tests should be 1-20 for optimal performance")

    if AI_CONFIG["confidence_threshold"] not in range(0, 101):
        errors.append("confidence_threshold must be 0-100")

    # Validate scenario types
    valid_types = [
        "functional",
        "security",
        "performance",
        "usability",
        "integration",
        "accessibility",
        "regression",
    ]
    invalid_types = [t for t in SCENARIO_TYPES if t not in valid_types]
    if invalid_types:
        errors.append(f"Invalid scenario types: {invalid_types}")

    return errors, warnings


def _configure_agent_models(agent_coordinator, model_config: Dict[str, Any]):
    """Configure agent coordinator with custom model settings."""

    try:
        # Get preset configuration
        preset = model_config.get("preset", "balanced")
        custom_models = model_config.get("custom_models", {})
        team_config = model_config.get("team_configurations", {})

        log(f"Applying agent model preset: {preset}", "CONFIG")

        # Configure individual agents with custom models
        for agent_name, model_settings in custom_models.items():
            try:
                # Map agent name to AgentType enum
                agent_type_mapping = {
                    "basic_llm": AgentType.BASIC_LLM,
                    "iterative_agent": AgentType.ITERATIVE_AGENT,
                    "a2a_agent": AgentType.A2A_AGENT,
                    "self_organizing": AgentType.SELF_ORGANIZING,
                    "mcp_agent": AgentType.MCP_AGENT,
                    "orchestration_manager": AgentType.ORCHESTRATION_MANAGER,
                }

                agent_type = agent_type_mapping.get(agent_name)
                if not agent_type:
                    continue

                # Create agent configuration
                agent_config = AgentConfig(
                    agent_type=agent_type,
                    provider=model_settings.get("provider", "ollama"),
                    model=model_settings.get("model", "llama3.2:latest"),
                    temperature=model_settings.get("temperature", 0.1),
                    max_tokens=model_settings.get("max_tokens", 2000),
                    timeout_seconds=model_settings.get("timeout_seconds", 30),
                    enabled=True,
                    collaboration_mode=team_config.get(
                        "collaboration_mode", "independent"
                    ),
                )

                # Add to agent coordinator
                agent_coordinator.add_agent(f"dev_{agent_name}", agent_config)

                log(
                    f"  • {agent_name}: {model_settings['provider']}:{model_settings['model']}",
                    "CONFIG",
                )

            except Exception as e:
                log(f"Failed to configure {agent_name}: {e}", "WARNING")

        # Configure team settings
        if team_config.get("enable_agent_pools"):
            log("  • Agent pools enabled for team formation", "CONFIG")

        if team_config.get("enable_a2a_communication"):
            log("  • Agent-to-Agent communication enabled", "CONFIG")

        if team_config.get("enable_iterative_analysis"):
            log("  • Iterative LLM analysis enabled", "CONFIG")

        log("Agent model configuration complete", "SUCCESS")

    except Exception as e:
        log(f"Agent model configuration failed: {e}", "ERROR")


async def run_developer_test():
    """Run comprehensive developer-configured QA testing."""

    # Header
    log("🚀 QA AGENTIC TESTING - DEVELOPER MODE", "INFO")
    log(f"Test Name: {TEST_NAME}", "CONFIG")
    log(f"Target: {TARGET_APP_PATH}", "CONFIG")

    # Validate configuration
    log("Validating configuration...", "INFO")
    errors, warnings = validate_config()

    if errors:
        for error in errors:
            log(error, "ERROR")
        return 1

    for warning in warnings:
        log(warning, "WARNING")

    # Setup paths
    if Path(TARGET_APP_PATH).is_absolute():
        app_path = Path(TARGET_APP_PATH)
    else:
        app_path = Path(__file__).parent / TARGET_APP_PATH

    # Determine output directory
    if OUTPUT_CONFIG["custom_output_dir"]:
        output_dir = Path(OUTPUT_CONFIG["custom_output_dir"])
    else:
        output_dir = app_path / "qa_results"

    output_dir.mkdir(parents=True, exist_ok=True)

    log(f"Output directory: {output_dir}", "CONFIG")

    try:
        # Initialize tester with custom config
        log("Initializing QA Tester with developer configuration...", "INFO")
        tester = AutonomousQATester(app_path=app_path, output_dir=output_dir)

        # Configure tester based on dev settings
        if hasattr(tester, "config"):
            # Merge discovery config with existing config
            tester.config["discovery"].update(
                {
                    "analyze_code": DISCOVERY_CONFIG["deep_scan"],
                    "analyze_docs": DISCOVERY_CONFIG["scan_config_files"],
                    "analyze_tests": DISCOVERY_CONFIG["scan_test_files"],
                    "extract_permissions": DISCOVERY_CONFIG["security_scan"],
                    "detect_interfaces": True,
                }
            )

            # Add custom config sections
            tester.config.update(
                {
                    "ai": AI_CONFIG,
                    "agent_models": AGENT_MODEL_CONFIG,
                    "performance": PERFORMANCE_CONFIG,
                    "security": SECURITY_CONFIG,
                }
            )

        # Configure agent coordinator with custom models
        if hasattr(tester, "agent_coordinator"):
            log("Configuring advanced agent systems with custom models...", "CONFIG")
            _configure_agent_models(tester.agent_coordinator, AGENT_MODEL_CONFIG)

        # Phase 1: Discovery
        log("=" * 60, "INFO")
        log("PHASE 1: APPLICATION DISCOVERY", "INFO")
        log("=" * 60, "INFO")

        log("Analyzing application structure...", "INFO")
        discovery = await tester.discover_app(app_path)

        log(
            f"Discovered {len(discovery.get('permissions', []))} permissions", "SUCCESS"
        )
        log(f"Discovered {len(discovery.get('interfaces', []))} interfaces", "SUCCESS")
        log(f"Discovered {len(discovery.get('operations', []))} operations", "SUCCESS")

        if DEV_CONFIG["verbose_output"]:
            log(f"Interfaces: {discovery.get('interfaces', [])}", "DEBUG")
            log(f"Sample permissions: {discovery.get('permissions', [])[:3]}", "DEBUG")

        # Phase 2: Persona Generation
        log("\n" + "=" * 60, "INFO")
        log("PHASE 2: PERSONA GENERATION", "INFO")
        log("=" * 60, "INFO")

        if CUSTOM_PERSONAS:
            log("Using custom personas", "CONFIG")
            personas = CUSTOM_PERSONAS
        else:
            log("Auto-generating personas...", "INFO")
            personas = tester.generate_personas()

        # Apply persona filters
        if PERSONA_FILTERS["include_roles"]:
            personas = [
                p for p in personas if p.role in PERSONA_FILTERS["include_roles"]
            ]
            log(
                f"Filtered to include only roles: {PERSONA_FILTERS['include_roles']}",
                "CONFIG",
            )

        if PERSONA_FILTERS["exclude_roles"]:
            personas = [
                p for p in personas if p.role not in PERSONA_FILTERS["exclude_roles"]
            ]
            log(
                f"Filtered to exclude roles: {PERSONA_FILTERS['exclude_roles']}",
                "CONFIG",
            )

        # Apply persona limit
        if MAX_PERSONAS and len(personas) > MAX_PERSONAS:
            personas = personas[:MAX_PERSONAS]
            log(f"Limited to {MAX_PERSONAS} personas", "CONFIG")

        log(f"Using {len(personas)} personas:", "SUCCESS")
        for i, p in enumerate(personas, 1):
            log(f"  {i}. {p.name} ({p.role})", "INFO")

        # Phase 3: Scenario Generation
        log("\n" + "=" * 60, "INFO")
        log("PHASE 3: SCENARIO GENERATION", "INFO")
        log("=" * 60, "INFO")

        # Convert scenario types to enums
        scenario_types = []
        type_mapping = {
            "functional": ScenarioType.FUNCTIONAL,
            "security": ScenarioType.SECURITY,
            "performance": ScenarioType.PERFORMANCE,
            "usability": ScenarioType.USABILITY,
            "integration": ScenarioType.INTEGRATION,
            "accessibility": ScenarioType.ACCESSIBILITY,
            "regression": ScenarioType.REGRESSION,
        }
        for t in SCENARIO_TYPES:
            if t in type_mapping:
                scenario_types.append(type_mapping[t])

        log(f"Generating scenarios for types: {SCENARIO_TYPES}", "CONFIG")
        scenarios = tester.generate_scenarios(
            personas=personas, scenario_types=scenario_types
        )

        # Apply scenario filters
        if (
            SCENARIO_FILTERS["max_scenarios"]
            and len(scenarios) > SCENARIO_FILTERS["max_scenarios"]
        ):
            scenarios = scenarios[: SCENARIO_FILTERS["max_scenarios"]]
            log(f"Limited to {SCENARIO_FILTERS['max_scenarios']} scenarios", "CONFIG")

        log(f"Generated {len(scenarios)} scenarios:", "SUCCESS")

        # Count by type
        type_counts = {}
        for scenario in scenarios:
            t = scenario.scenario_type.value
            type_counts[t] = type_counts.get(t, 0) + 1

        for t, count in type_counts.items():
            log(f"  {t}: {count} scenarios", "INFO")

        # Phase 4: Test Execution
        log("\n" + "=" * 60, "INFO")
        log("PHASE 4: TEST EXECUTION", "INFO")
        log("=" * 60, "INFO")

        if EXECUTION_CONFIG["dry_run"]:
            log("DRY RUN MODE - Skipping actual test execution", "WARNING")
            log(
                f"Would execute {len(scenarios)} scenarios with {len(personas)} personas",
                "INFO",
            )
        else:
            log(
                f"Executing {len(scenarios)} tests with {EXECUTION_CONFIG['max_concurrent_tests']} concurrent workers...",
                "INFO",
            )

            start_time = datetime.now()

            try:
                summary = await asyncio.wait_for(
                    tester.execute_tests(
                        scenarios,
                        max_concurrent=EXECUTION_CONFIG["max_concurrent_tests"],
                    ),
                    timeout=EXECUTION_CONFIG["total_timeout"],
                )

                execution_time = (datetime.now() - start_time).total_seconds()

                log(f"Execution completed in {execution_time:.1f} seconds", "SUCCESS")
                log(f"Total Tests: {summary.total_tests}", "INFO")
                log(f"Passed: {summary.passed_tests}", "SUCCESS")
                log(
                    f"Failed: {summary.failed_tests}",
                    "ERROR" if summary.failed_tests > 0 else "INFO",
                )
                log(
                    f"Success Rate: {summary.success_rate:.1f}%",
                    "SUCCESS" if summary.success_rate >= 80 else "WARNING",
                )

                if summary.success_rate < AI_CONFIG["confidence_threshold"]:
                    log(
                        f"Success rate below confidence threshold ({AI_CONFIG['confidence_threshold']}%)",
                        "WARNING",
                    )

            except asyncio.TimeoutError:
                log(
                    f"Test execution timed out after {EXECUTION_CONFIG['total_timeout']} seconds",
                    "ERROR",
                )
                return 1

        # Phase 5: Report Generation
        log("\n" + "=" * 60, "INFO")
        log("PHASE 5: REPORT GENERATION", "INFO")
        log("=" * 60, "INFO")

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename_prefix = OUTPUT_CONFIG["custom_filename"] or f"qa_test_dev_{timestamp}"

        generated_files = []

        # Generate JSON report
        if OUTPUT_CONFIG["generate_json"]:
            json_path = output_dir / f"{filename_prefix}.json"
            await tester.generate_report(output_file=json_path, format="json")
            generated_files.append(json_path)
            log(f"JSON report: {json_path.name}", "SUCCESS")

        # Generate HTML report
        if OUTPUT_CONFIG["generate_html"]:
            html_path = output_dir / f"{filename_prefix}.html"
            try:
                await tester.generate_report(output_file=html_path, format="html")
                generated_files.append(html_path)
                log(f"HTML report: {html_path.name}", "SUCCESS")
                log(f"View in browser: file://{html_path.absolute()}", "INFO")
            except Exception as e:
                log(f"HTML generation failed: {e}", "ERROR")

        # Generate CSV summary if requested
        if OUTPUT_CONFIG["generate_csv"]:
            csv_path = output_dir / f"{filename_prefix}_summary.csv"
            # Simple CSV generation
            try:
                import csv

                with open(csv_path, "w", newline="") as f:
                    writer = csv.writer(f)
                    writer.writerow(
                        ["Test ID", "Persona", "Status", "Duration", "Confidence"]
                    )
                    for result in tester.test_results:
                        writer.writerow(
                            [
                                result.test_id,
                                result.persona_key,
                                result.status.value,
                                f"{result.duration_seconds:.2f}s",
                                f"{result.confidence_score:.1f}%",
                            ]
                        )
                generated_files.append(csv_path)
                log(f"CSV summary: {csv_path.name}", "SUCCESS")
            except Exception as e:
                log(f"CSV generation failed: {e}", "WARNING")

        # Final Summary
        log("\n" + "=" * 60, "INFO")
        log("✅ DEVELOPER QA TESTING COMPLETE", "SUCCESS")
        log("=" * 60, "INFO")

        log(f"Test Name: {TEST_NAME}", "INFO")
        log(f"Application: {app_path.name}", "INFO")
        if not EXECUTION_CONFIG["dry_run"]:
            log(f"Success Rate: {summary.success_rate:.1f}%", "INFO")
            log(f"Execution Time: {execution_time:.1f} seconds", "INFO")

        log(f"\n📁 Results saved to: {output_dir}", "INFO")
        log("📄 Generated files:", "INFO")
        for file_path in generated_files:
            size = file_path.stat().st_size
            log(f"  • {file_path.name} ({size:,} bytes)", "INFO")

        # Advanced agent system insights
        if DEV_CONFIG["developer_notes"]:
            log("\n🤖 Advanced Agent System Analysis:", "INFO")

            # Show which agents were used
            available_agents = (
                tester.agent_coordinator.get_available_agents()
                if hasattr(tester, "agent_coordinator")
                else []
            )
            if available_agents:
                log(f"  • Active agents: {', '.join(available_agents)}", "DEBUG")

                # Show agent specializations
                try:
                    security_agents = (
                        tester.agent_coordinator.get_specialized_agents(
                            AnalysisType.SECURITY
                        )
                        if hasattr(tester.agent_coordinator, "get_specialized_agents")
                        else []
                    )
                    if security_agents:
                        log(
                            f"  • Security specialists: {', '.join(security_agents)}",
                            "DEBUG",
                        )

                    performance_agents = (
                        tester.agent_coordinator.get_specialized_agents(
                            AnalysisType.PERFORMANCE
                        )
                        if hasattr(tester.agent_coordinator, "get_specialized_agents")
                        else []
                    )
                    if performance_agents:
                        log(
                            f"  • Performance specialists: {', '.join(performance_agents)}",
                            "DEBUG",
                        )
                except:
                    pass

            # Show framework usage
            log("\n🏗️ Framework Usage Analysis:", "INFO")
            log("  • IterativeLLMAgent: Used for deep analysis iterations", "DEBUG")
            log("  • AgentPoolManagerNode: Team formation and coordination", "DEBUG")
            log("  • A2AAgentNode: Agent-to-agent collaboration", "DEBUG")
            log("  • SelfOrganizingAgentNode: Dynamic capability matching", "DEBUG")

            log("\n🔧 Developer Metrics:", "INFO")
            log(
                f"  • Scenarios per persona: {len(scenarios) / len(personas):.1f}",
                "DEBUG",
            )
            log(
                f"  • Test density: {len(scenarios) / len(discovery.get('operations', [1])):.1f} scenarios/operation",
                "DEBUG",
            )
            log(
                f"  • Coverage efficiency: {(summary.success_rate / 100) * len(scenarios):.1f} effective tests",
                "DEBUG",
            )

        return 0

    except Exception as e:
        log(f"Error: {e}", "ERROR")
        if DEV_CONFIG["debug_mode"]:
            import traceback

            traceback.print_exc()
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(run_developer_test())
    sys.exit(exit_code)
