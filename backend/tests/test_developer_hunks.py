from __future__ import annotations

import subprocess
from types import SimpleNamespace

import pytest

from app.api import developer_api

PATCH = """diff --git a/example.py b/example.py
index 1111111..2222222 100644
--- a/example.py
+++ b/example.py
@@ -1,3 +1,3 @@
 one
-two
+second
 three
@@ -8,2 +8,3 @@ seven
 eight
+nine
"""


def test_parse_repo_diff_exposes_independent_hunks():
    files = developer_api._parse_repo_diff(PATCH, staged=False)

    assert len(files) == 1
    assert files[0]["path"] == "example.py"
    assert files[0]["status"] == "modified"
    assert len(files[0]["fingerprint"]) == 64
    assert [hunk["index"] for hunk in files[0]["hunks"]] == [0, 1]
    assert files[0]["hunks"][1]["patch"].startswith("diff --git a/example.py")
    assert "@@ -8,2 +8,3 @@" in files[0]["hunks"][1]["patch"]
    assert "@@ -1,3 +1,3 @@" not in files[0]["hunks"][1]["patch"]


def test_parse_repo_diff_ignores_status_words_inside_hunk_content():
    patch = PATCH.replace("+second", '+message = "deleted file mode 100644"')

    files = developer_api._parse_repo_diff(patch, staged=False)

    assert files[0]["status"] == "modified"


def test_stage_hunk_applies_only_reviewed_patch(monkeypatch, tmp_path):
    file_path = tmp_path / "example.py"
    file_path.write_text("one\nsecond\nthree\n", encoding="utf-8")
    monkeypatch.setattr(developer_api, "_repo_path", lambda _name: tmp_path)
    monkeypatch.setattr(developer_api, "_safe_file_path", lambda _repo, _path: file_path)
    monkeypatch.setattr(developer_api, "_git_output", lambda _repo, *_args: PATCH)
    applied: dict[str, object] = {}

    def run(command, **kwargs):
        applied["command"] = command
        applied["patch"] = kwargs["input"]
        return SimpleNamespace(returncode=0, stderr="")

    monkeypatch.setattr(developer_api.subprocess, "run", run)
    fingerprint = developer_api._parse_repo_diff(PATCH, False)[0]["fingerprint"]

    result = developer_api._stage_repo_hunk("repo", "example.py", 1, fingerprint)

    assert result["success"] is True
    assert applied["command"][-4:] == ["apply", "--cached", "--whitespace=nowarn", "-"]
    assert "@@ -8,2 +8,3 @@" in str(applied["patch"])


def test_stage_hunk_rejects_stale_fingerprint(monkeypatch, tmp_path):
    file_path = tmp_path / "example.py"
    file_path.write_text("one\nsecond\n", encoding="utf-8")
    monkeypatch.setattr(developer_api, "_repo_path", lambda _name: tmp_path)
    monkeypatch.setattr(developer_api, "_safe_file_path", lambda _repo, _path: file_path)
    monkeypatch.setattr(developer_api, "_git_output", lambda _repo, *_args: PATCH)

    with pytest.raises(developer_api.DiffConflictError, match="changed since"):
        developer_api._stage_repo_hunk("repo", "example.py", 0, "stale")


def test_stage_hunk_stages_only_selected_change_in_real_repository(monkeypatch, tmp_path):
    subprocess.run(["git", "init", "-q", str(tmp_path)], check=True)
    subprocess.run(
        ["git", "-C", str(tmp_path), "config", "user.email", "test@example.invalid"], check=True
    )
    subprocess.run(["git", "-C", str(tmp_path), "config", "user.name", "Test"], check=True)
    file_path = tmp_path / "example.py"
    original = "\n".join(f"line {index}" for index in range(1, 16)) + "\n"
    file_path.write_text(original, encoding="utf-8")
    subprocess.run(["git", "-C", str(tmp_path), "add", "example.py"], check=True)
    subprocess.run(["git", "-C", str(tmp_path), "commit", "-qm", "baseline"], check=True)
    changed = original.replace("line 2", "changed 2").replace("line 14", "changed 14")
    file_path.write_text(changed, encoding="utf-8")
    monkeypatch.setattr(developer_api, "_repo_path", lambda _name: tmp_path)
    monkeypatch.setattr(developer_api, "_safe_file_path", lambda _repo, _path: file_path)

    diff = developer_api._get_repo_diffs("repo")["files"][0]
    assert len(diff["hunks"]) == 2

    developer_api._stage_repo_hunk("repo", "example.py", 1, diff["fingerprint"])

    staged = subprocess.run(
        ["git", "-C", str(tmp_path), "diff", "--cached"],
        check=True,
        capture_output=True,
        text=True,
    ).stdout
    unstaged = subprocess.run(
        ["git", "-C", str(tmp_path), "diff"],
        check=True,
        capture_output=True,
        text=True,
    ).stdout
    assert "changed 14" in staged and "changed 2" not in staged
    assert "changed 2" in unstaged and "changed 14" not in unstaged
