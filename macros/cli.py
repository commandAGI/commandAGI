#!/usr/bin/env python3
"""
Command-line interface for commandAGI documentation macros.
"""
import sys
from pathlib import Path

# Import the build_docs function directly
from macros.doc_generator import build_docs
from macros.utils import generate_single_page_api_docs


def main():
    """
    Build all documentation using the macros.
    """
    print("Building commandAGI documentation...")

    # # Build the documentation using the macros
    # print("\nGenerating documentation...")
    # result = build_docs()
    # print(result)

    # Generate single-page API documentation
    print("\nGenerating single-page API documentation...")
    api_result = generate_single_page_api_docs()
    print(api_result)

    print("\nDocumentation build complete!")
    print("Run 'mkdocs serve' to preview the documentation.")


if __name__ == "__main__":
    main()
