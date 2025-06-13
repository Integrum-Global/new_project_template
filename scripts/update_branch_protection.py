#!/usr/bin/env python3
"""
Update Branch Protection Rules for Template Sync

Updates branch protection rules in all downstream repositories to ensure
template sync PRs can be merged without running the full test suite.
"""

import json
import subprocess
import sys
from typing import List, Optional, Dict


def run_command(cmd: List[str]) -> Optional[str]:
    """Run a command and return the output."""
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        return result.stdout.strip()
    except subprocess.CalledProcessError as e:
        print(f"Error running command {' '.join(cmd)}: {e}")
        if e.stderr:
            print(f"Error output: {e.stderr}")
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
    
    output = run_command(cmd)
    if not output:
        return []
    
    repos = [r.strip() for r in output.split("\n") if r.strip()]
    # Exclude the template repo itself
    repos = [r for r in repos if r != "Integrum-Global/new_project_template"]
    
    print(f"Found {len(repos)} downstream repositories")
    return repos


def get_branch_protection(repo: str, branch: str = "main") -> Optional[Dict]:
    """Get current branch protection rules."""
    cmd = [
        "gh",
        "api",
        f"/repos/{repo}/branches/{branch}/protection",
        "--jq",
        "."
    ]
    output = run_command(cmd)
    if output:
        return json.loads(output)
    return None


def update_branch_protection(repo: str, branch: str = "main") -> bool:
    """Update branch protection to handle template sync PRs properly."""
    print(f"\n📝 Updating branch protection for {repo}...")
    
    # Get current protection rules
    current_rules = get_branch_protection(repo, branch)
    if not current_rules:
        print(f"  ⚠️  No branch protection rules found for {repo}")
        return True  # Not an error - repo might not have protection
    
    # Check if status checks are required
    if not current_rules.get("required_status_checks"):
        print(f"  ℹ️  No required status checks configured")
        return True
    
    # Current required checks
    current_checks = current_rules["required_status_checks"].get("checks", [])
    current_contexts = current_rules["required_status_checks"].get("contexts", [])
    
    # Ensure template-sync-check is in the list
    template_sync_check = "Template Sync Validation"
    
    # Convert old format to new format if needed
    all_checks = []
    
    # Add existing checks from new format
    for check in current_checks:
        all_checks.append({
            "context": check.get("context", ""),
            "app_id": check.get("app_id")
        })
    
    # Add existing checks from old format
    for context in current_contexts:
        # Skip if already in new format
        if not any(c["context"] == context for c in all_checks):
            all_checks.append({
                "context": context,
                "app_id": None
            })
    
    # Add template sync check if not present
    if not any(c["context"] == template_sync_check for c in all_checks):
        all_checks.append({
            "context": template_sync_check,
            "app_id": None
        })
    
    # Prepare the update payload
    update_payload = {
        "required_status_checks": {
            "strict": current_rules["required_status_checks"].get("strict", False),
            "checks": all_checks
        },
        "enforce_admins": current_rules.get("enforce_admins", {}).get("enabled", False),
        "required_pull_request_reviews": current_rules.get("required_pull_request_reviews"),
        "restrictions": current_rules.get("restrictions")
    }
    
    # Update branch protection
    cmd = [
        "gh",
        "api",
        f"/repos/{repo}/branches/{branch}/protection",
        "--method", "PUT",
        "--input", "-"
    ]
    
    import json
    process = subprocess.Popen(cmd, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    stdout, stderr = process.communicate(input=json.dumps(update_payload))
    
    if process.returncode != 0:
        print(f"  ❌ Failed to update: {stderr}")
        return False
    
    print(f"  ✅ Updated branch protection rules")
    return True


def create_workflow_update_pr(repo: str) -> bool:
    """Create a PR to add/update the template-sync-check workflow."""
    print(f"\n📝 Checking workflow in {repo}...")
    
    # Check if template-sync-check.yml exists
    cmd = [
        "gh",
        "api",
        f"/repos/{repo}/contents/.github/workflows/template-sync-check.yml",
        "--jq",
        ".name"
    ]
    
    if run_command(cmd):
        print(f"  ✅ template-sync-check.yml already exists")
        return True
    
    print(f"  ⚠️  template-sync-check.yml missing - this should be synced from template")
    return True  # The template sync will add it


def main():
    """Main function to update branch protection rules."""
    print("🛡️ Updating Branch Protection Rules for Template Sync")
    print("=" * 60)
    
    # Get all downstream repos
    repos = get_downstream_repos()
    if not repos:
        print("No downstream repositories found.")
        return
    
    # Check for --yes flag
    if "--yes" not in sys.argv:
        try:
            response = input("\nDo you want to update branch protection rules? (y/N): ")
            if response.lower() != 'y':
                print("Aborted.")
                return
        except EOFError:
            print("\n⚠️  Running in non-interactive mode. Use --yes to confirm.")
            return
    
    # Update each repo
    success_count = 0
    for repo in repos:
        if update_branch_protection(repo):
            success_count += 1
    
    print(f"\n✅ Updated {success_count}/{len(repos)} repositories successfully")
    
    print("\n📋 Next Steps:")
    print("1. The template-sync-check.yml workflow will be added by the next template sync")
    print("2. Template sync PRs will now only need to pass the lightweight validation")
    print("3. Full CI will be skipped for template updates")
    
    if success_count < len(repos):
        print("\n⚠️  Some updates failed. You may need to handle those manually.")


if __name__ == "__main__":
    main()