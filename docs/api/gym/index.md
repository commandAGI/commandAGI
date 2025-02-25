# Gym API

This section contains documentation for the gym framework, which provides a standardized interface for training and evaluating AI agents that control computers. The gym framework is based on the OpenAI Gym/Gymnasium interface.

## Core Components

- **[Base](base.md)** - Base classes and utilities for the gym framework
- **[Schema](schema.md)** - Data schemas and validation for gym components
- **[Drivers](drivers.md)** - Drivers for connecting agents to environments
- **[Trainer](trainer.md)** - Training utilities for gym agents

## Environments

- **[Environments](environments/index.md)** - Environment implementations
- **[Computer Task](computer_task.md)** - Task definitions for computer environments

## Agents

- **[Agents](agents/index.md)** - Agent implementations
- **[Llms](llms.md)** - Language model integrations for agents
- **[Llm Based Evals](llm_based_evals.md)** - Evaluation utilities using language models

## Wrappers

- **[Grid Overlay Wrapper](grid_overlay_wrapper.md)** - Environment wrapper for grid-based interactions
- **[Screen Parser Wrapper](screen_parser_wrapper.md)** - Environment wrapper for screen parsing
- **[Gymnasium](gymnasium.md)** - Wrappers for compatibility with Gymnasium
