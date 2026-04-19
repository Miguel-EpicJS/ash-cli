from __future__ import annotations

import tempfile
from pathlib import Path
from typing import Any

import pytest

from ash_cli import config as config_module
from ash_cli.config import AgentConfig, Config, ModelConfig, TUIConfig
from ash_cli.session import Message, Session


@pytest.fixture
def temp_dir() -> Path:
    with tempfile.TemporaryDirectory() as td:
        yield Path(td)


@pytest.fixture
def mock_config_dir(temp_dir: Path) -> Path:
    config_dir = temp_dir / "ash-cli"
    config_dir.mkdir(parents=True)
    return config_dir


@pytest.fixture
def mock_sessions_dir(temp_dir: Path) -> Path:
    sessions_dir = temp_dir / "ash-cli" / "sessions"
    sessions_dir.mkdir(parents=True)
    return sessions_dir


@pytest.fixture
def config_file(temp_dir: Path) -> Path:
    return temp_dir / "config.json"


@pytest.fixture
def yaml_config_file(temp_dir: Path) -> Path:
    return temp_dir / "config.yaml"


@pytest.fixture
def minimal_config() -> Config:
    return Config(
        model=ModelConfig(id="test-model"),
        agent=AgentConfig(description="test"),
        tui=TUIConfig(),
    )


@pytest.fixture
def sample_session() -> Session:
    return Session(
        id="test-id-123",
        name="Test Session",
        created_at="2024-01-01T00:00:00+00:00",
        updated_at="2024-01-01T00:00:00+00:00",
        messages=[
            Message(role="user", content="Hello"),
            Message(role="assistant", content="Hi there"),
        ],
    )


@pytest.fixture
def session_dict() -> dict[str, Any]:
    return {
        "id": "test-id-123",
        "name": "Test Session",
        "created_at": "2024-01-01T00:00:00+00:00",
        "updated_at": "2024-01-01T00:00:00+00:00",
        "messages": [
            {
                "role": "user",
                "content": "Hello",
                "timestamp": "2024-01-01T00:00:00+00:00",
            },
            {
                "role": "assistant",
                "content": "Hi there",
                "timestamp": "2024-01-01T00:00:00+00:00",
            },
        ],
        "model": "test-model",
        "temperature": 0.7,
        "max_tokens": 2048,
        "base_url": "http://localhost:8080/v1",
    }


@pytest.fixture
def config_data() -> dict[str, Any]:
    return {
        "model": {
            "id": "custom-model",
            "temperature": 0.8,
        },
        "tui": {
            "color": False,
        },
    }


@pytest.fixture
def mock_env_vars() -> dict[str, str]:
    return {
        "ASH_MODEL": "env-model",
        "ASH_API_KEY": "env-key",
        "ASH_BASE_URL": "http://env:8080/v1",
        "ASH_TEMPERATURE": "0.9",
    }


@pytest.fixture
def mock_config_dir_path(mocker: pytest.MockerFixture, mock_config_dir: Path) -> Path:
    mocker.patch.object(
        config_module, "_get_default_config_dir", return_value=mock_config_dir
    )
    return mock_config_dir
