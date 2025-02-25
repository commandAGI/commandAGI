"""
Computer implementations for commandLAB.

This package contains various computer implementations that can be used with commandLAB.
"""

from commandLAB.computers.base_computer import BaseComputer

# Import all computer implementations
try:
    from commandLAB.computers.local_pynput_computer import LocalPynputComputer
except ImportError:
    pass

try:
    from commandLAB.computers.local_pyautogui_computer import LocalPyAutoGUIComputer
except ImportError:
    pass

try:
    from commandLAB.computers.e2b_desktop_computer import E2BDesktopComputer
except ImportError:
    pass

try:
    from commandLAB.computers.daemon_client_computer import DaemonClientComputer
except ImportError:
    pass

__all__ = [
    "BaseComputer",
    "LocalPynputComputer",
    "LocalPyAutoGUIComputer",
    "E2BDesktopComputer",
    "DaemonClientComputer",
] 