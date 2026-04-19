from __future__ import annotations

import os
from pathlib import Path
from typing import Any

import pytest

from ash_cli import config as config_module
from ash_cli.config import (
    AgentConfig,
    Args,
    Config,
    ModelConfig,
    TUIConfig,
    _apply_args,
    _apply_config,
    _apply_env,
    _load_config_file,
    _load_json,
    _load_yaml,
    get_config,
    reset_config,
)


class TestGetDefaultConfigDir:
    def test_returns_path(self) -> None:
        result = config_module._get_default_config_dir()
        assert isinstance(result, Path)
        assert result.name == "ash-cli"


class TestApplyArgs:
    def test_applies_model(self) -> None:
        config = Config()
        args = Args(model="custom-model")
        result = _apply_args(config, args)
        assert result.model.id == "custom-model"

    def test_applies_temperature(self) -> None:
        config = Config()
        args = Args(temperature=0.9)
        result = _apply_args(config, args)
        assert result.model.temperature == 0.9

    def test_applies_max_tokens(self) -> None:
        config = Config()
        args = Args(max_tokens=2048)
        result = _apply_args(config, args)
        assert result.model.max_tokens == 2048

    def test_applies_url(self) -> None:
        config = Config()
        args = Args(url="http://custom:8080/v1")
        result = _apply_args(config, args)
        assert result.model.base_url == "http://custom:8080/v1"

    def test_applies_debug(self) -> None:
        config = Config()
        args = Args(debug=True)
        result = _apply_args(config, args)
        assert result.tui.refresh_rate == 1

    def test_applies_color(self) -> None:
        config = Config()
        args = Args(color=False)
        result = _apply_args(config, args)
        assert result.tui.color is False


class TestApplyEnv:
    def test_applies_model_from_env(self, mocker: pytest.MockerFixture) -> None:
        mocker.patch.dict(os.environ, {"ASH_MODEL": "env-model"})
        config = Config()
        result = _apply_env(config)
        assert result.model.id == "env-model"

    def test_applies_api_key_from_env(self, mocker: pytest.MockerFixture) -> None:
        mocker.patch.dict(os.environ, {"ASH_API_KEY": "secret-key"})
        config = Config()
        result = _apply_env(config)
        assert result.model.api_key == "secret-key"

    def test_applies_base_url_from_env(self, mocker: pytest.MockerFixture) -> None:
        mocker.patch.dict(os.environ, {"ASH_BASE_URL": "http://env:8080/v1"})
        config = Config()
        result = _apply_env(config)
        assert result.model.base_url == "http://env:8080/v1"

    def test_applies_temperature_from_env(self, mocker: pytest.MockerFixture) -> None:
        mocker.patch.dict(os.environ, {"ASH_TEMPERATURE": "0.7"})
        config = Config()
        result = _apply_env(config)
        assert result.model.temperature == 0.7

    def test_applies_max_tokens_from_env(self, mocker: pytest.MockerFixture) -> None:
        mocker.patch.dict(os.environ, {"ASH_MAX_TOKENS": "2048"})
        config = Config()
        result = _apply_env(config)
        assert result.model.max_tokens == 2048

    def test_applies_color_from_env(self, mocker: pytest.MockerFixture) -> None:
        mocker.patch.dict(os.environ, {"ASH_COLOR": "1"})
        config = Config()
        result = _apply_env(config)
        assert result.tui.color is True

    def test_applies_no_color_from_env(self, mocker: pytest.MockerFixture) -> None:
        mocker.patch.dict(os.environ, {"ASH_NO_COLOR": "1"})
        config = Config()
        result = _apply_env(config)
        assert result.tui.color is False


class TestApplyConfig:
    def test_applies_model_config(self) -> None:
        config = Config()
        data: dict[str, Any] = {"model": {"id": "custom-id"}}
        result = _apply_config(config, data)
        assert result.model.id == "custom-id"

    def test_applies_tui_config(self) -> None:
        config = Config()
        data: dict[str, Any] = {"tui": {"color": False}}
        result = _apply_config(config, data)
        assert result.tui.color is False

    def test_ignores_unknown_fields(self) -> None:
        config = Config()
        data: dict[str, Any] = {"unknown_field": "value"}
        result = _apply_config(config, data)
        assert result.model.id == config.model.id


class TestLoadYaml:
    def test_loads_yaml_file(self, temp_dir: Path) -> None:
        path = temp_dir / "test.yaml"
        path.write_text("model:\n  id: test-id\n")
        result = _load_yaml(path)
        assert result == {"model": {"id": "test-id"}}

    def test_handles_empty_file(self, temp_dir: Path) -> None:
        path = temp_dir / "empty.yaml"
        path.write_text("")
        result = _load_yaml(path)
        assert result == {}


class TestLoadJson:
    def test_loads_json_file(self, temp_dir: Path) -> None:
        path = temp_dir / "test.json"
        path.write_text('{"model": {"id": "test-id"}}')
        result = _load_json(path)
        assert result == {"model": {"id": "test-id"}}


class TestLoadConfigFile:
    def test_returns_empty_for_nonexistent_file(self) -> None:
        result = _load_config_file(None)
        assert result == {}

    def test_loads_json_config(self, temp_dir: Path) -> None:
        path = temp_dir / "config.json"
        path.write_text('{"model": {"id": "test-id"}}')
        result = _load_config_file(path)
        assert result == {"model": {"id": "test-id"}}

    def test_loads_yaml_config(self, temp_dir: Path) -> None:
        path = temp_dir / "config.yaml"
        path.write_text("model:\n  id: test-id\n")
        result = _load_config_file(path)
        assert result == {"model": {"id": "test-id"}}


class TestResetConfig:
    def test_removes_config_files(
        self, mocker: pytest.MockerFixture, temp_dir: Path
    ) -> None:
        mock_dir = temp_dir / "ash-cli"
        mock_dir.mkdir(parents=True)
        (mock_dir / "config.json").touch()
        (mock_dir / "config.yaml").touch()
        mocker.patch.object(
            config_module, "_get_default_config_dir", return_value=mock_dir
        )
        result = reset_config()
        assert len(result) == 2


class TestGetConfig:
    def test_returns_default_config(self, mocker: pytest.MockerFixture) -> None:
        mocker.patch.object(config_module, "_load_env_files", return_value=None)
        result = get_config()
        assert isinstance(result, Config)
        assert result.model.id == "qwen3.5:4b"

    def test_loads_from_file(
        self, mocker: pytest.MockerFixture, temp_dir: Path
    ) -> None:
        mock_dir = temp_dir / "ash-cli"
        mock_dir.mkdir(parents=True)
        config_path = mock_dir / "config.json"
        config_path.write_text('{"model": {"id": "custom-model"}}')
        mocker.patch.object(config_module, "_load_env_files", return_value=None)
        mocker.patch.object(
            config_module, "_get_default_config_dir", return_value=mock_dir
        )
        mocker.patch.object(
            config_module, "_get_default_config_path", return_value=config_path
        )
        result = get_config(path=config_path)
        assert result.model.id == "custom-model"

    def test_applies_args(self, mocker: pytest.MockerFixture) -> None:
        mocker.patch.object(config_module, "_load_env_files", return_value=None)
        args = Args(model="args-model")
        result = get_config(args=args)
        assert result.model.id == "args-model"

    def test_applies_env_vars(self, mocker: pytest.MockerFixture) -> None:
        mocker.patch.dict(os.environ, {"ASH_MODEL": "env-model"})
        mocker.patch.object(config_module, "_load_env_files", return_value=None)
        result = get_config()
        assert result.model.id == "env-model"


class TestModelConfig:
    def test_default_values(self) -> None:
        config = ModelConfig()
        assert config.id == "qwen3.5:4b"
        assert config.api_key == "not-needed"
        assert config.base_url == "http://localhost:8080/v1"
        assert config.temperature == 0.6


class TestAgentConfig:
    def test_default_values(self) -> None:
        config = AgentConfig()
        assert config.description == "CLI assistant that outputs bash commands"
        assert len(config.instructions) == 4


class TestTUIConfig:
    def test_default_values(self) -> None:
        config = TUIConfig()
        assert config.panel_height == 8
        assert config.color is True
