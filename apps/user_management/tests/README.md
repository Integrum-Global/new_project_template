# User Management App - Test Suite

This directory contains all tests for the User Management application.

## Test Structure

```
tests/
├── unit/           # Unit tests for models, services, validators
├── integration/    # Integration tests for API, database, workflows
├── functional/     # End-to-end functional tests for user flows
├── e2e/           # Complete end-to-end tests including UI
└── performance/   # Load and performance tests
```

## Running Tests

### Run All Tests
```bash
cd apps/user_management
pytest tests/
```

### Run Specific Category
```bash
# Unit tests only
pytest tests/unit/

# Integration tests only
pytest tests/integration/

# Functional tests only
pytest tests/functional/
```

### Run with Coverage
```bash
pytest tests/ --cov=core --cov=api --cov-report=html
```

## Test Categories

### Unit Tests
- Test individual components in isolation
- Mock external dependencies
- Fast execution
- Examples: model validation, service methods

### Integration Tests
- Test component interactions
- Use test database
- Test API endpoints
- Examples: user creation API, SSO integration

### Functional Tests
- Test complete user flows
- Business scenario validation
- Examples: complete registration flow, permission checks

### E2E Tests
- Full system tests
- Multi-step user journeys
- Examples: login → create team → invite users → logout

### Performance Tests
- Load testing
- Concurrent user scenarios
- Resource usage monitoring
- Examples: 1000 concurrent logins

## Key Test Files

- `unit/test_models.py` - User, Role, Permission model tests
- `unit/test_validators.py` - Input validation tests
- `integration/test_api_integration.py` - REST API tests
- `integration/test_sso_integration.py` - SSO provider tests
- `functional/test_user_flows.py` - Registration, login, profile flows
- `functional/test_permission_system.py` - RBAC/ABAC tests
- `e2e/test_complete_user_journey.py` - Full user lifecycle
- `performance/test_concurrent_users.py` - Load testing
