import pytest

from app.services.browser_library import export_html, import_html
from app.services.connections.store import CollectionStore

HTML = '''<DL><p><DT><H3 PERSONAL_TOOLBAR_FOLDER="true">Favorites</H3><DL><p>
<DT><A HREF="https://example.com/">Example</A></DL><p>
<DT><H3 ID="com.apple.ReadingList">Reading List</H3><DL><p>
<DT><A HREF="https://example.org/read">Read me</A>
<DT><A HREF="javascript:alert(1)">Unsafe</A></DL><p></DL>'''


def test_browser_import_merge_profile_isolation_and_roundtrip(tmp_path):
    store = CollectionStore(tmp_path / "collections.sqlite3")
    assert import_html(store, "alice", HTML, "safari")["imported"] == 2
    assert import_html(store, "alice", HTML, "safari")["imported"] == 0
    assert store.records("bob") == []
    bookmark = next(r for r in store.records("alice") if r["kind"] == "bookmarks")
    store.save("alice", "bookmarks", {**bookmark["data"], "title": "My title"}, bookmark["id"], bookmark["revision"])
    import_html(store, "alice", HTML, "safari")
    assert store.record("alice", bookmark["id"])["data"]["title"] == "My title"
    exported = export_html(store.records("alice"))
    assert "javascript:" not in exported
    assert import_html(store, "bob", exported, "firefox")["imported"] == 2
    records = store.records("bob")
    assert any(r["data"].get("favourite") for r in records)
    assert any(r["kind"] == "reading_list" for r in records)


def test_browser_import_rejects_oversize_and_invalid_source(tmp_path):
    store = CollectionStore(tmp_path / "collections.sqlite3")
    with pytest.raises(ValueError):
        import_html(store, "alice", "x" * 2_100_000, "safari")
    with pytest.raises(ValueError):
        import_html(store, "alice", HTML, "unknown")
