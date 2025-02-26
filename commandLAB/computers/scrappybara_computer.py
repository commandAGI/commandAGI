import base64
import io
from typing import Optional, Union, List

try:
    import scrapybara
    from PIL import Image
except ImportError:
    raise ImportError(
        "scrapybara and Pillow are not installed. Please install commandLAB with the scrapybara extra:\n\npip install commandLAB[scrapybara]"
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


# Scrapybara-specific mappings
def mouse_button_to_scrapybara(button: Union[MouseButton, str]) -> str:
    """Convert MouseButton to Scrapybara button action.
    
    Scrapybara uses specific action names for mouse buttons:
    - "left_click" for left button
    - "right_click" for right button
    - "middle_click" for middle button
    """
    if isinstance(button, str):
        button = MouseButton(button)
    
    # Scrapybara mouse button mapping
    scrapybara_button_mapping = {
        MouseButton.LEFT: "left_click",
        MouseButton.MIDDLE: "middle_click",
        MouseButton.RIGHT: "right_click"
    }
    
    return scrapybara_button_mapping.get(button, "left_click")  # Default to left click if not found

def keyboard_key_to_scrapybara(key: Union[KeyboardKey, str]) -> str:
    """Convert KeyboardKey to Scrapybara key name.
    
    Scrapybara uses specific key names that may differ from our standard KeyboardKey values.
    For hotkeys, Scrapybara uses the '+' separator (e.g., "ctrl+c").
    """
    if isinstance(key, str):
        key = KeyboardKey(key)
    
    # Scrapybara-specific key mappings
    scrapybara_key_mapping = {
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
        KeyboardKey.LCTRL: "ctrl",  # Scrapybara doesn't distinguish between left/right
        KeyboardKey.RCTRL: "ctrl",
        KeyboardKey.ALT: "alt",
        KeyboardKey.LALT: "alt",  # Scrapybara doesn't distinguish between left/right
        KeyboardKey.RALT: "alt",
        KeyboardKey.META: "meta",  # Command/Windows key
        KeyboardKey.LMETA: "meta",  # Scrapybara doesn't distinguish between left/right
        KeyboardKey.RMETA: "meta",
        
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
    return scrapybara_key_mapping.get(key, key.value)


class ScrapybaraComputer(BaseComputer):
    """Environment that uses Scrapybara for secure computer interactions"""

    def __init__(self, api_key: Optional[str] = None):
        super().__init__()
        self.api_key = api_key
        self.client = None

    def _start(self):
        """Start the Scrapybara environment."""
        if not self.client:
            # Initialize the Scrapybara client
            if self.api_key:
                self.client = scrapybara.Client(api_key=self.api_key)
            else:
                self.client = scrapybara.Client()
            
            # Start a default Ubuntu instance
            self.client = self.client.start_ubuntu()
        return True

    def _stop(self):
        """Stop the Scrapybara environment."""
        if self.client:
            self.client.stop()
            self.client = None
        return True

    def reset_state(self):
        """Reset the Scrapybara environment"""
        # For Scrapybara, it's more efficient to stop and restart
        self._stop()
        self._start()

    def _get_screenshot(self) -> ScreenshotObservation:
        """Return a screenshot of the current state as base64 encoded string."""
        # Capture the screenshot using Scrapybara
        response = self.client.screenshot()
        b64_screenshot = response.base_64_image
        return ScreenshotObservation(screenshot=b64_screenshot)

    def _get_mouse_state(self) -> MouseStateObservation:
        """Return mouse state from Scrapybara."""
        # Get cursor position using Scrapybara
        response = self.client.computer(action="cursor_position")
        position = response.output
        
        # Parse the position string into x, y coordinates
        # The output is typically in the format "x: X, y: Y"
        x_str = position.split("x:")[1].split(",")[0].strip()
        y_str = position.split("y:")[1].strip()
        x, y = int(x_str), int(y_str)
            
        # Scrapybara doesn't provide button state, so we return a default state
        return MouseStateObservation(
            buttons={
                MouseButton.LEFT: None,
                MouseButton.MIDDLE: None,
                MouseButton.RIGHT: None
            },
            position=(x, y)
        )

    def _get_keyboard_state(self) -> KeyboardStateObservation:
        """Return keyboard state from Scrapybara."""
        # Scrapybara doesn't provide keyboard state
        raise NotImplementedError("Scrapybara does not support getting keyboard state")

    def _execute_command(self, action: CommandAction) -> bool:
        """Execute a system command in the Scrapybara VM."""
        try:
            # Use bash command for Ubuntu instances
            response = self.client.bash(command=action.command)
            return True
        except Exception as e:
            print(f"Error executing command via Scrapybara: {e}")
            return False

    def _execute_keyboard_key_down(self, action: KeyboardKeyDownAction) -> bool:
        """Execute key down for a keyboard key using Scrapybara."""
        # Scrapybara doesn't have separate key down/up methods
        # We'll use the key method with a press and hold approach
        try:
            key = keyboard_key_to_scrapybara(action.key)
            # Note: This is a limitation as Scrapybara doesn't support key down without release
            self.client.computer(action="key", text=key)
            return True
        except Exception as e:
            print(f"Error executing key down via Scrapybara: {e}")
            return False

    def _execute_keyboard_key_release(self, action: KeyboardKeyReleaseAction) -> bool:
        """Execute key release for a keyboard key using Scrapybara."""
        # Scrapybara doesn't have separate key down/up methods
        raise NotImplementedError("Scrapybara does not support key release actions")

    def _execute_type(self, action: TypeAction) -> bool:
        """Type text using Scrapybara."""
        try:
            self.client.computer(action="type", text=action.text)
            return True
        except Exception as e:
            print(f"Error typing text via Scrapybara: {e}")
            return False

    def _execute_mouse_move(self, action: MouseMoveAction) -> bool:
        """Move mouse to specified coordinates using Scrapybara."""
        try:
            self.client.computer(action="mouse_move", coordinate=[action.x, action.y])
            return True
        except Exception as e:
            print(f"Error moving mouse via Scrapybara: {e}")
            return False

    def _execute_mouse_scroll(self, action: MouseScrollAction) -> bool:
        """Scroll mouse using Scrapybara."""
        try:
            # Scrapybara scroll takes [x, y] coordinates for horizontal and vertical scrolling
            # Convert our amount to a vertical scroll (positive = down, negative = up)
            x_scroll = 0
            y_scroll = int(action.amount)
            
            self.client.computer(action="scroll", coordinate=[x_scroll, y_scroll])
            return True
        except Exception as e:
            print(f"Error scrolling mouse via Scrapybara: {e}")
            return False

    def _execute_mouse_button_down(self, action: MouseButtonDownAction) -> bool:
        """Press mouse button down using Scrapybara."""
        # Scrapybara doesn't have separate mouse down/up methods
        raise NotImplementedError("Scrapybara does not support mouse button down actions")

    def _execute_mouse_button_up(self, action: MouseButtonUpAction) -> bool:
        """Release mouse button using Scrapybara."""
        # Scrapybara doesn't have separate mouse down/up methods
        raise NotImplementedError("Scrapybara does not support mouse button up actions")

    def _execute_click(self, action: ClickAction) -> bool:
        """Execute a click action at the given coordinates using Scrapybara's click action."""
        try:
            # Scrapybara has a direct click action
            # First move to the position
            self.client.computer(action="mouse_move", coordinate=[action.x, action.y])
            
            # Then perform the appropriate click based on the button
            click_action = mouse_button_to_scrapybara(action.button)
            self.client.computer(action=click_action)
            return True
        except Exception as e:
            print(f"Error executing click via Scrapybara: {e}")
            return False

    def _execute_keyboard_key_press(self, action: KeyboardKeyPressAction) -> bool:
        """Execute pressing a keyboard key using Scrapybara's key action."""
        try:
            # Scrapybara uses the computer action with key
            scrapybara_key = keyboard_key_to_scrapybara(action.key)
            self.client.computer(action="key", text=scrapybara_key)
            return True
        except Exception as e:
            print(f"Error executing key press via Scrapybara: {e}")
            return False
            
    def _execute_keyboard_hotkey(self, action: KeyboardHotkeyAction) -> bool:
        """Execute a keyboard hotkey using Scrapybara's key action with combined keys."""
        try:
            # Combine keys with + for Scrapybara hotkey format
            hotkey = "+".join([keyboard_key_to_scrapybara(key) for key in action.keys])
            self.client.computer(action="key", text=hotkey)
            return True
        except Exception as e:
            print(f"Error executing hotkey via Scrapybara: {e}")
            return False

    def _execute_double_click(self, action: DoubleClickAction) -> bool:
        """Execute a double click action at the given coordinates using Scrapybara's double click action."""
        try:
            # Move to position first
            self.client.computer(action="mouse_move", coordinate=[action.x, action.y])
            # Then double click
            self.client.computer(action="double_click")
            return True
        except Exception as e:
            print(f"Error executing double click via Scrapybara: {e}")
            return False

    def _execute_drag(self, action: DragAction) -> bool:
        """Execute a drag action using Scrapybara's left_click_drag method."""
        try:
            # Move to the start position first
            self.client.computer(action="mouse_move", coordinate=[action.start_x, action.start_y])
            # Then perform the drag to the end position
            self.client.computer(action="left_click_drag", coordinate=[action.end_x, action.end_y])
            return True
        except Exception as e:
            print(f"Error executing drag via Scrapybara: {e}")
            return False

    def pause(self) -> bool:
        """Pause the Scrapybara instance."""
        try:
            self.client.pause()
            return True
        except Exception as e:
            print(f"Error pausing Scrapybara instance: {e}")
            return False

    def resume(self, timeout_hours: float = None) -> bool:
        """Resume the Scrapybara instance.
        
        Args:
            timeout_hours: Optional timeout in hours before the instance is automatically paused.
        """
        try:
            if timeout_hours:
                self.client.resume(timeout_hours=timeout_hours)
            else:
                self.client.resume()
            return True
        except Exception as e:
            print(f"Error resuming Scrapybara instance: {e}")
            return False

    def get_stream_url(self) -> str:
        """Get the URL for the interactive stream of the Scrapybara instance."""
        try:
            response = self.client.get_stream_url()
            return response.stream_url
        except Exception as e:
            print(f"Error getting stream URL: {e}")
            return ""


class UbuntuScrapybaraComputer(ScrapybaraComputer):
    """Scrapybara computer specifically for Ubuntu instances"""

    def __init__(self, api_key: Optional[str] = None):
        super().__init__(api_key=api_key)

    def _start(self):
        """Start an Ubuntu Scrapybara instance."""
        if not self.client:
            # Initialize the Scrapybara client
            if self.api_key:
                client = scrapybara.Client(api_key=self.api_key)
            else:
                client = scrapybara.Client()
            
            # Start an Ubuntu instance
            self.client = client.start_ubuntu()
        return True

    def _execute_command(self, action: CommandAction) -> bool:
        """Execute a bash command in the Ubuntu instance."""
        try:
            response = self.client.bash(command=action.command)
            return True
        except Exception as e:
            print(f"Error executing bash command via Scrapybara: {e}")
            return False

    def edit_file(self, path: str, command: str, **kwargs) -> bool:
        """Edit a file in the Ubuntu instance.
        
        Args:
            path: Path to the file to edit
            command: Edit command ('create', 'replace', or 'insert')
            **kwargs: Additional arguments for the specific command
        """
        try:
            self.client.edit(command=command, path=path, **kwargs)
            return True
        except Exception as e:
            print(f"Error editing file via Scrapybara: {e}")
            return False


class BrowserScrapybaraComputer(ScrapybaraComputer):
    """Scrapybara computer specifically for Browser instances"""

    def __init__(self, api_key: Optional[str] = None):
        super().__init__(api_key=api_key)

    def _start(self):
        """Start a Browser Scrapybara instance."""
        if not self.client:
            # Initialize the Scrapybara client
            if self.api_key:
                client = scrapybara.Client(api_key=self.api_key)
            else:
                client = scrapybara.Client()
            
            # Start a Browser instance
            self.client = client.start_browser()
        return True

    def get_cdp_url(self) -> str:
        """Get the Playwright CDP URL for the browser instance."""
        try:
            response = self.client.get_cdp_url()
            return response.cdp_url
        except Exception as e:
            print(f"Error getting CDP URL: {e}")
            return ""

    def save_auth(self, name: str = "default") -> str:
        """Save the current browser authentication state.
        
        Args:
            name: Name to identify the saved auth state
            
        Returns:
            The auth state ID that can be used to restore this state
        """
        try:
            response = self.client.save_auth(name=name)
            return response.auth_state_id
        except Exception as e:
            print(f"Error saving auth state: {e}")
            return ""

    def authenticate(self, auth_state_id: str) -> bool:
        """Authenticate the browser using a saved auth state.
        
        Args:
            auth_state_id: The ID of the saved auth state to restore
        """
        try:
            self.client.authenticate(auth_state_id=auth_state_id)
            return True
        except Exception as e:
            print(f"Error authenticating with saved state: {e}")
            return False

    def _execute_command(self, action: CommandAction) -> bool:
        """Execute a command in the browser instance.
        
        Note: Browser instances don't support bash commands directly.
        This is a limitation of the browser-only environment.
        """
        print("Warning: Browser instances don't support direct command execution")
        return False


class WindowsScrapybaraComputer(ScrapybaraComputer):
    """Scrapybara computer specifically for Windows instances"""

    def __init__(self, api_key: Optional[str] = None):
        super().__init__(api_key=api_key)

    def _start(self):
        """Start a Windows Scrapybara instance."""
        if not self.client:
            # Initialize the Scrapybara client
            if self.api_key:
                client = scrapybara.Client(api_key=self.api_key)
            else:
                client = scrapybara.Client()
            
            # Start a Windows instance
            self.client = client.start_windows()
        return True

    def _execute_command(self, action: CommandAction) -> bool:
        """Execute a command in the Windows instance.
        
        Note: Windows instances don't support bash commands directly.
        This implementation uses computer actions to open cmd and type commands.
        """
        try:
            # Open Windows Run dialog
            self.client.computer(action="key", text="meta+r")
            self.client.computer(action="wait")  # Wait for Run dialog to open
            
            # Type cmd and press Enter
            self.client.computer(action="type", text="cmd")
            self.client.computer(action="key", text="enter")
            self.client.computer(action="wait")  # Wait for cmd to open
            
            # Type the command and press Enter
            self.client.computer(action="type", text=action.command)
            self.client.computer(action="key", text="enter")
            
            # Wait for command to complete if timeout is specified
            if action.timeout:
                self.client.computer(action="wait")
                
            return True
        except Exception as e:
            print(f"Error executing command via Scrapybara Windows: {e}")
            return False
