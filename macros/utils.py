"""
Utility functions for CommandLAB documentation macros.
"""

import os
import re
import importlib
import pkgutil
from pathlib import Path


def ensure_directory_exists(directory_path):
    """
    Ensure that a directory exists, creating it if necessary.

    Args:
        directory_path: The path to the directory

    Returns:
        Path: The path to the directory
    """
    path = Path(directory_path)
    os.makedirs(path, exist_ok=True)
    return path


def read_file_with_fallback_encoding(
    file_path, primary_encoding="utf-8", fallback_encoding="latin-1"
):
    """
    Read a file with a fallback encoding if the primary encoding fails.

    Args:
        file_path: The path to the file
        primary_encoding: The primary encoding to try
        fallback_encoding: The fallback encoding to use if the primary encoding fails

    Returns:
        str: The contents of the file
    """
    try:
        with open(file_path, "r", encoding=primary_encoding) as f:
            return f.read()
    except UnicodeDecodeError:
        with open(file_path, "r", encoding=fallback_encoding) as f:
            return f.read()


def extract_docstring(content):
    """
    Extract the docstring from a Python file content.

    Args:
        content: The content of the Python file

    Returns:
        str: The docstring, or None if no docstring is found
    """
    docstring_match = re.search(r'"""(.*?)"""', content, re.DOTALL)
    if not docstring_match:
        return None

    return docstring_match.group(1).strip()


def generate_single_page_api_docs():
    """
    Generate a single-page API documentation by scanning the codebase.

    This function scans the CommandLAB codebase and generates a single Markdown page
    containing documentation for all modules, organized by package structure.

    Returns:
        str: A message indicating the result of the operation
    """
    # Define the base package directory
    base_dir = Path("commandLAB")
    if not base_dir.exists():
        return f"Error: Package directory {base_dir} not found"

    # Output file for single-page API docs
    output_file = Path("docs/api/index.md")
    ensure_directory_exists(output_file.parent)

    # Initialize content with header
    content = "# CommandLAB API Reference\n\n"
    content += "This page contains the complete API reference for CommandLAB.\n\n"
    content += "## Table of Contents\n\n"

    # Track all modules to document
    modules = []

    # Walk through the directory structure
    for root, dirs, files in os.walk(base_dir):
        # Skip __pycache__ directories
        dirs[:] = [d for d in dirs if d != "__pycache__"]

        # Convert path to module path
        rel_path = os.path.relpath(root, start=os.path.dirname(base_dir))
        module_path = rel_path.replace(os.sep, ".")

        # Process Python files
        for file in files:
            if file.endswith(".py") and not file.startswith("__"):
                # Get the module name without extension
                module_name = os.path.splitext(file)[0]

                # Full module path
                full_module_path = (
                    f"{module_path}.{module_name}"
                    if module_path != "."
                    else module_name
                )

                # Convert snake_case to Title Case for display
                display_name = module_name.replace("_", " ").title()

                # Determine the module level for TOC indentation
                level = len(full_module_path.split(".")) - 1

                # Create module info
                module_info = {
                    "name": display_name,
                    "path": full_module_path,
                    "file_path": os.path.join(root, file),
                    "level": level,
                }

                # Add to modules list
                modules.append(module_info)

    # Sort modules by path for a logical order
    modules.sort(key=lambda m: m["path"])

    # Generate table of contents
    for module in modules:
        indent = "  " * module["level"]
        anchor = module["path"].replace(".", "-").lower()
        content += f"{indent}- [{module['name']}](#{anchor})\n"

    content += "\n---\n\n"

    # Generate module documentation
    for module in modules:
        # Add module header
        content += f"## {module['name']}\n\n"
        content += f"**Module Path:** `{module['path']}`\n\n"

        # Try to extract docstring from the file
        try:
            file_content = read_file_with_fallback_encoding(module["file_path"])
            docstring = extract_docstring(file_content)
            if docstring:
                content += f"{docstring}\n\n"
        except Exception as e:
            content += f"*Error extracting documentation: {str(e)}*\n\n"

        # Add a separator between modules
        content += "---\n\n"

    # Write the content to the output file
    with open(output_file, "w", encoding="utf-8") as f:
        f.write(content)

    return f"Generated single-page API documentation with {len(modules)} modules"
