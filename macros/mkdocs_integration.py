"""
MkDocs integration functions for commandAGI2 documentation macros.
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


def define_env(env):
    """
    Define environment variables for MkDocs macros.

    This function is called by the MkDocs-macros plugin to register
    all the macros with the MkDocs environment.

    Args:
        env: The MkDocs environment object
    """
    # Register example macros
    env.macro(include_example_code)
    env.macro(include_example_output)
    env.macro(extract_example_status)
    env.macro(extract_example_description)
    env.macro(get_example_title)

    # Register documentation generator macros
    env.macro(generate_example_docs)
    env.macro(generate_api_docs)
    env.macro(build_docs)
    env.macro(generate_single_page_api_docs)
