# Template Sync PR Merge Scripts

This directory contains scripts to manage and merge template sync PRs across multiple repositories.

## 🎯 Quick Start

To merge all template sync PRs across the 19 target repositories:

```bash
# Using the bash script (simpler, sequential processing)
./merge_template_sync_prs.sh

# Using the Python script (parallel processing, more features)
./merge_specific_repos_prs.py
```

## 📁 Scripts Overview

### 1. `merge_template_sync_prs.sh` (Bash)
A straightforward bash script that:
- Processes repositories sequentially
- Merges the most recent template sync PR in each repo
- Closes older template sync PRs
- Provides colored output and detailed reporting
- Handles merge conflicts gracefully

**Usage:**
```bash
./merge_template_sync_prs.sh
```

### 2. `merge_specific_repos_prs.py` (Python)
An enhanced Python script with additional features:
- Parallel processing for faster execution
- Dry-run mode to preview changes
- Detailed conflict detection and reporting
- Customizable worker count
- More comprehensive error handling

**Usage:**
```bash
# Basic usage
./merge_specific_repos_prs.py

# Dry run (preview without making changes)
./merge_specific_repos_prs.py --dry-run

# Process specific repositories only
./merge_specific_repos_prs.py --repos talentverse pg corpsec

# Use more parallel workers for faster processing
./merge_specific_repos_prs.py --workers 10
```

## 📋 Target Repositories

Both scripts process these 19 repositories by default:
1. talentverse
2. pg
3. corpsec
4. tpc_shipping_migration
5. tpc-migration
6. ESG-report
7. ai-coaching
8. cdl_kailash_migration
9. decisiontrackerfe
10. GIC_update
11. mcp_server
12. cbm
13. tpc_shipping_fe
14. tpc_shipping
15. market-insights
16. narrated_derivations
17. deal_sourcing
18. tpc_core
19. ai_coaching_demo

## 🔄 How It Works

1. **PR Discovery**: Finds all open PRs that match template sync patterns:
   - Title contains "Sync template updates"
   - Branch name contains "template-sync-"
   - Body contains specific template sync markers

2. **PR Processing**:
   - Sorts PRs by creation date (newest first)
   - Attempts to merge the most recent PR
   - Closes all older template sync PRs
   - Handles merge conflicts gracefully

3. **Error Handling**:
   - Detects merge conflicts before attempting merge
   - Falls back to non-admin merge if admin merge fails
   - Reports detailed status for each repository

## 📊 Output and Reporting

Both scripts provide:
- Real-time progress updates with colored output
- Summary statistics (successful merges, failures, conflicts)
- Detailed per-repository status
- Action items for manual intervention

### Example Output:
```
📦 Processing: talentverse
  Found 2 template sync PR(s)
  
  PR #123: Sync template updates from new_project_template
    Created: 2025-01-19T10:00:00Z
    → Attempting to merge...
    ✓ Successfully merged PR #123
    
  PR #120: Sync template updates from new_project_template
    Created: 2025-01-15T10:00:00Z
    → Closing older PR...
    ✓ Successfully closed PR #120

========================================
Summary Report
========================================

Overall Statistics:
  ✓ Successful merges: 15
  ✗ Failed merges: 2
  ⚠️ Conflicts: 1
  ○ No PRs found: 1
  ◉ Total older PRs closed: 8
    Total repositories: 19
```

## ⚠️ Prerequisites

1. **GitHub CLI**: Must be installed and authenticated
   ```bash
   # Check if gh is installed
   gh --version
   
   # Authenticate if needed
   gh auth login
   ```

2. **Permissions**: You need write access to all target repositories

3. **Dependencies**:
   - Bash script: `jq` (JSON processor)
   - Python script: Standard library only (Python 3.6+)

## 🚨 Handling Merge Conflicts

If a PR has merge conflicts:

1. The scripts will skip the merge and report the conflict
2. You'll need to resolve conflicts manually:
   ```bash
   # Check out the PR locally
   gh pr checkout <PR_NUMBER> --repo Integrum-Global/<REPO>
   
   # Resolve conflicts
   # ... edit conflicted files ...
   
   # Commit and push
   git add .
   git commit -m "Resolve merge conflicts"
   git push
   
   # Then merge via GitHub UI or CLI
   gh pr merge <PR_NUMBER> --repo Integrum-Global/<REPO>
   ```

## 🔍 Troubleshooting

### Common Issues:

1. **"Not authenticated with GitHub CLI"**
   - Run: `gh auth login`

2. **"PR is blocked by status checks"**
   - The script attempts admin merge to bypass
   - If that fails, resolve status check issues manually

3. **Rate limiting**
   - Reduce worker count: `--workers 3`
   - Process repos in batches

4. **Permission denied**
   - Ensure you have write access to repositories
   - Check organization permissions

## 🎯 Best Practices

1. **Run dry-run first**: Use `--dry-run` to preview changes
2. **Monitor the output**: Watch for conflicts and failures
3. **Process in batches**: For many repos, consider smaller batches
4. **Regular syncs**: Run weekly or after major template updates
5. **Review before merging**: Check PR contents, especially for critical repos

## 📈 Performance Tips

- The Python script with parallel processing is ~3-5x faster
- Default 5 workers is optimal for most cases
- Increase workers if you have good network/API limits
- Use bash script for simpler, more predictable execution

## 🔗 Related Scripts

- `trigger_template_sync.py`: Triggers template sync workflows
- `manage_template_prs.py`: General PR management across all repos
- `sync_repo_topics.py`: Manages repository topics