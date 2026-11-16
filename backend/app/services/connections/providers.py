from __future__ import annotations

import json
import time
import urllib.parse

from .google_auth import access_token, request_json


def quote(value):
    return urllib.parse.quote(str(value), safe="")


class GoogleAdapter:
    writable = {
        "tasks": {"title", "body", "status", "due"},
        "contacts": {"title", "body", "emails", "phones", "starred"},
        "notes": {"title", "body", "starred"},
        "calendar": {"title", "body", "start", "end"},
        "mail": {"read", "starred", "flags"},
    }

    def api(self, connection, url, *, method="GET", data=None, version=""):
        if time.monotonic() > connection.get("_deadline", float("inf")):
            raise RuntimeError("Sync time budget reached")
        check = connection.get("_drone_check")
        if check and (method != "GET" or url.split("?", 1)[0] not in connection["_drone_urls"]):
            raise PermissionError("Drone request is outside the enrolled scope")
        headers = {"Authorization": "Bearer " + access_token(connection)}
        if check:
            check()
        if version:
            headers["If-Match"] = version
        options = {}
        if check:
            remaining = connection["_deadline"] - time.monotonic()
            if remaining <= 0:
                raise RuntimeError("Drone preview time budget reached")
            options = {"timeout": remaining, "follow_redirects": False}
        return request_json(url, method=method, data=data, headers=headers, **options)

    def pages(self, connection, url, key):
        rows, token = [], ""
        for _ in range(20):
            result = self.api(
                connection,
                url + ("&" if "?" in url else "?") + urllib.parse.urlencode({"pageToken": token}),
            )
            rows.extend(result.get(key, []))
            if connection.get("_drone_check") and len(rows) > 100:
                return rows[:101]
            token = result.get("nextPageToken", "")
            if not token:
                return rows
        raise RuntimeError("Collection exceeds 20 pages; choose a smaller sync scope")

    def drive_text(self, connection, file_id, content=None, version=""):
        import urllib.error

        if time.monotonic() > connection.get("_deadline", float("inf")):
            raise RuntimeError("Sync time budget reached")
        import urllib.request

        url = (
            ("https://www.googleapis.com/drive/v3/files/" + quote(file_id) + "?alt=media")
            if content is None
            else (
                "https://www.googleapis.com/upload/drive/v3/files/"
                + quote(file_id)
                + "?uploadType=media"
            )
        )
        req = urllib.request.Request(
            url,
            data=content.encode() if content is not None else None,
            method="PATCH" if content is not None else "GET",
            headers={
                "Authorization": "Bearer " + access_token(connection),
                "Content-Type": "text/markdown; charset=utf-8",
                **({"If-Match": version} if version else {}),
            },
        )
        try:
            with urllib.request.urlopen(req, timeout=25) as response:
                value = response.read(1_000_001)
                if len(value) > 1_000_000:
                    raise RuntimeError("Note exceeds the sync size budget")
                return value.decode("utf-8") if content is None else ""
        except urllib.error.HTTPError as exc:
            raise RuntimeError(f"Drive note returned HTTP {exc.code}") from None

    def representation(self, kind, data, scope=None):
        result = {key: data[key] for key in self.writable.get(kind, set()) if key in data}
        if kind == "tasks":
            result["status"] = "completed" if data.get("status") == "completed" else "todo"
        return result

    def discover(self, connection):
        result = {}
        for kind in connection["config"]["collections"]:
            if kind == "tasks":
                result[kind] = [
                    {"id": r["id"], "title": r["title"]}
                    for r in self.pages(
                        connection,
                        "https://tasks.googleapis.com/tasks/v1/users/@me/lists?maxResults=100",
                        "items",
                    )
                ]
            elif kind == "contacts":
                result[kind] = [{"id": "people/me", "title": "All my contacts"}] + [
                    {"id": group["resourceName"], "title": group["name"]}
                    for group in self.api(
                        connection, "https://people.googleapis.com/v1/contactGroups?pageSize=1000"
                    ).get("contactGroups", [])
                ]
            elif kind == "notes":
                result[kind] = [{"id": "app-files", "title": "uCore Markdown notes in Drive"}]
            elif kind == "mail":
                result[kind] = [
                    {"id": r["id"], "title": r["name"], "type": r.get("type")}
                    for r in self.api(
                        connection, "https://gmail.googleapis.com/gmail/v1/users/me/labels"
                    ).get("labels", [])
                ]
            elif kind == "calendar":
                result[kind] = [
                    {
                        "id": r["id"],
                        "title": r.get("summary", r["id"]),
                        "writable": r.get("accessRole") in {"owner", "writer"},
                    }
                    for r in self.pages(
                        connection,
                        "https://www.googleapis.com/calendar/v3/users/me/calendarList?maxResults=100",
                        "items",
                    )
                ]
        return result

    @staticmethod
    def strip_marker(body):
        import re

        return re.sub(r"\n*uCore record: [a-f0-9]+\s*$", "", body).strip()

    def pull(self, connection, kind, scope):
        rows = []
        for collection in scope["lists"]:
            if kind == "tasks":
                list_info = self.api(
                    connection,
                    f"https://tasks.googleapis.com/tasks/v1/users/@me/lists/{quote(collection)}",
                )
                values = self.pages(
                    connection,
                    f"https://tasks.googleapis.com/tasks/v1/lists/{quote(collection)}/tasks?showCompleted=true&showHidden=true&maxResults=100",
                    "items",
                )
                for item in values:
                    if item.get("deleted"):
                        continue
                    rows.append(
                        {
                            "id": collection + "/" + item["id"],
                            "version": item.get("etag", ""),
                            "data": {
                                "title": item.get("title") or "Untitled",
                                "body": self.strip_marker(item.get("notes", "")),
                                "status": "completed"
                                if item.get("status") == "completed"
                                else "todo",
                                "due": item.get("due", ""),
                                "list": list_info.get("title")
                                or scope.get("list_titles", {}).get(collection, collection),
                            },
                        }
                    )
            elif kind == "contacts":
                values = self.pages(
                    connection,
                    "https://people.googleapis.com/v1/people/me/connections?personFields=names,emailAddresses,phoneNumbers,biographies,memberships,metadata&pageSize=1000",
                    "connections",
                )
                for item in values:
                    groups = {
                        m.get("contactGroupMembership", {}).get("contactGroupResourceName")
                        for m in item.get("memberships", [])
                    }
                    if collection != "people/me" and collection not in groups:
                        continue
                    rows.append(
                        {
                            "id": item["resourceName"],
                            "version": item.get("etag", ""),
                            "data": {
                                "title": next(
                                    (
                                        n.get("displayName")
                                        for n in item.get("names", [])
                                        if n.get("displayName")
                                    ),
                                    "Unnamed contact",
                                ),
                                "emails": [v["value"] for v in item.get("emailAddresses", [])],
                                "phones": [v["value"] for v in item.get("phoneNumbers", [])],
                                "body": next(
                                    (v.get("value", "") for v in item.get("biographies", [])), ""
                                ),
                                "starred": any(
                                    m.get("contactGroupMembership", {}).get(
                                        "contactGroupResourceName"
                                    )
                                    == "contactGroups/starred"
                                    for m in item.get("memberships", [])
                                ),
                            },
                        }
                    )
            elif kind == "notes":
                query = "trashed=false and appProperties has { key='ucore' and value='note' }"
                values = self.pages(
                    connection,
                    "https://www.googleapis.com/drive/v3/files?"
                    + urllib.parse.urlencode(
                        {
                            "q": query,
                            "fields": "nextPageToken,files(id,name,description,starred,version,appProperties)",
                            "pageSize": 100,
                        }
                    ),
                    "files",
                )
                for item in values:
                    metadata = self.api(
                        connection,
                        f"https://www.googleapis.com/drive/v3/files/{quote(item['id'])}?fields=id,name,starred,version",
                    )
                    etag = metadata.get("_http_etag", "")
                    rows.append(
                        {
                            "id": item["id"],
                            "version": etag or str(metadata.get("version", "")),
                            "data": {
                                "title": metadata["name"],
                                "body": self.drive_text(connection, item["id"], version=etag),
                                "starred": metadata.get("starred", False),
                            },
                        }
                    )
            elif kind == "calendar":
                values = self.pages(
                    connection,
                    f"https://www.googleapis.com/calendar/v3/calendars/{quote(collection)}/events?maxResults=250",
                    "items",
                )
                for item in values:
                    if item.get("status") == "cancelled":
                        continue
                    rows.append(
                        {
                            "id": collection + "/" + item["id"],
                            "version": item.get("etag", ""),
                            "data": {
                                "title": item.get("summary") or "Event",
                                "body": item.get("description", ""),
                                "start": item.get("start", {}),
                                "end": item.get("end", {}),
                            },
                        }
                    )
            elif kind == "mail":
                values = self.pages(
                    connection,
                    "https://gmail.googleapis.com/gmail/v1/users/me/messages?"
                    + urllib.parse.urlencode({"labelIds": collection, "maxResults": 100}),
                    "messages",
                )
                for item in values[:200]:
                    full = self.api(
                        connection,
                        f"https://gmail.googleapis.com/gmail/v1/users/me/messages/{quote(item['id'])}?format=metadata",
                    )
                    headers = {
                        v["name"].lower(): v["value"]
                        for v in full.get("payload", {}).get("headers", [])
                    }
                    rows.append(
                        {
                            "id": item["id"],
                            "version": str(full.get("historyId", "")),
                            "data": {
                                "title": headers.get("subject") or "Message",
                                "body": full.get("snippet", ""),
                                "sender": headers.get("from", ""),
                                "starred": "STARRED" in full.get("labelIds", []),
                                "read": "UNREAD" not in full.get("labelIds", []),
                                "labels": full.get("labelIds", []),
                                "flags": [
                                    colour
                                    for colour, label in scope.get("flag_labels", {}).items()
                                    if label and label in full.get("labelIds", [])
                                ],
                            },
                        }
                    )
        return rows

    def push(self, connection, kind, scope, record, mapping):
        data = record["data"]
        remote = mapping["remote"].split(":", 1)[1] if mapping else ""
        target = scope["target"]
        version = mapping["version"] if mapping else ""
        if kind == "tasks":
            collection, task = remote.split("/", 1) if remote else (target, "")
            marker = "uCore record: " + record["id"]
            if not task:
                existing = self.pages(
                    connection,
                    f"https://tasks.googleapis.com/tasks/v1/lists/{quote(collection)}/tasks?showCompleted=true&showHidden=true&maxResults=100",
                    "items",
                )
                prior = next((item for item in existing if marker in item.get("notes", "")), None)
                if prior:
                    task, version = prior["id"], prior.get("etag", "")
            payload = {
                "title": data["title"],
                "notes": self.strip_marker(data.get("body", "")) + "\n\n" + marker,
                "status": "completed" if data.get("status") == "completed" else "needsAction",
                "due": data.get("due") or None,
            }
            url = f"https://tasks.googleapis.com/tasks/v1/lists/{quote(collection)}/tasks" + (
                "/" + quote(task) if task else ""
            )
            result = self.api(
                connection, url, method="PATCH" if task else "POST", data=payload, version=version
            )
            return {"id": collection + "/" + result["id"], "version": result.get("etag", "")}
        if kind == "contacts":
            payload = {
                "names": [{"givenName": data["title"]}],
                "emailAddresses": [{"value": v} for v in data.get("emails", [])],
                "phoneNumbers": [{"value": v} for v in data.get("phones", [])],
                "biographies": [{"value": data.get("body", ""), "contentType": "TEXT_PLAIN"}],
            }
            fields = "names,emailAddresses,phoneNumbers,biographies"
            if remote:
                if mapping and json.loads(mapping["base"]).get("title") == data["title"]:
                    payload.pop("names", None)
                    fields = "emailAddresses,phoneNumbers,biographies"
                current = self.api(
                    connection,
                    f"https://people.googleapis.com/v1/{remote}?personFields=metadata,emailAddresses,phoneNumbers",
                )
                payload["metadata"] = current.get("metadata", {})
                for field, values in [
                    ("emailAddresses", data.get("emails", [])),
                    ("phoneNumbers", data.get("phones", [])),
                ]:
                    types = {v.get("value"): v.get("type") for v in current.get(field, [])}
                    payload[field] = [
                        {"value": v, **({"type": types[v]} if types.get(v) else {})} for v in values
                    ]
                payload["etag"] = current.get("etag", version)
                if version and current.get("etag") != version:
                    raise RuntimeError("Contact changed remotely; pull again before writing")
            result = self.api(
                connection,
                "https://people.googleapis.com/v1/"
                + (
                    remote + ":updateContact?updatePersonFields=" + fields
                    if remote
                    else "people:createContact"
                ),
                method="PATCH" if remote else "POST",
                data=payload,
            )
            if not remote and target != "people/me":
                self.api(
                    connection,
                    f"https://people.googleapis.com/v1/{target}/members:modify",
                    method="POST",
                    data={"resourceNamesToAdd": [result["resourceName"]]},
                )
            if "starred" in data:
                self.api(
                    connection,
                    "https://people.googleapis.com/v1/contactGroups/starred/members:modify",
                    method="POST",
                    data={
                        ("resourceNamesToAdd" if data["starred"] else "resourceNamesToRemove"): [
                            result["resourceName"]
                        ]
                    },
                )
                result = self.api(
                    connection,
                    f"https://people.googleapis.com/v1/{result['resourceName']}?personFields=metadata",
                )
            return {"id": result["resourceName"], "version": result.get("etag", "")}
        if kind == "notes":
            payload = {
                "name": data["title"],
                "starred": bool(data.get("starred")),
                "appProperties": {"ucore": "note", "record": record["id"]},
            }
            if not remote:
                query = (
                    "trashed=false and appProperties has { key='record' and value='"
                    + record["id"]
                    + "' }"
                )
                existing = self.api(
                    connection,
                    "https://www.googleapis.com/drive/v3/files?"
                    + urllib.parse.urlencode({"q": query, "fields": "files(id,version)"}),
                ).get("files", [])
                if existing:
                    remote = existing[0]["id"]
            if remote:
                current = self.api(
                    connection,
                    f"https://www.googleapis.com/drive/v3/files/{quote(remote)}?fields=version",
                )
                if (
                    version
                    and (
                        current.get("_http_etag")
                        if version.startswith('"')
                        else str(current.get("version"))
                    )
                    != version
                ):
                    raise RuntimeError("Drive note changed remotely; pull again before writing")
            else:
                payload["mimeType"] = "text/markdown"
            result = self.api(
                connection,
                "https://www.googleapis.com/drive/v3/files"
                + ("/" + quote(remote) if remote else "")
                + "?fields=id,version",
                method="PATCH" if remote else "POST",
                data=payload,
                version=current.get("_http_etag", "") if remote else "",
            )
            self.drive_text(
                connection, result["id"], data.get("body", ""), version=result.get("_http_etag", "")
            )
            current = self.api(
                connection,
                f"https://www.googleapis.com/drive/v3/files/{quote(result['id'])}?fields=version",
            )
            return {
                "id": result["id"],
                "version": current.get("_http_etag") or str(current.get("version", "")),
            }
        if kind == "calendar":
            collection, event = remote.split("/", 1) if remote else (target, "")
            if not data.get("start") or not data.get("end"):
                raise ValueError("Calendar events require start and end")
            result = self.api(
                connection,
                f"https://www.googleapis.com/calendar/v3/calendars/{quote(collection)}/events"
                + ("/" + quote(event) if event else ""),
                method="PATCH" if event else "POST",
                version=version,
                data={
                    "summary": data["title"],
                    "description": data.get("body", ""),
                    "start": data["start"],
                    "end": data["end"],
                },
            )
            return {"id": collection + "/" + result["id"], "version": result.get("etag", "")}
        if kind == "mail":
            if not remote:
                raise ValueError(
                    "Mail can sync flags and read state; it cannot copy or send messages"
                )
            add, remove = [], []
            for label, enabled in [
                ("STARRED", data.get("starred")),
                ("UNREAD", not data.get("read", False)),
            ]:
                (add if enabled else remove).append(label)
            colour_labels = scope.get("flag_labels", {})
            for colour, label in colour_labels.items():
                if not label:
                    continue
                (add if colour in data.get("flags", []) else remove).append(label)
            result = self.api(
                connection,
                f"https://gmail.googleapis.com/gmail/v1/users/me/messages/{quote(remote)}/modify",
                method="POST",
                data={"addLabelIds": add, "removeLabelIds": remove},
            )
            return {"id": remote, "version": str(result.get("historyId", ""))}
        raise ValueError("Unsupported collection")


from .apple import AppleAdapter  # noqa: E402,F401


def provider_capabilities(provider: str, *, host_platform: str) -> dict:
    """Describe adapter code support, never credential or authorization readiness."""
    adapter = {"google": GoogleAdapter, "apple": AppleAdapter}.get(provider)
    available = adapter is not None and (provider != "apple" or host_platform == "Darwin")
    return {
        "adapter_available": available,
        "qualified": False,
        "readiness": "requires_connection_and_permissions" if available else "unsupported_platform",
        "collections": {
            kind: {
                "discover": available,
                "read": available,
                "create": available and kind != "mail",
                "update": available,
                "delete": False,
                "writable_fields": sorted(fields) if available else [],
                "limitations": "Existing message flags/read state only; no sending or copying" if kind == "mail" else "Native field round-trip qualification pending",
            }
            for kind, fields in (adapter.writable.items() if adapter else [])
        },
    }
