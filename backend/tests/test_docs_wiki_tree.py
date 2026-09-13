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
