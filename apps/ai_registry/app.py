"""
AI Registry App - Pure Kailash SDK Implementation

A comprehensive AI use case registry with RAG capabilities, built entirely using
Kailash SDK components and patterns for optimal portability and integration.
"""

import logging
from pathlib import Path
from typing import Any, Dict, Optional

from kailash.middleware.mcp import MiddlewareMCPServer as MCPServer
from kailash.runtime import LocalRuntime

from .modules.analysis import AnalysisModule
from .modules.rag import RAGModule
from .modules.registry import RegistryModule
from .modules.search import SearchModule
from .workflows import AnalysisWorkflows, RAGWorkflows, SearchWorkflows

logger = logging.getLogger(__name__)


class AIRegistryApp:
    """
    Pure Kailash SDK application for AI Registry with RAG capabilities.

    Features:
    - Enhanced MCP Server with caching, metrics, and formatting
    - RAG processing for PDF documents and knowledge extraction
    - Semantic search and similarity matching
    - Cross-domain analysis and trend insights
    - Modular architecture for easy extension and maintenance
    """

    def __init__(
        self,
        config_file: Optional[str] = None,
        config_override: Optional[Dict[str, Any]] = None,
    ):
        """
        Initialize the AI Registry application.

        Args:
            config_file: Path to YAML configuration file
            config_override: Optional configuration overrides
        """
        # Set default config file if not provided
        if not config_file:
            config_file = Path(__file__).parent / "data" / "app_config.yaml"

        # Initialize Enhanced MCP Server with all production features
        self.server = MCPServer(
            name="ai-registry",
            config_file=config_file if Path(config_file).exists() else None,
            config_override=config_override,
            enable_cache=True,
            cache_ttl=300,  # 5 minute default
            enable_metrics=True,
            enable_formatting=True,
        )

        # Initialize runtime for workflow execution
        self.runtime = LocalRuntime()

        # Initialize business logic modules
        self._initialize_modules()

        # Initialize workflows
        self._initialize_workflows()

        # Setup MCP server components
        self._setup_mcp_components()

        logger.info("AI Registry App initialized successfully")

    def _initialize_modules(self):
        """Initialize business logic modules."""
        try:
            self.rag_module = RAGModule(self.server, self.runtime)
            self.search_module = SearchModule(self.server, self.runtime)
            self.analysis_module = AnalysisModule(self.server, self.runtime)
            self.registry_module = RegistryModule(self.server, self.runtime)

            logger.info("All modules initialized successfully")
        except Exception as e:
            logger.error(f"Module initialization failed: {str(e)}")
            raise

    def _initialize_workflows(self):
        """Initialize workflow orchestrators."""
        try:
            self.rag_workflows = RAGWorkflows(
                self.server, self.rag_module, self.runtime
            )
            self.search_workflows = SearchWorkflows(
                self.server, self.search_module, self.runtime
            )
            self.analysis_workflows = AnalysisWorkflows(
                self.server, self.analysis_module, self.runtime
            )

            logger.info("All workflows initialized successfully")
        except Exception as e:
            logger.error(f"Workflow initialization failed: {str(e)}")
            raise

    def _setup_mcp_components(self):
        """Setup MCP server tools and resources."""
        try:
            # Setup tools from workflows (they register themselves)
            self._setup_resources()

            logger.info("MCP components setup completed")
        except Exception as e:
            logger.error(f"MCP setup failed: {str(e)}")
            raise

    def _setup_resources(self):
        """Setup MCP resources for external access."""

        @self.server.resource("app://ai-registry/overview")
        def registry_overview() -> str:
            """Overview of the AI Registry application and capabilities."""
            stats = self.registry_module.get_statistics()
            return f"""# AI Registry Overview

**Total Use Cases**: {stats.get('total_use_cases', 0)}
**Domains**: {stats.get('unique_domains', 0)}
**AI Methods**: {stats.get('unique_ai_methods', 0)}
**RAG Enabled**: {stats.get('rag_enabled', False)}

## Capabilities
- Semantic search across AI use cases
- PDF document processing and knowledge extraction
- Cross-domain analysis and trend insights
- Real-time similarity matching
- Comprehensive use case discovery

## API Access
- Use MCP tools for programmatic access
- Query by domain, AI method, or free text
- Export results in multiple formats
"""

        @self.server.resource("app://ai-registry/status")
        def system_status() -> str:
            """Current system status and health metrics."""
            return self._format_system_status()

        @self.server.resource("app://ai-registry/config")
        def app_configuration() -> str:
            """Application configuration summary."""
            return self._format_app_config()

    def _format_system_status(self) -> str:
        """Format system status information."""
        try:
            # Get module status
            modules_status = {
                "rag": self.rag_module.get_status(),
                "search": self.search_module.get_status(),
                "analysis": self.analysis_module.get_status(),
                "registry": self.registry_module.get_status(),
            }

            # Check overall health
            all_healthy = all(
                status.get("healthy", False) for status in modules_status.values()
            )

            status_text = f"""# AI Registry System Status

**Overall Health**: {"✅ Healthy" if all_healthy else "⚠️ Issues Detected"}
**Cache**: {"✅ Enabled" if self.server.enable_cache else "❌ Disabled"}
**Metrics**: {"✅ Enabled" if self.server.enable_metrics else "❌ Disabled"}

## Module Status
"""

            for module_name, status in modules_status.items():
                health_icon = "✅" if status.get("healthy", False) else "❌"
                status_text += f"\n- **{module_name.upper()}**: {health_icon} {status.get('status', 'Unknown')}"

            return status_text

        except Exception as e:
            return f"❌ Status check failed: {str(e)}"

    def _format_app_config(self) -> str:
        """Format application configuration summary."""
        try:
            config_text = f"""# AI Registry Configuration

## Server Configuration
- **Name**: {self.server.name}
- **Cache TTL**: {self.server.cache_ttl}s
- **Features**: Cache: {self.server.enable_cache}, Metrics: {self.server.enable_metrics}

## Modules
- **RAG**: PDF processing, knowledge extraction
- **Search**: Semantic search, similarity matching
- **Analysis**: Trend analysis, cross-domain insights
- **Registry**: Core data management and indexing

## Data Sources
- Combined AI Registry JSON
- ISO/IEC TR 24030 PDFs (2021, 2024)
- Generated knowledge base (Markdown)
"""
            return config_text

        except Exception as e:
            return f"❌ Config formatting failed: {str(e)}"

    def run(self):
        """Start the AI Registry application."""
        try:
            logger.info("Starting AI Registry App...")

            # Verify all modules are ready
            self._verify_modules_ready()

            # Start the Enhanced MCP Server
            logger.info("AI Registry App is ready and running")
            self.server.run()

        except KeyboardInterrupt:
            logger.info("AI Registry App stopped by user")
        except Exception as e:
            logger.error(f"AI Registry App failed to start: {str(e)}")
            raise

    def _verify_modules_ready(self):
        """Verify all modules are ready for operation."""
        modules = [
            ("RAG", self.rag_module),
            ("Search", self.search_module),
            ("Analysis", self.analysis_module),
            ("Registry", self.registry_module),
        ]

        for name, module in modules:
            if not module.is_ready():
                raise RuntimeError(f"{name} module is not ready")
            logger.info(f"{name} module: ✅ Ready")

    def get_app_info(self) -> Dict[str, Any]:
        """Get comprehensive application information."""
        return {
            "name": "AI Registry",
            "version": "1.0.0",
            "server_name": self.server.name,
            "features": {
                "cache": self.server.enable_cache,
                "metrics": self.server.enable_metrics,
                "formatting": self.server.enable_formatting,
            },
            "modules": {
                "rag": self.rag_module.get_info(),
                "search": self.search_module.get_info(),
                "analysis": self.analysis_module.get_info(),
                "registry": self.registry_module.get_info(),
            },
            "workflows": {
                "rag": len(self.rag_workflows.get_available_workflows()),
                "search": len(self.search_workflows.get_available_workflows()),
                "analysis": len(self.analysis_workflows.get_available_workflows()),
            },
        }


# Factory function for different deployment modes
def create_app(
    mode: str = "production", config_override: Optional[Dict[str, Any]] = None
) -> AIRegistryApp:
    """
    Factory function to create AI Registry app with different configurations.

    Args:
        mode: Deployment mode ("development", "testing", "production")
        config_override: Additional configuration overrides

    Returns:
        Configured AIRegistryApp instance
    """
    base_config = config_override or {}

    if mode == "development":
        base_config.update(
            {
                "cache.enabled": False,
                "logging.level": "DEBUG",
                "rag.use_local_models": True,
            }
        )
    elif mode == "testing":
        base_config.update(
            {
                "cache.enabled": False,
                "metrics.enabled": False,
                "rag.mock_responses": True,
            }
        )
    elif mode == "production":
        base_config.update(
            {
                "cache.enabled": True,
                "metrics.enabled": True,
                "rag.use_local_models": False,
            }
        )

    return AIRegistryApp(config_override=base_config)


# Main entry point
def main():
    """Main entry point for the AI Registry application."""
    import argparse
    import sys

    parser = argparse.ArgumentParser(
        description="AI Registry App with RAG capabilities"
    )
    parser.add_argument(
        "--mode",
        choices=["development", "testing", "production"],
        default="production",
        help="Deployment mode",
    )
    parser.add_argument("--config", help="Path to configuration file")
    parser.add_argument("--debug", action="store_true", help="Enable debug logging")

    args = parser.parse_args()

    # Setup logging
    log_level = logging.DEBUG if args.debug else logging.INFO
    logging.basicConfig(
        level=log_level, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )

    try:
        # Create and run the app
        config_override = {}
        if args.debug:
            config_override["logging.level"] = "DEBUG"

        app = create_app(mode=args.mode, config_override=config_override)
        app.run()

    except Exception as e:
        logger.error(f"Application failed: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()
