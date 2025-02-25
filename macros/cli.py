#!/usr/bin/env python3
"""
Command-line interface for CommandLAB documentation macros.
"""
import sys
from pathlib import Path

# Import the build_docs function directly
from macros.doc_generator import build_docs


def main():
    """
    Build all documentation using the macros.
    """
    print("Building CommandLAB documentation...")
    
    # Build the documentation using the macros
    print("\nGenerating documentation...")
    result = build_docs()
    print(result)
    
    print("\nDocumentation build complete!")
    print("Run 'mkdocs serve' to preview the documentation.")


if __name__ == "__main__":
    main() 