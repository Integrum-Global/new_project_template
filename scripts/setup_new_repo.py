#!/usr/bin/env python3
"""
New Repository Setup Script

Automatically configures repositories created from this template to enable
automatic template synchronization and proper development workflow.
"""

import json
import logging
import os
import subprocess
import sys
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Required topics for template sync discovery
REQUIRED_TOPICS = ["kailash-template", "kailash", "business-solutions"]

# Default labels for issue tracking
DEFAULT_LABELS = [
    {
        "name": "template-sync",
        "color": "0075ca",
        "description": "Issues related to template synchronization",
    },
    {
        "name": "solution-development",
        "color": "008672",
        "description": "Solution-specific development tasks",
    },
    {
        "name": "kailash",
        "color": "1d76db",
        "description": "Issues related to Kailash SDK usage",
    },
    {
        "name": "documentation",
        "color": "d4c5f9",
        "description": "Documentation improvements",
    },
    {"name": "enhancement", "color": "a2eeef", "description": "New feature or request"},
]


class RepoSetup:
    """Handles automatic setup of new repositories from template."""

    def __init__(self):
        self.repo = os.environ.get("GITHUB_REPOSITORY", "")
        self.token = os.environ.get("GITHUB_TOKEN", "")

        if not self.repo:
            # Try to get from git remote
            try:
                result = subprocess.run(
                    ["git", "remote", "get-url", "origin"],
                    capture_output=True,
                    text=True,
                )
                if result.returncode == 0:
                    url = result.stdout.strip()
                    if "github.com" in url:
                        # Extract repo from URL
                        if url.startswith("https://"):
                            self.repo = url.split("github.com/")[1].replace(".git", "")
                        elif url.startswith("git@"):
                            self.repo = url.split("github.com:")[1].replace(".git", "")
            except Exception as e:
                logger.warning(f"Could not determine repository from git remote: {e}")

        if not self.repo:
            logger.error("Could not determine repository name")
            sys.exit(1)

        logger.info(f"Setting up repository: {self.repo}")

    def run_setup(self):
        """Run complete repository setup."""
        logger.info("Starting repository setup...")

        success = True

        # Add required topics
        if not self.add_topics():
            success = False

        # Create default labels
        if not self.create_labels():
            success = False

        # Setup environment files
        if not self.setup_environment():
            success = False

        # Initialize project structure
        if not self.init_project_structure():
            success = False

        if success:
            logger.info("✅ Repository setup completed successfully!")
            logger.info("🔄 Template sync is now automatically enabled")
            logger.info("📚 Review CLAUDE.md for development guidance")
        else:
            logger.warning("⚠️ Setup completed with some issues. Check logs above.")

        return success

    def add_topics(self) -> bool:
        """Add required topics for template discovery."""
        try:
            logger.info("Adding required topics...")

            # Get existing topics
            result = subprocess.run(
                ["gh", "api", f"/repos/{self.repo}", "--jq", ".topics"],
                capture_output=True,
                text=True,
            )

            existing_topics = []
            if result.returncode == 0:
                existing_topics = json.loads(result.stdout.strip())

            # Merge with required topics
            all_topics = list(set(existing_topics + REQUIRED_TOPICS))

            # Update topics
            topics_json = json.dumps({"names": all_topics})
            result = subprocess.run(
                [
                    "gh",
                    "api",
                    f"/repos/{self.repo}/topics",
                    "--method",
                    "PUT",
                    "--input",
                    "-",
                ],
                input=topics_json,
                text=True,
                capture_output=True,
            )

            if result.returncode == 0:
                logger.info(f"✅ Added topics: {REQUIRED_TOPICS}")
                return True
            else:
                logger.error(f"Failed to add topics: {result.stderr}")
                return False

        except Exception as e:
            logger.error(f"Error adding topics: {e}")
            return False

    def create_labels(self) -> bool:
        """Create default labels for issue tracking."""
        try:
            logger.info("Creating default labels...")

            success_count = 0
            for label in DEFAULT_LABELS:
                try:
                    label_json = json.dumps(label)
                    result = subprocess.run(
                        [
                            "gh",
                            "api",
                            f"/repos/{self.repo}/labels",
                            "--method",
                            "POST",
                            "--input",
                            "-",
                        ],
                        input=label_json,
                        text=True,
                        capture_output=True,
                    )

                    if result.returncode == 0:
                        success_count += 1
                    elif "already_exists" in result.stderr:
                        success_count += 1  # Label already exists, that's fine
                    else:
                        logger.warning(
                            f"Failed to create label '{label['name']}': {result.stderr}"
                        )

                except Exception as e:
                    logger.warning(f"Error creating label '{label['name']}': {e}")

            logger.info(
                f"✅ Created/verified {success_count}/{len(DEFAULT_LABELS)} labels"
            )
            return success_count > 0

        except Exception as e:
            logger.error(f"Error creating labels: {e}")
            return False

    def setup_environment(self) -> bool:
        """Setup environment files and configurations."""
        try:
            logger.info("Setting up environment files...")

            # Create .env.example if it doesn't exist
            env_example = Path(".env.example")
            if not env_example.exists():
                env_content = """# Kailash SDK Solution Environment Variables

# API Keys (replace with your actual keys)
OPENAI_API_KEY=your_openai_key_here
ANTHROPIC_API_KEY=your_anthropic_key_here

# Database Configuration
DATABASE_URL=sqlite:///solution.db
DATABASE_HOST=localhost
DATABASE_PORT=5432
DATABASE_NAME=solution_db
DATABASE_USER=solution_user
DATABASE_PASSWORD=your_password_here

# External Service Configuration
SHAREPOINT_TENANT_ID=your_tenant_id
SHAREPOINT_CLIENT_ID=your_client_id
SHAREPOINT_CLIENT_SECRET=your_client_secret

# Application Configuration
DEBUG=false
LOG_LEVEL=INFO
ENVIRONMENT=development

# Solution-Specific Variables
SOLUTION_NAME=my_solution
SOLUTION_VERSION=1.0.0
"""
                env_example.write_text(env_content)
                logger.info("✅ Created .env.example")

            # Create .gitignore additions for solution development
            gitignore = Path(".gitignore")
            gitignore_additions = """
# Solution Development
.env
.env.local
*.log
__pycache__/
*.pyc
*.pyo
*.pyd
.Python
env/
venv/
ENV/
env.bak/
venv.bak/

# Data files
data/private/
data/temp/
data/outputs/*.csv
data/outputs/*.json
data/outputs/*.xlsx
!data/outputs/.gitkeep

# IDE
.vscode/
.idea/
*.swp
*.swo

# OS
.DS_Store
Thumbs.db

# Solution artifacts
dist/
build/
*.egg-info/
"""

            if gitignore.exists():
                current_content = gitignore.read_text()
                if "# Solution Development" not in current_content:
                    gitignore.write_text(current_content + gitignore_additions)
                    logger.info("✅ Updated .gitignore")
            else:
                gitignore.write_text(gitignore_additions)
                logger.info("✅ Created .gitignore")

            return True

        except Exception as e:
            logger.error(f"Error setting up environment: {e}")
            return False

    def init_project_structure(self) -> bool:
        """Initialize basic project structure."""
        try:
            logger.info("Initializing project structure...")

            # Create essential directories
            directories = [
                "src/solutions",
                "data/inputs",
                "data/outputs",
                "data/configs",
                "data/samples",
                "examples",
                "docs/solution",
                "tests",
            ]

            for dir_path in directories:
                Path(dir_path).mkdir(parents=True, exist_ok=True)

                # Add .gitkeep to empty directories
                gitkeep = Path(dir_path) / ".gitkeep"
                if not any(Path(dir_path).iterdir()) and not gitkeep.exists():
                    gitkeep.touch()

            # Create initial solution template if src/solutions is empty
            solutions_dir = Path("src/solutions")
            if not any(solutions_dir.iterdir()) or only_gitkeep(solutions_dir):
                self.create_initial_solution_template()

            logger.info("✅ Project structure initialized")
            return True

        except Exception as e:
            logger.error(f"Error initializing project structure: {e}")
            return False

    def create_initial_solution_template(self):
        """Create initial solution template."""
        solution_name = self.repo.split("/")[-1]  # Use repo name as solution name
        solution_dir = Path(f"src/solutions/{solution_name}")
        solution_dir.mkdir(parents=True, exist_ok=True)

        # Create __init__.py
        init_file = solution_dir / "__init__.py"
        init_file.write_text(f'"""Solution: {solution_name}"""\n')

        # Create main workflow file
        workflow_file = solution_dir / "workflow.py"
        workflow_content = f'''"""
Main workflow for {solution_name} solution.

This file contains the primary workflow logic for the solution.
"""

from kailash import Workflow
from kailash.runtime.local import LocalRuntime
from kailash.nodes.data import CSVReaderNode, CSVWriterNode


def create_workflow() -> Workflow:
    """Create and configure the main workflow."""
    workflow = Workflow("{solution_name}_workflow", "Main {solution_name} workflow")

    # TODO: Add your nodes and connections here
    # Example:
    # workflow.add_node("reader", CSVReaderNode(), file_path="data/inputs/input.csv")
    # workflow.add_node("writer", CSVWriterNode(), file_path="data/outputs/output.csv")
    # workflow.connect("reader", "writer", mapping={{"data": "data"}})

    return workflow


def main():
    """Main entry point for the solution."""
    # Create workflow
    workflow = create_workflow()

    # Execute workflow
    runtime = LocalRuntime()
    results, run_id = runtime.execute(workflow)

    print(f"Workflow completed with run ID: {{run_id}}")
    print(f"Results: {{results}}")


if __name__ == "__main__":
    main()
'''
        workflow_file.write_text(workflow_content)

        # Create config file
        config_file = solution_dir / "config.py"
        config_content = f'''"""
Configuration for {solution_name} solution.
"""

import os
from pathlib import Path

# Solution metadata
SOLUTION_NAME = "{solution_name}"
SOLUTION_VERSION = "1.0.0"

# Paths
PROJECT_ROOT = Path(__file__).parent.parent.parent
DATA_DIR = PROJECT_ROOT / "data"
INPUT_DIR = DATA_DIR / "inputs"
OUTPUT_DIR = DATA_DIR / "outputs"
CONFIG_DIR = DATA_DIR / "configs"

# Ensure directories exist
INPUT_DIR.mkdir(parents=True, exist_ok=True)
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
CONFIG_DIR.mkdir(parents=True, exist_ok=True)

# Environment variables
DEBUG = os.getenv("DEBUG", "false").lower() == "true"
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
ENVIRONMENT = os.getenv("ENVIRONMENT", "development")

# External service configurations
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")

# Database configuration
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///solution.db")
'''
        config_file.write_text(config_content)

        # Create README
        readme_file = solution_dir / "README.md"
        readme_content = f"""# {solution_name.title()} Solution

## Overview

Brief description of what this solution does.

## Setup

1. Install dependencies:
   ```bash
   pip install kailash-sdk
   ```

2. Configure environment variables:
   ```bash
   cp .env.example .env
   # Edit .env with your actual values
   ```

3. Run the solution:
   ```bash
   python -m solutions.{solution_name}
   ```

## Configuration

- Input data: `data/inputs/`
- Output data: `data/outputs/`
- Configuration: `data/configs/`

## Development

- Follow the 5-phase development process outlined in `CLAUDE.md`
- Use `reference/` documentation for API details and patterns
- Track tasks in `todos/000-master.md`

## Testing

```bash
pytest tests/
```
"""
        readme_file.write_text(readme_content)

        logger.info(f"✅ Created initial solution template: {solution_name}")


def only_gitkeep(directory: Path) -> bool:
    """Check if directory only contains .gitkeep file."""
    files = list(directory.iterdir())
    return len(files) == 1 and files[0].name == ".gitkeep"


def main():
    """Main entry point."""
    if len(sys.argv) > 1 and sys.argv[1] == "--help":
        print(
            """
Repository Setup Script

This script automatically configures repositories created from the Kailash template
to enable automatic template synchronization and proper development workflow.

Usage:
  python scripts/setup_new_repo.py

Environment Variables:
  GITHUB_REPOSITORY - Repository name (detected automatically if not set)
  GITHUB_TOKEN - GitHub token for API access (optional, uses gh CLI if available)

The script will:
1. Add required topics for template sync discovery
2. Create default labels for issue tracking
3. Setup environment files (.env.example, .gitignore)
4. Initialize project structure (directories, templates)
5. Create initial solution template

After running this script, your repository will automatically receive
updates from the template repository.
"""
        )
        return

    setup = RepoSetup()
    success = setup.run_setup()
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
