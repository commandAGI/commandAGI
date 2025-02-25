# Basic Automation with commandLAB

This tutorial will guide you through the basics of automating computer interactions using commandLAB.

## Prerequisites

- commandLAB installed (see [Installation](../installation.md))
- Basic understanding of Python

## Getting Started

In this tutorial, we'll create a simple automation script that performs basic tasks on your computer.

### Step 1: Import the necessary modules

```python
from commandLAB import LocalPynputComputer
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
