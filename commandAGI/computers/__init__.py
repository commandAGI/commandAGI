"""
Computer implementations for commandAGI.

This package contains various computer implementations that can be used with commandAGI.
"""

import logging

# Setup logging
logger = logging.getLogger(__name__)

from commandAGI.computers.base_computer import BaseComputer, BaseComputerFile

try:
    from commandAGI.computers.local_computer import LocalComputer
except ImportError:
    logger.info(
        "LocalComputer not available. Install with: pip install commandAGI[local]"
    )

try:
    from commandAGI.computers.local_pynput_computer import LocalPynputComputer
except ImportError:
    logger.info(
        "LocalPynputComputer not available. Install with: pip install commandAGI[local]"
    )

try:
    from commandAGI.computers.local_pyautogui_computer import LocalPyAutoGUIComputer
except ImportError:
    logger.info(
        "LocalPyAutoGUIComputer not available. Install with: pip install commandAGI[local]"
    )

try:
    from commandAGI.computers.e2b_desktop_computer import E2BDesktopComputer
except ImportError:
    logger.info(
        "E2BDesktopComputer not available. Install with: pip install commandAGI[e2b_desktop]"
    )

try:
    from commandAGI.computers.daemon_client_computer import DaemonClientComputer
except ImportError:
    logger.info(
        "DaemonClientComputer not available. Install with: pip install commandAGI[daemon-client-all]"
    )

try:
    from commandAGI.computers.vnc_computer import VNCComputer
except ImportError:
    logger.info("VNCComputer not available. Install with: pip install commandAGI[vnc]")

try:
    from commandAGI.computers.pigdev_computer import PigDevComputer
except ImportError:
    logger.info(
        "PigDevComputer not available. Install with: pip install commandAGI[pigdev]"
    )

try:
    from commandAGI.computers.scrappybara_computer import (
        ScrapybaraComputer,
        UbuntuScrapybaraComputer,
        BrowserScrapybaraComputer,
        WindowsScrapybaraComputer,
    )
except ImportError:
    logger.info(
        "ScrapybaraComputer not available. Install with: pip install commandAGI[scrapybara]"
    )

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
