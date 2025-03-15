# Local Computer Control

This guide explains how to use commandAGI to control your local computer, including mouse and keyboard automation, taking screenshots, and executing system commands.

## Introduction

commandAGI provides several implementations for controlling your local computer:

- `LocalPynputComputer`: Uses the pynput library for precise control
- `LocalPyAutoGUIComputer`: Uses the PyAutoGUI library for cross-platform compatibility

These implementations allow you to:

- Take screenshots
- Control the mouse (move, click, scroll)
- Control the keyboard (press keys, type text)
- Execute system commands

## Installation

To use local computer control, install commandAGI with the local extra:

```bash
pip install "commandagi[local]"
```

This will install the necessary dependencies, including pynput, PyAutoGUI, and mss.

### Platform-Specific Requirements

**Windows**:

- No additional requirements

**macOS**:

- You may need to grant accessibility permissions to your terminal or Python application
- Go to System Preferences > Security & Privacy > Privacy > Accessibility and add your terminal application

**Linux**:

- X11 is required for input control
- Install X11 dependencies: `sudo apt-get install python3-xlib python3-tk python3-dev`

## Basic Usage

### Creating a Computer Instance

```python
from commandAGI.computers.local_pynput_computer import LocalPynputComputer

# Create a computer instance
computer = LocalPynputComputer()

# Always clean up when done
try:
    # Your automation code here
    pass
finally:
    computer.close()
```

### Taking Screenshots

```python
# Take a screenshot
screenshot = computer.get_screenshot()

# The screenshot is returned as a base64-encoded string
print(f"Screenshot size: {len(screenshot.screenshot)} bytes")

# You can convert it to a PIL Image
from commandAGI.utils.image import b64ToImage
image = b64ToImage(screenshot.screenshot)
print(f"Image dimensions: {image.size}")

# Or save it to a file
image.save("screenshot.png")
```

### Mouse Control

```python
from commandAGI.types import (
    ClickAction,
    DoubleClickAction,
    DragAction,
    MouseMoveAction,
    MouseScrollAction,
    MouseButton,
    MouseButtonDownAction,
    MouseButtonUpAction
)

# Move the mouse
computer.move(MouseMoveAction(
    x=100,
    y=100,
    move_duration=0.5  # Duration of the move in seconds
))

# Click
computer.click(ClickAction(
    x=100,
    y=100,
    button=MouseButton.LEFT,
    move_duration=0.5,  # Duration of the move to the position
    press_duration=0.1  # Duration to hold the button down
))

# Double-click
computer.double_click(DoubleClickAction(
    x=100,
    y=100,
    button=MouseButton.LEFT,
    double_click_interval_seconds=0.1  # Interval between clicks
))

# Drag
computer.drag(DragAction(
    start_x=100,
    start_y=100,
    end_x=200,
    end_y=200,
    button=MouseButton.LEFT,
    move_duration=0.5
))

# Scroll
computer.scroll(MouseScrollAction(
    amount=10  # Positive for up, negative for down
))

# Advanced: Manual button control
computer.mouse_down(MouseButtonDownAction(
    button=MouseButton.LEFT
))
computer.mouse_up(MouseButtonUpAction(
    button=MouseButton.LEFT
))
```

### Keyboard Control

```python
from commandAGI.types import (
    TypeAction,
    KeyboardHotkeyAction,
    KeyboardKeyPressAction,
    KeyboardKeyDownAction,
    KeyboardKeyReleaseAction,
    KeyboardKey
)

# Type text
computer.type(TypeAction(
    text="Hello, commandAGI!"
))

# Press a key
computer.keypress(KeyboardKeyPressAction(
    key=KeyboardKey.ENTER,
    duration=0.1  # Duration to hold the key down
))

# Press a keyboard shortcut
computer.hotkey(KeyboardHotkeyAction(
    keys=[KeyboardKey.CTRL, KeyboardKey.C]  # Ctrl+C (copy)
))

# Advanced: Manual key control
computer.keydown(KeyboardKeyDownAction(
    key=KeyboardKey.SHIFT
))
computer.keyup(KeyboardKeyReleaseAction(
    key=KeyboardKey.SHIFT
))
```

### Executing System Commands

```python
from commandAGI.types import CommandAction

# Execute a system command
result = computer.execute_command(CommandAction(
    command="echo Hello, commandAGI!",
    timeout=5  # Timeout in seconds (None for no timeout)
))

if result:
    print("Command executed successfully")
else:
    print("Command failed")
```

## Advanced Usage

### Getting Mouse and Keyboard State

```python
# Get mouse state
mouse_state = computer.get_mouse_state()
print(f"Mouse position: {mouse_state.position}")
print(f"Mouse buttons: {mouse_state.buttons}")

# Get keyboard state
keyboard_state = computer.get_keyboard_state()
print(f"Shift key pressed: {keyboard_state.keys.get(KeyboardKey.SHIFT, False)}")
```

### Using PyAutoGUI Instead of Pynput

```python
from commandAGI.computers.local_pyautogui_computer import LocalPyAutoGUIComputer

# Create a PyAutoGUI computer instance
computer = LocalPyAutoGUIComputer()

# Use the same API as with pynput
computer.click(ClickAction(x=100, y=100))
computer.type(TypeAction(text="Hello, commandAGI!"))
```

### Handling Errors

```python
try:
    computer.click(ClickAction(x=100, y=100))
except Exception as e:
    print(f"Error executing click: {e}")
```

## Common Tasks

### Opening an Application

```python
from commandAGI.types import CommandAction

# Windows
computer.execute_command(CommandAction(command="start notepad"))

# macOS
computer.execute_command(CommandAction(command="open -a TextEdit"))

# Linux
computer.execute_command(CommandAction(command="gedit"))
```

### Taking a Screenshot and Saving It

```python
import time
from datetime import datetime
from commandAGI.utils.image import b64ToImage

# Take a screenshot
screenshot = computer.get_screenshot()

# Convert to PIL Image
image = b64ToImage(screenshot.screenshot)

# Save with timestamp
timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
image.save(f"screenshot_{timestamp}.png")
```

### Automating a Web Browser

```python
import time
from commandAGI.types import (
    CommandAction,
    TypeAction,
    KeyboardKeyPressAction,
    KeyboardKey
)

# Open Chrome
computer.execute_command(CommandAction(command="start chrome"))
time.sleep(2)  # Wait for the browser to open

# Navigate to a website
computer.type(TypeAction(text="https://www.google.com"))
computer.keypress(KeyboardKeyPressAction(key=KeyboardKey.ENTER))
time.sleep(2)  # Wait for the page to load

# Search for something
computer.type(TypeAction(text="commandAGI python automation"))
computer.keypress(KeyboardKeyPressAction(key=KeyboardKey.ENTER))
```

### Automating a Text Editor

```python
import time
from commandAGI.types import (
    CommandAction,
    TypeAction,
    KeyboardHotkeyAction,
    KeyboardKey,
    KeyboardKeyPressAction
)

# Open Notepad
computer.execute_command(CommandAction(command="start notepad"))
time.sleep(1)  # Wait for Notepad to open

# Type some text
computer.type(TypeAction(text="Hello, commandAGI!\n\nThis is an automated test."))

# Save the file
computer.hotkey(KeyboardHotkeyAction(keys=[KeyboardKey.CTRL, KeyboardKey.S]))
time.sleep(1)  # Wait for the save dialog

# Type the filename
computer.type(TypeAction(text="commandAGI2_test.txt"))
computer.keypress(KeyboardKeyPressAction(key=KeyboardKey.ENTER))
```

## Best Practices

### Adding Delays

When automating UI interactions, it's important to add delays to account for application response times:

```python
import time

# Click a button
computer.click(ClickAction(x=100, y=100))
time.sleep(0.5)  # Wait for the click to register

# Type text
computer.type(TypeAction(text="Hello"))
time.sleep(0.2)  # Wait for the text to appear
```

### Error Handling

Always include error handling to make your automation robust:

```python
try:
    # Take a screenshot
    screenshot = computer.get_screenshot()
    
    # Process the screenshot
    # ...
    
except Exception as e:
    print(f"Error: {e}")
    # Handle the error or retry
```

### Resource Cleanup

Always clean up resources when you're done:

```python
computer = LocalPynputComputer()
try:
    # Your automation code here
    pass
finally:
    computer.close()
```

### Cross-Platform Compatibility

For cross-platform compatibility, use platform-specific commands:

```python
import platform

if platform.system() == "Windows":
    computer.execute_command(CommandAction(command="start notepad"))
elif platform.system() == "Darwin":  # macOS
    computer.execute_command(CommandAction(command="open -a TextEdit"))
else:  # Linux
    computer.execute_command(CommandAction(command="gedit"))
```

## Troubleshooting

### Permission Issues

**Problem**: `PermissionError` when trying to control mouse or keyboard

**Solution**:

- Run your script with administrator/root privileges
- On macOS, grant accessibility permissions to your terminal
- On Linux, ensure you have the necessary X11 permissions

### Coordinates Issues

**Problem**: Clicks are not happening at the expected coordinates

**Solution**:

- Check if you have multiple monitors and adjust coordinates accordingly
- Use `get_screenshot()` to verify the screen dimensions
- Add debugging to print the actual mouse position using `get_mouse_state()`

### Timing Issues

**Problem**: Actions are happening too quickly or too slowly

**Solution**:

- Adjust `move_duration` and `press_duration` parameters
- Add `time.sleep()` calls between actions
- Use `get_mouse_state()` and `get_keyboard_state()` to verify the current state

## Next Steps

- Learn about [Remote Computer Control](remote_computer_control.md)
- Explore [Vision-Language Models](vision_language_models.md) for intelligent automation
- Try the [Basic Automation Tutorial](../tutorials/basic_automation.md)
