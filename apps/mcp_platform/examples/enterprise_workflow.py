#!/usr/bin/env python3
"""
Enterprise MCP Workflow Example

This example demonstrates advanced MCP platform features including:
- Multi-tenant support
- Authentication and authorization
- Audit logging
- Rate limiting
- Circuit breaking
"""

from apps.mcp_platform import (
    AuthenticationManager,
    AuthorizationManager,
    EnterpriseGateway,
    ProductionMCPServer,
)
from kailash import WorkflowBuilder, create_gateway


# Example 1: Enterprise MCP Server with Security
def create_secure_mcp_server():
    """Create a production MCP server with enterprise features."""

    # Create production server with security features
    server = ProductionMCPServer(
        name="enterprise-tools",
        description="Enterprise-grade tools with security",
        config={
            "auth_required": True,
            "rate_limit": {"requests_per_minute": 100, "burst": 150},
            "audit_logging": True,
            "encryption": "AES-256-GCM",
        },
    )

    # Register authenticated tools
    @server.tool("process_payment", auth_required=True, roles=["finance", "admin"])
    async def process_payment(amount: float, currency: str, user_id: str) -> dict:
        """Process a payment transaction (requires authentication)."""
        # In production, this would integrate with payment systems
        return {
            "transaction_id": f"TXN-{user_id}-{amount}",
            "status": "pending",
            "amount": amount,
            "currency": currency,
        }

    @server.tool("generate_report", auth_required=True, roles=["analyst", "admin"])
    async def generate_report(report_type: str, date_range: dict) -> dict:
        """Generate business report (requires authentication)."""
        return {
            "report_id": f"RPT-{report_type}-001",
            "status": "generated",
            "url": f"/reports/{report_type}/latest",
        }

    return server


# Example 2: Multi-Tenant Gateway Setup
async def create_multi_tenant_gateway():
    """Set up enterprise gateway with multi-tenant support."""

    # Initialize authentication manager
    auth_manager = AuthenticationManager(
        providers=["oauth2", "saml", "jwt"], mfa_required=True
    )

    # Initialize authorization manager
    authz_manager = AuthorizationManager(
        strategy="rbac",  # Role-based access control
        policies={
            "finance": ["process_payment", "view_transactions"],
            "analyst": ["generate_report", "view_data"],
            "admin": ["*"],  # All permissions
        },
    )

    # Create enterprise gateway
    gateway = EnterpriseGateway(
        auth_manager=auth_manager,
        authz_manager=authz_manager,
        config={
            "multi_tenant": True,
            "tenant_isolation": "strict",
            "audit_retention_days": 90,
            "encryption_at_rest": True,
        },
    )

    # Register MCP servers per tenant
    finance_server = create_secure_mcp_server()
    gateway.register_tenant_server("tenant-001", "finance", finance_server)

    analytics_server = create_secure_mcp_server()
    gateway.register_tenant_server("tenant-001", "analytics", analytics_server)

    return gateway


# Example 3: Enterprise Workflow with MCP
def create_enterprise_workflow():
    """Create a workflow that uses enterprise MCP features."""

    builder = WorkflowBuilder()

    # Authentication node
    builder.add_node(
        "MultiFactorAuthNode",
        "authenticate_user",
        config={"methods": ["password", "totp"], "timeout": 300},
    )

    # MCP tool execution with authorization
    builder.add_node(
        "MCPToolNode",
        "execute_payment",
        config={
            "server": "enterprise-tools",
            "tool": "process_payment",
            "auth_context": "$.authenticate_user.context",
        },
    )

    # Audit logging
    builder.add_node(
        "AuditLogNode",
        "log_transaction",
        config={
            "event_type": "payment_processed",
            "include_user_context": True,
            "compliance": ["PCI-DSS", "SOX"],
        },
    )

    # Connections
    builder.add_connection("authenticate_user", "execute_payment", "success", "")
    builder.add_connection("execute_payment", "log_transaction", "result", "")

    return builder.build()


# Example 4: Circuit Breaker Pattern
async def circuit_breaker_example():
    """Implement circuit breaker for resilient MCP operations."""

    from apps.mcp_platform.core.patterns import CircuitBreaker

    # Create circuit breaker for external service calls
    breaker = CircuitBreaker(
        failure_threshold=5, recovery_timeout=60, expected_exception=Exception
    )

    @breaker.protect
    async def call_external_mcp_service(data: dict) -> dict:
        """Call external MCP service with circuit breaker protection."""
        # Simulated external call
        server = ProductionMCPServer(name="external-service")
        return await server.execute_tool("process", data)

    # Use the protected function
    try:
        result = await call_external_mcp_service({"data": "test"})
        print("Success:", result)
    except Exception as e:
        print("Circuit breaker opened:", e)


# Example 5: Monitoring and Observability
def setup_monitoring():
    """Set up monitoring for MCP platform."""

    from apps.mcp_platform.core.monitoring import MetricsCollector

    # Initialize metrics collector
    metrics = MetricsCollector(
        export_interval=60, exporters=["prometheus", "opentelemetry"]
    )

    # Track MCP metrics
    metrics.track_tool_execution(
        "enterprise-tools", "process_payment", 0.125, "success"
    )
    metrics.track_auth_attempt("tenant-001", "oauth2", True)
    metrics.track_rate_limit("tenant-001", "enterprise-tools", False)

    # Export metrics endpoint
    # Available at: GET /metrics (Prometheus format)

    return metrics


if __name__ == "__main__":
    import asyncio

    print("MCP Platform Enterprise Workflow Examples")
    print("=" * 50)

    # Example 1: Secure server
    print("\n1. Secure MCP Server:")
    server = create_secure_mcp_server()
    print(f"   Created: {server.name}")
    print("   Security: Auth required, Rate limited, Audit logging")

    # Example 2: Multi-tenant gateway
    print("\n2. Multi-Tenant Gateway:")
    gateway = asyncio.run(create_multi_tenant_gateway())
    print("   Features: Multi-tenant, RBAC, Audit trail")

    # Example 3: Enterprise workflow
    print("\n3. Enterprise Workflow:")
    workflow = create_enterprise_workflow()
    print("   Nodes: Authentication → Payment → Audit")

    # Example 4: Monitoring
    print("\n4. Monitoring Setup:")
    metrics = setup_monitoring()
    print("   Exporters: Prometheus, OpenTelemetry")

    print("\n✓ Enterprise examples completed!")
