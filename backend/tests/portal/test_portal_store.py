"""Unit tests for Sovereign Portal Store & Strict RBAC Isolation."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from app.identity.wordpress_rbac import (
    ROLE_CAPABILITIES,
    WordPressUserStore,
)
from app.portal.portal_store import PortalStore


class TestPortalStore(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.portal_file = Path(self.temp_dir.name) / "portal_store.json"
        self.users_file = Path(self.temp_dir.name) / "users.json"
        self.store = PortalStore(self.portal_file)
        self.user_store = WordPressUserStore(self.users_file)

        # Create test users across WordPress roles
        self.admin = self.user_store.create_user("admin_user", "Admin", role="administrator")
        self.editor = self.user_store.create_user("editor_user", "Editor", role="editor")
        self.author1 = self.user_store.create_user("author_one", "Author One", role="author")
        self.author2 = self.user_store.create_user("author_two", "Author Two", role="author")
        self.contributor = self.user_store.create_user("contrib_user", "Contrib", role="contributor")
        self.subscriber = self.user_store.create_user("sub_user", "Subscriber", role="subscriber")
        self.guest = {
            "id": "guest",
            "username": "guest",
            "display_name": "Guest",
            "role": "guest",
            "capabilities": sorted(ROLE_CAPABILITIES["guest"]),
        }

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_seed_taxonomies_and_initial_post(self):
        categories = self.store.get_taxonomy_terms("category")
        self.assertGreaterEqual(len(categories), 4)
        cat_slugs = {c["slug"] for c in categories}
        self.assertIn("general", cat_slugs)
        self.assertIn("news", cat_slugs)

        tags = self.store.get_taxonomy_terms("post_tag")
        tag_slugs = {t["slug"] for t in tags}
        self.assertIn("sovereign", tag_slugs)

        posts = self.store.list_posts(user=self.guest)
        self.assertGreaterEqual(len(posts), 1)
        welcome = posts[0]
        self.assertEqual(welcome["slug"], "welcome-to-udos-portal")
        self.assertEqual(welcome["visibility"], "public")
        self.assertEqual(welcome["status"], "publish")

    def test_taxonomy_crud(self):
        term = self.store.create_taxonomy_term(
            taxonomy="category",
            name="Hardware Hacking",
            description="Recycled tech guides",
        )
        self.assertEqual(term["name"], "Hardware Hacking")
        self.assertEqual(term["slug"], "hardware-hacking")

        fetched = self.store.get_taxonomy_term("category", term["id"])
        self.assertIsNotNone(fetched)
        self.assertEqual(fetched["name"], "Hardware Hacking")

        deleted = self.store.delete_taxonomy_term("category", term["id"])
        self.assertTrue(deleted)
        self.assertIsNone(self.store.get_taxonomy_term("category", term["id"]))

    def test_content_isolation_matrix(self):
        # 1. Public Published Post -> Readable by all
        pub_post = self.store.create_post(
            {
                "title": "Public Article",
                "content": "Everyone can read this.",
                "status": "publish",
                "visibility": "public",
            },
            author_user=self.author1,
        )
        self.assertTrue(self.store.check_access(pub_post, self.guest, "read"))
        self.assertTrue(self.store.check_access(pub_post, self.subscriber, "read"))
        self.assertTrue(self.store.check_access(pub_post, self.author2, "read"))

        # 2. Shared Published Post -> Readable by authenticated users (subscriber+), blocked for guests
        shared_post = self.store.create_post(
            {
                "title": "Household Shared Article",
                "content": "Shared within household/network.",
                "status": "publish",
                "visibility": "shared",
            },
            author_user=self.author1,
        )
        self.assertFalse(self.store.check_access(shared_post, self.guest, "read"))
        self.assertTrue(self.store.check_access(shared_post, self.subscriber, "read"))
        self.assertTrue(self.store.check_access(shared_post, self.author2, "read"))

        # 3. Private Post -> Only author, or editor/admin
        priv_post = self.store.create_post(
            {
                "title": "Author One Secret Diary",
                "content": "Strictly private.",
                "status": "publish",
                "visibility": "private",
            },
            author_user=self.author1,
        )
        self.assertFalse(self.store.check_access(priv_post, self.guest, "read"))
        self.assertFalse(self.store.check_access(priv_post, self.subscriber, "read"))
        self.assertFalse(self.store.check_access(priv_post, self.author2, "read"))
        self.assertTrue(self.store.check_access(priv_post, self.author1, "read"))
        self.assertTrue(self.store.check_access(priv_post, self.editor, "read"))
        self.assertTrue(self.store.check_access(priv_post, self.admin, "read"))

        # 4. Draft Post -> Only author, or editor/admin
        draft_post = self.store.create_post(
            {
                "title": "WIP Draft",
                "content": "Not ready yet.",
                "status": "draft",
                "visibility": "public",
            },
            author_user=self.author1,
        )
        self.assertFalse(self.store.check_access(draft_post, self.guest, "read"))
        self.assertFalse(self.store.check_access(draft_post, self.subscriber, "read"))
        self.assertFalse(self.store.check_access(draft_post, self.author2, "read"))
        self.assertTrue(self.store.check_access(draft_post, self.author1, "read"))
        self.assertTrue(self.store.check_access(draft_post, self.editor, "read"))
        self.assertTrue(self.store.check_access(draft_post, self.admin, "read"))

    def test_contributor_cannot_publish_directly(self):
        # Contributor has edit_posts but NOT publish_posts
        post = self.store.create_post(
            {
                "title": "Contributor Proposal",
                "content": "I want this published.",
                "status": "publish",
            },
            author_user=self.contributor,
        )
        # Status should be demoted to draft
        self.assertEqual(post["status"], "draft")

    def test_edit_and_delete_permissions(self):
        post = self.store.create_post(
            {
                "title": "Author Post",
                "content": "Content.",
                "status": "publish",
            },
            author_user=self.author1,
        )

        # Author can edit their own post
        updated = self.store.update_post(
            post["id"],
            {"title": "Author Post Updated"},
            user=self.author1,
        )
        self.assertEqual(updated["title"]["rendered"], "Author Post Updated")

        # Other author CANNOT edit
        with self.assertRaises(PermissionError):
            self.store.update_post(
                post["id"],
                {"title": "Hacked Title"},
                user=self.author2,
            )

        # Editor CAN edit
        updated_by_editor = self.store.update_post(
            post["id"],
            {"title": "Editor Polished Title"},
            user=self.editor,
        )
        self.assertEqual(updated_by_editor["title"]["rendered"], "Editor Polished Title")

        # Other author CANNOT delete
        with self.assertRaises(PermissionError):
            self.store.delete_post(post["id"], user=self.author2)

        # Author CAN delete (trash)
        self.assertTrue(self.store.delete_post(post["id"], user=self.author1))
        trashed = self.store.get_post(post["id"], user=self.author1)
        # Trashed post not readable by author unless they have edit_others_posts
        self.assertIsNone(trashed)

        # Admin CAN read trashed post
        admin_view = self.store.get_post(post["id"], user=self.admin)
        self.assertIsNotNone(admin_view)
        self.assertEqual(admin_view["status"], "trash")

    def test_feed_filters_properly(self):
        self.store.create_post(
            {"title": "Public Feed Item", "content": "Pub", "status": "publish", "visibility": "public"},
            author_user=self.author1,
        )
        self.store.create_post(
            {"title": "Shared Feed Item", "content": "Shared", "status": "publish", "visibility": "shared"},
            author_user=self.author1,
        )
        self.store.create_post(
            {"title": "Private Feed Item", "content": "Priv", "status": "publish", "visibility": "private"},
            author_user=self.author1,
        )

        guest_feed = self.store.get_feed(user=self.guest)
        sub_feed = self.store.get_feed(user=self.subscriber)

        # Guest only gets public posts (welcome + 1 new public)
        guest_titles = [f["title"]["rendered"] for f in guest_feed]
        self.assertIn("Public Feed Item", guest_titles)
        self.assertNotIn("Shared Feed Item", guest_titles)
        self.assertNotIn("Private Feed Item", guest_titles)

        # Subscriber gets public + shared
        sub_titles = [f["title"]["rendered"] for f in sub_feed]
        self.assertIn("Public Feed Item", sub_titles)
        self.assertIn("Shared Feed Item", sub_titles)
        self.assertNotIn("Private Feed Item", sub_titles)


if __name__ == "__main__":
    unittest.main()
