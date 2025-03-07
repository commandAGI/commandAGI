from typing import Any, Optional
import base64
import io
from PIL import Image

from commandAGI.gym.environments.computer_env import ComputerEnv
from commandAGI.processors.grid_overlay import overlay_grid
from commandAGI.types import ComputerObservation, ComputerAction


class GridOverlayWrapper(ComputerEnv):
    """Wrapper that adds a grid overlay to screenshot observations."""

    def __init__(self, env: ComputerEnv, grid_px_size: int = 100):
        """
        Args:
            env: The environment to wrap
            grid_px_size: Size of grid cells in pixels
        """
        self.env = env
        self.grid_px_size = grid_px_size
        # Initialize parent with same computer as wrapped env
        super().__init__(computer=env._computer)

    def get_observation(self) -> ComputerObservation:
        obs = super().get_observation()

        if obs.get("screenshot") and obs["screenshot"].screenshot:
            # Decode base64 screenshot to PIL Image
            img_bytes = base64.b64decode(obs["screenshot"].screenshot)
            img = Image.open(io.BytesIO(img_bytes))

            # Apply grid overlay
            img_with_grid = overlay_grid(img, self.grid_px_size)

            # Convert back to base64
            buffered = io.BytesIO()
            img_with_grid.save(buffered, format="PNG")
            img_base64 = base64.b64encode(buffered.getvalue()).decode()

            # Update observation with new screenshot
            obs["screenshot"].screenshot = img_base64

        return obs

    def __getattribute__(self, name: str):
        if name in ["get_observation", "env"]:
            return super().__getattribute__(name)
        else:
            return getattr(self.env, name)

    def __setattr__(self, name: str, value: Any) -> None:
        if name in ["get_observation", "env"]:
            super().__setattr__(name, value)
        else:
            setattr(self.env, name, value)

    def __delattr__(self, name: str) -> None:
        if name in ["get_observation", "env"]:
            super().__delattr__(name)
        else:
            delattr(self.env, name)
