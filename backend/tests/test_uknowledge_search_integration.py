"""Integration and unit tests for uKnowledge offline search and index engine.

Tests:
1. Multi-tier ranking in LibraryIndex (exact title match > heading > body match).
2. FTS5 snippet extraction with <mark> tags.
3. Dataset and standards searchability (JSON datasets, sovereign reference).
4. uKnowledge status and index endpoints:
   - GET /api/knowledge/status
   - GET /api/knowledge/index/status
   - POST /api/knowledge/index/rebuild
   - GET /api/knowledge/index/coverage
   - GET /api/knowledge/import/status
5. Documentation Wiki search API endpoint:
   - GET /api/docs/wiki/search with queries, vault filters, limit, and error handling.
"""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import patch

import pytest
from aiohttp import web
from aiohttp.test_utils import TestClient, TestServer

from app.knowledge.routes import register_routes
from app.services.library_index import build_index, get_stats, search as library_search
from app.surfaces.documentation_api import register_documentation_routes


# ─── 1. Library Index FTS5 Ranking & Snippet Tests ─────────────────────────


class TestLibraryIndexFtsEngine:
    """Test multi-tier scoring, prefix search, and <mark> snippets."""

    @pytest.fixture(autouse=True)
    def setup_tmp_index(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
        self.index_dir = tmp_path / "indices"
        self.index_db = self.index_dir / "library.db"
        self.vault_dir = tmp_path / "vaults"
        self.vault_dir.mkdir(parents=True, exist_ok=True)

        monkeypatch.setattr("app.services.library_index.INDEX_DIR", self.index_dir)
        monkeypatch.setattr("app.services.library_index.INDEX_DB", self.index_db)

    def _create_files(self, source: str, files: dict[str, str]) -> Path:
        source_dir = self.vault_dir / source
        source_dir.mkdir(parents=True, exist_ok=True)
        for name, content in files.items():
            fpath = source_dir / name
            fpath.parent.mkdir(parents=True, exist_ok=True)
            fpath.write_text(content, encoding="utf-8")
        return source_dir

    def test_multi_tier_ranking_title_over_body(self):
        """Exact title match should rank higher than body-only mentions."""
        # Doc A has term only in deep body text
        # Doc B has term in title
        self._create_files("public", {
            "astrophysics.md": (
                "---\ntitle: General Astrophysics\n---\n"
                "Planetary parameters are studied widely across cosmology."
            ),
            "planetary_parameters.md": (
                "---\ntitle: Planetary Parameters\n---\n"
                "Standard cosmological metric constants and orbit metrics."
            ),
        })

        build_index(vault_paths={"public": self.vault_dir / "public"})

        results = library_search("Planetary Parameters", source="public")
        assert len(results) >= 2
        # Highest ranked result (index 0) must be the exact title match
        assert results[0]["filename"] == "planetary_parameters.md"

    def test_fts5_snippet_extraction(self):
        """Search results contain <mark> tags around query terms."""
        self._create_files("public", {
            "sovereign.md": (
                "---\ntitle: Sovereign Host Reference\n---\n"
                "The host operating system is the authoritative clock and GPS source. "
                "Local hardware telemetry synchronizes offline without cloud leakage."
            ),
        })

        build_index(vault_paths={"public": self.vault_dir / "public"})

        results = library_search("telemetry", source="public")
        assert len(results) == 1
        snippet = results[0].get("snippet", "")
        assert "<mark>telemetry</mark>" in snippet.lower()

    def test_dataset_json_searchability(self):
        """JSON datasets (like world_parameters.json) are indexed and searchable."""
        dataset_content = json.dumps({
            "solar_system": {
                "earth": {
                    "radius_km": 6371.0,
                    "mass_kg": "5.972e24",
                    "atmosphere": "nitrogen-oxygen",
                },
                "jupiter": {
                    "radius_km": 69911.0,
                    "giant": True,
                },
            },
        }, indent=2)

        self._create_files("public", {
            "world_parameters.json": dataset_content,
        })

        build_index(vault_paths={"public": self.vault_dir / "public"})

        results = library_search("atmosphere", source="public")
        assert len(results) == 1
        assert "world_parameters.json" in results[0]["filename"]
        assert "<mark>" in results[0]["snippet"].lower()

    def test_prefix_query_handling(self):
        """As-you-type prefix queries (e.g. 'plan*') match words starting with prefix."""
        self._create_files("public", {
            "planets.md": "# Planets and Moons\nOrbits of our solar system.",
        })

        build_index(vault_paths={"public": self.vault_dir / "public"})

        # Search prefix "plane"
        results = library_search("plane", source="public")
        assert len(results) >= 1
        assert "planets.md" in results[0]["filename"]


# ─── 2. uKnowledge Routes Tests ───────────────────────────────────────────


@pytest.fixture
async def knowledge_client(monkeypatch: pytest.MonkeyPatch, tmp_path: Path):
    """Set up test client for uKnowledge API routes."""
    udos_home = tmp_path / ".udos"
    vault = tmp_path / "Vault"
    shared = tmp_path / "Shared"
    public = tmp_path / "Public"

    udos_home.mkdir(parents=True, exist_ok=True)
    vault.mkdir(parents=True, exist_ok=True)
    shared.mkdir(parents=True, exist_ok=True)
    public.mkdir(parents=True, exist_ok=True)

    monkeypatch.setenv("UDOS_HOME", str(udos_home))
    monkeypatch.setenv("UDOS_USER_VAULT_ROOT", str(vault))
    monkeypatch.setenv("UDOS_SHARED_ROOT", str(shared))
    monkeypatch.setenv("UDOS_PUBLIC_ROOT", str(public))

    index_dir = udos_home / "indices"
    index_db = index_dir / "library.db"
    monkeypatch.setattr("app.services.library_index.INDEX_DIR", index_dir)
    monkeypatch.setattr("app.services.library_index.INDEX_DB", index_db)

    app = web.Application()
    register_routes(app)

    async with TestClient(TestServer(app)) as client:
        yield client


@pytest.mark.asyncio
async def test_knowledge_status_endpoint(knowledge_client):
    """GET /api/knowledge/status returns offline status and engine metadata."""
    resp = await knowledge_client.get("/api/knowledge/status")
    assert resp.status == 200
    data = await resp.json()

    assert data["engine"] == "sqlite_fts5"
    assert data["offline"] is True
    assert data["zero_cloud_leakage"] is True
    assert "database" in data
    assert "total_documents" in data


@pytest.mark.asyncio
async def test_knowledge_index_status_endpoint(knowledge_client):
    """GET /api/knowledge/index/status returns index health."""
    resp = await knowledge_client.get("/api/knowledge/index/status")
    assert resp.status == 200
    data = await resp.json()

    assert "index_status" in data
    assert "total_entries" in data
    assert "by_source" in data
    assert data["is_indexing"] is False


@pytest.mark.asyncio
async def test_knowledge_index_rebuild_endpoint(knowledge_client, tmp_path: Path):
    """POST /api/knowledge/index/rebuild triggers index rebuild."""
    note = tmp_path / "Vault" / "test.md"
    note.write_text("# Test Document\nIndex me.", encoding="utf-8")

    resp = await knowledge_client.post("/api/knowledge/index/rebuild")
    assert resp.status == 200
    data = await resp.json()

    assert data["success"] is True
    assert data["rebuilt"] is True
    assert "timestamp" in data
    assert "total_indexed" in data


@pytest.mark.asyncio
async def test_knowledge_index_coverage_endpoint(knowledge_client):
    """GET /api/knowledge/index/coverage returns zone breakdown."""
    resp = await knowledge_client.get("/api/knowledge/index/coverage")
    assert resp.status == 200
    data = await resp.json()

    coverage = data.get("coverage", {})
    assert "personal_vault" in coverage
    assert "shared_vault" in coverage
    assert "public_canon" in coverage
    assert "manuals" in coverage
    assert coverage["personal_vault"]["accessible"] is True


@pytest.mark.asyncio
async def test_knowledge_import_status_endpoint(knowledge_client):
    """GET /api/knowledge/import/status returns empty/idle status."""
    resp = await knowledge_client.get("/api/knowledge/import/status")
    assert resp.status == 200
    data = await resp.json()

    assert data["status"] == "idle"
    assert data["in_progress"] is False
    assert data["last_import"] is None


# ─── 3. Documentation Wiki Search API Tests ───────────────────────────────


@pytest.fixture
async def docs_client(monkeypatch: pytest.MonkeyPatch, tmp_path: Path):
    """Set up test client for Documentation surface routes."""
    udos_home = tmp_path / ".udos"
    vault = tmp_path / "Vault"
    shared = tmp_path / "Shared"
    public = tmp_path / "Public"

    udos_home.mkdir(parents=True, exist_ok=True)
    vault.mkdir(parents=True, exist_ok=True)
    shared.mkdir(parents=True, exist_ok=True)
    public.mkdir(parents=True, exist_ok=True)

    index_dir = udos_home / "indices"
    index_db = index_dir / "library.db"

    monkeypatch.setattr("app.services.library_index.INDEX_DIR", index_dir)
    monkeypatch.setattr("app.services.library_index.INDEX_DB", index_db)

    # Seed test content and build index
    test_note = public / "standards" / "tokens.md"
    test_note.parent.mkdir(parents=True, exist_ok=True)
    test_note.write_text(
        "---\ntitle: USX Tokens\n---\nUSX standard design tokens and palettes.",
        encoding="utf-8",
    )

    build_index(vault_paths={"public": public})

    app = web.Application()
    register_documentation_routes(app)

    async with TestClient(TestServer(app)) as client:
        yield client


@pytest.mark.asyncio
async def test_docs_wiki_search_requires_query(docs_client):
    """GET /api/docs/wiki/search returns 400 when q is missing or empty."""
    resp = await docs_client.get("/api/docs/wiki/search")
    assert resp.status == 400
    data = await resp.json()
    assert "error" in data

    resp_blank = await docs_client.get("/api/docs/wiki/search?q=")
    assert resp_blank.status == 400


@pytest.mark.asyncio
async def test_docs_wiki_search_returns_formatted_results(docs_client):
    """GET /api/docs/wiki/search?q=USX returns matched results with metadata."""
    resp = await docs_client.get("/api/docs/wiki/search?q=USX")
    assert resp.status == 200
    data = await resp.json()

    assert data["query"] == "USX"
    assert data["count"] >= 1
    assert len(data["results"]) >= 1

    first = data["results"][0]
    assert "id" in first
    assert "title" in first
    assert "filename" in first
    assert "path" in first
    assert "rel_path" in first
    assert "source" in first
    assert "badge" in first
    assert "snippet" in first
    assert first["source"] == "public"
    assert first["badge"] == "~/Public"


@pytest.mark.asyncio
async def test_docs_wiki_search_vault_filtering(docs_client):
    """GET /api/docs/wiki/search filters results by vault."""
    # Searching within user vault when item is in public vault should return 0
    resp = await docs_client.get("/api/docs/wiki/search?q=USX&vault=personal")
    assert resp.status == 200
    data = await resp.json()
    assert data["count"] == 0

    # Searching within public vault should return the item
    resp_pub = await docs_client.get("/api/docs/wiki/search?q=USX&vault=public")
    assert resp_pub.status == 200
    data_pub = await resp_pub.json()
    assert data_pub["count"] >= 1
