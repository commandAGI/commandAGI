import base64
import io
from typing import Callable, Optional

from PIL import Image

from commandAGI.gym.environments.computer_env import ComputerEnv
from commandAGI.processors.grid_overlay import overlay_grid
from commandAGI.processors.screen_parser.pytesseract_screen_parser import (
    parse_screenshot as parse_with_tesseract,
)
from commandAGI.processors.screen_parser.screenparse_ai_screen_parser import (
    parse_screenshot as parse_with_screenparse_ai,
)
from commandAGI.processors.screen_parser.types import ParsedScreenshot
from commandAGI.types import ComputerAction, ComputerObservation


class GridOverlayWrapper(ComputerEnv):
    """Wrapper that adds a grid overlay to screenshot observations and optionally parses screen text."""

    def __init__(
        self,
        env: ComputerEnv,
        grid_px_size: int = 100,
        screen_parser: Optional[str] = None,
        screenparse_ai_key: Optional[str] = None,
    ):
        """
        Args:
            env: The environment to wrap
            grid_px_size: Size of grid cells in pixels
            screen_parser: Which parser to use ('tesseract' or 'screenparse_ai')
            screenparse_ai_key: API key for ScreenParse.ai if using that parser
        """
        self.env = env
        self.grid_px_size = grid_px_size
        self.screen_parser = screen_parser
        self.screenparse_ai_key = screenparse_ai_key
        self.parsed_screenshot: Optional[ParsedScreenshot] = None

        # Set up the appropriate parser function
        self.parser_fn: Optional[Callable] = None
        if screen_parser == "tesseract":
            self.parser_fn = parse_with_tesseract
        elif screen_parser == "screenparse_ai":
            if not screenparse_ai_key:
                raise ValueError(
                    "screenparse_ai_key is required when using screenparse_ai parser"
                )
            self.parser_fn = lambda screenshot: parse_with_screenparse_ai(
                screenshot, api_key=screenparse_ai_key
            )

        # Initialize parent with same computer as wrapped env
        super().__init__(computer=env._computer)

    def step(
        self, action: ComputerAction
    ) -> tuple[ComputerObservation, float, bool, dict]:
        obs, reward, done, info = self.env.step(action)
        obs = self._process_observation(obs)
        # Add parsed screenshot to info dict if available
        if self.parsed_screenshot:
            info["parsed_screenshot"] = self.parsed_screenshot
        return obs, reward, done, info

    def reset(self) -> ComputerObservation:
        obs = self.env.reset()
        return self._process_observation(obs)

    def _process_observation(self, obs: ComputerObservation) -> ComputerObservation:
        """Add grid overlay to screenshot and optionally parse screen text"""
        if obs.get("screenshot") and obs["screenshot"].screenshot:
            # Store original screenshot for parsing
            original_screenshot = obs["screenshot"].screenshot

            # Decode base64 screenshot to PIL Image
            img_bytes = base64.b64decode(original_screenshot)
            img = Image.open(io.BytesIO(img_bytes))

            # Apply grid overlay
            img_with_grid = overlay_grid(img, self.grid_px_size)

            # Convert back to base64
            buffered = io.BytesIO()
            img_with_grid.save(buffered, format="PNG")
            img_base64 = base64.b64encode(buffered.getvalue()).decode()

            # Update observation with new screenshot
            obs["screenshot"].screenshot = img_base64

            # Parse the original screenshot if parser is configured
            if self.parser_fn:
                self.parsed_screenshot = self.parser_fn(original_screenshot)

        return obs

    def close(self):
        self.env.close()

    def get_parsed_screenshot(self) -> Optional[ParsedScreenshot]:
        """Get the most recent parsed screenshot data"""
        return self.parsed_screenshot
