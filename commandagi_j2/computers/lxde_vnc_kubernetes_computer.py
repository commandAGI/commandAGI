from typing import Optional, Dict
import subprocess

from commandagi_j2.computers.vnc_kubernetes_computer import VNCKubernetesComputer
from commandagi_j2.envs.computer_types import (
    MouseStateObservation,
    CommandAction,
    KeyboardStateObservation,
)

class LXDEVNCKubernetesComputer(VNCKubernetesComputer):
    """
    Kubernetes computer with LXDE desktop and VNC support.
    Extends VNCKubernetesComputer by adding methods to retrieve the mouse state using xdotool.
    """
    
    def __init__(
        self,
        pod_name: str = "lxde-vnc-kub",
        namespace: str = "default",
        user: str = "root",
        password: str = "secret",
        vnc_port: int = 5900,
        env_vars: dict = None,
        ports: dict = None,
    ):
        # For LXDE environments, we use a specific image
        image = "lxde_image"
        super().__init__(
            pod_name=pod_name,
            image=image,
            namespace=namespace,
            vnc_port=vnc_port,
            user=user,
            password=password,
            env_vars=env_vars,
            ports=ports,
        )

    def get_mouse_state(self) -> Optional[MouseStateObservation]:
        """
        Retrieve the current mouse position using xdotool inside the pod.
        xdotool must be installed within the pod's LXDE environment.
        """
        try:
            cmd = [
                "kubectl", "exec", self.pod_name, "-n", self.namespace,
                "--", "xdotool", "getmouselocation"
            ]
            result = subprocess.run(cmd, capture_output=True, text=True)
            if result.returncode != 0:
                print(f"xdotool getmouselocation error: {result.stderr}")
                return MouseStateObservation(position=(0, 0), buttons={})

            # Expected output format: "x:100 y:200 screen:0 window:12345678"
            output = result.stdout.strip()
            parts = output.split()
            x = int(parts[0].split(":")[1])
            y = int(parts[1].split(":")[1])
            return MouseStateObservation(position=(x, y), buttons={})
        except Exception as e:
            print(f"Error in get_mouse_state: {e}")
            return MouseStateObservation(position=(0, 0), buttons={})

    def get_keyboard_state(self) -> Optional[KeyboardStateObservation]:
        """LXDE VNC doesn't support keyboard state observation"""
        return None

    def reset(self) -> bool:
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
        # Modify the command to ensure DISPLAY is set for GUI applications
        display_cmd = f"DISPLAY=:1 {action.command}"
        return super().execute_command(CommandAction(
            command=display_cmd,
            timeout=action.timeout
        ))

    def _create_pod(self):
        """
        Create the LXDE pod with necessary environment variables and configurations.
        """
        # Add LXDE-specific environment variables
        self.env_vars.update({
            "DISPLAY": ":1",
            "DESKTOP_SESSION": "LXDE",
            "XDG_CURRENT_DESKTOP": "LXDE",
        })
        
        # Create pod with environment variables
        env_args = []
        for key, value in self.env_vars.items():
            env_args.extend(["--env", f"{key}={value}"])

        cmd = [
            "kubectl", "run", self.pod_name,
            "--image", self.image,
            "--restart", "Never",
            "-n", self.namespace,
        ] + env_args

        result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        if result.returncode != 0:
            raise Exception(f"Failed to create LXDE pod: {result.stderr.decode('utf-8')}") 