from __future__ import annotations

import asyncio
import hashlib
import json
import platform
import time
from datetime import UTC, datetime, timedelta

from .reconcile import combine_records, merge_fields, selected
from .store import CollectionStore, now

_LOCKS: dict[str, asyncio.Lock] = {}


class SyncEngine:
    def __init__(self, store=None, adapters=None):
        self.store = store or CollectionStore()
        if adapters is None:
            from .providers import AppleAdapter, GoogleAdapter

            adapters = {"apple": AppleAdapter(), "google": GoogleAdapter()}
        self.adapters = adapters

    async def sync(self, profile, cid, *, manual=False):
        connection = self.store.connection(profile, cid)
        if not connection:
            raise ValueError("Connection not found")
        if not manual and not connection["config"]["enabled"]:
            return {"state": "disabled"}
        from .providers import provider_capabilities

        capabilities = provider_capabilities(connection["provider"], host_platform=platform.system())
        if not capabilities["adapter_available"]:
            self.store.health(cid, state="unsupported_platform", error="Provider adapter is unavailable on this host")
            return {"state": "unsupported_platform", "error": "Provider adapter is unavailable on this host"}
        connection["_manual"] = manual
        lock = _LOCKS.setdefault(profile, asyncio.Lock())
        if lock.locked():
            return {"state": "running"}
        async with lock:
            self.store.health(cid, state="running", last_attempt=now())
            try:
                # A single bounded native/network worker owns each connection.
                worker = asyncio.create_task(asyncio.to_thread(self._sync, connection))
                try:
                    result = await asyncio.shield(worker)
                except asyncio.CancelledError:
                    # Native calls cannot be killed safely. Retain the connection lock
                    # until the bounded worker exits, including during server shutdown.
                    await worker
                    raise
                self.store.health(cid, **result, last_success=now(), failures=0, next_attempt=None)
                return result
            except Exception as exc:
                latest = self.store.connection(profile, cid)
                if not latest or (
                    not latest["config"]["enabled"] and not connection.get("_manual")
                ):
                    return {"state": "disabled"}
                attempts = int(connection["health"].get("failures", 0)) + 1
                retry = datetime.now(UTC) + timedelta(seconds=min(3600, 60 * 2 ** min(attempts, 6)))
                # Provider errors deliberately contain no request bodies or credentials.
                self.store.health(
                    cid,
                    state="error",
                    error=str(exc)[:250],
                    failures=attempts,
                    next_attempt=retry.isoformat(),
                )
                return {"state": "error", "error": str(exc)[:250]}

    def _sync(self, connection):
        cid, profile = connection["id"], connection["profile"]
        adapter = self.adapters[connection["provider"]]
        connection["_deadline"] = time.monotonic() + 90
        self.refresh_tasks(profile)
        self.refresh_notes(profile)
        pulled = updated = pushed = unchanged = conflicts = automated = 0
        for kind, scope in connection["config"]["collections"].items():
            if time.monotonic() > connection["_deadline"]:
                raise RuntimeError("Sync time budget reached; remaining sources will retry")
            if not scope.get("lists"):
                continue
            incoming = adapter.pull(connection, kind, scope)
            seen = set()
            unresolved = {
                item["remote"]
                for item in self.store.conflicts(profile)
                if item["connection"] == cid
            }
            for remote in incoming:
                remote_id = kind + ":" + remote["id"]
                data = remote["data"]
                if kind == "tasks" and scope.get("local_list"):
                    data = {**data, "local_list": scope["local_list"]}
                if not selected(data, scope, remote["id"]):
                    continue
                seen.add(remote_id)
                replica = self.store.replica(cid, remote_id)
                record = self.store.record(profile, replica["record"]) if replica else None
                if record and remote_id in unresolved:
                    self.store.conflict(
                        cid, remote_id, record["id"], data, remote.get("version", "")
                    )
                    conflicts += 1
                    continue
                if record:
                    merged, collision = merge_fields(replica["base"], record["data"], data)
                    if collision:
                        self.store.conflict(
                            cid, remote_id, record["id"], data, remote.get("version", "")
                        )
                        conflicts += 1
                        continue
                    if merged != record["data"]:
                        record = self.store.save(
                            profile, kind, merged, record["id"], revision=record["revision"]
                        )
                        updated += 1
                    else:
                        unchanged += 1
                else:
                    record = self.store.save(profile, kind, data)
                    pulled += 1
                # Baseline is the last remote representation, not pending local edits.
                self.store.acknowledge(
                    cid, remote_id, record["id"], data, remote.get("version", "")
                )
                self.project(
                    profile, record, origin=(cid, remote_id, data, remote.get("version", ""))
                )
                if (
                    kind != "tasks"
                    and scope.get("flag_action") == "create-task"
                    and (
                        record["data"].get("flags")
                        or record["data"].get("starred")
                        or record["data"].get("vip")
                    )
                ):
                    automated += self.flag_task(profile, cid, record, scope)
            if scope.get("direction") != "both":
                continue
            blocked = {
                row["record"] for row in self.store.conflicts(profile) if row["connection"] == cid
            }
            replicas = self.store.replicas(cid)
            for record in self.store.records(profile, kind):
                data = record["data"]
                if record["id"] in blocked or data.get("merged_into") or data.get("deleted"):
                    continue
                mappings = [
                    r
                    for r in replicas
                    if r["record"] == record["id"] and r["remote"].startswith(kind + ":")
                ]
                # Outbound sharing is explicit per record, or an existing mapped replica.
                if not mappings and cid not in data.get("destinations", []):
                    continue
                if not mappings:
                    mappings = [None]
                for mapping in mappings:
                    if mapping and mapping["remote"] not in seen:
                        continue
                    if not mapping and (
                        scope.get("selection") == "records" or not selected(data, scope, "")
                    ):
                        continue
                    if time.monotonic() > connection["_deadline"]:
                        raise RuntimeError(
                            "Sync time budget reached; retry will resume mapped records"
                        )
                    if mapping:
                        baseline = json.loads(mapping["base"])
                        exported = (
                            adapter.representation(kind, data, scope)
                            if hasattr(adapter, "representation")
                            else data
                        )
                        writable = set(exported)
                        if all(exported.get(key) == baseline.get(key) for key in writable):
                            continue
                    latest = self.store.connection(profile, cid)
                    if not latest or (
                        not latest["config"]["enabled"] and not connection.get("_manual")
                    ):
                        raise ValueError("Connection disabled")
                    if not mapping:
                        self.store.begin_export(cid, record["id"], kind)
                    result = adapter.push(connection, kind, scope, record, mapping)
                    snapshot = json.loads(mapping["base"]) if mapping else {}
                    exported = (
                        adapter.representation(kind, data, scope)
                        if hasattr(adapter, "representation")
                        else data
                    )
                    snapshot.update(exported)
                    self.store.acknowledge(
                        cid,
                        kind + ":" + result["id"],
                        record["id"],
                        snapshot,
                        result.get("version", ""),
                    )
                    pushed += 1
        self.project_feed(profile)
        conflicts = sum(item["connection"] == cid for item in self.store.conflicts(profile))
        return {
            "state": "conflict" if conflicts else "connected",
            "error": "",
            "pulled": pulled,
            "updated": updated,
            "pushed": pushed,
            "automated_tasks": automated,
            "unchanged": unchanged,
            "conflicts": conflicts,
        }

    def flag_task(self, profile, cid, source, scope):
        """An explicitly configured flag rule creates a linked task once, never per poll."""
        rule_id = "flag-rule:" + cid
        if self.store.replica(rule_id, source["id"]):
            return 0
        tab = {"contacts": "contacts", "notes": "notes"}.get(source["kind"], "feeds")
        source_link = f"/workflow?tab={tab}&record={source['id']}"
        data = {
            "title": source["data"]["title"],
            "body": source["data"].get("body", "") + f"\n\n[Source item]({source_link})",
            "status": "todo",
            "origin_record": source["id"],
            "local_list": scope.get("flag_task_list") or "inbox",
        }
        task = self.store.save(profile, "tasks", data)
        self.store.acknowledge(rule_id, source["id"], task["id"], source["data"])
        self.project(profile, task)
        return 1

    def project_feed(self, profile):
        from app.services.feed_store import FeedServer, profile_feed_path

        feed = FeedServer(str(profile_feed_path(profile)))
        try:
            for record in self.store.records(profile):
                if record["kind"] not in {"mail", "calendar"} or record["data"].get("merged_into"):
                    continue
                data = record["data"]
                feed.ingest_activity_sync(
                    source=record["kind"],
                    external_id=record["id"],
                    type=record["kind"],
                    title=data["title"],
                    content=data.get("body", ""),
                    importance=0.85
                    if data.get("starred") or data.get("vip") or data.get("flags")
                    else 0.65,
                    metadata={
                        "profile": profile,
                        "collection_id": record["id"],
                        "vip": bool(data.get("vip")),
                        "is_flagged": bool(data.get("starred") or data.get("flags")),
                        "flags": data.get("flags", []),
                    },
                )
        finally:
            feed.close()

    def refresh_tasks(self, profile):
        """Mirror uFlow records, never another profile's task files."""
        import yaml

        from app.api.tasker_api import _is_user_workflow_task, _parse_markdown_task
        from app.flow.task_store import default_tasker_dir

        local_connection = "uflow:" + profile
        base = default_tasker_dir().resolve()
        for mapping in self.store.replicas(local_connection):
            if mapping["remote"].rsplit("/", 1)[-1].lower() == "readme.md":
                record = self.store.record(profile, mapping["record"])
                if record and record["data"] == json.loads(mapping["base"]):
                    self.store.save(
                        profile,
                        "tasks",
                        {**record["data"], "excluded_from_tasks": True},
                        record["id"],
                    )
        for path in base.glob("*/*.md"):
            if path.name.lower() == "readme.md":
                continue
            content = path.read_text(encoding="utf-8")
            try:
                meta = (
                    yaml.safe_load(content.split("---", 2)[1]) if content.startswith("---") else {}
                )
            except (ValueError, IndexError, yaml.YAMLError):
                continue
            owner = (meta or {}).get("profile")
            # Legacy tasks belong to the default local profile, not all profiles.
            if owner != profile and not (not owner and profile == "default"):
                continue
            if (meta or {}).get("source") == "user-connection":
                rid = (meta or {}).get("collection_id")
                record = self.store.record(profile, rid) if rid else None
            else:
                replica = self.store.replica(local_connection, str(path.relative_to(base)))
                record = self.store.record(profile, replica["record"]) if replica else None
            if record and record["data"].get("merged_into"):
                continue
            task = _parse_markdown_task(path)
            if not owner and not _is_user_workflow_task(task):
                continue
            data = {
                **(record["data"] if record else {}),
                "title": task["title"],
                "body": task.get("description") or "",
                "status": task["status"],
                "due": str(task.get("due") or ""),
            }
            if not record or data != record["data"]:
                record = self.store.save(profile, "tasks", data, record["id"] if record else None)
            self.store.acknowledge(
                local_connection, str(path.relative_to(base)), record["id"], data
            )

    def refresh_notes(self, profile):
        from app.core.settings import settings

        folder = (
            settings.vault_root / "Connections" / hashlib.sha256(profile.encode()).hexdigest()[:10]
        )
        for record in self.store.records(profile, "notes"):
            path = folder / (record["id"] + ".md")
            if path.is_file() and not record["data"].get("merged_into"):
                content = path.read_text(encoding="utf-8")
                title, _, body = content.partition("\n")
                data = {
                    **record["data"],
                    "title": title.removeprefix("# ").strip() or record["data"]["title"],
                    "body": body.lstrip("\n"),
                }
                if data != record["data"]:
                    self.store.save(profile, "notes", data, record["id"])
                self.store.acknowledge("notes:" + profile, record["id"], record["id"], data)

    def project(self, profile, record, origin=None):
        if record["kind"] == "notes" and not record["data"].get("merged_into"):
            from app.core.settings import settings

            folder = (
                settings.vault_root
                / "Connections"
                / hashlib.sha256(profile.encode()).hexdigest()[:10]
            )
            folder.mkdir(parents=True, exist_ok=True)
            path = folder / (record["id"] + ".md")
            snapshot = self.store.replica("notes:" + profile, record["id"])
            if path.exists() and snapshot:
                title, _, body = path.read_text(encoding="utf-8").partition("\n")
                actual = {
                    **record["data"],
                    "title": title.removeprefix("# ").strip(),
                    "body": body.lstrip("\n"),
                }
                merged, collisions = merge_fields(snapshot["base"], actual, record["data"])
                if collisions:
                    self.store.save(profile, "notes", actual, record["id"])
                    if origin:
                        cid, remote_id, incoming, version = origin
                        self.store.conflict(cid, remote_id, record["id"], incoming, version)
                    raise ValueError("Note was edited during sync; reload and review the changes")
                if merged != record["data"]:
                    record = self.store.save(profile, "notes", merged, record["id"])
            temporary = path.with_suffix(".tmp")
            temporary.write_text(
                "# " + record["data"]["title"] + "\n\n" + record["data"].get("body", ""),
                encoding="utf-8",
            )
            temporary.replace(path)
            self.store.acknowledge("notes:" + profile, record["id"], record["id"], record["data"])
            return
        if record["kind"] != "tasks" or record["data"].get("merged_into"):
            return
        from app.api.tasker_api import _parse_markdown_task, _update_task_file
        from app.flow.task_store import default_tasker_dir, slugify, write_task_markdown

        data = record["data"]
        for mapping in self.store.replicas("uflow:" + profile):
            if mapping["record"] != record["id"]:
                continue
            base = default_tasker_dir().resolve()
            path = (base / mapping["remote"]).resolve()
            if path.is_relative_to(base) and path.is_file():
                task = _parse_markdown_task(path)
                actual = {
                    **record["data"],
                    "title": task["title"],
                    "body": task.get("description") or "",
                    "status": task["status"],
                    "due": str(task.get("due") or ""),
                }
                baseline = json.loads(mapping["base"])
                local, collisions = merge_fields(baseline, actual, record["data"])
                if collisions:
                    self.store.save(profile, "tasks", actual, record["id"])
                    if origin:
                        cid, remote_id, incoming, version = origin
                        self.store.conflict(cid, remote_id, record["id"], incoming, version)
                    raise ValueError("Task was edited during sync; review competing changes")
                if local != record["data"]:
                    record = self.store.save(profile, "tasks", local, record["id"])
                    data = local
                _update_task_file(
                    base=base,
                    task_id=task["id"],
                    patch={
                        "title": data["title"],
                        "body": data.get("body", ""),
                        "status": data.get("status", "todo"),
                        "due": data.get("due", ""),
                    },
                )
                return
        # A profile-owned board prevents mixing imported tasks across local profiles.
        board = slugify(str(data.get("local_list") or data.get("list") or "inbox"))[:80]
        if profile != "default":
            board = "user-" + hashlib.sha256(profile.encode()).hexdigest()[:10] + "-" + board
        write_task_markdown(
            title=data["title"],
            board=board,
            status=data.get("status", "todo"),
            body=data.get("body", ""),
            task=f"connection-{record['id']}",
            source="user-connection",
            source_id=record["id"],
            metadata={
                "id": record["id"],
                "due": data.get("due"),
                "profile": profile,
                "collection_id": record["id"],
            },
        )

    def merge(self, profile, keep, other):
        left, right = self.store.record(profile, keep), self.store.record(profile, other)
        if not left or not right or keep == other or left["kind"] != right["kind"]:
            raise ValueError("Choose two records of the same type")
        result = self.store.save(
            profile, left["kind"], combine_records(left["data"], right["data"]), keep
        )
        self.store.save(profile, right["kind"], {**right["data"], "merged_into": keep}, other)
        if right["kind"] == "tasks":
            from app.api.tasker_api import _parse_markdown_task, _update_task_file
            from app.flow.task_store import default_tasker_dir

            base = default_tasker_dir().resolve()
            for mapping in self.store.replicas("uflow:" + profile):
                path = (base / mapping["remote"]).resolve()
                if mapping["record"] == other and path.is_relative_to(base) and path.is_file():
                    task = _parse_markdown_task(path)
                    _update_task_file(base=base, task_id=task["id"], patch={"merged_into": keep})
        with self.store.db() as db:
            db.execute("UPDATE replicas SET record=? WHERE record=?", (keep, other))
            db.execute("UPDATE conflicts SET record=? WHERE record=?", (keep, other))
        self.project(profile, result)
        return result

    def link(self, profile, cid, rid, remote):
        connection = self.store.connection(profile, cid)
        record = self.store.record(profile, rid)
        if not connection or not record:
            raise ValueError("Connection or record not found")
        kind = record["kind"]
        scope = connection["config"]["collections"].get(kind)
        if not scope:
            raise ValueError("Choose this collection first")
        incoming = self.adapters[connection["provider"]].pull(connection, kind, scope)
        item = next((r for r in incoming if r["id"] == remote), None)
        if not item:
            raise ValueError("Choose an existing remote record in the selected lists")
        previous = self.store.replica(cid, kind + ":" + remote)
        if previous and previous["record"] != rid:
            raise ValueError("Remote record already linked; combine its local records instead")
        self.store.acknowledge(cid, kind + ":" + remote, rid, item["data"], item.get("version", ""))
        self.store.conflict(cid, kind + ":" + remote, rid, item["data"], item.get("version", ""))
        return {"state": "review_required"}

    def resolve(self, profile, cid, remote, choice):
        row = next(
            (
                r
                for r in self.store.conflicts(profile)
                if r["connection"] == cid and r["remote"] == remote
            ),
            None,
        )
        if not row or choice not in {"local", "remote", "combine"}:
            raise ValueError("Conflict not found or invalid resolution")
        record = self.store.record(profile, row["record"])
        incoming = json.loads(row["incoming"])
        data = (
            incoming
            if choice == "remote"
            else combine_records(record["data"], incoming)
            if choice == "combine"
            else record["data"]
        )
        result = self.store.save(profile, record["kind"], data, record["id"])
        self.store.acknowledge(cid, remote, record["id"], incoming, row["version"])
        self.project(profile, result)
        return result


async def sync_due_connections():
    engine = SyncEngine()
    current = datetime.now(UTC)
    for connection in engine.store.connections():
        health = connection["health"]
        retry = health.get("next_attempt") or health.get("last_attempt")
        if retry:
            stamp = datetime.fromisoformat(retry)
            if health.get("next_attempt") and stamp > current:
                continue
            if (
                not health.get("next_attempt")
                and (current - stamp).total_seconds() < connection["config"]["interval"]
            ):
                continue
        if connection["config"]["enabled"]:
            from app.services.snackbar_sync import sync_connection

            await sync_connection(connection["profile"], connection["id"], store=engine.store)
