# Ash CLI - Local AI Agent

A local AI agent built with the Agno framework and powered by a Qwen 3.5 4B model running via llama.cpp for maximum efficiency.

## Features

- Uses Agno framework for agent orchestration
- Runs locally using llama.cpp for efficient inference
- No external API keys required
- Designed for privacy and offline use

## Project Structure

- `src/hello_agent_llama_cpp.py`: Main agent script using llama.cpp via OpenAI-compatible API
- `requirements.txt`: Python dependencies

## Setup Instructions

### 1. Install Dependencies

```bash
pip install -r requirements.txt
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

#### Option B: Using Docker (if available)

Alternatively, you can use a Docker container for llama.cpp if available.

### 3. Verify the Server is Running

The server should be accessible at `http://localhost:8080/v1`.

## Usage

Run the agent:

```bash
python src/hello_agent_llama_cpp.py
```

The agent will respond to the greeting "Hello! How are you today?" with a streamed response.

## Customization

You can modify the agent in `src/hello_agent_llama_cpp.py`:

- Change the model ID (if using a different model)
- Adjust temperature, max_tokens, etc.
- Modify the description and instructions to change the agent's behavior
- Add tools to extend the agent's capabilities

## Requirements

- Python 3.8+
- llama.cpp server with Qwen3.5-4B model (or compatible)
- Agno framework (installed via requirements.txt)

## License

This project is open source and available under the MIT License.

## Acknowledgments

- [Agno Framework](https://docs.agno.com)
- [llama.cpp](https://github.com/ggerganov/llama.cpp)
- [Qwen 3.5](https://huggingface.co/Qwen/Qwen3-5) by Alibaba Cloud