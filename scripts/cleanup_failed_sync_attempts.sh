#!/bin/bash
# Clean up failed sync attempts in downstream repos

set -e

echo "🧹 Cleaning up failed sync attempts"
echo "==================================="
echo ""

# Get list of repos
REPOS=$(gh api "search/repositories?q=org:Integrum-Global+topic:kailash-template&per_page=100" --jq '.items[].name' | grep -v -E "^(new_project_template|kailash_python_sdk)$" || true)

CLOSED_PRS=0
DELETED_BRANCHES=0

for repo in $REPOS; do
    if [ -z "$repo" ]; then
        continue
    fi
    
    echo "🔍 Checking $repo..."
    
    # Find and close sync-related PRs
    PR_NUMBERS=$(gh pr list -R "Integrum-Global/$repo" --state open --json number,title --jq '.[] | select(.title | test("(Sync|sync|template|Template|Fix:|fix:)")) | .number' 2>/dev/null || echo "")
    
    for pr in $PR_NUMBERS; do
        if [ -n "$pr" ]; then
            echo "  Closing PR #$pr..."
            gh pr close "$pr" -R "Integrum-Global/$repo" --comment "Closing failed sync attempt. A new fix is being deployed." 2>/dev/null || true
            ((CLOSED_PRS++))
        fi
    done
    
    # Delete sync-related branches
    BRANCHES=$(gh api "repos/Integrum-Global/$repo/branches" --jq '.[].name' 2>/dev/null | grep -E "(template-sync-|fix-sync-|fix-workflow|emergency-fix-)" || true)
    
    for branch in $BRANCHES; do
        if [ -n "$branch" ]; then
            echo "  Deleting branch $branch..."
            gh api -X DELETE "repos/Integrum-Global/$repo/git/refs/heads/$branch" 2>/dev/null || true
            ((DELETED_BRANCHES++))
        fi
    done
done

echo ""
echo "📊 Cleanup Summary:"
echo "  - Closed PRs: $CLOSED_PRS"
echo "  - Deleted branches: $DELETED_BRANCHES"
echo ""
echo "✅ Cleanup complete!"