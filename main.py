from agno.agent import Agent
from agno.models.openai.like import OpenAILike

# Create an agent using a local llama.cpp server (OpenAI-compatible API)
# Make sure to run the llama.cpp server with the Qwen3.5-4B model first:
#   ./server -m /path/to/qwen3.5-4b.q4_K_M.gguf --port 8080 --host 0.0.0.0
agent = Agent(
    model=OpenAILike(
        id="qwen3.5-4b",  # Model name, can be anything but must match what the server serves
        api_key="not-needed",  # llama.cpp server doesn't require an API key
        base_url="http://localhost:8080/v1",  # Default llama.cpp server endpoint
        temperature=0.7,
        max_tokens=2000,
    ),
    description="You are a helpful AI assistant.",
    instructions="Respond concisely and helpfully to user queries.",
    markdown=True
)

# Test the agent with a simple greeting
if __name__ == "__main__":
    agent.print_response("Hello! How are you today?", stream=True)