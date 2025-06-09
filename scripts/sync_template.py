#!/usr/bin/env python3
"""
Template Synchronization Script

Syncs template repository changes to all downstream repositories.
Preserves downstream-specific files while updating template components.

Last updated: 2025-06-09 - Force CLAUDE.md updates with correct paths
"""

import os
import sys
import json
import subprocess
from pathlib import Path
from typing import List, Dict, Optional
import logging
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Files and directories to preserve in downstream repos
PRESERVE_PATTERNS = [
    "src/solutions/*",  # Solution-specific code
    "data/*",  # Project-specific data
    ".env*",  # Environment files
    "config.yaml",  # Project-specific config
    "README.md",  # Project-specific readme (preserve if exists)
    ".git/*",  # Git history
    ".github/workflows/*_custom.yml",  # Custom workflows
]

# Files and directories to always sync from template
SYNC_PATTERNS = [
    # GitHub configuration
    ".github/*",
    ".github/**/*",
    
    # Reference - sync entire directory to downstream repos
    "guide/reference/*",
    "guide/reference/**/*",
    
    # Guide - specific files/dirs to always sync
    "guide/frontend/*",
    "guide/frontend/**/*",
    "guide/instructions/*",
    "guide/instructions/**/*",
    "guide/workflows/*",
    "guide/workflows/**/*",
    
    # README files with instructions (always update)
    "*/README.md",
    "**/README.md",
    
    # Scripts - always sync entire directory
    "scripts/*",
    "scripts/**/*",
    
    # Shared source code
    "src/shared/*",
    "src/shared/**/*",
    
    # Root configuration files
    ".pre-commit-config.yaml",
    "MANIFEST.in",
    
    # Instruction files (always update with latest instructions)
    "README.md",
    "CLAUDE.md",  # Always replace with template version
]

# Files that require special merge handling  
MERGE_FILES = {
    # CLAUDE.md removed from merge handling - will be replaced directly
}

# Files to sync only if they don't exist (preserve existing)
SYNC_IF_MISSING = [
    # Root files (excluding instruction files which are always synced)
    "pyproject.toml",
    "CHANGELOG.md",
    
    # Data directories
    "data/configs/",
    "data/samples/",
    
    # Code directories
    "examples/",
    "docs/",
    "src/solutions/",
    "todos/",
    
    # Solution module structure (sync folder structure if missing)
    "src/solutions/*/workflows/",
    "src/solutions/*/workflows/__init__.py",
    "src/solutions/*/nodes/",
    "src/solutions/*/nodes/__init__.py",
    "src/solutions/*/examples/", 
    "src/solutions/*/examples/__init__.py",
    
    # Guide files/dirs not in SYNC_PATTERNS (sync if missing)
    "guide/adr/*",  # ADR files (sync if missing only)
    "guide/adr/**/*",  # ADR subdirectories (sync if missing only)
    "guide/prd/*",  # PRD files (sync if missing only)
    "guide/prd/**/*",  # PRD subdirectories (sync if missing only)
    "guide/mistakes/*",  # Mistake files (sync if missing only)
    "guide/mistakes/**/*",  # Mistake subdirectories (sync if missing only)
    "mistakes/*",  # Root mistake files (sync if missing only)  
    "todos/*",  # All todo files (sync if missing only)
    
    # Reference files are handled by SYNC_PATTERNS - removed from here to avoid conflicts
]

# Directories that should be merged (not overwritten)
MERGE_DIRECTORIES = [
    "src/shared/nodes/",
    "src/shared/utils/",
    "src/shared/workflows/",
    "todos/active/",  # Preserve active project tasks
    "todos/completed/",  # Preserve completed session history
    "guide/reference/templates/workflow/",  # Allow project-specific workflow templates
    "guide/reference/templates/nodes/",  # Allow project-specific node templates
]


class TemplateSyncer:
    def __init__(self, template_repo: str, github_token: str):
        self.template_repo = template_repo
        self.github_token = github_token
        self.gh_api = f"https://api.github.com"

    def get_downstream_repos(self) -> List[str]:
        """Get list of downstream repositories from environment or input."""
        repos = []

        # Check for specific target repo
        target_repo = os.environ.get("TARGET_REPO", "").strip()
        if target_repo:
            return [target_repo]

        # Get from environment variable (comma-separated)
        downstream = os.environ.get("DOWNSTREAM_REPOS", "").strip()
        if downstream:
            # Clean up the string - remove backticks, extra whitespace, and newlines
            downstream = downstream.replace("`", "").replace("\n", ",").replace("\r", ",")
            # Split by comma and filter out empty strings
            repos = [r.strip() for r in downstream.split(",") if r.strip()]
            # Filter out any remaining invalid entries
            repos = [r for r in repos if "/" in r and not r.startswith("http")]
            logger.info(f"Parsed downstream repos: {repos}")

        # If no repos specified, find all repos with template topic
        if not repos:
            logger.info("No downstream repos specified, searching for repos with kailash-template topic")
            repos = self.find_repos_with_template()

        return repos

    def find_repos_with_template(self) -> List[str]:
        """Find all repositories that use this template."""
        try:
            # Get organization from template repo
            org = self.template_repo.split("/")[0]

            # Search for repos with template file
            cmd = [
                "gh",
                "api",
                "--paginate",
                f"/orgs/{org}/repos",
                "--jq",
                '.[] | select(.topics[]? | contains("kailash-template")) | .full_name',
            ]

            result = subprocess.run(cmd, capture_output=True, text=True)
            if result.returncode == 0:
                repos = [
                    r.strip() for r in result.stdout.strip().split("\n") if r.strip()
                ]
                # Exclude the template repo itself
                repos = [r for r in repos if r != self.template_repo]
                return repos
        except Exception as e:
            logger.warning(f"Failed to find repos with template: {e}")

        return []

    def sync_repo(self, downstream_repo: str) -> bool:
        """Sync template changes to a downstream repository."""
        logger.info(f"Syncing to {downstream_repo}")
        
        # Save current directory to restore later
        original_cwd = os.getcwd()

        try:
            # Create temporary directory
            import tempfile

            with tempfile.TemporaryDirectory() as tmpdir:
                downstream_path = Path(tmpdir) / "downstream"
                template_path = Path(tmpdir) / "template"

                # Clone downstream repo
                logger.info(f"Cloning {downstream_repo}")
                subprocess.run(
                    [
                        "git",
                        "clone",
                        f"https://x-access-token:{self.github_token}@github.com/{downstream_repo}.git",
                        str(downstream_path),
                    ],
                    check=True,
                )

                # Clone template repo
                logger.info(f"Cloning template {self.template_repo}")
                subprocess.run(
                    [
                        "git",
                        "clone",
                        f"https://x-access-token:{self.github_token}@github.com/{self.template_repo}.git",
                        str(template_path),
                    ],
                    check=True,
                )

                # Create sync branch
                os.chdir(downstream_path)
                branch_name = (
                    f"template-sync-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
                )
                subprocess.run(["git", "checkout", "-b", branch_name], check=True)

                # Perform sync
                changes_made = self.sync_files(template_path, downstream_path)

                if changes_made:
                    # Commit changes
                    subprocess.run(["git", "add", "-A"], check=True)
                    subprocess.run(
                        [
                            "git",
                            "commit",
                            "-m",
                            f"Sync template updates from {self.template_repo}\n\n"
                            f"Automated sync at {datetime.now().isoformat()}",
                        ],
                        check=True,
                    )

                    # Push branch
                    subprocess.run(["git", "push", "origin", branch_name], check=True)

                    # Change back to original directory before creating PR
                    os.chdir(original_cwd)
                    
                    # Create PR
                    self.create_pr(downstream_repo, branch_name)
                    logger.info(f"Successfully synced {downstream_repo}")
                    return True
                else:
                    # Change back to original directory
                    os.chdir(original_cwd)
                    logger.info(f"No changes needed for {downstream_repo}")
                    return True

        except Exception as e:
            # Ensure we restore the original directory on error
            os.chdir(original_cwd)
            logger.error(f"Failed to sync {downstream_repo}: {e}")
            return False

    def sync_files(self, template_path: Path, downstream_path: Path) -> bool:
        """Sync files from template to downstream, preserving specific files."""
        changes_made = False

        # First, clean up specific unwanted files from previous syncs
        if self.cleanup_unwanted_files(downstream_path):
            changes_made = True

        # Copy files that should always be synced
        for pattern in SYNC_PATTERNS:
            for file_path in template_path.glob(pattern):
                if file_path.is_file():
                    relative_path = file_path.relative_to(template_path)
                    
                    # Skip sync-to-downstream.yml - only for template repo
                    if str(relative_path) == ".github/workflows/sync-to-downstream.yml":
                        continue
                    
                    dest_path = downstream_path / relative_path

                    # Check if file should be preserved if it exists
                    preserve_existing = any(
                        str(relative_path).startswith(preserve_pattern.rstrip("/"))
                        for preserve_pattern in SYNC_IF_MISSING
                    )

                    if preserve_existing and dest_path.exists():
                        logger.info(f"Preserving existing {relative_path}")
                        continue

                    # Check if this is in a merge directory (only copy if file doesn't exist)
                    in_merge_dir = any(
                        str(relative_path).startswith(merge_pattern.rstrip("/"))
                        for merge_pattern in MERGE_DIRECTORIES
                    )

                    if in_merge_dir and dest_path.exists():
                        logger.info(
                            f"Preserving existing file in merge directory: {relative_path}"
                        )
                        continue

                    # Check if file needs special merge handling
                    if str(relative_path) in MERGE_FILES:
                        if self.merge_file(
                            file_path, dest_path, MERGE_FILES[str(relative_path)]
                        ):
                            changes_made = True
                    else:
                        # Simple copy
                        if self.copy_file(file_path, dest_path):
                            changes_made = True

        # Process SYNC_IF_MISSING patterns (only sync if file doesn't exist)
        for pattern in SYNC_IF_MISSING:
            for file_path in template_path.glob(pattern):
                if file_path.is_file():
                    relative_path = file_path.relative_to(template_path)
                    dest_path = downstream_path / relative_path
                    
                    # Only copy if destination doesn't exist
                    if not dest_path.exists():
                        if self.copy_file(file_path, dest_path):
                            changes_made = True
                            logger.info(f"Added missing file: {relative_path}")

        return changes_made

    def cleanup_unwanted_files(self, downstream_path: Path) -> bool:
        """Remove specific old files that should no longer exist in downstream repositories."""
        changes_made = False
        
        # Remove the entire reference directory at root level (it's now in guide/reference)
        reference_dir = downstream_path / "reference"
        if reference_dir.exists():
            logger.info(f"Removing old reference directory from root level")
            import shutil
            shutil.rmtree(reference_dir)
            changes_made = True
        
        # Remove sync-to-downstream.yml workflow (only for template repo)
        sync_workflow = downstream_path / ".github" / "workflows" / "sync-to-downstream.yml"
        if sync_workflow.exists():
            logger.info(f"Removing sync-to-downstream.yml (only needed in template repo)")
            sync_workflow.unlink()
            changes_made = True
        
        # Handle Claude.md → CLAUDE.md migration
        old_claude_file = downstream_path / "Claude.md"
        new_claude_file = downstream_path / "CLAUDE.md"
        
        if old_claude_file.exists():
            if not new_claude_file.exists():
                # Migrate content from Claude.md to CLAUDE.md
                logger.info("Migrating Claude.md to CLAUDE.md")
                old_claude_file.rename(new_claude_file)
                changes_made = True
            else:
                # Both exist - remove the old one (CLAUDE.md takes precedence)
                logger.info("Removing old Claude.md (CLAUDE.md already exists)")
                old_claude_file.unlink()
                changes_made = True
                    
        return changes_made

    def copy_file(self, src: Path, dst: Path) -> bool:
        """Copy file if different from destination."""
        dst.parent.mkdir(parents=True, exist_ok=True)

        if dst.exists():
            with open(src, "rb") as f1, open(dst, "rb") as f2:
                if f1.read() == f2.read():
                    return False

        import shutil

        shutil.copy2(src, dst)
        logger.info(f"Updated {dst.relative_to(dst.parent.parent)}")
        return True

    def merge_file(self, src: Path, dst: Path, merge_method: str) -> bool:
        """Merge file with special handling."""
        # No special merge methods currently implemented
        return False

    # CLAUDE.md merge function removed - now handled as regular file replacement

    def create_pr(self, repo: str, branch: str):
        """Create pull request for template sync."""
        try:
            subprocess.run(
                [
                    "gh",
                    "pr",
                    "create",
                    "--repo",
                    repo,
                    "--head",
                    branch,
                    "--base",
                    "main",
                    "--title",
                    f"Sync template updates from {self.template_repo}",
                    "--body",
                    f"""## Template Sync

This PR automatically syncs updates from the template repository: {self.template_repo}

### Changes included:
- Updated reference documentation
- Updated guides and instructions  
- Updated shared components
- Updated scripts and tools
- **NEW**: GitHub metrics tracking system in scripts/metrics/

### CI/CD Note:
✅ This PR will only run minimal validation checks (template-sync-check.yml)
❌ Full CI pipeline is skipped for template sync PRs

### Review checklist:
- [ ] Review changes for conflicts with project-specific code
- [ ] Test that existing functionality still works
- [ ] Update project-specific documentation if needed

This is an automated sync triggered at {datetime.now().isoformat()}
""",
                ],
                check=True,
            )
            logger.info(f"Created corrective PR for {repo}")
        except Exception as e:
            logger.error(f"Failed to create PR: {e}")


def main():
    """Main entry point for template sync."""
    # Get configuration
    template_repo = os.environ.get("GITHUB_REPOSITORY", "")
    github_token = os.environ.get("GITHUB_TOKEN", "")

    if not template_repo or not github_token:
        logger.error(
            "Missing required environment variables: GITHUB_REPOSITORY, GITHUB_TOKEN"
        )
        sys.exit(1)

    # Initialize syncer
    syncer = TemplateSyncer(template_repo, github_token)

    # Get downstream repositories
    downstream_repos = syncer.get_downstream_repos()

    if not downstream_repos:
        logger.warning("No downstream repositories found to sync")
        sys.exit(0)

    logger.info(f"Found {len(downstream_repos)} downstream repositories to sync")

    # Sync each repository
    success_count = 0
    for repo in downstream_repos:
        if syncer.sync_repo(repo):
            success_count += 1

    logger.info(
        f"Successfully synced {success_count}/{len(downstream_repos)} repositories"
    )

    if success_count < len(downstream_repos):
        sys.exit(1)


if __name__ == "__main__":
    main()
