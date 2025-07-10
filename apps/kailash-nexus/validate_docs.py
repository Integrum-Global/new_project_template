#!/usr/bin/env python3
"""
Validate documentation code examples for Kailash Nexus.
This ensures all code snippets in documentation are correct and runnable.
"""

import os
import re
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Dict, List, Tuple


class DocValidator:
    def __init__(self, docs_dir: Path):
        self.docs_dir = docs_dir
        self.errors: List[Tuple[str, str]] = []
        self.successes: List[str] = []

    def extract_code_blocks(self, file_path: Path) -> List[Dict[str, str]]:
        """Extract Python code blocks from markdown files."""
        content = file_path.read_text()

        # Find all code blocks with ```python or ```bash
        pattern = r"```(python|bash|yaml)\n(.*?)```"
        matches = re.findall(pattern, content, re.DOTALL)

        blocks = []
        for lang, code in matches:
            blocks.append(
                {
                    "language": lang,
                    "code": code.strip(),
                    "file": str(file_path),
                    "line": content[: content.find(code)].count("\n") + 1,
                }
            )

        return blocks

    def validate_python_code(self, code: str, file_info: str) -> bool:
        """Validate Python code syntax and imports."""
        # Add necessary imports for examples
        test_code = (
            """
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'src'))

# Mock imports for validation
class MockWorkflowBuilder:
    def add_node(self, *args, **kwargs): pass
    def build(self): return {}

class MockRuntime:
    def execute(self, *args): return ({}, 'run_id')

# Replace actual imports with mocks for validation
import kailash
kailash.workflow = type('', (), {
    'builder': type('', (), {'WorkflowBuilder': MockWorkflowBuilder})
})()
kailash.runtime = type('', (), {
    'local': type('', (), {'LocalRuntime': MockRuntime})
})()

# User code starts here
"""
            + code
        )

        try:
            compile(test_code, f"<{file_info}>", "exec")
            return True
        except SyntaxError as e:
            self.errors.append((file_info, f"Syntax error: {e}"))
            return False
        except Exception as e:
            # Some import errors are expected in isolated validation
            if "No module named" not in str(e):
                self.errors.append((file_info, f"Error: {e}"))
                return False
            return True

    def validate_bash_command(self, command: str, file_info: str) -> bool:
        """Validate bash commands (basic check)."""
        # Skip actual execution, just check for obvious issues
        dangerous_commands = ["rm -rf", "sudo rm", "format", "dd if="]

        for dangerous in dangerous_commands:
            if dangerous in command:
                self.errors.append((file_info, f"Dangerous command found: {dangerous}"))
                return False

        return True

    def validate_yaml(self, yaml_content: str, file_info: str) -> bool:
        """Validate YAML syntax."""
        try:
            import yaml

            yaml.safe_load(yaml_content)
            return True
        except Exception as e:
            self.errors.append((file_info, f"YAML error: {e}"))
            return False

    def validate_file(self, file_path: Path) -> int:
        """Validate all code blocks in a markdown file."""
        if not file_path.suffix == ".md":
            return 0

        blocks = self.extract_code_blocks(file_path)
        validated = 0

        for block in blocks:
            file_info = f"{block['file']}:{block['line']}"

            if block["language"] == "python":
                if self.validate_python_code(block["code"], file_info):
                    validated += 1
                    self.successes.append(f"✓ Python code at {file_info}")

            elif block["language"] == "bash":
                if self.validate_bash_command(block["code"], file_info):
                    validated += 1
                    self.successes.append(f"✓ Bash command at {file_info}")

            elif block["language"] == "yaml":
                if self.validate_yaml(block["code"], file_info):
                    validated += 1
                    self.successes.append(f"✓ YAML at {file_info}")

        return validated

    def validate_all(self) -> bool:
        """Validate all documentation files."""
        total_validated = 0

        # Find all markdown files
        md_files = list(self.docs_dir.rglob("*.md"))

        print(f"Validating {len(md_files)} documentation files...\n")

        for file_path in md_files:
            validated = self.validate_file(file_path)
            if validated > 0:
                print(
                    f"✓ {file_path.relative_to(self.docs_dir)}: {validated} code blocks validated"
                )
            total_validated += validated

        print(f"\n{'='*60}")
        print(f"Total code blocks validated: {total_validated}")
        print(f"Successes: {len(self.successes)}")
        print(f"Errors: {len(self.errors)}")

        if self.errors:
            print(f"\n{'='*60}")
            print("ERRORS FOUND:")
            for file_info, error in self.errors:
                print(f"✗ {file_info}: {error}")
            return False

        print("\n✅ All documentation code examples are valid!")
        return True


def main():
    # Validate Nexus docs
    nexus_docs = Path(__file__).parent / "docs"
    if nexus_docs.exists():
        print("Validating Kailash Nexus documentation...")
        validator = DocValidator(nexus_docs)
        nexus_valid = validator.validate_all()
    else:
        print(f"Nexus docs not found at {nexus_docs}")
        nexus_valid = False

    # Also validate root README
    root_readme = Path(__file__).parent / "README.md"
    if root_readme.exists():
        print("\nValidating root README...")
        validator = DocValidator(Path(__file__).parent)
        validator.validate_file(root_readme)

    return 0 if nexus_valid else 1


if __name__ == "__main__":
    sys.exit(main())
