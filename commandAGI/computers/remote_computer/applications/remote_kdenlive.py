from pathlib import Path
from typing import Dict, Optional, List, Union, Tuple, Any, Literal

from commandAGI.computers.base_computer.applications.base_kdenlive import BaseKdenlive
from commandAGI.computers.remote_computer.remote_application import (
    RemoteApplication,
)


class RemoteKdenlive(BaseKdenlive, RemoteApplication):
    """Base class for video editor operations.

    This class defines the interface for working with Kdenlive and similar
    MLT-based video editors. Implementations should provide methods to create
    and modify video projects through DBus or command-line interfaces.
    """

    model_config = {"arbitrary_types_allowed": True}

    # Application Management
    def launch_application(self, render_mode: bool = False) -> bool:
        """Launch the video editor application.

        Args:
            render_mode: Whether to launch in CLI render mode

        Returns:
            bool: True if application was launched successfully
        """
        raise NotImplementedError("Subclasses must implement launch_application")

    def close_application(self) -> bool:
        """Close the application.

        Returns:
            bool: True if application was closed successfully
        """
        raise NotImplementedError("Subclasses must implement close_application")

    # Project Management
    def create_project(self, profile: str = "hdv_1080_25p") -> bool:
        """Create a new project with specified profile.

        Args:
            profile: MLT profile name (e.g., hdv_1080_25p, atsc_1080p_25)

        Returns:
            bool: True if project was created successfully
        """
        raise NotImplementedError("Subclasses must implement create_project")

    def open_project(self, file_path: Union[str, Path]) -> bool:
        """Open a Kdenlive project file.

        Args:
            file_path: Path to the .kdenlive project file

        Returns:
            bool: True if project was opened successfully
        """
        raise NotImplementedError("Subclasses must implement open_project")

    def save_project(self, file_path: Optional[Union[str, Path]] = None) -> bool:
        """Save the current project.

        Args:
            file_path: Optional path to save to. If None, saves to current path.

        Returns:
            bool: True if project was saved successfully
        """
        raise NotImplementedError("Subclasses must implement save_project")

    # Clip Management
    def import_clip(
        self, file_path: Union[str, Path], folder_id: Optional[str] = None
    ) -> str:
        """Import media clip into project bin.

        Args:
            file_path: Path to the media file
            folder_id: Optional project bin ID

        Returns:
            str: ID of the imported clip
        """
        raise NotImplementedError("Subclasses must implement import_clip")

    def create_color_clip(
        self, color: str, duration: float, name: Optional[str] = None
    ) -> str:
        """Create a color clip.

        Args:
            color: Color name or hex code
            duration: Duration in seconds
            name: Optional name for the clip

        Returns:
            str: ID of the created clip
        """
        raise NotImplementedError("Subclasses must implement create_color_clip")

    def create_title_clip(
        self, text: str, duration: float, template: Optional[str] = None
    ) -> str:
        """Create a title clip.

        Args:
            text: Text content
            duration: Duration in seconds
            template: Optional title template name

        Returns:
            str: ID of the created clip
        """
        raise NotImplementedError("Subclasses must implement create_title_clip")

    # Timeline Operations
    def add_clip_to_timeline(
        self, clip_id: str, track: int, position: int, speed: float = 1.0  # in frames
    ) -> str:
        """Add clip to timeline.

        Args:
            clip_id: ID of the clip to add
            track: Track number
            position: Position in frames
            speed: Playback speed multiplier

        Returns:
            str: ID of the timeline clip
        """
        raise NotImplementedError("Subclasses must implement add_clip_to_timeline")

    def add_track(
        self, track_type: Literal["video", "audio"], position: Optional[int] = None
    ) -> int:
        """Add a new track.

        Args:
            track_type: Type of track
            position: Optional position for the new track

        Returns:
            int: Number of the created track
        """
        raise NotImplementedError("Subclasses must implement add_track")

    def split_clip(self, clip_id: str, frame: int) -> Tuple[str, str]:
        """Split a clip at specified frame.

        Args:
            clip_id: ID of the clip to split
            frame: Frame position where to split

        Returns:
            Tuple[str, str]: IDs of the resulting clips (left, right)
        """
        raise NotImplementedError("Subclasses must implement split_clip")

    def resize_clip(
        self,
        clip_id: str,
        in_point: int,  # in frames
        out_point: int,  # in frames
        ripple: bool = False,
    ) -> bool:
        """Resize a clip in the timeline.

        Args:
            clip_id: ID of the clip to resize
            in_point: New in point in frames
            out_point: New out point in frames
            ripple: Whether to ripple edit

        Returns:
            bool: True if clip was resized successfully
        """
        raise NotImplementedError("Subclasses must implement resize_clip")

    # Effects and Transitions
    def add_effect(
        self, clip_id: str, effect_id: str, parameters: Optional[Dict[str, Any]] = None
    ) -> str:
        """Add MLT effect to a clip.

        Args:
            clip_id: ID of the clip
            effect_id: MLT effect identifier
            parameters: Optional effect parameters

        Returns:
            str: ID of the added effect
        """
        raise NotImplementedError("Subclasses must implement add_effect")

    def add_transition(
        self, clip1_id: str, clip2_id: str, transition_id: str, duration: int
    ) -> str:  # duration in frames
        """Add transition between clips.

        Args:
            clip1_id: ID of first clip
            clip2_id: ID of second clip
            transition_id: MLT transition identifier
            duration: Duration in frames

        Returns:
            str: ID of the created transition
        """
        raise NotImplementedError("Subclasses must implement add_transition")

    def add_keyframe(
        self, effect_id: str, parameter: str, frame: int, value: Any
    ) -> bool:
        """Add a keyframe to an effect parameter.

        Args:
            effect_id: ID of the effect
            parameter: Name of the parameter
            frame: Frame position
            value: Parameter value at keyframe

        Returns:
            bool: True if keyframe was added successfully
        """
        raise NotImplementedError("Subclasses must implement add_keyframe")

    # Audio Operations
    def adjust_clip_volume(
        self,
        clip_id: str,
        gain: float,  # in dB
        keyframes: Optional[List[Dict[str, Any]]] = None,
    ) -> bool:
        """Adjust clip volume.

        Args:
            clip_id: ID of the clip
            gain: Volume adjustment in dB
            keyframes: Optional volume keyframes

        Returns:
            bool: True if volume was adjusted successfully
        """
        raise NotImplementedError("Subclasses must implement adjust_clip_volume")

    def normalize_audio(self, clip_id: str, target_db: float = -12.0) -> bool:
        """Normalize clip audio.

        Args:
            clip_id: ID of the clip
            target_db: Target peak level in dB

        Returns:
            bool: True if audio was normalized successfully
        """
        raise NotImplementedError("Subclasses must implement normalize_audio")

    # Rendering
    def render_project(
        self,
        output_path: Union[str, Path],
        render_preset: str,
        range: Optional[Tuple[int, int]] = None,
    ) -> bool:
        """Render the project.

        Args:
            output_path: Path to save the rendered file
            render_preset: Name of the render preset to use
            range: Optional (start, end) frame range to render

        Returns:
            bool: True if render was successful
        """
        raise NotImplementedError("Subclasses must implement render_project")

    def render_preview(self, frame: int, output_path: Union[str, Path]) -> bool:
        """Render a preview frame.

        Args:
            frame: Frame number to render
            output_path: Path to save the preview image

        Returns:
            bool: True if preview was rendered successfully
        """
        raise NotImplementedError("Subclasses must implement render_preview")

    # Project Analysis
    def get_project_fps(self) -> float:
        """Get project framerate.

        Returns:
            float: Frames per second
        """
        raise NotImplementedError("Subclasses must implement get_project_fps")

    def get_clip_properties(self, clip_id: str) -> Dict[str, Any]:
        """Get clip properties.

        Args:
            clip_id: ID of the clip

        Returns:
            Dict containing clip properties
        """
        raise NotImplementedError("Subclasses must implement get_clip_properties")

    def is_running(self) -> bool:
        """Check if the editor process is running.

        Returns:
            bool: True if editor is running, False otherwise
        """
        raise NotImplementedError("Subclasses must implement is_running")
