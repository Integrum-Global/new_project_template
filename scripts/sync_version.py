#!/usr/bin/env python3
"""
Sync Kailash SDK version between SDK and template repositories.

This script ensures the template repository uses the correct SDK version
and updates downstream repositories when new versions are released.
"""

import argparse
import logging
import subprocess
from pathlib import Path

import tomli
import tomli_w

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class VersionSyncer:
    def __init__(self, sdk_path: str, template_path: str):
        self.sdk_path = Path(sdk_path)
        self.template_path = Path(template_path)

    def get_sdk_version(self) -> str:
        """Get current SDK version from pyproject.toml."""
        pyproject_path = self.sdk_path / "pyproject.toml"
        if not pyproject_path.exists():
            raise FileNotFoundError(f"SDK pyproject.toml not found at {pyproject_path}")

        with open(pyproject_path, "rb") as f:
            data = tomli.load(f)

        version = data.get("project", {}).get("version")
        if not version:
            raise ValueError("Version not found in SDK pyproject.toml")

        logger.info(f"SDK version: {version}")
        return version

    def get_template_kailash_version(self) -> str:
        """Get current kailash dependency version from template."""
        pyproject_path = self.template_path / "pyproject.toml"
        if not pyproject_path.exists():
            raise FileNotFoundError(
                f"Template pyproject.toml not found at {pyproject_path}"
            )

        with open(pyproject_path, "rb") as f:
            data = tomli.load(f)

        dependencies = data.get("project", {}).get("dependencies", [])
        for dep in dependencies:
            if dep.startswith("kailash"):
                logger.info(f"Template kailash dependency: {dep}")
                return dep

        # Check in optional dependencies
        optional_deps = data.get("project", {}).get("optional-dependencies", {})
        for group, deps in optional_deps.items():
            for dep in deps:
                if dep.startswith("kailash"):
                    logger.info(
                        f"Template kailash dependency (optional-{group}): {dep}"
                    )
                    return dep

        raise ValueError("Kailash dependency not found in template pyproject.toml")

    def update_template_version(self, sdk_version: str, dry_run: bool = False):
        """Update template to use specific SDK version."""
        pyproject_path = self.template_path / "pyproject.toml"

        with open(pyproject_path, "rb") as f:
            data = tomli.load(f)

        # Update template version to match SDK
        if "project" not in data:
            data["project"] = {}
        data["project"]["version"] = sdk_version

        # Update kailash dependency
        dependencies = data.get("project", {}).get("dependencies", [])
        for i, dep in enumerate(dependencies):
            if dep.startswith("kailash"):
                # Update to exact version for templates
                dependencies[i] = f"kailash=={sdk_version}"
                logger.info(f"Updated dependency to: {dependencies[i]}")
                break
        else:
            # Add kailash dependency if not found
            dependencies.append(f"kailash=={sdk_version}")
            logger.info(f"Added kailash dependency: kailash=={sdk_version}")

        # Update optional dependencies too
        optional_deps = data.get("project", {}).get("optional-dependencies", {})
        for group, deps in optional_deps.items():
            for i, dep in enumerate(deps):
                if dep.startswith("kailash"):
                    deps[i] = f"kailash=={sdk_version}"
                    logger.info(f"Updated optional dependency ({group}): {deps[i]}")

        if not dry_run:
            with open(pyproject_path, "wb") as f:
                tomli_w.dump(data, f)
            logger.info(f"Updated template pyproject.toml with version {sdk_version}")
        else:
            logger.info(f"DRY RUN: Would update template to version {sdk_version}")

    def test_dependency_resolution(self):
        """Test that dependencies resolve correctly."""
        try:
            subprocess.run(
                ["uv", "sync", "--check"],
                cwd=self.template_path,
                capture_output=True,
                text=True,
                check=True,
            )
            logger.info("Dependency resolution test passed")
            return True
        except subprocess.CalledProcessError as e:
            logger.error(f"Dependency resolution failed: {e.stderr}")
            return False

    def commit_version_update(self, sdk_version: str):
        """Commit the version update."""
        try:
            subprocess.run(
                ["git", "add", "pyproject.toml"], cwd=self.template_path, check=True
            )
            subprocess.run(
                [
                    "git",
                    "commit",
                    "-m",
                    f"chore: update kailash dependency to v{sdk_version}",
                ],
                cwd=self.template_path,
                check=True,
            )
            logger.info(f"Committed version update to v{sdk_version}")
            return True
        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to commit: {e}")
            return False

    def sync_version(self, dry_run: bool = False, commit: bool = False):
        """Complete version sync process."""
        logger.info("Starting version sync...")

        # Get current versions
        sdk_version = self.get_sdk_version()
        current_template_dep = self.get_template_kailash_version()

        logger.info(f"SDK version: {sdk_version}")
        logger.info(f"Template dependency: {current_template_dep}")

        # Check if update needed
        if f"kailash=={sdk_version}" in current_template_dep:
            logger.info("Template is already up to date")
            return True

        # Update template
        self.update_template_version(sdk_version, dry_run)

        if not dry_run:
            # Test dependencies
            if not self.test_dependency_resolution():
                logger.error("Dependency test failed, not committing")
                return False

            # Commit if requested
            if commit:
                return self.commit_version_update(sdk_version)

        return True


def main():
    parser = argparse.ArgumentParser(
        description="Sync Kailash SDK version between repositories"
    )
    parser.add_argument(
        "--sdk-path",
        default="../kailash_python_sdk",
        help="Path to SDK repository (default: ../kailash_python_sdk)",
    )
    parser.add_argument(
        "--template-path",
        default=".",
        help="Path to template repository (default: current directory)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be done without making changes",
    )
    parser.add_argument(
        "--commit", action="store_true", help="Commit the changes after updating"
    )

    args = parser.parse_args()

    syncer = VersionSyncer(args.sdk_path, args.template_path)
    success = syncer.sync_version(dry_run=args.dry_run, commit=args.commit)

    if success:
        logger.info("Version sync completed successfully")
    else:
        logger.error("Version sync failed")
        exit(1)


if __name__ == "__main__":
    main()
