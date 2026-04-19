from dataclasses import dataclass, field


@dataclass
class ModelConfig:
    id: str = "qwen3.5:4b"
    api_key: str = "not-needed"
    base_url: str = "http://localhost:8080/v1"
    temperature: float = 0.6
    max_tokens: int = 4096


@dataclass
class AgentConfig:
    description: str = "CLI assistant that outputs bash commands"
    instructions: tuple[str, ...] = field(
        default_factory=lambda: (
            "You are a CLI assistant that outputs bash commands based on user instructions.",
            "Analyze the user's request and output ONLY the bash command(s) needed to accomplish the task.",
            "Respond with ONLY the command, no explanation or markdown formatting.",
        )
    )
    markdown: bool = False


@dataclass
class TUIConfig:
    panel_height: int = 17
    thinking_panel_height: int = 17
    refresh_rate: int = 8
    input_panel_title: str = "Input"
    thinking_panel_title: str = "Thinking"
    response_panel_title: str = "Response"


@dataclass
class Config:
    model: ModelConfig = field(default_factory=ModelConfig)
    agent: AgentConfig = field(default_factory=AgentConfig)
    tui: TUIConfig = field(default_factory=TUIConfig)
    default_prompt: str = "Explain what 1+1 equals"


def get_config() -> Config:
    return Config()