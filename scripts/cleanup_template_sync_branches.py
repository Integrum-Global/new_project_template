#!/usr/bin/env python3
"""
Clean up obsolete template-sync branches from downstream repositories.
This script finds and removes old template-sync-* branches that are no longer needed.
"""

import subprocess
import json
import sys
from typing import List, Dict, Optional
import argparse
from datetime import datetime, timezone
import re

def run_command(cmd: List[str]) -> Optional[str]:
    """Run a command and return output."""
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        return result.stdout.strip()
    except subprocess.CalledProcessError as e:
        print(f"Error running {' '.join(cmd)}: {e.stderr}")
        return None

def get_downstream_repos() -> List[str]:
    """Get list of downstream repositories with kailash-template topic."""
    cmd = [
        "gh", "search", "repos",
        "org:Integrum-Global topic:kailash-template",
        "--limit", "100",
        "--json", "name"
    ]
    
    output = run_command(cmd)
    if not output:
        return []
    
    repos = json.loads(output)
    # Filter out the template repo itself
    return [r['name'] for r in repos if r['name'] not in ['new_project_template', 'kailash_python_sdk']]

def get_template_sync_branches(repo: str) -> List[Dict]:
    """Get all template-sync branches for a repository."""
    # Get all branches
    cmd = [
        "gh", "api",
        f"/repos/Integrum-Global/{repo}/branches",
        "--paginate",
        "-q", ".[].name"
    ]
    
    output = run_command(cmd)
    if not output:
        return []
    
    all_branches = output.strip().split('\n') if output else []
    
    # Filter for template-sync branches
    template_branches = []
    for branch in all_branches:
        # Match template-sync-YYYYMMDD-HHMMSS pattern or just template-sync
        if branch.startswith('template-sync'):
            # Get branch details including last commit date
            detail_cmd = [
                "gh", "api",
                f"/repos/Integrum-Global/{repo}/branches/{branch}"
            ]
            detail_output = run_command(detail_cmd)
            if detail_output:
                branch_data = json.loads(detail_output)
                commit_date = branch_data['commit']['commit']['committer']['date']
                template_branches.append({
                    'name': branch,
                    'last_commit_date': commit_date,
                    'protected': branch_data.get('protected', False)
                })
    
    return template_branches

def check_pr_for_branch(repo: str, branch: str) -> bool:
    """Check if there's an open PR for this branch."""
    cmd = [
        "gh", "pr", "list",
        "--repo", f"Integrum-Global/{repo}",
        "--head", branch,
        "--state", "open",
        "--json", "number"
    ]
    
    output = run_command(cmd)
    if output:
        prs = json.loads(output)
        return len(prs) > 0
    return False

def delete_branch(repo: str, branch: str) -> bool:
    """Delete a branch from the repository."""
    cmd = [
        "gh", "api",
        "--method", "DELETE",
        f"/repos/Integrum-Global/{repo}/git/refs/heads/{branch}"
    ]
    
    result = run_command(cmd)
    return result is not None

def process_repo_branches(repo: str, dry_run: bool = False, age_days: int = 7) -> Dict:
    """Process all template-sync branches for a repository."""
    branches = get_template_sync_branches(repo)
    
    if not branches:
        return {'total': 0, 'deleted': 0, 'kept': 0}
    
    print(f"\n📦 {repo}: Found {len(branches)} template-sync branch(es)")
    
    # Sort branches by last commit date (newest first)
    branches.sort(key=lambda x: x['last_commit_date'], reverse=True)
    
    stats = {'total': len(branches), 'deleted': 0, 'kept': 0}
    
    for branch in branches:
        branch_date = datetime.fromisoformat(branch['last_commit_date'].replace('Z', '+00:00'))
        branch_age_days = (datetime.now(timezone.utc) - branch_date).days
        
        print(f"  🌿 {branch['name']}")
        print(f"    Last commit: {branch['last_commit_date']} ({branch_age_days} days ago)")
        
        # Determine if branch should be deleted
        should_delete = False
        reason = ""
        
        if branch['protected']:
            reason = "Protected branch"
        elif check_pr_for_branch(repo, branch['name']):
            reason = "Has open PR"
        elif branch['name'] == 'template-sync':
            # Keep the main template-sync branch
            reason = "Main template-sync branch"
        elif branch_age_days < age_days:
            reason = f"Too recent (< {age_days} days)"
        else:
            should_delete = True
            reason = f"Obsolete (> {age_days} days old)"
        
        if should_delete:
            if dry_run:
                print(f"    🗑️  Would delete: {reason}")
                stats['deleted'] += 1
            else:
                print(f"    🗑️  Deleting: {reason}")
                if delete_branch(repo, branch['name']):
                    print(f"    ✅ Successfully deleted")
                    stats['deleted'] += 1
                else:
                    print(f"    ❌ Failed to delete")
                    stats['kept'] += 1
        else:
            print(f"    ✅ Keeping: {reason}")
            stats['kept'] += 1
    
    return stats

def main():
    parser = argparse.ArgumentParser(description='Clean up obsolete template-sync branches')
    parser.add_argument(
        '--repo',
        help='Process only a specific repository'
    )
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Show what would be done without actually doing it'
    )
    parser.add_argument(
        '--age-days',
        type=int,
        default=7,
        help='Delete branches older than this many days (default: 7)'
    )
    parser.add_argument(
        '--include-main-branch',
        action='store_true',
        help='Also consider deleting the main template-sync branch if obsolete'
    )
    
    args = parser.parse_args()
    
    if args.dry_run:
        print("🔍 DRY RUN MODE - No branches will be deleted")
    
    # Get repos to process
    if args.repo:
        repos = [args.repo]
    else:
        print("🔍 Fetching downstream repositories...")
        repos = get_downstream_repos()
        print(f"📊 Found {len(repos)} repositories with kailash-template topic")
    
    # Process each repo
    total_stats = {'total': 0, 'deleted': 0, 'kept': 0}
    repos_with_branches = 0
    
    for repo in repos:
        stats = process_repo_branches(repo, args.dry_run, args.age_days)
        if stats['total'] > 0:
            repos_with_branches += 1
            total_stats['total'] += stats['total']
            total_stats['deleted'] += stats['deleted']
            total_stats['kept'] += stats['kept']
    
    # Summary
    print(f"\n📊 Summary:")
    print(f"  - Checked {len(repos)} repositories")
    print(f"  - Found {total_stats['total']} template-sync branches in {repos_with_branches} repositories")
    if args.dry_run:
        print(f"  - Would delete {total_stats['deleted']} obsolete branches")
        print(f"  - Would keep {total_stats['kept']} branches")
    else:
        print(f"  - Deleted {total_stats['deleted']} obsolete branches")
        print(f"  - Kept {total_stats['kept']} branches")

if __name__ == "__main__":
    main()