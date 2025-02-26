import base64
import io
from typing import Optional

try:
    import pig
    from PIL import Image
except ImportError:
    raise ImportError(
        "pig-python and Pillow are not installed. Please install commandLAB with the pigdev extra:\n\npip install commandLAB[pigdev]"
    )

from commandLAB.computers.base_computer import BaseComputer
from commandLAB.types import (
    CommandAction,
    KeyboardKey,
    KeyboardKeyDownAction,
    KeyboardKeyReleaseAction,
    KeyboardStateObservation,
    MouseButton,
    MouseButtonDownAction,
    MouseButtonUpAction,
    MouseMoveAction,
    MouseScrollAction,
    MouseStateObservation,
    ScreenshotObservation,
    TypeAction,
    ClickAction,
    DoubleClickAction,
    DragAction,
    KeyboardKeyPressAction,
    KeyboardHotkeyAction,
)


class PigDevComputer(BaseComputer):
    """Environment that uses PigDev for secure computer interactions"""

    def __init__(self, api_key: Optional[str] = None):
        super().__init__()
        self.api_key = api_key
        self.client = None
        self._start()

    def _start(self):
        """Start the PigDev environment."""
        if not self.client:
            if self.api_key:
                pig.api_key = self.api_key
            self.client = pig.VM()
            self.client.start()
        return True

    def _stop(self):
        """Stop the PigDev environment."""
        if self.client:
            self.client.stop()
            self.client = None
        return True

    def reset_state(self):
        """Reset the PigDev environment"""
        # For PigDev, it's more efficient to stop and restart the VM
        # than to try to reset the desktop state
        self._stop()
        self._start()

    def _get_screenshot(self) -> ScreenshotObservation:
        """Return a screenshot of the current state as base64 encoded string."""
        if not self.client:
            self._start()
            
        # Capture the screenshot using PigDev
        screenshot = self.client.screenshot()
        
        # Convert the image data to a base64 string
        buffered = io.BytesIO()
        screenshot.save(buffered, format="PNG")
        b64_screenshot = base64.b64encode(buffered.getvalue()).decode("utf-8")
        return ScreenshotObservation(screenshot=b64_screenshot)

    def _get_mouse_state(self) -> MouseStateObservation:
        """Return mouse state from PigDev."""
        raise NotImplementedError("PigDev does not support getting mouse state")

    def _get_keyboard_state(self) -> KeyboardStateObservation:
        """Return keyboard state from PigDev."""
        raise NotImplementedError("PigDev does not support getting keyboard state")

    def _execute_command(self, action: CommandAction) -> bool:
        """Execute a system command in the PigDev VM."""
        try:
            result = self.client.run(action.command, timeout=action.timeout)
            return result.returncode == 0
        except Exception as e:
            print(f"Error executing command via PigDev: {e}")
            return False

    def _execute_keyboard_key_down(self, action: KeyboardKeyDownAction) -> bool:
        """Execute key down for a keyboard key using PigDev."""
        try:
            # Convert to PigDev key format if needed
            key = action.key.value
            self.client.key_down(key)
            return True
        except Exception as e:
            print(f"Error executing key down via PigDev: {e}")
            return False

    def _execute_keyboard_key_release(self, action: KeyboardKeyReleaseAction) -> bool:
        """Execute key release for a keyboard key using PigDev."""
        try:
            # Convert to PigDev key format if needed
            key = action.key.value
            self.client.key_up(key)
            return True
        except Exception as e:
            print(f"Error executing key release via PigDev: {e}")
            return False

    def _execute_type(self, action: TypeAction) -> bool:
        """Type text using PigDev."""
        try:
            self.client.type(action.text)
            return True
        except Exception as e:
            print(f"Error typing text via PigDev: {e}")
            return False

    def _execute_mouse_move(self, action: MouseMoveAction) -> bool:
        """Move mouse to specified coordinates using PigDev."""
        try:
            self.client.mouse_move(action.x, action.y)
            return True
        except Exception as e:
            print(f"Error moving mouse via PigDev: {e}")
            return False

    def _execute_mouse_scroll(self, action: MouseScrollAction) -> bool:
        """Scroll mouse using PigDev."""
        try:
            self.client.mouse_scroll(int(action.amount))
            return True
        except Exception as e:
            print(f"Error scrolling mouse via PigDev: {e}")
            return False

    def _execute_mouse_button_down(self, action: MouseButtonDownAction) -> bool:
        """Press mouse button down using PigDev."""
        try:
            button = action.button.value
            self.client.mouse_down(button)
            return True
        except Exception as e:
            print(f"Error pressing mouse button via PigDev: {e}")
            return False

    def _execute_mouse_button_up(self, action: MouseButtonUpAction) -> bool:
        """Release mouse button using PigDev."""
        try:
            button = action.button.value
            self.client.mouse_up(button)
            return True
        except Exception as e:
            print(f"Error releasing mouse button via PigDev: {e}")
            return False

    def _execute_click(self, action: ClickAction) -> bool:
        """Execute a click action at the given coordinates using PigDev's click method."""
        try:
            # Move to position first
            self.client.mouse_move(action.x, action.y)
            # Then click using the appropriate button
            button = action.button.value
            self.client.click(button)
            return True
        except Exception as e:
            print(f"Error executing click via PigDev: {e}")
            return False

    def _execute_double_click(self, action: DoubleClickAction) -> bool:
        """Execute a double click action at the given coordinates using PigDev's double_click method."""
        try:
            # Move to position first
            self.client.mouse_move(action.x, action.y)
            # Then double click using the appropriate button
            button = action.button.value
            self.client.double_click(button)
            return True
        except Exception as e:
            print(f"Error executing double click via PigDev: {e}")
            return False

    def _execute_drag(self, action: DragAction) -> bool:
        """Execute a drag action using PigDev's drag method."""
        try:
            # PigDev has a direct drag method
            button = action.button.value
            self.client.drag(action.start_x, action.start_y, action.end_x, action.end_y, button)
            return True
        except Exception as e:
            print(f"Error executing drag via PigDev: {e}")
            return False

    def _execute_keyboard_key_press(self, action: KeyboardKeyPressAction) -> bool:
        """Execute pressing a keyboard key using PigDev's key_press method."""
        try:
            key = action.key.value
            self.client.key_press(key)
            return True
        except Exception as e:
            print(f"Error executing key press via PigDev: {e}")
            return False

    def _execute_keyboard_hotkey(self, action: KeyboardHotkeyAction) -> bool:
        """Execute a keyboard hotkey using PigDev's hotkey method."""
        try:
            # Convert keys to a list of key values
            keys = [key.value for key in action.keys]
            self.client.hotkey(keys)
            return True
        except Exception as e:
            print(f"Error executing hotkey via PigDev: {e}")
            return False
