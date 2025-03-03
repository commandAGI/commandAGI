"""
Processors for commandAGI2.

This package contains various processors for handling different types of data in commandAGI2.
"""

# Import core components
from commandAGI2.processors.grid_overlay import GridOverlay

# Import screen parser components if available
try:
    from commandAGI2.processors.screen_parser import ScreenParser
except ImportError:
    pass

# Import audio transcription components if available
try:
    from commandAGI2.processors.audio_transcription import AudioTranscription
except ImportError:
    pass

# Import text-to-speech components if available
try:
    from commandAGI2.processors.tts import TextToSpeech
except ImportError:
    pass

__all__ = [
    "GridOverlay",
    "ScreenParser",
    "AudioTranscription",
    "TextToSpeech",
]
