#!/bin/bash
# Emergency fix for broken sync workflows in all downstream repos

set -e

echo "🚨 Emergency Workflow Fix Script"
echo "================================"
echo "This will fix the broken sync-from-template.yml in all downstream repos"
echo ""

# Store template directory
TEMPLATE_DIR="$(pwd)"

# Get list of repos with kailash-template topic (excluding kailash_python_sdk)
REPOS=$(gh api "search/repositories?q=org:Integrum-Global+topic:kailash-template&per_page=100" --jq '.items[].name' | grep -v -E "^(new_project_template|kailash_python_sdk)$" || true)

TOTAL_REPOS=$(echo "$REPOS" | wc -l | tr -d ' ')
echo "📊 Found $TOTAL_REPOS downstream repositories to fix"
echo ""

SUCCESS_COUNT=0
FAILED_COUNT=0

for repo in $REPOS; do
    if [ -z "$repo" ]; then
        continue
    fi
    
    echo "🔧 Fixing $repo..."
    
    # Create temp directory
    TEMP_DIR=$(mktemp -d)
    trap "rm -rf $TEMP_DIR" EXIT
    
    cd "$TEMP_DIR"
    
    # Clone the repo
    if ! gh repo clone "Integrum-Global/$repo" -- --depth 1 2>/dev/null; then
        echo "❌ Failed to clone $repo"
        ((FAILED_COUNT++))
        continue
    fi
    
    cd "$repo"
    
    # Check if workflow exists
    if [ ! -f .github/workflows/sync-from-template.yml ]; then
        echo "⚠️  No sync workflow in $repo"
        cd ../..
        rm -rf "$TEMP_DIR"
        continue
    fi
    
    # Copy the fixed workflow from template repo
    cp "$TEMPLATE_DIR/.github/workflows/sync-from-template.yml" .github/workflows/
    
    # Check if there are changes
    if ! git diff --quiet; then
        # Create branch
        BRANCH="emergency-fix-sync-workflow"
        git checkout -b "$BRANCH" 2>/dev/null || git checkout "$BRANCH"
        
        # Commit
        git add .github/workflows/sync-from-template.yml
        git commit -m "fix: emergency repair of sync workflow syntax

- Fixes 'Unexpected value Note' error on line 162
- Removes problematic heredoc syntax
- Uses simple one-line PR body instead
- Enables template sync to work again"
        
        # Push
        if git push origin "$BRANCH" --force 2>/dev/null; then
            # Create and merge PR
            PR_URL=$(gh pr create \
                --title "🚨 Emergency: Fix sync workflow syntax error" \
                --body "This emergency fix repairs the broken sync-from-template.yml workflow. After merging, template syncs will work again." \
                --base main \
                --head "$BRANCH" 2>/dev/null || echo "")
            
            if [ -n "$PR_URL" ]; then
                PR_NUMBER=$(echo "$PR_URL" | sed 's/.*\///')
                # Try to merge immediately
                if gh pr merge "$PR_NUMBER" --merge --admin 2>/dev/null; then
                    echo "✅ Fixed and merged PR for $repo"
                    ((SUCCESS_COUNT++))
                else
                    echo "✅ Created PR for $repo: $PR_URL"
                    ((SUCCESS_COUNT++))
                fi
            else
                # PR might already exist
                echo "⚠️  PR may already exist for $repo"
            fi
        else
            echo "❌ Failed to push fix for $repo"
            ((FAILED_COUNT++))
        fi
    else
        echo "✅ $repo already has the fixed workflow"
        ((SUCCESS_COUNT++))
    fi
    
    cd ../..
    rm -rf "$TEMP_DIR"
done

echo ""
echo "📊 Summary:"
echo "  - Successfully processed: $SUCCESS_COUNT repos"
echo "  - Failed: $FAILED_COUNT repos"
echo ""
echo "✅ Emergency fix complete!"