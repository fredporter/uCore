from pathlib import Path

from app.api import chat_history_api


def test_chat_history_roundtrip(tmp_path: Path, monkeypatch):
    target = tmp_path / "chat.json"
    monkeypatch.setattr(chat_history_api, "_history_file", lambda: target)
    conversations = [{"id": "one", "title": "Test", "messages": []}]
    chat_history_api._write_history(conversations)
    assert chat_history_api._read_history() == conversations


def test_chat_history_is_bounded(tmp_path: Path, monkeypatch):
    target = tmp_path / "chat.json"
    monkeypatch.setattr(chat_history_api, "_history_file", lambda: target)
    chat_history_api._write_history([{"id": str(index)} for index in range(110)])
    stored = chat_history_api._read_history()
    assert len(stored) == 100
    assert stored[0]["id"] == "10"
