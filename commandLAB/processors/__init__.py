"""
Processors for commandLAB.

This package contains various processors for handling different types of data in commandLAB.
"""

# Import core components
from commandLAB.processors.grid_overlay import GridOverlay

# Import screen parser components if available
try:
    from commandLAB.processors.screen_parser import ScreenParser
except ImportError:
    pass

# Import audio transcription components if available
try:
    from commandLAB.processors.audio_transcription import AudioTranscription
except ImportError:
    pass

# Import text-to-speech components if available
try:
    from commandLAB.processors.tts import TextToSpeech
except ImportError:
    pass

__all__ = [
    "GridOverlay",
    "ScreenParser",
    "AudioTranscription",
    "TextToSpeech",
] 