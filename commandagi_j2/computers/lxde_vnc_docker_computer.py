from typing import Optional
from commandagi_j2.computers.vnc_docker_computer import VNCDockerComputer
from commandagi_j2.envs.computer_types import MouseStateObservation, KeyboardStateObservation, CommandAction

class LXDEVNCDockerComputer(VNCDockerComputer):
    """
    Docker computer with LXDE desktop support.
    Extends VNCDockerComputer by adding LXDE-specific functionality.
    """
    def __init__(
        self,
        container_name: str = None,
        user: str = "root",
        password: str = "secret",
        vnc_port: int = 5900,
        env_vars: dict = None,
        ports: dict = None,
    ):
        # For LXDE environments, we use a predefined Dockerfile and image tag
        dockerfile_path = "dockerfiles/lxde.Dockerfile"
        image_tag = "lxde_image"
        
        super().__init__(
            dockerfile_path=dockerfile_path,
            container_name=container_name,
            user=user,
            password=password,
            vnc_port=vnc_port,
            image_tag=image_tag,
            ports=ports,
            env_vars=env_vars,
        )

    def get_mouse_state(self) -> MouseStateObservation:
        """
        Retrieve the current mouse position using xdotool inside the container.
        Note: xdotool must be installed within the container.
        """
        try:
            result = self.container.exec_run("xdotool getmouselocation", tty=True)
            if result.exit_code != 0:
                print(f"xdotool getmouselocation error: {result.output.decode('utf-8')}")
                return MouseStateObservation(position=(0, 0), buttons={})

            # Expected output format: "x:100 y:200 screen:0 window:12345678"
            output = result.output.decode("utf-8").strip()
            parts = output.split()
            x = int(parts[0].split(":")[1])
            y = int(parts[1].split(":")[1])
            return MouseStateObservation(position=(x, y), buttons={})
        except Exception as e:
            print(f"Error in get_mouse_state: {e}")
            return MouseStateObservation(position=(0, 0), buttons={})

    def reset(self):
        """
        Reset the LXDE desktop environment by simulating the 'show desktop' hotkey.
        """
        try:
            # Send Super+d to show desktop in LXDE
            self.vnc.keyDown("super")
            self.vnc.keyDown("d")
            self.vnc.keyUp("d")
            self.vnc.keyUp("super")
            return True
        except Exception as e:
            print(f"Error resetting LXDE desktop: {e}")
            return False

    def execute_command(self, action: CommandAction) -> bool:
        """
        Execute a command in the LXDE container.
        Ensures DISPLAY is set for GUI applications.
        """
        try:
            # Ensure DISPLAY is set for GUI applications
            cmd = f"DISPLAY=:1 {action.command}"
            exec_result = self.container.exec_run(cmd, tty=True, stdin=True)
            return exec_result.exit_code == 0
        except Exception as e:
            print(f"Error executing command in container: {e}")
            return False

    def get_keyboard_state(self) -> Optional[KeyboardStateObservation]:
        """LXDE Docker VNC doesn't support keyboard state observation"""
        return None 