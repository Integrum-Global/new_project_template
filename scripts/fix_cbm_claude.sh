#!/bin/bash

# Get the current CLAUDE.md from cbm
echo "Fetching current CLAUDE.md from cbm..."
gh api /repos/Integrum-Global/cbm/contents/CLAUDE.md --jq '.content' | base64 -d > cbm_claude_current.md

# Get our template CLAUDE.md
cp CLAUDE.md cbm_claude_template.md

# Extract project-specific section if it exists
if grep -q "## Project-Specific Instructions" cbm_claude_current.md; then
    echo "Found project-specific section, preserving it..."
    # Extract everything from project marker to end
    sed -n '/## Project-Specific Instructions/,$p' cbm_claude_current.md > cbm_project_section.tmp
    
    # Get template content before project marker
    if grep -q "## Project-Specific Instructions" cbm_claude_template.md; then
        sed '/## Project-Specific Instructions/,$d' cbm_claude_template.md > cbm_claude_new.md
    else
        cp cbm_claude_template.md cbm_claude_new.md
    fi
    
    # Append project section
    echo "" >> cbm_claude_new.md
    cat cbm_project_section.tmp >> cbm_claude_new.md
else
    echo "No project-specific section found, using template as-is..."
    cp cbm_claude_template.md cbm_claude_new.md
fi

# Show the changes
echo ""
echo "=== Key changes that will be made ==="
echo "Old paths being replaced:"
grep -n "guide/todos" cbm_claude_current.md | head -5
echo ""
echo "New paths in template:"
grep -n "todos/000" cbm_claude_new.md | head -5

# Clean up
rm -f cbm_claude_current.md cbm_claude_template.md cbm_project_section.tmp

echo ""
echo "✅ Analysis complete. The CLAUDE.md needs updating."
echo ""
echo "To create a fix PR manually:"
echo "1. Fork the cbm repository"
echo "2. Replace CLAUDE.md with the corrected content"
echo "3. Create a PR with the title: 'fix: update CLAUDE.md with correct todo and mistake paths'"