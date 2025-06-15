#!/usr/bin/env python3
"""
Minimal QA Testing Script - Just specify the target app!
Everything else is automatic.
"""
import asyncio
import sys
from pathlib import Path

# ========== CHANGE THIS LINE ONLY ==========
TARGET_APP = "user_management"
# ===========================================

sys.path.insert(0, str(Path(__file__).parent))
from ..core.test_executor import AutonomousQATester


async def test_app():
    app_path = Path(__file__).parent / TARGET_APP
    tester = AutonomousQATester(app_path=app_path)

    # Auto-discover and test everything
    await tester.discover_app(app_path)
    tester.generate_personas()
    tester.generate_scenarios()
    summary = await tester.execute_tests()

    # Save results (HTML may fail but JSON always works)
    try:
        await tester.generate_report(format="both")
    except:
        await tester.generate_report(format="json")

    print(f"\n✅ Testing complete! Success rate: {summary.success_rate:.1f}%")
    print(f"📁 Results in: {app_path}/qa_results/")


if __name__ == "__main__":
    asyncio.run(test_app())
