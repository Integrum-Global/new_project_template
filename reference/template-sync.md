# Template Repository Synchronization Guide

## Overview
This repository serves as a template that automatically syncs updates to all downstream repositories at 3am SGT daily.

### Who Needs What?
- **Template Admin**: Needs PAT with access to all repositories (one-time setup)
- **Developers**: Need NOTHING - just collaborator access to their repo
- **Team Leads**: Just review and merge automated PRs

## GitHub Teams Setup

### For Organizations Using Collaborators
1. **Admin creates one PAT** with access to all repositories
2. **PAT is stored as secret** in template repository only
3. **CODEOWNERS is pre-configured** to protect `.github/` folder
4. **Developers added as collaborators** to downstream repos
5. **No PAT needed for developers** - they just work on their code

### How It Works
1. **Template repo** has `sync-to-downstream.yml` - pushes updates to all downstream repos
2. **Downstream repos** have `sync-from-template.yml` - pulls updates from template
3. **Automatic cleanup** - When creating from template, unnecessary files are removed
4. **No manual editing** - Everything is configured automatically

### Zero Developer Intervention
- ✅ **Automatic daily syncs** at 3am SGT
- ✅ **Protected `.github` folder** via CODEOWNERS
- ✅ **PRs created automatically** for review
- ✅ **No manual pulling required** from developers
- ✅ **Focus on writing code**, not maintaining infrastructure

## For Template Repository Maintainers

📋 **Quick Start**: See [Setup Checklist](../docs/SETUP-CHECKLIST.md) or [Detailed Setup Guide](../docs/SETUP-TEMPLATE-SYNC.md)

### Setup Requirements

#### 1. Create a Personal Access Token (Required)
**Why is a PAT needed?**
- GitHub Actions default token (`GITHUB_TOKEN`) cannot create PRs in other repositories
- Even with collaborator access, cross-repository operations need elevated permissions
- The PAT allows the template repo to push changes to all downstream repos

Create a PAT with these permissions:
- `repo` - Full control of private repositories (to push to downstream repos)
- `workflow` - Update GitHub Action workflows (to sync .github folder)

**Steps:**
1. Go to GitHub Settings → Developer settings → Personal access tokens → Tokens (classic)
2. Generate new token with the permissions above
3. Copy the token
4. This should be created by an admin who has access to all repositories

#### 2. Configure Secrets and Variables

**Organization Secret (Recommended):**
- Go to: Organization Settings → Secrets → Actions
- Add `TEMPLATE_SYNC_TOKEN` with your PAT
- Grant access to template repository
- Benefit: Can be shared across multiple template repos

**Repository Secret (Alternative):**
- Go to: Repository Settings → Secrets → Actions  
- Add `TEMPLATE_SYNC_TOKEN` with your PAT
- Only available to this specific repository

**Variables (Repository Level):**
- `DOWNSTREAM_REPOS`: Comma-separated list of repositories to sync
  ```
  org/repo1,org/repo2,org/repo3
  ```
  
**Alternative:** Add topic `kailash-template` to downstream repos for auto-discovery

#### 3. Path Filtering
The workflow only triggers on changes to template-relevant files:
- `.github/**` - GitHub Actions and workflows
- `docs/**` - Documentation
- `guide/**` - Guides and instructions
- `reference/**` - API references
- `templates/**` - Solution templates
- `src/shared/**` - Shared components
- `scripts/*.py` - Python scripts
- `pyproject.toml` - Dependencies
- `CLAUDE.md` - Claude instructions
- `README.md` - Main documentation

### Sync Triggers
- **Automatic**: Pushes to main branch
- **Scheduled**: Daily at 3am SGT (7pm UTC)
- **Manual**: GitHub Actions workflow dispatch

### Manual Sync Commands

**Via GitHub UI:**
1. Go to Actions → "Sync Template to Downstream Repositories"
2. Click "Run workflow"
3. Optionally specify a single target repo
4. Enable "Force sync" if needed

**Via CLI:**
```bash
# Sync all repositories
gh workflow run sync-to-downstream.yml

# Sync specific repository
gh workflow run sync-to-downstream.yml -f target_repo=org/specific-repo

# Force sync even if no changes detected
gh workflow run sync-to-downstream.yml -f force_sync=true

# Check sync status
gh run list --workflow=sync-to-downstream.yml
```

## For Downstream Repository Users (Developers)

### Automatic Updates - No Action Required!
1. **Template updates happen automatically** via pull requests
2. **`.github` folder is protected** - developers cannot modify it
3. **Your project-specific code is preserved** in `src/solutions/` and `data/`
4. **No PAT needed** - You're added as a collaborator

### What Developers Need to Know
- **DO NOT modify anything in `.github/`** - It's protected by CODEOWNERS
- **Focus on your solution code** in `src/solutions/`
- **Template updates appear as PRs** - Your team lead will review and merge
- **No manual sync needed** - Everything is automated
- **No tokens or secrets needed** - Just clone and code!

📋 **Detailed File List**: See [Complete Sync Reference](../docs/SYNC-FILES-REFERENCE.md)

### Files Preserved (🛡️ Never Touched)
- `src/solutions/*` - Your solution code
- `data/*` - Project-specific data
- `.env*` - Environment configurations
- README.md sections between markers
- Project-specific dependencies in pyproject.toml
- Custom workflows ending with `_custom.yml`

### Files Always Updated (✅ Synced from Template)
- `.github/**` - ALL GitHub Actions and workflows
- `reference/*` - API documentation and guides
- `guide/*` - Instructions, ADRs, mistakes
- `templates/*` - Solution templates
- `src/shared/*` - Shared components
- Core scripts: `setup_env.py`, `validate.py`, `deploy.py`

### Files Merged (🔄 Smart Merge)
- `README.md` - Template + your project sections
- `pyproject.toml` - Template + your dependencies
- `CLAUDE.md` - Template + your project instructions

### Customizing Your Repository
1. Add project-specific content in README.md between the markers:
   ```markdown
   <!-- PROJECT SPECIFIC START -->
   Your project-specific content here
   <!-- PROJECT SPECIFIC END -->
   ```

2. Add project-specific Claude instructions in CLAUDE.md after:
   ```markdown
   ## Project-Specific Instructions
   Your instructions here
   ```

3. Create custom workflows with `_custom.yml` suffix to prevent overwriting

## Troubleshooting

### Sync PR Conflicts
If the sync PR has conflicts:
1. Check out the PR branch locally
2. Resolve conflicts (prefer your changes for project-specific files)
3. Push resolved changes
4. Merge PR

### Managing Sync (Team Leads Only)
- **Disable sync temporarily**: Contact template maintainers
- **Custom workflows**: Must end with `_custom.yml` to avoid being overwritten
- **Emergency override**: Only through CODEOWNERS approval

## Testing & Rollout

### 1. Test with one repository first:
```bash
gh workflow run sync-to-downstream.yml -f target_repo=my-org/test-project
```

### 2. Gradually add more repositories:
Start with `DOWNSTREAM_REPOS`:
```
my-org/test-project
```

Then expand to:
```
my-org/test-project,my-org/project-1,my-org/project-2
```

### 3. Monitor the Actions tab for results

## Advantages of This Approach

- ✅ **Centralized management**: One place to control all syncing
- ✅ **Immediate updates**: Syncs automatically when template changes
- ✅ **Conflict handling**: Creates PRs for manual review when needed
- ✅ **Selective syncing**: Can target specific repos manually
- ✅ **Smart filtering**: Only runs when relevant files change
- ✅ **Preserve customizations**: Project-specific files remain untouched