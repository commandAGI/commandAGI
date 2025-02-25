#!/usr/bin/env python3
"""
Script to automatically generate documentation pages for all examples.
"""
import os
import re
from pathlib import Path


def main():
    """
    Generate documentation pages for all examples.
    """
    # Get the template
    template_path = Path("docs/examples/template.md")
    if not template_path.exists():
        print(f"Error: Template file {template_path} not found")
        return
    
    with open(template_path, "r", encoding="utf-8") as f:
        template = f.read()
    
    # Get all example files
    examples_dir = Path("examples")
    if not examples_dir.exists():
        print(f"Error: Examples directory {examples_dir} not found")
        return
    
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
        
        # Write the documentation page
        with open(doc_path, "w", encoding="utf-8") as f:
            f.write(doc_content)
        
        print(f"Generated documentation page for {example_file} at {doc_path}")
    
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
        title = get_example_title(example_path)
        
        # Add a link to the example documentation page
        index_content += f"- [{title}]({example_name}.md)\n"
    
    # Write the index page
    with open(index_path, "w", encoding="utf-8") as f:
        f.write(index_content)
    
    print(f"Generated examples index page at {index_path}")


def get_example_title(example_path):
    """
    Extract the title from an example file.
    
    Args:
        example_path: The path to the example file
        
    Returns:
        str: The title as a string
    """
    if not example_path.exists():
        return f"Example: {example_path.name}"
    
    try:
        with open(example_path, "r", encoding="utf-8") as f:
            content = f.read()
    except UnicodeDecodeError:
        # Try with a different encoding if utf-8 fails
        with open(example_path, "r", encoding="latin-1") as f:
            content = f.read()
    
    # Extract the docstring
    docstring_match = re.search(r'"""(.*?)"""', content, re.DOTALL)
    if not docstring_match:
        return f"Example: {example_path.name}"
    
    docstring = docstring_match.group(1).strip()
    
    # Get the first line (title)
    lines = docstring.split("\n")
    if lines and lines[0].strip():
        return lines[0].strip()
    
    return f"Example: {example_path.name}"


if __name__ == "__main__":
    main() 