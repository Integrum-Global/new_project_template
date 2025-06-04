"""
Basic CI setup tests to ensure template repository is properly configured.
"""

import pytest
from pathlib import Path
import yaml
import os


def test_project_structure():
    """Test that essential project structure exists."""
    root = Path(__file__).parent.parent.parent

    # Essential directories
    assert (root / "src").exists(), "src directory should exist"
    assert (root / "src" / "shared").exists(), "src/shared directory should exist"
    assert (root / "reference").exists(), "reference directory should exist"
    assert (root / "guide").exists(), "guide directory should exist"
    assert (root / "templates").exists(), "templates directory should exist"
    assert (root / "scripts").exists(), "scripts directory should exist"
    assert (root / "todos").exists(), "todos directory should exist"

    # Essential files
    assert (root / "pyproject.toml").exists(), "pyproject.toml should exist"
    assert (root / "README.md").exists(), "README.md should exist"
    assert (root / "Claude.md").exists(), "Claude.md should exist"


def test_github_workflows_exist():
    """Test that GitHub workflows are properly configured."""
    root = Path(__file__).parent.parent.parent
    workflows_dir = root / ".github" / "workflows"

    assert workflows_dir.exists(), ".github/workflows directory should exist"

    # Template sync workflows
    assert (
        workflows_dir / "sync-to-downstream.yml"
    ).exists(), "sync-to-downstream.yml should exist"
    assert (
        workflows_dir / "sync-from-template.yml"
    ).exists(), "sync-from-template.yml should exist"
    assert (
        workflows_dir / "template-cleanup.yml"
    ).exists(), "template-cleanup.yml should exist"


def test_workflow_yaml_syntax():
    """Test that workflow YAML files have valid syntax."""
    root = Path(__file__).parent.parent.parent
    workflows_dir = root / ".github" / "workflows"

    for workflow_file in workflows_dir.glob("*.yml"):
        with open(workflow_file, "r") as f:
            try:
                yaml.safe_load(f)
            except yaml.YAMLError as e:
                pytest.fail(f"Invalid YAML syntax in {workflow_file.name}: {e}")


def test_codeowners_exists():
    """Test that CODEOWNERS file exists and protects important directories."""
    root = Path(__file__).parent.parent.parent
    codeowners = root / ".github" / "CODEOWNERS"

    assert codeowners.exists(), "CODEOWNERS file should exist"

    content = codeowners.read_text()
    assert "/.github/" in content, "CODEOWNERS should protect .github directory"


def test_sync_scripts_exist():
    """Test that sync scripts are executable and exist."""
    root = Path(__file__).parent.parent.parent
    scripts_dir = root / "scripts"

    sync_script = scripts_dir / "sync_template.py"
    link_script = scripts_dir / "link-existing-repo.sh"

    assert sync_script.exists(), "sync_template.py should exist"
    assert link_script.exists(), "link-existing-repo.sh should exist"

    # Check if scripts are executable (on Unix-like systems)
    if os.name != "nt":  # Not Windows
        assert os.access(sync_script, os.X_OK), "sync_template.py should be executable"
        assert os.access(
            link_script, os.X_OK
        ), "link-existing-repo.sh should be executable"


def test_reference_documentation():
    """Test that reference documentation exists."""
    root = Path(__file__).parent.parent.parent
    reference_dir = root / "reference"

    essential_docs = [
        "api-registry.yaml",
        "validation-guide.md",
        "cheatsheet.md",
        "template-sync.md",
    ]

    for doc in essential_docs:
        assert (reference_dir / doc).exists(), f"{doc} should exist in reference/"


def test_template_sync_configuration():
    """Test that template sync configuration is properly set up."""
    root = Path(__file__).parent.parent.parent

    # Check sync-to-downstream workflow has required triggers
    sync_downstream = root / ".github" / "workflows" / "sync-to-downstream.yml"
    with open(sync_downstream, "r") as f:
        workflow = yaml.safe_load(f)

    # Handle the case where 'on' is parsed as True (boolean) due to YAML parsing
    triggers = workflow.get("on") or workflow.get(True)
    assert triggers is not None, "Workflow should have trigger configuration"
    assert "push" in triggers, "Should trigger on push"
    assert "schedule" in triggers, "Should have scheduled trigger"
    assert "workflow_dispatch" in triggers, "Should allow manual trigger"


def test_preserve_patterns():
    """Test that important preservation patterns are configured."""
    root = Path(__file__).parent.parent.parent
    sync_script = root / "scripts" / "sync_template.py"

    if sync_script.exists():
        content = sync_script.read_text()

        # Check for preservation patterns
        assert "src/solutions" in content, "Should preserve src/solutions"
        assert "data/*" in content, "Should preserve data directory"
        assert (
            "PRESERVE_PATTERNS" in content
        ), "Should have preservation patterns defined"


if __name__ == "__main__":
    pytest.main([__file__])
