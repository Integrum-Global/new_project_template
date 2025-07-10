#!/usr/bin/env python3
"""
Nexus Application Main Entry Point

Production-ready entry point with proper configuration and error handling.
"""

import asyncio
import logging
import signal
import sys
from pathlib import Path
from typing import Optional

from nexus.core.application import create_application
from nexus.core.config import NexusConfig


# Configure logging
def setup_logging(level: str = "INFO"):
    """Setup application logging."""
    logging.basicConfig(
        level=getattr(logging, level.upper()),
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[logging.StreamHandler(sys.stdout)],
    )


# Global app instance for signal handlers
app: Optional["NexusApplication"] = None


async def shutdown(sig: signal.Signals):
    """Graceful shutdown handler."""
    logging.info(f"Received signal {sig.name}. Shutting down...")
    if app:
        await app.stop()


def setup_signal_handlers():
    """Setup signal handlers for graceful shutdown."""
    loop = asyncio.get_event_loop()

    for sig in [signal.SIGTERM, signal.SIGINT]:
        loop.add_signal_handler(sig, lambda s=sig: asyncio.create_task(shutdown(s)))


async def main():
    """Main application entry point."""
    global app

    # Setup logging
    setup_logging()
    logger = logging.getLogger(__name__)

    logger.info("Starting Nexus Application...")

    # Load configuration
    config_path = Path("config/production.yaml")
    if config_path.exists():
        config = NexusConfig.from_yaml(str(config_path))
    else:
        # Use defaults with environment overrides
        config = NexusConfig()

    # Create application
    app = create_application(
        name=config.name,
        description=config.description,
        version=config.version,
        channels=config.channels.dict(),
        features=config.features.dict(),
    )

    # Setup signal handlers
    setup_signal_handlers()

    try:
        # Start application
        await app.start()

        logger.info(
            f"Nexus Application '{config.name}' v{config.version} started successfully"
        )
        logger.info(
            f"API: http://{config.channels.api.host}:{config.channels.api.port}"
        )
        if config.channels.mcp.enabled:
            logger.info(
                f"MCP: tcp://{config.channels.mcp.host}:{config.channels.mcp.port}"
            )

        # Run forever
        await app.run_forever()

    except Exception as e:
        logger.error(f"Application error: {str(e)}")
        raise
    finally:
        if app and app._running:
            await app.stop()
        logger.info("Nexus Application stopped")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
    except Exception as e:
        logging.error(f"Fatal error: {str(e)}")
        sys.exit(1)
