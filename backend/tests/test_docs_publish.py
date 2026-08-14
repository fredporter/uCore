"""Tests for the docs-site publish pipeline."""
from __future__ import annotations

import json
from pathlib import Path

from app.services import docs_publish


def _make_mirror(root: Path) -> Path:
    """Create a small fake mirror with a _mirror.json index."""
    mirror = root / "mirror"
    (mirror / "uCore").mkdir(parents=True)
    (mirror / "uCore" / "README.md").write_text("# Readme\n\nHello **world**.\n", encoding="utf-8")
    (mirror / "uCode").mkdir(parents=True)
    (mirror / "uCode" / "guide.md").write_text("# Guide\n\n- one\n- two\n", encoding="utf-8")

    index = {
        "synced_at": "2026-08-14T00:00:00+00:00",
        "total_files": 2,
        "sources": [],
        "entries": [
            {"source_repo": "uCore", "source_path": "README.md", "mirrored_path": "uCore/README.md", "git_sha": "abc", "size": 10},
            {"source_repo": "uCode", "source_path": "guide.md", "mirrored_path": "uCode/guide.md", "git_sha": "def", "size": 10},
        ],
    }
    (mirror / "_mirror.json").write_text(json.dumps(index), encoding="utf-8")
    return mirror


def test_build_site_generates_pages(tmp_path: Path):
    mirror = _make_mirror(tmp_path)
    site = tmp_path / "site"

    result = docs_publish.build_site(mirror_root=mirror, site_root=site)

    assert result["status"] == "ok"
    assert result["total_files"] == 2
    assert result["rendered_pages"] == 2

    assert (site / "index.html").exists()
    assert (site / "sitemap.html").exists()
    assert (site / "assets" / "style.css").exists()
    assert (site / "docs" / "uCore" / "README.md").exists()
    assert (site / "docs" / "uCore" / "README.html").exists()
    assert (site / "docs" / "uCode" / "guide.html").exists()
    assert (site / "docs" / "uCore" / "index.html").exists()

    html_page = (site / "docs" / "uCore" / "README.html").read_text(encoding="utf-8")
    assert "<strong>world</strong>" in html_page

    status = json.loads((site / "publish.json").read_text(encoding="utf-8"))
    assert status["repos"] == {"uCode": 1, "uCore": 1}


def test_publish_status_not_built(tmp_path: Path):
    status = docs_publish.publish_status(site_root=tmp_path / "none")
    assert status["status"] == "not-built"


def test_deploy_site_not_a_git_repo(tmp_path: Path):
    site = tmp_path / "site"
    site.mkdir()
    result = docs_publish.deploy_site(site_root=site)
    assert result["deployed"] is False
    assert result["reason"] == "site_root is not a git repository"


def test_markdown_to_html_renders_basics():
    html = docs_publish.markdown_to_html("# Title\n\nSome **bold** and `code`.\n")
    assert "<h1>Title</h1>" in html
    assert "<strong>bold</strong>" in html
    assert "<code>code</code>" in html
