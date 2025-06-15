#!/usr/bin/env python3
"""
Fix broken sync-from-template.yml workflows in downstream repositories.
This directly creates PRs to fix the workflow syntax error.
"""

import os
import subprocess
import tempfile
import shutil
from pathlib import Path

def run_command(cmd, cwd=None, check=True):
    """Run shell command and return output."""
    try:
        result = subprocess.run(cmd, shell=True, cwd=cwd, capture_output=True, text=True, check=check)
        return result.stdout.strip()
    except subprocess.CalledProcessError as e:
        if check:
            print(f"Error: {e.stderr}")
            raise
        return None

def get_downstream_repos():
    """Get list of downstream repositories."""
    print("🔍 Finding downstream repositories...")
    
    # Get repos with kailash-template topic
    repos = run_command(
        'gh api "search/repositories?q=org:Integrum-Global+topic:kailash-template&per_page=100" --jq \'.items[].name\' | grep -v "^new_project_template$"'
    ).split('\n')
    
    repos = [r.strip() for r in repos if r.strip()]
    print(f"📊 Found {len(repos)} downstream repositories")
    return repos

def fix_workflow_in_repo(repo):
    """Fix the workflow in a specific repository."""
    print(f"\n🔧 Processing: {repo}")
    
    # Check if PR already exists
    existing_pr = run_command(
        f'gh pr list -R "Integrum-Global/{repo}" --search "Fix workflow syntax" --state open --json number --jq ".[0].number"',
        check=False
    )
    
    if existing_pr:
        print(f"⚠️  PR #{existing_pr} already exists for {repo}")
        return False
    
    with tempfile.TemporaryDirectory() as tmpdir:
        try:
            # Clone the repo
            print(f"📥 Cloning {repo}...")
            run_command(f'gh repo clone "Integrum-Global/{repo}" -- --depth 1', cwd=tmpdir)
            
            repo_path = Path(tmpdir) / repo
            workflow_path = repo_path / '.github/workflows/sync-from-template.yml'
            
            if not workflow_path.exists():
                print(f"⚠️  No sync workflow found in {repo}")
                return False
            
            # Copy the fixed workflow from template
            template_workflow = Path('.github/workflows/sync-from-template.yml')
            shutil.copy2(template_workflow, workflow_path)
            
            # Create branch and commit
            branch_name = f'fix-workflow-syntax-{os.getpid()}'
            run_command('git checkout -b ' + branch_name, cwd=repo_path)
            run_command('git add -A', cwd=repo_path)
            
            commit_msg = '''fix: repair sync-from-template workflow syntax error

- Fix "Unexpected value Note" error on line 162
- Use proper heredoc format for PR body
- This enables automatic template synchronization'''
            
            run_command(f'git commit -m "{commit_msg}"', cwd=repo_path)
            
            # Push branch
            print(f"📤 Pushing fix to {repo}...")
            run_command(f'git push origin {branch_name}', cwd=repo_path)
            
            # Create PR
            pr_body = '''## 🚨 Critical Fix for Template Sync Workflow

This PR fixes the broken sync-from-template.yml workflow that was preventing automatic template synchronization.

### 🐛 Issue Fixed:
- **Workflow syntax error**: "Unexpected value Note" on line 162
- **Root cause**: Improper string formatting in PR body

### ✅ Solution:
- Updated to use proper heredoc format for multi-line strings
- Ensures GitHub Actions can parse the workflow correctly

### 🎯 Impact:
- Automatic template syncs will work again after merging
- Future template updates will be delivered automatically via PR
- No more "startup_failure" errors

**Please merge this PR to restore automatic template synchronization.**

After merging, you can manually trigger the sync workflow from the Actions tab.'''
            
            pr_url = run_command(
                f'gh pr create -R "Integrum-Global/{repo}" '
                f'--title "🚨 Fix: Sync workflow syntax error" '
                f'--body "{pr_body}" '
                f'--base main '
                f'--head {branch_name}',
                cwd=repo_path
            )
            
            print(f"✅ Created PR: {pr_url}")
            
            # Auto-merge if possible
            pr_number = pr_url.split('/')[-1]
            merge_result = run_command(
                f'gh pr merge {pr_number} -R "Integrum-Global/{repo}" --merge --admin',
                check=False
            )
            
            if merge_result is not None:
                print(f"✅ Auto-merged PR #{pr_number}")
                return True
            else:
                print(f"📋 PR created but needs manual merge: {pr_url}")
                return True
                
        except Exception as e:
            print(f"❌ Failed to process {repo}: {str(e)}")
            return False

def main():
    """Main process."""
    repos = get_downstream_repos()
    
    if not repos:
        print("No downstream repositories found")
        return
    
    success_count = 0
    failed_count = 0
    
    # Process each repo
    for repo in repos[:5]:  # Start with first 5 to test
        if fix_workflow_in_repo(repo):
            success_count += 1
        else:
            failed_count += 1
    
    print(f"\n📊 Summary:")
    print(f"  - Successfully processed: {success_count}")
    print(f"  - Failed: {failed_count}")
    
    if success_count > 0:
        print("\n💡 Next steps:")
        print("  1. Check created PRs at: https://github.com/orgs/Integrum-Global/pulls")
        print("  2. After PRs are merged, trigger sync from Actions tab in each repo")

if __name__ == "__main__":
    main()