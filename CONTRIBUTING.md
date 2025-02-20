# Contributing to CommandLab

## Quick Start

1. Fork & clone:

   ```bash
   git clone https://github.com/commandAGI/commandagi-lab.git
   cd commandagi-lab
   ```

2. Set up dev environment:

   ```bash
   poetry install
   pre-commit install
   ```

3. Create a branch:

   ```bash
   git checkout -b fix-something
   ```

4. Make your changes and ensure tests pass:

   ```bash
   poetry run pytest
   ```

5. Push and open a PR.

## Code Standards

We use several code quality tools that run automatically via pre-commit hooks:

- Code formatting with `black`
- Import sorting with `isort`
- Linting with `ruff` (includes auto-fixes for common issues)
- Additional checks for:
  - Trailing whitespace
  - File ending newlines
  - YAML syntax
  - Large file additions

Additional requirements:

- Must have tests for new functionality
- Keep commits atomic and messages clear

## Pull Requests

1. Keep changes focused and separate concerns into different PRs
2. Update tests and docs
3. Reference any related issues
4. Wait for CI to pass if applicable

## Questions?

[Open an issue](https://github.com/commandAGI/commandagi-lab/issues/new) or start a discussion.
