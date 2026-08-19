from __future__ import annotations

import json

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
    catalogue = tmp_path / "catalogue.json"
    catalogue.write_text(json.dumps({"version": 1, "modules": []}), encoding="utf-8")
    monkeypatch.setattr(registry, "BUILTIN_SKILL_PATH", builtin)
    monkeypatch.setattr(registry, "CATALOGUE_PATH", catalogue)

    assert registry._discover() == {}
    assert not marker.exists()


def test_catalogue_covers_every_builtin_module():
    entries = registry._catalogue_modules()

    assert entries
    assert all(entry["owner"] for entry in entries)
    assert all(entry["risk"] for entry in entries)
    assert all(isinstance(entry["allowed_roots"], list) for entry in entries)
