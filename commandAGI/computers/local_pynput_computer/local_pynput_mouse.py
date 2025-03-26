from typing import Optional, Union

try:
    from pynput.mouse import Button as PynputButton
except ImportError:
    raise ImportError(
        "The local dependencies are not installed. Please install commandAGI with the local extra:\n\npip install commandAGI[local]"
    )

from commandAGI.types import (
    MouseButton,
)


# Pynput-specific mappings
def mouse_button_to_pynput(button: Union[MouseButton, str]) -> PynputButton:
    """Convert MouseButton to Pynput mouse button.

    Pynput uses Button enum for mouse buttons:
    Button.left = left button
    Button.middle = middle button
    Button.right = right button
    """
    if isinstance(button, str):
        button = MouseButton(button)

    # Pynput mouse button mapping
    pynput_button_mapping = {
        MouseButton.LEFT: PynputButton.left,
        MouseButton.MIDDLE: PynputButton.middle,
        MouseButton.RIGHT: PynputButton.right,
    }

    return pynput_button_mapping.get(
        button, PynputButton.left
    )  # Default to left button if not found


def mouse_button_from_pynput(button: PynputButton) -> Optional[MouseButton]:
    """Convert Pynput mouse button to MouseButton.

    Maps from pynput.mouse.Button to our MouseButton enum.
    """
    # Pynput to MouseButton mapping
    pynput_to_mouse_button = {
        PynputButton.left: MouseButton.LEFT,
        PynputButton.middle: MouseButton.MIDDLE,
        PynputButton.right: MouseButton.RIGHT,
    }

    return pynput_to_mouse_button.get(button)  # Returns None if not found
