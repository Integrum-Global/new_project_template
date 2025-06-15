# Enterprise User Management API Reference

## 🌐 API Overview

The Kailash Enterprise User Management API provides comprehensive REST endpoints for managing users, authentication, permissions, and compliance in enterprise environments. The API is built using Kailash middleware patterns and exceeds Django Admin capabilities.

### Base URL
```
Production: https://api.company.com/user-management
Development: http://localhost:8000
```

### Authentication
All API endpoints require authentication. Supported methods:
- **Bearer Token**: `Authorization: Bearer <jwt_token>`
- **API Key**: `X-API-Key: <api_key>`
- **Session Cookie**: `sessionid=<session_id>`

### Response Format
```json
{
  "success": true,
  "data": { /* response data */ },
  "metadata": {
    "timestamp": "2024-01-15T10:30:00Z",
    "execution_time_ms": 45,
    "request_id": "req_123456"
  },
  "errors": [] // only present if success: false
}
```

---

## 🔐 Authentication Endpoints

### POST /api/auth/sso/{provider}
Initiate SSO authentication with specified provider.

**Parameters:**
- `provider` (path): SSO provider (`saml`, `azure`, `google`, `okta`, `auth0`)

**Request Body:**
```json
{
  "redirect_uri": "https://app.company.com/auth/callback",
  "state": "optional_state_parameter",
  "scope": "openid profile email" // OAuth2/OIDC only
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "auth_url": "https://provider.com/auth?client_id=...",
    "state": "csrf_protection_token",
    "provider": "azure",
    "expires_in": 300
  }
}
```

**Supported Providers:**

#### SAML 2.0
```json
{
  "provider": "saml",
  "redirect_uri": "https://app.company.com/saml/acs"
}
```

#### Azure AD
```json
{
  "provider": "azure", 
  "redirect_uri": "https://app.company.com/auth/azure/callback",
  "scope": "openid profile email User.Read"
}
```

#### Google Workspace
```json
{
  "provider": "google",
  "redirect_uri": "https://app.company.com/auth/google/callback",
  "scope": "openid profile email"
}
```

#### Okta
```json
{
  "provider": "okta",
  "redirect_uri": "https://app.company.com/auth/okta/callback",
  "scope": "openid profile email groups"
}
```

### POST /api/auth/callback
Handle authentication callback from SSO provider.

**Request Body:**
```json
{
  "provider": "azure",
  "code": "authorization_code_from_provider",
  "state": "csrf_protection_token",
  "session_state": "optional_session_state"
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "authenticated": true,
    "user_id": "user@company.com",
    "session_id": "sess_123456789",
    "access_token": "jwt_access_token",
    "refresh_token": "jwt_refresh_token",
    "expires_in": 3600,
    "user_info": {
      "email": "user@company.com",
      "first_name": "John",
      "last_name": "Doe",
      "groups": ["engineers", "managers"],
      "department": "Engineering"
    },
    "auth_method": "azure",
    "risk_score": 0.2,
    "additional_factors_required": []
  }
}
```

### POST /api/auth/mfa/challenge
Request MFA challenge for user.

**Request Body:**
```json
{
  "user_id": "user@company.com",
  "method": "totp", // totp, sms, email, webauthn
  "phone_number": "+1234567890" // required for SMS
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "challenge_id": "challenge_123456",
    "method": "totp",
    "expires_in": 300,
    "qr_code": "data:image/png;base64,..." // for TOTP setup
  }
}
```

### POST /api/auth/mfa/verify
Verify MFA challenge response.

**Request Body:**
```json
{
  "challenge_id": "challenge_123456",
  "code": "123456",
  "remember_device": true
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "verified": true,
    "session_id": "sess_123456789",
    "device_id": "device_123456",
    "trust_expires": "2024-02-15T10:30:00Z"
  }
}
```

### POST /api/auth/passwordless/challenge
Initiate passwordless authentication challenge.

**Request Body:**
```json
{
  "user_id": "user@company.com",
  "method": "webauthn"
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "challenge": "base64_encoded_challenge",
    "timeout": 60000,
    "user_verification": "required",
    "allowed_credentials": [
      {
        "id": "credential_id_1",
        "type": "public-key"
      }
    ]
  }
}
```

### POST /api/auth/passwordless/verify
Verify passwordless authentication response.

**Request Body:**
```json
{
  "user_id": "user@company.com",
  "credential_response": {
    "id": "credential_id",
    "rawId": "base64_raw_id",
    "response": {
      "authenticatorData": "base64_auth_data",
      "signature": "base64_signature",
      "clientDataJSON": "base64_client_data"
    }
  }
}
```

### POST /api/auth/logout
Logout user and invalidate session.

**Request Body:**
```json
{
  "session_id": "sess_123456789",
  "logout_all_sessions": false
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "logged_out": true,
    "sessions_terminated": 1
  }
}
```

---

## 👥 User Management Endpoints

### GET /api/users
List users with advanced filtering and pagination.

**Query Parameters:**
- `page` (int): Page number (default: 1)
- `limit` (int): Items per page (default: 50, max: 200)
- `search` (string): Search term for email, name, department
- `department` (string): Filter by department
- `status` (string): Filter by status (`active`, `inactive`, `suspended`)
- `sso_enabled` (bool): Filter by SSO status
- `mfa_enabled` (bool): Filter by MFA status
- `created_after` (date): Filter by creation date
- `sort` (string): Sort field (`email`, `created_at`, `last_login`)
- `order` (string): Sort order (`asc`, `desc`)

**Response:**
```json
{
  "success": true,
  "data": {
    "users": [
      {
        "user_id": "user123",
        "email": "john.doe@company.com",
        "first_name": "John",
        "last_name": "Doe",
        "department": "Engineering",
        "job_title": "Senior Developer",
        "status": "active",
        "sso_enabled": true,
        "mfa_enabled": true,
        "last_login": "2024-01-15T09:30:00Z",
        "created_at": "2024-01-01T10:00:00Z",
        "groups": ["engineers", "seniors"],
        "permissions": ["read", "write"],
        "session_count": 2
      }
    ],
    "pagination": {
      "page": 1,
      "limit": 50,
      "total": 1250,
      "pages": 25,
      "has_next": true,
      "has_prev": false
    }
  }
}
```

### POST /api/users
Create new user with enterprise provisioning.

**Request Body:**
```json
{
  "email": "jane.smith@company.com",
  "first_name": "Jane",
  "last_name": "Smith",
  "department": "Marketing",
  "job_title": "Marketing Manager",
  "manager_email": "manager@company.com",
  "groups": ["marketing", "managers"],
  "sso_providers": ["azure", "google"],
  "mfa_required": true,
  "temporary_password": false,
  "send_welcome_email": true,
  "custom_attributes": {
    "employee_id": "EMP001234",
    "cost_center": "MARKETING_001"
  }
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "user_id": "user124",
    "email": "jane.smith@company.com",
    "status": "active",
    "sso_setup": {
      "azure": "configured",
      "google": "configured"
    },
    "mfa_setup": {
      "status": "pending",
      "qr_code": "data:image/png;base64,..."
    },
    "welcome_email_sent": true,
    "execution_id": "exec_123456"
  }
}
```

### GET /api/users/{user_id}
Get detailed user information.

**Response:**
```json
{
  "success": true,
  "data": {
    "user_id": "user123",
    "email": "john.doe@company.com",
    "first_name": "John",
    "last_name": "Doe",
    "department": "Engineering",
    "job_title": "Senior Developer",
    "status": "active",
    "created_at": "2024-01-01T10:00:00Z",
    "last_login": "2024-01-15T09:30:00Z",
    "login_count": 142,
    "sso_providers": ["azure", "google"],
    "mfa_methods": ["totp", "sms"],
    "groups": ["engineers", "seniors"],
    "permissions": ["read", "write", "deploy"],
    "sessions": [
      {
        "session_id": "sess_123",
        "device_type": "desktop",
        "os": "Windows",
        "browser": "Chrome",
        "ip_address": "192.168.1.100",
        "created_at": "2024-01-15T09:30:00Z",
        "last_activity": "2024-01-15T10:15:00Z"
      }
    ],
    "security_events": [
      {
        "event_type": "login_success",
        "timestamp": "2024-01-15T09:30:00Z",
        "ip_address": "192.168.1.100",
        "risk_score": 0.1
      }
    ]
  }
}
```

### PATCH /api/users/{user_id}
Update user information.

**Request Body:**
```json
{
  "first_name": "John",
  "last_name": "Smith", 
  "department": "Platform Engineering",
  "job_title": "Principal Engineer",
  "groups": ["engineers", "principals", "architects"],
  "status": "active"
}
```

### DELETE /api/users/{user_id}
Deactivate or delete user (GDPR compliant).

**Query Parameters:**
- `action` (string): `deactivate` or `delete` (default: deactivate)
- `gdpr_request` (bool): Mark as GDPR deletion request

**Response:**
```json
{
  "success": true,
  "data": {
    "user_id": "user123",
    "action": "deactivated",
    "data_retention": {
      "audit_logs_retained": true,
      "personal_data_removed": false,
      "retention_period": "7 years"
    },
    "execution_id": "exec_789456"
  }
}
```

### POST /api/users/{user_id}/impersonate
Start user impersonation session (admin only).

**Request Body:**
```json
{
  "reason": "Customer support assistance",
  "duration_minutes": 30
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "impersonation_token": "imp_token_123456",
    "expires_at": "2024-01-15T11:00:00Z",
    "audit_log_id": "audit_456789"
  }
}
```

---

## 🔑 Permissions & Roles Endpoints

### GET /api/roles
List all roles and permissions.

**Response:**
```json
{
  "success": true,
  "data": {
    "roles": [
      {
        "role_id": "role_123",
        "name": "Engineering Manager",
        "description": "Manages engineering teams",
        "permissions": [
          "users.read",
          "users.write", 
          "projects.manage",
          "deployments.approve"
        ],
        "user_count": 15,
        "created_at": "2024-01-01T10:00:00Z"
      }
    ]
  }
}
```

### POST /api/roles
Create new role.

**Request Body:**
```json
{
  "name": "Senior Developer",
  "description": "Senior software developer role",
  "permissions": [
    "code.read",
    "code.write",
    "deployments.staging",
    "monitoring.read"
  ],
  "inherits_from": ["developer"]
}
```

### GET /api/permissions
List all available permissions.

**Response:**
```json
{
  "success": true,
  "data": {
    "permissions": [
      {
        "permission_id": "users.read",
        "name": "Read Users",
        "description": "View user information",
        "category": "user_management",
        "resource": "users",
        "action": "read"
      }
    ],
    "categories": [
      "user_management",
      "system_admin", 
      "security",
      "compliance"
    ]
  }
}
```

### POST /api/users/{user_id}/permissions
Assign permissions to user.

**Request Body:**
```json
{
  "permissions": ["users.read", "users.write"],
  "action": "add", // add, remove, replace
  "expires_at": "2024-12-31T23:59:59Z" // optional
}
```

### GET /api/users/{user_id}/effective-permissions
Get user's effective permissions (from roles and direct assignments).

**Response:**
```json
{
  "success": true,
  "data": {
    "user_id": "user123",
    "effective_permissions": [
      {
        "permission": "users.read",
        "source": "role",
        "role_name": "Manager",
        "granted_at": "2024-01-01T10:00:00Z"
      },
      {
        "permission": "admin.system",
        "source": "direct",
        "granted_at": "2024-01-15T10:00:00Z",
        "expires_at": "2024-12-31T23:59:59Z"
      }
    ]
  }
}
```

---

## 🔒 Security & Risk Assessment Endpoints

### POST /api/security/risk-assessment
Perform risk assessment for authentication attempt.

**Request Body:**
```json
{
  "user_id": "user123",
  "ip_address": "203.0.113.25",
  "device_info": {
    "user_agent": "Mozilla/5.0...",
    "device_type": "mobile",
    "os": "iOS",
    "browser": "Safari"
  },
  "location": {
    "country": "US",
    "city": "San Francisco",
    "timezone": "PST"
  },
  "timestamp": "2024-01-15T10:30:00Z"
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "risk_score": 0.65,
    "risk_level": "medium",
    "factors": [
      "unknown_device",
      "external_ip", 
      "unusual_hour"
    ],
    "recommendations": [
      "require_mfa",
      "additional_verification"
    ],
    "ai_analysis": {
      "confidence": 0.87,
      "reasoning": "User typically logs in from corporate network during business hours"
    }
  }
}
```

### GET /api/security/threats
Get recent security threats and alerts.

**Query Parameters:**
- `severity` (string): Filter by severity (`low`, `medium`, `high`, `critical`)
- `type` (string): Filter by threat type
- `since` (datetime): Filter by time period

**Response:**
```json
{
  "success": true,
  "data": {
    "threats": [
      {
        "threat_id": "threat_123",
        "type": "brute_force",
        "severity": "high",
        "source_ip": "192.0.2.100",
        "target_user": "admin@company.com",
        "detected_at": "2024-01-15T10:25:00Z",
        "status": "mitigated",
        "actions_taken": ["ip_blocked", "user_notified"],
        "confidence": 0.95
      }
    ]
  }
}
```

### POST /api/security/block-ip
Block suspicious IP address.

**Request Body:**
```json
{
  "ip_address": "192.0.2.100",
  "reason": "Brute force attack detected",
  "duration_hours": 24,
  "notify_admins": true
}
```

### GET /api/security/sessions
Monitor active sessions across the platform.

**Query Parameters:**
- `suspicious_only` (bool): Show only suspicious sessions
- `user_id` (string): Filter by specific user

**Response:**
```json
{
  "success": true,
  "data": {
    "active_sessions": 1247,
    "suspicious_sessions": 3,
    "sessions": [
      {
        "session_id": "sess_123",
        "user_id": "user123",
        "ip_address": "192.168.1.100",
        "device_info": {
          "device_type": "desktop",
          "os": "Windows",
          "browser": "Chrome"
        },
        "risk_score": 0.1,
        "created_at": "2024-01-15T09:30:00Z",
        "last_activity": "2024-01-15T10:30:00Z",
        "suspicious_flags": []
      }
    ]
  }
}
```

---

## 📊 Analytics & Reporting Endpoints

### GET /api/analytics/dashboard
Get admin dashboard statistics.

**Response:**
```json
{
  "success": true,
  "data": {
    "summary": {
      "total_users": 1250,
      "active_users_24h": 892,
      "new_users_7d": 25,
      "sso_adoption": 0.87,
      "mfa_adoption": 0.76
    },
    "authentication": {
      "total_attempts_24h": 3456,
      "successful_logins": 3201,
      "failed_attempts": 255,
      "blocked_attempts": 12,
      "sso_logins": 2789,
      "mfa_challenges": 456
    },
    "security": {
      "threats_detected_24h": 5,
      "high_risk_logins": 23,
      "suspicious_sessions": 3,
      "devices_blocked": 2
    },
    "performance": {
      "avg_login_time_ms": 245,
      "avg_api_response_ms": 89,
      "uptime_percentage": 99.98
    }
  }
}
```

### GET /api/analytics/users/activity
Get user activity analytics.

**Query Parameters:**
- `period` (string): Time period (`24h`, `7d`, `30d`, `90d`)
- `group_by` (string): Group by (`hour`, `day`, `week`)

**Response:**
```json
{
  "success": true,
  "data": {
    "period": "7d",
    "activity": [
      {
        "date": "2024-01-15",
        "logins": 456,
        "unique_users": 234,
        "new_users": 5,
        "sso_logins": 389,
        "mfa_challenges": 67
      }
    ],
    "trends": {
      "login_growth": 0.15,
      "sso_adoption_growth": 0.08,
      "mfa_adoption_growth": 0.12
    }
  }
}
```

### GET /api/analytics/security/report
Generate security analytics report.

**Query Parameters:**
- `period` (string): Report period (`weekly`, `monthly`, `quarterly`)
- `format` (string): Output format (`json`, `pdf`, `csv`)

**Response:**
```json
{
  "success": true,
  "data": {
    "report_id": "sec_report_123",
    "period": "monthly",
    "generated_at": "2024-01-15T10:30:00Z",
    "summary": {
      "total_threats": 25,
      "critical_threats": 2,
      "blocked_ips": 15,
      "compromised_accounts": 0,
      "avg_response_time_minutes": 2.5
    },
    "threat_breakdown": {
      "brute_force": 12,
      "credential_stuffing": 8,
      "suspicious_login": 5
    },
    "download_url": "https://api.company.com/reports/download/sec_report_123"
  }
}
```

---

## 🏛️ Compliance Endpoints

### GET /api/compliance/gdpr/users/{user_id}/export
Export user data for GDPR compliance.

**Query Parameters:**
- `format` (string): Export format (`json`, `xml`, `csv`)
- `include_audit` (bool): Include audit log data

**Response:**
```json
{
  "success": true,
  "data": {
    "export_id": "export_123456",
    "user_id": "user123",
    "generated_at": "2024-01-15T10:30:00Z",
    "format": "json",
    "size_bytes": 15672,
    "download_url": "https://api.company.com/exports/download/export_123456",
    "expires_at": "2024-01-22T10:30:00Z",
    "data_categories": [
      "profile_information",
      "authentication_history",
      "session_data",
      "permissions"
    ]
  }
}
```

### POST /api/compliance/gdpr/users/{user_id}/delete
Process GDPR data deletion request.

**Request Body:**
```json
{
  "request_type": "erasure",
  "legal_basis": "Article 17 - Right to erasure",
  "retain_audit_logs": true,
  "notify_user": true,
  "verification_code": "user_provided_code"
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "deletion_id": "del_123456",
    "user_id": "user123",
    "status": "processing",
    "estimated_completion": "2024-01-16T10:30:00Z",
    "data_to_delete": [
      "profile_information",
      "session_data", 
      "authentication_history"
    ],
    "data_to_retain": [
      "audit_logs",
      "legal_compliance_records"
    ]
  }
}
```

### GET /api/compliance/audit-logs
Get comprehensive audit logs.

**Query Parameters:**
- `user_id` (string): Filter by user
- `action` (string): Filter by action type
- `start_date` (datetime): Start date filter
- `end_date` (datetime): End date filter
- `severity` (string): Filter by severity
- `page` (int): Page number
- `limit` (int): Items per page

**Response:**
```json
{
  "success": true,
  "data": {
    "audit_logs": [
      {
        "log_id": "audit_123456",
        "timestamp": "2024-01-15T10:30:00Z",
        "user_id": "user123",
        "action": "user_login",
        "resource": "authentication_system",
        "ip_address": "192.168.1.100",
        "user_agent": "Mozilla/5.0...",
        "result": "success",
        "risk_score": 0.1,
        "details": {
          "auth_method": "sso",
          "provider": "azure",
          "session_id": "sess_123"
        }
      }
    ],
    "pagination": {
      "page": 1,
      "limit": 50,
      "total": 15672
    }
  }
}
```

### GET /api/compliance/retention-policies
Get data retention policies.

**Response:**
```json
{
  "success": true,
  "data": {
    "policies": [
      {
        "policy_id": "policy_123",
        "name": "User Data Retention",
        "data_type": "user_profiles",
        "retention_period": "7 years",
        "legal_basis": "Employment records requirement",
        "auto_delete": false,
        "archive_before_delete": true,
        "last_applied": "2024-01-15T02:00:00Z"
      }
    ]
  }
}
```

---

## 📡 WebSocket Real-time Events

### WebSocket Connection
```javascript
const ws = new WebSocket('wss://api.company.com/ws/admin');
```

### Event Types

#### User Events
```json
{
  "type": "user_created",
  "timestamp": "2024-01-15T10:30:00Z",
  "data": {
    "user_id": "user124",
    "email": "new.user@company.com",
    "department": "Engineering"
  }
}
```

#### Authentication Events  
```json
{
  "type": "authentication_success",
  "timestamp": "2024-01-15T10:30:00Z",
  "data": {
    "user_id": "user123",
    "auth_method": "sso",
    "provider": "azure",
    "risk_score": 0.2,
    "ip_address": "192.168.1.100"
  }
}
```

#### Security Events
```json
{
  "type": "threat_detected",
  "timestamp": "2024-01-15T10:30:00Z",
  "data": {
    "threat_type": "brute_force",
    "severity": "high",
    "source_ip": "192.0.2.100",
    "target_user": "admin@company.com",
    "actions_taken": ["ip_blocked"]
  }
}
```

#### System Events
```json
{
  "type": "system_alert",
  "timestamp": "2024-01-15T10:30:00Z", 
  "data": {
    "alert_type": "high_cpu_usage",
    "severity": "warning",
    "metric_value": 85,
    "threshold": 80
  }
}
```

---

## 🚀 Advanced Features

### Batch Operations

#### POST /api/users/batch
Perform batch operations on multiple users.

**Request Body:**
```json
{
  "operation": "update", // create, update, delete, activate, deactivate
  "users": [
    {
      "user_id": "user123", 
      "data": {"department": "Platform Engineering"}
    },
    {
      "user_id": "user124",
      "data": {"status": "inactive"}
    }
  ],
  "options": {
    "send_notifications": true,
    "validate_permissions": true
  }
}
```

### Workflow Integration

#### POST /api/workflows/user-onboarding
Trigger user onboarding workflow.

**Request Body:**
```json
{
  "template": "enterprise_user_onboarding",
  "inputs": {
    "user_data": {
      "email": "new.hire@company.com",
      "department": "Engineering",
      "manager": "manager@company.com"
    },
    "provisioning_options": {
      "sso_providers": ["azure", "google"],
      "default_groups": ["employees", "engineers"],
      "laptop_request": true,
      "software_licenses": ["jetbrains", "office365"]
    }
  }
}
```

### Custom Attributes

#### GET /api/users/{user_id}/attributes
Get user custom attributes.

#### POST /api/users/{user_id}/attributes
Set user custom attributes.

**Request Body:**
```json
{
  "attributes": {
    "employee_id": "EMP001234",
    "cost_center": "ENGINEERING_001", 
    "clearance_level": "SECRET",
    "emergency_contact": "+1234567890"
  }
}
```

---

## 🔧 Developer Tools

### API Testing

#### GET /api/health
Health check endpoint.

**Response:**
```json
{
  "status": "healthy",
  "timestamp": "2024-01-15T10:30:00Z",
  "version": "1.0.0",
  "components": {
    "database": "healthy",
    "redis": "healthy", 
    "sso_providers": "healthy",
    "ai_services": "healthy"
  },
  "performance": {
    "avg_response_time_ms": 45,
    "requests_per_second": 1250
  }
}
```

#### GET /api/debug/info
Debug information (admin only).

**Response:**
```json
{
  "environment": "production",
  "build_version": "1.0.0-abc123",
  "deployment_time": "2024-01-15T08:00:00Z",
  "active_sessions": 1247,
  "memory_usage": "512MB",
  "database_connections": 15
}
```

### Rate Limiting

All endpoints are rate limited:
- **Authentication**: 5 requests per minute per IP
- **User Operations**: 100 requests per minute per user
- **Admin Operations**: 200 requests per minute per admin
- **Reporting**: 10 requests per minute per user

Rate limit headers:
```
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 95
X-RateLimit-Reset: 1642267800
```

### Error Codes

| Code | Description |
|------|-------------|
| 400 | Bad Request - Invalid input data |
| 401 | Unauthorized - Authentication required |
| 403 | Forbidden - Insufficient permissions |
| 404 | Not Found - Resource not found |
| 409 | Conflict - Resource already exists |
| 422 | Unprocessable Entity - Validation error |
| 429 | Too Many Requests - Rate limit exceeded |
| 500 | Internal Server Error - Server error |
| 502 | Bad Gateway - Upstream service error |
| 503 | Service Unavailable - Maintenance mode |

### Error Response Format
```json
{
  "success": false,
  "errors": [
    {
      "code": "INVALID_EMAIL",
      "message": "Email address is not valid",
      "field": "email",
      "value": "invalid-email"
    }
  ],
  "metadata": {
    "request_id": "req_123456",
    "timestamp": "2024-01-15T10:30:00Z"
  }
}
```

---

## 📚 SDK Integration

### Python SDK Example
```python
from kailash_user_management import UserManagementClient

client = UserManagementClient(
    base_url="https://api.company.com",
    api_key="your_api_key"
)

# Create user
user = await client.users.create({
    "email": "new.user@company.com",
    "first_name": "Jane",
    "last_name": "Doe",
    "department": "Engineering"
})

# Setup SSO
sso_url = await client.auth.initiate_sso("azure", 
                                        redirect_uri="https://app.company.com/callback")

# Real-time events
async def handle_events(event):
    if event.type == "user_created":
        print(f"New user: {event.data.email}")

await client.events.subscribe(handle_events)
```

### JavaScript SDK Example
```javascript
import { UserManagementClient } from '@kailash/user-management';

const client = new UserManagementClient({
  baseUrl: 'https://api.company.com',
  apiKey: 'your_api_key'
});

// List users with real-time updates
const users = await client.users.list({ 
  department: 'Engineering',
  sso_enabled: true 
});

// WebSocket events
client.events.on('user_created', (event) => {
  console.log('New user created:', event.data);
});
```

---

*This API documentation is for Kailash Enterprise User Management v1.0.0*
*Last Updated: January 2024*
*© 2024 Kailash AI. All rights reserved.*