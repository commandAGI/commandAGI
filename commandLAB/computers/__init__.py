"""
Computer implementations for commandLAB.

This package contains various computer implementations that can be used with commandLAB.
"""

import logging

# Setup logging
logger = logging.getLogger(__name__)

from commandLAB.computers.base_computer import BaseComputer, BaseComputerFile

try:
    from commandLAB.computers.local_computer import LocalComputer
except ImportError:
    logger.info("LocalComputer not available. Install with: pip install commandLAB[local]")

try:
    from commandLAB.computers.local_pynput_computer import LocalPynputComputer
except ImportError:
    logger.info("LocalPynputComputer not available. Install with: pip install commandLAB[local]")

try:
    from commandLAB.computers.local_pyautogui_computer import LocalPyAutoGUIComputer
except ImportError:
    logger.info("LocalPyAutoGUIComputer not available. Install with: pip install commandLAB[local]")

try:
    from commandLAB.computers.e2b_desktop_computer import E2BDesktopComputer
except ImportError:
    logger.info("E2BDesktopComputer not available. Install with: pip install commandLAB[e2b_desktop]")

try:
    from commandLAB.computers.daemon_client_computer import DaemonClientComputer
except ImportError:
    logger.info("DaemonClientComputer not available. Install with: pip install commandLAB[daemon-client-all]")

try:
    from commandLAB.computers.vnc_computer import VNCComputer
except ImportError:
    logger.info("VNCComputer not available. Install with: pip install commandLAB[vnc]")

try:
    from commandLAB.computers.pigdev_computer import PigDevComputer
except ImportError:
    logger.info("PigDevComputer not available. Install with: pip install commandLAB[pigdev]")

try:
    from commandLAB.computers.scrappybara_computer import (
        ScrapybaraComputer,
        UbuntuScrapybaraComputer,
        BrowserScrapybaraComputer,
        WindowsScrapybaraComputer,
    )
except ImportError:
    logger.info("ScrapybaraComputer not available. Install with: pip install commandLAB[scrapybara]")

__all__ = [
    "BaseComputer",
    "BaseComputerFile",
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