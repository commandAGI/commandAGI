import os
import tempfile
import subprocess
import time
from vncdotool import api
from commandagi_j2.envs.base_computer_env import BaseComputerEnv
from commandagi_j2.envs.computer_actions import ComputerAction


class DockerLxdeEnv(BaseComputerEnv):
    def __init__(self, container_name="lxde_container", password="secret", vnc_port=5900):
        super().__init__()
        self.container_name = container_name
        self.password = password
        self.vnc_port = vnc_port
        self.vnc_host = "localhost"
        self.temp_dir = tempfile.mkdtemp()
        self.last_screenshot = None
        self.vnc = None

        # Replace the default action_space with actions that use vncdotool
        self.action_space = {
            ComputerAction.CLICK.value: self._vnc_click,
            ComputerAction.TYPE.value: self._vnc_type,
            ComputerAction.PRESS.value: self._vnc_press,
            ComputerAction.HOTKEY.value: self._vnc_hotkey
        }

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
        subprocess.run(f"docker rm -f {self.container_name}", shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

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
        self.vnc = api.connect(f"{self.vnc_host}::{self.vnc_port}", password=self.password)

    def _vnc_click(self, x_str, y_str):
        """
        Move mouse to (x, y) and perform a left-click
        """
        x, y = int(x_str), int(y_str)
        self.vnc.mouseMove(x, y)
        # left mouse button is button=1
        self.vnc.mouseDown(1)
        self.vnc.mouseUp(1)
        return True

    def _vnc_type(self, text):
        """
        Type text by sending keystrokes. If you need special keys, you may
        have to split them or use another approach in vncdotool.
        """
        for char in text:
            self.vnc.keyPress(char)
        return True

    def _vnc_press(self, key):
        """
        Press a single key (e.g., 'enter', 'backspace', etc.)
        For standard text characters, see the _vnc_type approach.
        """
        # For special keys, vncdotool might expect them in bracket notation, e.g.:
        # Enter: 'return', Tab: 'tab', etc.
        self.vnc.keyPress(key)
        return True

    def _vnc_hotkey(self, *keys):
        """
        Press multiple keys together (e.g., ctrl+c).
        """
        # As an example, we'll press them in quick succession. 
        # If you want them "held down" simultaneously, you can do keyDown() calls, then keyUp().
        for k in keys:
            self.vnc.keyPress(k)
        return True

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

    def _get_observation(self):
        """
        Currently returns a screenshot from the VNC server. 
        """
        return self._take_screenshot()

    def _take_screenshot(self):
        """
        Capture the screen through VNC and store locally.
        """
        screenshot_path = os.path.join(self.temp_dir, "docker_lxde_screenshot.png")
        self.vnc.captureScreen(screenshot_path)
        self.last_screenshot = screenshot_path
        return screenshot_path 