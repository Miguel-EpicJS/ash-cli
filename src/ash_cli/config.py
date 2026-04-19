from __future__ import annotations

import json
import os
import sys
from dataclasses import dataclass, field, fields
from pathlib import Path
from typing import Any

import yaml
from dotenv import load_dotenv

from ash_cli.logging import Level, LoggingConfig


def _find_project_root() -> Path:
    current = Path(__file__).resolve().parent
    for parent in current.parents:
        if (parent / "pyproject.toml").exists():
            return parent
    return current


def _load_env_files() -> None:
    env_paths = [
        _find_project_root() / ".env",
        _get_default_config_dir() / ".env",
    ]
    for env_path in env_paths:
        if env_path.exists():
            load_dotenv(env_path)
            return


@dataclass
class Args:
    model: str | None = None
    temperature: float | None = None
    max_tokens: int | None = None
    url: str | None = None
    debug: bool = False


@dataclass
class ModelConfig:
    id: str = "qwen3.5:4b"
    api_key: str = "not-needed"
    base_url: str = "http://localhost:8080/v1"
    temperature: float = 0.6
    max_tokens: int = 4096
    debug: bool = False


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
    panel_height: int = 8
    thinking_panel_height: int = 8
    refresh_rate: int = 8
    input_panel_title: str = "Input"
    thinking_panel_title: str = "Thinking"
    response_panel_title: str = "Response"


@dataclass
class Config:
    model: ModelConfig = field(default_factory=ModelConfig)
    agent: AgentConfig = field(default_factory=AgentConfig)
    tui: TUIConfig = field(default_factory=TUIConfig)
    logging: LoggingConfig = field(default_factory=LoggingConfig)


def _get_default_config_dir() -> Path:
    if sys.platform == "win32":
        base = Path(os.environ.get("APPDATA", Path.home() / ".ash-cli"))
    elif sys.platform == "darwin":
        base = Path.home() / "Library" / "Application Support"
    else:
        base = Path.home() / ".config"
    return base / "ash-cli"


def _get_default_config_path() -> Path:
    return _get_default_config_dir() / "config"


def _load_yaml(path: Path) -> dict[str, Any]:
    with open(path) as f:
        return yaml.safe_load(f) or {}


def _load_json(path: Path) -> dict[str, Any]:
    with open(path) as f:
        return json.load(f)  # type: ignore[no-any-return]


def _load_config_file(path: Path | None) -> dict[str, Any]:
    if path is None:
        default_path = _get_default_config_path()
        for ext in (".json", ".yaml", ".yml"):
            candidate = default_path.with_suffix(ext)
            if candidate.exists():
                path = candidate
                break
        else:
            return {}
    if path is None or not path.exists():
        return {}

    suffix = path.suffix.lower()
    if suffix in (".yaml", ".yml"):
        return _load_yaml(path)
    return _load_json(path)


def _apply_config(config: Config, data: dict[str, Any]) -> Config:
    for f in fields(config):
        if f.name in data:
            value = data[f.name]
            if isinstance(value, dict):
                current = getattr(config, f.name)
                if hasattr(current, "__dataclass_fields__"):
                    sub_fields = {sf.name: sf for sf in fields(current)}
                    for sub_k, sub_v in value.items():
                        if sub_k in sub_fields:
                            setattr(current, sub_k, sub_v)
    return config


def _apply_args(config: Config, args: Args) -> Config:
    if args.model is not None:
        config.model.id = args.model
    if args.temperature is not None:
        config.model.temperature = args.temperature
    if args.max_tokens is not None:
        config.model.max_tokens = args.max_tokens
    if args.url is not None:
        config.model.base_url = args.url
    if args.debug:
        config.tui.refresh_rate = 1
    return config


def _apply_env(config: Config) -> Config:
    if model_id := os.environ.get("ASH_MODEL"):
        config.model.id = model_id
    if api_key := os.environ.get("ASH_API_KEY"):
        config.model.api_key = api_key
    if base_url := os.environ.get("ASH_BASE_URL"):
        config.model.base_url = base_url
    if temperature := os.environ.get("ASH_TEMPERATURE"):
        config.model.temperature = float(temperature)
    if max_tokens := os.environ.get("ASH_MAX_TOKENS"):
        config.model.max_tokens = int(max_tokens)
    if log_level := os.environ.get("ASH_LOG_LEVEL"):
        config.logging.level = Level[log_level.upper()]
    if log_file := os.environ.get("ASH_LOG_FILE"):
        config.logging.file = Path(log_file)
    if log_format := os.environ.get("ASH_LOG_FORMAT"):
        config.logging.format = log_format  # type: ignore[assignment]
    return config


def get_config(path: Path | None = None, args: Args | None = None) -> Config:
    _load_env_files()
    base = Config()
    base = _apply_config(base, _load_config_file(path))
    base = _apply_env(base)
    if args is not None:
        base = _apply_args(base, args)
    return base
