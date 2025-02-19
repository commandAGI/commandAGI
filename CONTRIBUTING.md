# Contributing to CommandLab

## Quick Start

1. Fork & clone:

   ```bash
   git clone https://github.com/yourusername/commandlab.git
   cd commandlab
   ```

2. Set up dev environment:

   ```bash
   python -m venv venv
   source venv/bin/activate  # or `venv\Scripts\activate` on Windows
   pip install -e ".[dev]"
   ```

3. Create a branch:

   ```bash
   git checkout -b fix-something
   ```

4. Make your changes and ensure tests pass:

   ```bash
   pytest
   ```

5. Push and open a PR.

## Code Standards

- Format with `black`
- Sort imports with `isort`
- Must pass `ruff` linting
- Must have tests
- Keep commits atomic and messages clear

## Project Structure

- Core functionality goes in `src/commandlab/`
- Framework integrations go in their respective packages (e.g., `src/commandlab_langchain/`)
- Tests mirror the source structure in `tests/`

## Pull Requests

1. Keep changes focused and separate concerns into different PRs
2. Update tests and docs
3. Reference any related issues
4. Wait for CI to pass

## Questions?

Open an issue or start a discussion.
