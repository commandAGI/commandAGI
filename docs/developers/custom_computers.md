# Creating Custom Computers

This guide explains how to create custom computer implementations in commandAGI. Custom computers allow you to extend commandAGI to control new types of systems or to integrate with existing automation frameworks.

## Introduction

The `BaseComputer` class in commandAGI defines a standard interface for controlling computers. By implementing this interface, you can create custom computer implementations that work with the rest of the commandAGI ecosystem.

Some reasons to create a custom computer implementation:

- Integrate with a specialized hardware platform
- Support a new remote control protocol
- Optimize for specific performance requirements
- Add support for new input/output devices
- Integrate with existing automation frameworks

## Prerequisites

Before creating a custom computer implementation, you should:

- Understand the `BaseComputer` interface
- Be familiar with Python and object-oriented programming
- Have a clear use case for your custom implementation

## The BaseComputer Interface

The `BaseComputer` class defines the following key methods:

```python
class BaseComputer(BaseModel):
    def get_screenshot(self) -> ScreenshotObservation:
        """Return a screenshot of the computer"""
        
    def get_mouse_state(self) -> MouseStateObservation:
        """Return the current mouse state"""
        
    def get_keyboard_state(self) -> KeyboardStateObservation:
        """Return the current keyboard state"""
        
    def execute_command(self, action: CommandAction) -> bool:
        """Execute a system command"""
        
    def keydown(self, action: KeyboardKeyDownAction) -> bool:
        """Execute key down for a keyboard key"""
        
    def keyup(self, action: KeyboardKeyReleaseAction) -> bool:
        """Execute key release for a keyboard key"""
        
    def move(self, action: MouseMoveAction) -> bool:
        """Execute moving the mouse"""
        
    def scroll(self, action: MouseScrollAction) -> bool:
        """Execute mouse scroll"""
        
    def mouse_down(self, action: MouseButtonDownAction) -> bool:
        """Execute mouse button down"""
        
    def mouse_up(self, action: MouseButtonUpAction) -> bool:
        """Execute mouse button up"""
```

The base class also provides default implementations for composite actions like `click`, `type`, and `hotkey`, which are built on top of the primitive actions.

## Step 1: Create a New Computer Class

Start by creating a new class that inherits from `BaseComputer`:

```python
from commandAGI.computers.base_computer import BaseComputer
from commandAGI.types import (
    ScreenshotObservation,
    MouseStateObservation,
    KeyboardStateObservation,
    CommandAction,
    KeyboardKeyDownAction,
    KeyboardKeyReleaseAction,
    MouseMoveAction,
    MouseScrollAction,
    MouseButtonDownAction,
    MouseButtonUpAction,
)

class MyCustomComputer(BaseComputer):
    def __init__(self, custom_param: str = "default"):
        super().__init__()
        self.custom_param = custom_param
        # Initialize your custom resources here
        
    def close(self):
        """Clean up resources when the object is destroyed"""
        # Clean up your custom resources here
        pass
```

## Step 2: Implement Required Methods

Next, implement the required methods from the `BaseComputer` interface:

```python
class MyCustomComputer(BaseComputer):
    # ... __init__ and other methods ...
    
    def get_screenshot(self) -> ScreenshotObservation:
        """Return a screenshot of the computer"""
        # Implement screenshot capture logic
        screenshot_data = "base64_encoded_screenshot_data"  # Replace with actual implementation
        return ScreenshotObservation(screenshot=screenshot_data)
    
    def get_mouse_state(self) -> MouseStateObservation:
        """Return the current mouse state"""
        # Implement mouse state retrieval logic
        buttons = {MouseButton.LEFT: False, MouseButton.RIGHT: False, MouseButton.MIDDLE: False}
        position = (0, 0)  # Replace with actual implementation
        return MouseStateObservation(buttons=buttons, position=position)
    
    def get_keyboard_state(self) -> KeyboardStateObservation:
        """Return the current keyboard state"""
        # Implement keyboard state retrieval logic
        keys = {key: False for key in KeyboardKey}  # Replace with actual implementation
        return KeyboardStateObservation(keys=keys)
    
    def execute_command(self, action: CommandAction) -> bool:
        """Execute a system command"""
        # Implement command execution logic
        command = action.command
        timeout = action.timeout
        # Execute the command and return success/failure
        return True  # Replace with actual implementation
    
    def keydown(self, action: KeyboardKeyDownAction) -> bool:
        """Execute key down for a keyboard key"""
        # Implement key down logic
        key = action.key
        # Press the key and return success/failure
        return True  # Replace with actual implementation
    
    def keyup(self, action: KeyboardKeyReleaseAction) -> bool:
        """Execute key release for a keyboard key"""
        # Implement key release logic
        key = action.key
        # Release the key and return success/failure
        return True  # Replace with actual implementation
    
    def move(self, action: MouseMoveAction) -> bool:
        """Execute moving the mouse"""
        # Implement mouse move logic
        x = action.x
        y = action.y
        move_duration = action.move_duration
        # Move the mouse and return success/failure
        return True  # Replace with actual implementation
    
    def scroll(self, action: MouseScrollAction) -> bool:
        """Execute mouse scroll"""
        # Implement mouse scroll logic
        amount = action.amount
        # Scroll the mouse and return success/failure
        return True  # Replace with actual implementation
    
    def mouse_down(self, action: MouseButtonDownAction) -> bool:
        """Execute mouse button down"""
        # Implement mouse button down logic
        button = action.button
        # Press the mouse button and return success/failure
        return True  # Replace with actual implementation
    
    def mouse_up(self, action: MouseButtonUpAction) -> bool:
        """Execute mouse button up"""
        # Implement mouse button up logic
        button = action.button
        # Release the mouse button and return success/failure
        return True  # Replace with actual implementation
```

## Step 3: Implement Custom Methods (Optional)

You can add custom methods specific to your implementation:

```python
class MyCustomComputer(BaseComputer):
    # ... standard methods ...
    
    def custom_method(self, param: str) -> bool:
        """A custom method specific to this implementation"""
        # Custom implementation
        return True
```

## Step 4: Override Composite Methods (Optional)

If needed, you can override the default implementations of composite methods:

```python
class MyCustomComputer(BaseComputer):
    # ... standard methods ...
    
    def click(self, action: ClickAction) -> bool:
        """Custom implementation of click action"""
        # Custom click implementation that might be more efficient
        # than the default implementation that uses move, button down, and button up
        return True
```

## Example: WebDriverComputer

Here's an example of a custom computer implementation that uses Selenium WebDriver to control a web browser:

```python
from selenium import webdriver
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.keys import Keys
import base64
import time

from commandAGI.computers.base_computer import BaseComputer
from commandAGI.types import (
    ScreenshotObservation,
    MouseStateObservation,
    KeyboardStateObservation,
    CommandAction,
    KeyboardKeyDownAction,
    KeyboardKeyReleaseAction,
    MouseMoveAction,
    MouseScrollAction,
    MouseButtonDownAction,
    MouseButtonUpAction,
    MouseButton,
    KeyboardKey,
)

class WebDriverComputer(BaseComputer):
    def __init__(self, browser: str = "chrome", headless: bool = False):
        super().__init__()
        
        # Initialize WebDriver
        if browser.lower() == "chrome":
            options = webdriver.ChromeOptions()
            if headless:
                options.add_argument("--headless")
            self.driver = webdriver.Chrome(options=options)
        elif browser.lower() == "firefox":
            options = webdriver.FirefoxOptions()
            if headless:
                options.add_argument("--headless")
            self.driver = webdriver.Firefox(options=options)
        else:
            raise ValueError(f"Unsupported browser: {browser}")
        
        # Initialize ActionChains for mouse and keyboard actions
        self.actions = ActionChains(self.driver)
        
        # Set initial window size
        self.driver.set_window_size(1280, 800)
    
    def close(self):
        """Clean up resources"""
        if hasattr(self, 'driver'):
            self.driver.quit()
    
    def get_screenshot(self) -> ScreenshotObservation:
        """Take a screenshot using WebDriver"""
        screenshot = self.driver.get_screenshot_as_base64()
        return ScreenshotObservation(screenshot=screenshot)
    
    def get_mouse_state(self) -> MouseStateObservation:
        """WebDriver doesn't provide mouse state, so return a default value"""
        # This is a limitation of WebDriver
        buttons = {MouseButton.LEFT: False, MouseButton.RIGHT: False, MouseButton.MIDDLE: False}
        position = (0, 0)
        return MouseStateObservation(buttons=buttons, position=position)
    
    def get_keyboard_state(self) -> KeyboardStateObservation:
        """WebDriver doesn't provide keyboard state, so return a default value"""
        # This is a limitation of WebDriver
        keys = {key: False for key in KeyboardKey}
        return KeyboardStateObservation(keys=keys)
    
    def execute_command(self, action: CommandAction) -> bool:
        """Execute a JavaScript command in the browser"""
        try:
            self.driver.execute_script(action.command)
            return True
        except Exception as e:
            print(f"Error executing command: {e}")
            return False
    
    def keydown(self, action: KeyboardKeyDownAction) -> bool:
        """Press a key down using ActionChains"""
        try:
            selenium_key = self._convert_to_selenium_key(action.key)
            self.actions.key_down(selenium_key).perform()
            return True
        except Exception as e:
            print(f"Error executing key down: {e}")
            return False
    
    def keyup(self, action: KeyboardKeyReleaseAction) -> bool:
        """Release a key using ActionChains"""
        try:
            selenium_key = self._convert_to_selenium_key(action.key)
            self.actions.key_up(selenium_key).perform()
            return True
        except Exception as e:
            print(f"Error executing key release: {e}")
            return False
    
    def move(self, action: MouseMoveAction) -> bool:
        """Move the mouse using ActionChains"""
        try:
            # Find an element at the target position or use move_by_offset
            self.actions.move_by_offset(action.x, action.y).perform()
            return True
        except Exception as e:
            print(f"Error executing mouse move: {e}")
            return False
    
    def scroll(self, action: MouseScrollAction) -> bool:
        """Scroll using JavaScript"""
        try:
            self.driver.execute_script(f"window.scrollBy(0, {action.amount});")
            return True
        except Exception as e:
            print(f"Error executing mouse scroll: {e}")
            return False
    
    def mouse_down(self, action: MouseButtonDownAction) -> bool:
        """Press a mouse button using ActionChains"""
        try:
            if action.button == MouseButton.LEFT:
                self.actions.click_and_hold().perform()
            elif action.button == MouseButton.RIGHT:
                self.actions.context_click().perform()
            return True
        except Exception as e:
            print(f"Error executing mouse button down: {e}")
            return False
    
    def mouse_up(self, action: MouseButtonUpAction) -> bool:
        """Release a mouse button using ActionChains"""
        try:
            if action.button == MouseButton.LEFT:
                self.actions.release().perform()
            return True
        except Exception as e:
            print(f"Error executing mouse button up: {e}")
            return False
    
    def _convert_to_selenium_key(self, key: KeyboardKey):
        """Convert commandAGI key to Selenium key"""
        key_mapping = {
            KeyboardKey.ENTER: Keys.ENTER,
            KeyboardKey.TAB: Keys.TAB,
            KeyboardKey.SPACE: Keys.SPACE,
            KeyboardKey.BACKSPACE: Keys.BACKSPACE,
            KeyboardKey.ESCAPE: Keys.ESCAPE,
            KeyboardKey.UP: Keys.UP,
            KeyboardKey.DOWN: Keys.DOWN,
            KeyboardKey.LEFT: Keys.LEFT,
            KeyboardKey.RIGHT: Keys.RIGHT,
            KeyboardKey.SHIFT: Keys.SHIFT,
            KeyboardKey.CTRL: Keys.CONTROL,
            KeyboardKey.ALT: Keys.ALT,
            # Add more mappings as needed
        }
        
        if key in key_mapping:
            return key_mapping[key]
        else:
            # For regular keys, just return the key value
            return key.value
    
    # Custom methods specific to WebDriver
    
    def navigate_to(self, url: str) -> bool:
        """Navigate to a URL"""
        try:
            self.driver.get(url)
            return True
        except Exception as e:
            print(f"Error navigating to {url}: {e}")
            return False
    
    def find_and_click(self, selector: str) -> bool:
        """Find an element by CSS selector and click it"""
        try:
            element = self.driver.find_element_by_css_selector(selector)
            element.click()
            return True
        except Exception as e:
            print(f"Error finding and clicking {selector}: {e}")
            return False
```

## Best Practices

### Error Handling

Always include robust error handling in your implementation:

```python
def execute_command(self, action: CommandAction) -> bool:
    try:
        # Implementation
        return True
    except Exception as e:
        print(f"Error executing command: {e}")
        return False
```

### Resource Management

Properly manage resources in the `__init__` and `close` methods:

```python
def __init__(self):
    super().__init__()
    # Acquire resources
    
def close(self):
    try:
        # Release resources
        pass
    except Exception as e:
        print(f"Error closing resources: {e}")
```

### Documentation

Document your implementation thoroughly:

```python
class MyCustomComputer(BaseComputer):
    """
    A custom computer implementation that controls XYZ system.
    
    This implementation uses the ABC library to interact with XYZ hardware.
    It supports all standard commandAGI actions and adds custom methods
    for XYZ-specific functionality.
    
    Args:
        param1: Description of param1
        param2: Description of param2
    """
```

### Testing

Create comprehensive tests for your implementation:

```python
def test_my_custom_computer():
    computer = MyCustomComputer()
    try:
        # Test screenshot
        screenshot = computer.get_screenshot()
        assert screenshot is not None
        
        # Test mouse move
        result = computer.move(MouseMoveAction(x=100, y=100))
        assert result is True
        
        # Test click
        result = computer.click(ClickAction(x=100, y=100))
        assert result is True
        
        # Test type
        result = computer.type(TypeAction(text="Hello, World!"))
        assert result is True
    finally:
        computer.close()
```

## Integration with commandAGI

Once you've created your custom computer implementation, you can use it with the rest of the commandAGI ecosystem:

```python
from my_module import MyCustomComputer
from commandAGI.types import ClickAction, TypeAction

# Create an instance of your custom computer
computer = MyCustomComputer(custom_param="value")

# Use it like any other computer
computer.click(ClickAction(x=100, y=100))
computer.type(TypeAction(text="Hello, commandAGI!"))

# Use it with the gym framework
from commandAGI.gym.environments.computer_env import ComputerEnv, ComputerEnvConfig

# Create an environment with your custom computer
env = ComputerEnv(ComputerEnvConfig(
    computer_cls_name="MyCustomComputer",
    computer_cls_kwargs={"custom_param": "value"}
))
```

## Troubleshooting

### Common Issues

1. **Method Not Implemented**: If you forget to implement a required method, you'll get a `NotImplementedError`.

   **Solution**: Implement all required methods from the `BaseComputer` interface.

1. **Type Errors**: If your method returns the wrong type, you'll get a type error.

   **Solution**: Make sure your methods return the correct types as specified in the interface.

1. **Resource Leaks**: If you don't properly clean up resources, you may experience resource leaks.

   **Solution**: Implement the `close` method to clean up all resources.

### Debugging Tips

1. Add logging to your implementation:

```python
import logging

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

def move(self, action: MouseMoveAction) -> bool:
    logger.debug(f"Moving mouse to ({action.x}, {action.y})")
    # Implementation
```

2. Use a debugger to step through your code:

```python
import pdb

def execute_command(self, action: CommandAction) -> bool:
    pdb.set_trace()  # Start the debugger
    # Implementation
```

## Next Steps

- Learn about [Creating Custom Provisioners](custom_provisioners.md)
- Explore [Creating Custom Agents](custom_agents.md)
- Contribute your implementation to the commandAGI project
