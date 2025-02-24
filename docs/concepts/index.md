# Core Concepts

CommandLAB is built around several key concepts that work together to provide a flexible and powerful framework for computer automation.

![Core Concepts](../assets/images/core_concepts.png)

## Key Components

1. **[Computers](computers.md)**: The core interfaces for controlling computers
2. **[Provisioners](provisioners.md)**: Tools for setting up and managing computer environments
3. **[Gym Framework](gym.md)**: A reinforcement learning framework for training agents
4. **[Daemon](daemon.md)**: A service for remote computer control
5. **[Types](types.md)**: The data models that define actions and observations

## How They Work Together

CommandLAB's components are designed to work together in a modular way:

- **Computers** provide a unified interface for controlling different types of computers
- **Provisioners** handle the setup and teardown of computer environments
- The **Gym Framework** uses computers to train agents through reinforcement learning
- The **Daemon** exposes computer functionality through a REST API
- **Types** define the common language for actions and observations across the framework

This modular design allows you to mix and match components based on your needs. For example, you could:

- Use a local computer with pynput for simple automation
- Deploy a daemon-controlled computer in AWS for cloud-based testing
- Train an agent using the gym framework with any computer implementation
- Create your own custom computer implementation while leveraging existing provisioners

## Design Philosophy

CommandLAB follows several key design principles:

1. **Unified Interface**: All computer implementations share the same interface
2. **Modularity**: Components can be used independently or together
3. **Extensibility**: Easy to add new implementations of core interfaces
4. **Type Safety**: Strong typing throughout the codebase
5. **Cloud-Ready**: Support for various deployment environments