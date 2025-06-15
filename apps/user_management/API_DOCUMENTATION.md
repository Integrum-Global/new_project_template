# User Management System - API Documentation

## Overview

The User Management System provides a comprehensive REST API for managing users, teams, permissions, and administrative functions. The API is built using the Kailash SDK middleware for enterprise-grade features.

## Base URLs

- **API Server**: `http://localhost:8000`
- **WebSocket Server**: `ws://localhost:8001`

## Authentication

All API endpoints (except health check) require JWT authentication.

### Request Headers
```
Authorization: Bearer <JWT_TOKEN>
Content-Type: application/json
```

### JWT Token Structure
```json
{
  "sub": "user@company.com",
  "user_type": "user|manager|admin",
  "department": "Engineering",
  "permissions": ["read", "write"],
  "roles": ["developer"],
  "exp": 1234567890
}
```

## API Endpoints

### System Endpoints

#### Health Check
```http
GET /health
```

**Response:**
```json
{
  "status": "healthy",
  "timestamp": "2024-01-15T10:30:00Z",
  "service": "user-management-api",
  "version": "1.0.0"
}
```

#### Metrics
```http
GET /metrics
```

**Response:**
```json
{
  "active_users": 150,
  "total_requests": 10000,
  "error_rate": 0.01,
  "average_response_time": 45.5
}
```

### User Workflow Endpoints

#### 1. Profile Setup
```http
POST /api/v1/user/profile/setup
```

**Request Body:**
```json
{
  "first_name": "John",
  "last_name": "Doe",
  "email": "john.doe@company.com",
  "phone": "+1234567890",
  "department": "Engineering",
  "role": "Developer",
  "preferences": {
    "theme": "dark",
    "notifications": true
  }
}
```

**Response:**
```json
{
  "success": true,
  "workflow_id": "profile_setup",
  "execution_id": "exec_1234567890",
  "results": {
    "profile_id": "PROF_20240115_103000",
    "status": "active",
    "completion_steps": ["validation", "creation", "notification"]
  },
  "timestamp": "2024-01-15T10:30:00Z"
}
```

#### 2. Access Request
```http
POST /api/v1/user/access/request
```

**Request Body:**
```json
{
  "resource_type": "production_database",
  "access_level": "read",
  "justification": "Need to debug production issue",
  "duration_days": 7
}
```

**Response:**
```json
{
  "success": true,
  "workflow_id": "access_request",
  "execution_id": "exec_1234567890",
  "results": {
    "request_id": "REQ-12345",
    "status": "pending_approval",
    "approvers": ["manager@company.com"],
    "estimated_response": "24 hours"
  }
}
```

#### 3. MFA Setup
```http
POST /api/v1/user/auth/mfa/setup
```

**Request Body:**
```json
{
  "method": "totp",
  "phone_number": null,
  "backup_codes_count": 8
}
```

**Response:**
```json
{
  "success": true,
  "workflow_id": "mfa_setup",
  "execution_id": "exec_1234567890",
  "results": {
    "qr_code": "data:image/png;base64,...",
    "secret": "XXXX-XXXX-XXXX-XXXX",
    "backup_codes": ["code1", "code2", "..."],
    "verification_required": true
  }
}
```

#### 4. Privacy Settings
```http
POST /api/v1/user/privacy/settings
```

**Request Body:**
```json
{
  "data_sharing": false,
  "marketing_emails": false,
  "analytics_tracking": true,
  "profile_visibility": "team"
}
```

#### 5. Support Ticket
```http
POST /api/v1/user/support/ticket
```

**Request Body:**
```json
{
  "category": "technical",
  "priority": "high",
  "subject": "Cannot access dashboard",
  "description": "Getting 403 error when accessing dashboard",
  "attachments": ["screenshot1.png"]
}
```

### Manager Workflow Endpoints

#### 1. Team Setup
```http
POST /api/v1/manager/team/setup
```
**Requires:** Manager or Admin role

**Request Body:**
```json
{
  "team_name": "Backend Development",
  "team_description": "Core backend services team",
  "team_type": "development",
  "initial_members": ["john.doe@company.com", "jane.smith@company.com"],
  "team_goals": ["Improve API performance", "Implement new features"]
}
```

#### 2. Team Member Management
```http
POST /api/v1/manager/team/members
```

**Request Body:**
```json
{
  "action": "add",
  "user_email": "new.member@company.com",
  "role": "developer",
  "permissions": ["read", "write"]
}
```

**Actions:** `add`, `remove`, `update`

#### 3. Permission Updates
```http
POST /api/v1/manager/permissions/update
```

**Request Body:**
```json
{
  "user_email": "john.doe@company.com",
  "permissions_to_add": ["deploy", "admin_read"],
  "permissions_to_remove": ["delete"],
  "roles_to_assign": ["senior_developer"]
}
```

#### 4. Report Generation
```http
POST /api/v1/manager/reports/generate
```

**Request Body:**
```json
{
  "report_type": "team_performance",
  "period": "monthly",
  "metrics": ["productivity", "goals", "training"],
  "format": "json",
  "include_trends": true
}
```

**Report Types:**
- `team_performance`
- `activity_monitoring`
- Custom report types

#### 5. Approval Processing
```http
POST /api/v1/manager/approvals/process
```

**Request Body:**
```json
{
  "request_id": "REQ-12345",
  "action": "approve",
  "comments": "Approved for 7 days",
  "conditions": ["read_only", "audit_enabled"],
  "delegate_to": null
}
```

**Actions:** `approve`, `reject`, `delegate`

### Admin Workflow Endpoints

#### 1. Tenant Onboarding
```http
POST /api/v1/admin/tenant/onboard
```
**Requires:** Admin role

**Request Body:**
```json
{
  "company_name": "Tech Startup Inc",
  "company_domain": "techstartup.com",
  "admin_email": "admin@techstartup.com",
  "subscription_plan": "enterprise",
  "initial_user_count": 50,
  "features": ["sso", "advanced_analytics", "api_access"]
}
```

#### 2. Bulk User Operations
```http
POST /api/v1/admin/users/bulk
```

**Request Body:**
```json
{
  "action": "create",
  "user_data": [
    {
      "email": "user1@company.com",
      "first_name": "User",
      "last_name": "One",
      "role": "developer"
    }
  ],
  "send_notifications": true
}
```

**Actions:** `create`, `update`, `disable`, `delete`

#### 3. Security Policy Updates
```http
POST /api/v1/admin/security/policy
```

**Request Body:**
```json
{
  "policy_type": "password_policy",
  "enabled": true,
  "configuration": {
    "min_length": 12,
    "require_uppercase": true,
    "require_numbers": true,
    "require_special": true,
    "expiry_days": 90
  },
  "apply_to": ["all_users"]
}
```

#### 4. Backup Creation
```http
POST /api/v1/admin/backup/create
```

**Request Body:**
```json
{
  "backup_type": "full",
  "include_files": true,
  "include_database": true,
  "encryption_enabled": true,
  "retention_days": 30
}
```

**Backup Types:** `full`, `incremental`, `selective`

## WebSocket API

### Connection
```javascript
const ws = new WebSocket('ws://localhost:8001/ws?token=<JWT_TOKEN>');
```

### Message Types

#### Client to Server

**Subscribe to Channel:**
```json
{
  "type": "subscribe",
  "channel": "team_updates"
}
```

**Send Notification:**
```json
{
  "type": "notification",
  "target_user": "user@company.com",
  "notification": {
    "title": "New Task Assigned",
    "message": "You have been assigned a new task",
    "priority": "medium"
  }
}
```

**Broadcast Activity:**
```json
{
  "type": "activity",
  "activity": {
    "action": "file_uploaded",
    "resource": "project_docs/design.pdf"
  }
}
```

#### Server to Client

**Connection Confirmation:**
```json
{
  "type": "connection",
  "status": "connected",
  "message": "Welcome to User Management real-time system",
  "timestamp": "2024-01-15T10:30:00Z",
  "session_id": "ws_session_1234567890"
}
```

**Notification:**
```json
{
  "type": "notification",
  "from_user": "manager@company.com",
  "notification": {
    "title": "Access Request Approved",
    "message": "Your access request has been approved",
    "data": {
      "request_id": "REQ-12345",
      "expires_at": "2024-01-22T10:30:00Z"
    }
  },
  "timestamp": "2024-01-15T10:30:00Z"
}
```

**Heartbeat:**
```json
{
  "type": "heartbeat",
  "server_time": "2024-01-15T10:30:00Z",
  "online_users": 42
}
```

## Error Responses

### Standard Error Format
```json
{
  "success": false,
  "workflow_id": "access_request",
  "execution_id": "exec_1234567890",
  "error": "Insufficient permissions to access this resource",
  "timestamp": "2024-01-15T10:30:00Z"
}
```

### HTTP Status Codes
- `200` - Success
- `400` - Bad Request (validation errors)
- `401` - Unauthorized (invalid/missing token)
- `403` - Forbidden (insufficient permissions)
- `404` - Not Found
- `429` - Too Many Requests (rate limited)
- `500` - Internal Server Error

## Rate Limiting

Default rate limits:
- **User endpoints**: 100 requests per minute
- **Manager endpoints**: 200 requests per minute
- **Admin endpoints**: 500 requests per minute
- **WebSocket messages**: 10 per second

## Best Practices

### 1. Authentication
- Store JWT tokens securely
- Refresh tokens before expiration
- Use HTTPS in production

### 2. Error Handling
- Always check the `success` field in responses
- Implement exponential backoff for retries
- Log error details for debugging

### 3. WebSocket Usage
- Implement reconnection logic
- Handle connection drops gracefully
- Respond to heartbeats to maintain connection

### 4. Performance
- Use pagination for list endpoints
- Cache frequently accessed data
- Batch operations when possible

## Testing

### Using cURL

**Health Check:**
```bash
curl http://localhost:8000/health
```

**Authenticated Request:**
```bash
curl -X POST http://localhost:8000/api/v1/user/profile/setup \
  -H "Authorization: Bearer <TOKEN>" \
  -H "Content-Type: application/json" \
  -d '{"first_name":"John","last_name":"Doe","email":"john.doe@company.com","department":"Engineering","role":"Developer"}'
```

### Using the Test Script
```bash
python test_api.py
```

## SDK Integration

The API is built using Kailash SDK middleware, providing:
- Automatic request validation
- Built-in authentication and authorization
- Performance monitoring and metrics
- Real-time WebSocket support
- Database session management
- Audit logging

## Support

For API support:
- Check workflow execution logs
- Monitor WebSocket connection status
- Review error messages and codes
- Contact system administrators for access issues
