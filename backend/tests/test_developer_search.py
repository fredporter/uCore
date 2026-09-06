from app.api import developer_api


def test_repository_search_is_bounded_and_literal(monkeypatch, tmp_path):
    monkeypatch.setattr(developer_api, "_repo_path", lambda _name: tmp_path)
    captured = {}

    def run(command, **kwargs):
        captured["command"] = command
        return type(
            "Result",
            (),
            {"returncode": 0, "stdout": "src/app.py:4:8:literal result\n", "stderr": ""},
        )()

    monkeypatch.setattr(developer_api.subprocess, "run", run)
    matches = developer_api._search_repo("uCore", "$(unsafe)", 999)
    assert captured["command"][-2:] == ["$(unsafe)", "."]
    assert "--fixed-strings" in captured["command"]
    assert captured["command"][captured["command"].index("--max-count") + 1] == "100"
    assert matches == [{"path": "src/app.py", "line": 4, "column": 8, "preview": "literal result"}]


def test_repository_search_rejects_empty_query(monkeypatch, tmp_path):
    monkeypatch.setattr(developer_api, "_repo_path", lambda _name: tmp_path)
    try:
        developer_api._search_repo("uCore", "")
    except ValueError as exc:
        assert "query" in str(exc)
    else:
        raise AssertionError("empty query was accepted")
