"""Three-way reconciliation and reviewable duplicate suggestions, without data loss."""

from __future__ import annotations

import copy
import re

COLOURS = ("red", "orange", "yellow", "green", "blue", "purple", "grey")


def merge_fields(base, local, remote):
    """Merge independently edited fields; concurrent edits to a field need review."""
    merged = copy.deepcopy(local)
    conflicts = []
    for key in remote:
        before, ours, theirs = base.get(key), local.get(key), remote.get(key)
        if ours == before:
            if key in remote:
                merged[key] = theirs
            else:
                merged.pop(key, None)
        elif theirs != before and ours != theirs:
            conflicts.append(key)
    return merged, sorted(conflicts)


def selected(data, scope, remote_id):
    if scope.get("selection") == "records" and remote_id not in scope.get("records", []):
        return False
    mode = scope.get("filter", "all")
    return (
        mode == "all"
        or (mode == "flagged" and bool(data.get("flags")))
        or (mode == "starred" and data.get("starred") is True)
        or (mode == "vip" and data.get("vip") is True)
    )


def duplicate_candidates(records):
    """Index candidate identities rather than comparing every pair of records."""
    buckets = {}
    found = {}
    for record in records:
        data = record["data"]
        if data.get("merged_into"):
            continue
        keys = [
            ("email", str(v).strip().casefold()) for v in data.get("emails", []) if str(v).strip()
        ]
        keys += [
            ("phone", re.sub(r"\D", "", str(v)))
            for v in data.get("phones", [])
            if len(re.sub(r"\D", "", str(v))) >= 7
        ]
        keys.append(("similar title — review content", data.get("title", "").strip().casefold()))
        for reason, value in keys:
            if not value:
                continue
            key = (record["kind"], reason, value)
            for other in buckets.get(key, [])[:20]:
                pair = tuple(sorted((other, record["id"])))
                if pair not in found or reason in {"email", "phone"}:
                    found[pair] = {"left": other, "right": record["id"], "reason": reason}
            buckets.setdefault(key, []).append(record["id"])
        if len(found) >= 200:
            break
    return list(found.values())[:200]


def combine_records(left, right):
    """Keep left scalar choices; preserve alternative content and all list values."""
    result = copy.deepcopy(left)
    alternatives = dict(result.get("alternatives", {}))
    for key, value in right.items():
        if not result.get(key):
            result[key] = value
        elif isinstance(value, list) and isinstance(result[key], list):
            result[key] = list(dict.fromkeys(result[key] + value))
        elif result[key] != value and key not in {"merged_into", "alternatives"}:
            alternatives.setdefault(key, [])
            if value not in alternatives[key]:
                alternatives[key].append(value)
    if alternatives:
        result["alternatives"] = alternatives
    return result
