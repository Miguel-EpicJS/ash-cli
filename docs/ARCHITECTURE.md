# Architecture Overview - Ash CLI

This document describes the high-level architecture of Ash CLI and how its components interact.

## Components

Ash CLI is built as a modular Python application leveraging several key libraries:

### 1. CLI Entry Point (`__main__.py`)
- Uses `argparse` to handle command-line arguments.
- Manages high-level workflows like session management (list, export, import), configuration resets, and shell completion generation.
- Orchestrates the transition from CLI to the interactive TUI.

### 2. Configuration System (`config.py`)
- Uses `dataclasses` to define structured configuration for Models, Agents, and the TUI.
- Implements a tiered configuration loading strategy:
  1. Hardcoded defaults.
  2. Environment variables (via `.env`).
  3. Local file-based configuration (e.g., `~/.config/ash-cli/config.yaml`).
  4. Command-line overrides.
- Supports model presets for easy switching between different local LLM backends.

### 3. Agent Orchestration (`agent.py`)
- Powered by the **Agno** framework.
- Wraps the `OpenAILike` model class to communicate with `llama.cpp`'s OpenAI-compatible server.
- Sets up the agent's persona, instructions, and tool inventory.

### 4. Terminal User Interface (`tui.py` & `buffer.py`)
- Powered by **Rich**.
- Implements a custom streaming event loop that handles:
  - Asynchronous agent responses.
  - Thinking vs. Content panel separation.
  - Interactive prompt with history completion and search.
- **ScrollBuffer**: A custom utility to manage scrollable text areas within Fixed-height panels.

### 5. Session Management (`session.py`)
- Manages conversation history and usage metrics.
- Persists sessions as JSON files (soon to be SQLite) in the user's config directory.
- Implements `Usage` tracking for token counts and latency metrics.

### 6. Error Handling (`error.py`)
- Defines a hierarchy of application-specific exceptions.
- Provides validation helpers for configuration and user input.

## Data Flow

1.  **Initialization**: `main()` parses args and loads `Config`.
2.  **Session Setup**: Either a new session is created or an existing one is loaded via `session.py`.
3.  **TUI Loop**:
    - User enters a prompt in the TUI.
    - `tui.py` spawns a thread to run the `Agent`.
    - The Agent streams responses back; `tui.py` updates the `Live` display.
    - `buffer.py` handles the text rolling and scrolling.
4.  **Action**: After the agent responds, the user can **Execute**, **Copy**, or **Skip** the generated command.
5.  **Persistence**: The message and updated usage metrics are saved back to the session file.

## Design Principles

- **Local First**: Every feature must work offline assuming a local inference server is available.
- **Efficiency**: Minimize overhead and ensure the TUI remains responsive even during heavy streaming.
- **Transparency**: Give users full visibility into model behavior and resource usage.
