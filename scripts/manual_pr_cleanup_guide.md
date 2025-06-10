# Manual Template PR Cleanup Guide

The automated cleanup script identified duplicate template sync PRs that need manual cleanup. Here are the specific PRs to close:

## Summary
- **7 repositories** each have **2 template sync PRs**
- **Keep the latest PR** (created around 05:51-05:52)
- **Close the older PR** (created around 05:47)

## PRs to Close Manually

### 1. ai_coaching
- **KEEP**: PR #43 (created: 2025-06-09T05:51:53Z)
- **CLOSE**: PR #42 (created: 2025-06-09T05:47:12Z)
- URL: https://github.com/Integrum-Global/ai_coaching/pull/42

### 2. tpc_core
- **KEEP**: PR #28 (created: 2025-06-09T05:51:56Z)
- **CLOSE**: PR #27 (created: 2025-06-09T05:47:15Z)
- URL: https://github.com/Integrum-Global/tpc_core/pull/27

### 3. deal_sourcing
- **KEEP**: PR #27 (created: 2025-06-09T05:51:59Z)
- **CLOSE**: PR #26 (created: 2025-06-09T05:47:18Z)
- URL: https://github.com/Integrum-Global/deal_sourcing/pull/26

### 4. market-insights
- **KEEP**: PR #11 (created: 2025-06-09T05:52:02Z)
- **CLOSE**: PR #10 (created: 2025-06-09T05:47:21Z)
- URL: https://github.com/Integrum-Global/market-insights/pull/10

### 5. cbm
- **KEEP**: PR #12 (created: 2025-06-09T05:52:05Z)
- **CLOSE**: PR #11 (created: 2025-06-09T05:47:24Z)
- URL: https://github.com/Integrum-Global/cbm/pull/11

### 6. mcp_server
- **KEEP**: PR #11 (created: 2025-06-09T05:52:09Z)
- **CLOSE**: PR #10 (created: 2025-06-09T05:47:28Z)
- URL: https://github.com/Integrum-Global/mcp_server/pull/10

### 7. GIC_update
- **KEEP**: PR #11 (created: 2025-06-09T05:52:12Z)
- **CLOSE**: PR #10 (created: 2025-06-09T05:47:31Z)
- URL: https://github.com/Integrum-Global/GIC_update/pull/10

## Manual Cleanup Steps

For each repository listed above:

1. **Navigate to the PR URL**
2. **Click "Close pull request"**
3. **Add comment**: "Closing older template sync PR. Keeping only the latest sync."
4. **Optionally delete the branch** if GitHub offers the option

## CLI Commands (if you have proper permissions)

```bash
# Close each PR using GitHub CLI
gh pr close 42 --repo Integrum-Global/ai_coaching --comment "Closing older template sync PR. Keeping only the latest sync."
gh pr close 27 --repo Integrum-Global/tpc_core --comment "Closing older template sync PR. Keeping only the latest sync."
gh pr close 26 --repo Integrum-Global/deal_sourcing --comment "Closing older template sync PR. Keeping only the latest sync."
gh pr close 10 --repo Integrum-Global/market-insights --comment "Closing older template sync PR. Keeping only the latest sync."
gh pr close 11 --repo Integrum-Global/cbm --comment "Closing older template sync PR. Keeping only the latest sync."
gh pr close 10 --repo Integrum-Global/mcp_server --comment "Closing older template sync PR. Keeping only the latest sync."
gh pr close 10 --repo Integrum-Global/GIC_update --comment "Closing older template sync PR. Keeping only the latest sync."
```

## Verification

After cleanup, each repository should have exactly **1 open template sync PR** (the latest one).

You can verify this by running:
```bash
python scripts/cleanup_template_prs.py
```

The script will show which PRs remain and confirm the cleanup was successful.
