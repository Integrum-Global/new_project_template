#!/usr/bin/env python3
"""
Nexus Data Workflow Example with QueryBuilder and QueryCache

Demonstrates how workflows executed by Nexus can use QueryBuilder and QueryCache
for efficient data operations.
"""

import sys
from pathlib import Path

# Add SDK src to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent / "src"))

from kailash.nodes.code import PythonCodeNode
from kailash.runtime.local import LocalRuntime
from kailash.workflow.builder import WorkflowBuilder


def create_data_processing_workflow():
    """Create a workflow that uses QueryBuilder and QueryCache for data operations"""

    workflow = WorkflowBuilder()

    # Node 1: Initialize QueryBuilder and QueryCache
    workflow.add_node(
        "PythonCodeNode",
        "init_query_system",
        {
            "code": """
def execute(input_data):
    from kailash.nodes.data.query_builder import create_query_builder
    from kailash.nodes.data.query_cache import QueryCache, CacheInvalidationStrategy

    # Initialize query builder based on database type
    db_type = input_data.get("database_type", "postgresql")
    builder = create_query_builder(db_type)

    # Initialize query cache
    cache = QueryCache(
        redis_host="localhost",
        redis_port=6379,
        invalidation_strategy=CacheInvalidationStrategy.PATTERN_BASED,
        default_ttl=300
    )

    return {
        "query_builder": builder,
        "query_cache": cache,
        "database_type": db_type,
        "status": "Query system initialized"
    }
"""
        },
    )

    # Node 2: Build optimized query
    workflow.add_node(
        "PythonCodeNode",
        "build_query",
        {
            "code": """
def execute(input_data):
    builder = input_data["query_builder"]
    filters = input_data.get("filters", {})
    tenant_id = input_data.get("tenant_id")

    # Reset and configure table
    builder.reset().table("users")

    # Add tenant isolation if multi-tenant
    if tenant_id:
        builder.tenant(tenant_id)

    # Add dynamic filters
    if filters.get("min_age"):
        builder.where("age", "$gte", filters["min_age"])

    if filters.get("status"):
        builder.where("status", "$in", filters["status"])

    if filters.get("search"):
        builder.where("name", "$ilike", f"%{filters['search']}%")

    if filters.get("has_preferences"):
        builder.where("metadata", "$has_key", "preferences")

    # Build optimized SQL
    sql, params = builder.build_select([
        "id", "name", "email", "status", "created_at"
    ])

    return {
        "sql": sql,
        "parameters": params,
        "tenant_id": tenant_id,
        "query_builder": builder,
        "query_cache": input_data["query_cache"]
    }
"""
        },
    )

    # Node 3: Execute with caching
    workflow.add_node(
        "PythonCodeNode",
        "execute_cached_query",
        {
            "code": """
def execute(input_data):
    cache = input_data["query_cache"]
    sql = input_data["sql"]
    parameters = input_data["parameters"]
    tenant_id = input_data.get("tenant_id")

    # Try cache first
    cached_result = cache.get(sql, parameters, tenant_id=tenant_id)
    if cached_result:
        return {
            "result": cached_result["result"],
            "cache_hit": True,
            "cached_at": cached_result["cached_at"],
            "source": "cache"
        }

    # Simulate database query execution
    result = {
        "users": [
            {"id": 1, "name": "John Doe", "email": "john@example.com", "status": "active"},
            {"id": 2, "name": "Jane Smith", "email": "jane@example.com", "status": "premium"}
        ],
        "total": 2,
        "query": sql
    }

    # Cache the result
    cache.set(sql, parameters, result, tenant_id=tenant_id, ttl=300)

    return {
        "result": result,
        "cache_hit": False,
        "source": "database"
    }
"""
        },
    )

    # Node 4: Process and transform data
    workflow.add_node(
        "PythonCodeNode",
        "transform_data",
        {
            "code": """
def execute(input_data):
    result = input_data["result"]
    cache_hit = input_data["cache_hit"]

    # Transform user data
    if "users" in result:
        users = result["users"]

        # Add computed fields
        for user in users:
            user["display_name"] = user["name"].upper()
            user["email_domain"] = user["email"].split("@")[1]

    # Add metadata
    metadata = {
        "processed_at": "2024-01-15T10:30:00Z",
        "cache_hit": cache_hit,
        "source": input_data["source"],
        "total_users": len(result.get("users", []))
    }

    return {
        "transformed_result": result,
        "metadata": metadata,
        "query_cache": input_data.get("query_cache")
    }
"""
        },
    )

    # Node 5: Cache invalidation (for updates)
    workflow.add_node(
        "PythonCodeNode",
        "invalidate_cache",
        {
            "code": """
def execute(input_data):
    cache = input_data.get("query_cache")
    tenant_id = input_data.get("tenant_id")

    if not cache:
        return {"invalidated": False, "reason": "No cache available"}

    # Invalidate all user-related cache entries
    deleted_count = cache.invalidate_table("users", tenant_id=tenant_id)

    return {
        "invalidated": True,
        "deleted_count": deleted_count,
        "tenant_id": tenant_id
    }
"""
        },
    )

    # Connect the workflow
    workflow.add_connection(
        "init_query_system", "query_builder", "build_query", "query_builder"
    )
    workflow.add_connection(
        "init_query_system", "query_cache", "build_query", "query_cache"
    )
    workflow.add_connection(
        "init_query_system", "database_type", "build_query", "database_type"
    )

    workflow.add_connection("build_query", "sql", "execute_cached_query", "sql")
    workflow.add_connection(
        "build_query", "parameters", "execute_cached_query", "parameters"
    )
    workflow.add_connection(
        "build_query", "tenant_id", "execute_cached_query", "tenant_id"
    )
    workflow.add_connection(
        "build_query", "query_cache", "execute_cached_query", "query_cache"
    )

    workflow.add_connection(
        "execute_cached_query", "result", "transform_data", "result"
    )
    workflow.add_connection(
        "execute_cached_query", "cache_hit", "transform_data", "cache_hit"
    )
    workflow.add_connection(
        "execute_cached_query", "source", "transform_data", "source"
    )

    return workflow


def create_nexus_compatible_workflow():
    """Create a workflow formatted for Nexus platform deployment"""

    workflow_config = {
        "name": "data-processor-with-cache",
        "version": "1.0.0",
        "description": "High-performance data processing with QueryBuilder and Redis caching",
        "tags": ["data", "cache", "performance", "multi-tenant"],
        "requirements": {"redis": ">=6.0", "postgresql": ">=12.0"},  # or mysql, sqlite
        "workflow": create_data_processing_workflow(),
        "examples": [
            {
                "name": "basic_user_query",
                "input": {
                    "database_type": "postgresql",
                    "filters": {"min_age": 18, "status": ["active", "premium"]},
                },
            },
            {
                "name": "multi_tenant_search",
                "input": {
                    "database_type": "postgresql",
                    "tenant_id": "tenant_123",
                    "filters": {"search": "john", "has_preferences": True},
                },
            },
        ],
    }

    return workflow_config


def demonstrate_nexus_integration():
    """Demonstrate how this workflow would be used in Nexus"""

    print("🔄 Nexus Data Workflow with QueryBuilder & QueryCache")
    print("=" * 60)

    # Create the workflow
    workflow = create_data_processing_workflow()

    print("\n1. Workflow Structure:")
    print("   ┌─ init_query_system (QueryBuilder + QueryCache)")
    print("   ├─ build_query (MongoDB-style query building)")
    print("   ├─ execute_cached_query (Redis caching)")
    print("   ├─ transform_data (Data processing)")
    print("   └─ invalidate_cache (Cache management)")

    # Example input data
    test_inputs = [
        {
            "name": "Basic Query",
            "data": {
                "database_type": "postgresql",
                "filters": {"min_age": 21, "status": ["active", "premium"]},
            },
        },
        {
            "name": "Multi-tenant Query",
            "data": {
                "database_type": "postgresql",
                "tenant_id": "tenant_123",
                "filters": {"search": "john", "has_preferences": True},
            },
        },
    ]

    print("\n2. Test Scenarios:")
    for i, test in enumerate(test_inputs, 1):
        print(f"   {i}. {test['name']}")
        print(f"      Database: {test['data']['database_type']}")
        if "tenant_id" in test["data"]:
            print(f"      Tenant: {test['data']['tenant_id']}")
        print(f"      Filters: {test['data']['filters']}")

    # Nexus deployment commands
    print("\n3. Nexus Deployment Commands:")
    print("   # Register workflow with Nexus")
    print("   nexus register data-processor-with-cache.py")
    print()
    print("   # Execute via API")
    print(
        "   curl -X POST http://localhost:8000/workflows/data-processor-with-cache/execute \\"
    )
    print("        -H 'Content-Type: application/json' \\")
    print('        -d \'{"filters": {"min_age": 21, "status": ["active"]}}\'')
    print()
    print("   # Execute via CLI")
    print(
        '   nexus run data-processor-with-cache --input \'{"filters": {"min_age": 21}}\''
    )
    print()
    print("   # Execute via MCP")
    print("   # AI agent can call this workflow through MCP protocol")

    print("\n4. Performance Benefits:")
    print("   ✅ MongoDB-style queries work across PostgreSQL, MySQL, SQLite")
    print("   ✅ Redis caching reduces database load")
    print("   ✅ Multi-tenant isolation in both queries and cache")
    print("   ✅ Pattern-based cache invalidation")
    print("   ✅ Automatic tenant-aware query building")

    print("\n5. Enterprise Features:")
    print("   🔐 Tenant isolation at query and cache level")
    print("   📊 Cache hit rate monitoring")
    print("   🚀 Cross-database compatibility")
    print("   🔄 Intelligent cache invalidation")
    print("   📈 Performance optimization")


if __name__ == "__main__":
    demonstrate_nexus_integration()

    print("\n" + "=" * 60)
    print("✅ Nexus Data Workflow Example Complete!")
    print("\nKey Points:")
    print("• Nexus orchestrates workflows that USE QueryBuilder/QueryCache")
    print("• Not integrated into Nexus core (which is correct)")
    print("• Workflows benefit from caching and query optimization")
    print("• Multi-channel access (API, CLI, MCP) to cached data workflows")
