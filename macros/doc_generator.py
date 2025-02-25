"""
Macros for generating CommandLAB documentation.
"""
import os
import re
import importlib
import pkgutil
from pathlib import Path
from .example_macros import get_example_title_internal
from .utils import ensure_directory_exists, read_file_with_fallback_encoding


def generate_example_docs():
    """
    Generate documentation pages for all examples.
    
    Returns:
        str: A message indicating the result of the operation
    """
    # Get the template
    template_path = Path("docs/examples/template.md")
    if not template_path.exists():
        return f"Error: Template file {template_path} not found"
    
    template = read_file_with_fallback_encoding(template_path)
    
    # Get all example files
    examples_dir = Path("examples")
    if not examples_dir.exists():
        return f"Error: Examples directory {examples_dir} not found"
    
    example_files = sorted([f for f in os.listdir(examples_dir) if f.endswith(".py")])
    
    # Create documentation pages for each example
    for example_file in example_files:
        # Extract the example name (without the number prefix and extension)
        match = re.match(r"\d+_(.+)\.py", example_file)
        if match:
            example_name = match.group(1)
        else:
            example_name = os.path.splitext(example_file)[0]
        
        # Create the documentation page
        doc_path = Path(f"docs/examples/{example_name}.md")
        
        # Replace the placeholder with the actual example filename
        doc_content = template.replace("EXAMPLE_FILENAME", example_file)
        
        # Ensure the directory exists
        ensure_directory_exists(doc_path.parent)
        
        # Write the documentation page
        with open(doc_path, "w", encoding="utf-8") as f:
            f.write(doc_content)
    
    # Create an index page for the examples
    index_path = Path("docs/examples/index.md")
    
    index_content = "# Examples\n\nThis section contains examples demonstrating various aspects of CommandLAB.\n\n"
    
    for example_file in example_files:
        # Extract the example name (without the number prefix and extension)
        match = re.match(r"\d+_(.+)\.py", example_file)
        if match:
            example_name = match.group(1)
        else:
            example_name = os.path.splitext(example_file)[0]
        
        # Get the example title
        example_path = examples_dir / example_file
        title = get_example_title_internal(example_path)
        
        # Add a link to the example documentation page
        index_content += f"- [{title}]({example_name}.md)\n"
    
    # Write the index page
    with open(index_path, "w", encoding="utf-8") as f:
        f.write(index_content)
    
    return f"Generated documentation for {len(example_files)} examples"


def generate_api_docs():
    """
    Generate API documentation pages by scanning the directory structure.
    
    Returns:
        str: A message indicating the result of the operation
    """
    # Get the template
    template_path = Path("docs/api/template.md")
    if not template_path.exists():
        return f"Error: Template file {template_path} not found"
    
    template = read_file_with_fallback_encoding(template_path)
    
    # Define the base package directory
    base_dir = Path("commandLAB")
    if not base_dir.exists():
        return f"Error: Package directory {base_dir} not found"
    
    # Output directory for API docs
    output_base_dir = Path("docs/api")
    ensure_directory_exists(output_base_dir)
    
    # Track all modules to document
    modules = []
    
    # Walk through the directory structure
    for root, dirs, files in os.walk(base_dir):
        # Convert path to module path
        rel_path = os.path.relpath(root, start=os.path.dirname(base_dir))
        module_path = rel_path.replace(os.sep, ".")
        
        # Skip __pycache__ directories
        dirs[:] = [d for d in dirs if d != "__pycache__"]
        
        # Process Python files
        for file in files:
            if file.endswith(".py") and not file.startswith("__"):
                # Get the module name without extension
                module_name = os.path.splitext(file)[0]
                
                # Full module path
                full_module_path = f"{module_path}.{module_name}" if module_path != "." else module_name
                
                # Convert snake_case to Title Case for display
                display_name = module_name.replace("_", " ").title()
                
                # Create output directory structure mirroring the package structure
                rel_output_dir = os.path.relpath(root, start=os.path.dirname(base_dir))
                output_dir = output_base_dir / rel_output_dir
                ensure_directory_exists(output_dir)
                
                # Output file path
                output_file = output_dir / f"{module_name}.md"
                
                modules.append({
                    "name": display_name,
                    "path": full_module_path,
                    "output": str(output_file)
                })
    
    # Create documentation pages for each module
    for module in modules:
        # Create the documentation page
        doc_content = template.replace("MODULE_NAME", module["name"]).replace("MODULE_PATH", module["path"])
        
        # Write the documentation page
        with open(module["output"], "w", encoding="utf-8") as f:
            f.write(doc_content)
    
    return f"Generated API documentation for {len(modules)} modules"


def build_docs():
    """
    Build all documentation.
    
    Returns:
        str: A message indicating the result of the operation
    """
    result = []
    
    # Generate example documentation
    result.append("Generating example documentation...")
    example_result = generate_example_docs()
    result.append(example_result)
    
    # Generate API documentation
    result.append("\nGenerating API documentation...")
    api_result = generate_api_docs()
    result.append(api_result)
    
    result.append("\nDocumentation build complete!")
    
    return "\n".join(result) 