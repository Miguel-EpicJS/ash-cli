from agno.agent import Agent
from agno.models.ollama import Ollama

# Create an agent using the local Qwen3.5 4B model via Ollama
agent = Agent(
    model=Ollama(id="qwen3.5:4b"),
    description="You are a helpful AI assistant.",
    instructions="Respond concisely and helpfully to user queries.",
    markdown=True
)

# Test the agent with a simple greeting
if __name__ == "__main__":
    agent.print_response("Hello! How are you today?", stream=True)