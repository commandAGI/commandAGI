from typing import Union

try:
    pass

    # Try to import paramiko for SFTP file transfer
    try:
        pass

        SFTP_AVAILABLE = True
    except ImportError:
        SFTP_AVAILABLE = False
except ImportError:
    raise ImportError(
        "The VNC dependencies are not installed. Please install commandAGI with the vnc extra:\n\npip install commandAGI[vnc]"
    )

from commandAGI.types import (
    MouseButton,
)


# VNC-specific mappings
def mouse_button_to_vnc(button: Union[MouseButton, str]) -> int:
    """Convert MouseButton to VNC mouse button code.

    VNC uses integers for mouse buttons:
    1 = left button
    2 = middle button
    3 = right button
    4 = wheel up
    5 = wheel down
    """
    if isinstance(button, str):
        button = MouseButton(button)

    # VNC mouse button mapping
    vnc_button_mapping = {
        MouseButton.LEFT: 1,
        MouseButton.MIDDLE: 2,
        MouseButton.RIGHT: 3,
    }

    # Default to left button if not found
    return vnc_button_mapping.get(button, 1)
