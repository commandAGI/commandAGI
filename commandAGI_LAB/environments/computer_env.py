from typing import ClassVar

from commandAGI_LAB.computers.base_computer import BaseComputer
from commandAGI_LAB.environments.base_env import BaseEnv
from commandAGI_LAB.types import ComputerAction, ComputerObservation
from rich.console import Console

console = Console()


class BaseComputerEnv(BaseEnv[ComputerObservation, ComputerAction]):
    """Base class for computer environments with standard actions"""

    computer: BaseComputer
    _LOG_MODALITY_ERRORS: ClassVar[bool] = False

    def reset(self) -> ComputerObservation:
        return self.computer.reset()

    def close(self):
        self.computer.close()

    def get_observation(self) -> ComputerObservation:
        """
        Get the current observation of the environment as a ComputerObservation containing:
            screenshot: Optional[ScreenshotObservation]
            mouse_state: Optional[MouseStateObservation]
            keyboard_state: Optional[KeyboardStateObservation]
        """
        try:
            screenshot = self.computer.get_screenshot()
        except Exception as e:
            if self._LOG_MODALITY_ERRORS:
                console.print(f"🖼️ [red]Error getting screenshot:[/] {e}")
            screenshot = None

        try:
            mouse_state = self.computer.get_mouse_state()
        except Exception as e:
            if self._LOG_MODALITY_ERRORS:
                console.print(f"🖱️ [red]Error getting mouse state:[/] {e}")
            mouse_state = None

        try:
            keyboard_state = self.computer.get_keyboard_state()
        except Exception as e:
            if self._LOG_MODALITY_ERRORS:
                console.print(f"⌨️ [red]Error getting keyboard state:[/] {e}")
            keyboard_state = None

        return ComputerObservation(
            screenshot=screenshot,
            mouse_state=mouse_state,
            keyboard_state=keyboard_state,
        )

    def execute_action(self, action: ComputerAction) -> bool:
        """Route the action to the appropriate handler implemented by subclasses."""
        success = True

        if action.command:
            try:
                success = self.computer.execute_command(
                    action.command.command, action.command.timeout
                )
            except Exception as e:
                if self._LOG_MODALITY_ERRORS:
                    console.print(f"💻 [red]Error executing command:[/] {e}")
                success = False

        if action.keyboard_keys_press:
            try:
                success = self.computer.execute_keyboard_keys_press(
                    action.keyboard_keys_press.keys
                )
            except Exception as e:
                if self._LOG_MODALITY_ERRORS:
                    console.print(f"⌨️ [red]Error executing keyboard press:[/] {e}")
                success = False

        if action.keyboard_keys_down:
            try:
                success = self.computer.execute_keyboard_keys_down(
                    action.keyboard_keys_down.keys
                )
            except Exception as e:
                if self._LOG_MODALITY_ERRORS:
                    console.print(f"⌨️ [red]Error executing keyboard down:[/] {e}")
                success = False

        if action.keyboard_keys_release:
            try:
                success = self.computer.execute_keyboard_keys_release(
                    action.keyboard_keys_release.keys
                )
            except Exception as e:
                if self._LOG_MODALITY_ERRORS:
                    console.print(f"⌨️ [red]Error executing keyboard release:[/] {e}")
                success = False

        if action.keyboard_hotkey:
            try:
                success = self.computer.execute_keyboard_hotkey(
                    action.keyboard_hotkey.keys
                )
            except Exception as e:
                if self._LOG_MODALITY_ERRORS:
                    console.print(f"⌨️ [red]Error executing keyboard hotkey:[/] {e}")
                success = False

        if action.type:
            try:
                success = self.computer.execute_type(action.type.text)
            except Exception as e:
                if self._LOG_MODALITY_ERRORS:
                    console.print(f"⌨️ [red]Error executing type:[/] {e}")
                success = False

        if action.mouse_move:
            try:
                success = self.computer.execute_mouse_move(
                    action.mouse_move.x,
                    action.mouse_move.y,
                    action.mouse_move.move_duration,
                )
            except Exception as e:
                if self._LOG_MODALITY_ERRORS:
                    console.print(f"🖱️ [red]Error executing mouse move:[/] {e}")
                success = False

        if action.mouse_scroll:
            try:
                success = self.computer.execute_mouse_scroll(action.mouse_scroll.amount)
            except Exception as e:
                if self._LOG_MODALITY_ERRORS:
                    console.print(f"🖱️ [red]Error executing mouse scroll:[/] {e}")
                success = False

        if action.mouse_button_down:
            try:
                success = self.computer.execute_mouse_button_down(
                    action.mouse_button_down.button
                )
            except Exception as e:
                if self._LOG_MODALITY_ERRORS:
                    console.print(f"🖱️ [red]Error executing mouse button down:[/] {e}")
                success = False

        if action.mouse_button_up:
            try:
                success = self.computer.execute_mouse_button_up(
                    action.mouse_button_up.button
                )
            except Exception as e:
                if self._LOG_MODALITY_ERRORS:
                    console.print(f"🖱️ [red]Error executing mouse button up:[/] {e}")
                success = False

        if action.click:
            try:
                success = self.computer.execute_click(action.click)
            except Exception as e:
                if self._LOG_MODALITY_ERRORS:
                    console.print(f"🖱️ [red]Error executing click:[/] {e}")
                success = False

        if action.drag:
            try:
                success = self.computer.execute_drag(action.drag)
            except Exception as e:
                if self._LOG_MODALITY_ERRORS:
                    console.print(f"🖱️ [red]Error executing drag:[/] {e}")
                success = False

        return success

    def get_reward(self, action: ComputerAction) -> float:
        return 0

    def get_done(self, action: ComputerAction) -> bool:
        return False

    def render(self, mode="human"):
        if mode == "human":
            try:
                from commandAGI_LAB.utils.viewer import EnvironmentViewer
            except ImportError:
                console.print(
                    "❌ [red]TkRender is required for human rendering but is not installed.[/]"
                )
                raise ImportError(
                    "TkRender is required for human rendering but is not installed."
                )
            # Instantiate the TkRender with the current environment instance (self)
            self._env_viewer = EnvironmentViewer(
                self
            )  # This will open the window and block as mainloop runs
        elif mode == "rgb_array":
            obs = self.computer.get_screenshot()
            if not obs or not obs.screenshot:
                return None

            import numpy as np
            import base64
            import io
            from PIL import Image

            # Decode base64 string to bytes
            img_bytes = base64.b64decode(obs.screenshot)

            # Convert bytes to PIL Image
            img = Image.open(io.BytesIO(img_bytes))

            # Convert PIL Image to numpy array
            return np.array(img)
        else:
            console.print(f"❌ [red]Unsupported render mode:[/] {mode}")
            raise ValueError("Unsupported render mode: " + mode)
