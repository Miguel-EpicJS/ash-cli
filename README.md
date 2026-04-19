# Ash CLI - Local AI Agent

A local AI agent built with the Agno framework and powered by a Qwen 3.5 4B model running via llama.cpp for maximum efficiency.

## Features

- Uses Agno framework for agent orchestration
- Runs locally using llama.cpp for efficient inference
- No external API keys required
- Designed for privacy and offline use
- Managed with uv for fast dependency management
- Type-safe with full type hints

## Project Structure

```
ash-cli/
├── src/ash_cli/
│   ├── __init__.py     # package version
│   ├── __main__.py    # CLI entry point
│   ├── config.py      # configuration dataclasses
│   ├── buffer.py     # scroll buffer for streaming
│   ├── agent.py     # agent factory
│   └── tui.py      # terminal UI
├── pyproject.toml   # project configuration
├── uv.lock        # locked dependencies
└── README.md     # this file
```

## Setup

### 1. Install Dependencies

```bash
uv sync
```

### 2. Set Up llama.cpp Server

You need to have llama.cpp server running with the Qwen3.5-4B model.

#### Option A: Using Pre-built llama.cpp binary

1. Download llama.cpp from https://github.com/ggerganov/llama.cpp
2. Build the server (follow instructions in the llama.cpp repository)
3. Obtain a Qwen3.5-4B model in GGUF format (e.g., from Hugging Face)
4. Start the server:

```bash
./server -m /path/to/qwen3.5-4b.q4_K_M.gguf --port 8080 --host 0.0.0.0
```

#### Option B: Using Docker

Alternatively, you can use a Docker container for llama.cpp if available.

### 3. Verify the Server is Running

The server should be accessible at `http://localhost:8080/v1`.

## Usage

```bash
uv run ash-cli
```

Or with activation:

```bash
source .venv/bin/activate
ash-cli
```

## Configuration

Edit `src/ash_cli/config.py` to customize:

- `ModelConfig`: model id, temperature, max_tokens
- `AgentConfig`: description, instructions
- `TUIConfig`: panel heights, titles
- `Config.default_prompt`: default prompt

## Requirements

- Python 3.13+
- llama.cpp server with Qwen3.5-4B model (or compatible)
- Agno framework (installed via uv sync)

## License

MIT

## Acknowledgments

- [Agno Framework](https://docs.agno.com)
- [llama.cpp](https://github.com/ggerganov/llama.cpp)
- [Qwen 3.5](https://huggingface.co/Qwen/Qwen3-5) by Alibaba Cloud