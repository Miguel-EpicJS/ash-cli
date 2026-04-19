from agno.agent import Agent
from agno.models.openai.like import OpenAILike

from .config import AgentConfig, ModelConfig


def create_agent(
    model_config: ModelConfig,
    agent_config: AgentConfig,
    session_id: str | None = None,
) -> Agent:
    return Agent(
        model=OpenAILike(
            id=model_config.id,
            api_key=model_config.api_key,
            base_url=model_config.base_url,
            temperature=model_config.temperature,
            max_tokens=model_config.max_tokens,
        ),
        description=agent_config.description,
        instructions=list(agent_config.instructions),
        markdown=agent_config.markdown,
        session_id=session_id,
    )
