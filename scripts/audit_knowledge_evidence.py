"""Read-only check of a bounded Global Knowledge evidence manifest."""

import argparse
import hashlib
import json
import re
from datetime import date
from decimal import Decimal
from pathlib import Path
from urllib.parse import urlsplit


def unique_keys(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"duplicate JSON key: {key}")
        result[key] = value
    return result


def invalid_constant(value):
    raise ValueError(f"invalid JSON number: {value}")


def parse_json(raw):
    return json.loads(
        raw, parse_float=Decimal, object_pairs_hook=unique_keys, parse_constant=invalid_constant
    )


def require(condition, message):
    if not condition:
        raise ValueError(message)


def json_value(data, keys):
    for key in keys:
        if isinstance(data, dict) and isinstance(key, str):
            data = data[key]
        elif isinstance(data, list) and type(key) is int and key >= 0:
            data = data[key]
        else:
            raise ValueError(f"invalid path component: {key!r}")
    return data


def check_article(root, path, raw, record):
    lines = raw.decode("utf-8").splitlines()
    frontmatter = []
    if lines and lines[0] == "---":
        end = lines.index("---", 1)
        frontmatter = lines[1:end]
        lines = lines[end + 1 :]

    if "uid" in record:
        expected = record["uid"]
        require(isinstance(expected, str) and expected.strip(), "expected a nonempty UID")
        uids = [line[4:].strip() for line in frontmatter if line.startswith("uid:")]
        require(uids == [expected], f"expected one plain frontmatter UID {expected!r}, found {uids!r}")

    links = record.get("links", [])
    require(isinstance(links, list), "expected a list of Markdown links")
    body = "\n".join(lines)
    for link in links:
        require(
            isinstance(link, str) and re.fullmatch(r"(?:[\w.-]+/)*[\w.-]+\.md", link),
            "expected a plain relative Markdown link without a fragment",
        )
        require(
            re.search(r"(?<!!)\[[^\]\n]+\]\(" + re.escape(link) + r"\)", body),
            f"missing inline link: {link}",
        )
        target = (path.parent / link).resolve()
        require(
            target.is_relative_to(root) and target.is_file(),
            f"link target is missing or outside the library: {link}",
        )

    first = next((line for line in lines if line.strip()), "")
    return first.removeprefix("# ") if first.startswith("# ") else None


def check_record(root, record):
    name = record["path"]
    rel = Path(name)
    require(not rel.is_absolute() and ".." not in rel.parts, "expected a library-relative path")
    path = (root / rel).resolve(strict=True)
    require(path.is_relative_to(root) and path.is_file(), "path is outside the library or is not a file")
    raw = path.read_bytes()
    require(hashlib.sha256(raw).hexdigest() == record["sha256"], "file hash changed; review the diff")
    checks = record["checks"]
    require(isinstance(checks, list) and checks, "expected at least one check")

    if rel.suffix == ".json":
        require("uid" not in record and "links" not in record, "UID and links apply only to Markdown")
        content = parse_json(raw)
    elif rel.suffix == ".md":
        content = check_article(root, root / rel, raw, record)
    else:
        raise ValueError("expected Markdown or JSON")

    for check in checks:
        source = check["source"]
        url = urlsplit(source["url"])
        require(url.scheme == "https" and url.hostname, "source needs an HTTPS URL")
        date.fromisoformat(source["accessed"])
        for key in ("locator", "reuse_basis"):
            require(isinstance(source[key], str) and source[key].strip(), f"missing source {key}")

        expected = check["equals"]
        if rel.suffix == ".json":
            keys = check["keys"]
            require(isinstance(keys, list) and keys, "expected a nonempty JSON key path")
            actual = json_value(content, keys)
            location = keys
        else:
            actual = content
            location = "article title"
            require(isinstance(expected, str) and expected.strip(), "expected a nonempty article title")

        # Reject booleans as numbers; compare numeric values without float rounding.
        same_type = type(actual) is type(expected)
        both_numbers = all(type(value) in (int, Decimal) for value in (actual, expected))
        require(
            (same_type or both_numbers)
            and not isinstance(expected, (list, dict))
            and actual == expected,
            f"{location}: expected {expected!r}, found {actual!r}",
        )
    return len(checks)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--manifest", type=Path, required=True)
    args = parser.parse_args()
    report = {"files": [], "errors": []}
    try:
        root = args.root.resolve(strict=True)
        require(root.is_dir(), "library root must be a directory")
        manifest = parse_json(args.manifest.read_bytes())
        require(type(manifest["version"]) is int and manifest["version"] == 1, "expected manifest version 1")
        records = manifest["files"]
        require(isinstance(records, list) and records, "expected at least one file")
        seen = set()
        for record in records:
            name = record.get("path") if isinstance(record, dict) else None
            try:
                require(isinstance(name, str) and name, "missing file path")
                canonical_name = Path(name)
                require(canonical_name not in seen, "duplicate file")
                seen.add(canonical_name)
                count = check_record(root, record)
                report["files"].append({"path": name, "checks_passed": count})
            except (OSError, ValueError, TypeError, KeyError, IndexError, RuntimeError) as error:
                report["errors"].append({"path": name if isinstance(name, str) else None, "message": str(error)})
    except (OSError, ValueError, TypeError, KeyError, RuntimeError) as error:
        report["errors"].append({"message": str(error)})

    report["passed"] = not report["errors"]
    print(json.dumps(report, indent=2))
    return int(not report["passed"])


if __name__ == "__main__":
    raise SystemExit(main())
