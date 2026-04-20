from __future__ import annotations

import json  # noqa: UP017
import os
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from .config import _get_default_config_dir


@dataclass
class Message:
    role: str
    content: str
    timestamp: str = field(default_factory=lambda: datetime.now(UTC).isoformat())


@dataclass
class Usage:
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0
    total_latency: float = 0.0
    api_call_count: int = 0

    def add(self, other: Usage) -> None:
        self.prompt_tokens += other.prompt_tokens
        self.completion_tokens += other.completion_tokens
        self.total_tokens += other.total_tokens
        self.total_latency += other.total_latency
        self.api_call_count += other.api_call_count


@dataclass
class Session:
    id: str
    name: str
    created_at: str
    updated_at: str
    messages: list[Message] = field(default_factory=list)
    usage: Usage = field(default_factory=Usage)
    model: str = "qwen3.5:4b"
    temperature: float = 0.6
    max_tokens: int = 4096
    base_url: str = "http://localhost:8080/v1"

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "messages": [
                {"role": m.role, "content": m.content, "timestamp": m.timestamp}
                for m in self.messages
            ],
            "usage": {
                "prompt_tokens": self.usage.prompt_tokens,
                "completion_tokens": self.usage.completion_tokens,
                "total_tokens": self.usage.total_tokens,
                "total_latency": self.usage.total_latency,
                "api_call_count": self.usage.api_call_count,
            },
            "model": self.model,
            "temperature": self.temperature,
            "max_tokens": self.max_tokens,
            "base_url": self.base_url,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Session:
        messages = [
            Message(
                role=m["role"], content=m["content"], timestamp=m.get("timestamp", "")
            )
            for m in data.get("messages", [])
        ]
        usage_data = data.get("usage", {})
        usage = Usage(
            prompt_tokens=usage_data.get("prompt_tokens", 0),
            completion_tokens=usage_data.get("completion_tokens", 0),
            total_tokens=usage_data.get("total_tokens", 0),
            total_latency=usage_data.get("total_latency", 0.0),
            api_call_count=usage_data.get("api_call_count", 0),
        )
        return cls(
            id=data["id"],
            name=data["name"],
            created_at=data["created_at"],
            updated_at=data["updated_at"],
            messages=messages,
            usage=usage,
            model=data.get("model", "qwen3.5:4b"),
            temperature=data.get("temperature", 0.6),
            max_tokens=data.get("max_tokens", 4096),
            base_url=data.get("base_url", "http://localhost:8080/v1"),
        )


def _get_sessions_dir() -> Path:
    base = _get_default_config_dir()
    return base / "sessions"


def _ensure_sessions_dir() -> Path:
    dir_path = _get_sessions_dir()
    dir_path.mkdir(parents=True, exist_ok=True)
    return dir_path


def _session_path(session_id: str) -> Path:
    return _ensure_sessions_dir() / f"{session_id}.json"


def create_session(
    name: str,
    model: str = "qwen3.5:4b",
    temperature: float = 0.6,
    max_tokens: int = 4096,
    base_url: str = "http://localhost:8080/v1",
) -> Session:
    now = datetime.now(UTC).isoformat()
    session_id = os.urandom(16).hex()
    session = Session(
        id=session_id,
        name=name,
        created_at=now,
        updated_at=now,
        model=model,
        temperature=temperature,
        max_tokens=max_tokens,
        base_url=base_url,
    )
    save_session(session)
    return session


def save_session(session: Session) -> None:
    session.updated_at = datetime.now(UTC).isoformat()
    path = _session_path(session.id)
    with open(path, "w") as f:
        json.dump(session.to_dict(), f, indent=2)


def load_session(session_id: str) -> Session | None:
    path = _session_path(session_id)
    if not path.exists():
        return None
    with open(path) as f:
        data = json.load(f)
    return Session.from_dict(data)


def delete_session(session_id: str) -> bool:
    path = _session_path(session_id)
    if path.exists():
        path.unlink()
        return True
    return False


def rename_session(session_id: str, new_name: str) -> Session | None:
    session = load_session(session_id)
    if session is None:
        return None
    session.name = new_name
    save_session(session)
    return session


def list_sessions() -> list[Session]:
    sessions_dir = _ensure_sessions_dir()
    sessions: list[Session] = []
    for path in sessions_dir.glob("*.json"):
        try:
            with open(path) as f:
                data = json.load(f)
            sessions.append(Session.from_dict(data))
        except Exception:
            continue
    sessions.sort(key=lambda s: s.created_at, reverse=True)
    return sessions


def get_command_history() -> list[str]:
    sessions = list_sessions()
    history: list[str] = []
    seen: set[str] = set()
    for s in sessions:
        for m in s.messages:
            if m.role == "user" and m.content.strip() and m.content not in seen:
                if not m.content.startswith("/"):
                    history.append(m.content.strip())
                    seen.add(m.content)
    return history


def get_total_usage() -> Usage:
    sessions = list_sessions()
    total = Usage()
    for s in sessions:
        total.add(s.usage)
    return total


def export_session(session_id: str, path: Path) -> bool:
    session = load_session(session_id)
    if session is None:
        return False
    with open(path, "w") as f:
        json.dump(session.to_dict(), f, indent=2)
    return True


def import_session(path: Path) -> Session | None:
    if not path.exists():
        return None
    with open(path) as f:
        data = json.load(f)
    old_id = data.get("id")
    data["id"] = os.urandom(16).hex()
    data["created_at"] = datetime.now(UTC).isoformat()
    data["updated_at"] = datetime.now(UTC).isoformat()
    if old_id and data.get("name"):
        data["name"] = f"{data['name']} (imported)"
    session = Session.from_dict(data)
    save_session(session)
    return session
