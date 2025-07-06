#!/usr/bin/env python3
"""
Setup validation script for AI Registry MCP Server.

This script checks for common setup issues and validates the environment.
"""

import os
import sys
from pathlib import Path


def check_python_version():
    """Check Python version compatibility."""
    print("🐍 Checking Python version...")

    version = sys.version_info
    if version.major == 3 and version.minor >= 8:
        print(f"✅ Python {version.major}.{version.minor}.{version.micro} is supported")
        return True
    else:
        print(
            f"❌ Python {version.major}.{version.minor}.{version.micro} is not supported. Need Python 3.8+"
        )
        return False


def check_required_files():
    """Check that required files exist."""
    print("\n📁 Checking required files...")

    base_path = Path(__file__).parent
    required_files = [
        "config.py",
        "server/__init__.py",
        "server/registry_server.py",
        "server/tools.py",
        "server/indexer.py",
        "server/cache.py",
        "nodes/__init__.py",
        "nodes/registry_search_node.py",
        "nodes/registry_analytics_node.py",
        "nodes/registry_compare_node.py",
        "workflows/__init__.py",
        "workflows/basic_search.py",
        "workflows/domain_analysis.py",
        "examples/__init__.py",
        "examples/quickstart.py",
    ]

    missing_files = []
    for file_path in required_files:
        full_path = base_path / file_path
        if full_path.exists():
            print(f"✅ {file_path}")
        else:
            print(f"❌ {file_path} - MISSING")
            missing_files.append(file_path)

    if missing_files:
        print(f"\n⚠️ {len(missing_files)} required files are missing!")
        return False
    else:
        print(f"\n✅ All {len(required_files)} required files are present")
        return True


def check_registry_data():
    """Check for the AI registry data file."""
    print("\n📊 Checking AI registry data...")

    # Check common locations for the registry file
    possible_paths = [
        Path("src/solutions/ai_registry/data/combined_ai_registry.json"),
        Path("../../../data/combined_ai_registry.json"),
        Path("../../../../data/combined_ai_registry.json"),
    ]

    for path in possible_paths:
        if path.exists():
            size_mb = path.stat().st_size / (1024 * 1024)
            print(f"✅ Found registry data: {path} ({size_mb:.1f} MB)")
            return True

    print("❌ AI registry data file not found")
    print("Expected locations:")
    for path in possible_paths:
        print(f"   - {path.absolute()}")
    print(
        "\n💡 The registry data should contain 187 AI use cases from ISO/IEC standards"
    )
    return False


def check_dependencies():
    """Check for required dependencies."""
    print("\n📦 Checking dependencies...")

    required_packages = [
        ("json", "Built-in JSON support"),
        ("pathlib", "Built-in path utilities"),
        ("typing", "Built-in type hints"),
        ("collections", "Built-in collections"),
        ("re", "Built-in regex"),
        ("threading", "Built-in threading"),
        ("asyncio", "Built-in async support"),
        ("difflib", "Built-in string similarity"),
        ("hashlib", "Built-in hashing"),
        ("time", "Built-in time utilities"),
    ]

    optional_packages = [
        ("kailash", "Kailash SDK for workflows"),
        ("mcp", "Model Context Protocol"),
        ("yaml", "YAML configuration support"),
        ("pytest", "Testing framework"),
    ]

    print("Required packages (built-in):")
    for package, description in required_packages:
        try:
            __import__(package)
            print(f"✅ {package} - {description}")
        except ImportError:
            print(f"❌ {package} - {description} - MISSING")

    print("\nOptional packages (external):")
    for package, description in optional_packages:
        try:
            __import__(package)
            print(f"✅ {package} - {description}")
        except ImportError:
            print(f"⚠️ {package} - {description} - Not installed")

    return True


def check_environment():
    """Check environment variables."""
    print("\n🌍 Checking environment...")

    env_vars = {
        "AI_REGISTRY_FILE": "Path to AI registry JSON file",
        "AI_REGISTRY_TRANSPORT": "MCP transport type (stdio/http)",
        "AI_REGISTRY_PORT": "HTTP port for MCP server",
        "AI_REGISTRY_CACHE_ENABLED": "Enable caching (true/false)",
        "AI_REGISTRY_LOG_LEVEL": "Logging level (DEBUG/INFO/WARNING/ERROR)",
    }

    print("Environment variables (optional):")
    for var, description in env_vars.items():
        value = os.environ.get(var)
        if value:
            print(f"✅ {var}={value}")
        else:
            print(f"📝 {var} - {description} (using default)")

    return True


def suggest_fixes():
    """Suggest fixes for common issues."""
    print("\n🔧 Common Setup Issues & Fixes:")
    print("-" * 50)

    print("\n1. Missing Kailash SDK:")
    print("   pip install kailash")

    print("\n2. Missing MCP package:")
    print("   pip install mcp")

    print("\n3. Missing AI registry data:")
    print("   - Ensure combined_ai_registry.json is in src/solutions/ai_registry/data/")
    print("   - File should contain ISO/IEC AI use case data")
    print("   - Check file permissions and encoding (UTF-8)")

    print("\n4. Import errors:")
    print("   - Ensure you're running from the project root")
    print("   - Check PYTHONPATH includes project directory")
    print("   - Verify all __init__.py files are present")

    print("\n5. Configuration issues:")
    print("   - Create config/ai_registry.yaml for custom settings")
    print("   - Set environment variables for specific overrides")
    print("   - Check file paths are correct for your system")

    print("\n6. Testing issues:")
    print("   - Install pytest: pip install pytest")
    print(
        "   - Run from project root: python -m pytest src/solutions/ai_registry/tests/"
    )
    print("   - Use the test_implementation.py script for basic validation")


def main():
    """Run all validation checks."""
    print("🔍 AI Registry MCP Server - Setup Validation")
    print("=" * 60)

    checks = [
        ("Python Version", check_python_version),
        ("Required Files", check_required_files),
        ("Registry Data", check_registry_data),
        ("Dependencies", check_dependencies),
        ("Environment", check_environment),
    ]

    results = []
    for check_name, check_func in checks:
        try:
            success = check_func()
            results.append((check_name, success))
        except Exception as e:
            print(f"❌ Error during {check_name} check: {e}")
            results.append((check_name, False))

    # Summary
    print("\n" + "=" * 60)
    print("📋 Validation Summary")
    print("=" * 60)

    passed = sum(1 for _, success in results if success)
    total = len(results)

    for check_name, success in results:
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status:<8} {check_name}")

    print("=" * 60)
    print(f"Result: {passed}/{total} checks passed")

    if passed == total:
        print("\n🎉 Setup validation successful!")
        print("\nNext steps:")
        print(
            "1. Run implementation test: python src/solutions/ai_registry/test_implementation.py"
        )
        print(
            '2. Try quickstart example: python -c "from apps.ai_registry.examples.quickstart import quickstart_basic_search; quickstart_basic_search()"'
        )
        print("3. Start MCP server: python -m apps.ai_registry")
    else:
        print(f"\n⚠️ {total - passed} validation checks failed.")
        suggest_fixes()

    return passed == total


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
