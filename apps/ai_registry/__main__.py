"""
Entry point for running the AI Registry Enhanced MCP Server.

Usage:
    python -m apps.ai_registry [server-type]

Examples:
    # Run main AI Registry server (default)
    python -m apps.ai_registry

    # Run specific enterprise server
    python -m apps.ai_registry sharepoint
    python -m apps.ai_registry api-aggregator
    python -m apps.ai_registry iot-processor

    # Run with custom config
    python -m apps.ai_registry --config custom.yaml

    # Run in development mode with debug logging
    python -m apps.ai_registry --environment development --log-level DEBUG

    # Run with caching disabled (for testing)
    python -m apps.ai_registry --disable-cache
"""

import argparse
import logging
import os
import sys
from pathlib import Path

from .mcp_server import AIRegistryMCPServer
from .servers import APIAggregatorServer, IoTProcessorServer, SharePointConnectorServer


def main():
    """Main entry point for the AI Registry Enhanced MCP Server."""
    parser = argparse.ArgumentParser(
        description="AI Registry Enhanced MCP Server - Query and analyze 187 AI use cases",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Server Types:
  ai-registry        Main AI Registry server (default)
  sharepoint         SharePoint Connector server
  api-aggregator     API Aggregator server
  iot-processor      IoT Processor server

Environment Variables:
  REGISTRY_FILE      Path to AI registry JSON file
  LOG_LEVEL          Logging level (DEBUG, INFO, WARNING, ERROR)
  DEBUG              Enable debug mode (true/false)

Examples:
  %(prog)s                                    # Run main server
  %(prog)s sharepoint --config sharepoint.yaml # Run SharePoint server
  %(prog)s api-aggregator --disable-cache     # Run API aggregator without cache
  %(prog)s iot-processor --log-level DEBUG    # Run IoT processor with debug
        """,
    )

    # Add positional argument for server type
    parser.add_argument(
        "server",
        nargs="?",
        default="ai-registry",
        choices=["ai-registry", "sharepoint", "api-aggregator", "iot-processor"],
        help="Server type to run (default: ai-registry)",
    )

    # Configuration options
    parser.add_argument(
        "--config", help="Path to YAML configuration file (default: config.yaml)"
    )

    parser.add_argument(
        "--environment",
        choices=["development", "production", "testing"],
        help="Environment preset (overrides config settings)",
    )

    # Enhanced server options
    parser.add_argument(
        "--disable-cache",
        action="store_true",
        help="Disable caching (useful for development/testing)",
    )

    parser.add_argument(
        "--disable-metrics",
        action="store_true",
        help="Disable metrics collection",
    )

    parser.add_argument(
        "--disable-formatting",
        action="store_true",
        help="Disable response formatting",
    )

    # Registry options
    parser.add_argument(
        "--registry-file", help="Path to AI registry JSON file (overrides config)"
    )

    # Logging options
    parser.add_argument(
        "--log-level",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        help="Logging level (overrides config and environment)",
    )

    parser.add_argument(
        "--log-file",
        help="Log to file instead of stdout",
    )

    # Development options
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Enable debug mode (sets log level to DEBUG, enables stack traces)",
    )

    args = parser.parse_args()

    # Set up environment variables from args
    if args.debug:
        os.environ["DEBUG"] = "true"
        args.log_level = "DEBUG"

    if args.log_level:
        os.environ["LOG_LEVEL"] = args.log_level

    if args.log_file:
        os.environ["LOG_FILE"] = args.log_file

    # Build config overrides
    config_override = {}

    # Apply environment preset if specified
    if args.environment:
        config_override["environment"] = args.environment

    # Cache settings
    if args.disable_cache:
        config_override["cache.enabled"] = False

    # Metrics settings
    if args.disable_metrics:
        config_override["metrics.enabled"] = False

    # Formatting settings
    if args.disable_formatting:
        config_override["formatting.enabled"] = False

    # Registry file override
    if args.registry_file:
        config_override["registry.file"] = args.registry_file

    # Logging overrides (these also work via env vars)
    if args.log_level:
        config_override["logging.level"] = args.log_level

    if args.log_file:
        config_override["logging.file"] = args.log_file

    try:
        # Create appropriate server based on type
        if args.server == "ai-registry":
            server = AIRegistryMCPServer(
                config_file=args.config, config_override=config_override
            )
        elif args.server == "sharepoint":
            server = SharePointConnectorServer(
                config_file=args.config, config_override=config_override
            )
        elif args.server == "api-aggregator":
            server = APIAggregatorServer(
                config_file=args.config, config_override=config_override
            )
        elif args.server == "iot-processor":
            server = IoTProcessorServer(
                config_file=args.config, config_override=config_override
            )
        else:
            raise ValueError(f"Unknown server type: {args.server}")

        # Display startup info
        logging.info(f"Starting {args.server} server...")
        if not args.disable_cache:
            logging.info("Cache: ENABLED")
        if not args.disable_metrics:
            logging.info("Metrics: ENABLED")
        if not args.disable_formatting:
            logging.info("Response Formatting: ENABLED")

        server.run()

    except KeyboardInterrupt:
        logging.info("Server stopped by user")
        sys.exit(0)
    except FileNotFoundError as e:
        logging.error(f"File not found: {e}")
        sys.exit(1)
    except Exception as e:
        if args.debug or os.environ.get("DEBUG") == "true":
            logging.error(f"Server error: {e}", exc_info=True)
        else:
            logging.error(f"Server error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
