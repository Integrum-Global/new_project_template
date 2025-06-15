#!/bin/bash
# Force template sync by directly creating PRs in downstream repositories
# This bypasses the broken sync workflow in downstream repos

set -e

TEMPLATE_REPO="Integrum-Global/new_project_template"
TEMPLATE_BRANCH="main"

echo "🔍 Finding downstream repositories with kailash-template topic..."
REPOS=$(gh api "search/repositories?q=org:Integrum-Global+topic:kailash-template&per_page=100" --jq '.items[].name' | grep -v "new_project_template" || true)

REPO_COUNT=$(echo "$REPOS" | wc -l | tr -d ' ')
echo "📊 Found $REPO_COUNT downstream repositories"

SUCCESS_COUNT=0
FAILED_COUNT=0
SKIPPED_COUNT=0

for repo in $REPOS; do
    if [ -z "$repo" ]; then
        continue
    fi
    
    echo ""
    echo "🔄 Processing: $repo"
    
    # Check if PR already exists
    EXISTING_PR=$(gh pr list -R "Integrum-Global/$repo" --search "Sync template updates in:title" --state open --json number --jq '.[0].number' 2>/dev/null || echo "")
    
    if [ -n "$EXISTING_PR" ]; then
        echo "⚠️  Skipping $repo - PR #$EXISTING_PR already exists"
        ((SKIPPED_COUNT++))
        continue
    fi
    
    # Clone the repo in a temp directory
    TEMP_DIR=$(mktemp -d)
    trap "rm -rf $TEMP_DIR" EXIT
    
    cd "$TEMP_DIR"
    
    if ! gh repo clone "Integrum-Global/$repo" -- --depth 1 2>/dev/null; then
        echo "❌ Failed to clone $repo"
        ((FAILED_COUNT++))
        continue
    fi
    
    cd "$repo"
    
    # Add template remote and fetch
    git remote add template "https://github.com/$TEMPLATE_REPO.git"
    git fetch template main --depth 1
    
    # Create sync branch
    BRANCH_NAME="template-sync-$(date +%Y%m%d-%H%M%S)"
    git checkout -b "$BRANCH_NAME"
    
    # Sync critical files that need immediate update
    SYNC_FILES=(
        ".github/workflows/sync-from-template.yml"
        "sdk-users"
        "CLAUDE.md"
        "deployment"
    )
    
    # Sync each file/directory
    for item in "${SYNC_FILES[@]}"; do
        if git ls-tree template/main --name-only | grep -q "^$item"; then
            echo "  Syncing: $item"
            git checkout template/main -- "$item" 2>/dev/null || true
        fi
    done
    
    # Check if there are changes
    if [[ -n $(git status --porcelain) ]]; then
        git add -A
        git commit -m "fix: sync critical template updates including workflow fix

- Fix sync-from-template.yml workflow syntax error
- Update sdk-users documentation
- Update CLAUDE.md development patterns
- Add deployment directory if missing

This manual sync fixes the broken workflow to enable automatic syncs."
        
        # Push and create PR
        if git push origin HEAD 2>/dev/null; then
            if gh pr create \
                --title "🔧 Fix: Sync template updates and repair workflow" \
                --body "## 🚨 Critical Template Sync

This PR fixes the broken sync workflow and brings critical template updates.

### 🔧 Fixed Issues:
- **Workflow syntax error** in sync-from-template.yml that was preventing automatic syncs
- **Missing deployment directory** now included in sync

### 🔄 What was synced:
- **.github/workflows/sync-from-template.yml** - Fixed workflow syntax
- **sdk-users/** - Latest SDK documentation
- **CLAUDE.md** - Latest development patterns
- **deployment/** - Deployment configurations (if missing)

### ✅ After merging:
- Automatic template syncs will work again
- Future updates will be delivered via automated PRs
- Your custom code remains untouched

**Please merge this PR to restore automatic template synchronization.**" \
                --base main 2>/dev/null; then
                echo "✅ Successfully created PR for $repo"
                ((SUCCESS_COUNT++))
            else
                echo "❌ Failed to create PR for $repo"
                ((FAILED_COUNT++))
            fi
        else
            echo "❌ Failed to push changes for $repo"
            ((FAILED_COUNT++))
        fi
    else
        echo "⚠️  No changes needed for $repo"
        ((SKIPPED_COUNT++))
    fi
    
    cd ../..
    rm -rf "$TEMP_DIR"
done

echo ""
echo "📊 Summary:"
echo "  - Successfully created PRs: $SUCCESS_COUNT"
echo "  - Failed: $FAILED_COUNT"
echo "  - Skipped (no changes/existing PR): $SKIPPED_COUNT"
echo ""
echo "💡 Next steps:"
echo "  1. Visit https://github.com/orgs/Integrum-Global/pulls to see all PRs"
echo "  2. Merge the PRs to fix the sync workflow"
echo "  3. Future syncs will happen automatically"