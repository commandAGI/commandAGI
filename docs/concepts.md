# Concepts

## Computers

Computers are the core abstraction in commandLAB that provide a unified interface for interacting with different computing environments. They handle:

- Screen capture and observation (screenshot)
- Mouse input and state tracking (movement, clicks, scrolling, dragging)
- Keyboard input and state tracking (key presses, hotkeys, typing)
- Command execution (shell commands, timeouts) ([(Coming soon)](https://github.com/commandAGI/commandLAB/issues/5))
- Window management (focus, minimize, maximize) ([(Coming soon)](https://github.com/commandAGI/commandLAB/issues/5))
- Process management (start, stop, monitor) ([(Coming soon)](https://github.com/commandAGI/commandLAB/issues/5))
- Clipboard operations (copy, paste) ([(Coming soon)](https://github.com/commandAGI/commandLAB/issues/5))
- File system operations (read, write, delete) ([(Coming soon)](https://github.com/commandAGI/commandLAB/issues/5))
- Microphone input ([(Coming soon)](https://github.com/commandAGI/commandLAB/issues/5))
- Speaker output ([(Coming soon)](https://github.com/commandAGI/commandLAB/issues/5))

Available computer implementations:

### Base Computer

- {!BaseComputer!}: Abstract base class defining the computer interface

### Local Computers

- {!LocalPyAutoGUIComputer!}: Uses PyAutoGUI for local machine control
- {!LocalPynputComputer!}: Uses Pynput for local machine control with enhanced state tracking

### VNC Computers

- {!VNCComputer!}: Basic VNC implementation for remote machine control

### Docker-based Computers

- {!BaseDockerComputer!}: Base implementation for Docker containers
- {!VNCDockerComputer!}: Docker container with VNC capabilities
- {!LXDEVNCDockerComputer!}: Docker container with LXDE desktop environment and VNC

### Kubernetes-based Computers

- {!BaseKubernetesComputer!}: Base implementation for Kubernetes pods
- {!VNCKubernetesComputer!}: Kubernetes pod with VNC capabilities
- {!LXDEVNCKubernetesComputer!}: Kubernetes pod with LXDE desktop environment and VNC

### Third-party Integration

- {!E2BDesktopComputer!}: Integration with E2B Desktop Sandbox

## Processors

Processors are utility functions that help process and transform data for agents interacting with computers. They provide capabilities like:

- Screen parsing and text detection
- Grid overlay generation for precise location targeting 
- Audio transcription (coming soon)
- Text-to-speech synthesis (coming soon)

### Screen Parser

Screen parsers analyze screenshots to detect and locate text and UI elements. They return structured information about screen contents.

Available implementations:

- **TesseractScreenParser**: Uses the open-source Tesseract OCR engine
  - Lightweight and runs locally
  - Best for simple text detection scenarios
  - Requires the `pytesseract` package (`pip install commandLAB[pytesseract]`)

- **ScreenParseAIParser**: Uses the ScreenParse.ai API
  - More accurate text detection and element recognition
  - Handles complex UI layouts and different text styles
  - Requires an API key from ScreenParse.ai
  - Returns normalized coordinates that are converted to pixel values

Both parsers return:

- Text content found on screen
- Bounding boxes for each detected element
- Original screenshot data preserved

Example usage:

```python
from commandLAB.processors.screen_parser import parse_screenshot_tesseract

# Parse a screenshot
parsed = parse_screenshot_tesseract(screenshot_b64)
for element in parsed.elements:
    print(f"Found text '{element.text}' at {element.bounding_box}")
```

### Grid Overlay

A utility function that overlays a coordinate grid on top of screenshots to help agents specify precise locations. This technique was pioneered by Anthropic to enable Claude to precisely locate and interact with objects on the screen.

Example usage:

```python
from commandLAB.processors.grid_overlay import overlay_grid

# Add grid to screenshot
gridded_image = overlay_grid(screenshot, grid_px_size=100)
```

## Other utilities
