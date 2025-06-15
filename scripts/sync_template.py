#!/usr/bin/env python3
"""
Sync template changes to downstream repositories.
Uses TEMPLATE_SYNC_TOKEN to create PRs in downstream repos.
"""

import os
import subprocess
import json
import sys
from datetime import datetime

def run_command(cmd, check=True):
    """Run shell command and return output."""
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True, check=check)
        return result.stdout.strip()
    except subprocess.CalledProcessError as e:
        if check:
            print(f"Error running command: {cmd}")
            print(f"Error: {e.stderr}")
            raise
        return None

def get_downstream_repos():
    """Get list of downstream repositories."""
    print("🔍 Finding downstream repositories...")
    
    # Try topic-based search first
    repos_json = run_command(
        'gh api "search/repositories?q=org:Integrum-Global+topic:kailash-template&per_page=100" --jq \'.items[].name\''
    )
    
    repos = [r for r in repos_json.split('\n') if r and r not in ['new_project_template', 'kailash_python_sdk']]
    
    if not repos:
        print("⚠️  No repos found with topic, checking template relationships...")
        repos_json = run_command(
            'gh repo list Integrum-Global --limit 200 --json name,templateRepository'
        )
        data = json.loads(repos_json) if repos_json else []
        repos = [r['name'] for r in data if r.get('templateRepository', {}).get('name') == 'new_project_template' and r['name'] != 'kailash_python_sdk']
    
    print(f"📊 Found {len(repos)} downstream repositories")
    return repos

def trigger_sync_workflow(repo):
    """Trigger sync workflow in a downstream repository."""
    print(f"🔄 Triggering sync for: {repo}")
    
    # Check if workflow exists
    workflows = run_command(f'gh workflow list -R "Integrum-Global/{repo}"', check=False)
    
    if workflows and 'Sync from Template' in workflows:
        # Try to trigger the workflow
        result = run_command(
            f'gh workflow run sync-from-template.yml -R "Integrum-Global/{repo}"',
            check=False
        )
        
        if result is not None:
            print(f"✅ Successfully triggered sync for {repo}")
            return True
        else:
            print(f"❌ Failed to trigger sync for {repo}")
            return False
    else:
        print(f"⚠️  Skipping {repo} - no sync workflow found")
        return False

def main():
    """Main sync process."""
    # Check for required token
    if not os.environ.get('GITHUB_TOKEN'):
        print("❌ GITHUB_TOKEN not set")
        sys.exit(1)
    
    # Get target repo if specified
    target_repo = os.environ.get('TARGET_REPO', '').strip()
    
    if target_repo:
        repos = [target_repo]
        print(f"🎯 Syncing specific repository: {target_repo}")
    else:
        repos = get_downstream_repos()
    
    # Trigger syncs
    success_count = 0
    failed_count = 0
    skipped_count = 0
    
    for repo in repos:
        if not repo:
            continue
            
        result = trigger_sync_workflow(repo)
        
        if result is True:
            success_count += 1
        elif result is False:
            failed_count += 1
        else:
            skipped_count += 1
        
        # Small delay to avoid rate limiting
        if len(repos) > 1:
            subprocess.run(['sleep', '2'])
    
    # Summary
    print("\n📊 Summary:")
    print(f"  - Successfully triggered: {success_count} repositories")
    print(f"  - Failed to trigger: {failed_count} repositories") 
    print(f"  - Skipped: {skipped_count} repositories")
    
    if failed_count > 0:
        sys.exit(1)

if __name__ == "__main__":
    main()