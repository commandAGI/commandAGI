"""
Type stubs for commandLAB computer implementations.

This file provides type hints for all computer implementations without requiring
the actual dependencies to be installed, which is helpful for development environments
and static type checking.
"""

from typing import Dict, List, Optional, Tuple, Union, Any, Literal

from commandLAB.computers.base_computer import BaseComputer
from commandLAB.types import (
    CommandAction,
    KeyboardHotkeyAction,
    KeyboardKey,
    KeyboardKeyDownAction,
    KeyboardKeyPressAction,
    KeyboardKeyReleaseAction,
    KeyboardKeysDownAction,
    KeyboardKeysPressAction,
    KeyboardKeysReleaseAction,
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
    LayoutTreeObservation,
    ProcessesObservation,
    WindowsObservation,
    DisplaysObservation,
    RunProcessAction,
)

# Local PyAutoGUI Computer
class LocalPyAutoGUIComputer(BaseComputer):
    def __init__(self) -> None: ...
    def _start(self) -> bool: ...
    def _stop(self) -> bool: ...
    def reset_state(self) -> None: ...
    def _get_screenshot(self) -> ScreenshotObservation: ...
    def _get_mouse_state(self) -> MouseStateObservation: ...
    def _get_keyboard_state(self) -> KeyboardStateObservation: ...
    def _execute_command(self, action: CommandAction) -> bool: ...
    def _execute_keyboard_key_down(self, action: KeyboardKeyDownAction) -> bool: ...
    def _execute_keyboard_key_release(self, action: KeyboardKeyReleaseAction) -> bool: ...
    def _execute_type(self, action: TypeAction) -> bool: ...
    def _execute_mouse_move(self, action: MouseMoveAction) -> bool: ...
    def _execute_mouse_scroll(self, action: MouseScrollAction) -> bool: ...
    def _execute_mouse_button_down(self, action: MouseButtonDownAction) -> bool: ...
    def _execute_mouse_button_up(self, action: MouseButtonUpAction) -> bool: ...

# Local Pynput Computer
class LocalPynputComputer(BaseComputer):
    def __init__(self) -> None: ...
    def _start(self) -> bool: ...
    def _stop(self) -> bool: ...
    def reset_state(self) -> None: ...
    def _on_keyboard_press(self, key: Any) -> None: ...
    def _on_keyboard_release(self, key: Any) -> None: ...
    def _on_mouse_move(self, x: int, y: int) -> None: ...
    def _on_mouse_click(self, x: int, y: int, button: Any, pressed: bool) -> None: ...
    def _on_mouse_scroll(self, x: int, y: int, dx: int, dy: int) -> None: ...
    def _get_screenshot(self) -> ScreenshotObservation: ...
    def _get_mouse_state(self) -> MouseStateObservation: ...
    def _get_keyboard_state(self) -> KeyboardStateObservation: ...
    def get_observation(self) -> Dict[str, Any]: ...
    def _execute_command(self, action: CommandAction) -> bool: ...
    def _execute_keyboard_key_down(self, action: KeyboardKeyDownAction) -> bool: ...
    def _execute_keyboard_key_release(self, action: KeyboardKeyReleaseAction) -> bool: ...
    def _execute_type(self, action: TypeAction) -> bool: ...
    def _execute_mouse_move(self, action: MouseMoveAction) -> bool: ...
    def _execute_mouse_scroll(self, action: MouseScrollAction) -> bool: ...
    def _execute_mouse_button_down(self, action: MouseButtonDownAction) -> bool: ...
    def _execute_mouse_button_up(self, action: MouseButtonUpAction) -> bool: ...
    def _execute_keyboard_key_press(self, action: KeyboardKeyPressAction) -> bool: ...
    def _execute_keyboard_hotkey(self, action: KeyboardHotkeyAction) -> bool: ...

# VNC Computer
class VNCComputer(BaseComputer):
    def __init__(self, host: str = "localhost", port: int = 5900, password: Optional[str] = None) -> None: ...
    def _start(self) -> bool: ...
    def _stop(self) -> bool: ...
    def reset_state(self) -> None: ...
    def _get_screenshot(self) -> ScreenshotObservation: ...
    def _get_mouse_state(self) -> MouseStateObservation: ...
    def _get_keyboard_state(self) -> KeyboardStateObservation: ...
    def _execute_command(self, action: CommandAction) -> bool: ...
    def _execute_keyboard_key_down(self, action: KeyboardKeyDownAction) -> bool: ...
    def _execute_keyboard_key_release(self, action: KeyboardKeyReleaseAction) -> bool: ...
    def _execute_type(self, action: TypeAction) -> bool: ...
    def _execute_mouse_move(self, action: MouseMoveAction) -> bool: ...
    def _execute_mouse_scroll(self, action: MouseScrollAction) -> bool: ...
    def _execute_mouse_button_down(self, action: MouseButtonDownAction) -> bool: ...
    def _execute_mouse_button_up(self, action: MouseButtonUpAction) -> bool: ...

# E2B Desktop Computer
class E2BDesktopComputer(BaseComputer):
    def __init__(self, video_stream: bool = False) -> None: ...
    def _start(self) -> bool: ...
    def _stop(self) -> bool: ...
    def reset_state(self) -> None: ...
    def _get_screenshot(self, display_id: int = 0) -> ScreenshotObservation: ...
    def _get_mouse_state(self) -> MouseStateObservation: ...
    def _get_keyboard_state(self) -> KeyboardStateObservation: ...
    def _execute_command(self, action: CommandAction) -> bool: ...
    def _execute_keyboard_key_down(self, action: KeyboardKeyDownAction) -> bool: ...
    def _execute_keyboard_key_release(self, action: KeyboardKeyReleaseAction) -> bool: ...
    def _execute_type(self, action: TypeAction) -> bool: ...
    def _execute_mouse_move(self, action: MouseMoveAction) -> bool: ...
    def _execute_mouse_scroll(self, action: MouseScrollAction) -> bool: ...
    def _execute_mouse_button_down(self, action: MouseButtonDownAction) -> bool: ...
    def _execute_mouse_button_up(self, action: MouseButtonUpAction) -> bool: ...
    def _execute_click(self, action: ClickAction) -> bool: ...
    def _execute_double_click(self, action: DoubleClickAction) -> bool: ...
    def _execute_keyboard_key_press(self, action: KeyboardKeyPressAction) -> bool: ...
    def _execute_keyboard_hotkey(self, action: KeyboardHotkeyAction) -> bool: ...
    def locate_on_screen(self, text: str) -> Optional[Tuple[int, int]]: ...
    def open_file(self, file_path: str) -> bool: ...
    def get_video_stream_url(self) -> str: ...

# Daemon Client Computer
class DaemonClientComputer(BaseComputer):
    def __init__(
        self,
        daemon_base_url: str,
        daemon_port: int,
        daemon_token: str,
        provisioner: Any,
    ) -> None: ...
    def _start(self) -> bool: ...
    def _stop(self) -> bool: ...
    def reset_state(self) -> bool: ...
    def get_observation(self) -> Dict[str, Any]: ...
    def _get_screenshot(self) -> ScreenshotObservation: ...
    def _get_mouse_state(self) -> MouseStateObservation: ...
    def _get_keyboard_state(self) -> KeyboardStateObservation: ...
    def _execute_command(self, action: CommandAction) -> bool: ...
    def _execute_keyboard_key_down(self, action: KeyboardKeyDownAction) -> bool: ...
    def _execute_keyboard_key_release(self, action: KeyboardKeyReleaseAction) -> bool: ...
    def _execute_keyboard_key_press(self, action: KeyboardKeyPressAction) -> bool: ...
    def _execute_keyboard_hotkey(self, action: KeyboardHotkeyAction) -> bool: ...
    def _execute_type(self, action: TypeAction) -> bool: ...
    def _execute_mouse_move(self, action: MouseMoveAction) -> bool: ...
    def _execute_mouse_scroll(self, action: MouseScrollAction) -> bool: ...
    def _execute_mouse_button_down(self, action: MouseButtonDownAction) -> bool: ...
    def _execute_mouse_button_up(self, action: MouseButtonUpAction) -> bool: ...

# PigDev Computer
class PigDevComputer(BaseComputer):
    def __init__(self, api_key: Optional[str] = None, machine_id: Optional[str] = None) -> None: ...
    def _start(self) -> bool: ...
    def _stop(self) -> bool: ...
    def reset_state(self) -> None: ...
    def _get_screenshot(self) -> ScreenshotObservation: ...
    def _get_mouse_state(self) -> MouseStateObservation: ...
    def _get_keyboard_state(self) -> KeyboardStateObservation: ...
    def _execute_command(self, action: CommandAction) -> bool: ...
    def _execute_keyboard_key_down(self, action: KeyboardKeyDownAction) -> bool: ...
    def _execute_keyboard_key_release(self, action: KeyboardKeyReleaseAction) -> bool: ...
    def _execute_type(self, action: TypeAction) -> bool: ...
    def _execute_mouse_move(self, action: MouseMoveAction) -> bool: ...
    def _execute_mouse_scroll(self, action: MouseScrollAction) -> bool: ...
    def _execute_mouse_button_down(self, action: MouseButtonDownAction) -> bool: ...
    def _execute_mouse_button_up(self, action: MouseButtonUpAction) -> bool: ...
    def _execute_click(self, action: ClickAction) -> bool: ...
    def _execute_double_click(self, action: DoubleClickAction) -> bool: ...
    def _execute_drag(self, action: DragAction) -> bool: ...
    def _execute_keyboard_key_press(self, action: KeyboardKeyPressAction) -> bool: ...
    def _execute_keyboard_hotkey(self, action: KeyboardHotkeyAction) -> bool: ...

# Scrapybara Computer
class ScrapybaraComputer(BaseComputer):
    def __init__(self, api_key: Optional[str] = None) -> None: ...
    def _start(self) -> bool: ...
    def _stop(self) -> bool: ...
    def reset_state(self) -> None: ...
    def _get_screenshot(self) -> ScreenshotObservation: ...
    def _get_mouse_state(self) -> MouseStateObservation: ...
    def _get_keyboard_state(self) -> KeyboardStateObservation: ...
    def _execute_command(self, action: CommandAction) -> bool: ...
    def _execute_keyboard_key_down(self, action: KeyboardKeyDownAction) -> bool: ...
    def _execute_keyboard_key_release(self, action: KeyboardKeyReleaseAction) -> bool: ...
    def _execute_type(self, action: TypeAction) -> bool: ...
    def _execute_mouse_move(self, action: MouseMoveAction) -> bool: ...
    def _execute_mouse_scroll(self, action: MouseScrollAction) -> bool: ...
    def _execute_mouse_button_down(self, action: MouseButtonDownAction) -> bool: ...
    def _execute_mouse_button_up(self, action: MouseButtonUpAction) -> bool: ...
    def _execute_click(self, action: ClickAction) -> bool: ...
    def _execute_keyboard_key_press(self, action: KeyboardKeyPressAction) -> bool: ...
    def _execute_keyboard_hotkey(self, action: KeyboardHotkeyAction) -> bool: ...
    def _execute_double_click(self, action: DoubleClickAction) -> bool: ...
    def _execute_drag(self, action: DragAction) -> bool: ...
    def pause(self) -> bool: ...
    def resume(self, timeout_hours: float = None) -> bool: ...
    def get_stream_url(self) -> str: ...

class UbuntuScrapybaraComputer(ScrapybaraComputer):
    def __init__(self, api_key: Optional[str] = None) -> None: ...
    def _start(self) -> bool: ...
    def _execute_command(self, action: CommandAction) -> bool: ...
    def edit_file(self, path: str, command: str, **kwargs) -> bool: ...

class BrowserScrapybaraComputer(ScrapybaraComputer):
    def __init__(self, api_key: Optional[str] = None) -> None: ...
    def _start(self) -> bool: ...
    def get_cdp_url(self) -> str: ...
    def save_auth(self, name: str = "default") -> str: ...
    def authenticate(self, auth_state_id: str) -> bool: ...
    def _execute_command(self, action: CommandAction) -> bool: ...

class WindowsScrapybaraComputer(ScrapybaraComputer):
    def __init__(self, api_key: Optional[str] = None) -> None: ...
    def _start(self) -> bool: ...
    def _execute_command(self, action: CommandAction) -> bool: ... 