# AGENTS.md

## Setup

```bash
uv sync          # install dependencies
```

Requires **llama.cpp server running** at `http://localhost:8080/v1` with Qwen3.5-4B model before running the CLI.

## Run

```bash
uv run ash-cli   # prompts for instructions, outputs bash command
```

## Lint & Typecheck

```bash
uv run ruff check src/
uv run ruff format src/
uv run mypy src/
```

Ruff: line-length 88, target py313. mypy: strict mode.

## Key Files

- `src/ash_cli/__main__.py` - CLI entry point
- `src/ash_cli/config.py` - Model, agent, TUI config dataclasses
- `src/ash_cli/agent.py` - Agent factory using Agno
- `src/ash_cli/tui.py` - Terminal UI with streaming

## Project Conventions

- **Python 3.13+**
- **No comments** unless explicitly requested
- All code uses strict type hints
- Package lives in `src/ash_cli/`