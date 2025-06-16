# GitHub Actions Workflow Strategy for Client Projects

## Overview

This repository provides a focused CI/CD pipeline optimized for **Kailash SDK client projects**. The workflows are designed to validate client applications and solutions while maintaining the template synchronization ecosystem.

## Active Workflows for Client Projects

### 1. `unified-ci.yml` - Template Validation ⭐ **PRIMARY CI**
- **Purpose**: Smart CI pipeline for client project validation
- **Triggers**:
  - Push to feature branches (`feat/*`, `feature/*`)
  - Pull requests to `main`
  - Manual dispatch
- **Smart Features**:
  - For pushes: Checks if PR exists, skips duplicate runs
  - For PRs: Always runs full validation suite
  - For manual: Always runs comprehensive tests
- **Validation Includes**:
  - Template structure validation (apps/, solutions/)
  - Code formatting (black, isort)
  - Linting (ruff critical errors)
  - Python compatibility (3.11, 3.12)
  - Security scanning (Trivy)
  - Kailash SDK import validation
- **Duration**: 5-10 minutes

### 2. `template-init.yml` - Repository Initialization
- **Purpose**: Automatically configures new client repositories
- **Triggers**: Runs once when repository is created from template
- **Setup Includes**:
  - Creates `.env.example` with Kailash SDK configuration
  - Configures `.gitignore` for client projects
  - Creates `data/inputs/` and `data/outputs/` directories
  - Adds `kailash-template` topic for automatic updates
- **Duration**: 1-2 minutes

### 3. `sync-from-template.yml` - Template Updates
- **Purpose**: Syncs latest SDK guidance and development patterns
- **Triggers**: Manual dispatch only (no automatic runs)
- **Sync Strategy**: **Sync-If-Missing**
  - **Always Replace**: `sdk-users/` (latest SDK docs), `CLAUDE.md` (development patterns)
  - **Add If Missing**: Template structure (apps/_template/, solutions/, etc.)
  - **Never Touch**: Client apps, client solutions, project management
- **Duration**: 2-3 minutes

### 4. `template-sync-check.yml` - Sync Validation
- **Purpose**: Lightweight validation for template sync PRs
- **Triggers**: Pull requests containing template updates
- **Benefits**: Faster validation (1-2 min) vs full CI (5-10 min)
- **Checks**: Template structure integrity, basic validation

### 5. `security-report.yml` - Security Scanning
- **Purpose**: Provides security feedback on pull requests
- **Triggers**: Pull requests to `main` branch
- **Features**:
  - Trivy vulnerability scanning
  - Severity breakdown (Critical, High, Medium)
  - Automated PR comments with results
  - Smart skipping for template sync PRs
- **Duration**: 2-3 minutes

### 6. `template-cleanup.yml` - Post-Creation Cleanup
- **Purpose**: Removes template-specific files from new repositories
- **Triggers**: Runs once in new repositories, then self-disables
- **Cleanup Actions**:
  - Removes `sync-to-downstream.yml` (template-only workflow)
  - Removes template sync scripts
  - Creates client project directories
  - Self-disables after completion

## Template Synchronization Ecosystem

### How Template Updates Work

1. **Template Repository** (`new_project_template`):
   - Contains latest SDK guidance in `sdk-users/`
   - Contains development patterns in `CLAUDE.md`
   - Provides app/solution templates

2. **Client Repositories** (created from template):
   - Automatically receive SDK updates via `sync-from-template.yml`
   - **Protected Content**: Apps, solutions, project management remain untouched
   - **Updated Content**: Only SDK documentation and development patterns

3. **Sync-If-Missing Strategy**:
   - **Zero Risk**: Client customizations are never overwritten
   - **Always Current**: SDK guidance stays up-to-date
   - **Template Structure**: Added if missing, preserved if exists

### Manual Template Sync

Client repositories can manually sync template updates:

```bash
# In client repository
gh workflow run sync-from-template.yml
```

## Workflow Optimization Features

### 1. Smart Duplicate Prevention
- Detects when PR exists for a branch
- Skips redundant test runs on push events
- **40-50% CI resource savings**

### 2. Context-Aware Execution
- Template sync PRs use lightweight validation
- Documentation-only changes skip heavy testing
- Security scanning skips for template updates

### 3. Intelligent Test Selection
- Basic validation for template structure
- Full testing matrix for client code changes
- Security scanning for all client changes

## Client Development Workflow

### 1. Creating New Apps
```bash
# Copy template structure
cp -r apps/_template/ apps/my_new_app/
cd apps/my_new_app/

# Customize configuration
vim config.py  # Update app name and settings
```

### 2. Running Tests Locally
```bash
# Install dependencies
pip install kailash-sdk
pip install -e .

# Run validation
pytest apps/my_app/tests/
black apps/my_app/
ruff check apps/my_app/
```

### 3. Push and CI Validation
- Push to feature branch: Basic validation (2-3 min)
- Create PR: Full validation suite (5-10 min)
- Merge to main: Complete validation with reports

## Security and Compliance

### Automated Security Scanning
- **Trivy Integration**: Scans for vulnerabilities in dependencies
- **PR Comments**: Immediate feedback on security issues
- **Severity Tracking**: Critical, High, Medium vulnerability counts
- **Actionable Reports**: Detailed findings for remediation

### Secret Protection
- `.env` files excluded from repository
- `.env.example` provides configuration template
- Gitignore configured for client secrets

## Troubleshooting

### Common Issues

1. **Template Sync Failures**
   - Check repository has `kailash-template` topic
   - Verify workflow permissions (write access needed)
   - Review sync logs for conflicts

2. **CI Test Failures**
   - Ensure `kailash-sdk` is in dependencies
   - Check Python version compatibility (3.11+)
   - Verify app structure follows template

3. **Security Scan Issues**
   - Review vulnerability details in PR comments
   - Update dependencies to fix known issues
   - Consider ignore-unfixed for unavoidable issues

### Getting Help

- **SDK Documentation**: Check `sdk-users/developer/` for usage patterns
- **Development Patterns**: Review `CLAUDE.md` for workflow guidance
- **Template Issues**: Report in template repository issues

## Migration from SDK Development

This template is specifically designed for **client projects** that:
- Install `kailash-sdk` from PyPI (not source)
- Build applications using the SDK
- Focus on business solutions, not SDK development

**Not Included** (intentionally removed):
- SDK source code testing workflows
- Documentation build/deploy for SDK
- SDK development specific tools
- Complex test matrices for SDK internals

The streamlined workflow focuses on what client projects actually need while maintaining connection to the latest SDK guidance and development patterns.# Template sync trigger
