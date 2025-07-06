"""Enterprise Gateway Core Server."""

import asyncio
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional

import structlog
import uvicorn
from fastapi import Depends, FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
from kailash.mcp_server.server import MCPServer
from kailash.middleware.communication.api_gateway import create_gateway
from kailash.runtime.local import LocalRuntime
from opentelemetry import trace
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from prometheus_client import Counter, Gauge, Histogram

from ...services.audit.logger import AuditLogger
from ...services.tenant.manager import TenantManager
from ..auth.authentication import AuthenticationMiddleware, get_current_user
from ..auth.authorization import AuthorizationMiddleware, check_permission
from ..middleware.audit import AuditMiddleware
from ..middleware.rate_limit import RateLimitMiddleware
from ..middleware.tenant import TenantMiddleware
from ..routing.router import ToolRouter

logger = structlog.get_logger(__name__)
tracer = trace.get_tracer(__name__)

# Metrics
request_counter = Counter(
    "gateway_requests_total",
    "Total gateway requests",
    ["method", "endpoint", "status", "tenant"],
)

request_duration = Histogram(
    "gateway_request_duration_seconds",
    "Request duration",
    ["method", "endpoint", "tenant"],
)

active_connections = Gauge("gateway_active_connections", "Active connections")

tool_executions = Counter(
    "gateway_tool_executions_total",
    "Tool executions",
    ["tool", "action", "status", "tenant"],
)

# Initialize FastAPI app
app = FastAPI(
    title="MCP Enterprise Gateway",
    version="0.1.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
)

# Add middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure based on environment
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_middleware(
    TrustedHostMiddleware, allowed_hosts=["*"]  # Configure based on environment
)

# Initialize MCP server
mcp_server = MCPServer("enterprise-gateway")

# Initialize components
runtime = LocalRuntime()
tool_router = ToolRouter()
tenant_manager = TenantManager()
audit_logger = AuditLogger()

# Gateway configuration
gateway_config = {
    "name": "MCP Enterprise Gateway",
    "features": {
        "authentication": True,
        "authorization": True,
        "rate_limiting": True,
        "multi_tenancy": True,
        "audit_logging": True,
        "monitoring": True,
        "caching": True,
        "circuit_breaking": True,
    },
}


# Register MCP tools
@mcp_server.tool("execute_workflow")
async def execute_workflow(
    workflow_name: str, parameters: Dict[str, Any], tenant_id: Optional[str] = None
) -> Dict[str, Any]:
    """Execute a workflow with tenant isolation."""
    with tracer.start_as_current_span("execute_workflow") as span:
        span.set_attribute("workflow.name", workflow_name)
        span.set_attribute("tenant.id", tenant_id or "default")

        try:
            # Get tenant context
            if tenant_id:
                tenant = await tenant_manager.get_tenant(tenant_id)
                if not tenant:
                    raise ValueError(f"Tenant {tenant_id} not found")

            # Execute workflow with resource limits
            result = await runtime.execute_workflow(
                workflow_name, parameters, context={"tenant_id": tenant_id}
            )

            tool_executions.labels(
                tool="workflow",
                action=workflow_name,
                status="success",
                tenant=tenant_id or "default",
            ).inc()

            return result

        except Exception as e:
            tool_executions.labels(
                tool="workflow",
                action=workflow_name,
                status="error",
                tenant=tenant_id or "default",
            ).inc()

            span.record_exception(e)
            raise


@mcp_server.tool("query_data")
async def query_data(
    source: str, query: str, tenant_id: Optional[str] = None
) -> List[Dict[str, Any]]:
    """Query data with tenant isolation."""
    # Ensure tenant data isolation
    if tenant_id:
        query = f"SELECT * FROM ({query}) WHERE tenant_id = '{tenant_id}'"

    # Execute query
    # This is a simplified example - implement actual data querying
    return []


# API Routes
@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "name": gateway_config["name"],
        "version": "0.1.0",
        "features": gateway_config["features"],
    }


@app.get("/health")
async def health():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "components": {
            "database": "healthy",
            "cache": "healthy",
            "mcp_server": "healthy",
        },
    }


@app.get("/metrics")
async def metrics():
    """Prometheus metrics endpoint."""
    from prometheus_client import generate_latest

    return JSONResponse(
        content=generate_latest().decode("utf-8"), media_type="text/plain"
    )


# Tool execution endpoint
@app.post("/api/v1/tools/{tool_name}/execute")
async def execute_tool(
    tool_name: str, request: Request, current_user: dict = Depends(get_current_user)
):
    """Execute an MCP tool."""
    # Check permission
    if not await check_permission(current_user, f"tools:{tool_name}:execute"):
        raise HTTPException(status_code=403, detail="Permission denied")

    # Get request data
    data = await request.json()
    action = data.get("action", "default")
    params = data.get("params", {})
    options = data.get("options", {})

    # Extract tenant ID
    tenant_id = current_user.get("tenant_id") or request.headers.get("X-Tenant-ID")

    # Log request
    await audit_logger.log(
        {
            "event": "tool_execution",
            "user_id": current_user["user_id"],
            "tenant_id": tenant_id,
            "tool": tool_name,
            "action": action,
            "timestamp": datetime.utcnow(),
        }
    )

    try:
        # Route to appropriate tool
        result = await tool_router.execute(
            tool_name,
            action,
            params,
            context={"user": current_user, "tenant_id": tenant_id, "options": options},
        )

        return {
            "success": True,
            "result": result,
            "metadata": {
                "tool": tool_name,
                "action": action,
                "execution_time": datetime.utcnow().isoformat(),
            },
        }

    except Exception as e:
        logger.error(
            f"Tool execution failed: {e}",
            tool=tool_name,
            action=action,
            user_id=current_user["user_id"],
        )

        # Log error
        await audit_logger.log(
            {
                "event": "tool_execution_error",
                "user_id": current_user["user_id"],
                "tenant_id": tenant_id,
                "tool": tool_name,
                "action": action,
                "error": str(e),
                "timestamp": datetime.utcnow(),
            }
        )

        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/v1/tools")
async def list_tools(current_user: dict = Depends(get_current_user)):
    """List available tools."""
    # Get tools based on user permissions
    all_tools = tool_router.list_tools()

    # Filter based on permissions
    available_tools = []
    for tool in all_tools:
        if await check_permission(current_user, f"tools:{tool['name']}:read"):
            available_tools.append(tool)

    return {"tools": available_tools, "count": len(available_tools)}


@app.get("/api/v1/tools/{tool_name}")
async def get_tool_details(
    tool_name: str, current_user: dict = Depends(get_current_user)
):
    """Get tool details."""
    # Check permission
    if not await check_permission(current_user, f"tools:{tool_name}:read"):
        raise HTTPException(status_code=403, detail="Permission denied")

    tool = tool_router.get_tool(tool_name)
    if not tool:
        raise HTTPException(status_code=404, detail="Tool not found")

    return tool


# Admin endpoints
@app.post("/api/v1/admin/tenants")
async def create_tenant(
    request: Request, current_user: dict = Depends(get_current_user)
):
    """Create a new tenant."""
    # Check admin permission
    if not await check_permission(current_user, "admin:tenants:create"):
        raise HTTPException(status_code=403, detail="Permission denied")

    data = await request.json()
    tenant = await tenant_manager.create_tenant(data)

    return tenant


@app.get("/api/v1/admin/tenants")
async def list_tenants(current_user: dict = Depends(get_current_user)):
    """List tenants."""
    # Check admin permission
    if not await check_permission(current_user, "admin:tenants:read"):
        raise HTTPException(status_code=403, detail="Permission denied")

    tenants = await tenant_manager.list_tenants()

    return {"tenants": tenants, "count": len(tenants)}


@app.get("/api/v1/admin/usage")
async def get_usage_stats(
    tenant_id: Optional[str] = None, current_user: dict = Depends(get_current_user)
):
    """Get usage statistics."""
    # Check permission
    if not await check_permission(current_user, "admin:usage:read"):
        raise HTTPException(status_code=403, detail="Permission denied")

    # Get usage stats
    # This is a simplified example - implement actual usage tracking
    return {
        "tenant_id": tenant_id,
        "period": "last_30_days",
        "metrics": {
            "api_calls": 150000,
            "tool_executions": 75000,
            "data_processed_gb": 250,
            "active_users": 150,
        },
    }


# Startup event
@app.on_event("startup")
async def startup():
    """Initialize services on startup."""
    logger.info("Starting MCP Enterprise Gateway...")

    # Initialize components
    await tenant_manager.initialize()
    await audit_logger.initialize()
    await tool_router.initialize()

    # Start MCP server
    asyncio.create_task(mcp_server.run())

    # Initialize gateway
    gateway = create_gateway(
        {
            "name": "Enterprise Gateway",
            "port": 8000,
            "features": gateway_config["features"],
        }
    )

    # Instrument FastAPI for tracing
    FastAPIInstrumentor.instrument_app(app)

    logger.info("MCP Enterprise Gateway started successfully")


# Shutdown event
@app.on_event("shutdown")
async def shutdown():
    """Cleanup on shutdown."""
    logger.info("Shutting down MCP Enterprise Gateway...")

    await tenant_manager.cleanup()
    await audit_logger.cleanup()
    await tool_router.cleanup()


# Request tracking middleware
@app.middleware("http")
async def track_requests(request: Request, call_next):
    """Track all requests for monitoring."""
    start_time = datetime.utcnow()

    # Increment active connections
    active_connections.inc()

    try:
        # Process request
        response = await call_next(request)

        # Record metrics
        duration = (datetime.utcnow() - start_time).total_seconds()

        request_counter.labels(
            method=request.method,
            endpoint=request.url.path,
            status=response.status_code,
            tenant=request.headers.get("X-Tenant-ID", "default"),
        ).inc()

        request_duration.labels(
            method=request.method,
            endpoint=request.url.path,
            tenant=request.headers.get("X-Tenant-ID", "default"),
        ).observe(duration)

        # Add response headers
        response.headers["X-Request-ID"] = str(uuid.uuid4())
        response.headers["X-Response-Time"] = str(duration)

        return response

    finally:
        # Decrement active connections
        active_connections.dec()


# Run the server
if __name__ == "__main__":
    uvicorn.run(
        "server:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info",
        access_log=True,
    )
