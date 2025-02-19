import subprocess
import base64
from typing import Optional

from e2b_desktop import Sandbox
from commandagi_j2.computers.base_computer import Computer
from commandagi_j2.envs.computer_types import (
    KeyboardKey,
    MouseButton,
    ScreenshotObservation,
    MouseStateObservation,
    KeyboardStateObservation,
    CommandAction,
    TypeAction,
    KeyboardKeyDownAction,
    KeyboardKeyReleaseAction,
    MouseMoveAction,
    MouseScrollAction,
    MouseButtonDownAction,
    MouseButtonUpAction,
)

class E2BDesktopComputer(Computer):
    """
    Computer implementation using E2B Desktop Sandbox for secure computer interactions.
    """

    def __init__(self, video_stream: bool = False):
        self.desktop = Sandbox(video_stream=video_stream)

    def get_screenshot(self) -> Optional[ScreenshotObservation]:
        screenshot = self.desktop.take_screenshot()
        b64_screenshot = base64.b64encode(screenshot).decode('utf-8')
        return ScreenshotObservation(screenshot=b64_screenshot)

    def get_mouse_state(self) -> Optional[MouseStateObservation]:
        raise NotImplementedError("E2BDesktopComputer does not support mouse state observation.")

    def get_keyboard_state(self) -> Optional[KeyboardStateObservation]:
        raise NotImplementedError("E2BDesktopComputer does not support keyboard state observation.")

    def execute_command(self, action: CommandAction) -> bool:
        try:
            result = subprocess.run(
                action.command,
                shell=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                timeout=action.timeout if action.timeout is not None else 10,
            )
            return result.returncode == 0
        except Exception as e:
            print(f"Error executing command: {e}")
            return False

    def execute_keyboard_key_down(self, action: KeyboardKeyDownAction) -> bool:
        e2b_key = KeyboardKey.to_e2b(action.key)
        return self.desktop.pyautogui(f"pyautogui.keyDown('{e2b_key}')")

    def execute_keyboard_key_release(self, action: KeyboardKeyReleaseAction) -> bool:
        e2b_key = KeyboardKey.to_e2b(action.key)
        return self.desktop.pyautogui(f"pyautogui.keyUp('{e2b_key}')")

    def execute_type(self, action: TypeAction) -> bool:
        return self.desktop.write(action.text)

    def execute_mouse_move(self, action: MouseMoveAction) -> bool:
        return self.desktop.mouse_move(action.x, action.y)

    def execute_mouse_scroll(self, action: MouseScrollAction) -> bool:
        return self.desktop.pyautogui(f"pyautogui.scroll({action.amount})")

    def execute_mouse_button_down(self, action: MouseButtonDownAction) -> bool:
        e2b_button = MouseButton.to_e2b(action.button)
        return self.desktop.pyautogui(f"pyautogui.mouseDown(button='{e2b_button}')")

    def execute_mouse_button_up(self, action: MouseButtonUpAction) -> bool:
        e2b_button = MouseButton.to_e2b(action.button)
        return self.desktop.pyautogui(f"pyautogui.mouseUp(button='{e2b_button}')")

    def close(self):
        self.desktop = None 