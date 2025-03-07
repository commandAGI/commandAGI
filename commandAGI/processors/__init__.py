"""
Processors for commandAGI.

This package contains various processors for handling different types of data in commandAGI.
"""

# Import core components
from commandAGI.processors.grid_overlay import GridOverlay

# Import screen parser components if available
try:
    from commandAGI.processors.screen_parser import ScreenParser
except ImportError:
    pass

# Import audio transcription components if available
try:
    from commandAGI.processors.audio_transcription import AudioTranscription
except ImportError:
    pass

# Import text-to-speech components if available
try:
    from commandAGI.processors.tts import TextToSpeech
except ImportError:
    pass

__all__ = [
    "GridOverlay",
    "ScreenParser",
    "AudioTranscription",
    "TextToSpeech",
]
