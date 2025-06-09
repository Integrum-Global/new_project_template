#!/usr/bin/env python3
"""
Rename Claude.md to CLAUDE.md in all downstream repositories.
"""

import subprocess
import json
from typing import List

# Downstream repositories
DOWNSTREAM_REPOS = [
    "Integrum-Global/ai_coaching",
    "Integrum-Global/tpc_core",
    "Integrum-Global/deal_sourcing",
    "Integrum-Global/market-insights",
    "Integrum-Global/cbm",
    "Integrum-Global/mcp_server",
    "Integrum-Global/GIC_update",
]


def run_command(cmd: List[str], capture=True) -> str:
    """Run a command and return output."""
    if capture:
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            print(f"Error: {result.stderr}")
        return result.stdout.strip()
    else:
        subprocess.run(cmd)
        return ""


def check_file_exists(repo: str, filename: str) -> bool:
    """Check if a file exists in the repository."""
    cmd = ["gh", "api", f"/repos/{repo}/contents/{filename}"]
    result = subprocess.run(cmd, capture_output=True)
    return result.returncode == 0


def rename_claude_file(repo: str) -> bool:
    """Rename Claude.md to CLAUDE.md in a repository."""
    print(f"\n🔄 Processing {repo}...")

    # Check if Claude.md exists
    has_claude = check_file_exists(repo, "Claude.md")
    has_claude_upper = check_file_exists(repo, "CLAUDE.md")

    if not has_claude and has_claude_upper:
        print("  ✅ Already has CLAUDE.md (uppercase)")
        return False

    if not has_claude and not has_claude_upper:
        print("  ❌ No Claude.md or CLAUDE.md found")
        return False

    if has_claude and has_claude_upper:
        print("  ⚠️  Both Claude.md and CLAUDE.md exist - needs manual review")
        return False

    # Get file content and SHA
    print("  📥 Fetching Claude.md content...")
    cmd = ["gh", "api", f"/repos/{repo}/contents/Claude.md"]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print("  ❌ Failed to fetch Claude.md")
        return False

    file_data = json.loads(result.stdout)
    content = file_data["content"]
    sha = file_data["sha"]

    # Get default branch
    cmd = ["gh", "api", f"/repos/{repo}", "--jq", ".default_branch"]
    default_branch = run_command(cmd).strip() or "main"

    # Create a new branch
    branch_name = "rename-claude-to-uppercase"
    print(f"  🌿 Creating branch {branch_name}...")

    # Get the latest commit SHA from default branch
    cmd = [
        "gh",
        "api",
        f"/repos/{repo}/git/refs/heads/{default_branch}",
        "--jq",
        ".object.sha",
    ]
    base_sha = run_command(cmd).strip()

    if not base_sha:
        print("  ❌ Failed to get base commit SHA")
        return False

    # Create new branch
    cmd = [
        "gh",
        "api",
        f"/repos/{repo}/git/refs",
        "-X",
        "POST",
        "-f",
        f"ref=refs/heads/{branch_name}",
        "-f",
        f"sha={base_sha}",
    ]
    result = subprocess.run(cmd, capture_output=True)

    # If branch already exists, delete it and recreate
    if result.returncode != 0:
        print("  🗑️  Deleting existing branch...")
        cmd = [
            "gh",
            "api",
            f"/repos/{repo}/git/refs/heads/{branch_name}",
            "-X",
            "DELETE",
        ]
        run_command(cmd)

        # Try creating again
        cmd = [
            "gh",
            "api",
            f"/repos/{repo}/git/refs",
            "-X",
            "POST",
            "-f",
            f"ref=refs/heads/{branch_name}",
            "-f",
            f"sha={base_sha}",
        ]
        result = subprocess.run(cmd, capture_output=True)
        if result.returncode != 0:
            print("  ❌ Failed to create branch")
            return False

    # Create CLAUDE.md with same content
    print("  📝 Creating CLAUDE.md...")
    cmd = [
        "gh",
        "api",
        f"/repos/{repo}/contents/CLAUDE.md",
        "-X",
        "PUT",
        "-f",
        "message=rename: Claude.md to CLAUDE.md for consistency",
        "-f",
        f"content={content}",
        "-f",
        f"branch={branch_name}",
    ]
    result = subprocess.run(cmd, capture_output=True)
    if result.returncode != 0:
        print("  ❌ Failed to create CLAUDE.md")
        return False

    # Delete Claude.md
    print("  🗑️  Deleting Claude.md...")
    cmd = [
        "gh",
        "api",
        f"/repos/{repo}/contents/Claude.md",
        "-X",
        "DELETE",
        "-f",
        "message=rename: remove old Claude.md (now CLAUDE.md)",
        "-f",
        f"sha={sha}",
        "-f",
        f"branch={branch_name}",
    ]
    result = subprocess.run(cmd, capture_output=True)
    if result.returncode != 0:
        print("  ❌ Failed to delete Claude.md")
        return False

    # Create PR
    print("  📋 Creating pull request...")
    cmd = [
        "gh",
        "pr",
        "create",
        "--repo",
        repo,
        "--head",
        branch_name,
        "--base",
        default_branch,
        "--title",
        "rename: Claude.md to CLAUDE.md for consistency",
        "--body",
        """## Rename Claude.md to CLAUDE.md

This PR renames the Claude instructions file from `Claude.md` to `CLAUDE.md` for consistency across all repositories.

### Changes:
- 📝 Renamed `Claude.md` → `CLAUDE.md`
- ✅ Content remains exactly the same
- 🔄 Maintains all existing instructions and customizations

### Why this change:
Standardizing on `CLAUDE.md` (uppercase) across all repositories for consistency with the template repository naming convention.

This is a simple file rename with no content changes.""",
    ]

    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"  ❌ Failed to create PR: {result.stderr}")
        return False

    # Extract PR URL from output
    pr_url = result.stdout.strip()
    print(f"  ✅ Created PR: {pr_url}")
    return True


def main():
    """Main function."""
    print("🚀 Starting Claude.md → CLAUDE.md rename process...")

    success_count = 0
    skip_count = 0
    fail_count = 0

    for repo in DOWNSTREAM_REPOS:
        try:
            if rename_claude_file(repo):
                success_count += 1
            else:
                skip_count += 1
        except Exception as e:
            print(f"  ❌ Error processing {repo}: {e}")
            fail_count += 1

    print("\n📊 Summary:")
    print(f"  ✅ PRs created: {success_count}")
    print(f"  ⏭️  Skipped: {skip_count}")
    print(f"  ❌ Failed: {fail_count}")
    print("\n✨ Process complete!")


if __name__ == "__main__":
    main()
