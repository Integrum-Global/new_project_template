#!/bin/bash
# Script to link an existing repository to the template

set -e

# Check if repo name is provided
if [ -z "$1" ]; then
    echo "Usage: ./link-existing-repo.sh <repo-name>"
    echo "Example: ./link-existing-repo.sh ai_coaching"
    exit 1
fi

REPO_NAME=$1
ORG_NAME="Integrum-Global"
TEMPLATE_REPO="${ORG_NAME}/new_project_template"

echo "Linking ${REPO_NAME} to template ${TEMPLATE_REPO}..."

# Clone the repo if not already cloned
if [ ! -d "$REPO_NAME" ]; then
    echo "Cloning ${ORG_NAME}/${REPO_NAME}..."
    git clone "https://github.com/${ORG_NAME}/${REPO_NAME}.git"
fi

cd "$REPO_NAME"

# Add template remote
echo "Adding template remote..."
git remote add template "https://github.com/${TEMPLATE_REPO}.git" 2>/dev/null || echo "Template remote already exists"
git fetch template main

# Get essential files from template
echo "Getting sync workflow and CODEOWNERS..."
git checkout template/main -- .github/workflows/sync-from-template.yml
git checkout template/main -- .github/CODEOWNERS

# Get other useful template files (optional)
echo "Getting reference documentation..."
git checkout template/main -- reference/ 2>/dev/null || echo "Reference folder will be created on first sync"

# Create .github folder if it doesn't exist
mkdir -p .github

# Check if there are changes
if [[ -n $(git status --porcelain) ]]; then
    echo "Committing changes..."
    git add .
    git commit -m "Link repository to template ${TEMPLATE_REPO}

- Add template sync workflow
- Add CODEOWNERS for .github protection
- Template updates will now sync automatically"

    echo "Pushing to GitHub..."
    git push

    echo "✅ Success! ${REPO_NAME} is now linked to the template."
    echo ""
    echo "Next steps:"
    echo "1. Add ${ORG_NAME}/${REPO_NAME} to DOWNSTREAM_REPOS in template settings"
    echo "2. Template sync will run automatically:"
    echo "   - Daily at 3:30am SGT"
    echo "   - Or manually: Go to Actions → 'Sync from Template' → Run workflow"
else
    echo "✅ Repository already has template sync configured!"
fi

cd ..
