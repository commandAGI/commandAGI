"""
Macros for handling example code in CommandLAB documentation.
"""

import os
import re
import subprocess
import tempfile
from pathlib import Path
from .utils import read_file_with_fallback_encoding, extract_docstring


def include_example_code(example_file):
    """
    Include the code from an example file.

    Args:
        example_file: The name of the example file (e.g., "1_getting_started.py")

    Returns:
        str: The code from the example file as a markdown code block
    """
    example_path = Path("examples") / example_file
    if not example_path.exists():
        return f"```\nError: Example file {example_file} not found\n```"

    code = read_file_with_fallback_encoding(example_path)
    return f"```python\n{code}\n```"


def include_example_output(example_file):
    """
    Run an example and include its output.

    Args:
        example_file: The name of the example file (e.g., "1_getting_started.py")

    Returns:
        str: The output from running the example as a markdown code block
    """
    example_path = Path("examples") / example_file
    if not example_path.exists():
        return f"```\nError: Example file {example_file} not found\n```"

    # Create a temporary file to capture output
    with tempfile.NamedTemporaryFile(delete=False) as tmp:
        tmp_path = tmp.name

    try:
        # Run the example and capture its output
        result = subprocess.run(
            ["python", str(example_path)],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            timeout=30,  # Timeout after 30 seconds
        )
        output = result.stdout
        if result.stderr:
            output += "\n" + result.stderr

        return f"```\n{output}\n```"
    except subprocess.TimeoutExpired:
        return "```\nError: Example execution timed out\n```"
    except Exception as e:
        return f"```\nError running example: {str(e)}\n```"
    finally:
        # Clean up the temporary file
        if os.path.exists(tmp_path):
            os.unlink(tmp_path)


def extract_example_status(example_file):
    """
    Extract the status information from an example file.

    Args:
        example_file: The name of the example file (e.g., "1_getting_started.py")

    Returns:
        str: The status information as markdown
    """
    example_path = Path("examples") / example_file
    if not example_path.exists():
        return "Status: Unknown"

    content = read_file_with_fallback_encoding(example_path)

    # Extract status information using regex
    status_match = re.search(r"Status:\s*(.*?)(?:\n|$)", content)
    if not status_match:
        return "Status: Not specified"

    status_line = status_match.group(1).strip()

    # Extract bullet points that follow the status line
    bullet_points = []
    for line in content.split("\n"):
        if line.strip().startswith("- ") and status_match.end() < content.index(line):
            # Stop if we hit another section
            if line.strip().startswith("- ") and line.strip().endswith(":"):
                break
            bullet_points.append(line.strip())

    # Format the status information as markdown
    result = f"## Status\n\n{status_line}\n"
    if bullet_points:
        result += "\n" + "\n".join(bullet_points) + "\n"

    return result


def extract_example_description(example_file):
    """
    Extract the description from an example file.

    Args:
        example_file: The name of the example file (e.g., "1_getting_started.py")

    Returns:
        str: The description as markdown
    """
    example_path = Path("examples") / example_file
    if not example_path.exists():
        return "Description: Unknown"

    content = read_file_with_fallback_encoding(example_path)
    docstring = extract_docstring(content)

    if not docstring:
        return "Description: Not provided"

    # Remove the first line (title) and status information
    lines = docstring.split("\n")
    if lines and lines[0].strip():
        title = lines[0].strip()
        lines = lines[1:]

    # Remove status lines
    filtered_lines = []
    skip_status = False
    for line in lines:
        if line.strip().startswith("Status:"):
            skip_status = True
            continue
        if skip_status and line.strip().startswith("- "):
            continue
        skip_status = False
        filtered_lines.append(line)

    description = "\n".join(filtered_lines).strip()
    return f"## Description\n\n{description}\n"


def get_example_title(example_file):
    """
    Extract the title from an example file.

    Args:
        example_file: The name of the example file (e.g., "1_getting_started.py")

    Returns:
        str: The title as a string
    """
    example_path = Path("examples") / example_file
    return get_example_title_internal(example_path)


def get_example_title_internal(example_path):
    """
    Extract the title from an example file.

    Args:
        example_path: The path to the example file

    Returns:
        str: The title as a string
    """
    if not example_path.exists():
        return f"Example: {example_path.name}"

    content = read_file_with_fallback_encoding(example_path)
    docstring = extract_docstring(content)

    if not docstring:
        return f"Example: {example_path.name}"

    # Get the first line (title)
    lines = docstring.split("\n")
    if lines and lines[0].strip():
        return lines[0].strip()

    return f"Example: {example_path.name}"
