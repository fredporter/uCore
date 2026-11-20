"""Tests for Publishing Lane — Local First Library Delivery.

Covers:
- Successful binder compilation and correct Tomb output location.
- Validation that private front‑matter fields ('private_author_key') are stripped.
- Handling of missing or malformed binder data (error response / exceptions).
"""

from __future__ import annotations

import json
import sys
import types
from pathlib import Path

import pytest
from aiohttp import web
from aiohttp.test_utils import make_mocked_request

from app.api import publish_api
from app.services import publish_service


@pytest.fixture(autouse=True)
def publishing_identity(monkeypatch):
    identity = {
        "authenticated": True,
        "active_profile_id": "fixture-wizard",
        "active_profile": {"role": "wizard"},
    }
    monkeypatch.setattr(publish_api, "get_full_identity", lambda: identity)
    return identity


async def request_fixture_export(headers=None):
    app = web.Application()
    publish_api.register_publish_routes(app)
    request = make_mocked_request("POST", "/api/publish/binder", headers=headers, app=app)
    route = await app.router.resolve(request)
    return await route.handler(request)


async def test_publish_binder_success(tmp_path, monkeypatch):
    # Mock fixture path to use temp fixture
    mock_fixture_path = tmp_path / "fixture.json"
    mock_output_dir = tmp_path / "tombs"

    fixture_data = {
        "fixture_revision": "2026-11-19",
        "type": "library_delivery",
        "id": "test-library",
        "binder": {
            "binder_id": "test-binder",
            "title": "Test Sanctuary Guide",
            "edition_num": 1,
            "documents": [
                {
                    "filename": "doc1.md",
                    "title": "Doc 1",
                    "content": "---\ntitle: Doc 1\nauthor: Test Author\nprivate_author_key: SECRET-KEY-123\n---\n# Hello World\nSome content here."
                }
            ]
        }
    }
    mock_fixture_path.write_text(json.dumps(fixture_data), encoding="utf-8")

    def compile_edition_to_static(*, edition_markdown, output_dir, **_kwargs):
        markdown_path = output_dir / "edition.md"
        markdown_path.write_text(edition_markdown, encoding="utf-8")
        (output_dir / "index.html").write_text("<html></html>", encoding="utf-8")
        return {"markdown_path": str(markdown_path)}

    publishing = types.ModuleType("udos_publishing")
    publishing.__path__ = []
    source = types.ModuleType("udos_publishing.src")
    source.__path__ = []
    compiler = types.ModuleType("udos_publishing.src.compiler")
    compiler.compile_edition_to_static = compile_edition_to_static
    publishing.src = source
    source.compiler = compiler
    monkeypatch.setitem(sys.modules, "udos_publishing", publishing)
    monkeypatch.setitem(sys.modules, "udos_publishing.src", source)
    monkeypatch.setitem(sys.modules, "udos_publishing.src.compiler", compiler)

    monkeypatch.setattr(publish_service, "FIXTURE_PATH", mock_fixture_path)
    monkeypatch.setattr(publish_service, "DEFAULT_TOMB_OUTPUT", mock_output_dir)

    resp = await request_fixture_export()
    assert resp.status == 200
    data = json.loads(resp.text)
    assert data["type"] == "publish_result"
    assert data["title"] == "Test Sanctuary Guide"
    assert "tomb_path" in data

    # Verify output files exist and private frontmatter is stripped
    out_dir = Path(data["tomb_path"])
    assert (out_dir / "index.html").exists()
    markdown_files = list(out_dir.glob("*.md"))
    assert len(markdown_files) > 0

    md_content = markdown_files[0].read_text(encoding="utf-8")
    assert "private_author_key" not in md_content
    assert "SECRET-KEY-123" not in md_content
    assert "Hello World" in md_content


async def test_publish_binder_missing_fixture(monkeypatch):
    monkeypatch.setattr(publish_service, "FIXTURE_PATH", Path("/nonexistent/path/fixture.json"))

    resp = await request_fixture_export()
    assert resp.status == 404
    assert "error" in json.loads(resp.text)


async def test_publish_binder_malformed_fixture(tmp_path, monkeypatch):
    mock_fixture_path = tmp_path / "fixture.json"
    mock_fixture_path.write_text(json.dumps({"type": "bad"}), encoding="utf-8")

    monkeypatch.setattr(publish_service, "FIXTURE_PATH", mock_fixture_path)

    resp = await request_fixture_export()
    assert resp.status == 422
    assert "error" in json.loads(resp.text)



async def test_publish_binder_requires_wizard(publishing_identity, monkeypatch):
    publishing_identity["active_profile"]["role"] = "knight"

    def unexpected_compile():
        pytest.fail("Non-Wizard should be denied before compilation")

    monkeypatch.setattr(publish_service, "compile_binder_to_tomb", unexpected_compile)
    assert (await request_fixture_export()).status == 403


async def test_publish_binder_requires_local_authenticated_profile(publishing_identity):
    with pytest.raises(web.HTTPForbidden):
        await request_fixture_export(headers={"Origin": "https://example.org"})
    publishing_identity["authenticated"] = False
    with pytest.raises(web.HTTPUnauthorized):
        await request_fixture_export()
