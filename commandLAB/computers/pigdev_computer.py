import base64
import io
from typing import Optional, Union

try:
    from pig import Client
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


# PigDev-specific mappings
def mouse_button_to_pigdev(button: Union[MouseButton, str]) -> str:
    """Convert MouseButton to PigDev button name.
    
    PigDev uses string names for mouse buttons that match our MouseButton values.
    """
    if isinstance(button, str):
        button = MouseButton(button)
    
    # PigDev mouse button mapping
    pigdev_button_mapping = {
        MouseButton.LEFT: "left",
        MouseButton.MIDDLE: "middle",
        MouseButton.RIGHT: "right"
    }
    
    return pigdev_button_mapping.get(button, "left")  # Default to left button if not found

def keyboard_key_to_pigdev(key: Union[KeyboardKey, str]) -> str:
    """Convert KeyboardKey to PigDev key name.
    
    PigDev uses specific key names that may differ from our standard KeyboardKey values.
    """
    if isinstance(key, str):
        key = KeyboardKey(key)
    
    # PigDev-specific key mappings
    pigdev_key_mapping = {
        # Special keys
        KeyboardKey.ENTER: "enter",
        KeyboardKey.TAB: "tab",
        KeyboardKey.SPACE: "space",
        KeyboardKey.BACKSPACE: "backspace",
        KeyboardKey.DELETE: "delete",
        KeyboardKey.ESCAPE: "escape",
        KeyboardKey.HOME: "home",
        KeyboardKey.END: "end",
        KeyboardKey.PAGE_UP: "pageup",
        KeyboardKey.PAGE_DOWN: "pagedown",
        
        # Arrow keys
        KeyboardKey.UP: "up",
        KeyboardKey.DOWN: "down",
        KeyboardKey.LEFT: "left",
        KeyboardKey.RIGHT: "right",
        
        # Modifier keys
        KeyboardKey.SHIFT: "shift",
        KeyboardKey.CTRL: "ctrl",
        KeyboardKey.LCTRL: "ctrl",  # PigDev may not distinguish between left/right
        KeyboardKey.RCTRL: "ctrl",
        KeyboardKey.ALT: "alt",
        KeyboardKey.LALT: "alt",  # PigDev may not distinguish between left/right
        KeyboardKey.RALT: "alt",
        KeyboardKey.META: "super",  # Command/Windows key is called "super" in PigDev
        KeyboardKey.LMETA: "super",  # PigDev may not distinguish between left/right
        KeyboardKey.RMETA: "super",
        
        # Function keys
        KeyboardKey.F1: "f1",
        KeyboardKey.F2: "f2",
        KeyboardKey.F3: "f3",
        KeyboardKey.F4: "f4",
        KeyboardKey.F5: "f5",
        KeyboardKey.F6: "f6",
        KeyboardKey.F7: "f7",
        KeyboardKey.F8: "f8",
        KeyboardKey.F9: "f9",
        KeyboardKey.F10: "f10",
        KeyboardKey.F11: "f11",
        KeyboardKey.F12: "f12",
    }
    
    # For letter keys and number keys, use the value directly
    return pigdev_key_mapping.get(key, key.value)


class PigDevComputer(BaseComputer):
    """Environment that uses PigDev for secure computer interactions"""

    def __init__(self, api_key: Optional[str] = None, machine_id: Optional[str] = None):
        super().__init__()
        self.api_key = api_key
        self.machine_id = machine_id
        self.client = None
        self.machine = None
        self.connection = None

    def _start(self):
        """Start the PigDev environment and establish a connection.
        
        This method initializes the Pig client, selects the appropriate machine,
        and establishes a connection that will be maintained throughout the session.
        """
        # Initialize the Pig client
        if self.api_key:
            self.client = Client(api_key=self.api_key)
        else:
            self.client = Client()
            
        # Get the machine (either local or remote)
        if self.machine_id:
            self.machine = self.client.machines.get(self.machine_id)
        else:
            self.machine = self.client.machines.local()
        
        # Establish a connection that will be maintained throughout the session
        self.connection = self.machine.connect().__enter__()
        return True

    def _stop(self):
        """Stop the PigDev environment and close the connection.
        
        This method properly closes the connection and cleans up resources.
        """
        if self.connection:
            # Properly exit the connection context manager
            self.machine.connect().__exit__(None, None, None)
            self.connection = None
            
        self.client = None
        self.machine = None
        return True

    def reset_state(self):
        """Reset the PigDev environment"""
        # For PigDev, we'll restart the client connection
        self._stop()
        self._start()

    def _get_screenshot(self) -> ScreenshotObservation:
        """Return a screenshot of the current state as base64 encoded string."""
        # Capture the screenshot using the existing connection
        screenshot = self.connection.screenshot()
        
        # Convert the image data to a base64 string
        buffered = io.BytesIO()
        screenshot.save(buffered, format="PNG")
        b64_screenshot = base64.b64encode(buffered.getvalue()).decode("utf-8")
        return ScreenshotObservation(screenshot=b64_screenshot)

    def _get_mouse_state(self) -> MouseStateObservation:
        """Return mouse state from PigDev."""
        # Get cursor position using the existing connection
        x, y = self.connection.cursor_position()
            
        # PigDev doesn't provide button state, so we return a default state
        return MouseStateObservation(
            buttons={
                MouseButton.LEFT: False,
                MouseButton.MIDDLE: False,
                MouseButton.RIGHT: False
            },
            position=(x, y)
        )

    def _get_keyboard_state(self) -> KeyboardStateObservation:
        """Return keyboard state from PigDev."""
        # PigDev doesn't provide keyboard state
        raise NotImplementedError("PigDev does not support getting keyboard state")

    def _execute_command(self, action: CommandAction) -> bool:
        """Execute a system command in the PigDev VM."""
        # PigDev doesn't have a direct command execution method
        raise NotImplementedError("PigDev does not support direct command execution")

    def _execute_keyboard_key_down(self, action: KeyboardKeyDownAction) -> bool:
        """Execute key down for a keyboard key using PigDev."""
        try:
            # Convert to PigDev key format
            key = keyboard_key_to_pigdev(action.key)
            
            # Use the existing connection
            self.connection.key_down(key)
            return True
        except Exception as e:
            print(f"Error executing key down via PigDev: {e}")
            return False

    def _execute_keyboard_key_release(self, action: KeyboardKeyReleaseAction) -> bool:
        """Execute key release for a keyboard key using PigDev."""
        try:
            # Convert to PigDev key format
            key = keyboard_key_to_pigdev(action.key)
            
            # Use the existing connection
            self.connection.key_up(key)
            return True
        except Exception as e:
            print(f"Error executing key release via PigDev: {e}")
            return False

    def _execute_type(self, action: TypeAction) -> bool:
        """Type text using PigDev."""
        try:
            # Use the existing connection
            self.connection.type(action.text)
            return True
        except Exception as e:
            print(f"Error typing text via PigDev: {e}")
            return False

    def _execute_mouse_move(self, action: MouseMoveAction) -> bool:
        """Move mouse to specified coordinates using PigDev."""
        try:
            # Use the existing connection
            self.connection.mouse_move(x=action.x, y=action.y)
            return True
        except Exception as e:
            print(f"Error moving mouse via PigDev: {e}")
            return False

    def _execute_mouse_scroll(self, action: MouseScrollAction) -> bool:
        """Scroll mouse using PigDev."""
        # PigDev doesn't have a direct scroll method
        raise NotImplementedError("PigDev does not support mouse scrolling")

    def _execute_mouse_button_down(self, action: MouseButtonDownAction) -> bool:
        """Press mouse button down using PigDev."""
        try:
            button = mouse_button_to_pigdev(action.button)
            
            # Use the existing connection
            self.connection.mouse_down(button)
            return True
        except Exception as e:
            print(f"Error pressing mouse button via PigDev: {e}")
            return False

    def _execute_mouse_button_up(self, action: MouseButtonUpAction) -> bool:
        """Release mouse button using PigDev."""
        try:
            button = mouse_button_to_pigdev(action.button)
            
            # Use the existing connection
            self.connection.mouse_up(button)
            return True
        except Exception as e:
            print(f"Error releasing mouse button via PigDev: {e}")
            return False

    def _execute_click(self, action: ClickAction) -> bool:
        """Execute a click action at the given coordinates using PigDev's click method."""
        try:
            # Use the existing connection
            # Move to position first
            self.connection.mouse_move(x=action.x, y=action.y)
            # Then click using the appropriate button
            if action.button == MouseButton.LEFT:
                self.connection.left_click()
            else:
                self.connection.right_click()
            return True
        except Exception as e:
            print(f"Error executing click via PigDev: {e}")
            return False

    def _execute_double_click(self, action: DoubleClickAction) -> bool:
        """Execute a double click action at the given coordinates using PigDev's double_click method."""
        try:
            # Use the existing connection
            # Move to position first
            self.connection.mouse_move(x=action.x, y=action.y)
            # Then double click (PigDev only supports left double click)
            self.connection.double_click()
            return True
        except Exception as e:
            print(f"Error executing double click via PigDev: {e}")
            return False

    def _execute_drag(self, action: DragAction) -> bool:
        """Execute a drag action using PigDev's left_click_drag method."""
        try:
            # Use the existing connection
            # First move to the start position
            self.connection.mouse_move(x=action.start_x, y=action.start_y)
            # Then perform the drag to the end position
            self.connection.left_click_drag(x=action.end_x, y=action.end_y)
            return True
        except Exception as e:
            print(f"Error executing drag via PigDev: {e}")
            return False

    def _execute_keyboard_key_press(self, action: KeyboardKeyPressAction) -> bool:
        """Execute pressing a keyboard key using PigDev's key method."""
        try:
            key = keyboard_key_to_pigdev(action.key)
            
            # Use the existing connection
            self.connection.key(key)
            return True
        except Exception as e:
            print(f"Error executing key press via PigDev: {e}")
            return False

    def _execute_keyboard_hotkey(self, action: KeyboardHotkeyAction) -> bool:
        """Execute a keyboard hotkey using PigDev's key method with combined keys."""
        try:
            # Convert keys to PigDev format
            keys = [keyboard_key_to_pigdev(key) for key in action.keys]
            
            # Use the existing connection
            # PigDev supports hotkeys as a single string with '+' separator
            self.connection.key("+".join(keys))
            return True
        except Exception as e:
            print(f"Error executing hotkey via PigDev: {e}")
            return False
