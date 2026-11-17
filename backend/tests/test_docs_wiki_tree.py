"""Unit tests for the multi-vault Documentation Wiki tree aggregator."""

from __future__ import annotations

import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from app.surfaces.documentation_api import _build_dir_tree, _list_courses


class TestDocsWikiTree(unittest.TestCase):
    def test_build_dir_tree_filters_hidden_and_builds_hierarchy(self):
        with TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            (temp_path / ".hidden_dir").mkdir()
            (temp_path / ".hidden.md").write_text("hidden", encoding="utf-8")
            (temp_path / "node_modules").mkdir()

            sub = temp_path / "Subfolder"
            sub.mkdir()
            (sub / "Article.md").write_text("# Article Title\n\nContent", encoding="utf-8")
            (temp_path / "RootDoc.md").write_text("# Root Doc\n\nContent", encoding="utf-8")

            tree = _build_dir_tree(temp_path, "vault")
            self.assertEqual(len(tree), 2)
            names = {item["name"] for item in tree}
            self.assertIn("RootDoc.md", names)
            self.assertIn("Subfolder", names)

            sub_item = next(i for i in tree if i["name"] == "Subfolder")
            self.assertTrue(sub_item["is_dir"])
            self.assertEqual(len(sub_item["children"]), 1)
            self.assertEqual(sub_item["children"][0]["name"], "Article.md")

    def test_list_courses_includes_sources(self):
        courses = _list_courses()
        # Ensure courses returns a list
        self.assertIsInstance(courses, list)
        sources = {c.get("source") for c in courses}
        # If uCode or Sonic manuals exist, they will be indexed
        if any(c.get("source") == "manual" for c in courses):
            self.assertIn("manual", sources)
        if any(c.get("source") == "sonic" for c in courses):
            self.assertIn("sonic", sources)


if __name__ == "__main__":
    unittest.main()


def test_course_catalog_only_reads_learning_roots(tmp_path, monkeypatch):
    from types import SimpleNamespace

    from app.surfaces import documentation_api as docs

    roots = [tmp_path / 'uCode/docs/manual', tmp_path / 'SonicScrewdriver/docs/manual', tmp_path / 'learning']
    for root in roots:
        root.mkdir(parents=True)
        (root / 'guide.md').write_text('# Guide', encoding='utf-8')
    archive = tmp_path / 'uCore/docs/archive'
    archive.mkdir(parents=True)
    (archive / 'internal-report.md').write_text('# Internal report', encoding='utf-8')
    monkeypatch.setattr(docs, 'settings', SimpleNamespace(udos_root=tmp_path))
    monkeypatch.setattr(docs, 'LEARNING_ROOT', roots[-1])
    courses = docs._list_courses()
    assert {course['source'] for course in courses} == {'manual', 'sonic', 'learning'}
    assert len(courses) == 3


def test_public_documentation_consolidates_binders(tmp_path, monkeypatch):
    from app.surfaces import documentation_api as docs

    paths = [
        "Developer-docs/guide/devstudio-guide.md",
        "udos-docs/docs/uCode/uCode-User-Manual.md",
        "udos-docs/docs/uCode/spatial/runtime.md",
        "udos-docs/docs/uCode/gridcore/runtime.md",
        "udos-docs/docs/uCore/specs/surface.md",
        "udos-docs/docs/uCode/tutorials/ucode-mini-game.md",
        "udos-docs/docs/learning/lesson.md",
        "global-knowledge/datasets/reference.md",
    ]
    for name in paths:
        path = tmp_path / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("# Document\n", encoding="utf-8")
    monkeypatch.setitem(docs._CONTENT_ROOTS, "public", tmp_path)
    items = docs._build_dir_tree(tmp_path, "public")
    manual = {"path": "manual.md", "source": "manual", "is_dir": False}
    docs._group_public_documentation(items, [manual])

    documentation, knowledge = items
    assert documentation["name"] == "uDOS Documentation"
    assert knowledge["name"] == "Global Knowledge"

    def leaves(item):
        if not item["is_dir"]:
            return {item["path"]}
        return set().union(*(leaves(child) for child in item["children"]))

    assert leaves(documentation) == set(paths[1:7]) | {"manual.md"}
    assert leaves(knowledge) == {paths[7]}
    ucode = next(child for child in documentation["children"] if child["path"].endswith("/uCode"))
    assert {"GridCore uCode1", "Spatial uCode2"} <= {child["name"] for child in ucode["children"]}
