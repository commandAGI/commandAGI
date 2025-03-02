"""
MkDocs macros for CommandLAB documentation.
"""

from .example_macros import (
    include_example_code,
    include_example_output,
    extract_example_status,
    extract_example_description,
    get_example_title,
)

from .doc_generator import (
    generate_example_docs,
    generate_api_docs,
    build_docs,
)

from .utils import generate_single_page_api_docs

# Import the define_env function for MkDocs integration
from .mkdocs_integration import define_env

# Export all public functions
__all__ = [
    # Example macros
    "include_example_code",
    "include_example_output",
    "extract_example_status",
    "extract_example_description",
    "get_example_title",
    # Documentation generator macros
    "generate_example_docs",
    "generate_api_docs",
    "build_docs",
    "generate_single_page_api_docs",
    # MkDocs integration
    "define_env",
]
