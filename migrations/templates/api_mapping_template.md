# API Mapping - [Project Name]

Generated: [Date]

## Overview

This document maps existing API endpoints to Kailash SDK workflow implementations. Each endpoint is analyzed and provided with a suggested Kailash implementation pattern.

## API Summary

| Method | Endpoint | Purpose | Priority | Complexity |
|--------|----------|---------|----------|------------|
| GET | /api/example | Example endpoint | High | Low |
| POST | /api/users | Create user | High | Medium |
| [Add all endpoints] | | | | |

**Total Endpoints:** [Count]
**Estimated Migration Effort:** [Hours/Days]

## Detailed API Mapping

### Authentication Endpoints

#### 1. POST /api/auth/login
**Current Implementation:**
- Validates user credentials
- Generates JWT token
- Returns user profile and token

**Request Schema:**
```json
{
  "email": "string",
  "password": "string"
}
```

**Response Schema:**
```json
{
  "token": "string",
  "user": {
    "id": "string",
    "email": "string",
    "name": "string"
  }
}
```

**Kailash Workflow Implementation:**
```python
# Authentication workflow
auth_workflow = Workflow("user_authentication")

# Input validation
input_validator = APIInputNode(
    name="validate_input",
    expected_schema={
        "email": {"type": "string", "required": True},
        "password": {"type": "string", "required": True}
    }
)

# User lookup
user_lookup = DatabaseQueryNode(
    name="find_user",
    query="SELECT * FROM users WHERE email = :email",
    connection_name="main_db"
)

# Password verification
password_verifier = PasswordVerificationNode(
    name="verify_password",
    hash_algorithm="bcrypt"
)

# Token generation
token_generator = JWTGeneratorNode(
    name="generate_token",
    secret_key=config.JWT_SECRET,
    expiration_hours=24
)

# Response formatter
response_formatter = ResponseFormatterNode(
    name="format_response",
    response_schema={
        "token": "string",
        "user": {"id": "string", "email": "string", "name": "string"}
    }
)

# API output
api_output = APIOutputNode(
    name="api_response",
    status_code=200
)

# Connect workflow
auth_workflow.add_nodes([
    input_validator, user_lookup, password_verifier,
    token_generator, response_formatter, api_output
])

auth_workflow.connect(input_validator, user_lookup, mapping={"email": "email"})
auth_workflow.connect(user_lookup, password_verifier, mapping={"password_hash": "stored_hash"})
auth_workflow.connect(input_validator, password_verifier, mapping={"password": "input_password"})
auth_workflow.connect(password_verifier, token_generator)
auth_workflow.connect(token_generator, response_formatter)
auth_workflow.connect(user_lookup, response_formatter, mapping={"user_data": "user"})
auth_workflow.connect(response_formatter, api_output)
```

**Testing Requirements:**
- [ ] Unit test for password verification
- [ ] Integration test for complete flow
- [ ] Test invalid credentials
- [ ] Test missing fields
- [ ] Performance test for concurrent logins

**Migration Notes:**
- Ensure JWT secret is properly configured
- Migrate existing user sessions
- Update frontend to use new endpoint

---

### User Management Endpoints

#### 2. GET /api/users
[Continue with similar detailed mapping for each endpoint]

---

### Data Processing Endpoints

#### 3. POST /api/data/process
[Continue with similar detailed mapping for each endpoint]

---

## Common Patterns

### CRUD Operations Pattern
```python
# Generic CRUD workflow pattern
def create_crud_workflow(resource_name, table_name):
    # CREATE
    create_workflow = Workflow(f"create_{resource_name}")
    # ... implementation

    # READ
    read_workflow = Workflow(f"read_{resource_name}")
    # ... implementation

    # UPDATE
    update_workflow = Workflow(f"update_{resource_name}")
    # ... implementation

    # DELETE
    delete_workflow = Workflow(f"delete_{resource_name}")
    # ... implementation

    return {
        "create": create_workflow,
        "read": read_workflow,
        "update": update_workflow,
        "delete": delete_workflow
    }
```

### File Upload Pattern
```python
# File upload workflow pattern
upload_workflow = Workflow("file_upload")

# File validation
file_validator = FileValidatorNode(
    name="validate_file",
    allowed_types=["pdf", "docx", "xlsx"],
    max_size_mb=10
)

# Virus scan
virus_scanner = VirusScanNode(
    name="scan_file",
    scanner="clamav"
)

# File storage
file_storage = FileStorageNode(
    name="store_file",
    storage_backend="s3",
    bucket_name=config.UPLOAD_BUCKET
)

# Metadata storage
metadata_storage = DatabaseWriterNode(
    name="store_metadata",
    table="file_uploads"
)
```

### Batch Processing Pattern
```python
# Batch processing workflow pattern
batch_workflow = Workflow("batch_processor")

# Batch reader
batch_reader = BatchDataReaderNode(
    name="read_batch",
    batch_size=1000
)

# Parallel processor
parallel_processor = ParallelProcessorNode(
    name="process_items",
    worker_count=4,
    processor_workflow=item_processor_workflow
)

# Result aggregator
result_aggregator = DataAggregatorNode(
    name="aggregate_results",
    aggregation_type="merge"
)
```

## API Compatibility Layer

### Wrapper Implementation
```python
# Maintain backward compatibility during migration
from flask import Flask, request, jsonify
from kailash_sdk import Runtime

app = Flask(__name__)
runtime = Runtime()

@app.route('/api/<path:path>', methods=['GET', 'POST', 'PUT', 'DELETE'])
def api_wrapper(path):
    # Map legacy endpoints to Kailash workflows
    workflow_mapping = {
        "auth/login": "user_authentication",
        "users": "user_management",
        "data/process": "data_processing"
    }

    workflow_name = workflow_mapping.get(path)
    if not workflow_name:
        return jsonify({"error": "Endpoint not found"}), 404

    try:
        workflow = load_workflow(workflow_name)
        result = runtime.execute(workflow, parameters={
            "request_data": request.get_json(),
            "request_method": request.method,
            "request_headers": dict(request.headers),
            "path_params": path
        })

        return jsonify(result.get("response", {})), result.get("status_code", 200)
    except Exception as e:
        return jsonify({"error": str(e)}), 500
```

## Migration Priorities

### Phase 1 - Critical Path (Week 1-2)
1. Authentication endpoints
2. User management CRUD
3. Core business logic endpoints

### Phase 2 - Data Operations (Week 3-4)
1. Data processing endpoints
2. Report generation
3. File upload/download

### Phase 3 - Integration Points (Week 5)
1. External API integrations
2. Webhook handlers
3. Background job endpoints

### Phase 4 - Administrative (Week 6)
1. Admin panel endpoints
2. Monitoring endpoints
3. Configuration endpoints

## Testing Strategy

### Unit Tests
```python
# Example unit test for endpoint
def test_login_endpoint():
    workflow = load_workflow("user_authentication")

    result = runtime.execute(workflow, parameters={
        "request_data": {
            "email": "test@example.com",
            "password": "testpass123"
        }
    })

    assert result["status_code"] == 200
    assert "token" in result["response"]
    assert result["response"]["user"]["email"] == "test@example.com"
```

### Integration Tests
- Test complete request/response cycle
- Verify database state changes
- Check external service interactions

### Performance Tests
- Measure response times
- Test concurrent requests
- Monitor resource usage

## Rollback Plan

### Feature Flags
```python
# Use feature flags for gradual rollout
if feature_flags.is_enabled("use_kailash_auth"):
    return execute_kailash_workflow("authentication")
else:
    return legacy_auth_handler()
```

### Dual Running
- Run both systems in parallel
- Compare results
- Log discrepancies
- Gradual traffic shift

## Success Metrics

- [ ] All endpoints migrated
- [ ] Response times <= legacy system
- [ ] Zero data inconsistencies
- [ ] 100% test coverage
- [ ] API compatibility maintained

## Next Steps

1. Review and prioritize endpoint migrations
2. Set up Kailash development environment
3. Implement first endpoint as proof of concept
4. Create comprehensive test suite
5. Plan phased rollout strategy

---
**Document Version:** 1.0
**Last Updated:** [Date]
**Approved By:** [Names]
