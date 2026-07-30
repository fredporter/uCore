"""Extension manifest — declares what an extension provides and requires."""

from __future__ import annotations

import enum
from dataclasses import dataclass, field


class ExtensionKind(str, enum.Enum):
    """Broad category for an extension."""
    CORE = "core"              # uCore built-in (never externalised)
    WORKFLOW = "workflow"      # workflow engine, task orchestration
    KNOWLEDGE = "knowledge"    # knowledge bridge, search, indexing
    PLUGIN = "plugin"          # optional udos-* domain capability
    SURFACE = "surface"        # UI surface served by uCore
    TOOL = "tool"              # dev tool integration (docker, git, etc.)


@dataclass
class ExtensionManifest:
    """Lightweight extension declaration.

    Each extension ships a manifest dict in a blessed location.
    The registry reads these and wires them into uCore at startup.
    """

    id: str
    """Unique extension id, e.g. 'uflow', 'uknowledge', 'udos-home'."""

    name: str
    """Human-readable name."""

    kind: ExtensionKind
    """Broad category."""

    version: str = "0.1.0"
    """Semver."""

    description: str = ""
    """Short description."""

    # ── Lifecycle hooks (optional) ──────────────────────────────────

    entrypoint: str | None = None
    """Dotted path to a callable `setup(app)` or None for stub-only."""

    dependencies: list[str] = field(default_factory=list)
    """Other extension ids this one requires."""

    optional: bool = True
    """If True, uCore runs fine without this extension loaded."""

    # ── API surface hints ───────────────────────────────────────────

    api_prefix: str | None = None
    """Optional URL prefix for routes registered by this extension,
    e.g. '/api/workflows', '/api/knowledge'."""

    route_registrar: str | None = None
    """Dotted path to a `register_routes(app)` callable."""

    @classmethod
    def from_dict(cls, data: dict) -> ExtensionManifest:
        """Construct from a raw dict (JSON/YAML manifest)."""
        kind_raw = data.get("kind", "plugin")
        kind = ExtensionKind(kind_raw) if kind_raw in ExtensionKind._value2member_map_ else ExtensionKind.PLUGIN
        return cls(
            id=data["id"],
            name=data["name"],
            kind=kind,
            version=data.get("version", "0.1.0"),
            description=data.get("description", ""),
            entrypoint=data.get("entrypoint"),
            dependencies=data.get("dependencies", []),
            optional=data.get("optional", True),
            api_prefix=data.get("api_prefix"),
            route_registrar=data.get("route_registrar"),
        )