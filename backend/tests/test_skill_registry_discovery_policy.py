from __future__ import annotations

from app.skills import registry


def test_registry_does_not_scan_runtime_user_python(monkeypatch, tmp_path):
    marker = tmp_path / "executed"
    user_skills = tmp_path / "skills"
    user_skills.mkdir()
    (user_skills / "side_effect.py").write_text(
        f"from pathlib import Path\nPath({str(marker)!r}).write_text('ran')\n",
        encoding="utf-8",
    )
    builtin = tmp_path / "builtin"
    builtin.mkdir()
    monkeypatch.setattr(registry, "BUILTIN_SKILL_PATH", builtin)

    assert registry._discover() == {}
    assert not marker.exists()
