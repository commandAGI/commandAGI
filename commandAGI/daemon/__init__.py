"""
Daemon components for commandAGI.

This package contains the daemon server and client components for remote computer control.
"""

from commandAGI.daemon.cli import cli
from commandAGI.daemon.client import AuthenticatedClient
from commandAGI.daemon.server import ComputerDaemon

__all__ = [
    "ComputerDaemon",
    "AuthenticatedClient",
    "cli",
]
