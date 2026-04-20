# Ash CLI - Your Local AI Wingman ⚡

[![Python 3.13+](https://img.shields.io/badge/python-3.13+-blue.svg)](https://www.python.org/downloads/release/python-3130/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Code style: ruff](https://img.shields.io/badge/code%20style-ruff-000000.svg)](https://github.com/astral-sh/ruff)

**Ash CLI** is a privacy-focused, high-performance terminal assistant designed for developers who want the intelligence of large language models without the cloud. Built on the **Agno** framework and powered by **Qwen 3.5 (4B)** via **llama.cpp**, Ash provides a fast, offline, and secure way to interact with AI directly from your command line.

---

## Why Ash?

- 🔒 **Privacy-First**: No data ever leaves your machine. Perfect for proprietary codebases and sensitive environments.
- 🚀 **Blazing Fast**: Optimized for local CPUs using GGUF quantization. No API latency, no rate limits.
- 🛠️ **Developer Centric**: Outputs ready-to-use bash commands with one-click execution or copy-to-clipboard.
- 💾 **Smart Sessions**: Fully persistent history saved in SQLite, allowing you to resume conversations across terminal sessions.
- 🎨 **Beautiful TUI**: A rich terminal interface with streaming responses, "thinking" panels, and Vim-style navigation.

---

## 🏗️ Project Structure

```text
ash-cli/
├── src/ash_cli/
│   ├── __main__.py    # CLI entry point & argument parsing
│   ├── agent.py       # Agno agent orchestration logic
│   ├── config.py      # Configuration & model presets
│   ├── session.py     # SQLite session & history management
│   ├── tui.py         # Terminal User Interface with Rich
│   ├── buffer.py      # Scroll buffers for streaming output
│   ├── error.py       # Robust error handling & validation
│   └── completions.py # Shell completion generation
├── tests/             # Comprehensive test suite
├── pyproject.toml     # Project metadata & dependencies
└── README.md          # You are here
```

---

## 🚀 Getting Started

### 1. Prerequisites

- **Python 3.13+**
- **uv**: The fastest Python package manager. [Install uv](https://github.com/astral-sh/uv).

### 2. Installation

Clone the repository and sync dependencies:

```bash
git clone https://github.com/Miguel-EpicJS/ash-cli.git
cd ash-cli
uv sync
```

### 3. Start the Local Inference Server

Ash requires a `llama.cpp` server running the **Qwen 3.5 4B** model.

1.  **Download Model**: Get a `q4_K_M` GGUF version of Qwen 3.5 4B (e.g., from [Hugging Face](https://huggingface.co/Qwen/Qwen2.5-3B-Instruct-GGUF)).
2.  **Run Server**:
    ```bash
    ./llama-server -m models/qwen3.5-4b-q4_K_M.gguf --port 8080 --host 0.0.0.0
    ```

### 4. Launch Ash

```bash
uv run ash-cli
```

---

## 📖 Documentation

### CLI Usage

Ash supports several command-line flags to customize your experience:

| Flag | Description |
| :--- | :--- |
| `--model <id>` | Specify which model preset to use. |
| `--temp <float>` | Set sampling temperature (0.0 to 2.0). |
| `--session <id>` | Load a specific past session. |
| `--sessions` | List all historical sessions. |
| `--list-models` | Show all available model presets. |
| `--export <id>:<path>` | Export a session to a JSON file. |
| `--import <path>` | Import a session from a JSON file. |
| `--rename <id>:<name>` | Rename a session. |
| `--completions <sh>` | Generate bash or zsh shell completions. |
| `--reset` | Reset all configurations to defaults. |
| `--debug` | Enable verbose logging for troubleshooting. |

### ⌨️ TUI Commands

Once inside the interactive TUI, you can use several slash-commands:

- `/help`: Show available commands and shortcuts.
- `/quit` or `/q`: Exit the application.
- `/models`: List and view the active model.
- `/model <id>`: Switch models on the fly.
- `/theme <dark\|light\|system>`: Change the UI appearance.
- `/metrics`: View token usage and latency for the *current* session.
- `/stats`: View aggregate usage statistics across *all* sessions.
- `/rename <id> <name>`: Rename the session you are in.

### 🎮 TUI Shortcuts

- **Enter**: Send message or execute command.
- **`\` at end of line**: Continue on a new line (Multi-line input).
- **Tab**: Auto-complete prompt from history.
- **`/` (with empty input)**: Enter history search mode.
- **`j` / `k`** (or arrows): Scroll the response panel up/down.
- **PageUp / PageDown**: Scroll responses by page.
- **`q` or `Esc`**: Stop a streaming response.

---

## ⚙️ Configuration

Ash can be configured via environment variables or a local configuration file.

### Environment Variables (.env)

Create a `.env` file in the project root:

```env
ASH_MODEL_ID=qwen-4b
ASH_TEMPERATURE=0.7
ASH_MAX_TOKENS=2048
ASH_API_URL=http://localhost:8080/v1
```

### Advanced Config

Edit `src/ash_cli/config.py` to define custom model presets or change the default agent instructions.

---

## 📊 Observability

Ash tracks everything locally so you can stay in control:
- **Token Tracking**: Prompt, completion, and total tokens.
- **Latency**: Real-time monitoring of inference speed.
- **Session Telemetry**: See how much you've interacted with your local models over time.

Use `/metrics` or `/stats` to see your data.

---

## 🛠️ Development

### Linting & Formatting

```bash
uv run ruff check src/
uv run ruff format src/
```

### Type Checking

```bash
uv run mypy src/
```

### Testing

```bash
uv run pytest
```

---

## 📜 License

Distributed under the MIT License. See `LICENSE` for more information.

## 🙏 Acknowledgments

- [Agno](https://docs.agno.com) for the powerful agent framework.
- [llama.cpp](https://github.com/ggerganov/llama.cpp) for efficient local inference.
- [Rich](https://github.com/Textualize/rich) for the beautiful terminal UI.