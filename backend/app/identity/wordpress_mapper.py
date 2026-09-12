"""Pure mapping adapters between uDos identity records and WordPress payloads."""

from __future__ import annotations

from typing import Any

WORDPRESS_USER_FIELDS = {"email", "display_name", "first_name", "last_name", "url"}
UDOS_META_PREFIX = "udos_"


def _clean_strings(values: list[Any]) -> list[str]:
    return sorted({str(value).strip() for value in values if str(value).strip()})


def map_to_wordpress(
    *,
    profile: dict[str, Any],
    variables: dict[str, Any],
    groups: list[Any],
) -> dict[str, Any]:
    """Map uDos profile data to an allowlisted WordPress user payload."""
    user = {
        field: profile[field]
        for field in WORDPRESS_USER_FIELDS
        if field in profile and profile[field] not in (None, "")
    }

    meta: dict[str, Any] = {}
    for key, value in variables.items():
        normalized = str(key).strip().lower().replace("-", "_").replace(" ", "_")
        if normalized and value is not None:
            meta[f"{UDOS_META_PREFIX}{normalized}"] = value

    for field in ("user_id", "codeword", "install_id"):
        value = profile.get(field)
        if value not in (None, ""):
            meta[f"{UDOS_META_PREFIX}{field}"] = value

    return {
        "user": user,
        "meta": meta,
        "taxonomies": {"udos_group": _clean_strings(groups)},
    }


def map_from_wordpress(payload: dict[str, Any]) -> dict[str, Any]:
    """Map an allowlisted WordPress payload back to uDos profile data."""
    raw_user = payload.get("user", {})
    raw_meta = payload.get("meta", {})
    raw_taxonomies = payload.get("taxonomies", {})

    user = raw_user if isinstance(raw_user, dict) else {}
    meta = raw_meta if isinstance(raw_meta, dict) else {}
    taxonomies = raw_taxonomies if isinstance(raw_taxonomies, dict) else {}

    profile = {
        field: user[field]
        for field in WORDPRESS_USER_FIELDS
        if field in user and user[field] not in (None, "")
    }
    for field in ("user_id", "codeword", "install_id"):
        key = f"{UDOS_META_PREFIX}{field}"
        if key in meta and meta[key] not in (None, ""):
            profile[field] = meta[key]

    protected = {
        f"{UDOS_META_PREFIX}user_id",
        f"{UDOS_META_PREFIX}codeword",
        f"{UDOS_META_PREFIX}install_id",
    }
    variables = {
        key.removeprefix(UDOS_META_PREFIX): value
        for key, value in meta.items()
        if isinstance(key, str)
        and key.startswith(UDOS_META_PREFIX)
        and key not in protected
    }
    raw_groups = taxonomies.get("udos_group", [])
    groups = _clean_strings(raw_groups if isinstance(raw_groups, list) else [])

    return {"profile": profile, "variables": variables, "groups": groups}
