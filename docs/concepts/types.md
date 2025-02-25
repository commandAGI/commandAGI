# Types

CommandLAB uses a comprehensive type system to define actions, observations, and other data structures.

![Type System](../assets/images/type_system.png)

## Core Types

### Actions

Actions represent operations that can be performed on a computer:

```python
from commandLAB.types import (
    ClickAction,
    TypeAction,
    KeyboardHotkeyAction,
    KeyboardKey,
    MouseButton
)

# Click at coordinates
click_action = ClickAction(
    x=100, 
    y=200, 
    button=MouseButton.LEFT
)

# Type text
type_action = TypeAction(
    text="Hello, CommandLAB!"
)

# Press a keyboard shortcut
hotkey_action = KeyboardHotkeyAction(
    keys=[KeyboardKey.CTRL, KeyboardKey.C]
)
```

### Observations

Observations represent the state of a computer:

```python
from commandLAB.types import (
    ScreenshotObservation,
    MouseStateObservation,
    KeyboardStateObservation
)

# Screenshot
screenshot = ScreenshotObservation(
    screenshot="base64_encoded_image_data"
)

# Mouse state
mouse_state = MouseStateObservation(
    buttons={MouseButton.LEFT: False, MouseButton.RIGHT: False},
    position=(100, 200)
)

# Keyboard state
keyboard_state = KeyboardStateObservation(
    keys={KeyboardKey.SHIFT: True, KeyboardKey.A: False}
)
```

### ComputerAction and ComputerObservation

These are container types that can hold any action or observation:

```python
from commandLAB.types import ComputerAction, ComputerObservation

# An action that could be any type of action
action = ComputerAction(
    click=ClickAction(x=100, y=200),
    # All other action fields are None
)

# An observation that could include any type of observation
observation = ComputerObservation(
    screenshot=screenshot,
    mouse_state=mouse_state,
    keyboard_state=keyboard_state
)
```

## Enums

CommandLAB includes several enums for standardizing values:

### MouseButton

```python
class MouseButton(str, Enum):
    LEFT = "left"
    RIGHT = "right"
    MIDDLE = "middle"
```

### KeyboardKey

```python
class KeyboardKey(str, Enum):
    # Special Keys
    ENTER = "enter"
    TAB = "tab"
    SPACE = "space"
    # ... many more keys
    
    # Alphabet
    A = "a"
    B = "b"
    # ... and so on
```

## Backend Mappings

The type system includes mappings to convert between CommandLAB's standard types and backend-specific types:

```python
# Convert a CommandLAB mouse button to a PyAutoGUI button
pyautogui_button = MouseButton.to_pyautogui(MouseButton.LEFT)  # "left"

# Convert a CommandLAB key to a pynput key
pynput_key = KeyboardKey.to_pynput(KeyboardKey.ENTER)  # pynput.keyboard.Key.enter
```

This allows CommandLAB to provide a consistent interface while supporting multiple backends.

## Why Strong Typing?

CommandLAB uses strong typing for several reasons:

1. **API Clarity**: Makes it clear what data is expected
1. **Error Prevention**: Catches type errors at development time
1. **Documentation**: Types serve as documentation
1. **IDE Support**: Enables autocomplete and type hints
1. **Serialization**: Simplifies conversion to/from JSON

## Using Types in Your Code

When working with CommandLAB, you'll typically use these types to create actions and process observations:

```python
from commandLAB.computers.local_pynput_computer import LocalPynputComputer
from commandLAB.types import ClickAction, TypeAction

computer = LocalPynputComputer()

# Create and execute actions
computer.execute_click(ClickAction(x=100, y=200))
computer.execute_type(TypeAction(text="Hello!"))

# Get and process observations
screenshot = computer.get_screenshot()
mouse_state = computer.get_mouse_state()
```

Understanding the type system is key to effectively using CommandLAB.
