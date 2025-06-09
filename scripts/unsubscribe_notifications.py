#!/usr/bin/env python3
"""
Unsubscribe from notifications for all downstream repositories.
"""

import subprocess
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


def run_command(cmd: List[str], check=True):
    """Run a command and return the result."""
    result = subprocess.run(cmd, capture_output=True, text=True)
    if check and result.returncode != 0:
        print(f"Error running command: {' '.join(cmd)}")
        print(f"Error: {result.stderr}")
    return result


def get_subscription_status(repo: str) -> str:
    """Get current subscription status for a repository."""
    result = run_command(
        ["gh", "api", f"/repos/{repo}/subscription", "--jq", ".subscribed"], check=False
    )

    if result.returncode == 0:
        return result.stdout.strip()
    return "unknown"


def unsubscribe_from_repo(repo: str) -> bool:
    """Unsubscribe from notifications for a repository."""
    print(f"📌 Processing {repo}...")

    # Check current status
    status = get_subscription_status(repo)

    if status == "false":
        print("  ✅ Already unsubscribed")
        return False

    # Unsubscribe
    result = run_command(
        [
            "gh",
            "api",
            f"/repos/{repo}/subscription",
            "--method",
            "PUT",
            "-f",
            "subscribed=false",
            "-f",
            "ignored=true",
        ],
        check=False,
    )

    if result.returncode == 0:
        print("  ✅ Successfully unsubscribed")
        return True
    else:
        print("  ❌ Failed to unsubscribe")
        return False


def unwatch_repo(repo: str) -> bool:
    """Unwatch a repository (stop watching for all activity)."""
    result = run_command(
        ["gh", "api", f"/repos/{repo}/subscription", "--method", "DELETE"], check=False
    )

    if result.returncode == 0:
        print("  🚫 Stopped watching repository")
        return True
    return False


def main():
    """Main function to unsubscribe from all downstream repos."""
    print("🔕 Unsubscribing from notifications for all downstream repositories...")
    print(f"📋 Processing {len(DOWNSTREAM_REPOS)} repositories\n")

    unsubscribed = 0
    already_unsubscribed = 0
    failed = 0

    for repo in DOWNSTREAM_REPOS:
        try:
            # First try to unsubscribe (keep watching but no notifications)
            if unsubscribe_from_repo(repo):
                unsubscribed += 1
            else:
                already_unsubscribed += 1

            # Optionally, completely unwatch (uncomment if you want to stop watching entirely)
            # unwatch_repo(repo)

        except Exception as e:
            print(f"  ❌ Error: {e}")
            failed += 1

        print()  # Empty line between repos

    print("📊 Summary:")
    print(f"  ✅ Unsubscribed: {unsubscribed}")
    print(f"  ⏭️  Already unsubscribed: {already_unsubscribed}")
    print(f"  ❌ Failed: {failed}")

    print(
        "\n✨ Done! You will no longer receive notifications from these repositories."
    )
    print("💡 Note: You can still manually watch specific issues or PRs if needed.")


if __name__ == "__main__":
    main()
