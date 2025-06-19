#!/usr/bin/env python3
"""
Merge template sync PRs for specific repositories.
Enhanced version with parallel processing and detailed reporting.
"""

import subprocess
import json
import sys
import argparse
from typing import List, Dict, Optional, Tuple
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
import time
from dataclasses import dataclass
from enum import Enum

# ANSI color codes
class Colors:
    RED = '\033[0;31m'
    GREEN = '\033[0;32m'
    YELLOW = '\033[1;33m'
    BLUE = '\033[0;34m'
    BOLD = '\033[1m'
    NC = '\033[0m'  # No Color

class MergeStatus(Enum):
    SUCCESS = "success"
    FAILED = "failed"
    CONFLICT = "conflict"
    NO_PRS = "no_prs"
    BLOCKED = "blocked"
    ERROR = "error"

@dataclass
class RepoResult:
    repo: str
    status: MergeStatus
    pr_merged: Optional[int] = None
    prs_closed: List[int] = None
    error_message: Optional[str] = None
    conflict_pr: Optional[int] = None

class TemplateSyncMerger:
    def __init__(self, org: str = "Integrum-Global", dry_run: bool = False):
        self.org = org
        self.dry_run = dry_run
        self.results: List[RepoResult] = []
        
    def run_command(self, cmd: List[str]) -> Optional[str]:
        """Run a command and return output."""
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            return result.stdout.strip()
        except subprocess.CalledProcessError as e:
            return None
    
    def get_template_sync_prs(self, repo: str) -> List[Dict]:
        """Get all template sync PRs for a repository."""
        cmd = [
            "gh", "pr", "list",
            "--repo", f"{self.org}/{repo}",
            "--state", "open",
            "--json", "number,title,author,createdAt,headRefName,body,mergeable,mergeStateStatus",
            "--limit", "100"
        ]
        
        output = self.run_command(cmd)
        if not output:
            return []
        
        try:
            prs = json.loads(output)
        except json.JSONDecodeError:
            return []
        
        # Filter for template sync PRs
        template_prs = []
        for pr in prs:
            title = pr.get('title', '')
            body = pr.get('body', '')
            branch = pr.get('headRefName', '')
            
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
    
    def check_pr_status(self, repo: str, pr_number: int) -> Tuple[str, str]:
        """Check if a PR is mergeable."""
        cmd = [
            "gh", "pr", "view", str(pr_number),
            "--repo", f"{self.org}/{repo}",
            "--json", "mergeable,mergeStateStatus"
        ]
        
        output = self.run_command(cmd)
        if not output:
            return "UNKNOWN", "UNKNOWN"
        
        try:
            status = json.loads(output)
            return status.get('mergeable', 'UNKNOWN'), status.get('mergeStateStatus', 'UNKNOWN')
        except json.JSONDecodeError:
            return "UNKNOWN", "UNKNOWN"
    
    def merge_pr(self, repo: str, pr_number: int) -> Tuple[bool, Optional[str]]:
        """Merge a PR, returns (success, error_message)."""
        if self.dry_run:
            print(f"    [DRY RUN] Would merge PR #{pr_number}")
            return True, None
        
        # First try with admin flag
        cmd = [
            "gh", "pr", "merge", str(pr_number),
            "--repo", f"{self.org}/{repo}",
            "--merge",
            "--delete-branch",
            "--admin"
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode == 0:
            return True, None
        
        # Try without admin flag
        cmd.remove("--admin")
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode == 0:
            return True, None
        
        return False, result.stderr
    
    def close_pr(self, repo: str, pr_number: int) -> bool:
        """Close a PR without merging."""
        if self.dry_run:
            print(f"    [DRY RUN] Would close PR #{pr_number}")
            return True
        
        cmd = [
            "gh", "pr", "close", str(pr_number),
            "--repo", f"{self.org}/{repo}",
            "--comment", "Closing outdated template sync PR. A newer sync is available."
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        return result.returncode == 0
    
    def process_repository(self, repo: str) -> RepoResult:
        """Process all template sync PRs for a repository."""
        print(f"\n{Colors.BOLD}📦 Processing: {repo}{Colors.NC}")
        
        try:
            prs = self.get_template_sync_prs(repo)
            
            if not prs:
                print(f"  {Colors.YELLOW}No template sync PRs found{Colors.NC}")
                return RepoResult(repo=repo, status=MergeStatus.NO_PRS)
            
            print(f"  Found {Colors.BOLD}{len(prs)}{Colors.NC} template sync PR(s)")
            
            # Sort PRs by creation date (newest first)
            prs.sort(key=lambda x: x['createdAt'], reverse=True)
            
            result = RepoResult(repo=repo, status=MergeStatus.NO_PRS, prs_closed=[])
            
            for i, pr in enumerate(prs):
                pr_number = pr['number']
                pr_title = pr['title'][:60] + "..." if len(pr['title']) > 60 else pr['title']
                pr_created = pr['createdAt']
                
                print(f"\n  {Colors.BOLD}PR #{pr_number}:{Colors.NC} {pr_title}")
                print(f"    Created: {pr_created}")
                
                if i == 0:  # Most recent PR
                    # Check mergeable status
                    mergeable, merge_state = self.check_pr_status(repo, pr_number)
                    
                    if mergeable == "CONFLICTING":
                        print(f"    {Colors.YELLOW}⚠️  PR has merge conflicts{Colors.NC}")
                        result.status = MergeStatus.CONFLICT
                        result.conflict_pr = pr_number
                        continue
                    
                    if merge_state == "BLOCKED":
                        print(f"    {Colors.YELLOW}⚠️  PR is blocked by status checks{Colors.NC}")
                    
                    print(f"    {Colors.BLUE}→ Attempting to merge...{Colors.NC}")
                    success, error = self.merge_pr(repo, pr_number)
                    
                    if success:
                        print(f"    {Colors.GREEN}✓ Successfully merged PR #{pr_number}{Colors.NC}")
                        result.status = MergeStatus.SUCCESS
                        result.pr_merged = pr_number
                    else:
                        print(f"    {Colors.RED}✗ Failed to merge PR #{pr_number}{Colors.NC}")
                        if error:
                            print(f"    {Colors.RED}  Error: {error}{Colors.NC}")
                        result.status = MergeStatus.FAILED
                        result.error_message = error
                else:
                    # Close older PRs
                    print(f"    {Colors.BLUE}→ Closing older PR...{Colors.NC}")
                    if self.close_pr(repo, pr_number):
                        print(f"    {Colors.GREEN}✓ Successfully closed PR #{pr_number}{Colors.NC}")
                        result.prs_closed.append(pr_number)
                    else:
                        print(f"    {Colors.RED}✗ Failed to close PR #{pr_number}{Colors.NC}")
            
            return result
            
        except Exception as e:
            print(f"  {Colors.RED}Error processing repository: {str(e)}{Colors.NC}")
            return RepoResult(repo=repo, status=MergeStatus.ERROR, error_message=str(e))
    
    def process_repositories(self, repos: List[str], max_workers: int = 5):
        """Process multiple repositories in parallel."""
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            future_to_repo = {executor.submit(self.process_repository, repo): repo for repo in repos}
            
            for future in as_completed(future_to_repo):
                repo = future_to_repo[future]
                try:
                    result = future.result()
                    self.results.append(result)
                except Exception as e:
                    print(f"{Colors.RED}Exception processing {repo}: {str(e)}{Colors.NC}")
                    self.results.append(RepoResult(repo=repo, status=MergeStatus.ERROR, error_message=str(e)))
    
    def print_summary(self):
        """Print a summary of all operations."""
        print(f"\n{Colors.BOLD}{Colors.BLUE}{'='*60}{Colors.NC}")
        print(f"{Colors.BOLD}{Colors.BLUE}Summary Report{Colors.NC}")
        print(f"{Colors.BOLD}{Colors.BLUE}{'='*60}{Colors.NC}\n")
        
        # Count statuses
        status_counts = {status: 0 for status in MergeStatus}
        for result in self.results:
            status_counts[result.status] += 1
        
        total_prs_closed = sum(len(r.prs_closed) for r in self.results if r.prs_closed)
        
        print(f"{Colors.BOLD}Overall Statistics:{Colors.NC}")
        print(f"  {Colors.GREEN}✓ Successful merges: {status_counts[MergeStatus.SUCCESS]}{Colors.NC}")
        print(f"  {Colors.RED}✗ Failed merges: {status_counts[MergeStatus.FAILED]}{Colors.NC}")
        print(f"  {Colors.YELLOW}⚠️  Conflicts: {status_counts[MergeStatus.CONFLICT]}{Colors.NC}")
        print(f"  {Colors.YELLOW}○ No PRs found: {status_counts[MergeStatus.NO_PRS]}{Colors.NC}")
        print(f"  {Colors.RED}❌ Errors: {status_counts[MergeStatus.ERROR]}{Colors.NC}")
        print(f"  {Colors.BLUE}◉ Total older PRs closed: {total_prs_closed}{Colors.NC}")
        print(f"  {Colors.BOLD}  Total repositories: {len(self.results)}{Colors.NC}")
        
        print(f"\n{Colors.BOLD}Detailed Results:{Colors.NC}")
        
        # Group by status
        for status in MergeStatus:
            repos_with_status = [r for r in self.results if r.status == status]
            if not repos_with_status:
                continue
            
            print(f"\n  {Colors.BOLD}{status.value.title()}:{Colors.NC}")
            for result in repos_with_status:
                if status == MergeStatus.SUCCESS:
                    print(f"    {Colors.GREEN}✓{Colors.NC} {result.repo} - Merged PR #{result.pr_merged}")
                elif status == MergeStatus.FAILED:
                    print(f"    {Colors.RED}✗{Colors.NC} {result.repo} - Failed to merge")
                    if result.error_message:
                        print(f"       Error: {result.error_message[:100]}")
                elif status == MergeStatus.CONFLICT:
                    print(f"    {Colors.YELLOW}⚠️{Colors.NC} {result.repo} - PR #{result.conflict_pr} has conflicts")
                elif status == MergeStatus.NO_PRS:
                    print(f"    {Colors.YELLOW}○{Colors.NC} {result.repo} - No template sync PRs")
                elif status == MergeStatus.ERROR:
                    print(f"    {Colors.RED}❌{Colors.NC} {result.repo} - Error: {result.error_message}")
        
        # Action items
        conflicts = [r for r in self.results if r.status == MergeStatus.CONFLICT]
        failures = [r for r in self.results if r.status in [MergeStatus.FAILED, MergeStatus.ERROR]]
        
        if conflicts or failures:
            print(f"\n{Colors.YELLOW}{Colors.BOLD}⚠️  Action Required:{Colors.NC}")
            
            if conflicts:
                print(f"\n  {Colors.BOLD}Repositories with conflicts:{Colors.NC}")
                for result in conflicts:
                    print(f"    - {result.repo} (PR #{result.conflict_pr})")
                print(f"\n  To resolve conflicts, run:")
                print(f"    gh pr checkout <PR_NUMBER> --repo {self.org}/<REPO>")
                print(f"    # Resolve conflicts")
                print(f"    git push")
            
            if failures:
                print(f"\n  {Colors.BOLD}Failed merges requiring manual intervention:{Colors.NC}")
                for result in failures:
                    print(f"    - {result.repo}")

def main():
    # Target repositories
    REPOS = [
        "talentverse", "pg", "corpsec", "tpc_shipping_migration", "tpc-migration",
        "ESG-report", "ai-coaching", "cdl_kailash_migration", "decisiontrackerfe",
        "GIC_update", "mcp_server", "cbm", "tpc_shipping_fe", "tpc_shipping",
        "market-insights", "narrated_derivations", "deal_sourcing", "tpc_core",
        "ai_coaching_demo"
    ]
    
    parser = argparse.ArgumentParser(
        description='Merge template sync PRs for specific repositories',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Merge all PRs
  %(prog)s
  
  # Dry run to see what would be done
  %(prog)s --dry-run
  
  # Process specific repositories only
  %(prog)s --repos talentverse pg corpsec
  
  # Use more parallel workers
  %(prog)s --workers 10
        """
    )
    
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Show what would be done without making changes'
    )
    parser.add_argument(
        '--repos',
        nargs='+',
        help='Process only these repositories (default: all 19 repos)'
    )
    parser.add_argument(
        '--workers',
        type=int,
        default=5,
        help='Number of parallel workers (default: 5)'
    )
    parser.add_argument(
        '--org',
        default='Integrum-Global',
        help='GitHub organization (default: Integrum-Global)'
    )
    
    args = parser.parse_args()
    
    # Check prerequisites
    print(f"{Colors.BOLD}{Colors.BLUE}Template Sync PR Merger{Colors.NC}")
    print("Checking prerequisites...")
    
    if subprocess.run(["gh", "auth", "status"], capture_output=True).returncode != 0:
        print(f"{Colors.RED}Error: Not authenticated with GitHub CLI{Colors.NC}")
        print("Please run: gh auth login")
        sys.exit(1)
    
    print(f"{Colors.GREEN}✓ GitHub CLI is authenticated{Colors.NC}")
    
    if args.dry_run:
        print(f"\n{Colors.YELLOW}{Colors.BOLD}DRY RUN MODE - No changes will be made{Colors.NC}")
    
    # Determine repositories to process
    repos_to_process = args.repos if args.repos else REPOS
    
    print(f"\nWill process {len(repos_to_process)} repositories")
    
    # Process repositories
    merger = TemplateSyncMerger(org=args.org, dry_run=args.dry_run)
    
    start_time = time.time()
    merger.process_repositories(repos_to_process, max_workers=args.workers)
    elapsed_time = time.time() - start_time
    
    # Print summary
    merger.print_summary()
    
    print(f"\n{Colors.BOLD}Completed in {elapsed_time:.1f} seconds{Colors.NC}")

if __name__ == "__main__":
    main()