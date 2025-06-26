# Template Sync Workflow

## Overview

This document explains how template synchronization works with the new `template-sync` branch workflow, providing safer integration of template updates.

## How It Works

### 1. Automatic Template Sync Process

When changes are pushed to the template repository (`new_project_template`), the system:

1. **Creates/Updates `template-sync` branch** in each downstream repository
2. **Creates a timestamped feature branch** from `template-sync`
3. **Syncs template updates** to the feature branch
4. **Creates a PR** targeting the `template-sync` branch (not `main`)

### 2. Integration Workflow for Downstream Repos

#### Phase 1: Template Update Review
```bash
# 1. Review the automated PR targeting template-sync
# 2. Check for conflicts with your project-specific code
# 3. Merge the PR to template-sync branch
gh pr merge <pr-number> --squash
```

#### Phase 2: Testing and Validation
```bash
# 1. Switch to template-sync branch
git checkout template-sync
git pull origin template-sync

# 2. Test your application with new template updates
# Run your tests, check functionality, etc.

# 3. If issues found, create fixes directly on template-sync
git checkout -b fix/template-integration-issue
# Make your fixes
git commit -m "fix: resolve template integration issue"
git push origin fix/template-integration-issue
# Create PR: fix/template-integration-issue → template-sync
```

#### Phase 3: Integration to Main
```bash
# 1. When ready, create PR to merge template-sync → main
gh pr create --base main --head template-sync \
  --title "Integrate template updates" \
  --body "Integrating validated template updates from template-sync branch"

# 2. Review and merge to main
gh pr merge <pr-number> --squash
```

## Benefits

### ✅ **Safety**
- Template changes don't directly affect your main branch
- Full testing opportunity before integration
- Easy rollback if issues are found

### ✅ **Control**
- You decide when to integrate template updates
- You can batch multiple template updates
- You can add project-specific fixes before main integration

### ✅ **Transparency**
- Clear separation between template updates and project code
- Full audit trail of what changes came from template
- Easy to see what needs to be integrated

## Branch Strategy

```
main                    ← Your stable production code
├── template-sync       ← Staging area for template updates
│   ├── template-sync-20250624-054826  ← Automated sync PRs
│   ├── template-sync-20250624-123456  ← Another sync PR
│   └── fix/template-integration-issue ← Your fixes/adaptations
```

## Handling Multiple Template Updates

If multiple template sync PRs accumulate:

```bash
# 1. Merge them to template-sync in chronological order
gh pr list --base template-sync --state open
gh pr merge <earliest-pr> --squash
gh pr merge <next-pr> --squash
# etc.

# 2. Test the combined changes
git checkout template-sync
# Run tests

# 3. Create single integration PR to main
gh pr create --base main --head template-sync \
  --title "Integrate multiple template updates"
```

## Emergency Procedures

### If Template Update Breaks Your Code

```bash
# 1. Don't panic - main branch is unaffected
# 2. Create fix branch from template-sync
git checkout template-sync
git checkout -b hotfix/template-compatibility
# Make necessary fixes
git commit -m "fix: restore compatibility with template changes"
git push origin hotfix/template-compatibility

# 3. Merge fix to template-sync
gh pr create --base template-sync --head hotfix/template-compatibility
gh pr merge <pr-number> --squash

# 4. Now safe to integrate to main
```

### If You Need to Skip a Template Update

```bash
# 1. Close the template sync PR without merging
gh pr close <pr-number>

# 2. The template-sync branch remains at previous state
# 3. Future template updates will include the skipped changes
```

## Configuration

The template sync targets `template-sync` branch by default. If you need to customize this:

1. **Template Repository**: Modify `scripts/sync_template.py`
2. **Downstream Repository**: Create `.github/template-sync-config.yml`

```yaml
# .github/template-sync-config.yml
target_branch: "template-integration"  # Custom branch name
auto_merge: false                      # Require manual review
skip_patterns:                         # Skip certain files
  - "custom-config.yaml"
  - "project-specific/**"
```

## Monitoring

Monitor template sync status:

```bash
# Check pending template updates
gh pr list --base template-sync --state open

# Check template-sync branch status vs main
git log --oneline main..template-sync

# Check if template-sync is ahead of main
git rev-list --count main..template-sync
```

## Best Practices

### 1. **Regular Integration**
- Review and merge template sync PRs weekly
- Don't let too many accumulate
- Test immediately after merging to template-sync

### 2. **Project-Specific Customizations**
- Keep customizations in clearly marked areas
- Document any template file modifications
- Consider contributing useful changes back to template

### 3. **Testing Strategy**
- Always test in template-sync before main integration
- Include template update testing in your CI pipeline
- Validate that existing functionality still works

### 4. **Communication**
- Notify team when integrating template updates
- Document any breaking changes or required actions
- Share successful integration patterns with other teams

## Troubleshooting

### Common Issues

**Q: Template sync PR has conflicts**
```bash
# A: Resolve conflicts in the feature branch
git checkout <template-sync-branch>
# Resolve conflicts manually
git add .
git commit -m "resolve: template sync conflicts"
git push origin <template-sync-branch>
```

**Q: Need to modify template files for project compatibility**
```bash
# A: Make changes in template-sync branch
git checkout template-sync
# Edit files as needed
git commit -m "adapt: template changes for project compatibility"
git push origin template-sync
```

**Q: Want to contribute fix back to template**
```bash
# A: Create PR to template repository
# 1. Fork/clone template repository
# 2. Apply your fix
# 3. Create PR to template repo
# 4. Reference in your downstream integration PR
```

This workflow provides maximum safety and control while keeping downstream repositories updated with template improvements.