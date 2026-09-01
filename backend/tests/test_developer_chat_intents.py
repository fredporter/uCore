from app.api import developer_api


def test_list_repos_intent_executes_read_contract(monkeypatch):
    monkeypatch.setattr(
        developer_api,
        "_list_repos",
        lambda scope="code": [
            {"name": "uCore", "branch": "main", "dirty": False},
            {"name": "uCode", "branch": "codex/runtime", "dirty": True},
        ],
    )

    response = developer_api._execute_developer_read_intent("list repos")

    assert "Found 2 repositories" in response
    assert "**uCore** — `main` (clean)" in response
    assert "**uCode** — `codex/runtime` (dirty)" in response


def test_unknown_intent_remains_advisory():
    assert developer_api._execute_developer_read_intent("explain this function") is None
