"""
Macros for generating commandAGI2 documentation.
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

    index_content = "# Examples\n\nThis section contains examples demonstrating various aspects of commandAGI2.\n\n"

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
    base_dir = Path("commandAGI2")
    if not base_dir.exists():
        return f"Error: Package directory {base_dir} not found"

    # Output directory for API docs
    output_base_dir = Path("docs/api")
    ensure_directory_exists(output_base_dir)

    # Define which second-level directories should have their own subpages
    important_subdirs = [
        "computers/provisioners",
        "gym/agents",
        "gym/environments",
        "processors/screen_parser",
    ]

    # Track all modules to document
    modules = []

    # Track top-level directories and their modules
    top_level_dirs = {}
    subdir_modules = {}

    # Initialize subdir_modules for each important subdir
    for subdir in important_subdirs:
        subdir_modules[subdir] = []

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
                full_module_path = (
                    f"{module_path}.{module_name}"
                    if module_path != "."
                    else module_name
                )

                # Convert snake_case to Title Case for display
                display_name = module_name.replace("_", " ").title()

                # Determine if this is a top-level module or belongs to a specific subdir
                rel_dir_path = os.path.relpath(root, start=base_dir)
                rel_dir_path = rel_dir_path.replace(
                    "\\", "/"
                )  # Normalize path separators
                if rel_dir_path == ".":
                    rel_dir_path = ""

                # Create module info
                module_info = {
                    "name": display_name,
                    "path": full_module_path,
                    "rel_dir": rel_dir_path,
                }

                # Check if this belongs to an important subdir
                is_important_subdir = False
                for subdir in important_subdirs:
                    if rel_dir_path == subdir:
                        subdir_modules[subdir].append(module_info)
                        is_important_subdir = True
                        break

                # If not in an important subdir, add to top-level dir
                if not is_important_subdir:
                    # Get top-level directory
                    if rel_dir_path == "":
                        top_dir = "root"
                    else:
                        top_dir = rel_dir_path.split("/")[0]

                    if top_dir not in top_level_dirs:
                        top_level_dirs[top_dir] = []

                    top_level_dirs[top_dir].append(module_info)

                # Add to all modules list
                modules.append(module_info)

    # Create documentation pages for each module
    for module in modules:
        # Determine the output directory
        rel_dir = module["rel_dir"]

        # Check if this is in an important subdir
        is_in_important_subdir = False
        for subdir in important_subdirs:
            if rel_dir == subdir:
                # Create the important subdir path
                subdir_parts = subdir.split("/")
                top_dir = subdir_parts[0]
                sub_dir = subdir_parts[1]
                output_dir = output_base_dir / top_dir / sub_dir
                is_in_important_subdir = True
                break

        if not is_in_important_subdir:
            # Handle top-level modules
            if rel_dir == "":
                output_dir = output_base_dir
            else:
                # Only create top-level directory
                top_dir = rel_dir.split("/")[0]
                output_dir = output_base_dir / top_dir

        ensure_directory_exists(output_dir)

        # Output file path
        module_name = module["path"].split(".")[-1]
        output_file = output_dir / f"{module_name}.md"

        # Create the documentation page
        doc_content = template.replace("MODULE_NAME", module["name"]).replace(
            "MODULE_PATH", module["path"]
        )

        # Write the documentation page
        with open(output_file, "w", encoding="utf-8") as f:
            f.write(doc_content)

    # Create or preserve index pages for top-level directories
    for top_dir, dir_modules in top_level_dirs.items():
        if top_dir == "root":
            index_path = output_base_dir / "index.md"
            title = "commandAGI2 API"
        else:
            index_path = output_base_dir / top_dir / "index.md"
            title = f"{top_dir.replace('_', ' ').title()} API"

        ensure_directory_exists(index_path.parent)

        # Check if the index file already exists
        if index_path.exists():
            # Preserve the existing index file
            continue

        # Generate a new index file if it doesn't exist
        index_content = f"# {title}\n\nThis section contains documentation for the {top_dir} modules.\n\n"

        for module in sorted(dir_modules, key=lambda m: m["name"]):
            module_name = module["path"].split(".")[-1]
            index_content += f"- [{module['name']}]({module_name}.md)\n"

        # Add links to important subdirectories if they exist
        for subdir in important_subdirs:
            if subdir.startswith(f"{top_dir}/"):
                subdir_name = subdir.split("/")[-1]
                display_name = subdir_name.replace("_", " ").title()
                index_content += f"- [{display_name}]({subdir_name}/index.md)\n"

        with open(index_path, "w", encoding="utf-8") as f:
            f.write(index_content)

    # Create or preserve index pages for important subdirectories
    for subdir, subdir_modules_list in subdir_modules.items():
        if not subdir_modules_list:
            continue

        # Create the path for the subdir index
        subdir_parts = subdir.split("/")
        top_dir = subdir_parts[0]
        sub_dir = subdir_parts[1]
        index_path = output_base_dir / top_dir / sub_dir / "index.md"
        ensure_directory_exists(index_path.parent)

        # Check if the index file already exists
        if index_path.exists():
            # Preserve the existing index file
            continue

        display_name = sub_dir.replace("_", " ").title()

        index_content = f"# {display_name} API\n\nThis section contains documentation for the {display_name} modules.\n\n"

        for module in sorted(subdir_modules_list, key=lambda m: m["name"]):
            module_name = module["path"].split(".")[-1]
            index_content += f"- [{module['name']}]({module_name}.md)\n"

        with open(index_path, "w", encoding="utf-8") as f:
            f.write(index_content)

    # Create or preserve main API index page
    main_index_path = output_base_dir / "index.md"

    # Check if the main index file already exists
    if not main_index_path.exists():
        # Generate a new main index file if it doesn't exist
        main_index_content = "# commandAGI2 API Reference\n\n"
        main_index_content += (
            "This section contains the API reference for commandAGI2.\n\n"
        )

        # Add links to top-level directories
        for top_dir in sorted(top_level_dirs.keys()):
            if top_dir == "root":
                continue
            display_name = top_dir.replace("_", " ").title()
            main_index_content += f"- [{display_name}]({top_dir}/index.md)\n"

        # Add links to root modules
        if "root" in top_level_dirs:
            main_index_content += "\n## Core Modules\n\n"
            for module in sorted(top_level_dirs["root"], key=lambda m: m["name"]):
                module_name = module["path"].split(".")[-1]
                main_index_content += f"- [{module['name']}]({module_name}.md)\n"

        with open(main_index_path, "w", encoding="utf-8") as f:
            f.write(main_index_content)

    return f"Generated API documentation for {len(modules)} modules"


def update_api_indexes():
    """
    Update the API index files with improved content and organization.

    Returns:
        str: A message indicating the result of the operation
    """
    # Main API index
    main_index_path = Path("docs/api/index.md")
    main_index_content = """# commandAGI2 API Reference

This section contains the complete API reference for commandAGI2. The documentation is organized by major components of the framework.

## Top-Level Components

- **[Computers](computers/index.md)** - Core computer control interfaces and implementations
- **[Gym](gym/index.md)** - Reinforcement learning framework for training and evaluating agents
- **[Processors](processors/index.md)** - Screen parsing, text recognition, and other processing utilities
- **[Daemon](daemon/index.md)** - Remote control server and client components
- **[Utils](utils/index.md)** - Utility functions and helper classes
- **[Dev](dev/index.md)** - Development and testing utilities

## Core Modules

These modules provide the foundational types and functionality used throughout the framework:

- **[Types](types.md)** - Core data models and type definitions
- **[CLI](cli.md)** - Command-line interface for commandAGI2
- **[Version](version.md)** - Version information and compatibility utilities

## Key Subcomponents

- **[Provisioners](computers/provisioners/index.md)** - Environment provisioning for different platforms
- **[Agents](gym/agents/index.md)** - Agent implementations for the gym framework
- **[Environments](gym/environments/index.md)** - Environment implementations for the gym framework
- **[Screen Parser](processors/screen_parser/index.md)** - Screen parsing and text recognition utilities
"""
    with open(main_index_path, "w", encoding="utf-8") as f:
        f.write(main_index_content)

    # Computers index
    computers_index_path = Path("docs/api/computers/index.md")
    computers_index_content = """# Computers API

This section contains documentation for the computer control interfaces and implementations. Computers are the core abstraction in commandAGI2 that provide a unified interface for controlling different types of computers.

## Base Classes

- **[Base Computer](base_computer.md)** - Abstract base class defining the computer interface

## Computer Implementations

- **[Local Pynput Computer](local_pynput_computer.md)** - Control the local computer using the Pynput library
- **[Local PyAutoGUI Computer](local_pyautogui_computer.md)** - Control the local computer using the PyAutoGUI library
- **[E2B Desktop Computer](e2b_desktop_computer.md)** - Control a computer using the E2B Desktop API
- **[Daemon Client Computer](daemon_client_computer.md)** - Control a remote computer via the commandAGI2 daemon

## Subcomponents

- **[Provisioners](provisioners/index.md)** - Environment provisioning for different platforms (Docker, Kubernetes, cloud providers, etc.)
"""
    with open(computers_index_path, "w", encoding="utf-8") as f:
        f.write(computers_index_content)

    # Provisioners index
    provisioners_index_path = Path("docs/api/computers/provisioners/index.md")
    provisioners_index_content = """# Provisioners API

This section contains documentation for the provisioners that manage computer environments. Provisioners handle the creation, configuration, and cleanup of environments where computers run.

## Base Classes

- **[Base Provisioner](base_provisioner.md)** - Abstract base class defining the provisioner interface
- **[Manual Provisioner](manual_provisioner.md)** - Simple provisioner for manually managed environments

## Container Provisioners

- **[Docker Provisioner](docker_provisioner.md)** - Provision environments using Docker containers
- **[Kubernetes Provisioner](kubernetes_provisioner.md)** - Provision environments using Kubernetes pods

## Cloud Provisioners

- **[AWS Provisioner](aws_provisioner.md)** - Provision environments on Amazon Web Services
- **[Azure Provisioner](azure_provisioner.md)** - Provision environments on Microsoft Azure
- **[GCP Provisioner](gcp_provisioner.md)** - Provision environments on Google Cloud Platform

## Virtual Machine Provisioners

- **[VirtualBox Provisioner](virtualbox_provisioner.md)** - Provision environments using VirtualBox VMs
- **[VMware Provisioner](vmware_provisioner.md)** - Provision environments using VMware VMs
- **[Vagrant Provisioner](vagrant_provisioner.md)** - Provision environments using Vagrant
"""
    with open(provisioners_index_path, "w", encoding="utf-8") as f:
        f.write(provisioners_index_content)

    # Gym index
    gym_index_path = Path("docs/api/gym/index.md")
    gym_index_content = """# Gym API

This section contains documentation for the gym framework, which provides a standardized interface for training and evaluating AI agents that control computers. The gym framework is based on the OpenAI Gym/Gymnasium interface.

## Core Components

- **[Base](base.md)** - Base classes and utilities for the gym framework
- **[Schema](schema.md)** - Data schemas and validation for gym components
- **[Drivers](drivers.md)** - Drivers for connecting agents to environments
- **[Trainer](trainer.md)** - Training utilities for gym agents

## Environments

- **[Environments](environments/index.md)** - Environment implementations
- **[Computer Task](computer_task.md)** - Task definitions for computer environments

## Agents

- **[Agents](agents/index.md)** - Agent implementations
- **[Llms](llms.md)** - Language model integrations for agents
- **[Llm Based Evals](llm_based_evals.md)** - Evaluation utilities using language models

## Wrappers

- **[Grid Overlay Wrapper](grid_overlay_wrapper.md)** - Environment wrapper for grid-based interactions
- **[Screen Parser Wrapper](screen_parser_wrapper.md)** - Environment wrapper for screen parsing
- **[Gymnasium](gymnasium.md)** - Wrappers for compatibility with Gymnasium
"""
    with open(gym_index_path, "w", encoding="utf-8") as f:
        f.write(gym_index_content)

    # Gym Agents index
    gym_agents_index_path = Path("docs/api/gym/agents/index.md")
    gym_agents_index_content = """# Agents API

This section contains documentation for the agent implementations in the gym framework. Agents are responsible for making decisions and taking actions in environments.

## Base Classes

- **[Base Agent](base_agent.md)** - Abstract base class defining the agent interface

## Computer Agents

- **[Naive Vision Language Computer Agent](naive_vision_language_computer_agent.md)** - Simple agent that uses vision and language models to control computers
- **[React Vision Language Computer Agent](react_vision_language_computer_agent.md)** - Agent that uses the ReAct framework with vision and language models to control computers
"""
    with open(gym_agents_index_path, "w", encoding="utf-8") as f:
        f.write(gym_agents_index_content)

    # Gym Environments index
    gym_environments_index_path = Path("docs/api/gym/environments/index.md")
    gym_environments_index_content = """# Environments API

This section contains documentation for the environment implementations in the gym framework. Environments define the interface between agents and the systems they control.

## Base Classes

- **[Base Env](base_env.md)** - Abstract base class defining the environment interface

## Computer Environments

- **[Computer Env](computer_env.md)** - Environment for controlling computers through the Computer interface
- **[Multimodal Env](multimodal_env.md)** - Environment that supports multiple input and output modalities
"""
    with open(gym_environments_index_path, "w", encoding="utf-8") as f:
        f.write(gym_environments_index_content)

    # Processors index
    processors_index_path = Path("docs/api/processors/index.md")
    processors_index_content = """# Processors API

This section contains documentation for the processors that handle various types of data processing in commandAGI2. Processors transform raw data into useful information for computers and agents.

## Visual Processing

- **[Grid Overlay](grid_overlay.md)** - Overlay a grid on screenshots for precise coordinate-based interactions
- **[Screen Parser](screen_parser/index.md)** - Extract text and information from screenshots

## Audio Processing

- **[Whisper](whisper.md)** - Speech-to-text processing using OpenAI's Whisper model

## AI Models

- **[OpenAI](openai.md)** - Integration with OpenAI's models
- **[Some Local Model](some_local_model.md)** - Integration with local AI models
"""
    with open(processors_index_path, "w", encoding="utf-8") as f:
        f.write(processors_index_content)

    # Screen Parser index
    screen_parser_index_path = Path("docs/api/processors/screen_parser/index.md")
    screen_parser_index_content = """# Screen Parser API

This section contains documentation for the screen parser components that extract text and information from screenshots. Screen parsers are used to enable computers and agents to understand the content displayed on screens.

## Core Components

- **[Types](types.md)** - Data types and interfaces for screen parsing

## Parser Implementations

- **[Pytesseract Screen Parser](pytesseract_screen_parser.md)** - Screen parser using the Pytesseract OCR engine
- **[Screenparse AI Screen Parser](screenparse_ai_screen_parser.md)** - Screen parser using AI-based text recognition
"""
    with open(screen_parser_index_path, "w", encoding="utf-8") as f:
        f.write(screen_parser_index_content)

    # Daemon index
    daemon_index_path = Path("docs/api/daemon/index.md")
    daemon_index_content = """# Daemon API

This section contains documentation for the daemon components that enable remote control of computers. The daemon provides a server-client architecture for controlling computers over a network.

## Server Components

- **[Server](server.md)** - The daemon server that runs on the target computer and exposes a control API

## Client Components

- **[Client](client.md)** - Client library for connecting to and controlling a daemon server

## Command-line Interface

- **[CLI](cli.md)** - Command-line interface for managing daemon servers and clients
"""
    with open(daemon_index_path, "w", encoding="utf-8") as f:
        f.write(daemon_index_content)

    return "Updated API index files with improved content and organization"


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

    # Update API index files
    result.append("\nUpdating API index files...")
    update_result = update_api_indexes()
    result.append(update_result)

    result.append("\nDocumentation build complete!")

    return "\n".join(result)
