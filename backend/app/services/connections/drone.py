"""Read-only Google Tasks gateway hosted by the existing connections service."""

import logging
import time
import uuid

from app.services.identity import load_identity

from .google_auth import require_direct_google, token_data
from .providers import GoogleAdapter, quote

log = logging.getLogger(__name__)
MAX_DURATION = 24 * 60 * 60
REQUEST_INTERVAL = 60


def _profile_exists(profile):
    return any(item.id == profile for item in load_identity().profiles)


def _list_allowed(connection, list_id):
    scope = connection["config"]["collections"].get("tasks", {})
    return (list_id in scope.get("lists", [])
            and scope.get("selection", "all") == "all"
            and scope.get("filter", "all") == "all")


def enroll(store, owner, *, recipient, connection_id, list_id, duration):
    require_direct_google(owner, administrator=True)
    if recipient == owner or not _profile_exists(recipient):
        raise ValueError("Choose another existing local profile")
    if not isinstance(duration, int) or isinstance(duration, bool) or not 60 <= duration <= MAX_DURATION:
        raise ValueError("Grant duration must be between one minute and 24 hours")
    connection = store.connection(owner, connection_id)
    if not connection or connection["provider"] != "google":
        raise ValueError("Choose a Google connection you own")
    if connection["health"].get("state") == "disconnected":
        raise ValueError("Connect the Google account first")
    if not _list_allowed(connection, list_id):
        raise ValueError("Choose a task list configured for all records")
    subject = token_data(connection).get("account_subject")
    if not subject:
        raise ValueError("Sign in again to verify the Google account before enrollment")
    grant = uuid.uuid4().hex
    with store.db() as db:
        db.execute(
            """INSERT INTO drone_grants
               (id, owner, recipient, connection, account_subject, list_id, expires)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (grant, owner, recipient, connection_id, subject, list_id, time.time() + duration),
        )
    log.info("Drone grant enrolled id=%s owner=%s recipient=%s", grant, owner, recipient)
    return grant


def grants(store, profile):
    with store.db() as db:
        return [dict(row) for row in db.execute(
            """SELECT id, owner, recipient, connection, expires, revoked, last_used
               FROM drone_grants WHERE owner=? OR recipient=? ORDER BY expires DESC""",
            (profile, profile),
        )]


def revoke(store, owner, grant):
    require_direct_google(owner, administrator=True)
    with store.db() as db:
        updated = db.execute(
            "UPDATE drone_grants SET revoked=COALESCE(revoked, ?) WHERE id=? AND owner=?",
            (time.time(), grant, owner),
        )
        if not updated.rowcount:
            raise PermissionError("Drone grant is unavailable")
    log.info("Drone grant revoked id=%s owner=%s", grant, owner)


def revoke_connection(store, owner, connection):
    with store.db() as db:
        db.execute(
            """UPDATE drone_grants SET revoked=?
               WHERE owner=? AND connection=? AND revoked IS NULL""",
            (time.time(), owner, connection),
        )


def preview(store, recipient, grant):
    def check():
        with store.db() as db:
            row = db.execute(
                """SELECT * FROM drone_grants WHERE id=? AND recipient=?
                   AND revoked IS NULL AND expires>?""",
                (grant, recipient, time.time()),
            ).fetchone()
        if row is None or not _profile_exists(recipient):
            raise PermissionError("Drone grant expired, was revoked, or is unavailable")
        require_direct_google(row["owner"], administrator=True)
        connection = store.connection(row["owner"], row["connection"])
        if not connection or connection["health"].get("state") == "disconnected":
            raise PermissionError("The enrolled connection is disconnected")
        if not _list_allowed(connection, row["list_id"]):
            raise PermissionError("The enrolled list is outside the current connection scope")
        return row, connection

    row, connection = check()
    with store.db() as db:
        current = time.time()
        claimed = db.execute(
            """UPDATE drone_grants SET last_used=? WHERE id=? AND revoked IS NULL AND expires>?
               AND (last_used IS NULL OR last_used<=?)""",
            (current, grant, current, current - REQUEST_INTERVAL),
        )
        if not claimed.rowcount:
            raise PermissionError("Drone preview is unavailable or was requested within the last minute")
    list_id = row["list_id"]
    encoded = quote(list_id)
    connection.update(
        _deadline=time.monotonic() + 25,
        _drone_check=check,
        _drone_account_subject=row["account_subject"],
        _drone_urls={
            f"https://tasks.googleapis.com/tasks/v1/users/@me/lists/{encoded}",
            f"https://tasks.googleapis.com/tasks/v1/lists/{encoded}/tasks",
        },
    )
    log.info("Drone preview started id=%s recipient=%s", grant, recipient)
    records = GoogleAdapter().pull(connection, "tasks", {"lists": [list_id]})
    check()
    log.info("Drone preview completed id=%s recipient=%s", grant, recipient)
    return {
        "provenance": {"provider": "google", "operation": "tasks.preview", "grant": grant},
        "records": records[:100],
        "truncated": len(records) > 100,
    }
