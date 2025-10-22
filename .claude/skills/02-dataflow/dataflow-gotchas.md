---
name: dataflow-gotchas
description: "Common DataFlow mistakes and misunderstandings. Use when DataFlow issues, gotchas, common mistakes DataFlow, troubleshooting DataFlow, or DataFlow problems."
---

# DataFlow Common Gotchas

Common misunderstandings and mistakes when using DataFlow, with solutions.

> **Skill Metadata**
> Category: `dataflow`
> Priority: `HIGH`
> SDK Version: `0.9.25+ / DataFlow 0.6.0`
> Related Skills: [`dataflow-models`](#), [`dataflow-crud-operations`](#), [`dataflow-nexus-integration`](#)
> Related Subagents: `dataflow-specialist` (complex troubleshooting)

## Quick Reference

- **NOT an ORM**: DataFlow is workflow-native, not like SQLAlchemy
- **Primary Key MUST be `id`**: NOT `user_id`, `model_id`, or anything else
- **CreateNode ≠ UpdateNode**: Different parameter patterns (flat vs nested)
- **Template Syntax**: DON'T use `${}` - conflicts with PostgreSQL
- **Connections**: Use connections, NOT template strings
- **Result Access**: `results["node"]["result"]`, not `results["node"]`

## Critical Gotchas

### 0. Empty Dict Truthiness Bug (Fixed in v0.6.2-v0.6.3) ⚠️ CRITICAL

#### The Bug
Python treats empty dict `{}` as falsy, causing incorrect behavior in filter operations.

#### Symptoms (Before Fix)
```python
# This would return ALL records instead of filtered records (v0.6.1 and earlier)
workflow.add_node("UserListNode", "query", {
    "filter": {"status": {"$ne": "inactive"}}
})
# Expected: 2 users (active only)
# Actual (v0.6.1 and earlier): 3 users (ALL records)
```

#### The Fix (v0.6.2+)
✅ **Upgrade to DataFlow v0.6.2 or later**
```bash
pip install --upgrade kailash-dataflow>=0.6.3
```

✅ All filter operators now work correctly:
- $ne (not equal)
- $nin (not in)
- $in (in)
- $not (logical NOT)
- All comparison operators ($gt, $lt, $gte, $lte)

#### Prevention Pattern
When checking if a parameter was provided:
```python
# ❌ WRONG - treats empty dict as "not provided"
if filter_dict:
    process_filter()

# ✅ CORRECT - checks if key exists
if "filter" in kwargs:
    process_filter()
```

#### Root Cause
Two locations had truthiness bugs:
1. **v0.6.2 fix**: ListNode at nodes.py:1810 - `if filter_dict:` → `if "filter" in kwargs:`
2. **v0.6.3 fix**: BulkDeleteNode at bulk_delete.py:177 - `not filter_conditions` → `"filter" not in validated_inputs`

#### Affected Versions
- ❌ v0.5.4 - v0.6.1: Broken
- ✅ v0.6.2+: Filter operators fixed
- ✅ v0.6.3+: BulkDelete safe mode fixed

#### Impact
**High**: All query filtering was broken in v0.6.1 and earlier. Upgrade immediately if using filters.

---

### 0.1. Primary Key MUST Be Named 'id' ⚠️ HIGH IMPACT

```python
# WRONG - Custom primary key names FAIL
@db.model
class User:
    user_id: str  # FAILS - DataFlow requires 'id'
    name: str

# WRONG - Other variations also fail
@db.model
class Agent:
    agent_id: str  # FAILS
    model_id: str  # FAILS
```

**Why**: DataFlow's auto-generated nodes expect `id` as the primary key field name.

**Fix: Use 'id' Exactly**
```python
# CORRECT - Primary key MUST be 'id'
@db.model
class User:
    id: str  # ✅ REQUIRED - must be exactly 'id'
    name: str
```

**Impact**: 10-20 minutes debugging if violated. Use `id` for all models, always.

### 0.1. CreateNode vs UpdateNode Pattern Difference ⚠️ CRITICAL

```python
# WRONG - Applying CreateNode pattern to UpdateNode
workflow.add_node("UserUpdateNode", "update", {
    "db_instance": "my_db",
    "model_name": "User",
    "id": "user_001",  # ❌ Individual fields don't work for UpdateNode
    "name": "Alice",
    "status": "active"
})
# Error: "column user_id does not exist" (misleading!)
```

**Why**: CreateNode and UpdateNode use FUNDAMENTALLY DIFFERENT patterns:
- **CreateNode**: Flat individual fields at top level
- **UpdateNode**: Nested `filter` + `fields` dicts

**Fix: Use Correct Pattern**
```python
# CreateNode: FLAT individual fields
workflow.add_node("UserCreateNode", "create", {
    "db_instance": "my_db",
    "model_name": "User",
    "id": "user_001",  # ✅ Individual fields
    "name": "Alice",
    "email": "alice@example.com"
})

# UpdateNode: NESTED filter + fields
workflow.add_node("UserUpdateNode", "update", {
    "db_instance": "my_db",
    "model_name": "User",
    "filter": {"id": "user_001"},  # ✅ Which records
    "fields": {"name": "Alice Updated"}  # ✅ What to change
    # ⚠️ Do NOT include created_at or updated_at - auto-managed!
})
```

**Impact**: 1-2 hours debugging if violated. Different patterns for different operations.

### 0.2. Auto-Managed Timestamp Fields ⚠️

```python
# WRONG - Including auto-managed fields
workflow.add_node("UserUpdateNode", "update", {
    "filter": {"id": "user_001"},
    "fields": {
        "name": "Alice",
        "updated_at": datetime.now()  # ❌ FAILS - auto-managed
    }
})
# Error: "multiple assignments to same column 'updated_at'"
```

**Why**: DataFlow automatically manages `created_at` and `updated_at` fields.

**Fix: Omit Auto-Managed Fields**
```python
# CORRECT - Omit auto-managed fields
workflow.add_node("UserUpdateNode", "update", {
    "filter": {"id": "user_001"},
    "fields": {
        "name": "Alice"  # ✅ Only your fields
        # created_at, updated_at auto-managed by DataFlow
    }
})
```

**Impact**: 5-10 minutes debugging. Never manually set `created_at` or `updated_at`.

### 1. DataFlow is NOT an ORM

```python
# WRONG - Models are not instantiable
from dataflow import DataFlow
db = DataFlow()

@db.model
class User:
    name: str

user = User(name="John")  # FAILS - not supported by design
user.save()  # FAILS - no save() method
```

**Why**: DataFlow is workflow-native, not object-oriented. Models are schemas, not classes.

**Fix: Use Workflow Nodes**
```python
workflow = WorkflowBuilder()
workflow.add_node("UserCreateNode", "create", {
    "name": "John"  # Correct pattern
})
```

### 2. Template Syntax Conflicts with PostgreSQL

```python
# WRONG - ${} conflicts with PostgreSQL
workflow.add_node("OrderCreateNode", "create", {
    "customer_id": "${create_customer.id}"  # FAILS with PostgreSQL
})
```

**Fix: Use Workflow Connections**
```python
workflow.add_node("OrderCreateNode", "create", {
    "total": 100.0
})
workflow.add_connection("create_customer", "id", "create", "customer_id")
```

### 3. Nexus Integration Blocks Startup

```python
# WRONG - Blocks Nexus for minutes
db = DataFlow()  # Default auto_migrate=True
nexus = Nexus(dataflow_config={"integration": db})
```

**Fix: Critical Configuration**
```python
db = DataFlow(
    auto_migrate=False,
    existing_schema_mode=True
)
nexus = Nexus(dataflow_config={
    "integration": db,
    "auto_discovery": False  # CRITICAL
})
```

### 4. Wrong Result Access Pattern

```python
# WRONG - missing 'result' key
results, run_id = runtime.execute(workflow.build())
user_data = results["create_user"]  # Returns metadata, not data
user_id = user_data["id"]  # FAILS
```

**Fix: Access Through 'result'**
```python
results, run_id = runtime.execute(workflow.build())
user_data = results["create_user"]["result"]  # Correct
user_id = user_data["id"]  # Works
```

### 5. String IDs Forced to Integer (Pre-v0.4.0)

```python
# OLD ISSUE (pre-v0.4.0)
@db.model
class Session:
    id: str  # String IDs were converted to int

workflow.add_node("SessionReadNode", "read", {
    "id": "session-uuid-string"  # Failed - converted to int
})
```

**Fix: Upgrade to v0.4.0+**
```python
# Fixed in v0.4.0+ - string IDs preserved
@db.model
class Session:
    id: str  # Fully supported now

workflow.add_node("SessionReadNode", "read", {
    "id": "session-uuid-string"  # Works perfectly
})
```

### 6. VARCHAR(255) Content Limits (Pre-v0.4.0)

```python
# OLD ISSUE (pre-v0.4.0)
@db.model
class Article:
    content: str  # Was VARCHAR(255) - truncated!

# Long content failed or got truncated
```

**Fix: Automatic in v0.4.0+**
```python
# Fixed in v0.4.0+ - now TEXT type
@db.model
class Article:
    content: str  # Unlimited content - TEXT type
```

### 7. DateTime Serialization Issues (Pre-v0.4.0)

```python
# OLD ISSUE (pre-v0.4.0)
from datetime import datetime

workflow.add_node("OrderCreateNode", "create", {
    "due_date": datetime.now().isoformat()  # String failed validation
})
```

**Fix: Use Native datetime (v0.4.0+)**
```python
from datetime import datetime

workflow.add_node("OrderCreateNode", "create", {
    "due_date": datetime.now()  # Native datetime works
})
```

### 8. Multi-Instance Context Leaks (Pre-v0.4.0)

```python
# OLD ISSUE (pre-v0.4.0)
db_dev = DataFlow("sqlite:///dev.db")
db_prod = DataFlow("postgresql://...")

@db_dev.model
class DevModel:
    name: str

# Model leaked to db_prod instance!
```

**Fix: Fixed in v0.4.0+ (Context Isolation)**
```python
# Fixed in v0.4.0+ - proper isolation
db_dev = DataFlow("sqlite:///dev.db")
db_prod = DataFlow("postgresql://...")

@db_dev.model
class DevModel:
    name: str
# Only in db_dev, not in db_prod
```

## Documentation References

### Primary Sources
- **DataFlow Specialist**: [`.claude/skills/dataflow-specialist.md`](../../dataflow-specialist.md#L28-L72)
- **README**: [`sdk-users/apps/dataflow/README.md`](../../../../sdk-users/apps/dataflow/README.md)
- **DataFlow CLAUDE**: [`sdk-users/apps/dataflow/CLAUDE.md`](../../../../sdk-users/apps/dataflow/CLAUDE.md)

### Related Documentation
- **Troubleshooting**: [`sdk-users/apps/dataflow/docs/production/troubleshooting.md`](../../../../sdk-users/apps/dataflow/docs/production/troubleshooting.md)
- **Nexus Blocking Analysis**: [`sdk-users/apps/dataflow/docs/integration/nexus-blocking-issue-analysis.md`](../../../../sdk-users/apps/dataflow/docs/integration/nexus-blocking-issue-analysis.md)

## Related Patterns

- **For models**: See [`dataflow-models`](#)
- **For result access**: See [`dataflow-result-access`](#)
- **For Nexus integration**: See [`dataflow-nexus-integration`](#)
- **For connections**: See [`param-passing-quick`](#)

## When to Escalate to Subagent

Use `dataflow-specialist` when:
- Complex workflow debugging
- Performance optimization issues
- Migration failures
- Multi-database problems

## Quick Tips

- DataFlow is workflow-native, NOT an ORM
- Use connections, NOT `${}` template syntax
- Enable critical config for Nexus integration
- Access results via `results["node"]["result"]`
- v0.4.0+ fixes: string IDs, TEXT type, datetime, multi-instance

## Version Notes

- **v0.6.3**: BulkDeleteNode safe mode validation fix (truthiness bug)
- **v0.6.2**: ListNode filter operators fix ($ne, $nin, $in, $not - truthiness bug)
- **v0.4.0+**: String ID support, TEXT type, datetime fix, multi-instance isolation
- **v0.9.4+**: Password special character support
- **v0.9.25+**: Threading fixes for Docker

## Keywords for Auto-Trigger

<!-- Trigger Keywords: DataFlow issues, gotchas, common mistakes DataFlow, troubleshooting DataFlow, DataFlow problems, DataFlow errors, not working, DataFlow bugs -->
