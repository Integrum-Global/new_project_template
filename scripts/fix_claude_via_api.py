#!/usr/bin/env python3
"""
Fix CLAUDE.md via GitHub API without cloning.
"""

import subprocess
import base64
import json
from typing import Dict, Optional

DOWNSTREAM_REPOS = [
    "Integrum-Global/tpc_core",
    "Integrum-Global/deal_sourcing", 
    "Integrum-Global/market-insights",
    "Integrum-Global/cbm",
    "Integrum-Global/mcp_server",
    "Integrum-Global/GIC_update"
]

def run_gh_api(endpoint: str, method: str = "GET", data: Optional[Dict] = None) -> Dict:
    """Run GitHub API command."""
    cmd = ["gh", "api", endpoint]
    if method != "GET":
        cmd.extend(["--method", method])
    if data:
        cmd.extend(["--input", "-"])
        
    result = subprocess.run(cmd, capture_output=True, text=True, 
                          input=json.dumps(data) if data else None)
    
    if result.returncode != 0:
        print(f"API Error: {result.stderr}")
        return {}
    
    try:
        return json.loads(result.stdout) if result.stdout else {}
    except:
        return {}

def get_file_content(repo: str, path: str) -> Optional[Dict]:
    """Get file content from repo."""
    return run_gh_api(f"/repos/{repo}/contents/{path}")

def get_default_branch(repo: str) -> str:
    """Get default branch name."""
    repo_info = run_gh_api(f"/repos/{repo}")
    return repo_info.get("default_branch", "main")

def create_or_update_file(repo: str, path: str, content: str, message: str, branch: str, sha: Optional[str] = None) -> bool:
    """Create or update a file via API."""
    data = {
        "message": message,
        "content": base64.b64encode(content.encode()).decode(),
        "branch": branch
    }
    if sha:
        data["sha"] = sha
    
    result = run_gh_api(f"/repos/{repo}/contents/{path}", "PUT", data)
    return bool(result)

def create_branch(repo: str, branch_name: str, base_sha: str) -> bool:
    """Create a new branch."""
    data = {
        "ref": f"refs/heads/{branch_name}",
        "sha": base_sha
    }
    result = run_gh_api(f"/repos/{repo}/git/refs", "POST", data)
    return bool(result)

def create_pr(repo: str, title: str, body: str, head: str, base: str) -> Optional[str]:
    """Create a pull request."""
    data = {
        "title": title,
        "body": body,
        "head": head,
        "base": base
    }
    result = run_gh_api(f"/repos/{repo}/pulls", "POST", data)
    return result.get("html_url")

def fix_claude_md_for_repo(repo: str) -> bool:
    """Fix CLAUDE.md for a single repository."""
    print(f"\n🔧 Processing {repo}...")
    
    # Get current CLAUDE.md
    claude_info = get_file_content(repo, "CLAUDE.md")
    if not claude_info:
        print(f"  ❌ Failed to get CLAUDE.md")
        return False
    
    # Decode content
    current_content = base64.b64decode(claude_info["content"]).decode('utf-8')
    
    # Check if needs fixing
    if "guide/todos/" not in current_content:
        print(f"  ✅ CLAUDE.md already has correct paths")
        return False
    
    print(f"  ⚠️  CLAUDE.md needs path updates")
    
    # Get template CLAUDE.md
    with open("CLAUDE.md", "r") as f:
        template_content = f.read()
    
    # Preserve project-specific section
    project_marker = "## Project-Specific Instructions"
    new_content = template_content
    
    if project_marker in current_content:
        idx = current_content.find(project_marker)
        project_section = current_content[idx:]
        
        if project_marker in template_content:
            idx = template_content.find(project_marker)
            new_content = template_content[:idx].rstrip() + "\n\n" + project_section
        else:
            new_content = template_content.rstrip() + "\n\n" + project_section
    
    # Get default branch info
    default_branch = get_default_branch(repo)
    branch_info = run_gh_api(f"/repos/{repo}/git/refs/heads/{default_branch}")
    if not branch_info:
        print(f"  ❌ Failed to get branch info")
        return False
    
    base_sha = branch_info["object"]["sha"]
    
    # Create new branch
    branch_name = "fix-claude-md-paths"
    print(f"  🌿 Creating branch {branch_name}...")
    
    # Delete branch if exists
    run_gh_api(f"/repos/{repo}/git/refs/heads/{branch_name}", "DELETE")
    
    if not create_branch(repo, branch_name, base_sha):
        print(f"  ❌ Failed to create branch")
        return False
    
    # Update CLAUDE.md
    print(f"  📝 Updating CLAUDE.md...")
    if not create_or_update_file(
        repo, "CLAUDE.md", new_content,
        "fix: update CLAUDE.md with correct todo and mistake paths\n\n"
        "- Updated all references from guide/todos/ to todos/\n"
        "- Updated all references from guide/mistakes/ to mistakes/\n"
        "- Preserved project-specific instructions section",
        branch_name, claude_info["sha"]
    ):
        print(f"  ❌ Failed to update CLAUDE.md")
        return False
    
    # Create PR
    print(f"  🚀 Creating pull request...")
    pr_url = create_pr(
        repo,
        "fix: update CLAUDE.md with correct todo and mistake paths",
        """## Fix CLAUDE.md Path References

This PR updates all path references in CLAUDE.md to reflect the correct project structure:

### Changes:
- ✅ Updated `guide/todos/` → `todos/`
- ✅ Updated `guide/mistakes/` → `mistakes/`
- ✅ Updated `guide/reference/` → remains as is (correct location)
- ✅ Preserved project-specific instructions section

### Why this change:
The todos and mistakes directories are at the root level in downstream repos, but CLAUDE.md had outdated references to their previous location under guide/.

This is a one-time fix to ensure Claude Code uses the correct paths when working with your repository.""",
        branch_name,
        default_branch
    )
    
    if pr_url:
        print(f"  ✅ Created PR: {pr_url}")
        return True
    else:
        print(f"  ❌ Failed to create PR")
        return False

def main():
    """Main function."""
    print("🚀 Fixing CLAUDE.md in all downstream repositories via API...")
    
    success = 0
    skipped = 0
    failed = 0
    
    for repo in DOWNSTREAM_REPOS:
        try:
            if fix_claude_md_for_repo(repo):
                success += 1
            else:
                skipped += 1
        except Exception as e:
            print(f"  ❌ Error: {e}")
            failed += 1
    
    print(f"\n📊 Summary:")
    print(f"  ✅ PRs created: {success}")
    print(f"  ⏭️  Skipped: {skipped}")
    print(f"  ❌ Failed: {failed}")

if __name__ == "__main__":
    main()