#!/bin/bash
# Create CLAUDE.md fix PR for a specific repo

REPO=$1
if [ -z "$REPO" ]; then
    echo "Usage: $0 <owner/repo>"
    exit 1
fi

echo "Creating CLAUDE.md fix PR for $REPO..."

# Create a temporary directory
TMPDIR=$(mktemp -d)
cd $TMPDIR

# Clone the repo
gh repo clone $REPO repo -- --depth=1
cd repo

# Check if CLAUDE.md needs updating
if ! grep -q "guide/todos/000-master.md" CLAUDE.md; then
    echo "CLAUDE.md already has correct paths"
    cd ../..
    rm -rf $TMPDIR
    exit 0
fi

# Get the template CLAUDE.md
curl -s https://raw.githubusercontent.com/Integrum-Global/new_project_template/main/CLAUDE.md > CLAUDE_template.md

# Extract project-specific section if exists
if grep -q "## Project-Specific Instructions" CLAUDE.md; then
    # Extract everything after project-specific marker
    awk '/## Project-Specific Instructions/{p=1}p' CLAUDE.md > project_section.tmp
    
    # Get template content before project-specific section (if it has one)
    if grep -q "## Project-Specific Instructions" CLAUDE_template.md; then
        awk '/## Project-Specific Instructions/{exit}1' CLAUDE_template.md > template_before.tmp
    else
        cp CLAUDE_template.md template_before.tmp
    fi
    
    # Combine them
    cat template_before.tmp > CLAUDE.md
    echo "" >> CLAUDE.md
    cat project_section.tmp >> CLAUDE.md
    
    rm -f project_section.tmp template_before.tmp
else
    # No project-specific section, just use template
    cp CLAUDE_template.md CLAUDE.md
fi

# Create branch and commit
git checkout -b fix-claude-md-paths
git add CLAUDE.md
git commit -m "fix: update CLAUDE.md with correct todo and mistake paths

- Updated all references from guide/todos/ to todos/
- Updated all references from guide/mistakes/ to mistakes/  
- Preserved project-specific instructions section"

# Push and create PR
git push origin fix-claude-md-paths

gh pr create \
    --title "fix: update CLAUDE.md with correct todo and mistake paths" \
    --body "## Fix CLAUDE.md Path References

This PR updates all path references in CLAUDE.md to reflect the correct project structure:

### Changes:
- ✅ Updated \`guide/todos/\` → \`todos/\`
- ✅ Updated \`guide/mistakes/\` → \`mistakes/\`
- ✅ Updated \`guide/reference/\` → remains as is (correct location)
- ✅ Preserved project-specific instructions section

### Why this change:
The todos and mistakes directories are at the root level in downstream repos, but CLAUDE.md had outdated references to their previous location under guide/.

This is a one-time fix to ensure Claude Code uses the correct paths when working with your repository."

# Cleanup
cd ../..
rm -rf $TMPDIR

echo "✅ PR created successfully!"