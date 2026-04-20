from agno.agent import Agent
from agno.models.openai.like import OpenAILike

from .config import AgentConfig, ModelConfig
from .logging import init_logging

logger = init_logging()


def create_agent(
    model_config: ModelConfig,
    agent_config: AgentConfig,
    session_id: str | None = None,
) -> Agent:
    """
    Creates and configures an Agno Agent instance.

    Args:
        model_config: Configuration for the LLM model.
        agent_config: Configuration for the agent's persona and instructions.
        session_id: Optional ID to associate the agent with a persistent session.

    Returns:
        A configured Agno Agent instance.
    """
    logger.debug(f"Creating agent with model: {model_config.id}")
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
