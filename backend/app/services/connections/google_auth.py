"""Google authorization code + PKCE; refresh credentials stay in uCore's secret store."""

from __future__ import annotations

import base64
import hashlib
import json
import secrets
import time
from threading import Lock
import urllib.error
import urllib.parse
import urllib.request

from app.secret.store import AESGCM, get_store

SCOPES = {
    "tasks": "https://www.googleapis.com/auth/tasks",
    "contacts": "https://www.googleapis.com/auth/contacts",
    "notes": "https://www.googleapis.com/auth/drive.file",
    "calendar": "https://www.googleapis.com/auth/calendar.events https://www.googleapis.com/auth/calendar.calendarlist.readonly",
    "mail": "https://www.googleapis.com/auth/gmail.modify",
}
_PENDING = {}
_CREDENTIAL_LOCK = Lock()


class _NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


def request_json(url, *, method="GET", data=None, headers=None, form=False, timeout=25, follow_redirects=True):
    body = (
        urllib.parse.urlencode(data).encode()
        if form
        else json.dumps(data).encode()
        if data is not None
        else None
    )
    request = urllib.request.Request(
        url,
        data=body,
        method=method,
        headers={
            **(headers or {}),
            **(
                {
                    "Content-Type": "application/x-www-form-urlencoded"
                    if form
                    else "application/json"
                }
                if body
                else {}
            ),
        },
    )
    try:
        open_request = urllib.request.urlopen if follow_redirects else urllib.request.build_opener(_NoRedirect()).open
        with open_request(request, timeout=timeout) as response:
            raw = response.read(8_000_001)
            if len(raw) > 8_000_000:
                raise RuntimeError("Google response exceeded the connection budget")
            value = json.loads(raw) if raw else {}
            if isinstance(value, dict) and response.headers.get("ETag"):
                value["_http_etag"] = response.headers["ETag"]
            return value
    except urllib.error.HTTPError as exc:
        raise RuntimeError(
            f"Google returned HTTP {exc.code}; reconnect for authorization errors or retry later"
        ) from None


def secret_key(connection):
    return "CONNECTION_GOOGLE_" + connection["id"]


def token_data(connection):
    if AESGCM is None:
        raise RuntimeError("Encrypted credential storage is unavailable")
    value = get_store().get(secret_key(connection))
    return json.loads(value) if value else {}


def client():
    store = get_store()
    import os

    cid = (
        store.get("GOOGLE_OAUTH_CLIENT_ID")
        or store.get("GOOGLE_CLIENT_ID")
        or os.environ.get("GOOGLE_OAUTH_CLIENT_ID")
        or os.environ.get("GOOGLE_CLIENT_ID")
    )
    if not cid:
        raise ValueError("Configure the Google OAuth desktop client in Advanced Settings first")
    return {
        "client_id": cid,
        "client_secret": store.get("GOOGLE_OAUTH_CLIENT_SECRET")
        or store.get("GOOGLE_CLIENT_SECRET")
        or os.environ.get("GOOGLE_CLIENT_SECRET")
        or "",
    }


def require_direct_google(profile_id, *, administrator=False):
    """Use the stored local role for every new provider operation."""
    from app.services.identity import load_identity

    profile = next((item for item in load_identity().profiles if item.id == profile_id), None)
    role = str(profile.role).casefold() if profile else ""
    allowed = {"wizard", "owner"} if administrator else {"wizard", "owner", "sorcerer", "sorceror"}
    if role not in allowed:
        raise PermissionError("Direct Google access requires an authorized local role.")


def start(connection, redirect):
    require_direct_google(connection["profile"])
    if AESGCM is None:
        raise ValueError("Encrypted credential storage is required")
    if not redirect.startswith("http://127.0.0.1:"):
        raise ValueError("Google sign-in requires a loopback callback")
    kinds = connection["config"]["collections"]
    if not kinds:
        raise ValueError("Choose collections before signing in")
    with _CREDENTIAL_LOCK:
        current = time.time()
        for old in list(_PENDING):
            if _PENDING[old]["expires"] < current:
                del _PENDING[old]
        state, verifier = secrets.token_urlsafe(32), secrets.token_urlsafe(48)
        _PENDING[state] = {
            "connection": connection,
            "verifier": verifier,
            "redirect": redirect,
            "expires": current + 600,
        }
    challenge = (
        base64.urlsafe_b64encode(hashlib.sha256(verifier.encode()).digest()).decode().rstrip("=")
    )
    return "https://accounts.google.com/o/oauth2/v2/auth?" + urllib.parse.urlencode(
        {
            "client_id": client()["client_id"],
            "redirect_uri": redirect,
            "response_type": "code",
            "scope": "openid email " + " ".join(SCOPES[k] for k in kinds),
            "state": state,
            "code_challenge": challenge,
            "code_challenge_method": "S256",
            "access_type": "offline",
            "prompt": "select_account consent",
        }
    )


def finish(state, code):
    with _CREDENTIAL_LOCK:
        pending = _PENDING.get(state)
        if not pending or pending.get("claimed") or pending["expires"] < time.time():
            if pending and pending["expires"] < time.time():
                _PENDING.pop(state, None)
            raise ValueError("Sign-in expired; start again from Connections")
        pending["claimed"] = True
    connection = pending["connection"]
    require_direct_google(connection["profile"])
    result = request_json(
        "https://oauth2.googleapis.com/token",
        method="POST",
        form=True,
        data={
            **client(),
            "code": code,
            "code_verifier": pending["verifier"],
            "redirect_uri": pending["redirect"],
            "grant_type": "authorization_code",
        },
    )
    required = {scope for k in connection["config"]["collections"] for scope in SCOPES[k].split()}
    granted = set(result.get("scope", "").split())
    if not result.get("refresh_token") or not required <= granted:
        raise ValueError(
            "Required permissions were not granted; reconnect and choose the collections again"
        )
    require_direct_google(connection["profile"])
    account = request_json(
        "https://openidconnect.googleapis.com/v1/userinfo",
        headers={"Authorization": "Bearer " + result["access_token"]},
    )
    from .store import CollectionStore

    with _CREDENTIAL_LOCK:
        if _PENDING.pop(state, None) is not pending or pending["expires"] < time.time():
            raise ValueError("Sign-in expired or was cancelled")
        require_direct_google(connection["profile"])
        store = CollectionStore()
        latest = store.connection(connection["profile"], connection["id"])
        if not latest:
            raise ValueError("Connection no longer exists")
        if latest["config"]["collections"].keys() != connection["config"]["collections"].keys():
            raise ValueError("Connection collections changed during sign-in")
        result["account_subject"] = account.get("sub", "")
        result["expires_at"] = time.time() + result.get("expires_in", 3600)
        credentials = get_store()
        credentials.set(secret_key(connection), json.dumps(result))
        credentials.save()
        store.health(connection["id"], account=account.get("email", "Google account"), state="scope_required", error="")
    return connection


def disconnect_credentials(connection):
    """Cancel pending sign-ins and remove credentials in one critical section."""
    key = secret_key(connection)
    with _CREDENTIAL_LOCK:
        for state, pending in list(_PENDING.items()):
            if secret_key(pending["connection"]) == key:
                del _PENDING[state]
        credentials = get_store()
        credentials.delete(key)
        credentials.save()


def access_token(connection):
    require_direct_google(connection["profile"])
    value = token_data(connection)
    if not value:
        raise RuntimeError("Google sign-in required")
    expected_subject = connection.get("_drone_account_subject")
    if expected_subject and value.get("account_subject") != expected_subject:
        raise PermissionError("The enrolled Google account changed")
    check = connection.get("_drone_check")
    if check:
        check()
    required = {scope for k in connection["config"]["collections"] for scope in SCOPES[k].split()}
    if not required <= set(value.get("scope", "").split()):
        raise RuntimeError("Reconnect Google to authorize the selected collections")
    if value.get("expires_at", 0) < time.time() + 60:
        original = value.copy()
        options = {"timeout": max(0.1, connection["_deadline"] - time.monotonic()), "follow_redirects": False} if check else {}
        result = request_json(
            "https://oauth2.googleapis.com/token",
            method="POST",
            form=True,
            **options,
            data={
                **client(),
                "refresh_token": value["refresh_token"],
                "grant_type": "refresh_token",
            },
        )
        value.update(result)
        value["expires_at"] = time.time() + result.get("expires_in", 3600)
        with _CREDENTIAL_LOCK:
            require_direct_google(connection["profile"])
            if check:
                check()
            if token_data(connection) != original:
                raise RuntimeError("Google credentials changed; retry the connection")
            get_store().set(secret_key(connection), json.dumps(value))
            get_store().save()
    return value["access_token"]
