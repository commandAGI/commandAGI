import base64
import subprocess
from typing import Union, Optional

try:
    from e2b_desktop import Sandbox
except ImportError:
    raise ImportError(
        "e2b_desktop is not installed. Please install commandLAB with the e2b_desktop extra:\n\npip install commandLAB[e2b_desktop]"
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
)


# E2B Desktop-specific mappings
def mouse_button_to_e2b(button: Union[MouseButton, str]) -> str:
    """Convert MouseButton to E2B Desktop button name.
    
    E2B Desktop uses the following button names:
    'left' = left button
    'middle' = middle button
    'right' = right button
    """
    if isinstance(button, str):
        button = MouseButton(button)
    
    # E2B Desktop mouse button mapping
    e2b_button_mapping = {
        MouseButton.LEFT: "left",
        MouseButton.MIDDLE: "middle",
        MouseButton.RIGHT: "right"
    }
    
    return e2b_button_mapping.get(button, "left")  # Default to left button if not found

def keyboard_key_to_e2b(key: Union[KeyboardKey, str]) -> str:
    """Convert KeyboardKey to E2B Desktop key name.
    
    E2B Desktop uses specific key names that may differ from our standard KeyboardKey values.
    """
    if isinstance(key, str):
        key = KeyboardKey(key)
    
    # E2B Desktop key mappings
    e2b_key_mapping = {
        # Special keys
        KeyboardKey.ENTER: "enter",
        KeyboardKey.TAB: "tab",
        KeyboardKey.SPACE: "space",
        KeyboardKey.BACKSPACE: "backspace",
        KeyboardKey.DELETE: "delete",
        KeyboardKey.ESCAPE: "esc",
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
        KeyboardKey.LCTRL: "ctrlleft",
        KeyboardKey.RCTRL: "ctrlright",
        KeyboardKey.ALT: "alt",
        KeyboardKey.LALT: "altleft",
        KeyboardKey.RALT: "altright",
        KeyboardKey.META: "win",  # Windows key
        KeyboardKey.LMETA: "winleft",
        KeyboardKey.RMETA: "winright",
        
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
    return e2b_key_mapping.get(key, key.value)


class E2BDesktopComputer(BaseComputer):
    """Environment that uses E2B Desktop Sandbox for secure computer interactions"""

    def __init__(self, video_stream=False):
        super().__init__()
        self.video_stream = video_stream
        self.desktop = None

    def _start(self):
        """Start the E2B desktop environment."""
        if not self.desktop:
            self.desktop = Sandbox(video_stream=self.video_stream)
        return True

    def _stop(self):
        """Stop the E2B desktop environment."""
        if self.desktop:
            self.desktop = None  # E2B sandbox automatically closes when object is destroyed
        return True

    def reset_state(self):
        """Reset the desktop environment and return initial observation"""
        # Show desktop to reset the environment state
        self.desktop.hotkey("win", "d")

    def _get_screenshot(self) -> ScreenshotObservation:
        """Return a screenshot of the current state as base64 encoded string."""
        screenshot = self.desktop.take_screenshot()
        b64_screenshot = base64.b64encode(screenshot).decode("utf-8")
        return ScreenshotObservation(screenshot=b64_screenshot)

    def _get_mouse_state(self) -> MouseStateObservation:
        """Return dummy mouse state as Sandbox does not provide real-time states."""
        raise NotImplementedError(
            "E2BDesktopEnv does not support mouse state observation"
        )

    def _get_keyboard_state(self) -> KeyboardStateObservation:
        """Return dummy keyboard state as Sandbox does not track key states."""
        raise NotImplementedError(
            "E2BDesktopEnv does not support keyboard state observation"
        )

    def _execute_command(self, action: CommandAction) -> bool:
        """Execute a system command in the host environment using E2B's commands.run."""
        try:
            result = self.desktop.commands.run(action.command)
            return True
        except Exception as e:
            print(f"Error executing command: {e}")
            return False

    def _execute_keyboard_key_down(self, action: KeyboardKeyDownAction) -> bool:
        """Execute key down for a keyboard key using action signature."""
        # E2B Desktop doesn't have direct key_down method, use PyAutoGUI
        e2b_key = keyboard_key_to_e2b(action.key)
        return self.desktop.pyautogui(f"pyautogui.keyDown('{e2b_key}')")

    def _execute_keyboard_key_release(self, action: KeyboardKeyReleaseAction) -> bool:
        """Execute key release for a keyboard key using action signature."""
        # E2B Desktop doesn't have direct key_up method, use PyAutoGUI
        e2b_key = keyboard_key_to_e2b(action.key)
        return self.desktop.pyautogui(f"pyautogui.keyUp('{e2b_key}')")

    def _execute_type(self, action: TypeAction) -> bool:
        """Type text using E2B Desktop's write method."""
        return self.desktop.write(action.text)

    def _execute_mouse_move(self, action: MouseMoveAction) -> bool:
        """Move mouse to specified coordinates using E2B Desktop's mouse_move method."""
        return self.desktop.mouse_move(action.x, action.y)

    def _execute_mouse_scroll(self, action: MouseScrollAction) -> bool:
        """Scroll mouse using E2B Desktop's scroll method."""
        return self.desktop.scroll(int(action.amount))

    def _execute_mouse_button_down(self, action: MouseButtonDownAction) -> bool:
        """Press mouse button down using PyAutoGUI through E2B Desktop."""
        e2b_button = mouse_button_to_e2b(action.button)
        return self.desktop.pyautogui(f"pyautogui.mouseDown(button='{e2b_button}')")

    def _execute_mouse_button_up(self, action: MouseButtonUpAction) -> bool:
        """Release mouse button using PyAutoGUI through E2B Desktop."""
        e2b_button = mouse_button_to_e2b(action.button)
        return self.desktop.pyautogui(f"pyautogui.mouseUp(button='{e2b_button}')")

    def _execute_click(self, action: ClickAction) -> bool:
        """Execute a click action using E2B Desktop's click methods."""
        # Move to position first
        self.desktop.mouse_move(action.x, action.y)
        
        # Then click using the appropriate method
        e2b_button = mouse_button_to_e2b(action.button)
        if e2b_button == "left":
            return self.desktop.left_click()
        elif e2b_button == "right":
            return self.desktop.right_click()
        elif e2b_button == "middle":
            return self.desktop.middle_click()
        else:
            return False

    def _execute_double_click(self, action: DoubleClickAction) -> bool:
        """Execute a double click action using E2B Desktop's double_click method."""
        # Move to position first
        self.desktop.mouse_move(action.x, action.y)
        
        # Then double click (E2B only supports left double click)
        return self.desktop.double_click()

    def _execute_keyboard_key_press(self, action: KeyboardKeyPressAction) -> bool:
        """Execute pressing a keyboard key using PyAutoGUI through E2B Desktop."""
        e2b_key = keyboard_key_to_e2b(action.key)
        return self.desktop.pyautogui(f"pyautogui.press('{e2b_key}')")

    def _execute_keyboard_hotkey(self, action: KeyboardHotkeyAction) -> bool:
        """Execute a keyboard hotkey using E2B Desktop's hotkey method."""
        # Convert keys to E2B format
        e2b_keys = [keyboard_key_to_e2b(key) for key in action.keys]
        
        # E2B Desktop's hotkey method takes individual arguments, not a list
        return self.desktop.hotkey(*e2b_keys)

    def get_video_stream_url(self) -> str:
        """Get the URL for the video stream of the E2B Desktop instance."""
        if not self.video_stream:
            print("Warning: Video stream was not enabled during initialization")
            return ""
            
        try:
            return self.desktop.get_video_stream_url()
        except Exception as e:
            print(f"Error getting video stream URL: {e}")
            return ""
