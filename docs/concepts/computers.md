# Computers

In CommandLAB, a **Computer** is an object that provides methods to control a computer system - whether it's your local machine, a remote server, or a virtual environment.

![Computer Architecture](../assets/images/computer_architecture.png)

## The BaseComputer Interface

All computer implementations inherit from the `BaseComputer` class, which defines a standard interface:

```python
class BaseComputer:
    def get_screenshot(self) -> ScreenshotObservation:
        """Return a screenshot of the computer"""
        
    def get_mouse_state(self) -> MouseStateObservation:
        """Return the current mouse state"""
        
    def get_keyboard_state(self) -> KeyboardStateObservation:
        """Return the current keyboard state"""
        
    def execute_command(self, action: CommandAction) -> bool:
        """Execute a system command"""
        
    def execute_keyboard_key_press(self, action: KeyboardKeyPressAction) -> bool:
        """Press a keyboard key"""
        
    # ... and many more methods for mouse/keyboard control
```

This unified interface means you can write code that works with any computer implementation.

## Available Computer Implementations

CommandLAB includes several computer implementations:

### LocalPynputComputer

Uses the `pynput` library to control your local computer:

```python
from commandLAB.computers.local_pynput_computer import LocalPynputComputer

computer = LocalPynputComputer()
```

### LocalPyAutoGUIComputer

Uses the `pyautogui` library for local control:

```python
from commandLAB.computers.local_pyautogui_computer import LocalPyAutoGUIComputer

computer = LocalPyAutoGUIComputer()
```

### E2BDesktopComputer

Uses the E2B Desktop Sandbox for secure interactions:

```python
from commandLAB.computers.e2b_desktop_computer import E2BDesktopComputer

computer = E2BDesktopComputer()
```

### DaemonClientComputer

Connects to a remote daemon for computer control:

```python
from commandLAB.computers.daemon_client_computer import DaemonClientComputer

computer = DaemonClientComputer(
    daemon_base_url="http://remote-computer",
    daemon_port=8000
)
```

## Why Multiple Implementations?

Different computer implementations serve different needs:

- **Local control** is simple and direct but only works on your machine
- **Remote control** via daemon allows controlling computers over a network
- **Sandboxed environments** provide isolation for security
- **Cloud deployments** enable scaling and distribution

## Creating Your Own Computer Implementation

You can create your own computer implementation by subclassing `BaseComputer`:

```python
from commandLAB.computers.base_computer import BaseComputer
from commandLAB.types import ScreenshotObservation, CommandAction

class MyCustomComputer(BaseComputer):
    def get_screenshot(self) -> ScreenshotObservation:
        # Your implementation here
        
    def execute_command(self, action: CommandAction) -> bool:
        # Your implementation here
        
    # Implement other required methods...
```

This allows you to integrate CommandLAB with any system that can be controlled programmatically.