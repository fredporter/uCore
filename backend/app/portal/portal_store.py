"""Local-First Sovereign Portal Store.

Implements WordPress-compatible post, page, and taxonomy management
backed by local JSON storage under UDOS_HOME/portal/portal_store.json,
with strict RBAC content isolation.
"""

from __future__ import annotations

import json
import logging
import re
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from app.core.settings import settings
from app.identity.wordpress_rbac import ROLE_CAPABILITIES, get_user_store

log = logging.getLogger("ucore.portal.store")

SUPPORTED_TAXONOMIES = {"category", "post_tag", "udos_group", "format"}
SUPPORTED_FORMATS = {"standard", "aside", "gallery", "link", "image", "quote", "status", "video", "audio", "chat"}
VALID_VISIBILITIES = {"public", "shared", "private"}
VALID_STATUSES = {"publish", "draft", "private", "trash", "review"}


def _slugify(text: str) -> str:
    text = text.lower().strip()
    text = re.sub(r"[^\w\s-]", "", text)
    text = re.sub(r"[\s_-]+", "-", text)
    return text.strip("-")


def _default_store_path() -> Path:
    return settings.udos_home / "portal" / "portal_store.json"


class PortalStore:
    """JSON-backed store for posts, pages, and WordPress taxonomies."""

    def __init__(self, data_file: Path | None = None) -> None:
        self.data_file = data_file or _default_store_path()
        self._ensure_seed()

    def _load(self) -> dict[str, Any]:
        if not self.data_file.exists():
            return {
                "taxonomies": {tax: [] for tax in SUPPORTED_TAXONOMIES},
                "posts": {},
                "next_post_id": 1,
                "next_term_id": 1,
            }
        try:
            data = json.loads(self.data_file.read_text(encoding="utf-8"))
            if isinstance(data, dict):
                data.setdefault("taxonomies", {tax: [] for tax in SUPPORTED_TAXONOMIES})
                data.setdefault("posts", {})
                data.setdefault("next_post_id", 1)
                data.setdefault("next_term_id", 1)
                return data
        except (json.JSONDecodeError, OSError):
            pass
        return {
            "taxonomies": {tax: [] for tax in SUPPORTED_TAXONOMIES},
            "posts": {},
            "next_post_id": 1,
            "next_term_id": 1,
        }

    def _save(self, data: dict[str, Any]) -> None:
        self.data_file.parent.mkdir(parents=True, exist_ok=True)
        temp = self.data_file.with_suffix(f"{self.data_file.suffix}.tmp")
        temp.write_text(json.dumps(data, indent=2), encoding="utf-8")
        temp.replace(self.data_file)

    def _ensure_seed(self) -> None:
        """Seed default taxonomies and welcome post if store is empty."""
        data = self._load()
        changed = False

        taxonomies = data.setdefault("taxonomies", {})
        if not taxonomies.get("category"):
            taxonomies["category"] = [
                {"id": 1, "name": "General", "slug": "general", "description": "General discussions and posts", "parent": 0, "count": 1},
                {"id": 2, "name": "News", "slug": "news", "description": "Announcements and updates", "parent": 0, "count": 0},
                {"id": 3, "name": "Knowledge", "slug": "knowledge", "description": "Offline reference notes and guides", "parent": 0, "count": 0},
                {"id": 4, "name": "Curriculum", "slug": "curriculum", "description": "Learning and course material", "parent": 0, "count": 0},
            ]
            changed = True

        if not taxonomies.get("post_tag"):
            taxonomies["post_tag"] = [
                {"id": 5, "name": "udos", "slug": "udos", "description": "uDos universal platform", "count": 1},
                {"id": 6, "name": "sovereign", "slug": "sovereign", "description": "Sovereign data and identity", "count": 1},
                {"id": 7, "name": "offline", "slug": "offline", "description": "Offline-first capability", "count": 0},
            ]
            changed = True

        if not taxonomies.get("udos_group"):
            taxonomies["udos_group"] = [
                {"id": 8, "name": "Household", "slug": "household", "description": "Household shared group", "count": 0},
                {"id": 9, "name": "Public", "slug": "public", "description": "Public federation group", "count": 1},
            ]
            changed = True

        if not taxonomies.get("format"):
            taxonomies["format"] = [
                {"id": 10, "name": "Standard", "slug": "standard", "description": "Standard article post", "count": 1},
                {"id": 11, "name": "Aside", "slug": "aside", "description": "Brief note or status", "count": 0},
                {"id": 12, "name": "Quote", "slug": "quote", "description": "Quotation snippet", "count": 0},
            ]
            changed = True

        if data.get("next_term_id", 1) < 20:
            data["next_term_id"] = 20
            changed = True

        posts = data.setdefault("posts", {})
        if not posts:
            now = datetime.now(UTC).isoformat()
            posts["1"] = {
                "id": 1,
                "date": now,
                "modified": now,
                "slug": "welcome-to-udos-portal",
                "status": "publish",
                "type": "post",
                "title": {
                    "rendered": "Welcome to uDos Sovereign Portal",
                    "raw": "Welcome to uDos Sovereign Portal",
                },
                "content": {
                    "rendered": "<p>Welcome to your local sovereign portal. Content is decentralized, offline-first, and governed by WordPress-compatible RBAC.</p>",
                    "raw": "Welcome to your local sovereign portal. Content is decentralized, offline-first, and governed by WordPress-compatible RBAC.",
                },
                "excerpt": {
                    "rendered": "<p>Welcome to your local sovereign portal.</p>",
                    "raw": "Welcome to your local sovereign portal.",
                },
                "author": "admin",
                "visibility": "public",
                "categories": [1],
                "tags": [5, 6],
                "udos_group": [9],
                "format": "standard",
                "meta": {},
            }
            data["next_post_id"] = 2
            changed = True

        if changed:
            self._save(data)

    # ── Taxonomy Management ──────────────────────────────────────────

    def get_taxonomy_terms(self, taxonomy: str) -> list[dict[str, Any]]:
        tax = taxonomy.lower().strip()
        if tax == "tags":
            tax = "post_tag"
        elif tax == "categories":
            tax = "category"
        data = self._load()
        return list(data.get("taxonomies", {}).get(tax, []))

    def get_taxonomy_term(self, taxonomy: str, term_id_or_slug: str | int) -> dict[str, Any] | None:
        terms = self.get_taxonomy_terms(taxonomy)
        for term in terms:
            if str(term.get("id")) == str(term_id_or_slug) or term.get("slug") == str(term_id_or_slug):
                return term
        return None

    def create_taxonomy_term(
        self,
        taxonomy: str,
        name: str,
        slug: str | None = None,
        description: str = "",
        parent: int = 0,
    ) -> dict[str, Any]:
        tax = taxonomy.lower().strip()
        if tax == "tags":
            tax = "post_tag"
        elif tax == "categories":
            tax = "category"
        if tax not in SUPPORTED_TAXONOMIES:
            raise ValueError(f"Unsupported taxonomy: {taxonomy}")

        data = self._load()
        terms = data.setdefault("taxonomies", {}).setdefault(tax, [])
        term_id = data.get("next_term_id", 1)
        data["next_term_id"] = term_id + 1

        term_slug = slug.strip() if slug else _slugify(name)
        if not term_slug:
            term_slug = f"term-{term_id}"

        new_term = {
            "id": term_id,
            "name": name.strip(),
            "slug": term_slug,
            "description": description.strip(),
            "parent": parent,
            "count": 0,
        }
        terms.append(new_term)
        self._save(data)
        return new_term

    def delete_taxonomy_term(self, taxonomy: str, term_id: int) -> bool:
        tax = taxonomy.lower().strip()
        if tax == "tags":
            tax = "post_tag"
        elif tax == "categories":
            tax = "category"

        data = self._load()
        terms = data.get("taxonomies", {}).get(tax, [])
        initial_len = len(terms)
        data["taxonomies"][tax] = [t for t in terms if t.get("id") != term_id]
        if len(data["taxonomies"][tax]) < initial_len:
            self._save(data)
            return True
        return False

    # ── RBAC Access Isolation Policy ─────────────────────────────────

    def check_access(self, post: dict[str, Any], user: dict[str, Any] | None, action: str = "read") -> bool:
        """Evaluate strict WordPress RBAC and content isolation.

        Rules:
        - Trash posts: Only viewable/restorable by users with edit_others_posts.
        - Read Public + Publish: Accessible to all (including guests with read_public).
        - Read Shared + Publish: Accessible to authenticated users with 'read' capability (subscriber+).
        - Read Private / Draft: Accessible only to author with 'edit_posts', or editor/admin with 'read_private_posts' / 'edit_others_posts'.
        - Edit: Author with 'edit_posts', or editor/admin with 'edit_others_posts'.
        - Publish: Requires 'publish_posts'.
        - Delete: Author with 'delete_posts', or editor/admin with 'delete_others_posts'.
        """
        user_dict = user or {
            "id": "guest",
            "role": "guest",
            "capabilities": sorted(ROLE_CAPABILITIES["guest"]),
        }
        user_id = str(user_dict.get("id", "guest"))
        role = str(user_dict.get("role", "guest"))
        caps = set(user_dict.get("capabilities", ROLE_CAPABILITIES.get(role, [])))

        post_author = str(post.get("author", ""))
        status = post.get("status", "draft")
        visibility = post.get("visibility", "public")
        is_author = user_id != "guest" and user_id == post_author

        if action == "read":
            if status == "trash":
                return "edit_others_posts" in caps

            if visibility == "public" and status == "publish":
                return "read_public" in caps or "read" in caps

            if visibility == "shared" and status == "publish":
                return "read" in caps  # Blocked for guests

            # Private or draft/review
            if is_author and "edit_posts" in caps:
                return True
            if "read_private_posts" in caps or "edit_others_posts" in caps:
                return True
            return False

        if action == "edit":
            if "edit_others_posts" in caps:
                return True
            if is_author and "edit_posts" in caps:
                return True
            return False

        if action == "publish":
            return "publish_posts" in caps

        if action == "delete":
            if "delete_others_posts" in caps:
                return True
            if is_author and "delete_posts" in caps:
                return True
            return False

        return False

    # ── Post Management ──────────────────────────────────────────────

    def list_posts(
        self,
        user: dict[str, Any] | None = None,
        status: str | None = None,
        category: int | str | None = None,
        tag: int | str | None = None,
        udos_group: int | str | None = None,
        search: str | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> list[dict[str, Any]]:
        data = self._load()
        posts = list(data.get("posts", {}).values())

        # Sort newest first
        posts.sort(key=lambda p: p.get("date", ""), reverse=True)

        results: list[dict[str, Any]] = []
        for post in posts:
            if status and post.get("status") != status:
                continue
            if category:
                cats = [str(c) for c in post.get("categories", [])]
                if str(category) not in cats:
                    continue
            if tag:
                tags = [str(t) for t in post.get("tags", [])]
                if str(tag) not in tags:
                    continue
            if udos_group:
                groups = [str(g) for g in post.get("udos_group", [])]
                if str(udos_group) not in groups:
                    continue
            if search:
                query = search.lower()
                title = post.get("title", {}).get("rendered", "").lower()
                content = post.get("content", {}).get("rendered", "").lower()
                if query not in title and query not in content:
                    continue

            # Access check
            if self.check_access(post, user, action="read"):
                results.append(post)

        return results[offset : offset + limit]

    def get_post(self, post_id_or_slug: int | str, user: dict[str, Any] | None = None) -> dict[str, Any] | None:
        data = self._load()
        posts = data.get("posts", {})
        post = posts.get(str(post_id_or_slug))
        if not post:
            for p in posts.values():
                if p.get("slug") == str(post_id_or_slug):
                    post = p
                    break
        if not post:
            return None

        if not self.check_access(post, user, action="read"):
            return None
        return post

    def create_post(self, post_data: dict[str, Any], author_user: dict[str, Any]) -> dict[str, Any]:
        user_caps = set(author_user.get("capabilities", []))
        if "edit_posts" not in user_caps:
            raise PermissionError("User lacks edit_posts capability")

        requested_status = post_data.get("status", "draft")
        if requested_status not in VALID_STATUSES:
            requested_status = "draft"

        # Demote to draft if publishing without permission
        if requested_status == "publish" and "publish_posts" not in user_caps:
            requested_status = "draft"

        data = self._load()
        post_id = data.get("next_post_id", 1)
        data["next_post_id"] = post_id + 1

        now = datetime.now(UTC).isoformat()
        title_raw = str(post_data.get("title", "")).strip() or "Untitled"
        content_raw = str(post_data.get("content", "")).strip()
        excerpt_raw = str(post_data.get("excerpt", "")).strip() or (content_raw[:160] if content_raw else "")

        slug = post_data.get("slug") or _slugify(title_raw)
        if not slug:
            slug = f"post-{post_id}"

        visibility = post_data.get("visibility", "public")
        if visibility not in VALID_VISIBILITIES:
            visibility = "public"

        fmt = post_data.get("format", "standard")
        if fmt not in SUPPORTED_FORMATS:
            fmt = "standard"

        post = {
            "id": post_id,
            "date": now,
            "modified": now,
            "slug": slug,
            "status": requested_status,
            "type": post_data.get("type", "post"),
            "title": {
                "raw": title_raw,
                "rendered": title_raw,
            },
            "content": {
                "raw": content_raw,
                "rendered": f"<p>{content_raw}</p>",
            },
            "excerpt": {
                "raw": excerpt_raw,
                "rendered": f"<p>{excerpt_raw}</p>",
            },
            "author": author_user.get("id", "admin"),
            "visibility": visibility,
            "categories": post_data.get("categories", [1]),
            "tags": post_data.get("tags", []),
            "udos_group": post_data.get("udos_group", []),
            "format": fmt,
            "meta": post_data.get("meta", {}),
        }

        data["posts"][str(post_id)] = post
        self._save(data)
        return post

    def update_post(
        self,
        post_id: int | str,
        post_data: dict[str, Any],
        user: dict[str, Any],
    ) -> dict[str, Any] | None:
        data = self._load()
        posts = data.get("posts", {})
        post = posts.get(str(post_id))
        if not post:
            return None

        if not self.check_access(post, user, action="edit"):
            raise PermissionError("User lacks permission to edit this post")

        user_caps = set(user.get("capabilities", []))

        # Check status change to publish
        new_status = post_data.get("status")
        if new_status:
            if new_status not in VALID_STATUSES:
                new_status = post.get("status")
            if new_status == "publish" and "publish_posts" not in user_caps:
                raise PermissionError("User lacks publish_posts capability")
            post["status"] = new_status

        if "title" in post_data:
            title_val = str(post_data["title"]).strip()
            post["title"] = {"raw": title_val, "rendered": title_val}
        if "content" in post_data:
            content_val = str(post_data["content"]).strip()
            post["content"] = {"raw": content_val, "rendered": f"<p>{content_val}</p>"}
        if "excerpt" in post_data:
            excerpt_val = str(post_data["excerpt"]).strip()
            post["excerpt"] = {"raw": excerpt_val, "rendered": f"<p>{excerpt_val}</p>"}
        if "visibility" in post_data and post_data["visibility"] in VALID_VISIBILITIES:
            post["visibility"] = post_data["visibility"]
        if "categories" in post_data and isinstance(post_data["categories"], list):
            post["categories"] = post_data["categories"]
        if "tags" in post_data and isinstance(post_data["tags"], list):
            post["tags"] = post_data["tags"]
        if "udos_group" in post_data and isinstance(post_data["udos_group"], list):
            post["udos_group"] = post_data["udos_group"]
        if "format" in post_data and post_data["format"] in SUPPORTED_FORMATS:
            post["format"] = post_data["format"]
        if "meta" in post_data and isinstance(post_data["meta"], dict):
            post["meta"].update(post_data["meta"])
        if "slug" in post_data and post_data["slug"]:
            post["slug"] = _slugify(str(post_data["slug"]))

        post["modified"] = datetime.now(UTC).isoformat()
        posts[str(post_id)] = post
        data["posts"] = posts
        self._save(data)
        return post

    def delete_post(self, post_id: int | str, user: dict[str, Any], force: bool = False) -> bool:
        data = self._load()
        posts = data.get("posts", {})
        post = posts.get(str(post_id))
        if not post:
            return False

        if not self.check_access(post, user, action="delete"):
            raise PermissionError("User lacks permission to delete this post")

        if force:
            del posts[str(post_id)]
        else:
            post["status"] = "trash"
            post["modified"] = datetime.now(UTC).isoformat()
            posts[str(post_id)] = post

        data["posts"] = posts
        self._save(data)
        return True

    def get_feed(self, user: dict[str, Any] | None = None, limit: int = 20) -> list[dict[str, Any]]:
        """Return published feed items accessible to user."""
        return self.list_posts(user=user, status="publish", limit=limit)


_DEFAULT_PORTAL_STORE: PortalStore | None = None


def get_portal_store(data_file: Path | None = None) -> PortalStore:
    global _DEFAULT_PORTAL_STORE
    if data_file is not None:
        return PortalStore(data_file)
    if _DEFAULT_PORTAL_STORE is None:
        _DEFAULT_PORTAL_STORE = PortalStore()
    return _DEFAULT_PORTAL_STORE
