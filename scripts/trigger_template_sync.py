#!/usr/bin/env python3
"""
Trigger template sync workflow across downstream repositories.
This script can trigger the sync-from-template.yml workflow in multiple repos at once.
"""

import subprocess
import json
import sys
import time
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
    """Get list of downstream repositories with the kailash-template topic."""
    # Get all repos with the kailash-template topic
    cmd = [
        "gh", "repo", "list", "Integrum-Global", 
        "--limit", "100", 
        "--topic", "kailash-template",
        "--json", "name"
    ]
    
    output = run_command(cmd)
    if not output:
        # Fallback to getting all non-template repos
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
        return [r['name'] for r in repos if not r.get('isTemplate', False) and r['name'] != 'new_project_template']
    
    repos = json.loads(output)
    return [r['name'] for r in repos if r['name'] != 'new_project_template']

def check_workflow_exists(repo: str) -> bool:
    """Check if sync-from-template workflow exists in the repository."""
    cmd = [
        "gh", "workflow", "list",
        "--repo", f"Integrum-Global/{repo}",
        "--json", "name,path"
    ]
    
    output = run_command(cmd)
    if not output:
        return False
    
    workflows = json.loads(output)
    for workflow in workflows:
        if 'sync-from-template.yml' in workflow.get('path', ''):
            return True
    
    return False

def trigger_sync_workflow(repo: str, create_pr: bool = True) -> bool:
    """Trigger the sync-from-template workflow for a repository."""
    cmd = [
        "gh", "workflow", "run", "sync-from-template.yml",
        "--repo", f"Integrum-Global/{repo}",
        "-f", f"create_pr={str(create_pr).lower()}"
    ]
    
    result = run_command(cmd)
    return result is not None

def get_latest_workflow_run(repo: str) -> Optional[Dict]:
    """Get the latest workflow run for sync-from-template."""
    cmd = [
        "gh", "run", "list",
        "--repo", f"Integrum-Global/{repo}",
        "--workflow", "sync-from-template.yml",
        "--limit", "1",
        "--json", "status,conclusion,createdAt,databaseId"
    ]
    
    output = run_command(cmd)
    if not output:
        return None
    
    runs = json.loads(output)
    return runs[0] if runs else None

def process_repo(repo: str, create_pr: bool, check_status: bool = False) -> Dict[str, any]:
    """Process a single repository."""
    result = {
        'repo': repo,
        'workflow_exists': False,
        'triggered': False,
        'status': None,
        'error': None
    }
    
    # Check if workflow exists
    if not check_workflow_exists(repo):
        result['error'] = 'Workflow not found'
        return result
    
    result['workflow_exists'] = True
    
    # Trigger the workflow
    if trigger_sync_workflow(repo, create_pr):
        result['triggered'] = True
        
        if check_status:
            # Wait a bit for the workflow to start
            time.sleep(3)
            
            # Check the status
            run = get_latest_workflow_run(repo)
            if run:
                result['status'] = run.get('status', 'unknown')
    else:
        result['error'] = 'Failed to trigger workflow'
    
    return result

def main():
    parser = argparse.ArgumentParser(description='Trigger template sync workflows across repositories')
    parser.add_argument(
        '--repo',
        help='Process only a specific repository'
    )
    parser.add_argument(
        '--no-pr',
        action='store_true',
        help='Run workflow without creating PR (diff only)'
    )
    parser.add_argument(
        '--check-status',
        action='store_true',
        help='Check workflow status after triggering'
    )
    parser.add_argument(
        '--batch-size',
        type=int,
        default=5,
        help='Number of workflows to trigger in parallel (default: 5)'
    )
    parser.add_argument(
        '--delay',
        type=int,
        default=2,
        help='Delay in seconds between batches (default: 2)'
    )
    
    args = parser.parse_args()
    
    # Get repos to process
    if args.repo:
        repos = [args.repo]
    else:
        print("🔍 Fetching downstream repositories...")
        repos = get_downstream_repos()
        print(f"📊 Found {len(repos)} repositories to check")
    
    create_pr = not args.no_pr
    
    # Process repositories
    results = []
    total_repos = len(repos)
    
    print(f"\n🚀 Triggering sync workflows (create_pr={create_pr})...")
    
    for i in range(0, total_repos, args.batch_size):
        batch = repos[i:i + args.batch_size]
        batch_num = i // args.batch_size + 1
        total_batches = (total_repos + args.batch_size - 1) // args.batch_size
        
        print(f"\n📦 Processing batch {batch_num}/{total_batches}...")
        
        for repo in batch:
            print(f"  🔄 {repo}...", end='', flush=True)
            result = process_repo(repo, create_pr, args.check_status)
            results.append(result)
            
            if result['triggered']:
                status = f" [{result.get('status', 'triggered')}]" if result.get('status') else ""
                print(f" ✅{status}")
            elif result['error'] == 'Workflow not found':
                print(f" ⚠️  (no sync workflow)")
            else:
                print(f" ❌ ({result['error']})")
        
        # Delay between batches to avoid rate limiting
        if i + args.batch_size < total_repos:
            print(f"⏳ Waiting {args.delay} seconds before next batch...")
            time.sleep(args.delay)
    
    # Summary
    triggered = sum(1 for r in results if r['triggered'])
    no_workflow = sum(1 for r in results if r['error'] == 'Workflow not found')
    failed = sum(1 for r in results if r['error'] and r['error'] != 'Workflow not found')
    
    print(f"\n📊 Summary:")
    print(f"  - Total repositories: {total_repos}")
    print(f"  - Workflows triggered: {triggered}")
    print(f"  - No sync workflow: {no_workflow}")
    print(f"  - Failed to trigger: {failed}")
    
    if triggered > 0:
        print(f"\n💡 Next steps:")
        print(f"  1. Wait for workflows to complete (usually 2-5 minutes)")
        print(f"  2. Run 'python scripts/manage_template_prs.py list' to see created PRs")
        print(f"  3. Run 'python scripts/manage_template_prs.py merge-latest' to merge PRs")
    
    if no_workflow > 0:
        print(f"\n⚠️  {no_workflow} repositories don't have the sync workflow.")
        print(f"  These repos may need the workflow file added first.")

if __name__ == "__main__":
    main()