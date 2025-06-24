# System Administrator Test Scenarios

## Test Scenario Categories

### 1. Authentication & Access Tests
- **SA-AUTH-001**: First-time login with temporary password
- **SA-AUTH-002**: Password change enforcement
- **SA-AUTH-003**: 2FA setup and verification
- **SA-AUTH-004**: Session timeout handling
- **SA-AUTH-005**: Concurrent session management

### 2. User Management Tests
- **SA-USER-001**: Create single user with all fields
- **SA-USER-002**: Create user with minimal fields
- **SA-USER-003**: Bulk import 100 users
- **SA-USER-004**: Handle duplicate user creation
- **SA-USER-005**: Deactivate user and verify access revoked
- **SA-USER-006**: Reactivate user and verify access restored
- **SA-USER-007**: Delete user and verify data handling

### 3. Role & Permission Tests
- **SA-ROLE-001**: Create custom role with specific permissions
- **SA-ROLE-002**: Create role hierarchy (parent-child)
- **SA-ROLE-003**: Modify existing role permissions
- **SA-ROLE-004**: Delete role with active users
- **SA-ROLE-005**: Test permission inheritance
- **SA-ROLE-006**: Bulk role assignment to users
- **SA-ROLE-007**: Role conflict resolution

### 4. Security Tests
- **SA-SEC-001**: Detect and block SQL injection attempts
- **SA-SEC-002**: Monitor failed login attempts
- **SA-SEC-003**: Auto-lock account after failed attempts
- **SA-SEC-004**: IP-based access restrictions
- **SA-SEC-005**: Suspicious activity detection
- **SA-SEC-006**: Concurrent modification protection
- **SA-SEC-007**: Audit trail completeness

### 5. Performance Tests
- **SA-PERF-001**: Bulk import 1000 users in < 30 seconds
- **SA-PERF-002**: Search 10000 users in < 100ms
- **SA-PERF-003**: Generate audit report for 1 month in < 5 seconds
- **SA-PERF-004**: Handle 100 concurrent admin operations
- **SA-PERF-005**: Permission check response < 10ms

### 6. Integration Tests
- **SA-INT-001**: LDAP user synchronization
- **SA-INT-002**: Email notification delivery
- **SA-INT-003**: API rate limiting
- **SA-INT-004**: Webhook event delivery
- **SA-INT-005**: SSO integration

### 7. Error Handling Tests
- **SA-ERR-001**: Database connection failure
- **SA-ERR-002**: Email service unavailable
- **SA-ERR-003**: Disk space exhaustion
- **SA-ERR-004**: Network timeout handling
- **SA-ERR-005**: Corrupted data recovery

### 8. Compliance Tests
- **SA-COMP-001**: GDPR data export
- **SA-COMP-002**: Data retention policy enforcement
- **SA-COMP-003**: Audit log immutability
- **SA-COMP-004**: PII data masking
- **SA-COMP-005**: Compliance report generation

## Detailed Test Cases

### SA-USER-001: Create Single User with All Fields

**Objective**: Verify complete user creation flow with all optional fields

**Preconditions**:
- Admin user logged in with appropriate permissions
- No existing user with test email

**Test Steps**:
1. Navigate to user creation form
2. Fill in all fields:
   - Email: `testuser001@example.com`
   - Username: `testuser001`
   - First Name: `Test`
   - Last Name: `User`
   - Department: `Engineering`
   - Phone: `+1-555-0100`
   - Employee ID: `EMP001`
   - Manager: `manager@example.com`
   - Start Date: Current date
   - Custom Attributes: `{"team": "Backend", "location": "NYC"}`
3. Select roles: `Employee`, `Developer`
4. Set password policy: Require change on first login
5. Enable email verification
6. Submit form

**Expected Results**:
- User created successfully
- Confirmation message displayed
- User appears in user list
- Welcome email sent
- Audit log entry created
- All fields properly stored

**Validation**:
- Verify user can login
- Check all fields are retrievable
- Confirm roles are assigned
- Validate audit trail

### SA-PERF-001: Bulk Import Performance Test

**Objective**: Verify system can handle bulk import efficiently

**Preconditions**:
- CSV file with 1000 valid user records
- Admin user with bulk import permission

**Test Steps**:
1. Prepare CSV file with columns:
   - email, username, first_name, last_name, department, role
2. Start performance timer
3. Upload file via bulk import API
4. Monitor import progress
5. Wait for completion
6. Stop timer

**Expected Results**:
- All 1000 users imported successfully
- Total time < 30 seconds
- No timeout errors
- Progress updates every 10%
- Detailed import report generated

**Performance Metrics**:
- Import rate: > 33 users/second
- Memory usage: < 500MB peak
- CPU usage: < 80% peak
- Database connections: < 50

### SA-SEC-003: Auto-lock After Failed Attempts

**Objective**: Verify account lockout mechanism

**Preconditions**:
- Test user account active
- Lockout threshold set to 5 attempts

**Test Steps**:
1. Attempt login with wrong password 5 times
2. Verify account locked message
3. Try correct password
4. Verify still locked
5. Wait for lockout duration (30 min) or admin unlock
6. Verify can login again

**Expected Results**:
- Account locked after 5th attempt
- Clear error message about lockout
- Security event logged
- Admin notification sent
- Cannot login even with correct password
- Unlock successful after timeout/admin action

**Security Validation**:
- Audit log shows all attempts
- IP address recorded
- Security score updated
- No timing attack vulnerability
