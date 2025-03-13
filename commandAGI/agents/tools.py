from typing import Any, Optional, Type, Dict, List, Union
from pydantic import BaseModel
from commandAGI.computers.base_computer import BaseComputer
from langchain.tools import BaseTool
from pathlib import Path
from commandAGI.types import MouseButton, KeyboardKey

def shell_tool(computer: BaseComputer, extra_args: dict[str, Any] = {}):
    return BaseTool.from_function(
        name="shell",
        description="Use the shell to run commands",
        func=computer.shell,
        **extra_args
    )

# Define property-based tools for computer operations
class ComputerTools:
    """Tools for interacting with a computer."""
    
    def __init__(self, computer: BaseComputer):
        self.computer = computer
    
    @property
    def shell(self):
        """Execute a shell command on the computer."""
        return BaseTool.from_function(
            name="shell",
            description="Execute a shell command on the computer",
            func=self.computer.shell
        )
    
    @property
    def screenshot(self):
        """Take a screenshot of the computer display."""
        return BaseTool.from_function(
            name="screenshot",
            description="Take a screenshot of the computer display",
            func=self.computer.get_screenshot
        )
    
    @property
    def click(self):
        """Click at the specified coordinates on the computer screen."""
        return BaseTool.from_function(
            name="click",
            description="Click at the specified coordinates on the computer screen",
            func=self.computer.execute_click
        )
    
    @property
    def double_click(self):
        """Double-click at the specified coordinates on the computer screen."""
        return BaseTool.from_function(
            name="double_click",
            description="Double-click at the specified coordinates on the computer screen",
            func=self.computer.execute_double_click
        )
    
    @property
    def type_text(self):
        """Type text on the computer keyboard."""
        return BaseTool.from_function(
            name="type_text",
            description="Type text on the computer keyboard",
            func=self.computer.execute_type
        )
    
    @property
    def mouse_move(self):
        """Move the mouse to the specified coordinates on the computer screen."""
        return BaseTool.from_function(
            name="mouse_move",
            description="Move the mouse to the specified coordinates on the computer screen",
            func=self.computer.execute_mouse_move
        )
    
    @property
    def mouse_scroll(self):
        """Scroll the mouse wheel on the computer."""
        return BaseTool.from_function(
            name="mouse_scroll",
            description="Scroll the mouse wheel on the computer",
            func=self.computer.execute_mouse_scroll
        )
    
    @property
    def drag(self):
        """Drag from one position to another on the computer screen."""
        return BaseTool.from_function(
            name="drag",
            description="Drag from one position to another on the computer screen",
            func=self.computer.execute_drag
        )
    
    @property
    def keyboard_hotkey(self):
        """Execute a keyboard hotkey combination on the computer."""
        return BaseTool.from_function(
            name="keyboard_hotkey",
            description="Execute a keyboard hotkey combination on the computer",
            func=self.computer.execute_keyboard_hotkey
        )
    
    @property
    def run_process(self):
        """Run a process on the computer."""
        return BaseTool.from_function(
            name="run_process",
            description="Run a process on the computer",
            func=self.computer.run_process
        )
    
    @property
    def copy_to_computer(self):
        """Copy a file or directory to the computer."""
        return BaseTool.from_function(
            name="copy_to_computer",
            description="Copy a file or directory to the computer",
            func=self.computer.copy_to_computer
        )
    
    @property
    def copy_from_computer(self):
        """Copy a file or directory from the computer."""
        return BaseTool.from_function(
            name="copy_from_computer",
            description="Copy a file or directory from the computer",
            func=self.computer.copy_from_computer
        )
    
    @property
    def open_file(self):
        """Open a file on the computer."""
        return BaseTool.from_function(
            name="open_file",
            description="Open a file on the computer",
            func=self.computer.open
        )
    
    @property
    def get_layout_tree(self):
        """Get the UI layout tree of the computer."""
        return BaseTool.from_function(
            name="get_layout_tree",
            description="Get the UI layout tree of the computer",
            func=self.computer.get_layout_tree
        )
    
    @property
    def get_processes(self):
        """Get information about running processes on the computer."""
        return BaseTool.from_function(
            name="get_processes",
            description="Get information about running processes on the computer",
            func=self.computer.get_processes
        )
    
    @property
    def get_windows(self):
        """Get information about open windows on the computer."""
        return BaseTool.from_function(
            name="get_windows",
            description="Get information about open windows on the computer",
            func=self.computer.get_windows
        )

# Add the tools property to BaseComputer
def add_tools_to_computer(cls):
    """Add tools property to BaseComputer class."""
    @property
    def tools(self):
        """Get tools for interacting with this computer."""
        return ComputerTools(self)
    
    setattr(cls, 'tools', tools)
    return cls

# Apply the decorator to BaseComputer
BaseComputer = add_tools_to_computer(BaseComputer)
