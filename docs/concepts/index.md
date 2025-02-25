# Core Concepts

CommandLAB is built around several key concepts that work together to provide a flexible and powerful framework for computer automation. This section explains these concepts in detail and how they interact with each other.

![Core Concepts](../assets/images/core_concepts.png)

## Overview

CommandLAB's architecture is designed to be modular, extensible, and cloud-ready. The key components are:

1. **Computers**: The core interfaces for controlling computers
1. **Provisioners**: Tools for setting up and managing computer environments
1. **Gym Framework**: A reinforcement learning framework for training agents
1. **Daemon**: A service for remote computer control
1. **Types**: The data models that define actions and observations

## Computers

[Computers](computers.md) are the central abstraction in CommandLAB. A Computer represents any system that can be controlled programmatically, whether it's your local machine, a remote server, or a virtual environment.

All computers implement the `BaseComputer` interface, which provides methods for:

- Taking screenshots
- Getting mouse and keyboard state
- Executing commands
- Controlling the mouse and keyboard

Available computer implementations include:

- `LocalPynputComputer`: Controls your local computer using pynput
- `LocalPyAutoGUIComputer`: Controls your local computer using PyAutoGUI
- `E2BDesktopComputer`: Uses E2B Desktop Sandbox for secure interactions
- `DaemonClientComputer`: Connects to a remote daemon for computer control

## Provisioners

[Provisioners](provisioners.md) handle the setup, management, and teardown of computer environments. They're especially useful for cloud and container deployments.

A provisioner is responsible for:

1. **Setting up** a computer environment (e.g., starting a Docker container)
1. **Checking** if the environment is running
1. **Tearing down** the environment when it's no longer needed

Available provisioner implementations include:

- `ManualProvisioner`: For manually managed environments
- `DockerProvisioner`: For Docker container environments
- `KubernetesProvisioner`: For Kubernetes deployments
- `AWSProvisioner`: For AWS EC2 instances
- `AzureProvisioner`: For Azure VMs
- `GCPProvisioner`: For Google Cloud Platform VMs

## Gym Framework

The [Gym Framework](gym.md) is a reinforcement learning framework inspired by OpenAI Gym, designed specifically for training agents to use computers.

Key components of the gym framework include:

- **Environments**: Represent tasks that agents can interact with
- **Agents**: Entities that interact with environments by taking actions
- **Episodes**: Sequences of interactions between agents and environments
- **Drivers**: Manage the interaction between agents and environments
- **Trainers**: Train agents using episodes collected by drivers

The gym framework implements the standard reinforcement learning loop:

1. The environment provides an observation
1. The agent selects an action based on the observation
1. The environment executes the action and returns a new observation, reward, and done flag
1. The process repeats until the episode is complete

## Daemon

The [Daemon](daemon.md) is a service that allows remote control of computers through a REST API. It exposes computer functionality through HTTP endpoints, providing authentication via API tokens.

The daemon can be deployed in various environments:

- Locally on your machine
- In Docker containers
- In Kubernetes clusters
- On cloud VMs

The `DaemonClientComputer` can use provisioners to automatically set up and manage daemon environments, making it easy to create and control remote computers.

## Types

The [Types](types.md) system defines the data models used throughout CommandLAB. These include:

- **Actions**: Operations that can be performed on a computer (e.g., `ClickAction`, `TypeAction`)
- **Observations**: Information about the computer's state (e.g., `ScreenshotObservation`, `MouseStateObservation`)
- **Enums**: Standardized values for keys, mouse buttons, etc.

The type system includes mappings to convert between CommandLAB's standard types and backend-specific types, allowing CommandLAB to provide a consistent interface while supporting multiple backends.

## How They Work Together

CommandLAB's components are designed to work together in a modular way:

- **Computers** provide a unified interface for controlling different types of computers
- **Provisioners** handle the setup and teardown of computer environments
- The **Gym Framework** uses computers to train agents through reinforcement learning
- The **Daemon** exposes computer functionality through a REST API
- **Types** define the common language for actions and observations across the framework

This diagram illustrates how the components interact:

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│    Agent    │────▶│ Environment │────▶│  Computer   │
└─────────────┘     └─────────────┘     └─────────────┘
                                              │
                                              ▼
                                        ┌─────────────┐
                                        │ Provisioner │
                                        └─────────────┘
                                              │
                                              ▼
                                        ┌─────────────┐
                                        │   Daemon    │
                                        └─────────────┘
```

## Design Philosophy

CommandLAB follows several key design principles:

1. **Unified Interface**: All computer implementations share the same interface, making it easy to switch between different backends.

1. **Modularity**: Components can be used independently or together. For example, you can use a computer without the gym framework, or use the gym framework with any computer implementation.

1. **Extensibility**: It's easy to add new implementations of core interfaces. For example, you can create a new computer implementation that controls a specialized system while leveraging existing provisioners and the gym framework.

1. **Type Safety**: Strong typing throughout the codebase ensures that errors are caught at development time rather than runtime.

1. **Cloud-Ready**: Support for various deployment environments, from local development to cloud-based production.

1. **Separation of Concerns**: Each component has a clear responsibility, making the system easier to understand and extend.

## Next Steps

Now that you understand the core concepts, you can explore each one in more detail:

- [Computers](computers.md): Learn about the different computer implementations
- [Provisioners](provisioners.md): Understand how to manage computer environments
- [Gym Framework](gym.md): Discover how to train agents to use computers
- [Daemon](daemon.md): Learn about remote computer control
- [Types](types.md): Explore the data models used throughout CommandLAB
