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
        "Respond concisely - keep answers short and direct.",
        "Think briefly and give your final answer only.",
    ],
    markdown=True,
)

if __name__ == "__main__":
    agent.print_response("Hello! How are you today?")