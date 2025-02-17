import os
import tempfile
import subprocess
import time
from vncdotool import api
from commandagi_j2.envs.base_computer_env import BaseComputerEnv
from commandagi_j2.envs.computer_types import (
    ComputerAction,
    KeyboardKey,
    KeyboardKeyDownAction,
    KeyboardKeyPressAction,
    KeyboardKeyReleaseAction,
    ScreenshotObservation,
    MouseStateObservation,
    KeyboardStateObservation,
    MouseButton,
    CommandAction,
    TypeAction,
    MouseMoveAction,
    MouseScrollAction,
    MouseButtonDownAction,
    MouseButtonUpAction,
    ClickAction,
)


class DockerLxdeEnv(BaseComputerEnv):
    def __init__(
        self, container_name="lxde_container", password="secret", vnc_port=5900
    ):
        super().__init__()
        self.container_name = container_name
        self.password = password
        self.vnc_port = vnc_port
        self.vnc_host = "localhost"
        self.temp_dir = tempfile.mkdtemp()
        self.last_screenshot = None
        self.vnc = None

        # Start the container and connect to its VNC
        self._start_docker_container()
        self._connect_vnc()

    def _start_docker_container(self):
        """
        Start a Docker container that has a VNC server (e.g., dorowu/ubuntu-desktop-lxde-vnc).
        This container will expose VNC on 5900 by default. Adjust as needed.
        """
        # If it's already running, you might want to skip, or do a docker stop/rm first
        # In this example, we'll forcibly remove if it exists, then run again:
        subprocess.run(
            f"docker rm -f {self.container_name}",
            shell=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )

        # Example run command using dorowu/ubuntu-desktop-lxde-vnc
        # Expose the container's 5900 on localhost:5900
        # We set the PASSWORD env var to the "secret" password.
        run_cmd = (
            f"docker run -d --name {self.container_name} "
            f"-p {self.vnc_port}:5900 "
            f"-e USER=root "
            f"-e PASSWORD={self.password} "
            f"dorowu/ubuntu-desktop-lxde-vnc"
        )
        subprocess.run(run_cmd, shell=True, check=True)

        # Give the container time to spin up the VNC server
        time.sleep(5)

    def _connect_vnc(self):
        """
        Connect to the container's VNC server using vncdotool
        """
        # vncdotool expects host::port format; password is passed at connect time
        self.vnc = api.connect(
            f"{self.vnc_host}::{self.vnc_port}", password=self.password
        )

    def execute_in_container(self, cmd):
        """
        (Deprecated in this VNC-based approach)
        We no longer rely on xdotool or direct docker exec commands for interactions.
        You could keep a method to run commands in the container if needed,
        but for user input simulation we now use VNC.
        """
        pass

    def reset(self):
        """
        Reset the environment. For instance, pressing 'Super+d' in LXDE inside
        the Docker container might show the desktop. Adjust to your needs.
        """
        # Example hotkey for "Show Desktop" in LXDE or Ubuntu
        # (You might need the right combination, e.g., 'ctrl+alt+d' or 'super+d')
        # We'll try super+d:
        self._vnc_hotkey("super", "d")
        time.sleep(1)
        return self._get_observation()

    def step(self, action):
        success = self._execute_action(action)
        observation = self._get_observation()
        reward = 1.0 if success else -1.0
        done = False
        info = {"action_success": success}
        return observation, reward, done, info

    def close(self):
        """
        Close the environment and stop the container if desired
        """
        if self.vnc:
            self.vnc.disconnect()
        subprocess.run(f"docker rm -f {self.container_name}", shell=True)

    def get_screenshot(self) -> ScreenshotObservation:
        screenshot_path = os.path.join(self.temp_dir, "docker_lxde_screenshot.png")
        self.vnc.captureScreen(screenshot_path)
        self.last_screenshot = screenshot_path
        return ScreenshotObservation(screenshot=screenshot_path)

    def get_mouse_state(self) -> MouseStateObservation:
        raise NotImplementedError(
            "DockerLxdeEnv does not support mouse state observation"
        )

    def get_keyboard_state(self) -> KeyboardStateObservation:
        raise NotImplementedError(
            "DockerLxdeEnv does not support keyboard state observation"
        )

    def execute_command(self, action: CommandAction) -> bool:
        try:
            result = subprocess.run(
                f"docker exec {self.container_name} {action.command}",
                shell=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                timeout=action.timeout if action.timeout is not None else 10,
            )
            return result.returncode == 0
        except Exception as e:
            print(f"Error executing command in container: {e}")
            return False

    def execute_keyboard_key_down(self, action: KeyboardKeyDownAction) -> bool:
        """Execute key down for a keyboard key using VNC."""
        vnc_key = KeyboardKey.to_vnc(action.key)
        self.vnc.keyDown(vnc_key)
        return True

    def execute_keyboard_key_release(self, action: KeyboardKeyReleaseAction) -> bool:
        """Execute key release for a keyboard key using VNC."""
        vnc_key = KeyboardKey.to_vnc(action.key)
        self.vnc.keyUp(vnc_key)
        return True

    def execute_type(self, action: TypeAction) -> bool:
        self.vnc.write(action.text)
        return True

    def execute_mouse_move(self, action: MouseMoveAction) -> bool:
        self.vnc.mouseMove(action.x, action.y)
        return True

    def execute_mouse_scroll(self, action: MouseScrollAction) -> bool:
        print(f"Scrolling by amount {action.amount} not implemented in DockerLxdeEnv")
        return False

    def execute_mouse_button_down(self, action: MouseButtonDownAction) -> bool:
        vnc_button = MouseButton.to_vnc(action.button)
        self.vnc.mouseDown(vnc_button)
        return True

    def execute_mouse_button_up(self, action: MouseButtonUpAction) -> bool:
        vnc_button = MouseButton.to_vnc(action.button)
        self.vnc.mouseUp(vnc_button)
        return True
