"""
Service Discovery System for Apps

Automatically discovers apps by scanning manifests and provides
unified service registration and routing capabilities.
"""

import yaml
import asyncio
import logging
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from datetime import datetime
import httpx

logger = logging.getLogger(__name__)


@dataclass
class AppManifest:
    """Parsed app manifest with all capabilities."""
    name: str
    version: str
    type: str  # api, mcp, hybrid
    description: str
    capabilities: Dict[str, Any]
    dependencies: Dict[str, List[str]]
    deployment: Dict[str, Any]
    tags: List[str]
    manifest_path: Path
    
    @property
    def has_api(self) -> bool:
        """Check if app has API capabilities."""
        return self.capabilities.get("api", {}).get("enabled", False)
    
    @property
    def has_mcp(self) -> bool:
        """Check if app has MCP capabilities."""
        return self.capabilities.get("mcp", {}).get("enabled", False)
    
    @property
    def api_port(self) -> int:
        """Get API port if available."""
        return self.capabilities.get("api", {}).get("port", 8000)
    
    @property
    def api_endpoints(self) -> List[str]:
        """Get list of API endpoints."""
        return self.capabilities.get("api", {}).get("endpoints", [])
    
    @property
    def mcp_tools(self) -> List[str]:
        """Get list of MCP tools."""
        return self.capabilities.get("mcp", {}).get("tools", [])
    
    @property
    def health_check_url(self) -> str:
        """Get health check URL for the app."""
        health_path = self.deployment.get("health_check", "/health")
        return f"http://{self.name}:{self.api_port}{health_path}"


class ServiceRegistry:
    """Centralized service registry for all apps."""
    
    def __init__(self, apps_directory: Path = None):
        self.apps_directory = apps_directory or Path("apps")
        self.services: Dict[str, AppManifest] = {}
        self.health_status: Dict[str, Dict[str, Any]] = {}
        
    def discover_apps(self) -> List[AppManifest]:
        """Scan apps directory and return all discovered apps."""
        apps = []
        
        if not self.apps_directory.exists():
            logger.warning(f"Apps directory {self.apps_directory} does not exist")
            return apps
            
        for app_dir in self.apps_directory.iterdir():
            if not app_dir.is_dir():
                continue
                
            # Skip template directories
            if app_dir.name.startswith("_template"):
                continue
                
            manifest_path = app_dir / "manifest.yaml"
            if not manifest_path.exists():
                logger.warning(f"No manifest.yaml found for app: {app_dir.name}")
                continue
                
            try:
                with open(manifest_path, 'r') as f:
                    manifest_data = yaml.safe_load(f)
                
                # Create AppManifest instance
                app = AppManifest(
                    name=manifest_data["name"],
                    version=manifest_data["version"],
                    type=manifest_data["type"],
                    description=manifest_data["description"],
                    capabilities=manifest_data.get("capabilities", {}),
                    dependencies=manifest_data.get("dependencies", {"required": [], "optional": []}),
                    deployment=manifest_data.get("deployment", {}),
                    tags=manifest_data.get("tags", []),
                    manifest_path=manifest_path
                )
                
                apps.append(app)
                logger.info(f"Discovered app: {app.name} (type: {app.type})")
                
            except Exception as e:
                logger.error(f"Failed to parse manifest for {app_dir.name}: {e}")
                
        return apps
    
    def register_services(self, apps: List[AppManifest]):
        """Register all discovered apps as services."""
        for app in apps:
            self.services[app.name] = app
            logger.info(f"Registered service: {app.name}")
    
    async def check_service_health(self, service_name: str) -> Dict[str, Any]:
        """Check health of a specific service."""
        if service_name not in self.services:
            return {"status": "unknown", "error": "Service not found"}
            
        app = self.services[service_name]
        
        if not app.has_api:
            # For non-API services, assume healthy if process is running
            return {"status": "healthy", "type": "non-api"}
            
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get(app.health_check_url)
                if response.status_code == 200:
                    return {
                        "status": "healthy",
                        "response_time": response.elapsed.total_seconds(),
                        "details": response.json() if response.headers.get("content-type", "").startswith("application/json") else {}
                    }
                else:
                    return {
                        "status": "unhealthy", 
                        "error": f"HTTP {response.status_code}"
                    }
        except Exception as e:
            return {
                "status": "unreachable",
                "error": str(e)
            }
    
    async def check_all_health(self) -> Dict[str, Dict[str, Any]]:
        """Check health of all registered services."""
        health_checks = {}
        
        # Run health checks concurrently
        tasks = []
        for service_name in self.services.keys():
            tasks.append(self.check_service_health(service_name))
            
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        for service_name, result in zip(self.services.keys(), results):
            if isinstance(result, Exception):
                health_checks[service_name] = {
                    "status": "error",
                    "error": str(result)
                }
            else:
                health_checks[service_name] = result
                
        self.health_status = health_checks
        return health_checks
    
    def get_services_by_type(self, service_type: str) -> List[AppManifest]:
        """Get all services of a specific type."""
        return [app for app in self.services.values() if app.type == service_type]
    
    def get_services_with_capability(self, capability: str) -> List[AppManifest]:
        """Get all services that have a specific capability."""
        services = []
        for app in self.services.values():
            if capability == "api" and app.has_api:
                services.append(app)
            elif capability == "mcp" and app.has_mcp:
                services.append(app)
        return services
    
    def get_api_services(self) -> List[AppManifest]:
        """Get all services that expose APIs."""
        return [app for app in self.services.values() if app.has_api]
    
    def get_mcp_services(self) -> List[AppManifest]:
        """Get all services that provide MCP tools."""
        return [app for app in self.services.values() if app.has_mcp]
    
    def get_service(self, name: str) -> Optional[AppManifest]:
        """Get a specific service by name."""
        return self.services.get(name)
    
    def get_all_mcp_tools(self) -> Dict[str, List[str]]:
        """Get aggregated MCP tools from all services."""
        tools = {}
        for app in self.get_mcp_services():
            tools[app.name] = app.mcp_tools
        return tools
    
    def get_routing_table(self) -> Dict[str, Any]:
        """Generate routing table for the gateway."""
        routing = {
            "api_services": {},
            "mcp_services": {},
            "health_endpoints": {}
        }
        
        for app in self.services.values():
            if app.has_api:
                routing["api_services"][app.name] = {
                    "host": app.name,
                    "port": app.api_port,
                    "endpoints": app.api_endpoints,
                    "health_check": app.health_check_url
                }
                routing["health_endpoints"][app.name] = app.health_check_url
                
            if app.has_mcp:
                routing["mcp_services"][app.name] = {
                    "host": app.name,
                    "port": app.api_port,  # Assuming MCP over HTTP
                    "tools": app.mcp_tools,
                    "protocol": app.capabilities.get("mcp", {}).get("protocol", "stdio")
                }
        
        return routing


# Global service registry instance
registry = ServiceRegistry()


async def initialize_service_discovery(apps_directory: Path = None):
    """Initialize the service discovery system."""
    logger.info("🔍 Starting service discovery...")
    
    # Update registry path if provided
    if apps_directory:
        registry.apps_directory = apps_directory
    
    # Try different possible paths for apps directory
    possible_paths = [
        Path("/apps"),
        Path("apps"),
        Path("../apps")
    ]
    
    for path in possible_paths:
        if path.exists():
            logger.info(f"Found apps directory at: {path}")
            registry.apps_directory = path
            break
    else:
        logger.warning("No apps directory found in any of the expected locations")
    
    # Discover all apps
    apps = registry.discover_apps()
    logger.info(f"Found {len(apps)} apps")
    
    # Register services
    registry.register_services(apps)
    
    # Check initial health
    await registry.check_all_health()
    
    logger.info("✅ Service discovery initialized")
    return registry


def get_registry() -> ServiceRegistry:
    """Get the global service registry instance."""
    return registry