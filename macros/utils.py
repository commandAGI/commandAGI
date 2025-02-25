"""
Utility functions for CommandLAB documentation macros.
"""
import os
import re
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


def read_file_with_fallback_encoding(file_path, primary_encoding="utf-8", fallback_encoding="latin-1"):
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