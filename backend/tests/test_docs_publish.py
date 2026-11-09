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


def test_deploy_site_is_retired_without_git_or_filesystem_changes(tmp_path, monkeypatch):
    import subprocess
    def unexpected(*args, **kwargs):
        raise AssertionError("Started Git deployment")
    monkeypatch.setattr(subprocess, 'run', unexpected)
    site = tmp_path / "site"
    result = docs_publish.deploy_site(site_root=site)
    assert result["deployed"] is False
    assert result["error"] == "runtime_deployment_retired"
    assert not site.exists()


def test_external_build_requires_explicit_destination():
    import pytest
    with pytest.raises(ValueError, match="explicit output"):
        docs_publish.build_site()


def test_markdown_to_html_renders_basics():
    html = docs_publish.markdown_to_html("# Title\n\nSome **bold** and `code`.\n")
    assert "<h1>Title</h1>" in html
    assert "<strong>bold</strong>" in html
    assert "<code>code</code>" in html


async def test_docs_publish_api_never_dispatches_build_or_deploy(monkeypatch):
    from aiohttp.test_utils import make_mocked_request

    from app.surfaces.documentation_api import handle_docs_publish
    def unexpected(*args, **kwargs):
        raise AssertionError("Runtime started maintainer publication")
    monkeypatch.setattr(docs_publish, 'build_site', unexpected)
    monkeypatch.setattr(docs_publish, 'deploy_site', unexpected)
    assert (await handle_docs_publish(make_mocked_request('POST', '/api/docs/publish'))).status == 410


async def test_docs_export_probe_is_read_only_and_post_stays_in_user_space(tmp_path, monkeypatch):
    import json
    from unittest.mock import AsyncMock

    from aiohttp.test_utils import make_mocked_request

    from app.surfaces import documentation_api as api
    vault, shared, public = [tmp_path / name for name in ('Vault', 'Shared', 'Public')]
    vault.mkdir()
    (vault / 'note.md').write_text('# Note\n\nKeep this source')
    outside = tmp_path / 'outside.md'
    outside.write_text('OUTSIDE-SOURCE-SENTINEL')
    (vault / 'linked.md').symlink_to(outside)
    monkeypatch.setattr(api.settings, 'vault_root', vault)
    monkeypatch.setattr(api.settings, 'shared_vault_root', shared)
    monkeypatch.setattr(api.settings, 'public_vault_root', public)
    monkeypatch.setattr(api, 'DEFAULT_VAULT_SOURCE', vault)
    output = vault / 'Exports/doclang/notes.jsonl'
    monkeypatch.setattr(api, 'DEFAULT_EXPORT_OUTPUT', output)
    response = await api.handle_docs_export(make_mocked_request('GET', '/api/docs/export'))
    assert response.status == 200
    assert not output.exists()
    request = make_mocked_request('POST', '/api/docs/export')
    request.json = AsyncMock(return_value={})
    response = await api.handle_docs_export(request)
    assert response.status == 200
    assert output.exists()
    assert 'Keep this source' in output.read_text()
    assert 'OUTSIDE-SOURCE-SENTINEL' not in output.read_text()
    request.json = AsyncMock(return_value={'output_path': str(public / 'global-knowledge/canon.jsonl')})
    assert (await api.handle_docs_export(request)).status == 403
    assert not public.exists()
    request.json = AsyncMock(return_value={'source_dir': str(tmp_path)})
    assert (await api.handle_docs_export(request)).status == 403


async def test_jekyll_git_request_is_rejected_before_creating_output(tmp_path, monkeypatch):
    from unittest.mock import AsyncMock, Mock

    from aiohttp.test_utils import make_mocked_request

    from app.api import user_workflow as api
    request = make_mocked_request('POST', '/api/user/workflow/publish-jekyll', payload=Mock(at_eof=lambda: False))
    request.json = AsyncMock(return_value={'content': 'Do not publish', 'execute_git': True})
    assert (await api.handle_user_workflow_publish_jekyll(request)).status == 410


async def test_local_jekyll_preparation_defaults_to_user_vault(tmp_path, monkeypatch):
    import json
    from unittest.mock import AsyncMock, Mock

    from aiohttp.test_utils import make_mocked_request

    from app.api import user_workflow as api
    vault = tmp_path / 'Vault'
    monkeypatch.setattr(api, 'VAULT_LAYERS', [{'id': 'user', 'path': str(vault), 'permissions': 'read_write'}])
    request = make_mocked_request('POST', '/api/user/workflow/publish-jekyll', payload=Mock(at_eof=lambda: False))
    request.json = AsyncMock(return_value={'content': '# Garden notes', 'title': 'Garden', 'slug': 'garden'})
    response = await api.handle_user_workflow_publish_jekyll(request)
    assert response.status == 200
    result = json.loads(response.text)
    assert result['vault_layer'] == 'user'
    assert result['git_publish'] is None
    assert Path(result['path']).is_relative_to(vault.resolve())
    assert 'Garden notes' in Path(result['path']).read_text()
