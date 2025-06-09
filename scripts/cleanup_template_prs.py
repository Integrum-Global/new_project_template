#!/usr/bin/env python3
"""
Template PR Cleanup Script

Finds all template sync PRs in downstream repositories and closes older ones,
keeping only the most recent PR in each repository.
"""

import subprocess
import json
from typing import List, Dict, Optional


def run_gh_command(cmd: List[str]) -> Optional[str]:
    """Run a GitHub CLI command and return the output."""
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        return result.stdout.strip()
    except subprocess.CalledProcessError as e:
        print(f"Error running command {' '.join(cmd)}: {e}")
        return None


def get_downstream_repos() -> List[str]:
    """Get list of downstream repositories with kailash-template topic."""
    print("🔍 Finding downstream repositories...")

    cmd = [
        "gh",
        "api",
        "--paginate",
        "/orgs/Integrum-Global/repos",
        "--jq",
        '.[] | select(.topics[]? | contains("kailash-template")) | .full_name',
    ]

    output = run_gh_command(cmd)
    if not output:
        return []

    repos = [r.strip() for r in output.split("\n") if r.strip()]
    # Exclude the template repo itself
    repos = [r for r in repos if r != "Integrum-Global/new_project_template"]

    print(f"Found {len(repos)} downstream repositories:")
    for repo in repos:
        print(f"  - {repo}")

    return repos


def get_template_sync_prs(repo: str) -> List[Dict]:
    """Get all template sync PRs for a repository."""
    print(f"\n🔍 Checking PRs in {repo}...")

    cmd = [
        "gh",
        "api",
        f"/repos/{repo}/pulls",
        "--jq",
        '.[] | select(.title | contains("Sync template")) | {number: .number, title: .title, created_at: .created_at, head_ref: .head.ref}',
    ]

    output = run_gh_command(cmd)
    if not output:
        return []

    prs = []
    for line in output.split("\n"):
        if line.strip():
            try:
                pr_data = json.loads(line)
                prs.append(pr_data)
            except json.JSONDecodeError:
                continue

    # Sort by creation date (newest first)
    prs.sort(key=lambda x: x["created_at"], reverse=True)

    print(f"Found {len(prs)} template sync PRs:")
    for i, pr in enumerate(prs):
        status = "🟢 KEEP" if i == 0 else "🔴 CLOSE"
        print(
            f"  {status} #{pr['number']}: {pr['title']} (created: {pr['created_at']})"
        )

    return prs


def close_pr(repo: str, pr_number: int, branch: str) -> bool:
    """Close a PR and delete its branch."""
    print(f"🗑️  Closing PR #{pr_number} in {repo}...")

    # Close the PR
    close_cmd = [
        "gh",
        "pr",
        "close",
        str(pr_number),
        "--repo",
        repo,
        "--comment",
        "Closing older template sync PR. Keeping only the latest sync.",
    ]

    if not run_gh_command(close_cmd):
        print(f"❌ Failed to close PR #{pr_number}")
        return False

    # Delete the branch
    delete_cmd = [
        "gh",
        "api",
        f"/repos/{repo}/git/refs/heads/{branch}",
        "--method",
        "DELETE",
    ]

    if not run_gh_command(delete_cmd):
        print(f"⚠️  Failed to delete branch {branch} (may not exist or already deleted)")

    print(f"✅ Closed PR #{pr_number}")
    return True


def cleanup_template_prs():
    """Main function to cleanup template sync PRs."""
    print("🧹 Starting template PR cleanup...\n")

    # Get downstream repositories
    repos = get_downstream_repos()
    if not repos:
        print("❌ No downstream repositories found")
        return

    total_closed = 0
    total_kept = 0

    # Process each repository
    for repo in repos:
        prs = get_template_sync_prs(repo)

        if not prs:
            print(f"✅ No template sync PRs in {repo}")
            continue

        if len(prs) == 1:
            print(f"✅ Only 1 PR in {repo} - keeping it")
            total_kept += 1
            continue

        # Close all PRs except the newest (first in sorted list)
        for i, pr in enumerate(prs):
            if i == 0:
                print(f"✅ Keeping latest PR #{pr['number']} in {repo}")
                total_kept += 1
            else:
                if close_pr(repo, pr["number"], pr["head_ref"]):
                    total_closed += 1

    print("\n🎉 Cleanup complete!")
    print("📊 Summary:")
    print(f"  - Repositories processed: {len(repos)}")
    print(f"  - PRs kept (latest): {total_kept}")
    print(f"  - PRs closed (older): {total_closed}")


if __name__ == "__main__":
    cleanup_template_prs()
