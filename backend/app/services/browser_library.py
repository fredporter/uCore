"""Local, bounded browser HTML exchange. Browser apps retain account/cloud sync.

Owner: Snackbar coordination and profile CollectionStore. No private browser DBs,
credentials, network fetches, watchers or new state directories are used.
"""

import hashlib
from html import escape
from html.parser import HTMLParser
from urllib.parse import urlsplit, urlunsplit


def clean_url(value):
    try:
        parsed = urlsplit(str(value))
        if (
            parsed.scheme.lower() not in {"http", "https"}
            or not parsed.hostname
            or parsed.username
            or parsed.password
        ):
            return None
        return urlunsplit(
            (
                parsed.scheme.lower(),
                parsed.netloc.lower(),
                parsed.path,
                parsed.query,
                parsed.fragment,
            )
        )
    except ValueError:
        return None


class BookmarkParser(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.stack = []
        self.pending = None
        self.capture = None
        self.text = []
        self.attrs = {}
        self.rows = []

    def handle_starttag(self, tag, attrs):
        values = dict(attrs)
        if tag in {"h3", "a"}:
            self.capture = tag
            self.text = []
            self.attrs = values
        elif tag == "dl":
            self.stack.append(self.pending)
            self.pending = None

    def handle_data(self, value):
        if self.capture and sum(map(len, self.text)) < 2048:
            self.text.append(value)

    def handle_endtag(self, tag):
        if tag == "dl":
            if self.stack:
                self.stack.pop()
        elif tag == self.capture:
            title = "".join(self.text).strip()
            if tag == "h3":
                self.pending = {"title": title, **self.attrs}
            elif tag == "a":
                url = clean_url(self.attrs.get("href", ""))
                if url:
                    folders = [f for f in self.stack if f]
                    reading = any(
                        f.get("id") == "com.apple.ReadingList"
                        or f.get("title", "").lower() == "reading list"
                        for f in folders
                    )
                    favourite = any(
                        f.get("personal_toolbar_folder", "").lower() == "true"
                        or f.get("title", "").lower()
                        in {"favorites", "favourites", "bookmarks bar"}
                        for f in folders
                    )
                    self.rows.append(
                        {
                            "kind": "reading_list" if reading else "bookmarks",
                            "title": title or url,
                            "url": url,
                            "folders": [f["title"] for f in folders],
                            "favourite": favourite,
                        }
                    )
                    if len(self.rows) > 5000:
                        raise ValueError("Choose an export with at most 5000 links")
            self.capture = None
            self.text = []


def import_html(store, profile, html, source="browser", selection="all"):
    if not isinstance(html, str) or len(html.encode()) > 2_000_000:
        raise ValueError("Choose a bookmark HTML export under 2 MB")
    if source not in {"browser", "safari", "chrome", "firefox", "edge"} or selection not in {
        "all",
        "bookmarks",
        "reading_list",
    }:
        raise ValueError("Choose a browser and collection")
    parser = BookmarkParser()
    parser.feed(html)
    parser.close()
    existing = {
        (r["kind"], r["data"].get("url")): r
        for r in store.records(profile)
        if r["kind"] in {"bookmarks", "reading_list"}
    }
    imported = updated = 0
    for row in parser.rows:
        if selection != "all" and row["kind"] != selection:
            continue
        key = (row["kind"], row["url"])
        record = existing.get(key)
        if record:
            data = {**record["data"]}
            if data.get("title") == data.get("import_title"):
                data["title"] = row["title"]
            data.update(
                import_title=row["title"],
                folders=sorted(set(data.get("folders", []) + row["folders"])),
                browsers=sorted(set(data.get("browsers", []) + [source])),
                favourite=bool(data.get("favourite") or row["favourite"]),
            )
            if data != record["data"]:
                record = store.save(profile, row["kind"], data, record["id"], record["revision"])
                updated += 1
        else:
            rid = hashlib.sha256(
                (profile + "\0" + row["kind"] + "\0" + row["url"]).encode()
            ).hexdigest()[:32]
            record = store.save(
                profile,
                row["kind"],
                {
                    k: v
                    for k, v in {
                        **row,
                        "body": "",
                        "import_title": row["title"],
                        "browsers": [source],
                        "read": False,
                        "flags": [],
                    }.items()
                    if k != "kind"
                },
                rid,
            )
            imported += 1
        existing[key] = record
    return {
        "state": "imported",
        "coordinator": "snackbar",
        "imported": imported,
        "updated": updated,
        "matched": len(parser.rows),
        "mode": "manual-file-exchange",
    }


def export_html(records):
    lines = [
        "<!DOCTYPE NETSCAPE-Bookmark-file-1>",
        '<META HTTP-EQUIV="Content-Type" CONTENT="text/html; charset=UTF-8">',
        "<TITLE>uDOS Browser Library</TITLE>",
        "<H1>uDOS Browser Library</H1>",
        "<DL><p>",
    ]
    for kind, label, attrs in [
        ("bookmarks", "Bookmarks", ""),
        ("favourites", "Favorites", ' PERSONAL_TOOLBAR_FOLDER="true"'),
        ("reading_list", "Reading List", ' ID="com.apple.ReadingList"'),
    ]:
        lines.append(f"<DT><H3{attrs}>{label}</H3><DL><p>")
        for record in records:
            data = record["data"]
            url = clean_url(data.get("url", ""))
            matches = (record["kind"] == "bookmarks" and bool(data.get("favourite"))) if kind == "favourites" else (record["kind"] == kind and (kind != "bookmarks" or not data.get("favourite")))
            if matches and url:
                lines.append(f'<DT><A HREF="{escape(url, quote=True)}">{escape(data["title"])}</A>')
        lines.append("</DL><p>")
    lines.append("</DL><p>")
    return "\n".join(lines)
