# Basic Automation with commandAGI2

This tutorial will guide you through the basics of automating computer interactions using commandAGI2.

## Prerequisites

- commandAGI2 installed (see [Installation](../installation.md))
- Basic understanding of Python

## Getting Started

In this tutorial, we'll create a simple automation script that performs basic tasks on your computer.

### Step 1: Import the necessary modules

```python
from commandAGI2 import LocalPynputComputer
```

### Step 2: Create a computer instance

```python
computer = LocalPynputComputer()
```

### Step 3: Perform basic interactions

```python
# Take a screenshot
screenshot = computer.screenshot()

# Move the mouse
computer.move_mouse(x=100, y=100)

# Click
computer.click()

# Type text
computer.type_text("Hello, world!")
```

## Next Steps

After completing this tutorial, you can explore more advanced features:

- [Using Provisioners](../guides/provisioners.md)
- [Cloud Containers](../guides/cloud_containers.md)
