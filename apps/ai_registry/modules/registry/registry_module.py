"""
Registry Module - Pure Kailash Implementation

Provides core registry data management and indexing.
"""

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class RegistryModule:
    """Registry module using pure Kailash SDK components."""

    def __init__(self, server, runtime):
        self.server = server
        self.runtime = runtime
        self.use_cases = []
        self.stats = {}
        self._ready = True
        self._load_registry_data()
        logger.info("Registry Module initialized")

    def _load_registry_data(self):
        """Load existing registry data."""
        try:
            registry_file = (
                Path(__file__).parent.parent.parent
                / "data"
                / "combined_ai_registry.json"
            )
            if registry_file.exists():
                with open(registry_file, "r") as f:
                    data = json.load(f)
                    self.use_cases = data.get("use_cases", [])
                    self._calculate_stats()
            logger.info(f"Loaded {len(self.use_cases)} use cases from registry")
        except Exception as e:
            logger.warning(f"Could not load registry data: {str(e)}")

    def _calculate_stats(self):
        """Calculate registry statistics."""
        if not self.use_cases:
            self.stats = {"total_use_cases": 0}
            return

        domains = set()
        ai_methods = set()
        statuses = {}

        for case in self.use_cases:
            if case.get("application_domain"):
                domains.add(case["application_domain"])

            for method in case.get("ai_methods", []):
                ai_methods.add(method)

            status = case.get("status", "unknown")
            statuses[status] = statuses.get(status, 0) + 1

        self.stats = {
            "total_use_cases": len(self.use_cases),
            "unique_domains": len(domains),
            "unique_ai_methods": len(ai_methods),
            "status_breakdown": statuses,
            "rag_enabled": True,
        }

    def get_statistics(self) -> Dict[str, Any]:
        """Get registry statistics."""
        return self.stats

    def is_ready(self) -> bool:
        return self._ready

    def get_status(self) -> Dict[str, Any]:
        return {
            "healthy": True,
            "status": "Ready",
            "use_cases_loaded": len(self.use_cases),
            "last_activity": datetime.now().isoformat(),
        }

    def get_info(self) -> Dict[str, Any]:
        return {
            "name": "Registry Module",
            "version": "1.0.0",
            "description": "Core registry data management and indexing",
            "data_sources": ["combined_ai_registry.json", "Section 7 PDFs"],
        }
