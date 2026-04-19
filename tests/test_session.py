from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import patch

import pytest

from ash_cli.session import (
    Message,
    Session,
    _ensure_sessions_dir,
    _get_sessions_dir,
    _session_path,
    create_session,
    delete_session,
    export_session,
    import_session,
    list_sessions,
    load_session,
    rename_session,
    save_session,
)


@pytest.fixture
def mock_sessions_dir(temp_dir: Path) -> Path:
    sessions_dir = temp_dir / "ash-cli" / "sessions"
    sessions_dir.mkdir(parents=True)
    return sessions_dir


class TestMessage:
    def test_default_timestamp(self) -> None:
        msg = Message(role="user", content="hello")
        assert msg.role == "user"
        assert msg.content == "hello"
        assert msg.timestamp != ""

    def test_custom_timestamp(self) -> None:
        msg = Message(
            role="user", content="hello", timestamp="2024-01-01T00:00:00+00:00"
        )
        assert msg.timestamp == "2024-01-01T00:00:00+00:00"


class TestSession:
    def test_to_dict(self, sample_session: Session) -> None:
        result = sample_session.to_dict()
        assert result["id"] == "test-id-123"
        assert result["name"] == "Test Session"
        assert len(result["messages"]) == 2

    def test_from_dict(self, session_dict: dict) -> None:
        session = Session.from_dict(session_dict)
        assert session.id == "test-id-123"
        assert session.name == "Test Session"
        assert len(session.messages) == 2

    def test_from_dict_defaults(self) -> None:
        data = {
            "id": "id",
            "name": "name",
            "created_at": "2024-01-01T00:00:00+00:00",
            "updated_at": "2024-01-01T00:00:00+00:00",
        }
        session = Session.from_dict(data)
        assert session.model == "qwen3.5:4b"
        assert session.temperature == 0.6
        assert session.max_tokens == 4096


class TestGetSessionsDir:
    def test_returns_sessions_dir(
        self, temp_dir: Path, mock_sessions_dir: Path
    ) -> None:
        with patch(
            "ash_cli.session._get_default_config_dir", return_value=temp_dir / "ash-cli"
        ):
            result = _get_sessions_dir()
            assert result.name == "sessions"


class TestEnsureSessionsDir:
    def test_creates_dir(self, temp_dir: Path, mock_sessions_dir: Path) -> None:
        with patch(
            "ash_cli.session._get_default_config_dir", return_value=temp_dir / "ash-cli"
        ):
            _ensure_sessions_dir()
        assert mock_sessions_dir.exists()


class TestSessionPath:
    def test_returns_json_path(self) -> None:
        path = _session_path("abc123")
        assert path.name == "abc123.json"


class TestCreateSession:
    def test_creates_session_file(
        self, temp_dir: Path, mock_sessions_dir: Path
    ) -> None:
        with patch(
            "ash_cli.session._get_default_config_dir", return_value=temp_dir / "ash-cli"
        ):
            session = create_session("Test", "model", 0.7, 2048, "http://test:8080/v1")
        assert session.name == "Test"
        assert session.model == "model"
        assert session.temperature == 0.7
        assert session.max_tokens == 2048
        assert (mock_sessions_dir / f"{session.id}.json").exists()

    def test_generates_unique_id(self, temp_dir: Path, mock_sessions_dir: Path) -> None:
        with patch(
            "ash_cli.session._get_default_config_dir", return_value=temp_dir / "ash-cli"
        ):
            session1 = create_session("Test1")
            session2 = create_session("Test2")
        assert session1.id != session2.id


class TestSaveSession:
    def test_saves_to_file(
        self, temp_dir: Path, mock_sessions_dir: Path, sample_session: Session
    ) -> None:
        with patch(
            "ash_cli.session._get_default_config_dir", return_value=temp_dir / "ash-cli"
        ):
            save_session(sample_session)
        path = mock_sessions_dir / f"{sample_session.id}.json"
        assert path.exists()


class TestLoadSession:
    def test_loads_existing_session(
        self, temp_dir: Path, mock_sessions_dir: Path, sample_session: Session
    ) -> None:
        path = mock_sessions_dir / f"{sample_session.id}.json"
        with open(path, "w") as f:
            json.dump(sample_session.to_dict(), f)
        with patch(
            "ash_cli.session._get_default_config_dir", return_value=temp_dir / "ash-cli"
        ):
            result = load_session(sample_session.id)
        assert result is not None
        assert result.id == sample_session.id

    def test_returns_none_for_missing(
        self, temp_dir: Path, mock_sessions_dir: Path
    ) -> None:
        with patch(
            "ash_cli.session._get_default_config_dir", return_value=temp_dir / "ash-cli"
        ):
            result = load_session("nonexistent")
        assert result is None


class TestDeleteSession:
    def test_deletes_existing_session(
        self, temp_dir: Path, mock_sessions_dir: Path, sample_session: Session
    ) -> None:
        path = mock_sessions_dir / f"{sample_session.id}.json"
        path.touch()
        with patch(
            "ash_cli.session._get_default_config_dir", return_value=temp_dir / "ash-cli"
        ):
            result = delete_session(sample_session.id)
        assert result is True
        assert not path.exists()

    def test_returns_false_for_missing(
        self, temp_dir: Path, mock_sessions_dir: Path
    ) -> None:
        with patch(
            "ash_cli.session._get_default_config_dir", return_value=temp_dir / "ash-cli"
        ):
            result = delete_session("nonexistent")
        assert result is False


class TestRenameSession:
    def test_renames_existing_session(
        self, temp_dir: Path, mock_sessions_dir: Path, sample_session: Session
    ) -> None:
        path = mock_sessions_dir / f"{sample_session.id}.json"
        with open(path, "w") as f:
            json.dump(sample_session.to_dict(), f)
        with patch(
            "ash_cli.session._get_default_config_dir", return_value=temp_dir / "ash-cli"
        ):
            result = rename_session(sample_session.id, "New Name")
        assert result is not None
        assert result.name == "New Name"

    def test_returns_none_for_missing(
        self, temp_dir: Path, mock_sessions_dir: Path
    ) -> None:
        with patch(
            "ash_cli.session._get_default_config_dir", return_value=temp_dir / "ash-cli"
        ):
            result = rename_session("nonexistent", "New Name")
        assert result is None


class TestListSessions:
    def test_lists_sessions(
        self, temp_dir: Path, mock_sessions_dir: Path, sample_session: Session
    ) -> None:
        path = mock_sessions_dir / f"{sample_session.id}.json"
        with open(path, "w") as f:
            json.dump(sample_session.to_dict(), f)
        with patch(
            "ash_cli.session._get_default_config_dir", return_value=temp_dir / "ash-cli"
        ):
            result = list_sessions()
        assert len(result) == 1

    def test_returns_empty_for_empty_dir(
        self, temp_dir: Path, mock_sessions_dir: Path
    ) -> None:
        with patch(
            "ash_cli.session._get_default_config_dir", return_value=temp_dir / "ash-cli"
        ):
            result = list_sessions()
        assert result == []

    def test_sorts_by_created_at(self, temp_dir: Path, mock_sessions_dir: Path) -> None:
        session1 = Session(
            id="id1",
            name="name1",
            created_at="2024-01-02T00:00:00+00:00",
            updated_at="2024-01-02T00:00:00+00:00",
        )
        session2 = Session(
            id="id2",
            name="name2",
            created_at="2024-01-01T00:00:00+00:00",
            updated_at="2024-01-01T00:00:00+00:00",
        )
        with open(mock_sessions_dir / "id1.json", "w") as f:
            json.dump(session1.to_dict(), f)
        with open(mock_sessions_dir / "id2.json", "w") as f:
            json.dump(session2.to_dict(), f)
        with patch(
            "ash_cli.session._get_default_config_dir", return_value=temp_dir / "ash-cli"
        ):
            result = list_sessions()
        assert len(result) == 2
        assert result[0].created_at > result[1].created_at


class TestExportSession:
    def test_exports_to_path(
        self, temp_dir: Path, mock_sessions_dir: Path, sample_session: Session
    ) -> None:
        path = mock_sessions_dir / f"{sample_session.id}.json"
        with open(path, "w") as f:
            json.dump(sample_session.to_dict(), f)
        export_path = temp_dir / "export.json"
        with patch(
            "ash_cli.session._get_default_config_dir", return_value=temp_dir / "ash-cli"
        ):
            result = export_session(sample_session.id, export_path)
        assert result is True
        assert export_path.exists()

    def test_returns_false_for_missing(
        self, temp_dir: Path, mock_sessions_dir: Path
    ) -> None:
        export_path = temp_dir / "export.json"
        with patch(
            "ash_cli.session._get_default_config_dir", return_value=temp_dir / "ash-cli"
        ):
            result = export_session("nonexistent", export_path)
        assert result is False


class TestImportSession:
    def test_imports_from_path(
        self, temp_dir: Path, mock_sessions_dir: Path, sample_session: Session
    ) -> None:
        import_path = temp_dir / "import.json"
        with open(import_path, "w") as f:
            json.dump(sample_session.to_dict(), f)
        with patch(
            "ash_cli.session._get_default_config_dir", return_value=temp_dir / "ash-cli"
        ):
            result = import_session(import_path)
        assert result is not None
        assert result.id != sample_session.id
        assert result.name == f"{sample_session.name} (imported)"

    def test_returns_none_for_missing(
        self, temp_dir: Path, mock_sessions_dir: Path
    ) -> None:
        import_path = temp_dir / "nonexistent.json"
        with patch(
            "ash_cli.session._get_default_config_dir", return_value=temp_dir / "ash-cli"
        ):
            result = import_session(import_path)
        assert result is None
