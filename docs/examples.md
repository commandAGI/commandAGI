# commandAGI Examples

This page provides an overview of the example scripts included in the commandAGI repository. Each example demonstrates different aspects of the framework and can be used as a starting point for your own automation projects.

## Example Status Legend

- ✅ **Works perfectly**: The example runs without issues
- ⚠️ **Works with limitations**: The example works but has some limitations or issues
- ❌ **Not implemented**: The example is a placeholder for future implementation

## Available Examples

### 1. Getting Started

**File**: `examples/1_getting_started.py`

**Description**: Demonstrates how to import the commandAGI library and print its version.

**Status**: ✅ Works perfectly

- Correctly displays version information

**Run with**: `poetry run python examples/1_getting_started.py`

### 2. Basic Concepts

**File**: `examples/2_concepts.py`

**Description**: Demonstrates basic concepts of commandAGI, including creating a computer instance, taking a screenshot, and saving it to a file.

**Status**: ✅ Works perfectly

- Successfully takes a screenshot and saves it to a file

**Run with**: `poetry run python examples/2_concepts.py`

### 3. Advanced Concepts

**File**: `examples/3_advanced_concepts.py`

**Description**: Demonstrates advanced concepts of commandAGI, including mouse movement and clicking, keyboard typing, keyboard hotkeys, and getting mouse and keyboard state.

**Status**: ✅ Works perfectly

- Successfully performs mouse and keyboard actions

**Run with**: `poetry run python examples/3_advanced_concepts.py`

### 4. Docker Integration

**File**: `examples/4_using_docker.py`

**Description**: Demonstrates how to use the Docker provisioner to create and control a Docker container.

**Status**: ⚠️ Works with limitations

- Handles the error gracefully when the Docker image doesn't exist
- Provides helpful information about building the image

**Run with**: `poetry run python examples/4_using_docker.py`

### 5. Kubernetes Integration

**File**: `examples/5_using_kubernetes.py`

**Description**: Demonstrates how to use the Kubernetes provisioner to create and control a Kubernetes pod running the commandAGI daemon.

**Status**: ❌ Not implemented yet

- This is a placeholder for future implementation

**Run with**: `poetry run python examples/5_using_kubernetes.py`

### 6. Scripting Computer Interactions

**File**: `examples/6_scripting_computer_interactions.py`

**Description**: Demonstrates how to use the manual provisioner to script computer interactions. The manual provisioner is the simplest way to get started with commandAGI.

**Status**: ⚠️ Requires manual setup

- Needs the daemon to be running in a separate terminal

**Run with**: `poetry run python examples/6_scripting_computer_interactions.py`

### 7. Automating Computer Interactions

**File**: `examples/7_automating_computer_interactions.py`

**Description**: Demonstrates how to use the grid overlay utility to help with positioning when automating computer interactions.

**Status**: ✅ Works perfectly

- Successfully creates a grid overlay image and demonstrates mouse actions

**Run with**: `poetry run python examples/7_automating_computer_interactions.py`

### 8. Document Editing

**File**: `examples/8_document_editing.py`

**Description**: Demonstrates how to use the screen parser to extract text from a screenshot, which can be useful for document editing and text extraction tasks.

**Status**: ✅ Works perfectly

- Successfully extracts text from a screenshot and saves it to a file

**Run with**: `poetry run python examples/8_document_editing.py`

### 9. Web Automation

**File**: `examples/9_using_the_internet.py`

**Description**: Demonstrates how to use commandAGI for web automation tasks, such as opening a browser, navigating to a website, and interacting with web elements.

**Status**: ⚠️ Works with minor issues

- Successfully opens a browser, navigates to a website, and takes a screenshot
- Encounters an error when closing the browser

**Run with**: `poetry run python examples/9_using_the_internet.py`

### 10. Programming

**File**: `examples/10_programming.py`

**Description**: Demonstrates how to use commandAGI for programming tasks, such as opening a code editor, writing code, and running it.

**Status**: ⚠️ Works with limitations

- Successfully creates a Python script
- Encounters an error when trying to edit the script
- The script itself works correctly when run directly

**Run with**: `poetry run python examples/10_programming.py`

## Running the Examples

To run any of the examples, make sure you have commandAGI installed with the appropriate extras:

```bash
# For basic examples
pip install commandagi[local]

# For Docker examples
pip install commandagi[docker]

# For OCR examples
pip install commandagi[local,pytesseract]
```

Then run the example using Python:

```bash
python examples/1_getting_started.py
```

Or using Poetry:

```bash
poetry run python examples/1_getting_started.py
```

## Troubleshooting

If you encounter issues running the examples:

1. Make sure you have all the required dependencies installed
1. Check that you're running the examples from the root of the commandAGI repository
1. For Docker examples, ensure Docker is installed and running
1. For examples that require manual setup, follow the instructions in the console output
