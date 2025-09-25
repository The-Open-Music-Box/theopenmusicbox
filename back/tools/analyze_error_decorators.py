#!/usr/bin/env python3
"""
Analyze and report on error decorator usage in the codebase.

This script identifies potentially problematic uses of @handle_service_errors
in application service methods that should return dictionaries.
"""

import os
import re
from pathlib import Path
from typing import List, Dict, Tuple

# ANSI color codes for terminal output
RED = '\033[91m'
GREEN = '\033[92m'
YELLOW = '\033[93m'
BLUE = '\033[94m'
RESET = '\033[0m'
BOLD = '\033[1m'

def find_service_files(base_path: Path) -> List[Path]:
    """Find all Python files in application services."""
    service_paths = []

    # Application services (primary concern)
    app_services = base_path / "app/src/application/services"
    if app_services.exists():
        service_paths.extend(app_services.glob("*.py"))

    # Domain services (secondary check)
    domain_services = base_path / "app/src/domain/services"
    if domain_services.exists():
        service_paths.extend(domain_services.glob("*.py"))

    # Other services (for completeness)
    other_services = base_path / "app/src/services"
    if other_services.exists():
        # Exclude specific directories
        for file in other_services.glob("**/*.py"):
            if "error" not in str(file) and "response" not in str(file):
                service_paths.append(file)

    return service_paths

def analyze_file(file_path: Path) -> List[Dict]:
    """Analyze a single file for decorator issues."""
    issues = []

    with open(file_path, 'r') as f:
        lines = f.readlines()

    for i, line in enumerate(lines):
        if '@handle_service_errors' in line:
            # Look ahead to find the method signature
            method_found = False
            for j in range(i+1, min(i+5, len(lines))):
                if 'def ' in lines[j]:
                    method_line = lines[j].strip()
                    method_found = True

                    # Extract method name
                    method_match = re.search(r'def\s+(\w+)', method_line)
                    if method_match:
                        method_name = method_match.group(1)

                        # Check return type
                        return_type_match = re.search(r'->\s*([^:]+):', method_line)
                        return_type = return_type_match.group(1).strip() if return_type_match else "None"

                        # Determine if this is problematic
                        is_problematic = False
                        reason = ""

                        # Check if it's in application services
                        if "application/services" in str(file_path):
                            if "Dict" in return_type:
                                is_problematic = True
                                reason = "Application service returning Dict should not use @handle_service_errors"
                            elif return_type == "None" and method_name.startswith("_"):
                                is_problematic = True
                                reason = "Private methods should not use @handle_service_errors"

                        # Check if it's a use_case method
                        if "use_case" in method_name and "Dict" in return_type:
                            is_problematic = True
                            reason = "Use case methods should handle errors explicitly"

                        # Special check for methods that are called internally
                        internal_indicators = ["_handle", "_process", "_execute", "_validate"]
                        if any(indicator in method_name for indicator in internal_indicators):
                            is_problematic = True
                            reason = "Internal methods should not use @handle_service_errors"

                        if is_problematic:
                            issues.append({
                                'file': str(file_path),
                                'line': i + 1,
                                'method': method_name,
                                'return_type': return_type,
                                'reason': reason,
                                'severity': 'HIGH' if "application/services" in str(file_path) else 'MEDIUM'
                            })
                    break

    return issues

def generate_report(issues: List[Dict]) -> None:
    """Generate a formatted report of issues."""
    print(f"\n{BOLD}{'='*80}{RESET}")
    print(f"{BOLD}{BLUE}Error Decorator Analysis Report{RESET}")
    print(f"{BOLD}{'='*80}{RESET}\n")

    if not issues:
        print(f"{GREEN}✅ No issues found! All decorators appear to be used correctly.{RESET}")
        return

    # Group by severity
    high_severity = [i for i in issues if i['severity'] == 'HIGH']
    medium_severity = [i for i in issues if i['severity'] == 'MEDIUM']

    total = len(issues)
    print(f"{BOLD}Found {total} potential issues:{RESET}")
    print(f"  {RED}• HIGH severity: {len(high_severity)}{RESET}")
    print(f"  {YELLOW}• MEDIUM severity: {len(medium_severity)}{RESET}\n")

    # Print high severity issues
    if high_severity:
        print(f"{BOLD}{RED}HIGH SEVERITY ISSUES (Must Fix):{RESET}")
        print("-" * 80)
        for issue in high_severity:
            file_short = issue['file'].replace(str(Path.cwd()) + "/", "")
            print(f"\n📍 {BOLD}{file_short}:{issue['line']}{RESET}")
            print(f"   Method: {issue['method']}")
            print(f"   Return Type: {issue['return_type']}")
            print(f"   {RED}Issue: {issue['reason']}{RESET}")
            print(f"   {BOLD}Fix:{RESET} Remove @handle_service_errors and add explicit try/except")

    # Print medium severity issues
    if medium_severity:
        print(f"\n{BOLD}{YELLOW}MEDIUM SEVERITY ISSUES (Should Review):{RESET}")
        print("-" * 80)
        for issue in medium_severity:
            file_short = issue['file'].replace(str(Path.cwd()) + "/", "")
            print(f"\n📍 {BOLD}{file_short}:{issue['line']}{RESET}")
            print(f"   Method: {issue['method']}")
            print(f"   Return Type: {issue['return_type']}")
            print(f"   {YELLOW}Issue: {issue['reason']}{RESET}")

def generate_fix_script(issues: List[Dict]) -> None:
    """Generate a script to help fix the issues."""
    high_severity = [i for i in issues if i['severity'] == 'HIGH']

    if not high_severity:
        return

    print(f"\n{BOLD}{'='*80}{RESET}")
    print(f"{BOLD}{GREEN}Suggested Fixes:{RESET}")
    print(f"{BOLD}{'='*80}{RESET}\n")

    print("Here are the methods that need immediate attention:\n")

    for issue in high_severity[:5]:  # Show first 5 as examples
        file_short = issue['file'].replace(str(Path.cwd()) + "/", "")
        print(f"{BOLD}File: {file_short}{RESET}")
        print(f"Method: {issue['method']}")
        print("\nSuggested change:")
        print(f"{GREEN}# Remove: @handle_service_errors(...)")
        print(f"# Add explicit error handling:{RESET}")
        print("""
async def {method}(self, ...) -> Dict[str, Any]:
    try:
        # ... existing implementation
        return {{
            "success": True,
            "message": "Operation successful",
            "data": result
        }}
    except Exception as e:
        logger.error(f"Error in {method}: {{e}}")
        return {{
            "success": False,
            "message": f"Operation failed: {{str(e)}}",
            "error_type": "internal_error"
        }}
""".format(method=issue['method']))
        print("-" * 40)

def main():
    """Main execution function."""
    base_path = Path.cwd()

    print(f"{BOLD}{BLUE}Analyzing error decorator usage...{RESET}")

    # Find all service files
    service_files = find_service_files(base_path)
    print(f"Found {len(service_files)} service files to analyze")

    # Analyze each file
    all_issues = []
    for file_path in service_files:
        issues = analyze_file(file_path)
        all_issues.extend(issues)

    # Generate report
    generate_report(all_issues)

    # Generate fix suggestions
    if all_issues:
        generate_fix_script(all_issues)

    # Return exit code based on severity
    high_severity = [i for i in all_issues if i['severity'] == 'HIGH']
    if high_severity:
        print(f"\n{RED}{BOLD}⚠️  Action required: {len(high_severity)} high-severity issues found!{RESET}")
        return 1
    elif all_issues:
        print(f"\n{YELLOW}ℹ️  {len(all_issues)} medium-severity issues found for review.{RESET}")
        return 0
    else:
        print(f"\n{GREEN}✅ All clear! No issues found.{RESET}")
        return 0

if __name__ == "__main__":
    exit(main())