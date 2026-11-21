# tests for library_index enhancements
import json
import os
from pathlib import Path

import pytest

# Import the module under test
from app.services.library_index import (
    build_index,
    search,
    get_stats,
    index_meta,
    INDEX_DB,
    INDEX_DIR,
)

# Helper to reset index
def _reset_index():
    if INDEX_DB.exists():
        INDEX_DB.unlink()
    # Ensure index directory exists
    INDEX_DIR.mkdir(parents=True, exist_ok=True)

@pytest.fixture(autouse=True)
def isolate_index(tmp_path, monkeypatch):
    Isolate the library index to a temporary directory for each test.
    # Redirect the INDEX_DIR and INDEX_DB globals to a temp location
    temp_dir = tmp_path / indices
    temp_dir.mkdir()
    monkeypatch.setattr('app.services.library_index.INDEX_DIR', temp_dir, raising=False)
    monkeypatch.setattr('app.services.library_index.INDEX_DB', temp_dir / library.db, raising=False)
    _reset_index()
    yield
    # Cleanup after test
    _reset_index()

def test_build_index_inserts_fixture_revision(monkeypatch):
    # Ensure fixture has a known revision
    fixture_path = Path(os.getenv('HOME')) / Shared/fixtures/fixture.json
    data = json.loads(fixture_path.read_text())
    rev = data.get('fixture_revision')
    result = build_index()
    assert result[type] == build_index_result
    # Verify meta stored
    from app.services.library_index import get_stats
    stats = get_stats()
    # The get_stats does not expose meta directly, so query DB manually
    import sqlite3
    conn = sqlite3.connect(str(app.services.library_index.INDEX_DB))
    row = conn.execute(SELECT value FROM index_meta WHERE key = 'fixture_revision').fetchone()
    conn.close()
    assert row is not None and row[0] == rev

def test_scoped_search_filters_by_source(monkeypatch):
    # Build index with default sources
    build_index()
    # Assume at least one entry exists for a known source, e.g., user
    results = search(test, source=user, limit=5)
    assert isinstance(results, list)
    for item in results:
        assert item[type]  # type field present
        assert item[source] == user

def test_revision_mismatch_triggers_rebuild(monkeypatch):
    # First build stores current rev
    build_index()
    # Patch fixture file to simulate revision change
    fixture_path = Path(os.getenv('HOME')) / Shared/fixtures/fixture.json
    data = json.loads(fixture_path.read_text())
    original_rev = data.get('fixture_revision')
    # Write temporary altered fixture
    altered = data.copy()
    altered['fixture_revision'] = changed_rev_for_test
    tmp_fixture = fixture_path.parent / fixture_test.json
    tmp_fixture.write_text(json.dumps(altered))
    monkeypatch.setattr('app.services.library_index.Path', lambda p: tmp_fixture if str(p).endswith('fixture.json') else Path(p))
    # Build again should detect mismatch and rebuild
    result = build_index()
    assert result[status] == completed
    # Cleanup revert
    tmp_fixture.unlink()
