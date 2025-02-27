"""
Type stubs for commandLAB.computers package.

This file provides type hints for the computers package without requiring
the actual dependencies to be installed, which is helpful for development environments
and static type checking.
"""

import logging
from commandLAB.computers.base_computer import BaseComputer, BaseJupyterNotebook, BaseShell
from commandLAB.computers.local_computer import LocalComputer, LocalShell, NbFormatJupyterNotebook
from commandLAB.computers.local_pynput_computer import LocalPynputComputer
from commandLAB.computers.local_pyautogui_computer import LocalPyAutoGUIComputer
from commandLAB.computers.e2b_desktop_computer import E2BDesktopComputer
from commandLAB.computers.daemon_client_computer import DaemonClientComputer
from commandLAB.computers.vnc_computer import VNCComputer
from commandLAB.computers.pigdev_computer import PigDevComputer
from commandLAB.computers.scrappybara_computer import (
    ScrapybaraComputer,
    UbuntuScrapybaraComputer,
    BrowserScrapybaraComputer,
    WindowsScrapybaraComputer,
)

__all__ = [
    "BaseComputer",
    "BaseJupyterNotebook",
    "BaseShell",
    "LocalComputer",
    "LocalShell",
    "NbFormatJupyterNotebook",
    "LocalPynputComputer",
    "LocalPyAutoGUIComputer",
    "E2BDesktopComputer",
    "DaemonClientComputer",
    "VNCComputer",
    "PigDevComputer",
    "ScrapybaraComputer",
    "UbuntuScrapybaraComputer",
    "BrowserScrapybaraComputer",
    "WindowsScrapybaraComputer",
] 