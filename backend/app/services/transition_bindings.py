"""Reviewed transition bindings (Gate B milestone 1).

Bindings are trusted configuration, not event data. An event can never name a
workflow, owner or grant; it can only match a binding that already exists.
"""
from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from app.core.settings import settings

IDENTIFIER = re.compile(r"^[A-Za-z0-9._:-]{1,128}$")
FIELD_NAME = re.compile(r"^[A-Za-z0-9_.-]{1,64}$")


class BindingError(ValueError):
    """Raised when the binding configuration is not trustworthy."""


@dataclass(frozen=True)
class Binding:
    binding_id: str
    source_id: str
    subject_id: str
    workflow_id: str
    owner: str = "default"
    pipeline_version: str = "v1"
    enabled: bool = True
    allowed_changes: frozenset[str] = field(default_factory=frozenset)


def default_bindings_path() -> Path:
    return settings.udos_home / "config" / "transition-bindings.json"


def _require(value: Any, name: str, pattern: re.Pattern[str]) -> str:
    text = str(value or "")
    if not pattern.match(text):
        raise BindingError(f"{name} is invalid: {text!r}")
    return text


def load_bindings(path: Path | None = None) -> list[Binding]:
    """Load bindings; a missing file is a valid default-deny state."""
    target = path or default_bindings_path()
    if not target.exists():
        return []
    try:
        payload = json.loads(target.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        raise BindingError(f"bindings unreadable: {exc}") from exc

    entries = payload.get("bindings") if isinstance(payload, dict) else None
    if not isinstance(entries, list):
        raise BindingError("bindings file must contain a 'bindings' list")

    bindings: list[Binding] = []
    for entry in entries:
        if not isinstance(entry, dict):
            raise BindingError("each binding must be an object")
        allowed = entry.get("allowed_changes", [])
        if not isinstance(allowed, list) or not all(
            isinstance(name, str) and FIELD_NAME.match(name) for name in allowed
        ):
            raise BindingError("allowed_changes must be a list of field names")
        bindings.append(
            Binding(
                binding_id=_require(entry.get("binding_id"), "binding_id", IDENTIFIER),
                source_id=_require(entry.get("source_id"), "source_id", IDENTIFIER),
                subject_id=_require(entry.get("subject_id"), "subject_id", IDENTIFIER),
                workflow_id=_require(entry.get("workflow_id"), "workflow_id", IDENTIFIER),
                owner=_require(entry.get("owner", "default"), "owner", IDENTIFIER),
                pipeline_version=str(entry.get("pipeline_version", "v1")),
                enabled=bool(entry.get("enabled", True)),
                allowed_changes=frozenset(allowed),
            )
        )
    return bindings


def match_binding(
    bindings: list[Binding],
    *,
    source_id: str,
    subject_id: str,
    pipeline_version: str,
    fields: set[str],
) -> tuple[Binding | None, str]:
    """Return the single matching enabled binding, or a suppression reason."""
    candidates = [
        binding
        for binding in bindings
        if binding.source_id == source_id
        and binding.subject_id == subject_id
        and binding.pipeline_version == pipeline_version
    ]
    if not candidates:
        return None, "unmatched"
    enabled = [binding for binding in candidates if binding.enabled]
    if not enabled:
        return None, "disabled"
    if len(enabled) > 1:
        return None, "ambiguous"
    binding = enabled[0]
    outside = sorted(fields - set(binding.allowed_changes))
    if outside:
        return None, f"predicate:{','.join(outside)}"
    return binding, "matched"
