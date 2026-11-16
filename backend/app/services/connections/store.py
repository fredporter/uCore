from __future__ import annotations

import json
import re
import sqlite3
import uuid
from contextlib import contextmanager
from datetime import UTC, datetime
from pathlib import Path

from app.core.settings import settings

PIM_KINDS = {"tasks", "contacts", "notes", "calendar", "mail"}
KINDS = PIM_KINDS | {"bookmarks", "reading_list"}


def now():
    return datetime.now(UTC).isoformat()


class CollectionStore:
    def __init__(self, path: Path | None = None):
        self.path = path or settings.data_dir / "connections.sqlite3"
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.db() as db:
            db.executescript("""
            CREATE TABLE IF NOT EXISTS connections(id TEXT PRIMARY KEY, profile TEXT NOT NULL,
                provider TEXT NOT NULL, config TEXT NOT NULL, health TEXT NOT NULL);
            CREATE TABLE IF NOT EXISTS collection(id TEXT PRIMARY KEY, profile TEXT NOT NULL,
                kind TEXT NOT NULL, data TEXT NOT NULL, revision INTEGER NOT NULL, updated TEXT NOT NULL);
            CREATE TABLE IF NOT EXISTS replicas(connection TEXT NOT NULL, remote TEXT NOT NULL,
                record TEXT NOT NULL, base TEXT NOT NULL, version TEXT NOT NULL,
                PRIMARY KEY(connection,remote));
            CREATE TABLE IF NOT EXISTS conflicts(connection TEXT NOT NULL, remote TEXT NOT NULL,
                record TEXT NOT NULL, incoming TEXT NOT NULL, version TEXT NOT NULL,
                PRIMARY KEY(connection,remote));
            CREATE TABLE IF NOT EXISTS pending_exports(connection TEXT NOT NULL, record TEXT NOT NULL,
                kind TEXT NOT NULL, started TEXT NOT NULL, PRIMARY KEY(connection,record));
            CREATE TABLE IF NOT EXISTS drone_grants(
                id TEXT PRIMARY KEY, owner TEXT NOT NULL, recipient TEXT NOT NULL,
                connection TEXT NOT NULL, account_subject TEXT NOT NULL, list_id TEXT NOT NULL,
                expires REAL NOT NULL, revoked REAL, last_used REAL,
                FOREIGN KEY(connection) REFERENCES connections(id));
            CREATE TABLE IF NOT EXISTS setup(profile TEXT PRIMARY KEY, data TEXT NOT NULL);
            """)
        self.path.chmod(0o600)

    @contextmanager
    def db(self):
        db = sqlite3.connect(self.path, timeout=10)
        db.row_factory = sqlite3.Row
        db.execute("PRAGMA foreign_keys=ON")
        try:
            with db:
                yield db
        finally:
            db.close()

    def connections(self, profile=None):
        with self.db() as db:
            rows = db.execute(
                "SELECT * FROM connections" + (" WHERE profile=?" if profile else ""),
                (profile,) if profile else (),
            ).fetchall()
        return [
            {**dict(row), "config": json.loads(row["config"]), "health": json.loads(row["health"])}
            for row in rows
        ]

    def connection(self, profile, cid):
        return next((c for c in self.connections(profile) if c["id"] == cid), None)

    def configure(self, profile, provider, config, cid=None):
        if provider not in {"apple", "google"}:
            raise ValueError("Unknown provider")
        scopes = config.get("collections", {})
        if not isinstance(scopes, dict) or not set(scopes) <= PIM_KINDS:
            raise ValueError("Invalid collections")
        for kind, scope in scopes.items():
            if not isinstance(scope, dict) or scope.get("direction", "pull") not in {
                "pull",
                "both",
            }:
                raise ValueError("Invalid sync direction")
            if scope.get("flag_action", "") not in {"", "create-task"}:
                raise ValueError("Unknown flag automation")
            if scope.get("filter", "all") not in {"all", "starred", "vip", "flagged"}:
                raise ValueError("Invalid record filter")
            if scope.get("filter") == "vip" and (
                provider != "apple" or kind != "contacts" or not scope.get("vip_group")
            ):
                raise ValueError(
                    "VIP filtering requires an explicitly selected Apple Contacts group"
                )
            if scope.get("filter") == "starred" and (
                provider != "google" or kind not in {"contacts", "notes", "mail"}
            ):
                raise ValueError("Star filtering is not available for this collection")
            if (
                not isinstance(scope.get("records", []), list)
                or len(scope.get("records", [])) > 1000
            ):
                raise ValueError("Select up to 1000 records")
            if not isinstance(scope.get("lists", []), list) or len(scope.get("lists", [])) > 50:
                raise ValueError("Choose up to 50 lists")
            if (
                config.get("enabled")
                and scope.get("selection") == "records"
                and not scope.get("records")
            ):
                raise ValueError("Choose individual records before enabling sync")
            if any(
                not isinstance(value, str) or len(value) > 500 for value in scope.get("lists", [])
            ):
                raise ValueError("Invalid list identifier")
            for label in scope.get("flag_labels", {}).values():
                if not isinstance(label, str) or (
                    label
                    and (
                        label
                        in {
                            "INBOX",
                            "SENT",
                            "TRASH",
                            "SPAM",
                            "DRAFT",
                            "UNREAD",
                            "STARRED",
                            "IMPORTANT",
                        }
                        or label.startswith("CATEGORY_")
                    )
                ):
                    raise ValueError("Map colour flags to custom Gmail labels, not system folders")
            if scope.get("direction") == "both" and not scope.get("target"):
                raise ValueError("Choose an outbound destination")
        existing = self.connection(profile, cid) if cid else None
        if cid and (not existing or existing["provider"] != provider):
            raise ValueError("Connection not found")
        if config.get("enabled") and not any(scope.get("lists") for scope in scopes.values()):
            raise ValueError("Choose at least one list before enabling sync")
        cid = cid or uuid.uuid4().hex
        clean = {
            "enabled": bool(config.get("enabled", False)),
            "collections": scopes,
            "interval": max(60, min(int(config.get("interval", 300)), 86400)),
        }
        with self.db() as db:
            db.execute(
                "INSERT INTO connections VALUES(?,?,?,?,?) ON CONFLICT(id) DO UPDATE SET config=excluded.config",
                (
                    cid,
                    profile,
                    provider,
                    json.dumps(clean),
                    json.dumps({"state": "setup_required"}),
                ),
            )
        return self.connection(profile, cid)

    def health(self, cid, **values):
        with self.db() as db:
            row = db.execute("SELECT health FROM connections WHERE id=?", (cid,)).fetchone()
            data = json.loads(row[0]) if row else {}
            data.update(values)
            db.execute("UPDATE connections SET health=? WHERE id=?", (json.dumps(data), cid))

    def records(self, profile, kind=None):
        with self.db() as db:
            rows = db.execute(
                "SELECT * FROM collection WHERE profile=? AND COALESCE(json_extract(data, '$.excluded_from_tasks'),0)=0"
                + (" AND kind=?" if kind else "")
                + " ORDER BY updated DESC",
                (profile, kind) if kind else (profile,),
            ).fetchall()
        return [{**dict(r), "data": json.loads(r["data"])} for r in rows]

    def record(self, profile, rid):
        with self.db() as db:
            row = db.execute(
                "SELECT * FROM collection WHERE profile=? AND id=?", (profile, rid)
            ).fetchone()
        return {**dict(row), "data": json.loads(row["data"])} if row else None

    def save(self, profile, kind, data, rid=None, revision=None):
        if (
            kind not in KINDS
            or not isinstance(data, dict)
            or not str(data.get("title", "")).strip()
        ):
            raise ValueError("A collection type and title are required")
        if not isinstance(data["title"], str) or not isinstance(data.get("body", ""), str):
            raise ValueError("Title and notes must be text")
        if len(json.dumps(data)) > 1_000_000:
            raise ValueError("Record is too large")
        if kind in {"bookmarks", "reading_list"}:
            from app.services.browser_library import clean_url

            if not clean_url(data.get("url", "")):
                raise ValueError("Browser links require an HTTP or HTTPS URL")
        from .reconcile import COLOURS

        if not isinstance(data.get("flags", []), list) or any(
            flag not in COLOURS for flag in data.get("flags", [])
        ):
            raise ValueError("Invalid flag colour")
        rid = rid or uuid.uuid4().hex
        if not re.fullmatch(r"[a-f0-9]{32}", rid):
            raise ValueError("Invalid record ID")
        for key in ["emails", "phones", "flags", "destinations", "labels"]:
            if key in data and (
                not isinstance(data[key], list) or any(not isinstance(v, str) for v in data[key])
            ):
                raise ValueError("Invalid record values")
        with self.db() as db:
            row = db.execute(
                "SELECT profile,revision,kind FROM collection WHERE id=?", (rid,)
            ).fetchone()
            if row and (row["profile"] != profile or row["kind"] != kind):
                raise ValueError("Record not found")
            if row and revision is not None and row["revision"] != revision:
                raise ValueError("Record changed; reload before saving")
            db.execute(
                "INSERT INTO collection VALUES(?,?,?,?,?,?) ON CONFLICT(id) DO UPDATE SET data=excluded.data, revision=excluded.revision, updated=excluded.updated",
                (rid, profile, kind, json.dumps(data), row["revision"] + 1 if row else 1, now()),
            )
        return self.record(profile, rid)

    def replica(self, cid, remote):
        with self.db() as db:
            row = db.execute(
                "SELECT * FROM replicas WHERE connection=? AND remote=?", (cid, remote)
            ).fetchone()
        return {**dict(row), "base": json.loads(row["base"])} if row else None

    def replicas(self, cid):
        with self.db() as db:
            return [
                dict(r) for r in db.execute("SELECT * FROM replicas WHERE connection=?", (cid,))
            ]

    def acknowledge(self, cid, remote, rid, data, version=""):
        with self.db() as db:
            db.execute(
                "INSERT INTO replicas VALUES(?,?,?,?,?) ON CONFLICT(connection,remote) DO UPDATE SET base=excluded.base, version=excluded.version",
                (cid, remote, rid, json.dumps(data), version),
            )
            db.execute("DELETE FROM conflicts WHERE connection=? AND remote=?", (cid, remote))
            db.execute("DELETE FROM pending_exports WHERE connection=? AND record=?", (cid, rid))

    def conflict(self, cid, remote, rid, incoming, version):
        with self.db() as db:
            db.execute(
                "INSERT OR REPLACE INTO conflicts VALUES(?,?,?,?,?)",
                (cid, remote, rid, json.dumps(incoming), version),
            )

    def conflicts(self, profile):
        with self.db() as db:
            return [
                dict(r)
                for r in db.execute(
                    "SELECT x.* FROM conflicts x JOIN connections c ON x.connection=c.id WHERE c.profile=?",
                    (profile,),
                )
            ]

    def begin_export(self, cid, rid, kind):
        with self.db() as db:
            if db.execute(
                "SELECT 1 FROM pending_exports WHERE connection=? AND record=?", (cid, rid)
            ).fetchone():
                raise ValueError(
                    "An earlier create has an uncertain outcome. Review the destination and link the existing record before retrying."
                )
            db.execute("INSERT INTO pending_exports VALUES(?,?,?,?)", (cid, rid, kind, now()))

    def pending_exports(self, profile):
        with self.db() as db:
            return [
                dict(r)
                for r in db.execute(
                    "SELECT p.* FROM pending_exports p JOIN connections c ON c.id=p.connection WHERE c.profile=?",
                    (profile,),
                )
            ]

    def setup(self, profile, data=None):
        if data and data.get("self_contact"):
            contact = self.record(profile, data["self_contact"])
            if not contact or contact["kind"] != "contacts":
                raise ValueError("Choose a contact from this profile")
        with self.db() as db:
            if data is not None:
                clean = {
                    "display_name": str(data.get("display_name", "")).strip()[:100],
                    "completed": bool(data.get("completed")),
                    "self_contact": data.get("self_contact", ""),
                    "story_id": str(data.get("story_id", "")),
                    "step": max(0, min(int(data.get("step", 0)), 6)),
                    "deferred": bool(data.get("deferred", False)),
                    "updated": now(),
                }
                db.execute("INSERT OR REPLACE INTO setup VALUES(?,?)", (profile, json.dumps(clean)))
            row = db.execute("SELECT data FROM setup WHERE profile=?", (profile,)).fetchone()
        return json.loads(row[0]) if row else {"completed": False, "display_name": ""}
