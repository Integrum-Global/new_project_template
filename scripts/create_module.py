#!/usr/bin/env python3
"""
Create a new module from the module template.

Usage:
    python scripts/create_module.py <module_name>
"""

import argparse
import shutil
import sys
from pathlib import Path


def replace_placeholders(file_path: Path, module_name: str):
    """Replace [MODULE_NAME] placeholders in a file."""
    try:
        content = file_path.read_text()
        content = content.replace("[MODULE_NAME]", module_name)
        file_path.write_text(content)
    except Exception as e:
        print(f"Warning: Could not process {file_path}: {e}")


def create_module(module_name: str):
    """Create a new module from the template."""
    # Paths
    project_root = Path(__file__).parent.parent
    template_dir = project_root / "src" / "solutions" / "module_template"
    target_dir = project_root / "src" / "solutions" / module_name
    
    # Check if template exists
    if not template_dir.exists():
        print(f"Error: Template directory not found at {template_dir}")
        return 1
    
    # Check if target already exists
    if target_dir.exists():
        print(f"Error: Module '{module_name}' already exists at {target_dir}")
        return 1
    
    # Copy template
    print(f"Creating module '{module_name}' from template...")
    shutil.copytree(template_dir, target_dir)
    
    # Replace placeholders
    print("Customizing module files...")
    for file_path in target_dir.rglob("*"):
        if file_path.is_file() and file_path.suffix in [".py", ".md", ".txt", ""]:
            replace_placeholders(file_path, module_name)
    
    print(f"\n✅ Module '{module_name}' created successfully!")
    print(f"   Location: {target_dir}")
    print("\nNext steps:")
    print(f"1. Update {target_dir}/README.md with module description")
    print(f"2. Add requirements to {target_dir}/prd/")
    print(f"3. Document decisions in {target_dir}/adr/")
    print(f"4. Track tasks in {target_dir}/todos/000-master.md")
    print(f"5. Track mistakes in {target_dir}/mistakes/000-master.md")
    print(f"6. Implement nodes in {target_dir}/nodes/")
    print(f"7. Create workflows in {target_dir}/workflows/")
    print(f"8. Add tests in {target_dir}/tests/")
    print(f"9. Provide examples in {target_dir}/examples/")
    
    return 0


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Create a new module from the module template",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    
    parser.add_argument(
        "module_name",
        help="Name of the new module (use lowercase with underscores)",
    )
    
    args = parser.parse_args()
    
    # Validate module name
    if not args.module_name.replace("_", "").isalnum():
        print("Error: Module name should only contain letters, numbers, and underscores")
        return 1
    
    if args.module_name == "module_template":
        print("Error: Cannot create a module named 'module_template'")
        return 1
    
    return create_module(args.module_name)


if __name__ == "__main__":
    sys.exit(main())