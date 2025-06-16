#!/usr/bin/env python3
"""
Sync repository topics from template to all downstream repositories.
Ensures all repos created from this template have the proper topics.
"""

import subprocess
import json
import sys
from typing import List, Set, Optional
import argparse

def run_command(cmd: List[str]) -> Optional[str]:
    """Run a command and return output."""
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        return result.stdout.strip()
    except subprocess.CalledProcessError as e:
        print(f"Error running {' '.join(cmd)}: {e.stderr}")
        return None

def get_repo_topics(repo: str) -> Set[str]:
    """Get topics for a repository."""
    cmd = [
        "gh", "repo", "view", f"Integrum-Global/{repo}",
        "--json", "repositoryTopics"
    ]
    
    output = run_command(cmd)
    if not output:
        return set()
    
    try:
        data = json.loads(output)
        topics = data.get('repositoryTopics', [])
        if topics is None:
            return set()
        return {topic['name'] for topic in topics if topic and 'name' in topic}
    except (json.JSONDecodeError, TypeError):
        return set()

def set_repo_topics(repo: str, topics: List[str]) -> bool:
    """Set topics for a repository."""
    if not topics:
        return True
    
    # GitHub CLI doesn't have a direct command for setting topics, 
    # so we'll use the API
    topics_str = ' '.join(f'"{topic}"' for topic in topics)
    cmd = [
        "gh", "api",
        f"repos/Integrum-Global/{repo}/topics",
        "-X", "PUT",
        "-f", f"names[]={topics_str}",
        "--silent"
    ]
    
    # Use curl with gh auth for setting topics
    cmd = [
        "bash", "-c",
        f'gh api repos/Integrum-Global/{repo}/topics -X PUT -H "Accept: application/vnd.github+json" --field "names[]={topics[0]}"' + 
        ''.join(f' --field "names[]={topic}"' for topic in topics[1:])
    ]
    
    result = run_command(cmd)
    return result is not None

def check_template_creation(repo: str) -> bool:
    """Check if a repo was created from the template."""
    # Explicitly exclude the SDK - it should never have the template topic
    if repo == 'kailash_python_sdk':
        return False
    
    cmd = [
        "gh", "repo", "view", f"Integrum-Global/{repo}",
        "--json", "templateRepository"
    ]
    
    output = run_command(cmd)
    if not output:
        return False
    
    data = json.loads(output)
    template = data.get('templateRepository')
    
    # Primary check: GitHub's official template tracking
    if template and template.get('name') == 'new_project_template':
        return True
    
    # Secondary check: Only for repos that might have lost GitHub template metadata
    # Must have ALL key template structure AND be relatively recent
    structure_cmd = [
        "gh", "api", f"repos/Integrum-Global/{repo}/contents",
        "--jq", ".[].name"
    ]
    
    structure_output = run_command(structure_cmd)
    if structure_output:
        contents = set(structure_output.strip().split('\n'))
        
        # Require ALL template markers, not just any
        required_markers = {'sdk-users', 'CLAUDE.md'}
        template_structure_markers = {'apps', 'solutions', 'deployment'}
        
        # Must have core template files AND template directory structure
        has_core_files = required_markers.issubset(contents)
        has_template_structure = any(marker in contents for marker in template_structure_markers)
        
        if has_core_files and has_template_structure:
            # Additional verification: check if CLAUDE.md contains template content
            claude_cmd = [
                "gh", "api", f"repos/Integrum-Global/{repo}/contents/CLAUDE.md",
                "--jq", ".content | @base64d"
            ]
            claude_output = run_command(claude_cmd)
            if claude_output and "Kailash SDK" in claude_output and "new_project_template" in claude_output:
                return True
    
    return False

def get_downstream_repos() -> List[str]:
    """Get list of potential downstream repositories."""
    cmd = [
        "gh", "repo", "list", "Integrum-Global", 
        "--limit", "100", 
        "--json", "name,createdAt,isTemplate"
    ]
    
    output = run_command(cmd)
    if not output:
        return []
    
    repos = json.loads(output)
    
    # Filter out the template itself and other templates
    downstream = []
    for repo in repos:
        if repo['isTemplate'] or repo['name'] == 'new_project_template':
            continue
        downstream.append(repo['name'])
    
    return downstream

def main():
    parser = argparse.ArgumentParser(description='Sync repository topics from template')
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Show what would be done without making changes'
    )
    parser.add_argument(
        '--repo',
        help='Process only a specific repository'
    )
    parser.add_argument(
        '--add-topic',
        action='append',
        dest='additional_topics',
        help='Additional topic to add (can be used multiple times)'
    )
    
    args = parser.parse_args()
    
    # Get template topics
    print("📋 Fetching template repository topics...")
    template_topics = get_repo_topics('new_project_template')
    print(f"✅ Template topics: {', '.join(sorted(template_topics))}")
    
    # Add any additional topics requested
    if args.additional_topics:
        template_topics.update(args.additional_topics)
        print(f"➕ Additional topics to add: {', '.join(args.additional_topics)}")
    
    # Get repos to process
    if args.repo:
        repos = [args.repo]
    else:
        print("\n🔍 Fetching downstream repositories...")
        repos = get_downstream_repos()
        print(f"📊 Found {len(repos)} repositories to check")
    
    # Process each repo
    repos_updated = 0
    repos_checked = 0
    repos_from_template = 0
    
    print("\n🔄 Processing repositories...")
    for repo in repos:
        # Check if repo was created from template
        is_from_template = check_template_creation(repo)
        
        if not is_from_template and not args.repo:
            # Skip repos not created from template (unless specific repo requested)
            continue
        
        repos_checked += 1
        if is_from_template:
            repos_from_template += 1
        
        # Get current topics
        current_topics = get_repo_topics(repo)
        
        # Calculate missing topics
        missing_topics = template_topics - current_topics
        
        if missing_topics:
            all_topics = sorted(current_topics | template_topics)
            
            print(f"\n📦 {repo}:")
            print(f"  Current topics: {', '.join(sorted(current_topics)) or '(none)'}")
            print(f"  Missing topics: {', '.join(sorted(missing_topics))}")
            print(f"  New topics: {', '.join(all_topics)}")
            
            if not args.dry_run:
                if set_repo_topics(repo, all_topics):
                    print(f"  ✅ Successfully updated topics")
                    repos_updated += 1
                else:
                    print(f"  ❌ Failed to update topics")
            else:
                print(f"  🔍 [DRY RUN] Would update topics")
                repos_updated += 1
    
    # Summary
    print(f"\n📊 Summary:")
    print(f"  - Checked {repos_checked} repositories")
    print(f"  - Found {repos_from_template} created from template")
    print(f"  - Updated {repos_updated} repositories with missing topics")
    
    if args.dry_run:
        print("\n🔍 This was a dry run - no changes were made")
        print("Run without --dry-run to apply changes")

if __name__ == "__main__":
    main()