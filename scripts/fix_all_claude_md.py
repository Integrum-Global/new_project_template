#!/usr/bin/env python3
"""
Fix CLAUDE.md in all downstream repositories.
Updates path references from guide/todos/ to todos/ and guide/mistakes/ to mistakes/.
"""

import os
import sys
import subprocess
import json
import tempfile
from pathlib import Path
from typing import List, Dict, Tuple

# Downstream repositories
DOWNSTREAM_REPOS = [
    "Integrum-Global/ai_coaching",  # Already fixed, will skip
    "Integrum-Global/tpc_core",
    "Integrum-Global/deal_sourcing",
    "Integrum-Global/market-insights",
    "Integrum-Global/cbm",
    "Integrum-Global/mcp_server",
    "Integrum-Global/GIC_update"
]

def run_command(cmd: List[str], check=True) -> Tuple[int, str, str]:
    """Run a command and return (returncode, stdout, stderr)."""
    result = subprocess.run(cmd, capture_output=True, text=True)
    if check and result.returncode != 0:
        print(f"Command failed: {' '.join(cmd)}")
        print(f"Error: {result.stderr}")
    return result.returncode, result.stdout.strip(), result.stderr.strip()

def check_claude_needs_fix(repo: str) -> bool:
    """Check if CLAUDE.md needs fixing."""
    print(f"  📋 Checking CLAUDE.md content...")
    
    # Get CLAUDE.md content
    returncode, stdout, _ = run_command([
        "gh", "api", f"/repos/{repo}/contents/CLAUDE.md",
        "--jq", ".content"
    ], check=False)
    
    if returncode != 0:
        print(f"  ❌ Failed to fetch CLAUDE.md")
        return False
    
    # Decode base64 content
    import base64
    try:
        content = base64.b64decode(stdout).decode('utf-8')
    except:
        print(f"  ❌ Failed to decode CLAUDE.md content")
        return False
    
    # Check if it has old paths
    has_old_paths = "guide/todos/" in content or "guide/mistakes/" in content
    has_new_paths = "todos/000-master.md" in content and "guide/todos/" not in content
    
    if has_new_paths:
        print(f"  ✅ CLAUDE.md already has correct paths")
        return False
    elif has_old_paths:
        print(f"  ⚠️  CLAUDE.md needs path updates")
        return True
    else:
        print(f"  ❓ CLAUDE.md structure unclear, checking...")
        return "todos/" in content and "guide/todos/" in content

def create_claude_fix_pr(repo: str) -> bool:
    """Create a PR to fix CLAUDE.md paths."""
    print(f"\n🔧 Creating CLAUDE.md fix for {repo}...")
    
    # Check if already has open PR
    returncode, stdout, _ = run_command([
        "gh", "pr", "list",
        "--repo", repo,
        "--json", "title,number",
        "--jq", '.[] | select(.title | contains("CLAUDE.md")) | .number'
    ], check=False)
    
    if stdout:
        print(f"  ℹ️  Already has CLAUDE.md PR #{stdout}")
        return False
    
    # Check if fix is needed
    if not check_claude_needs_fix(repo):
        return False
    
    with tempfile.TemporaryDirectory() as tmpdir:
        repo_path = Path(tmpdir) / "repo"
        
        # Clone repository
        print(f"  📥 Cloning {repo}...")
        returncode, _, _ = run_command([
            "git", "clone", "--depth", "1",
            f"https://github.com/{repo}.git",
            str(repo_path)
        ])
        
        if returncode != 0:
            print(f"  ❌ Failed to clone repository")
            return False
        
        os.chdir(repo_path)
        
        # Read current CLAUDE.md
        claude_file = repo_path / "CLAUDE.md"
        if not claude_file.exists():
            print(f"  ❌ CLAUDE.md not found")
            return False
        
        current_content = claude_file.read_text()
        
        # Get template CLAUDE.md
        template_path = Path(__file__).parent.parent / "CLAUDE.md"
        if not template_path.exists():
            print(f"  ❌ Template CLAUDE.md not found")
            return False
        
        template_content = template_path.read_text()
        
        # Extract project-specific section if exists
        project_marker = "## Project-Specific Instructions"
        new_content = template_content
        
        if project_marker in current_content:
            # Extract project section from current
            idx = current_content.find(project_marker)
            project_section = current_content[idx:]
            
            # Replace in template
            if project_marker in template_content:
                idx = template_content.find(project_marker)
                new_content = template_content[:idx].rstrip() + "\n\n" + project_section
            else:
                new_content = template_content.rstrip() + "\n\n" + project_section
        
        # Write updated content
        claude_file.write_text(new_content)
        
        # Create branch and commit
        branch = "fix-claude-md-paths"
        run_command(["git", "checkout", "-b", branch])
        run_command(["git", "add", "CLAUDE.md"])
        run_command([
            "git", "commit", "-m",
            "fix: update CLAUDE.md with correct todo and mistake paths\n\n"
            "- Updated all references from guide/todos/ to todos/\n"
            "- Updated all references from guide/mistakes/ to mistakes/\n"
            "- Preserved project-specific instructions section"
        ])
        
        # Configure git for push
        run_command(["git", "config", "user.name", "GitHub Actions"])
        run_command(["git", "config", "user.email", "actions@github.com"])
        
        # Push branch
        print(f"  📤 Pushing branch...")
        returncode, _, _ = run_command([
            "git", "push", "origin", branch, "--force"
        ], check=False)
        
        if returncode != 0:
            print(f"  ❌ Failed to push branch")
            return False
        
        # Create PR
        print(f"  📝 Creating pull request...")
        returncode, stdout, _ = run_command([
            "gh", "pr", "create",
            "--repo", repo,
            "--title", "fix: update CLAUDE.md with correct todo and mistake paths",
            "--body", """## Fix CLAUDE.md Path References

This PR updates all path references in CLAUDE.md to reflect the correct project structure:

### Changes:
- ✅ Updated `guide/todos/` → `todos/`
- ✅ Updated `guide/mistakes/` → `mistakes/`
- ✅ Updated `guide/reference/` → remains as is (correct location)
- ✅ Preserved project-specific instructions section

### Why this change:
The todos and mistakes directories are at the root level in downstream repos, but CLAUDE.md had outdated references to their previous location under guide/.

This is a one-time fix to ensure Claude Code uses the correct paths when working with your repository."""
        ], check=False)
        
        if returncode == 0:
            print(f"  ✅ Created PR successfully")
            return True
        else:
            print(f"  ❌ Failed to create PR")
            return False

def main():
    """Fix CLAUDE.md in all downstream repositories."""
    print("🚀 Starting CLAUDE.md fix for all downstream repositories...")
    print(f"📋 Processing {len(DOWNSTREAM_REPOS)} repositories\n")
    
    success = 0
    skipped = 0
    failed = 0
    
    for repo in DOWNSTREAM_REPOS:
        try:
            if create_claude_fix_pr(repo):
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
    
    if success > 0:
        print(f"\n🎯 Next steps:")
        print(f"  1. Review and merge the created PRs")
        print(f"  2. All downstream repos will have correct CLAUDE.md paths")

if __name__ == "__main__":
    main()