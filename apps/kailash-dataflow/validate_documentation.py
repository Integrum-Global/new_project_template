#!/usr/bin/env python3
"""
DataFlow Documentation Validation Script

Validates that all documentation paths referenced in CLAUDE.md exist
and that examples can be executed successfully.
"""

import importlib.util
import os
import shutil
import subprocess
import sys
import tempfile
import traceback
from pathlib import Path
from typing import Dict, List, Optional, Tuple


class DataFlowValidator:
    """Validates DataFlow documentation and examples."""

    def __init__(self):
        self.base_path = Path(__file__).parent
        self.errors = []
        self.warnings = []
        self.successes = []

    def validate_all(self) -> bool:
        """Run all validation checks."""
        print("🔍 DataFlow Documentation Validation")
        print("=" * 50)

        # Check directory structure
        self.check_directory_structure()

        # Validate documentation links
        self.validate_documentation_links()

        # Test code examples
        self.test_code_examples()

        # Validate example projects
        self.validate_example_projects()

        # Check deployment files
        self.check_deployment_files()

        # Print results
        self.print_results()

        return len(self.errors) == 0

    def check_directory_structure(self):
        """Check that all required directories exist."""
        print("\n📁 Checking directory structure...")

        required_dirs = [
            "docs",
            "docs/getting-started",
            "docs/development",
            "docs/workflows",
            "docs/production",
            "docs/advanced",
            "docs/comparisons",
            "examples",
            "examples/simple-crud",
            "examples/enterprise",
            "examples/data-migration",
            "examples/api-backend",
            "deployment",
            "deployment/docker",
            "deployment/kubernetes",
            "deployment/scripts",
            "tests",
            "tests/unit",
            "tests/integration",
            "tests/e2e",
            "src",
            "src/kailash_dataflow",
        ]

        for dir_path in required_dirs:
            full_path = self.base_path / dir_path
            if full_path.exists():
                self.successes.append(f"✓ Directory exists: {dir_path}")
            else:
                self.errors.append(f"✗ Missing directory: {dir_path}")

    def validate_documentation_links(self):
        """Validate all documentation files referenced in CLAUDE.md."""
        print("\n📄 Validating documentation links...")

        # Read CLAUDE.md
        claude_md_path = self.base_path / "CLAUDE.md"
        if not claude_md_path.exists():
            self.errors.append("✗ CLAUDE.md not found")
            return

        with open(claude_md_path, "r") as f:
            content = f.read()

        # Extract all markdown links
        import re

        link_pattern = r"\[([^\]]+)\]\(([^\)]+\.md)\)"
        links = re.findall(link_pattern, content)

        for link_text, link_path in links:
            # Skip external links
            if link_path.startswith("http"):
                continue

            # Check if file exists
            full_path = self.base_path / link_path
            if full_path.exists():
                self.successes.append(f"✓ Link valid: {link_path}")
            else:
                self.errors.append(f"✗ Broken link: {link_path} ('{link_text}')")

    def test_code_examples(self):
        """Test that code examples in documentation can execute."""
        print("\n🧪 Testing code examples...")

        # Test basic pattern from CLAUDE.md
        test_code = """
from kailash_dataflow import DataFlow
from kailash.workflow.builder import WorkflowBuilder
from kailash.runtime.local import LocalRuntime

# Test basic pattern
db = DataFlow()

@db.model
class User:
    name: str
    email: str
    active: bool = True

# Test workflow creation
workflow = WorkflowBuilder()
workflow.add_node("UserCreateNode", "create_user", {
    "name": "Test User",
    "email": "test@example.com"
})

print("✓ Basic pattern works")
"""

        # Create temporary file and test
        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write(test_code)
            temp_file = f.name

        try:
            # Add src to path for imports
            env = os.environ.copy()
            env["PYTHONPATH"] = (
                str(self.base_path / "src") + ":" + env.get("PYTHONPATH", "")
            )

            result = subprocess.run(
                [sys.executable, temp_file], capture_output=True, text=True, env=env
            )

            if result.returncode == 0:
                self.successes.append("✓ Basic code pattern executes successfully")
            else:
                self.errors.append(f"✗ Basic code pattern failed: {result.stderr}")
        except Exception as e:
            self.errors.append(f"✗ Error testing basic pattern: {str(e)}")
        finally:
            os.unlink(temp_file)

    def validate_example_projects(self):
        """Validate that example projects have required files."""
        print("\n📦 Validating example projects...")

        examples = ["simple-crud", "enterprise", "data-migration", "api-backend"]

        for example in examples:
            example_path = self.base_path / "examples" / example

            if not example_path.exists():
                self.errors.append(f"✗ Example missing: {example}")
                continue

            # Check for README
            if (example_path / "README.md").exists():
                self.successes.append(f"✓ {example}/README.md exists")

                # Check README has required sections
                with open(example_path / "README.md", "r") as f:
                    content = f.read()

                required_sections = ["Overview", "Usage", "Requirements"]
                for section in required_sections:
                    if f"## {section}" in content:
                        self.successes.append(f"✓ {example} has {section} section")
                    else:
                        self.warnings.append(f"⚠ {example} missing {section} section")
            else:
                self.errors.append(f"✗ {example}/README.md missing")

    def check_deployment_files(self):
        """Check deployment configuration files."""
        print("\n🚀 Checking deployment files...")

        deployment_files = [
            "deployment/docker/Dockerfile",
            "deployment/docker/docker-compose.yml",
            "deployment/kubernetes/dataflow-deployment.yaml",
            "deployment/kubernetes/postgres-deployment.yaml",
            "deployment/kubernetes/redis-deployment.yaml",
            "deployment/scripts/deploy.sh",
        ]

        for file_path in deployment_files:
            full_path = self.base_path / file_path
            if full_path.exists():
                self.successes.append(f"✓ Deployment file exists: {file_path}")

                # Check if script is executable
                if file_path.endswith(".sh"):
                    if os.access(full_path, os.X_OK):
                        self.successes.append(f"✓ Script is executable: {file_path}")
                    else:
                        self.warnings.append(f"⚠ Script not executable: {file_path}")
            else:
                self.errors.append(f"✗ Missing deployment file: {file_path}")

    def print_results(self):
        """Print validation results."""
        print("\n" + "=" * 50)
        print("📊 Validation Results")
        print("=" * 50)

        # Print successes
        print(f"\n✅ Successes ({len(self.successes)}):")
        if len(self.successes) > 10:
            print(f"   ... {len(self.successes)} checks passed")
        else:
            for success in self.successes:
                print(f"   {success}")

        # Print warnings
        if self.warnings:
            print(f"\n⚠️  Warnings ({len(self.warnings)}):")
            for warning in self.warnings:
                print(f"   {warning}")

        # Print errors
        if self.errors:
            print(f"\n❌ Errors ({len(self.errors)}):")
            for error in self.errors:
                print(f"   {error}")

        # Calculate score
        total_checks = len(self.successes) + len(self.warnings) + len(self.errors)
        if total_checks > 0:
            success_rate = (len(self.successes) / total_checks) * 100
            print(f"\n📈 Success Rate: {success_rate:.1f}%")

            if success_rate == 100:
                print("🎉 Perfect! All validation checks passed!")
            elif success_rate >= 90:
                print("👍 Good! Most validation checks passed.")
            elif success_rate >= 70:
                print("⚠️  Fair. Several issues need attention.")
            else:
                print("❌ Poor. Many issues need to be fixed.")


def main():
    """Main entry point."""
    validator = DataFlowValidator()

    success = validator.validate_all()

    # Exit with appropriate code
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
