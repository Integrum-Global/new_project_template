"""
User Search and Filtering API using Kailash SDK
"""

from typing import Any, Dict, List, Optional

from apps.user_management.config.settings import UserManagementConfig
from kailash.runtime.local import LocalRuntime
from kailash.workflow.builder import WorkflowBuilder


class SearchAPI:
    """User search and filtering functionality"""

    def __init__(self):
        self.config = UserManagementConfig()
        self.runtime = LocalRuntime()

    def create_user_search_workflow(self) -> WorkflowBuilder:
        """Create workflow for user search with filters"""
        workflow = WorkflowBuilder("user_search")

        # Add nodes
        workflow.add_node(
            "permission_checker",
            "PermissionCheckNode",
            self.config.NODE_CONFIGS["PermissionCheckNode"],
        )
        workflow.add_node("query_builder", "PythonCodeNode")
        workflow.add_node(
            "user_searcher",
            "UserManagementNode",
            self.config.NODE_CONFIGS["UserManagementNode"],
        )
        workflow.add_node("result_formatter", "PythonCodeNode")
        workflow.add_node(
            "audit_logger",
            "EnterpriseAuditLogNode",
            self.config.NODE_CONFIGS["EnterpriseAuditLogNode"],
        )

        # Connect nodes
        workflow.add_connection("input", "permission_checker", "data", "input")
        workflow.add_connection(
            "permission_checker", "query_builder", "result", "input"
        )
        workflow.add_connection("query_builder", "user_searcher", "result", "input")
        workflow.add_connection("user_searcher", "result_formatter", "result", "input")
        workflow.add_connection("result_formatter", "audit_logger", "result", "input")
        workflow.add_connection("audit_logger", "output", "result", "result")

        # Configure permission checker
        workflow.update_node(
            "permission_checker",
            {"user_id": "$.user_id", "resource": "users", "action": "search"},
        )

        # Configure query builder
        query_code = """
if not input_data.get("allowed"):
    result = {"success": False, "error": "Permission denied"}
else:
    # Build search query from filters
    filters = input_data.get("filters", {})
    search_params = {
        "operation": "search_users",
        "filters": {}
    }

    # Text search
    if filters.get("query"):
        search_params["query"] = filters["query"]

    # Status filter
    if filters.get("status"):
        search_params["filters"]["status"] = filters["status"]

    # Role filter
    if filters.get("role"):
        search_params["filters"]["role"] = filters["role"]

    # Date range filter
    if filters.get("created_after"):
        search_params["filters"]["created_after"] = filters["created_after"]
    if filters.get("created_before"):
        search_params["filters"]["created_before"] = filters["created_before"]

    # Pagination
    search_params["limit"] = filters.get("limit", 20)
    search_params["offset"] = filters.get("offset", 0)

    # Sorting
    search_params["sort_by"] = filters.get("sort_by", "created_at")
    search_params["sort_order"] = filters.get("sort_order", "desc")

    result = search_params
"""
        workflow.update_node("query_builder", {"code": query_code})

        # Configure result formatter
        formatter_code = """
users = input_data.get("users", [])
total = input_data.get("total", 0)
limit = input_data.get("limit", 20)
offset = input_data.get("offset", 0)

# Calculate pagination metadata
total_pages = (total + limit - 1) // limit if limit > 0 else 0
current_page = (offset // limit) + 1 if limit > 0 else 1

# Format user data (remove sensitive fields)
formatted_users = []
for user in users:
    formatted_users.append({
        "id": user["id"],
        "username": user["username"],
        "email": user["email"],
        "status": user.get("status", "active"),
        "created_at": user.get("created_at"),
        "last_login": user.get("last_login"),
        "roles": user.get("roles", [])
    })

result = {
    "success": True,
    "data": formatted_users,
    "pagination": {
        "total": total,
        "limit": limit,
        "offset": offset,
        "total_pages": total_pages,
        "current_page": current_page,
        "has_next": current_page < total_pages,
        "has_prev": current_page > 1
    }
}
"""
        workflow.update_node("result_formatter", {"code": formatter_code})

        return workflow

    def create_advanced_search_workflow(self) -> WorkflowBuilder:
        """Create workflow for advanced search with complex filters"""
        workflow = WorkflowBuilder("advanced_user_search")

        # Add nodes
        workflow.add_node(
            "permission_checker",
            "PermissionCheckNode",
            self.config.NODE_CONFIGS["PermissionCheckNode"],
        )
        workflow.add_node("query_optimizer", "PythonCodeNode")
        workflow.add_node("parallel_searcher", "PythonCodeNode")
        workflow.add_node(
            "user_searcher",
            "UserManagementNode",
            self.config.NODE_CONFIGS["UserManagementNode"],
        )
        workflow.add_node(
            "role_searcher",
            "RoleManagementNode",
            self.config.NODE_CONFIGS["RoleManagementNode"],
        )
        workflow.add_node("result_merger", "PythonCodeNode")
        workflow.add_node("relevance_scorer", "PythonCodeNode")

        # Connect nodes
        workflow.add_connection("input", "permission_checker", "data", "input")
        workflow.add_connection(
            "permission_checker", "query_optimizer", "result", "input"
        )
        workflow.add_connection(
            "query_optimizer", "parallel_searcher", "result", "input"
        )
        workflow.add_connection(
            "parallel_searcher", "user_searcher", "user_query", "input"
        )
        workflow.add_connection(
            "parallel_searcher", "role_searcher", "role_query", "input"
        )
        workflow.add_connection("user_searcher", "result_merger", "result", "users")
        workflow.add_connection("role_searcher", "result_merger", "result", "roles")
        workflow.add_connection("result_merger", "relevance_scorer", "result", "input")
        workflow.add_connection("relevance_scorer", "output", "result", "result")

        # Configure query optimizer
        optimizer_code = """
if not input_data.get("allowed"):
    result = {"success": False, "error": "Permission denied"}
else:
    query = input_data.get("query", {})

    # Optimize search strategy based on query complexity
    has_role_filters = bool(query.get("roles") or query.get("permissions"))
    has_attribute_filters = bool(query.get("attributes"))
    has_activity_filters = bool(query.get("last_login_after") or query.get("last_login_before"))

    # Determine search strategy
    if has_role_filters and (has_attribute_filters or has_activity_filters):
        strategy = "parallel"  # Search users and roles in parallel
    else:
        strategy = "sequential"  # Simple user search

    result = {
        "strategy": strategy,
        "query": query,
        "optimizations": {
            "use_index": True,
            "cache_results": True,
            "batch_size": 100
        }
    }
"""
        workflow.update_node("query_optimizer", {"code": optimizer_code})

        # Configure parallel searcher
        parallel_code = """
strategy = input_data["strategy"]
query = input_data["query"]

if strategy == "parallel":
    # Prepare parallel queries
    result = {
        "user_query": {
            "operation": "search_users",
            "query": query.get("text", ""),
            "filters": {
                k: v for k, v in query.items()
                if k not in ["roles", "permissions", "text"]
            }
        },
        "role_query": {
            "operation": "get_users_by_role",
            "roles": query.get("roles", []),
            "permissions": query.get("permissions", [])
        }
    }
else:
    # Sequential search
    result = {
        "user_query": {
            "operation": "search_users",
            "query": query.get("text", ""),
            "filters": query
        },
        "role_query": {"operation": "noop"}  # No role search needed
    }
"""
        workflow.update_node("parallel_searcher", {"code": parallel_code})

        # Configure result merger
        merger_code = """
users_from_search = input_data.get("users", {}).get("users", [])
users_from_roles = input_data.get("roles", {}).get("users", [])

# Merge and deduplicate users
user_map = {}
for user in users_from_search:
    user_map[user["id"]] = user

for user in users_from_roles:
    if user["id"] in user_map:
        # Merge additional data
        user_map[user["id"]]["matched_by_role"] = True
    else:
        user["matched_by_search"] = False
        user_map[user["id"]] = user

# Convert back to list
merged_users = list(user_map.values())

result = {
    "users": merged_users,
    "total": len(merged_users),
    "search_metadata": {
        "from_text_search": len(users_from_search),
        "from_role_search": len(users_from_roles),
        "total_unique": len(merged_users)
    }
}
"""
        workflow.update_node("result_merger", {"code": merger_code})

        # Configure relevance scorer
        scorer_code = """
import re
from datetime import datetime

users = input_data["users"]
original_query = input_data.get("query", {})
search_text = original_query.get("text", "").lower()

# Score each user based on relevance
scored_users = []
for user in users:
    score = 0.0

    # Text match scoring
    if search_text:
        username_match = search_text in user.get("username", "").lower()
        email_match = search_text in user.get("email", "").lower()

        if username_match:
            score += 2.0  # Higher weight for username match
        if email_match:
            score += 1.5

        # Partial match
        for term in search_text.split():
            if term in user.get("username", "").lower():
                score += 0.5
            if term in user.get("email", "").lower():
                score += 0.3

    # Role match scoring
    if user.get("matched_by_role"):
        score += 1.0

    # Activity scoring (recent activity = higher score)
    last_login = user.get("last_login")
    if last_login:
        days_since_login = (datetime.utcnow() - datetime.fromisoformat(last_login)).days
        if days_since_login < 7:
            score += 0.5
        elif days_since_login < 30:
            score += 0.3

    user["relevance_score"] = score
    scored_users.append(user)

# Sort by relevance score
scored_users.sort(key=lambda x: x["relevance_score"], reverse=True)

result = {
    "success": True,
    "users": scored_users[:input_data.get("limit", 20)],
    "total": len(scored_users),
    "search_metadata": input_data["search_metadata"]
}
"""
        workflow.update_node("relevance_scorer", {"code": scorer_code})

        return workflow

    def create_export_workflow(self) -> WorkflowBuilder:
        """Create workflow for exporting user data"""
        workflow = WorkflowBuilder("user_export")

        # Add nodes
        workflow.add_node(
            "permission_checker",
            "PermissionCheckNode",
            self.config.NODE_CONFIGS["PermissionCheckNode"],
        )
        workflow.add_node(
            "data_collector",
            "UserManagementNode",
            self.config.NODE_CONFIGS["UserManagementNode"],
        )
        workflow.add_node("formatter", "PythonCodeNode")
        workflow.add_node("file_writer", "FileWriterNode")
        workflow.add_node(
            "audit_logger",
            "EnterpriseAuditLogNode",
            self.config.NODE_CONFIGS["EnterpriseAuditLogNode"],
        )

        # Connect nodes
        workflow.add_connection("input", "permission_checker", "data", "input")
        workflow.add_connection(
            "permission_checker", "data_collector", "result", "input"
        )
        workflow.add_connection("data_collector", "formatter", "result", "input")
        workflow.add_connection("formatter", "file_writer", "result", "input")
        workflow.add_connection("file_writer", "audit_logger", "result", "input")
        workflow.add_connection("audit_logger", "output", "result", "result")

        # Configure data collector
        workflow.update_node(
            "data_collector",
            {"operation": "export_users", "filters": "$.filters", "fields": "$.fields"},
        )

        # Configure formatter
        formatter_code = """
import json
import csv
from io import StringIO

users = input_data.get("users", [])
format_type = input_data.get("format", "json")
fields = input_data.get("fields", ["id", "username", "email", "status", "created_at"])

if format_type == "json":
    # JSON format
    output_data = []
    for user in users:
        user_data = {field: user.get(field) for field in fields}
        output_data.append(user_data)

    content = json.dumps(output_data, indent=2)
    filename = "users_export.json"

elif format_type == "csv":
    # CSV format
    output = StringIO()
    writer = csv.DictWriter(output, fieldnames=fields)
    writer.writeheader()

    for user in users:
        row = {field: user.get(field, "") for field in fields}
        writer.writerow(row)

    content = output.getvalue()
    filename = "users_export.csv"

else:
    content = "Unsupported format"
    filename = "error.txt"

result = {
    "content": content,
    "filename": filename,
    "format": format_type,
    "record_count": len(users)
}
"""
        workflow.update_node("formatter", {"code": formatter_code})

        return workflow

    def register_endpoints(self, app):
        """Register search and export endpoints"""

        # Initialize workflows
        search_workflow = self.create_user_search_workflow()
        advanced_workflow = self.create_advanced_search_workflow()
        export_workflow = self.create_export_workflow()

        @app.post("/api/v1/users/search")
        async def search_users(user_id: str, filters: Dict[str, Any]):
            """Search users with filters"""
            result = await self.runtime.execute_async(
                search_workflow, {"user_id": user_id, "filters": filters}
            )
            return result

        @app.post("/api/v1/users/advanced-search")
        async def advanced_search(user_id: str, query: Dict[str, Any]):
            """Advanced user search with complex queries"""
            result = await self.runtime.execute_async(
                advanced_workflow, {"user_id": user_id, "query": query}
            )
            return result

        @app.post("/api/v1/users/export")
        async def export_users(
            user_id: str,
            filters: Optional[Dict[str, Any]] = None,
            format: str = "json",
            fields: Optional[List[str]] = None,
        ):
            """Export user data"""
            result = await self.runtime.execute_async(
                export_workflow,
                {
                    "user_id": user_id,
                    "filters": filters or {},
                    "format": format,
                    "fields": fields,
                },
            )
            return result

        @app.get("/api/v1/users/suggestions")
        async def get_suggestions(user_id: str, query: str, limit: int = 10):
            """Get user suggestions for autocomplete"""
            # Simple implementation using search
            result = await self.runtime.execute_async(
                search_workflow,
                {
                    "user_id": user_id,
                    "filters": {
                        "query": query,
                        "limit": limit,
                        "fields": ["id", "username", "email"],
                    },
                },
            )
            return result
