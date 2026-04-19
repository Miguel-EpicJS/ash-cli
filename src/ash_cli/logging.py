from __future__ import annotations

import json
import logging as stdlib_logging
import os
import sys
from dataclasses import dataclass, field
from enum import IntEnum
from pathlib import Path
from typing import Any, Literal

from dotenv import load_dotenv


class Level(IntEnum):
    DEBUG = 10
    INFO = 20
    WARNING = 30
    ERROR = 40


@dataclass
class LoggingConfig:
    level: Level = Level.INFO
    file: Path | None = None
    format: Literal["text", "json"] = "text"
    max_bytes: int = 10_000_000
    backup_count: int = 3


class JsonFormatter(stdlib_logging.Formatter):
    def __init__(self) -> None:
        super().__init__()

    def format(self, record: stdlib_logging.LogRecord) -> str:
        log_data: dict[str, Any] = {
            "timestamp": self.formatTime(record),
            "level": record.levelname,
            "name": record.name,
            "message": record.getMessage(),
        }
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)
        return json.dumps(log_data)


class TextFormatter(stdlib_logging.Formatter):
    def __init__(
        self,
        fmt: str = "%(asctime)s :: %(levelname)s :: %(name)s :: %(message)s",
    ) -> None:
        super().__init__(fmt=fmt)


class RotatingFileHandler(stdlib_logging.Handler):
    def __init__(
        self,
        filename: Path,
        max_bytes: int = 10_000_000,
        backup_count: int = 3,
    ) -> None:
        super().__init__()
        self.filename = filename
        self.max_bytes = max_bytes
        self.backup_count = backup_count
        self._size: int = 0
        self._open_file()

    def _open_file(self) -> None:
        self._file = open(self.filename, "a")
        self._file.seek(0, 2)
        self._size = self._file.tell()

    def _rotate(self) -> None:
        self._file.close()
        for i in range(self.backup_count - 1, 0, -1):
            src = self.filename.with_suffix(f".{i}")
            dst = self.filename.with_suffix(f".{i + 1}")
            if src.exists():
                src.rename(dst)
        self.filename.rename(self.filename.with_suffix(".1"))
        self._open_file()

    def emit(self, record: stdlib_logging.LogRecord) -> None:
        try:
            msg = self.format(record)
            if isinstance(msg, bytes):
                msg = msg.decode("utf-8")
            msg += "\n"
            msg_bytes = msg.encode("utf-8")
            if self._size + len(msg_bytes) > self.max_bytes:
                self._rotate()
            self._file.write(msg)
            self._size += len(msg_bytes)
        except Exception:
            self.handleError(record)

    def close(self) -> None:
        self._file.close()
        super().close()


class Logger:
    _instance: Logger | None = None
    _config: LoggingConfig = field(default_factory=LoggingConfig)
    _logger: stdlib_logging.Logger | None = None

    def __new__(cls) -> Logger:
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    @property
    def config(self) -> LoggingConfig:
        return self._config

    def configure(self, config: LoggingConfig) -> None:
        self._config = config
        if self._logger is not None:
            self._logger.setLevel(config.level)
            self._logger.handlers.clear()
            self._setup_handlers()

    def _setup_handlers(self) -> None:
        if not self._logger:
            return

        console_handler = stdlib_logging.StreamHandler(sys.stderr)
        if self._config.format == "json":
            console_handler.setFormatter(JsonFormatter())
        else:
            console_handler.setFormatter(TextFormatter())
        self._logger.addHandler(console_handler)

        if self._config.file:
            self._config.file.parent.mkdir(parents=True, exist_ok=True)
            file_handler = RotatingFileHandler(
                self._config.file,
                self._config.max_bytes,
                self._config.backup_count,
            )
            if self._config.format == "json":
                file_handler.setFormatter(JsonFormatter())
            else:
                file_handler.setFormatter(TextFormatter())
            self._logger.addHandler(file_handler)

    def _ensure_logger(self) -> stdlib_logging.Logger:
        if self._logger is None:
            self._logger = stdlib_logging.getLogger("ash-cli")
            self._logger.setLevel(self._config.level)
            self._setup_handlers()
        return self._logger

    def debug(self, message: str) -> None:
        self._ensure_logger().debug(message)

    def info(self, message: str) -> None:
        self._ensure_logger().info(message)

    def warning(self, message: str) -> None:
        self._ensure_logger().warning(message)

    def error(self, message: str) -> None:
        self._ensure_logger().error(message)


def _find_project_root() -> Path:
    current = Path(__file__).resolve().parent
    for parent in current.parents:
        if (parent / "pyproject.toml").exists():
            return parent
    return current


def _load_env_files() -> None:
    env_paths = [
        _find_project_root() / ".env",
        _get_default_log_dir() / ".env",
    ]
    for env_path in env_paths:
        if env_path.exists():
            load_dotenv(env_path)
            return


def _get_default_log_dir() -> Path:
    if sys.platform == "win32":
        base = Path(os.environ.get("APPDATA", Path.home() / ".ash-cli"))
    elif sys.platform == "darwin":
        base = Path.home() / "Library" / "Application Support"
    else:
        base = Path.home() / ".config"
    return base / "ash-cli"


def _apply_env_logging(config: LoggingConfig) -> LoggingConfig:
    if log_level := os.environ.get("ASH_LOG_LEVEL"):
        config.level = Level[log_level.upper()]
    if log_file := os.environ.get("ASH_LOG_FILE"):
        config.file = Path(log_file)
    if log_format := os.environ.get("ASH_LOG_FORMAT"):
        config.format = log_format  # type: ignore[assignment]
    return config


def get_logging_config() -> LoggingConfig:
    _load_env_files()
    config = LoggingConfig()
    return _apply_env_logging(config)


def init_logging(config: LoggingConfig | None = None) -> Logger:
    if config is None:
        config = get_logging_config()
    logger = Logger()
    logger.configure(config)
    return logger
