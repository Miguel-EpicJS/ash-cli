from agno.agent import Agent
from agno.models.openai.like import OpenAILike

agent = Agent(
    model=OpenAILike(
        id="qwen3.5:4b",
        api_key="not-needed",
        base_url="http://localhost:8080/v1",
        temperature=0.3,
        max_tokens=300,
    ),
    description="You are a helpful AI assistant.",
    instructions=[
        "Think and respond very briefly.",
        "Keep all responses under 2 sentences.",
    ],
    markdown=True,
)

if __name__ == "__main__":
    agent.print_response("Hello! How are you today?", stream=True)