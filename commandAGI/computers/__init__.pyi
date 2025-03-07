"""
Type stubs for commandAGI.computers package.

This file provides type hints for the computers package without requiring
the actual dependencies to be installed, which is helpful for development environments
and static type checking.
"""

import logging
from commandAGI.computers.base_computer import (
    BaseComputer,
    BaseJupyterNotebook,
    BaseShell,
    BaseComputerFile,
)
from commandAGI.computers.local_computer import (
    LocalComputer,
    LocalShell,
    NbFormatJupyterNotebook,
    LocalComputerFile,
)
from commandAGI.computers.local_pynput_computer import LocalPynputComputer
from commandAGI.computers.local_pyautogui_computer import LocalPyAutoGUIComputer
from commandAGI.computers.e2b_desktop_computer import E2BDesktopComputer
from commandAGI.computers.daemon_client_computer import DaemonClientComputer
from commandAGI.computers.vnc_computer import VNCComputer
from commandAGI.computers.pigdev_computer import PigDevComputer
from commandAGI.computers.scrappybara_computer import (
    ScrapybaraComputer,
    UbuntuScrapybaraComputer,
    BrowserScrapybaraComputer,
    WindowsScrapybaraComputer,
)

__all__ = [
    "BaseComputer",
    "BaseJupyterNotebook",
    "BaseShell",
    "BaseComputerFile",
    "LocalComputer",
    "LocalShell",
    "LocalComputerFile",
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
