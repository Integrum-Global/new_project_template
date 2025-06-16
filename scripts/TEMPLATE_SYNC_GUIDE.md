# Template Sync Workflow Guide

This guide explains how to trigger and manage template syncs across all downstream repositories.

## 🔄 Overview of the Sync Process

The sync workflow in downstream repositories:
1. **Triggers**: Manual workflow dispatch only (no automatic syncs)
2. **Creates a PR**: With all template updates (can be disabled with `create_pr=false`)
3. **Syncs specific files**: Always replaces SDK docs, CLAUDE.md, workflows, and example apps
4. **Preserves client work**: Never overwrites client apps, solutions, or customizations

## 📋 What Gets Synced

### Always Replaced (from template):
- `sdk-users/` - Latest SDK documentation and guides
- `CLAUDE.md` - Latest development patterns and workflows
- `.github/workflows/` - Essential template sync workflows:
  - `sync-from-template.yml` - Template sync capability
  - `template-sync-check.yml` - Sync validation
  - `template-init.yml` - Repository setup
  - `README.md` - Workflow documentation
- Example apps:
  - `apps/qa_agentic_testing`
  - `apps/studio`
  - `apps/user_management`

### Created If Missing (preserves existing):
- Root files: `README.md`, `pyproject.toml`, `CHANGELOG.md`, `.gitignore`, `.env.example`
- Template structure: `apps/_template/`, `solutions/`, `infrastructure/`, `data/`, `docs/`, `scripts/`

### Always Preserved:
- Client apps (all apps except template examples)
- Client solutions
- Project management files (todos/, adr/, mistakes/)
- Configuration customizations
- Custom workflows

## 🚀 How to Trigger Syncs

### Option 1: Trigger All Repositories at Once

```bash
# Trigger sync workflow in all downstream repos (creates PRs)
python scripts/trigger_template_sync.py

# Trigger without creating PRs (diff only)
python scripts/trigger_template_sync.py --no-pr

# Trigger with status checking
python scripts/trigger_template_sync.py --check-status

# Trigger for a specific repo only
python scripts/trigger_template_sync.py --repo my-client-repo
```

### Option 2: Manually Trigger Individual Repos

```bash
# Using GitHub CLI
gh workflow run sync-from-template.yml \
  --repo Integrum-Global/my-client-repo \
  -f create_pr=true
```

### Option 3: Via GitHub Web UI
1. Go to the downstream repository
2. Click "Actions" tab
3. Select "Sync from Template" workflow
4. Click "Run workflow"
5. Choose whether to create PR or just show diff

## 📊 Managing Sync PRs

After triggering syncs, use the PR management script:

```bash
# List all open template sync PRs
python scripts/manage_template_prs.py list

# Merge the latest PR in each repo (closes older ones)
python scripts/manage_template_prs.py merge-latest

# Close all template sync PRs without merging
python scripts/manage_template_prs.py close-all

# Process a specific repo only
python scripts/manage_template_prs.py list --repo my-client-repo
```

## 🔄 Complete Sync Process

Here's the recommended workflow for syncing all repositories:

```bash
# 1. Trigger sync workflows across all repos
python scripts/trigger_template_sync.py

# 2. Wait for workflows to complete (2-5 minutes)
# You can check the status in GitHub Actions tab

# 3. List created PRs to verify
python scripts/manage_template_prs.py list

# 4. Review and merge PRs
python scripts/manage_template_prs.py merge-latest

# 5. (Optional) Ensure all repos have proper topics
python scripts/sync_repo_topics.py
```

## 🎯 Best Practices

1. **Regular Syncs**: Run template syncs weekly or after major template updates
2. **Review PRs**: Always review the sync PRs before merging, especially for critical repos
3. **Batch Processing**: The trigger script processes repos in batches to avoid rate limits
4. **Clean PR History**: Use `merge-latest` to keep only the most recent sync PR
5. **Topic Management**: Use the `kailash-template` topic to identify downstream repos

## ⚠️ Troubleshooting

### Workflow Not Found
Some repos might not have the sync workflow yet. These need manual setup:
```bash
# The workflow file needs to be added to:
.github/workflows/sync-from-template.yml
```

### PR Merge Conflicts
If a sync PR has conflicts:
1. Clone the repository locally
2. Checkout the sync branch
3. Resolve conflicts manually
4. Push and merge

### Rate Limiting
If you hit GitHub API rate limits:
- Reduce `--batch-size` (default: 5)
- Increase `--delay` between batches (default: 2 seconds)

### Authentication Issues
Ensure you're authenticated with GitHub CLI:
```bash
gh auth status
gh auth login  # if needed
```

## 📈 Monitoring

Track sync status:
- Check GitHub Actions tab in each repo for workflow runs
- Use `--check-status` flag to monitor triggered workflows
- Review PR descriptions for detailed sync information

## 🔮 Future Improvements

Consider automating this process:
1. Schedule regular sync triggers via GitHub Actions
2. Auto-merge PRs that pass CI checks
3. Send notifications for failed syncs
4. Create dashboard for sync status across all repos