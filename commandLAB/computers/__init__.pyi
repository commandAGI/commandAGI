"""
Type stubs for commandLAB.computers package.

This file provides type hints for the computers package without requiring
the actual dependencies to be installed, which is helpful for development environments
and static type checking.
"""

import logging
from commandLAB.computers.base_computer import BaseComputer
from commandLAB.computers.local_computer import LocalComputer
from commandLAB.computers.computers import (
    LocalPynputComputer,
    LocalPyAutoGUIComputer,
    E2BDesktopComputer,
    DaemonClientComputer,
    VNCComputer,
    PigDevComputer,
    ScrapybaraComputer,
    UbuntuScrapybaraComputer,
    BrowserScrapybaraComputer,
    WindowsScrapybaraComputer,
)

__all__ = [
    "BaseComputer",
    "LocalComputer",
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