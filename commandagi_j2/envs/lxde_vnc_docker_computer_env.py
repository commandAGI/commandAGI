import time

from commandagi_j2.envs.base_vnc_docker_computer_env import VNCDockerComputerEnv
from commandagi_j2.envs.computer_types import (
    MouseStateObservation,
    KeyboardKey,
)


class LXDEVNCDockerComputerEnv(VNCDockerComputerEnv):
    def __init__(self, user="root", password="secret", vnc_port=5900):
        # Note: the dockerfile_path is given first and the container name will be auto-generated.
        super().__init__(
            dockerfile_path="dockerfiles/lxde.Dockerfile",
            user=user,
            password=password,
            vnc_port=vnc_port,
        )

    def get_mouse_state(self) -> MouseStateObservation:
        """
        Retrieve the current mouse position using xdotool inside the container.
        Note: xdotool must be installed within the container.
        """
        try:
            result = self.run_command_in_container(
                "xdotool getmouselocation", timeout=5
            )
            if result.returncode != 0:
                print(
                    f"xdotool getmouselocation error: {result.stderr.decode('utf-8')}"
                )
                return MouseStateObservation(position=(0, 0), buttons={})

            output = result.stdout.decode("utf-8").strip()
            # Expected output example: "x:100 y:200 screen:0 window:12345678"
            parts = output.split()
            x = int(parts[0].split(":")[1])
            y = int(parts[1].split(":")[1])

            return MouseStateObservation(position=(x, y), buttons={})
        except Exception as e:
            print(f"Error in get_mouse_state: {e}")
            return MouseStateObservation(position=(0, 0), buttons={})

    def _vnc_hotkey(self, modifier: str, key: str):
        """
        Simulate a hotkey press using the VNC connection.
        Presses the modifier (e.g. "super") and the key (e.g. "d") sequentially.
        This can be used for LXDE-specific shortcuts (e.g. Show Desktop).
        """
        vnc_modifier = KeyboardKey.to_vnc(modifier)
        vnc_key = KeyboardKey.to_vnc(key)
        self.vnc.keyDown(vnc_modifier)
        time.sleep(0.1)
        self.vnc.keyDown(vnc_key)
        time.sleep(0.1)
        self.vnc.keyUp(vnc_key)
        time.sleep(0.1)
        self.vnc.keyUp(vnc_modifier)
