#!/usr/bin/env python3
"""
Force update CLAUDE.md in downstream repositories.

This script directly replaces CLAUDE.md content while preserving project-specific sections.
"""

import os
import subprocess
import tempfile
from pathlib import Path

# Template repository
TEMPLATE_REPO = "Integrum-Global/new_project_template"

# Downstream repositories to update
DOWNSTREAM_REPOS = [
    "Integrum-Global/ai_coaching",
    "Integrum-Global/tpc_core",
    "Integrum-Global/deal_sourcing",
    "Integrum-Global/market-insights",
    "Integrum-Global/cbm",
    "Integrum-Global/mcp_server",
    "Integrum-Global/GIC_update",
]


def get_github_token():
    """Get GitHub token from environment."""
    token = os.environ.get("GITHUB_TOKEN", "")
    if not token:
        print("Error: GITHUB_TOKEN environment variable not set")
        exit(1)
    return token


def update_claude_md(repo: str, token: str):
    """Force update CLAUDE.md in a downstream repository."""
    print(f"\n🔄 Updating CLAUDE.md in {repo}...")

    with tempfile.TemporaryDirectory() as tmpdir:
        repo_path = Path(tmpdir) / "repo"

        # Clone the repository
        print(f"  📥 Cloning {repo}...")
        subprocess.run(
            [
                "git",
                "clone",
                "--depth",
                "1",
                f"https://x-access-token:{token}@github.com/{repo}.git",
                str(repo_path),
            ],
            check=True,
            capture_output=True,
        )

        # Read the current CLAUDE.md
        claude_file = repo_path / "CLAUDE.md"
        if not claude_file.exists():
            print(f"  ❌ CLAUDE.md not found in {repo}")
            return False

        current_content = claude_file.read_text()

        # Check if it already has the correct paths
        if (
            "todos/000-master.md" in current_content
            and "guide/todos/000-master.md" not in current_content
        ):
            print(f"  ✅ CLAUDE.md already has correct paths in {repo}")
            return False

        # Get the template CLAUDE.md content
        template_claude = Path(__file__).parent.parent / "CLAUDE.md"
        if not template_claude.exists():
            print("  ❌ Template CLAUDE.md not found")
            return False

        template_content = template_claude.read_text()

        # Extract project-specific section if it exists
        project_marker = "## Project-Specific Instructions"
        project_section = ""

        if project_marker in current_content:
            idx = current_content.find(project_marker)
            project_section = current_content[idx:]

        # Combine template content with project-specific section
        if project_marker in template_content:
            # Replace template's project section with downstream's
            idx = template_content.find(project_marker)
            new_content = template_content[:idx].rstrip() + "\n\n" + project_section
        else:
            # Append project section to template
            new_content = template_content.rstrip() + "\n\n" + project_section

        # Write the updated content
        claude_file.write_text(new_content)

        # Create branch and commit
        os.chdir(repo_path)
        branch_name = "fix-claude-md-paths"

        subprocess.run(["git", "checkout", "-b", branch_name], check=True)
        subprocess.run(["git", "add", "CLAUDE.md"], check=True)
        subprocess.run(
            [
                "git",
                "commit",
                "-m",
                "fix: update CLAUDE.md with correct todo and mistake paths\n\n"
                "- Updated all references from guide/todos/ to todos/\n"
                "- Updated all references from guide/mistakes/ to mistakes/\n"
                "- Preserved project-specific instructions section",
            ],
            check=True,
        )

        # Push the branch
        subprocess.run(["git", "push", "origin", branch_name], check=True)

        # Create PR
        print(f"  📝 Creating PR in {repo}...")
        subprocess.run(
            [
                "gh",
                "pr",
                "create",
                "--repo",
                repo,
                "--head",
                branch_name,
                "--base",
                "main",
                "--title",
                "fix: update CLAUDE.md with correct todo and mistake paths",
                "--body",
                """## Fix CLAUDE.md Path References

This PR updates all path references in CLAUDE.md to reflect the correct project structure:

### Changes:
- ✅ Updated `guide/todos/` → `todos/`
- ✅ Updated `guide/mistakes/` → `mistakes/`
- ✅ Updated `guide/reference/` → remains as is (correct location)
- ✅ Preserved project-specific instructions section

### Why this change:
The todos and mistakes directories are at the root level in downstream repos, but CLAUDE.md had outdated references to their previous location under guide/.

This is a one-time fix to ensure Claude Code uses the correct paths when working with your repository.
""",
            ],
            check=True,
        )

        print(f"  ✅ Successfully created PR for {repo}")
        return True


def main():
    """Main function to update all downstream repos."""
    token = get_github_token()

    print("🚀 Starting CLAUDE.md force update for all downstream repositories...")

    updated = 0
    skipped = 0
    failed = 0

    for repo in DOWNSTREAM_REPOS:
        try:
            if update_claude_md(repo, token):
                updated += 1
            else:
                skipped += 1
        except Exception as e:
            print(f"  ❌ Failed to update {repo}: {e}")
            failed += 1

    print("\n📊 Summary:")
    print(f"  - Updated: {updated}")
    print(f"  - Skipped (already correct): {skipped}")
    print(f"  - Failed: {failed}")


if __name__ == "__main__":
    main()
