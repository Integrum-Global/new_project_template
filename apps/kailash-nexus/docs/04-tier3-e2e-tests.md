# Kailash Nexus - Tier 3 End-to-End Tests

## Overview
This document defines comprehensive Tier 3 E2E tests based on the user flows and enterprise features. These tests validate complete user journeys across all channels (API, CLI, MCP) and ensure enterprise features work correctly in production scenarios.

## Test Organization

Following the Kailash SDK test organization policy:
- **Location**: `apps/kailash-nexus/tests/e2e/`
- **Naming**: `test_e2e_{feature}_{scenario}.py`
- **Framework**: pytest with async support
- **Markers**: `@pytest.mark.e2e`, `@pytest.mark.tier3`

## E2E Test Scenarios

### 1. Developer Journey Tests

#### Test 1.1: Solo Developer - Zero to Hello World
```python
@pytest.mark.e2e
@pytest.mark.tier3
async def test_e2e_solo_developer_hello_world():
    """
    Validates complete journey from installation to first workflow execution.

    User Flow: Solo Developer Flow 1.1
    Channels: CLI, API
    Duration: ~5 minutes
    """
    # Step 1: Start Nexus with zero configuration
    nexus = await start_nexus_zero_config()
    assert nexus.health_check()["healthy"] == True

    # Step 2: Create workflow using CLI
    result = await cli_execute("nexus create workflow hello-world --template=basic")
    assert result.exit_code == 0
    workflow_id = result.output["workflow_id"]

    # Step 3: Test workflow locally
    result = await cli_execute(f"nexus test {workflow_id} --input='{{\"name\": \"World\"}}'")
    assert result.output["message"] == "Hello, World!"

    # Step 4: Deploy workflow
    result = await cli_execute(f"nexus deploy {workflow_id}")
    assert result.output["status"] == "deployed"

    # Step 5: Execute via API
    api_client = create_api_client(nexus.api_url)
    response = await api_client.execute_workflow(workflow_id, {"name": "Nexus"})
    assert response["result"]["message"] == "Hello, Nexus!"

    # Step 6: Check execution history
    history = await cli_execute("nexus history --limit=2")
    assert len(history.output["executions"]) == 2
```

#### Test 1.2: Startup Developer - MVP to Production
```python
@pytest.mark.e2e
@pytest.mark.tier3
@pytest.mark.slow
async def test_e2e_startup_mvp_deployment():
    """
    Validates journey from development to production deployment.

    User Flow: Startup Developer Flow 2.1
    Channels: API, CLI
    Duration: ~15 minutes
    """
    # Step 1: Create development environment
    dev_env = await create_nexus_environment("development")

    # Step 2: Build multi-component workflow
    workflow = await build_complex_workflow([
        "data_ingestion",
        "processing",
        "notification"
    ])

    # Step 3: Run integration tests
    test_results = await run_workflow_tests(workflow, "integration")
    assert test_results["passed"] == test_results["total"]

    # Step 4: Deploy to staging
    staging_env = await create_nexus_environment("staging")
    deployment = await deploy_workflow(workflow, staging_env)
    assert deployment["status"] == "success"

    # Step 5: Run E2E tests in staging
    e2e_results = await run_workflow_tests(workflow, "e2e", env=staging_env)
    assert e2e_results["passed"] == e2e_results["total"]

    # Step 6: Deploy to production with monitoring
    prod_env = await create_nexus_environment("production", monitoring=True)
    prod_deployment = await deploy_workflow(workflow, prod_env)

    # Step 7: Verify production metrics
    await asyncio.sleep(60)  # Let metrics accumulate
    metrics = await get_production_metrics(workflow.id)
    assert metrics["error_rate"] < 0.01
    assert metrics["p95_latency"] < 1000  # ms
```

### 2. Enterprise Journey Tests

#### Test 2.1: Enterprise - Multi-Tenant Deployment
```python
@pytest.mark.e2e
@pytest.mark.tier3
@pytest.mark.enterprise
async def test_e2e_enterprise_multi_tenant():
    """
    Validates multi-tenant enterprise deployment with isolation.

    User Flow: Enterprise Developer Flow 3.1
    Channels: API, CLI, MCP
    Enterprise Features: Multi-tenancy, RBAC, Audit
    Duration: ~20 minutes
    """
    # Step 1: Deploy Nexus with enterprise features
    nexus = await deploy_enterprise_nexus({
        "multi_tenant": True,
        "authentication": "ldap",
        "rbac": True,
        "audit": True
    })

    # Step 2: Create multiple tenants
    tenants = []
    for i in range(3):
        tenant = await create_tenant(f"tenant-{i}", {
            "quota": {"workflows": 10, "executions": 1000},
            "isolation": "strict"
        })
        tenants.append(tenant)

    # Step 3: Deploy workflows per tenant
    for tenant in tenants:
        workflow = await deploy_tenant_workflow(tenant, "data-processor")

        # Verify isolation - cannot access other tenant's resources
        other_tenant = tenants[(tenants.index(tenant) + 1) % 3]
        with pytest.raises(PermissionDeniedError):
            await access_workflow(workflow.id, auth=other_tenant.auth)

    # Step 4: Test cross-channel access with RBAC
    # Admin via CLI
    admin_result = await cli_execute("nexus tenant list", auth="admin")
    assert len(admin_result.output["tenants"]) == 3

    # User via API
    user_client = create_api_client(nexus.api_url, auth=tenants[0].user_auth)
    user_workflows = await user_client.list_workflows()
    assert len(user_workflows) == 1  # Only sees own tenant's workflow

    # AI Agent via MCP
    mcp_client = create_mcp_client(nexus.mcp_url, auth=tenants[1].mcp_auth)
    tools = await mcp_client.discover_tools()
    assert "workflow_data-processor" in [t["name"] for t in tools]

    # Step 5: Verify audit logging
    audit_logs = await get_audit_logs(start_time=test_start)
    assert len(audit_logs) > 50  # All actions logged
    assert all(log["tenant_id"] is not None for log in audit_logs)
```

#### Test 2.2: Enterprise - High Availability Failover
```python
@pytest.mark.e2e
@pytest.mark.tier3
@pytest.mark.enterprise
@pytest.mark.slow
async def test_e2e_enterprise_ha_failover():
    """
    Validates high availability with automatic failover.

    User Flow: Platform Engineer Flow 4.1
    Channels: API, CLI
    Enterprise Features: HA, Monitoring, Auto-recovery
    Duration: ~30 minutes
    """
    # Step 1: Deploy HA cluster
    cluster = await deploy_ha_cluster({
        "nodes": 3,
        "regions": ["us-east-1", "us-west-2", "eu-west-1"],
        "load_balancer": True
    })

    # Step 2: Start continuous workload
    workload = await start_continuous_workload(
        rate=100,  # requests per second
        duration=1800  # 30 minutes
    )

    # Step 3: Verify initial health
    health = await cluster.health_check()
    assert health["status"] == "healthy"
    assert len(health["nodes"]) == 3

    # Step 4: Simulate node failure
    await cluster.nodes[0].stop()
    await asyncio.sleep(30)  # Allow failover

    # Step 5: Verify continued operation
    health_after = await cluster.health_check()
    assert health_after["status"] == "degraded"
    assert len(health_after["healthy_nodes"]) == 2

    # Verify no request failures during failover
    workload_stats = await workload.get_stats()
    assert workload_stats["error_rate"] < 0.001  # < 0.1%

    # Step 6: Test auto-recovery
    await cluster.nodes[0].start()
    await asyncio.sleep(60)  # Allow rebalancing

    health_recovered = await cluster.health_check()
    assert health_recovered["status"] == "healthy"
    assert len(health_recovered["nodes"]) == 3
```

### 3. Integration Journey Tests

#### Test 3.1: API Consumer - Complete Integration
```python
@pytest.mark.e2e
@pytest.mark.tier3
async def test_e2e_api_consumer_integration():
    """
    Validates external system integration via API.

    User Flow: API Consumer Flow 6.1
    Channels: API
    Features: Authentication, Rate Limiting, Webhooks
    Duration: ~10 minutes
    """
    # Step 1: Register API application
    app = await register_api_application({
        "name": "external-system",
        "webhook_url": "https://external.example.com/webhook"
    })
    api_key = app["api_key"]

    # Step 2: Test authentication methods
    # API Key auth
    client1 = create_api_client(auth={"api_key": api_key})
    assert await client1.health_check()

    # OAuth2 flow
    oauth_token = await oauth2_flow(app["client_id"], app["client_secret"])
    client2 = create_api_client(auth={"bearer": oauth_token})
    assert await client2.health_check()

    # Step 3: Execute workflows with rate limiting
    results = []
    for i in range(150):  # Exceed rate limit
        try:
            result = await client1.execute_workflow("test-workflow")
            results.append(result)
        except RateLimitError as e:
            assert e.retry_after > 0
            await asyncio.sleep(e.retry_after)
            result = await client1.execute_workflow("test-workflow")
            results.append(result)

    assert len(results) == 150

    # Step 4: Verify webhook delivery
    webhook_events = await get_webhook_deliveries(app["id"])
    assert len(webhook_events) >= 150
    assert all(e["status"] == "delivered" for e in webhook_events[-10:])
```

#### Test 3.2: MCP Agent - Multi-Tool Workflow
```python
@pytest.mark.e2e
@pytest.mark.tier3
async def test_e2e_mcp_agent_multi_tool():
    """
    Validates AI agent executing complex multi-tool workflow.

    User Flow: AI Agent Flow 8.2
    Channels: MCP
    Features: Tool Discovery, Chaining, Error Recovery
    Duration: ~10 minutes
    """
    # Step 1: Start MCP-enabled Nexus
    nexus = await start_nexus(mcp_enabled=True)

    # Step 2: Connect AI agent
    agent = await create_mcp_agent(nexus.mcp_url)
    session = await agent.connect()

    # Step 3: Discover available tools
    tools = await agent.discover_tools()
    assert len(tools) > 10
    assert any(t["name"] == "workflow_data_processor" for t in tools)

    # Step 4: Execute multi-step task
    task = {
        "goal": "Analyze customer data and send report",
        "steps": [
            "fetch customer data from database",
            "calculate metrics",
            "generate visualization",
            "send email report"
        ]
    }

    result = await agent.execute_complex_task(task)

    # Verify all steps completed
    assert result["status"] == "completed"
    assert len(result["steps_completed"]) == 4
    assert result["report_sent"] == True

    # Step 5: Test error recovery
    task_with_error = {
        "goal": "Process invalid data",
        "data_source": "non_existent_table"
    }

    error_result = await agent.execute_complex_task(task_with_error)
    assert error_result["status"] == "completed_with_recovery"
    assert "fallback" in error_result["recovery_actions"]
```

### 4. Operations Journey Tests

#### Test 4.1: Platform Engineer - Production Deployment
```python
@pytest.mark.e2e
@pytest.mark.tier3
@pytest.mark.infrastructure
async def test_e2e_platform_production_deployment():
    """
    Validates complete production deployment with monitoring.

    User Flow: Platform Engineer Flow 4.1
    Channels: CLI, API
    Features: Infrastructure, Monitoring, Backup
    Duration: ~45 minutes
    """
    # Step 1: Provision infrastructure
    infra = await provision_infrastructure({
        "provider": "aws",
        "config": "production-ha.yaml",
        "terraform": True
    })

    # Step 2: Deploy Nexus cluster
    deployment = await deploy_nexus_cluster(infra, {
        "version": "latest",
        "features": ["all"],
        "monitoring": {
            "prometheus": True,
            "grafana": True,
            "alerting": True
        }
    })

    # Step 3: Configure monitoring
    monitoring = await configure_monitoring(deployment, {
        "metrics": ["standard", "custom"],
        "dashboards": ["operations", "business"],
        "alerts": load_alert_rules("production-alerts.yaml")
    })

    # Step 4: Set up backup
    backup = await configure_backup(deployment, {
        "schedule": "0 2 * * *",  # 2 AM daily
        "retention": 30,  # days
        "destination": "s3://nexus-backups"
    })

    # Step 5: Run smoke tests
    smoke_results = await run_smoke_tests(deployment.url)
    assert smoke_results["all_passed"] == True

    # Step 6: Verify monitoring
    metrics = await monitoring.get_metrics()
    assert metrics["nexus_up"] == 1
    assert metrics["nexus_healthy_nodes"] == deployment.node_count

    # Step 7: Test backup/restore
    test_workflow = await create_test_workflow(deployment)
    await backup.trigger_manual()

    # Simulate data loss
    await delete_workflow(test_workflow.id)

    # Restore
    await backup.restore_latest()
    restored = await get_workflow(test_workflow.id)
    assert restored is not None
```

### 5. Cross-Channel Journey Tests

#### Test 5.1: Unified Session - Cross-Channel Workflow
```python
@pytest.mark.e2e
@pytest.mark.tier3
async def test_e2e_cross_channel_unified_session():
    """
    Validates unified session management across all channels.

    Channels: API, CLI, MCP
    Features: Session Sync, Event Routing, State Management
    Duration: ~15 minutes
    """
    # Step 1: Create session via API
    api_client = create_api_client()
    session = await api_client.create_session({
        "user": "developer@example.com",
        "metadata": {"project": "nexus-test"}
    })
    session_id = session["id"]

    # Step 2: Access same session via CLI
    cli_result = await cli_execute(
        "nexus session info",
        env={"NEXUS_SESSION": session_id}
    )
    assert cli_result.output["user"] == "developer@example.com"
    assert cli_result.output["metadata"]["project"] == "nexus-test"

    # Step 3: Execute workflow via MCP with session
    mcp_client = create_mcp_client(session_id=session_id)
    mcp_result = await mcp_client.execute_tool(
        "workflow_analyzer",
        {"data": "test-data"}
    )

    # Step 4: Verify execution visible across channels
    # Check via API
    api_history = await api_client.get_session_executions(session_id)
    assert len(api_history) == 1
    assert api_history[0]["channel"] == "mcp"

    # Check via CLI
    cli_history = await cli_execute(
        "nexus session history",
        env={"NEXUS_SESSION": session_id}
    )
    assert len(cli_history.output["executions"]) == 1

    # Step 5: Test real-time event sync
    # Subscribe to events via WebSocket (API channel)
    ws_client = await api_client.connect_websocket(session_id)
    events = []

    async def collect_events():
        async for event in ws_client:
            events.append(event)

    # Start event collection
    event_task = asyncio.create_task(collect_events())

    # Trigger events from different channels
    await cli_execute("nexus workflow create test-realtime")
    await mcp_client.execute_tool("test_tool", {})

    # Wait and verify events
    await asyncio.sleep(2)
    event_task.cancel()

    assert len(events) >= 2
    assert any(e["source"] == "cli" for e in events)
    assert any(e["source"] == "mcp" for e in events)
```

## Test Configuration

### Environment Setup
```python
# tests/e2e/conftest.py
import pytest
from kailash_nexus import create_nexus

@pytest.fixture(scope="session")
async def nexus_cluster():
    """Provides a test Nexus cluster for E2E tests."""
    nexus = await create_nexus(
        name="e2e-test-cluster",
        enable_api=True,
        enable_cli=True,
        enable_mcp=True,
        test_mode=True
    )
    yield nexus
    await nexus.cleanup()

@pytest.fixture
async def test_tenant(nexus_cluster):
    """Creates an isolated tenant for each test."""
    tenant = await nexus_cluster.create_tenant(
        name=f"test-{uuid.uuid4()}",
        isolation="strict"
    )
    yield tenant
    await tenant.cleanup()
```

### Performance Requirements
Each E2E test must meet these criteria:
- **Fast Tests**: < 5 minutes
- **Standard Tests**: < 15 minutes
- **Slow Tests**: < 45 minutes (marked with @pytest.mark.slow)
- **Infrastructure Tests**: < 60 minutes (marked with @pytest.mark.infrastructure)

### Success Metrics
- **Coverage**: 100% of critical user flows
- **Reliability**: < 1% flakiness rate
- **Performance**: Meet timing requirements
- **Isolation**: No test interference

## Next Steps
These E2E tests will be used to:
1. Drive implementation of Nexus features
2. Create Tier 1 & 2 tests for components
3. Validate against user requirements
4. Ensure production readiness
5. Generate performance benchmarks
