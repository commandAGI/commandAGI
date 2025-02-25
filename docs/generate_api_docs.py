#!/usr/bin/env python3
"""
Script to automatically generate API documentation pages.
"""
import os
from pathlib import Path


def main():
    """
    Generate API documentation pages.
    """
    # Get the template
    template_path = Path("docs/api/template.md")
    if not template_path.exists():
        print(f"Error: Template file {template_path} not found")
        return
    
    with open(template_path, "r", encoding="utf-8") as f:
        template = f.read()
    
    # Define the API modules to document
    api_modules = [
        # Core
        {
            "name": "BaseComputer",
            "path": "commandLAB.computers.base_computer",
            "output": "docs/api/core/base_computer.md",
        },
        {
            "name": "Types",
            "path": "commandLAB.types",
            "output": "docs/api/core/types.md",
        },
        {
            "name": "Utilities",
            "path": "commandLAB.utils",
            "output": "docs/api/core/utils.md",
        },
        
        # Computers
        {
            "name": "LocalPynputComputer",
            "path": "commandLAB.computers.local_pynput_computer",
            "output": "docs/api/computers/local_pynput_computer.md",
        },
        {
            "name": "LocalPyAutoGUIComputer",
            "path": "commandLAB.computers.local_pyautogui_computer",
            "output": "docs/api/computers/local_pyautogui_computer.md",
        },
        {
            "name": "E2BDesktopComputer",
            "path": "commandLAB.computers.e2b_desktop_computer",
            "output": "docs/api/computers/e2b_desktop_computer.md",
        },
        {
            "name": "DaemonClientComputer",
            "path": "commandLAB.computers.daemon_client_computer",
            "output": "docs/api/computers/daemon_client_computer.md",
        },
        
        # Provisioners
        {
            "name": "BaseProvisioner",
            "path": "commandLAB.computers.provisioners.base_provisioner",
            "output": "docs/api/provisioners/base_provisioner.md",
        },
        {
            "name": "DockerProvisioner",
            "path": "commandLAB.computers.provisioners.docker_provisioner",
            "output": "docs/api/provisioners/docker_provisioner.md",
        },
        {
            "name": "KubernetesProvisioner",
            "path": "commandLAB.computers.provisioners.kubernetes_provisioner",
            "output": "docs/api/provisioners/kubernetes_provisioner.md",
        },
        {
            "name": "AWSProvisioner",
            "path": "commandLAB.computers.provisioners.aws_provisioner",
            "output": "docs/api/provisioners/aws_provisioner.md",
        },
        {
            "name": "AzureProvisioner",
            "path": "commandLAB.computers.provisioners.azure_provisioner",
            "output": "docs/api/provisioners/azure_provisioner.md",
        },
        {
            "name": "GCPProvisioner",
            "path": "commandLAB.computers.provisioners.gcp_provisioner",
            "output": "docs/api/provisioners/gcp_provisioner.md",
        },
        
        # Daemon
        {
            "name": "ComputerDaemon",
            "path": "commandLAB.daemon.server",
            "output": "docs/api/daemon/computer_daemon.md",
        },
        {
            "name": "DaemonClient",
            "path": "commandLAB.daemon.client",
            "output": "docs/api/daemon/daemon_client.md",
        },
        {
            "name": "CLI",
            "path": "commandLAB.daemon.cli",
            "output": "docs/api/daemon/cli.md",
        },
        
        # Gym Framework
        {
            "name": "BaseEnv",
            "path": "commandLAB.gym.environments.base_env",
            "output": "docs/api/gym/base_env.md",
        },
        {
            "name": "ComputerEnv",
            "path": "commandLAB.gym.environments.computer_env",
            "output": "docs/api/gym/computer_env.md",
        },
        {
            "name": "BaseAgent",
            "path": "commandLAB.gym.agents.base_agent",
            "output": "docs/api/gym/base_agent.md",
        },
        {
            "name": "NaiveComputerAgent",
            "path": "commandLAB.gym.agents.naive_vision_language_computer_agent",
            "output": "docs/api/gym/naive_computer_agent.md",
        },
        
        # Processors
        {
            "name": "ScreenParser",
            "path": "commandLAB.processors.screen_parser",
            "output": "docs/api/processors/screen_parser.md",
        },
        {
            "name": "GridOverlay",
            "path": "commandLAB.processors.grid_overlay",
            "output": "docs/api/processors/grid_overlay.md",
        },
    ]
    
    # Create documentation pages for each API module
    for module in api_modules:
        # Create the documentation page
        doc_content = template.replace("MODULE_NAME", module["name"]).replace("MODULE_PATH", module["path"])
        
        # Ensure the directory exists
        os.makedirs(os.path.dirname(module["output"]), exist_ok=True)
        
        # Write the documentation page
        with open(module["output"], "w", encoding="utf-8") as f:
            f.write(doc_content)
        
        print(f"Generated API documentation page for {module['name']} at {module['output']}")


if __name__ == "__main__":
    main() 