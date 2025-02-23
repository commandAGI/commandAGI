from commandLAB.types import MouseStateObservation
from commandLAB.computers.vnc_docker_computer import VNCDockerComputer


class LXDEVNCDockerComputer(VNCDockerComputer):
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
            # Docker exec results have output attribute instead of stdout
            if result.exit_code != 0:
                print(
                    f"xdotool getmouselocation error: {result.output.decode('utf-8') if result.output else ''}"
                )
                return MouseStateObservation(position=(0, 0), buttons={})

            output = result.output.decode("utf-8").strip()
            # Expected output example: "x:100 y:200 screen:0 window:12345678"
            parts = output.split()
            x = int(parts[0].split(":")[1])
            y = int(parts[1].split(":")[1])

            return MouseStateObservation(position=(x, y), buttons={})
        except Exception as e:
            print(f"Error in get_mouse_state: {e}")
            return None
