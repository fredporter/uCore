from __future__ import annotations

import unittest
from datetime import UTC, datetime, timedelta
from pathlib import Path
from tempfile import TemporaryDirectory

from aiohttp import web

from app.identity.routes import register_routes
from app.identity.story_store import IdentityStoryStore
from app.identity.wordpress_mapper import map_from_wordpress, map_to_wordpress

EXPECTED_ROUTES = {
    ("GET", "/api/identity/plugin/profile"),
    ("GET", "/api/identity/plugin/session"),
    ("GET", "/api/identity/variables"),
    ("PUT", "/api/identity/variables"),
    ("POST", "/api/identity/stories"),
    ("GET", "/api/identity/stories/{story_id}"),
    ("PATCH", "/api/identity/stories/{story_id}"),
    ("GET", "/api/identity/privacy/{resource_id}"),
    ("PUT", "/api/identity/privacy/{resource_id}"),
    ("POST", "/api/identity/wordpress/map-outbound"),
    ("POST", "/api/identity/wordpress/map-inbound"),
}


class IdentityRouteContractTests(unittest.TestCase):
    def test_registered_routes_match_contract(self) -> None:
        app = web.Application()
        register_routes(app)
        actual = {
            (route.method, route.resource.canonical)
            for route in app.router.routes()
            if route.method != "HEAD"
        }
        self.assertEqual(EXPECTED_ROUTES, actual)


class IdentityStoryStoreTests(unittest.TestCase):
    def test_variables_and_story_progression_persist(self) -> None:
        with TemporaryDirectory() as temporary_dir:
            data_file = Path(temporary_dir) / "identity-story.json"
            store = IdentityStoryStore(data_file)

            variables = store.update_variables({"timezone": "UTC", "locale": "en-GB"})
            self.assertEqual("UTC", variables["timezone"])
            self.assertEqual(variables, IdentityStoryStore(data_file).get_variables())

            story = store.create_story("onboarding", {"name": "Ada"})
            updated = store.update_story(
                story["id"],
                step=1,
                status="in_progress",
                responses={"city": "London"},
            )

            self.assertIsNotNone(updated)
            assert updated is not None
            self.assertEqual(1, updated["step"])
            self.assertEqual("in_progress", updated["status"])
            self.assertEqual("Ada", updated["responses"]["name"])
            self.assertEqual("London", updated["responses"]["city"])
            self.assertEqual(updated, IdentityStoryStore(data_file).get_story(story["id"]))

    def test_missing_story_update_returns_none(self) -> None:
        with TemporaryDirectory() as temporary_dir:
            store = IdentityStoryStore(Path(temporary_dir) / "identity-story.json")
            self.assertIsNone(store.update_story("missing", step=1))

    def test_share_policy_expires_to_private(self) -> None:
        with TemporaryDirectory() as temporary_dir:
            store = IdentityStoryStore(Path(temporary_dir) / "identity-story.json")
            future = (datetime.now(UTC) + timedelta(hours=1)).isoformat()
            past = (datetime.now(UTC) - timedelta(hours=1)).isoformat()

            active = store.set_privacy(
                "story-1",
                visibility="shared",
                expires_at=future,
            )
            self.assertTrue(active["share_active"])
            self.assertEqual("shared", active["effective_visibility"])

            expired = store.set_privacy(
                "story-1",
                visibility="public",
                expires_at=past,
            )
            self.assertTrue(expired["expired"])
            self.assertFalse(expired["share_active"])
            self.assertEqual("private", expired["effective_visibility"])

    def test_unspecified_privacy_defaults_to_private(self) -> None:
        with TemporaryDirectory() as temporary_dir:
            store = IdentityStoryStore(Path(temporary_dir) / "identity-story.json")
            policy = store.get_privacy("unknown")
            self.assertEqual("private", policy["effective_visibility"])
            self.assertFalse(policy["share_active"])


class WordPressMapperTests(unittest.TestCase):
    def test_outbound_mapping_allowlists_user_fields_and_namespaces_meta(self) -> None:
        mapped = map_to_wordpress(
            profile={
                "email": "ada@example.test",
                "display_name": "Ada",
                "user_id": "UDOS-1",
                "password": "must-not-leak",
            },
            variables={"Favorite Color": "blue", "timezone": "UTC"},
            groups=["writers", "writers", "editors"],
        )

        self.assertEqual(
            {"email": "ada@example.test", "display_name": "Ada"},
            mapped["user"],
        )
        self.assertNotIn("password", mapped["user"])
        self.assertEqual("UDOS-1", mapped["meta"]["udos_user_id"])
        self.assertEqual("blue", mapped["meta"]["udos_favorite_color"])
        self.assertEqual(["editors", "writers"], mapped["taxonomies"]["udos_group"])

    def test_inbound_mapping_ignores_non_udos_meta(self) -> None:
        mapped = map_from_wordpress({
            "user": {"email": "ada@example.test", "role": "administrator"},
            "meta": {
                "udos_user_id": "UDOS-1",
                "udos_timezone": "UTC",
                "session_token": "must-not-import",
            },
            "taxonomies": {"udos_group": ["writers"]},
        })

        self.assertEqual("ada@example.test", mapped["profile"]["email"])
        self.assertNotIn("role", mapped["profile"])
        self.assertEqual("UDOS-1", mapped["profile"]["user_id"])
        self.assertEqual({"timezone": "UTC"}, mapped["variables"])
        self.assertEqual(["writers"], mapped["groups"])


if __name__ == "__main__":
    unittest.main()
