import base64
import io
from typing import Optional, Union

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
    KeyboardKeyPressAction,
    DoubleClickAction,
    DragAction,
    KeyboardHotkeyAction,
)


class ScrapybaraComputer(BaseComputer):
    """Base environment that uses Scrapybara for secure computer interactions"""

    def __init__(self, api_key: Optional[str] = None):
        super().__init__()
        self.api_key = api_key
        self.client = None
        self._connect()

    def _connect(self):
        """Connect to the Scrapybara service - to be implemented by subclasses"""
        if self.api_key:
            scrapybara.api_key = self.api_key

    def reset(self):
        """Reset the Scrapybara environment and return initial observation"""
        self.close()
        self._connect()
        return self.get_observation()

    def close(self):
        """Clean up resources - to be implemented by subclasses"""
        if self.client:
            self.client.stop()
            self.client = None

    def get_screenshot(self) -> ScreenshotObservation:
        """Return a screenshot of the current state as base64 encoded string."""
        if not self.client:
            self._connect()
            
        # Capture the screenshot using Scrapybara
        screenshot_data = self.client.screenshot().base_64_image
        return ScreenshotObservation(screenshot=screenshot_data)

    def get_mouse_state(self) -> MouseStateObservation:
        """Return mouse state from Scrapybara."""
        raise NotImplementedError("Scrapybara does not support getting mouse state")

    def get_keyboard_state(self) -> KeyboardStateObservation:
        """Return keyboard state from Scrapybara."""
        raise NotImplementedError("Scrapybara does not support getting keyboard state")

    def execute_command(self, action: CommandAction) -> bool:
        """Execute a system command in the Scrapybara environment."""
        # This is a base method that should be overridden by subclasses
        raise NotImplementedError("Command execution must be implemented by subclasses")

    def execute_keyboard_key_down(self, action: KeyboardKeyDownAction) -> bool:
        """Execute key down for a keyboard key using Scrapybara."""
        try:
            # Scrapybara uses the computer action with key_down
            self.client.computer(action="key", text=action.key.value)
            return True
        except Exception as e:
            print(f"Error executing key down via Scrapybara: {e}")
            return False

    def execute_keyboard_key_release(self, action: KeyboardKeyReleaseAction) -> bool:
        """Execute key release for a keyboard key using Scrapybara."""
        # Scrapybara doesn't have a direct key release method in its API
        raise NotImplementedError("Scrapybara does not support key release actions")

    def execute_type(self, action: TypeAction) -> bool:
        """Type text using Scrapybara."""
        try:
            self.client.computer(action="type", text=action.text)
            return True
        except Exception as e:
            print(f"Error typing text via Scrapybara: {e}")
            return False

    def execute_mouse_move(self, action: MouseMoveAction) -> bool:
        """Move mouse to specified coordinates using Scrapybara."""
        try:
            self.client.computer(action="mouse_move", coordinate=[action.x, action.y])
            return True
        except Exception as e:
            print(f"Error moving mouse via Scrapybara: {e}")
            return False

    def execute_mouse_scroll(self, action: MouseScrollAction) -> bool:
        """Scroll mouse using Scrapybara."""
        try:
            # Scrapybara expects scroll as [x, y] coordinates
            # Convert our amount to appropriate coordinates
            x_scroll = 0
            y_scroll = int(action.amount)
            self.client.computer(action="scroll", coordinate=[x_scroll, y_scroll])
            return True
        except Exception as e:
            print(f"Error scrolling mouse via Scrapybara: {e}")
            return False

    def execute_mouse_button_down(self, action: MouseButtonDownAction) -> bool:
        """Press mouse button down using Scrapybara."""
        # Scrapybara doesn't have separate mouse down/up methods
        raise NotImplementedError("Scrapybara does not support mouse button down actions")

    def execute_mouse_button_up(self, action: MouseButtonUpAction) -> bool:
        """Release mouse button using Scrapybara."""
        # Scrapybara doesn't have separate mouse down/up methods
        raise NotImplementedError("Scrapybara does not support mouse button up actions")

    def execute_click(self, action: ClickAction) -> bool:
        """Execute a click action at the given coordinates using Scrapybara's click action."""
        try:
            # Scrapybara has a direct click action
            self.client.computer(action="click", coordinate=[action.x, action.y])
            return True
        except Exception as e:
            print(f"Error executing click via Scrapybara: {e}")
            return False
            
    def execute_keyboard_key_press(self, action: KeyboardKeyPressAction) -> bool:
        """Execute pressing a keyboard key using Scrapybara's key action."""
        try:
            # Scrapybara uses the computer action with key
            self.client.computer(action="key", text=action.key.value)
            return True
        except Exception as e:
            print(f"Error executing key press via Scrapybara: {e}")
            return False
            
    def execute_keyboard_hotkey(self, action: KeyboardHotkeyAction) -> bool:
        """Execute a keyboard hotkey using Scrapybara's key action with combined keys."""
        try:
            # Combine keys with + for Scrapybara hotkey format
            hotkey = "+".join([key.value for key in action.keys])
            self.client.computer(action="key", text=hotkey)
            return True
        except Exception as e:
            print(f"Error executing hotkey via Scrapybara: {e}")
            return False

    def execute_double_click(self, action: DoubleClickAction) -> bool:
        """Execute a double click action at the given coordinates using Scrapybara's double click action."""
        try:
            # Scrapybara has a direct double click action
            self.client.computer(action="double_click", coordinate=[action.x, action.y])
            return True
        except Exception as e:
            print(f"Error executing double click via Scrapybara: {e}")
            return False

    def execute_drag(self, action: DragAction) -> bool:
        """Execute a drag action using Scrapybara's drag action."""
        try:
            # Scrapybara has a direct drag action
            self.client.computer(
                action="drag", 
                coordinate=[[action.start_x, action.start_y], [action.end_x, action.end_y]]
            )
            return True
        except Exception as e:
            print(f"Error executing drag via Scrapybara: {e}")
            return False

    def pause(self) -> bool:
        """Pause the instance."""
        try:
            self.client.pause()
            return True
        except Exception as e:
            print(f"Error pausing Scrapybara instance: {e}")
            return False

    def resume(self, timeout_hours: float = None) -> bool:
        """Resume the instance."""
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
        """Get the interactive stream URL."""
        try:
            return self.client.get_stream_url().stream_url
        except Exception as e:
            print(f"Error getting stream URL: {e}")
            return None


class UbuntuScrapybaraComputer(ScrapybaraComputer):
    """Scrapybara environment for Ubuntu interactions"""

    def __init__(self, api_key: Optional[str] = None):
        super().__init__(api_key=api_key)

    def _connect(self):
        """Connect to the Scrapybara Ubuntu service"""
        super()._connect()
        self.client = scrapybara.client.start_ubuntu()
        
    def execute_command(self, action: CommandAction) -> bool:
        """Execute a system command in the Ubuntu environment using bash."""
        try:
            # Ubuntu-specific command execution via bash
            output = self.client.bash(command=action.command)
            return True
        except Exception as e:
            print(f"Error executing command in Ubuntu via Scrapybara: {e}")
            return False
            
    def edit_file(self, path: str, command: str, **kwargs) -> bool:
        """Edit a file on the Ubuntu instance."""
        try:
            self.client.edit(command=command, path=path, **kwargs)
            return True
        except Exception as e:
            print(f"Error editing file in Ubuntu via Scrapybara: {e}")
            return False


class BrowserScrapybaraComputer(ScrapybaraComputer):
    """Scrapybara environment for Browser interactions"""

    def __init__(self, api_key: Optional[str] = None):
        super().__init__(api_key=api_key)

    def _connect(self):
        """Connect to the Scrapybara Browser service"""
        super()._connect()
        self.client = scrapybara.client.start_browser()
        
    def get_cdp_url(self) -> str:
        """Get the Playwright CDP URL."""
        try:
            return self.client.get_cdp_url().cdp_url
        except Exception as e:
            print(f"Error getting CDP URL: {e}")
            return None
            
    def save_auth(self, name: str = "default") -> str:
        """Save the browser auth state."""
        try:
            return self.client.browser.save_auth(name=name).auth_state_id
        except Exception as e:
            print(f"Error saving auth state: {e}")
            return None
            
    def authenticate(self, auth_state_id: str) -> bool:
        """Authenticate the browser using a saved auth state."""
        try:
            self.client.browser.authenticate(auth_state_id=auth_state_id)
            return True
        except Exception as e:
            print(f"Error authenticating browser: {e}")
            return False
            
    def execute_command(self, action: CommandAction) -> bool:
        """Execute JavaScript in the browser context."""
        try:
            # For browser, we interpret commands as JavaScript
            # Note: This is an approximation as the docs don't show a direct method for this
            self.client.browser.evaluate(action.command)
            return True
        except Exception as e:
            print(f"Error executing JavaScript in browser via Scrapybara: {e}")
            return False


class WindowsScrapybaraComputer(ScrapybaraComputer):
    """Scrapybara environment for Windows interactions"""

    def __init__(self, api_key: Optional[str] = None):
        super().__init__(api_key=api_key)

    def _connect(self):
        """Connect to the Scrapybara Windows service"""
        super()._connect()
        self.client = scrapybara.client.start_windows()
        
    def execute_command(self, action: CommandAction) -> bool:
        """Execute a system command in the Windows environment."""
        try:
            # Windows doesn't have a direct command execution method in the docs
            # We'll use computer actions to open PowerShell and type commands
            # Open PowerShell (Windows+R, then type powershell)
            self.client.computer(action="key", text="win+r")
            self.client.computer(action="wait")  # Wait for Run dialog
            self.client.computer(action="type", text="powershell")
            self.client.computer(action="key", text="enter")
            self.client.computer(action="wait")  # Wait for PowerShell
            
            # Type and execute the command
            self.client.computer(action="type", text=action.command)
            self.client.computer(action="key", text="enter")
            
            return True
        except Exception as e:
            print(f"Error executing command in Windows via Scrapybara: {e}")
            return False
