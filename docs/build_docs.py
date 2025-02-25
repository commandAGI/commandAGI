#!/usr/bin/env python3
"""
Script to build all documentation.
"""
import os
import subprocess
import sys


def main():
    """
    Build all documentation.
    """
    print("Building CommandLAB documentation...")
    
    # Generate example documentation
    print("\nGenerating example documentation...")
    try:
        subprocess.run([sys.executable, "docs/generate_example_docs.py"], check=True)
    except subprocess.CalledProcessError as e:
        print(f"Error generating example documentation: {e}")
        return
    
    # Generate API documentation
    print("\nGenerating API documentation...")
    try:
        subprocess.run([sys.executable, "docs/generate_api_docs.py"], check=True)
    except subprocess.CalledProcessError as e:
        print(f"Error generating API documentation: {e}")
        return
    
    print("\nDocumentation build complete!")
    print("Run 'mkdocs serve' to preview the documentation.")


if __name__ == "__main__":
    main() 