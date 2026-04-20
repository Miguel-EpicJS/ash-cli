# Contributing to Ash CLI

Thank you for your interest in contributing to Ash CLI! We welcome all kinds of contributions, from bug reports and documentation improvements to new features and performance optimizations.

## Getting Started

1.  **Fork the Repository**: Create your own fork of the ash-cli repository.
2.  **Clone Locally**:
    ```bash
    git clone https://github.com/YOUR_USERNAME/ash-cli.git
    cd ash-cli
    ```
3.  **Setup Development Environment**:
    Use `uv` (recommended) to install dependencies and setup the virtual environment:
    ```bash
    uv sync
    ```
4.  **Install Pre-commit Hooks** (Optional but recommended):
    We use `ruff` for formatting and linting.

## Development Workflow

### Coding Standards

- **Python 3.13+**: We take advantage of the latest Python features.
- **Strict Typing**: All code must have complete and accurate type hints. Use `mypy` to verify.
- **No Unused Imports**: Use `ruff` to clean up imports.

### Verification Tools

Before submitting a PR, please run the following:

```bash
# Formatter
uv run ruff format src/

# Linter
uv run ruff check src/

# Type Checker
uv run mypy src/

# Tests
uv run pytest
```

## Adding New Features

- **Models**: New model presets should be added to `src/ash_cli/config.py`.
- **Tools**: If you want the agent to use new tools, update `src/ash_cli/agent.py` and the agent's instructions.
- **TUI**: UI enhancements should be made in `src/ash_cli/tui.py`.

## Submitting Pull Requests

1.  Create a new branch for your feature or bugfix.
2.  Write clear, concise commit messages.
3.  Push your changes to your fork.
4.  Submit a Pull Request to the main repository.

## Community

If you have questions or want to discuss ideas, please open an Issue or start a Discussion on GitHub.

---

*Happy hacking!*
