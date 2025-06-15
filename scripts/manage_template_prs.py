#!/usr/bin/env python3
"""
Manage template sync PRs across downstream repositories.
This script can list, merge, or delete template sync PRs.
"""

import subprocess
import json
import sys
from typing import List, Dict, Optional
import argparse
from datetime import datetime

def run_command(cmd: List[str]) -> Optional[str]:
    """Run a command and return output."""
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        return result.stdout.strip()
    except subprocess.CalledProcessError as e:
        print(f"Error running {' '.join(cmd)}: {e.stderr}")
        return None

def get_downstream_repos() -> List[str]:
    """Get list of downstream repositories."""
    # Get all non-template repos from the organization
    cmd = [
        "gh", "repo", "list", "Integrum-Global", 
        "--limit", "100", 
        "--json", "name,isTemplate"
    ]
    
    output = run_command(cmd)
    if not output:
        return []
    
    repos = json.loads(output)
    # Filter out template repo and return only non-template repos
    return [r['name'] for r in repos if not r['isTemplate'] and r['name'] != 'new_project_template']

def get_template_sync_prs(repo: str) -> List[Dict]:
    """Get all template sync PRs for a repository."""
    cmd = [
        "gh", "pr", "list",
        "--repo", f"Integrum-Global/{repo}",
        "--state", "open",
        "--json", "number,title,author,createdAt,headRefName,body",
        "--limit", "100"
    ]
    
    output = run_command(cmd)
    if not output:
        return []
    
    prs = json.loads(output)
    
    # Filter for template sync PRs
    template_prs = []
    for pr in prs:
        title = pr.get('title', '')
        body = pr.get('body', '')
        branch = pr.get('headRefName', '')
        
        # Check various indicators of template sync
        is_template_sync = (
            'Sync template updates' in title or
            'template-sync-' in branch or
            'Automated template sync from' in body or
            'What was synced (always replaced)' in body or
            'This PR automatically syncs updates from the template repository' in body
        )
        
        if is_template_sync:
            template_prs.append(pr)
    
    return template_prs

def merge_pr(repo: str, pr_number: int) -> bool:
    """Merge a PR."""
    cmd = [
        "gh", "pr", "merge", str(pr_number),
        "--repo", f"Integrum-Global/{repo}",
        "--merge",
        "--delete-branch"
    ]
    
    result = run_command(cmd)
    return result is not None

def close_pr(repo: str, pr_number: int) -> bool:
    """Close a PR without merging."""
    cmd = [
        "gh", "pr", "close", str(pr_number),
        "--repo", f"Integrum-Global/{repo}",
        "--comment", "Closing outdated template sync PR. A newer sync is available."
    ]
    
    result = run_command(cmd)
    return result is not None

def process_repo_prs(repo: str, action: str) -> None:
    """Process all template sync PRs for a repository."""
    prs = get_template_sync_prs(repo)
    
    if not prs:
        return
    
    print(f"\n📦 {repo}: Found {len(prs)} template sync PR(s)")
    
    # Sort PRs by creation date (newest first)
    prs.sort(key=lambda x: x['createdAt'], reverse=True)
    
    for i, pr in enumerate(prs):
        pr_date = datetime.fromisoformat(pr['createdAt'].replace('Z', '+00:00'))
        age_days = (datetime.now(pr_date.tzinfo) - pr_date).days
        
        print(f"  PR #{pr['number']}: {pr['title'][:60]}...")
        print(f"    Created: {pr['createdAt']} ({age_days} days ago)")
        print(f"    Branch: {pr['headRefName']}")
        
        if action == 'list':
            continue
        elif action == 'merge-latest':
            if i == 0:  # Only merge the most recent PR
                print(f"    ✅ Merging latest PR...")
                if merge_pr(repo, pr['number']):
                    print(f"    ✅ Successfully merged PR #{pr['number']}")
                else:
                    print(f"    ❌ Failed to merge PR #{pr['number']}")
            else:
                print(f"    🗑️  Closing older PR...")
                if close_pr(repo, pr['number']):
                    print(f"    ✅ Successfully closed PR #{pr['number']}")
                else:
                    print(f"    ❌ Failed to close PR #{pr['number']}")
        elif action == 'close-all':
            print(f"    🗑️  Closing PR...")
            if close_pr(repo, pr['number']):
                print(f"    ✅ Successfully closed PR #{pr['number']}")
            else:
                print(f"    ❌ Failed to close PR #{pr['number']}")

def main():
    parser = argparse.ArgumentParser(description='Manage template sync PRs')
    parser.add_argument(
        'action',
        choices=['list', 'merge-latest', 'close-all'],
        help='Action to perform on template sync PRs'
    )
    parser.add_argument(
        '--repo',
        help='Process only a specific repository'
    )
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Show what would be done without actually doing it'
    )
    
    args = parser.parse_args()
    
    if args.dry_run and args.action != 'list':
        print("🔍 DRY RUN MODE - No changes will be made")
        args.action = 'list'
    
    # Get repos to process
    if args.repo:
        repos = [args.repo]
    else:
        print("🔍 Fetching downstream repositories...")
        repos = get_downstream_repos()
        print(f"📊 Found {len(repos)} repositories to check")
    
    # Process each repo
    total_prs = 0
    repos_with_prs = 0
    
    for repo in repos:
        prs = get_template_sync_prs(repo)
        if prs:
            repos_with_prs += 1
            total_prs += len(prs)
            process_repo_prs(repo, args.action)
    
    # Summary
    print(f"\n📊 Summary:")
    print(f"  - Checked {len(repos)} repositories")
    print(f"  - Found {total_prs} template sync PRs in {repos_with_prs} repositories")
    
    if args.action == 'merge-latest':
        print(f"  - Merged {repos_with_prs} PRs (latest in each repo)")
        print(f"  - Closed {total_prs - repos_with_prs} older PRs")
    elif args.action == 'close-all':
        print(f"  - Closed all {total_prs} PRs")

if __name__ == "__main__":
    main()