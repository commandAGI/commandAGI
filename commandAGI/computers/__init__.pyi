"""
Type stubs for commandAGI.computers package.

This file provides type hints for the computers package without requiring
the actual dependencies to be installed, which is helpful for development environments
and static type checking.
"""

import logging

from commandAGI.computers.base_computer import (
    BaseComputer,
    BaseComputerFile,
    BaseJupyterNotebook,
    BaseShell,
)
from commandAGI.computers.remote_computer import RemoteComputer
from commandAGI.computers.e2b_desktop_computer import E2BDesktopComputer
from commandAGI.computers.local_computer import (
    LocalComputer,
    LocalComputerFile,
    LocalShell,
    NbFormatJupyterNotebook,
)
from commandAGI.computers.local_pyautogui_computer import LocalPyAutoGUIComputer
from commandAGI.computers.local_pynput_computer import LocalPynputComputer
from commandAGI.computers.pigdev_computer import PigDevComputer
from commandAGI.computers.scrappybara_computer import (
    BrowserScrapybaraComputer,
    ScrapybaraComputer,
    UbuntuScrapybaraComputer,
    WindowsScrapybaraComputer,
)
from commandAGI.computers.vnc_computer import VNCComputer

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
    "RemoteComputer",
    "VNCComputer",
    "PigDevComputer",
    "ScrapybaraComputer",
    "UbuntuScrapybaraComputer",
    "BrowserScrapybaraComputer",
    "WindowsScrapybaraComputer",
]
# TODO: update this file to include all the imports from __init__.py
