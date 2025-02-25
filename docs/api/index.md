# CommandLAB API Reference

This page contains the complete API reference for CommandLAB.

## Table of Contents

  - [Cli](#commandlab-cli)
    - [Base Computer](#commandlab-computers-base_computer)
    - [Daemon Client Computer](#commandlab-computers-daemon_client_computer)
    - [E2B Desktop Computer](#commandlab-computers-e2b_desktop_computer)
    - [Local Pyautogui Computer](#commandlab-computers-local_pyautogui_computer)
    - [Local Pynput Computer](#commandlab-computers-local_pynput_computer)
      - [Aws Provisioner](#commandlab-computers-provisioners-aws_provisioner)
      - [Azure Provisioner](#commandlab-computers-provisioners-azure_provisioner)
      - [Base Provisioner](#commandlab-computers-provisioners-base_provisioner)
      - [Docker Provisioner](#commandlab-computers-provisioners-docker_provisioner)
      - [Gcp Provisioner](#commandlab-computers-provisioners-gcp_provisioner)
      - [Kubernetes Provisioner](#commandlab-computers-provisioners-kubernetes_provisioner)
      - [Manual Provisioner](#commandlab-computers-provisioners-manual_provisioner)
      - [Vagrant Provisioner](#commandlab-computers-provisioners-vagrant_provisioner)
      - [Virtualbox Provisioner](#commandlab-computers-provisioners-virtualbox_provisioner)
      - [Vmware Provisioner](#commandlab-computers-provisioners-vmware_provisioner)
    - [Cli](#commandlab-daemon-cli)
    - [Client](#commandlab-daemon-client)
    - [Server](#commandlab-daemon-server)
    - [Build Images](#commandlab-dev-build_images)
    - [Dev Cli](#commandlab-dev-dev_cli)
    - [Update Daemon Client](#commandlab-dev-update_daemon_client)
      - [Llms](#commandlab-gym-_utils-llms)
      - [Base Agent](#commandlab-gym-agents-base_agent)
      - [Naive Vision Language Computer Agent](#commandlab-gym-agents-naive_vision_language_computer_agent)
      - [React Vision Language Computer Agent](#commandlab-gym-agents-react_vision_language_computer_agent)
    - [Drivers](#commandlab-gym-drivers)
      - [Base Env](#commandlab-gym-environments-base_env)
      - [Computer Env](#commandlab-gym-environments-computer_env)
      - [Multimodal Env](#commandlab-gym-environments-multimodal_env)
        - [Grid Overlay Wrapper](#commandlab-gym-environments-wrappers-grid_overlay_wrapper)
        - [Gymnasium](#commandlab-gym-environments-wrappers-gymnasium)
        - [Screen Parser Wrapper](#commandlab-gym-environments-wrappers-screen_parser_wrapper)
      - [Llm Based Evals](#commandlab-gym-evals-llm_based_evals)
    - [Schema](#commandlab-gym-schema)
      - [Base](#commandlab-gym-tasks-base)
      - [Computer Task](#commandlab-gym-tasks-computer_task)
    - [Trainer](#commandlab-gym-trainer)
      - [Whisper](#commandlab-processors-audio_transcription-whisper)
    - [Grid Overlay](#commandlab-processors-grid_overlay)
      - [Pytesseract Screen Parser](#commandlab-processors-screen_parser-pytesseract_screen_parser)
      - [Screenparse Ai Screen Parser](#commandlab-processors-screen_parser-screenparse_ai_screen_parser)
      - [Types](#commandlab-processors-screen_parser-types)
      - [Openai](#commandlab-processors-tts-openai)
      - [Some Local Model](#commandlab-processors-tts-some_local_model)
  - [Types](#commandlab-types)
    - [Image](#commandlab-utils-image)
    - [Viewer](#commandlab-utils-viewer)
  - [Version](#commandlab-version)

---

## Cli

**Module Path:** `commandLAB.cli`

CommandLAB CLI

A command-line interface for interacting with CommandLAB functionality.

Subcommands:
  run-example     Run one of the example scripts
  run-gym         Run a gym environment with a specified agent
  screenshot      Take a screenshot using a specified computer
  daemon          Start a daemon server for remote control
  grid-overlay    Create a grid overlay on a screenshot to help with positioning
  ocr             Extract text from a screenshot using OCR
  version         Display version information

---

## Base Computer

**Module Path:** `commandLAB.computers.base_computer`

Return a ScreenshotObservation containing the screenshot encoded as a base64 string.

---

## Daemon Client Computer

**Module Path:** `commandLAB.computers.daemon_client_computer`

Return the appropriate provisioner class based on the provisioning method

---

## E2B Desktop Computer

**Module Path:** `commandLAB.computers.e2b_desktop_computer`

Environment that uses E2B Desktop Sandbox for secure computer interactions

---

## Local Pyautogui Computer

**Module Path:** `commandLAB.computers.local_pyautogui_computer`

Reset environment and return initial observation

---

## Local Pynput Computer

**Module Path:** `commandLAB.computers.local_pynput_computer`

Reset environment, initialize pynput listener threads, and return the initial observation.

---

## Aws Provisioner

**Module Path:** `commandLAB.computers.provisioners.aws_provisioner`

#!/bin/bash
                        pip install commandlab[local,daemon]
                        python -m commandlab.daemon.daemon --port {self.port} --backend pynput

---

## Azure Provisioner

**Module Path:** `commandLAB.computers.provisioners.azure_provisioner`

pip install commandlab[local,daemon]
                                python -m commandlab.daemon.daemon --port {self.port} --backend pynput

---

## Base Provisioner

**Module Path:** `commandLAB.computers.provisioners.base_provisioner`

Setup the daemon with the specific provisioning method

---

## Docker Provisioner

**Module Path:** `commandLAB.computers.provisioners.docker_provisioner`

Setup local Docker container

---

## Gcp Provisioner

**Module Path:** `commandLAB.computers.provisioners.gcp_provisioner`

Setup GCP Compute Engine instance

---

## Kubernetes Provisioner

**Module Path:** `commandLAB.computers.provisioners.kubernetes_provisioner`

Create Kubernetes deployment and service

---

## Manual Provisioner

**Module Path:** `commandLAB.computers.provisioners.manual_provisioner`

---

## Vagrant Provisioner

**Module Path:** `commandLAB.computers.provisioners.vagrant_provisioner`

Setup a Vagrant VM and start the daemon.

---

## Virtualbox Provisioner

**Module Path:** `commandLAB.computers.provisioners.virtualbox_provisioner`

Setup a VirtualBox VM and start the daemon.

---

## Vmware Provisioner

**Module Path:** `commandLAB.computers.provisioners.vmware_provisioner`

Setup a VMware VM and start the daemon.

---

## Cli

**Module Path:** `commandLAB.daemon.cli`

---

## Client

**Module Path:** `commandLAB.daemon.client`

---

## Server

**Module Path:** `commandLAB.daemon.server`

---

## Build Images

**Module Path:** `commandLAB.dev.build_images`

Get base directory paths for resources

---

## Dev Cli

**Module Path:** `commandLAB.dev.dev_cli`

Update the daemon client from the OpenAPI spec

---

## Update Daemon Client

**Module Path:** `commandLAB.dev.update_daemon_client`

---

## Llms

**Module Path:** `commandLAB.gym._utils.llms`

Instantiate and return a chat model based on the specified model provider.

    Args:
        model_provider (str): One of "openai", "custom_openai_compat", "anthropic", or "huggingface".
        options (dict, optional): Additional keyword arguments for the chat model.

    Returns:
        An instance of the appropriate chat model.

    Raises:
        ValueError: If a required API key for a provider isn't set or an unsupported provider is specified.

---

## Base Agent

**Module Path:** `commandLAB.gym.agents.base_agent`

Base class for agents

---

## Naive Vision Language Computer Agent

**Module Path:** `commandLAB.gym.agents.naive_vision_language_computer_agent`

List of action functions that can be called to create ComputerAction objects.

---

## React Vision Language Computer Agent

**Module Path:** `commandLAB.gym.agents.react_vision_language_computer_agent`

Initialize the React agent with a Hugging Face model.

        Args:
            model: Name of the Hugging Face model to use
            device: Device to run the model on (e.g., 'cuda', 'cpu')

---

## Drivers

**Module Path:** `commandLAB.gym.drivers`

Abstract base class for drivers.

---

## Base Env

**Module Path:** `commandLAB.gym.environments.base_env`

Abstract base class for environments.

---

## Computer Env

**Module Path:** `commandLAB.gym.environments.computer_env`

Configuration for the computer environment.

---

## Multimodal Env

**Module Path:** `commandLAB.gym.environments.multimodal_env`

Base class for environments with multiple modalities for observations and actions

---

## Grid Overlay Wrapper

**Module Path:** `commandLAB.gym.environments.wrappers.grid_overlay_wrapper`

Wrapper that adds a grid overlay to screenshot observations.

---

## Gymnasium

**Module Path:** `commandLAB.gym.environments.wrappers.gymnasium`

Wrapper that converts BaseComputerEnv to OpenRL Gym environment

---

## Screen Parser Wrapper

**Module Path:** `commandLAB.gym.environments.wrappers.screen_parser_wrapper`

Wrapper that adds a grid overlay to screenshot observations and optionally parses screen text.

---

## Llm Based Evals

**Module Path:** `commandLAB.gym.evals.llm_based_evals`

A base class for evaluators that use LLMs to evaluate tasks.

---

## Schema

**Module Path:** `commandLAB.gym.schema`

Abstract base class for episodes.

---

## Base

**Module Path:** `commandLAB.gym.tasks.base`

A task is a description of the goal of the agent.

---

## Computer Task

**Module Path:** `commandLAB.gym.tasks.computer_task`

---

## Trainer

**Module Path:** `commandLAB.gym.trainer`

Base class for trainers.

---

## Whisper

**Module Path:** `commandLAB.processors.audio_transcription.whisper`

---

## Grid Overlay

**Module Path:** `commandLAB.processors.grid_overlay`

Overlay a grid on an image.

    Args:
        img: PIL Image to overlay grid on
        grid_px_size: Size of grid cells in pixels

    Returns:
        PIL Image with grid overlaid

    Examples:
        >>> # Create a test image
        >>> from PIL import Image
        >>> test_img = Image.new('RGB', (300, 200), color='white')
        >>> # Apply grid overlay
        >>> result = overlay_grid(test_img, grid_px_size=100)
        >>> # Check that result is an Image
        >>> isinstance(result, Image.Image)
        True
        >>> # Check that dimensions are preserved
        >>> result.size
        (300, 200)
        >>> # Check that it's a different image object (copy was made)
        >>> result is not test_img
        True

        >>> # Test with different grid size
        >>> small_grid = overlay_grid(test_img, grid_px_size=50)
        >>> small_grid.size
        (300, 200)

---

## Pytesseract Screen Parser

**Module Path:** `commandLAB.processors.screen_parser.pytesseract_screen_parser`

Parse a screenshot using Tesseract OCR.

    Args:
        screenshot_b64: Base64 encoded screenshot image

    Returns:
        ParsedScreenshot containing the detected text elements and their bounding boxes

    Examples:
        >>> # This example demonstrates the expected pattern but won't run in doctest
        >>> # Create a mock base64 image with text
        >>> import base64
        >>> from PIL import Image, ImageDraw, ImageFont
        >>> import io
        >>> # Create a blank image
        >>> img = Image.new('RGB', (200, 50), color='white')
        >>> # Add text to the image
        >>> draw = ImageDraw.Draw(img)
        >>> draw.text((10, 10), "Hello CommandLAB", fill='black')
        >>> # Convert to base64
        >>> buffer = io.BytesIO()
        >>> img.save(buffer, format="PNG")
        >>> b64_str = base64.b64encode(buffer.getvalue()).decode('utf-8')
        >>>
        >>> # Parse the screenshot (this would be the actual test)
        >>> # result = parse_screenshot(b64_str)
        >>> # Check that we get a ParsedScreenshot
        >>> # isinstance(result, ParsedScreenshot)
        >>> # True
        >>> # Check that we found some text
        >>> # len(result.elements) > 0
        >>> # True
        >>> # Check that the first element contains our text
        >>> # "Hello" in result.elements[0].text
        >>> # True

---

## Screenparse Ai Screen Parser

**Module Path:** `commandLAB.processors.screen_parser.screenparse_ai_screen_parser`

Parse a screenshot using the ScreenParse.ai API.

    Args:
        base64_image: Base64 encoded image string
        api_key: ScreenParse.ai API key
        api_url: ScreenParse.ai API endpoint URL

    Returns:
        ParsedScreenshot containing the detected text elements and their bounding boxes

---

## Types

**Module Path:** `commandLAB.processors.screen_parser.types`

---

## Openai

**Module Path:** `commandLAB.processors.tts.openai`

---

## Some Local Model

**Module Path:** `commandLAB.processors.tts.some_local_model`

---

## Types

**Module Path:** `commandLAB.types`

Convert a standard mouse button into the VNC-compatible code.
        For VNC, left=1, middle=2, right=3.

---

## Image

**Module Path:** `commandLAB.utils.image`

Convert a base64 encoded image string to a PIL Image.

    Args:
        b64: Base64 encoded image string

    Returns:
        PIL Image object

    Examples:
        >>> # This example shows the pattern but won't actually run in doctest
        >>> import base64
        >>> from PIL import Image
        >>> # Create a small red 1x1 pixel image
        >>> img = Image.new('RGB', (1, 1), color='red')
        >>> buffer = io.BytesIO()
        >>> img.save(buffer, format="PNG")
        >>> b64_str = base64.b64encode(buffer.getvalue()).decode('utf-8')
        >>> result_img = b64ToImage(b64_str)
        >>> result_img.size
        (1, 1)
        >>> result_img.getpixel((0, 0))
        (255, 0, 0)

---

## Viewer

**Module Path:** `commandLAB.utils.viewer`

Initialize the Environment Viewer.

        computer_or_env: An environment instance that supports _get_observation(), returning a ComputerObservation.
        refresh_rate: Refresh interval in milliseconds.
        show_mouse: Whether to display mouse state information.
        show_keyboard: Whether to display keyboard state information.

---

## Version

**Module Path:** `commandLAB.version`

Get the container version to use for deployments

---

