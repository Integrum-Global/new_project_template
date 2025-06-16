#!/bin/bash

# Clean up duplicate template sync PRs across all downstream repositories
# Keeps only the latest template sync PR in each repo and closes older ones

echo "🧹 Cleaning up duplicate template sync PRs..."

# Get list of downstream repos (exclude template and kailash_python_sdk)
REPOS=$(gh api "search/repositories?q=org:Integrum-Global+topic:kailash-template&per_page=100" --jq '.items[].name' | grep -v -E "^(new_project_template|kailash_python_sdk)$" || true)

if [ -z "$REPOS" ]; then
    echo "❌ No downstream repositories found"
    exit 1
fi

TOTAL_CLOSED=0

for repo in $REPOS; do
    echo ""
    echo "📁 Checking $repo..."
    
    # Get template sync PRs (open state only)
    TEMPLATE_PRS=$(gh pr list --repo "Integrum-Global/$repo" --state open --search "template sync" --json number,title,createdAt --jq 'sort_by(.createdAt) | reverse | .[].number' 2>/dev/null || true)
    
    if [ -z "$TEMPLATE_PRS" ]; then
        echo "  ✅ No template sync PRs found"
        continue
    fi
    
    # Convert to array
    PR_ARRAY=($TEMPLATE_PRS)
    PR_COUNT=${#PR_ARRAY[@]}
    
    if [ $PR_COUNT -eq 1 ]; then
        echo "  ✅ Only 1 template sync PR found (#${PR_ARRAY[0]}) - keeping it"
        continue
    fi
    
    echo "  📊 Found $PR_COUNT template sync PRs"
    echo "  🎯 Keeping latest PR #${PR_ARRAY[0]}"
    
    # Close all but the first (latest) PR
    for ((i=1; i<$PR_COUNT; i++)); do
        PR_NUM=${PR_ARRAY[i]}
        echo "  🗑️  Closing older PR #$PR_NUM..."
        
        gh pr close "$PR_NUM" --repo "Integrum-Global/$repo" \
            --comment "🤖 Closing duplicate template sync PR - superseded by newer sync #${PR_ARRAY[0]}" \
            2>/dev/null || echo "    ⚠️  Failed to close PR #$PR_NUM"
        
        ((TOTAL_CLOSED++))
    done
done

echo ""
echo "✅ Cleanup complete!"
echo "📊 Total PRs closed: $TOTAL_CLOSED"
echo ""
echo "🎯 Next steps:"
echo "  1. Review the remaining template sync PRs in each repo"
echo "  2. Test that they only trigger template-sync-check.yml (not unified-ci.yml)"
echo "  3. Merge the PRs once validation passes"