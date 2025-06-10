# Sync Configuration for new_project_template

This template repository automatically syncs certain directories from the Kailash Python SDK to ensure SDK users always have the latest documentation and workflow patterns.

## 📁 Synced Directories

### sdk-users/
- **Source**: Kailash Python SDK `sdk-users/` directory
- **Purpose**: SDK reference documentation, patterns, and examples
- **Status**: READ-ONLY - Do not edit locally
- **Sync**: Daily at 3 AM UTC

### project-workflows/
- **Source**: Kailash Python SDK `project-workflows/` directory
- **Purpose**: Claude Code workflow guides and templates
- **Status**: READ-ONLY - Do not edit locally
- **Sync**: Daily at 2 AM UTC
- **Note**: Currently the SDK doesn't have this directory - reserved for future use

## ⚙️ How Sync Works

1. **Automated Schedule**: GitHub Actions run daily to check for updates
2. **Pull Request Creation**: Changes are proposed via PR for review
3. **Manual Trigger**: Can sync on-demand from Actions tab
4. **Complete Replacement**: Entire directories are replaced (not merged)

## ⚠️ Important Rules

### Never Edit Synced Directories
Any changes to these directories will be lost:
- ❌ `sdk-users/` - SDK documentation
- ❌ `project-workflows/` - Workflow guides

### Make Changes Upstream
To update these directories:
1. Submit PR to Kailash Python SDK repository
2. Wait for merge and next sync
3. Changes will flow to all template users

## 🔧 Configuration

The sync is configured in:
- `.github/workflows/sync-sdk-users.yml`
- `.github/workflows/sync-project-workflows.yml`

To customize:
1. Update `SOURCE_REPO` to point to your fork
2. Adjust schedule in cron expression
3. Modify labels or PR templates

## 📋 Package Distribution

When building packages from this template:
- `sdk-users/` is excluded (see MANIFEST.in)
- `project-workflows/` is excluded
- `infrastructure/` is excluded
- Only `src/solutions/` is packaged

This ensures:
- Smaller package size
- No duplicate documentation
- Clean dependency on kailash SDK

## 🔄 Version Synchronization

The template automatically maintains version compatibility with the Kailash SDK:

### Manual Version Update
```bash
# Update template to use latest SDK version
python scripts/sync_version.py --commit

# Check version compatibility
python scripts/sync_version.py --dry-run
```

### Automatic Version Sync
- Template version tracks SDK version
- Dependency version uses exact pin: `kailash==X.Y.Z`
- Version updates create separate commits
- Downstream repos get notified of version changes

## 🚀 For Template Users

If you're using this template for your project:

1. **Keep syncs enabled** to get latest SDK patterns
2. **Review sync PRs** before merging
3. **Never modify** synced directories
4. **Build solutions** in `src/solutions/`
5. **Use Claude Code** with workflow guides

## 📞 Getting Help

- **Sync issues**: Check Actions tab for errors
- **Content issues**: Report to Kailash SDK repository
- **Template issues**: Open issue in this repository
