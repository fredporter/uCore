"""Unit tests for WordPress RBAC roles, capabilities, and user store."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from app.identity.wordpress_rbac import (
    ROLE_CAPABILITIES,
    VALID_ROLES,
    WordPressUserStore,
    get_current_user,
)


class DummyRequest:
    def __init__(self, headers: dict[str, str] | None = None):
        self.headers = headers or {}


class TestWordPressRBAC(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.store_file = Path(self.temp_dir.name) / "users.json"
        self.store = WordPressUserStore(self.store_file)

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_roles_and_capabilities_matrix(self):
        self.assertIn("administrator", VALID_ROLES)
        self.assertIn("editor", VALID_ROLES)
        self.assertIn("author", VALID_ROLES)
        self.assertIn("contributor", VALID_ROLES)
        self.assertIn("subscriber", VALID_ROLES)
        self.assertIn("guest", VALID_ROLES)

        admin_caps = ROLE_CAPABILITIES["administrator"]
        self.assertIn("manage_options", admin_caps)
        self.assertIn("manage_users", admin_caps)
        self.assertIn("manage_taxonomies", admin_caps)
        self.assertIn("publish_posts", admin_caps)
        self.assertIn("edit_others_posts", admin_caps)
        self.assertIn("delete_others_posts", admin_caps)

        editor_caps = ROLE_CAPABILITIES["editor"]
        self.assertNotIn("manage_users", editor_caps)
        self.assertIn("manage_taxonomies", editor_caps)
        self.assertIn("publish_posts", editor_caps)
        self.assertIn("edit_others_posts", editor_caps)

        author_caps = ROLE_CAPABILITIES["author"]
        self.assertIn("publish_posts", author_caps)
        self.assertIn("edit_posts", author_caps)
        self.assertNotIn("edit_others_posts", author_caps)

        subscriber_caps = ROLE_CAPABILITIES["subscriber"]
        self.assertIn("read", subscriber_caps)
        self.assertIn("read_public", subscriber_caps)
        self.assertNotIn("edit_posts", subscriber_caps)

        guest_caps = ROLE_CAPABILITIES["guest"]
        self.assertEqual(guest_caps, {"read_public"})

    def test_auto_seed_owner(self):
        users = self.store.list_users()
        self.assertGreaterEqual(len(users), 1)
        owner = next((u for u in users if u.get("meta", {}).get("udos_is_owner")), None)
        self.assertIsNotNone(owner)
        self.assertEqual(owner["role"], "administrator")
        self.assertIn("manage_users", owner["capabilities"])
        self.assertNotIn("auth_hash", owner)
        self.assertNotIn("auth_salt", owner)

    def test_create_and_get_user(self):
        created = self.store.create_user(
            username="alice",
            display_name="Alice Author",
            email="alice@udos.local",
            role="author",
            meta={"household": True},
        )
        self.assertTrue(created["id"].startswith("usr_"))
        self.assertEqual(created["role"], "author")
        self.assertIn("publish_posts", created["capabilities"])
        self.assertTrue(self.store.has_capability(created["id"], "publish_posts"))
        self.assertFalse(self.store.has_capability(created["id"], "edit_others_posts"))

        fetched = self.store.get_user(created["id"])
        self.assertIsNotNone(fetched)
        self.assertEqual(fetched["display_name"], "Alice Author")

    def test_token_authentication(self):
        created = self.store.create_user(
            username="bob",
            display_name="Bob Contributor",
            role="contributor",
        )
        token = created["api_token"]
        self.assertTrue(token)

        by_token = self.store.get_user_by_token(token)
        self.assertIsNotNone(by_token)
        self.assertEqual(by_token["id"], created["id"])

        req = DummyRequest(headers={"Authorization": f"Bearer {token}"})
        user = get_current_user(req, store=self.store)
        self.assertEqual(user["id"], created["id"])
        self.assertEqual(user["role"], "contributor")

    def test_guest_resolution(self):
        req = DummyRequest(headers={"X-Udos-User": "guest"})
        user = get_current_user(req, store=self.store)
        self.assertEqual(user["role"], "guest")
        self.assertFalse(self.store.has_capability(user, "read"))
        self.assertTrue(self.store.has_capability(user, "read_public"))

    def test_update_and_delete_user(self):
        user = self.store.create_user(
            username="charlie",
            display_name="Charlie",
            role="subscriber",
        )
        updated = self.store.update_user(
            user["id"],
            display_name="Charlie Editor",
            role="editor",
        )
        self.assertEqual(updated["role"], "editor")
        self.assertTrue(self.store.has_capability(user["id"], "edit_others_posts"))

        # Delete user
        self.assertTrue(self.store.delete_user(user["id"]))
        self.assertIsNone(self.store.get_user(user["id"]))


if __name__ == "__main__":
    unittest.main()
