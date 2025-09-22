# Copyright (c) 2025 Jonathan Piette
# This file is part of TheOpenMusicBox and is licensed for non-commercial use only.
# See the LICENSE file for details.

"""Helper functions for Architecture Testing Suite.

Provides utilities for analyzing Python code structure, imports, and dependencies
to support automated architectural compliance testing.
"""

import ast
import glob
import os
from pathlib import Path
from typing import List, Set, Dict, Tuple
import re


def get_all_python_files(directory: str, exclude_patterns: List[str] = None) -> List[str]:
    """Retrieve all Python files in a directory recursively.

    Args:
        directory: Root directory to search
        exclude_patterns: List of patterns to exclude (e.g., ['__pycache__', 'test_'])

    Returns:
        List of Python file paths
    """
    exclude_patterns = exclude_patterns or ['__pycache__', '.pytest_cache']

    python_files = []
    pattern = f"{directory}/**/*.py"

    for file_path in glob.glob(pattern, recursive=True):
        # Skip excluded patterns
        should_exclude = any(pattern in file_path for pattern in exclude_patterns)
        if not should_exclude:
            python_files.append(file_path)

    return sorted(python_files)


def extract_imports_from_file(file_path: str) -> List[str]:
    """Extract all import statements from a Python file.

    Args:
        file_path: Path to Python file

    Returns:
        List of imported module names
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        tree = ast.parse(content)
        imports = []

        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    imports.append(alias.name)
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    imports.append(node.module)

        return imports

    except (SyntaxError, UnicodeDecodeError, FileNotFoundError) as e:
        print(f"Warning: Could not parse {file_path}: {e}")
        return []


def extract_class_names(file_path: str) -> List[str]:
    """Extract all class names from a Python file.

    Args:
        file_path: Path to Python file

    Returns:
        List of class names
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        tree = ast.parse(content)
        classes = []

        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                classes.append(node.name)

        return classes

    except (SyntaxError, UnicodeDecodeError, FileNotFoundError) as e:
        print(f"Warning: Could not parse {file_path}: {e}")
        return []


def path_to_module_name(file_path: str, base_path: str = "app/src/") -> str:
    """Convert file path to Python module name.

    Args:
        file_path: File path (e.g., 'app/src/domain/models/playlist.py')
        base_path: Base path to remove (e.g., 'app/src/')

    Returns:
        Module name (e.g., 'domain.models.playlist')
    """
    # Normalize path separators
    normalized_path = file_path.replace('\\', '/')

    # Remove base path
    if normalized_path.startswith(base_path):
        normalized_path = normalized_path[len(base_path):]

    # Remove .py extension
    if normalized_path.endswith('.py'):
        normalized_path = normalized_path[:-3]

    # Convert to module notation
    module_name = normalized_path.replace('/', '.')

    return module_name


def get_project_root() -> str:
    """Get the project root directory.

    Returns:
        Absolute path to project root
    """
    current_file = Path(__file__)
    # Navigate up from tests/architecture/helpers.py to project root
    project_root = current_file.parent.parent.parent
    return str(project_root.absolute())


def build_dependency_graph() -> Dict[str, List[str]]:
    """Build a dependency graph for the entire project.

    Returns:
        Dictionary mapping module names to their dependencies
    """
    project_root = get_project_root()
    app_src_path = os.path.join(project_root, "app", "src")

    dependency_graph = {}

    python_files = get_all_python_files(app_src_path)

    for file_path in python_files:
        module_name = path_to_module_name(file_path)
        imports = extract_imports_from_file(file_path)

        # Filter to only app.src imports
        app_imports = [imp for imp in imports if imp.startswith('app.src')]
        dependency_graph[module_name] = app_imports

    return dependency_graph


def find_circular_dependencies(dependency_graph: Dict[str, List[str]]) -> List[List[str]]:
    """Find circular dependencies in the dependency graph.

    Args:
        dependency_graph: Dictionary mapping modules to their dependencies

    Returns:
        List of circular dependency chains
    """
    def has_path(graph: Dict[str, List[str]], start: str, end: str, visited: Set[str] = None) -> bool:
        """Check if there's a path from start to end in the graph."""
        if visited is None:
            visited = set()

        if start == end:
            return True

        if start in visited:
            return False

        visited.add(start)

        for neighbor in graph.get(start, []):
            if has_path(graph, neighbor, end, visited.copy()):
                return True

        return False

    cycles = []

    for module in dependency_graph:
        for dependency in dependency_graph.get(module, []):
            if has_path(dependency_graph, dependency, module):
                cycle = [module, dependency]
                if cycle not in cycles and [dependency, module] not in cycles:
                    cycles.append(cycle)

    return cycles


def get_layer_from_module(module_name: str) -> str:
    """Determine the architectural layer from module name.

    Args:
        module_name: Module name (e.g., 'domain.models.playlist')

    Returns:
        Layer name ('domain', 'application', 'infrastructure', 'presentation', 'unknown')
    """
    if module_name.startswith('domain.'):
        return 'domain'
    elif module_name.startswith('application.'):
        return 'application'
    elif module_name.startswith('infrastructure.'):
        return 'infrastructure'
    elif module_name.startswith('routes.') or module_name.startswith('controllers.'):
        return 'presentation'
    elif module_name.startswith('services.'):
        # Services can be application or infrastructure depending on context
        return 'services'
    else:
        return 'unknown'


def validate_ddd_layer_dependencies(dependency_graph: Dict[str, List[str]]) -> List[str]:
    """Validate that dependencies follow DDD layer rules.

    DDD Rules:
    - Domain should not depend on any other layer
    - Application can depend on Domain only
    - Infrastructure can depend on Domain only
    - Presentation can depend on Application and Infrastructure

    Args:
        dependency_graph: Module dependency graph

    Returns:
        List of violation messages
    """
    violations = []

    for module, dependencies in dependency_graph.items():
        module_layer = get_layer_from_module(module)

        for dependency in dependencies:
            dependency_layer = get_layer_from_module(dependency)

            # Domain layer violations
            if module_layer == 'domain':
                if dependency_layer in ['application', 'infrastructure', 'presentation', 'services']:
                    violations.append(
                        f"❌ Domain layer violation: {module} → {dependency} "
                        f"(Domain cannot depend on {dependency_layer})"
                    )

            # Application layer violations
            elif module_layer == 'application':
                if dependency_layer in ['infrastructure', 'presentation']:
                    violations.append(
                        f"❌ Application layer violation: {module} → {dependency} "
                        f"(Application should only depend on Domain)"
                    )

            # Infrastructure layer violations
            elif module_layer == 'infrastructure':
                if dependency_layer in ['application', 'presentation']:
                    violations.append(
                        f"❌ Infrastructure layer violation: {module} → {dependency} "
                        f"(Infrastructure should only depend on Domain)"
                    )

    return violations


def check_naming_conventions() -> List[str]:
    """Check DDD naming conventions.

    Returns:
        List of naming convention violations
    """
    violations = []
    project_root = get_project_root()

    # Application Services should end with "ApplicationService"
    app_services_path = os.path.join(project_root, "app", "src", "application", "services")
    if os.path.exists(app_services_path):
        app_service_files = get_all_python_files(app_services_path)

        for file_path in app_service_files:
            if not file_path.endswith('application_service.py') and '__init__.py' not in file_path:
                violations.append(f"❌ Application service file should end with 'application_service.py': {file_path}")

            # Check class names
            classes = extract_class_names(file_path)
            for class_name in classes:
                if 'Service' in class_name and not class_name.endswith('ApplicationService'):
                    violations.append(f"❌ Application service class should end with 'ApplicationService': {class_name} in {file_path}")

    # Domain Services should end with "DomainService"
    domain_services_path = os.path.join(project_root, "app", "src", "domain", "services")
    if os.path.exists(domain_services_path):
        domain_service_files = get_all_python_files(domain_services_path)

        for file_path in domain_service_files:
            classes = extract_class_names(file_path)
            for class_name in classes:
                if 'Service' in class_name and not class_name.endswith('DomainService') and not class_name.endswith('Service'):
                    violations.append(f"❌ Domain service class should end with 'DomainService': {class_name} in {file_path}")

    # Repository interfaces should end with "Protocol" or "Repository"
    domain_repos_path = os.path.join(project_root, "app", "src", "domain", "repositories")
    if os.path.exists(domain_repos_path):
        repo_files = get_all_python_files(domain_repos_path)

        for file_path in repo_files:
            classes = extract_class_names(file_path)
            for class_name in classes:
                if 'Repository' in class_name and not (class_name.endswith('Protocol') or class_name.endswith('Repository')):
                    violations.append(f"❌ Domain repository should be interface (Protocol): {class_name} in {file_path}")

    return violations