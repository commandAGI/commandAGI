# CommandLab

CommandLab is a modular framework for building and managing AI-powered command applications. It provides integrations with popular AI frameworks and community extensions.

## Packages

- `commandlab`: Core functionality and standard features
- `commandlab-openrl`: Integration with OpenAI and Reinforcement Learning
- `commandlab-langchain`: Integration with LangChain
- `commandlab-huggingface`: Integration with Hugging Face Transformers
- `commandlab-community`: Community-contributed extensions

## Project Structure

```filetree
commandlab/
├── pyproject.toml
├── README.md
├── src/
│   ├── commandlab/
│   │   ├── __init__.py
│   │   ├── core/
│   │   └── ...
│   ├── commandlab_openrl/
│   │   ├── __init__.py
│   │   └── ...
│   ├── commandlab_langchain/
│   │   ├── __init__.py
│   │   └── ...
│   ├── commandlab_huggingface/
│   │   ├── __init__.py
│   │   └── ...
│   └── commandlab_community/
│       ├── __init__.py
│       └── ...
└── tests/
    ├── test_commandlab/
    ├── test_openrl/
    ├── test_langchain/
    ├── test_huggingface/
    └── test_community/
```

## Installation

Basic installation (includes core functionality):

```bash
pip install commandlab
```

Install with specific integrations:

```bash
pip install "commandlab[openrl]"     # OpenAI and RL support
pip install "commandlab[langchain]"  # LangChain integration
pip install "commandlab[huggingface]" # Hugging Face integration
pip install "commandlab[community]"   # Community extensions

# Install all integrations
pip install "commandlab[openrl,langchain,huggingface,community]"

# Install for development
pip install -e ".[dev]"
```
