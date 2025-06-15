#!/usr/bin/env python3
"""
Test script to verify refactored workflows are using proper patterns.

This script checks that workflows are structured correctly without
requiring full service integration.
"""

import sys
import os
import importlib.util
import inspect
from typing import Dict, List, Tuple

# Add paths
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))


def analyze_workflow_file(filepath: str) -> Dict[str, any]:
    """
    Analyze a workflow file to check for proper patterns.
    
    Args:
        filepath: Path to the workflow file
        
    Returns:
        Analysis results
    """
    results = {
        "filename": os.path.basename(filepath),
        "uses_service_nodes": False,
        "uses_inline_pythoncode": False,
        "uses_http_api": False,
        "node_types": set(),
        "inline_code_lines": 0,
        "issues": []
    }
    
    try:
        with open(filepath, 'r') as f:
            content = f.read()
            
        # Check for service node imports
        if "from service_nodes import" in content or "ServiceNode" in content:
            results["uses_service_nodes"] = True
            
        # Check for HTTP API usage
        if "HTTPRequestNode" in content or "RESTClientNode" in content:
            results["uses_http_api"] = True
            
        # Count inline PythonCodeNode usage
        inline_code_count = content.count('"code": """')
        if inline_code_count > 0:
            results["uses_inline_pythoncode"] = True
            # Rough estimate of inline code lines
            results["inline_code_lines"] = content.count('\n', content.find('"code": """'))
            
        # Extract node types used
        import re
        node_pattern = r'builder\.add_node\("([^"]+)"'
        node_types = re.findall(node_pattern, content)
        results["node_types"] = set(node_types)
        
        # Check for specific anti-patterns
        if "generate_id()" in content and "service" not in content.lower():
            results["issues"].append("Implements ID generation instead of using service")
            
        if "password_hash" in content and "SecurityService" not in content:
            results["issues"].append("Implements password hashing instead of using SecurityService")
            
        if "role_assignments = []" in content and "RoleService" not in content:
            results["issues"].append("Implements role logic instead of using RoleService")
            
        if results["inline_code_lines"] > 50:
            results["issues"].append(f"Excessive inline code ({results['inline_code_lines']} lines)")
            
    except Exception as e:
        results["issues"].append(f"Error analyzing file: {str(e)}")
        
    return results


def check_workflow_directory(directory: str) -> List[Dict[str, any]]:
    """
    Check all workflow files in a directory.
    
    Args:
        directory: Directory path containing workflow scripts
        
    Returns:
        List of analysis results
    """
    results = []
    
    script_dir = os.path.join(directory, "scripts")
    if not os.path.exists(script_dir):
        return results
        
    for filename in os.listdir(script_dir):
        if filename.endswith('.py') and not filename.startswith('__'):
            filepath = os.path.join(script_dir, filename)
            analysis = analyze_workflow_file(filepath)
            results.append(analysis)
            
    return results


def print_analysis_report(workflow_type: str, analyses: List[Dict[str, any]]):
    """
    Print analysis report for workflows.
    
    Args:
        workflow_type: Type of workflows (admin, manager, user)
        analyses: List of analysis results
    """
    print(f"\n{'='*70}")
    print(f"{workflow_type.upper()} WORKFLOWS ANALYSIS")
    print('='*70)
    
    for analysis in analyses:
        status = "❌" if analysis["issues"] else "✅"
        refactored = "REFACTORED" if ("refactored" in analysis["filename"]) else "ORIGINAL"
        
        print(f"\n{status} {analysis['filename']} ({refactored})")
        print(f"  - Service Nodes: {'Yes' if analysis['uses_service_nodes'] else 'No'}")
        print(f"  - HTTP API: {'Yes' if analysis['uses_http_api'] else 'No'}")
        print(f"  - Inline Code: {'Yes' if analysis['uses_inline_pythoncode'] else 'No'}")
        
        if analysis["node_types"]:
            print(f"  - Node Types: {', '.join(sorted(analysis['node_types']))}")
            
        if analysis["issues"]:
            print("  - Issues:")
            for issue in analysis["issues"]:
                print(f"    • {issue}")


def main():
    """
    Main analysis function.
    """
    print("🔍 Analyzing User Management Workflows...")
    
    base_dir = os.path.join(os.path.dirname(__file__))
    
    # Analyze each workflow type
    workflow_types = ["admin_workflows", "manager_workflows", "user_workflows"]
    
    all_good = True
    
    for workflow_type in workflow_types:
        workflow_dir = os.path.join(base_dir, workflow_type)
        if os.path.exists(workflow_dir):
            analyses = check_workflow_directory(workflow_dir)
            print_analysis_report(workflow_type, analyses)
            
            # Check if any non-refactored workflows have issues
            for analysis in analyses:
                if "refactored" not in analysis["filename"] and analysis["issues"]:
                    all_good = False
    
    # Summary
    print(f"\n{'='*70}")
    print("SUMMARY")
    print('='*70)
    
    if all_good:
        print("✅ All workflows follow proper patterns!")
    else:
        print("❌ Some workflows need refactoring to use service components")
        print("\nRecommendations:")
        print("1. Replace inline PythonCodeNode business logic with service nodes")
        print("2. Use HTTPRequestNode to call app APIs instead of mock data")
        print("3. Leverage AuditLogNode for compliance tracking")
        print("4. Use proper SDK nodes for all operations")
    
    return 0 if all_good else 1


if __name__ == "__main__":
    sys.exit(main())