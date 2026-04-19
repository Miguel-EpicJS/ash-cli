from agno.agent import Agent
from agno.models.openai.like import OpenAILike

agent = Agent(
    model=OpenAILike(
        id="qwen3.5:4b",
        api_key="not-needed",
        base_url="http://localhost:8080/v1",
        temperature=0.7,
        max_tokens=500,
    ),
    description="You are a helpful AI assistant.",
    instructions=[
        "Respond concisely and helpfully to user queries.",
        "Do not show your thinking process - just give the final answer.",
    ],
    markdown=True,
    thinking={},  # Disable thinking to speed up responses
    show_tool_calls=False,
)

if __name__ == "__main__":
    agent.print_response("Hello! How are you today?")
