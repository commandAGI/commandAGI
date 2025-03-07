# Basic Automation Tutorial

In this tutorial, we'll create a simple automation script using commandAGI to open a text editor, type some text, and save a file.

## Prerequisites

- commandAGI installed with local backend: `pip install commandagi[local]`
- A text editor (like Notepad on Windows or TextEdit on macOS)

## Step 1: Import Required Modules

```python
from commandAGI.computers.local_pynput_computer import LocalPynputComputer
from commandAGI.types import (
    CommandAction,
    TypeAction,
    ClickAction,
    KeyboardHotkeyAction,
    KeyboardKey,
    KeyboardKeyPressAction
)
import os
import time
```

## Step 2: Create a Computer Instance

```python
# Create a computer instance
computer = LocalPynputComputer()

# Give yourself time to switch to the right window
print("Starting in 3 seconds...")
time.sleep(3)
```

## Step 3: Open the Text Editor

```python
# Open text editor (Notepad on Windows, TextEdit on macOS)
if computer.execute_command(CommandAction(command="notepad" if os.name == "nt" else "open -a TextEdit")):
    print("Opened text editor")
    # Wait for it to open
    time.sleep(2)
else:
    print("Failed to open text editor")
    exit(1)
```

## Step 4: Type Some Text

```python
# Type some text
computer.execute_type(TypeAction(text="Hello from commandAGI!\n\nThis file was created automatically."))
print("Typed text")
```

## Step 5: Save the File

```python
# Press Ctrl+S to save
computer.execute_keyboard_hotkey(KeyboardHotkeyAction(keys=[KeyboardKey.CTRL, KeyboardKey.S]))
print("Pressed Ctrl+S")
time.sleep(1)

# Type the filename
computer.execute_type(TypeAction(text="commandAGI2_example.txt"))
print("Entered filename")
time.sleep(1)

# Press Enter to confirm
computer.execute_keyboard_key_press(KeyboardKeyPressAction(key=KeyboardKey.ENTER))
print("Saved file")
time.sleep(1)
```

## Step 6: Close the Editor

```python
# Press Alt+F4 to close
computer.execute_keyboard_hotkey(KeyboardHotkeyAction(keys=[KeyboardKey.ALT, KeyboardKey.F4]))
print("Closed editor")
```

## Complete Script

Here's the complete script:

```python
import os
import time
from commandAGI.computers.local_pynput_computer import LocalPynputComputer
from commandAGI.types import (
    CommandAction,
    TypeAction,
    KeyboardHotkeyAction,
    KeyboardKey,
    KeyboardKeyPressAction
)

# Create a computer instance
computer = LocalPynputComputer()

# Give yourself time to switch to the right window
print("Starting in 3 seconds...")
time.sleep(3)

# Open text editor
if computer.execute_command(CommandAction(command="notepad" if os.name == "nt" else "open -a TextEdit")):
    print("Opened text editor")
    # Wait for it to open
    time.sleep(2)
else:
    print("Failed to open text editor")
    exit(1)

# Type some text
computer.execute_type(TypeAction(text="Hello from commandAGI!\n\nThis file was created automatically."))
print("Typed text")

# Press Ctrl+S to save
computer.execute_keyboard_hotkey(KeyboardHotkeyAction(keys=[KeyboardKey.CTRL, KeyboardKey.S]))
print("Pressed Ctrl+S")
time.sleep(1)

# Type the filename
computer.execute_type(TypeAction(text="commandAGI2_example.txt"))
print("Entered filename")
time.sleep(1)

# Press Enter to confirm
computer.execute_keyboard_key_press(KeyboardKeyPressAction(key=KeyboardKey.ENTER))
print("Saved file")
time.sleep(1)

# Press Alt+F4 to close
computer.execute_keyboard_hotkey(KeyboardHotkeyAction(keys=[KeyboardKey.ALT, KeyboardKey.F4]))
print("Closed editor")
```

## Next Steps

Now that you've created a basic automation script, you can:

1. Modify it to work with different applications
2. Add error handling for more robustness
3. Create more complex automation sequences
4. Try using different computer implementations (e.g., Docker or cloud-based)

Check out the [Advanced Automation Tutorial](advanced_automation.md) for more complex examples.
</rewritten_file>
