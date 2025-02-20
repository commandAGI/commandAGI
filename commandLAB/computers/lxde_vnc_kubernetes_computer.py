from commandLAB.computers.computer_types import MouseStateObservation
from commandLAB.computers.vnc_kubernetes_computer import \
    VNCKubernetesComputer


class LXDEVNCKubernetesComputer(VNCKubernetesComputer):
    """
    Kubernetes environment with VNC and LXDE desktop support.
    Extends VNCKubernetesComputer by adding methods to retrieve the mouse state using xdotool
    and a reset method that simulates the LXDE 'show desktop' hotkey (super+d).
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
        # For LXDE environments, we assume the pod uses an image with LXDE (e.g., "lxde_image")
        image = "lxde_image"
        super().__init__(pod_name, image, namespace, env_vars, ports)
        self.vnc_port = vnc_port
        self.vnc_host = "localhost"  # Assumes port-forwarding is set up
        self.password = password
        self._connect_vnc()

    def get_mouse_state(self) -> MouseStateObservation:
        """
        Retrieve the current mouse position using xdotool inside the pod.
        xdotool must be installed within the pod's LXDE environment.
        """
        try:
            result = self._exec_in_pod("xdotool getmouselocation", timeout=5)
            if result.returncode != 0:
                print(
                    f"xdotool getmouselocation error: {result.stderr.decode('utf-8')}"
                )
                return MouseStateObservation(position=(0, 0), buttons={})
            output = result.stdout.decode("utf-8").strip()
            # Expected output format: "x:100 y:200 screen:0 window:12345678"
            parts = output.split()
            x = int(parts[0].split(":")[1])
            y = int(parts[1].split(":")[1])
            return MouseStateObservation(position=(x, y), buttons={})
        except Exception as e:
            print(f"Error in get_mouse_state: {e}")
            return MouseStateObservation(position=(0, 0), buttons={})

    def reset(self):
        """
        Reset the environment, e.g., by showing the desktop using the 'super+d' hotkey combination.
        Returns the current observation.
        """
        return self.get_observation()
