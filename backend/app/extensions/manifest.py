"""Extension manifest — declares what an extension provides and requires."""

from __future__ import annotations

import enum
from dataclasses import dataclass, field


ALLOWED_MANIFEST_FIELDS = {
    "id",
    "name",
    "kind",
    "version",
    "description",
    "entrypoint",
    "dependencies",
    "optional",
    "api_prefix",
    "route_registrar",
}
REQUIRED_MANIFEST_FIELDS = {"id", "name", "kind"}


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

    @staticmethod
    def _is_dotted_path(value: str) -> bool:
        parts = value.split(".")
        return len(parts) >= 2 and all(parts)

    @classmethod
    def validate_dict(cls, data: dict) -> None:
        """Validate manifest payload shape and field semantics."""
        if not isinstance(data, dict):
            raise ValueError("Manifest payload must be a dict")

        unknown = set(data) - ALLOWED_MANIFEST_FIELDS
        if unknown:
            raise ValueError(
                f"Unknown manifest fields: {sorted(unknown)}",
            )

        missing = REQUIRED_MANIFEST_FIELDS - set(data)
        if missing:
            raise ValueError(
                f"Missing required manifest fields: {sorted(missing)}",
            )

        if not isinstance(data.get("id"), str) or not data["id"].strip():
            raise ValueError("Field 'id' must be a non-empty string")

        if not isinstance(data.get("name"), str) or not data["name"].strip():
            raise ValueError("Field 'name' must be a non-empty string")

        kind = data.get("kind")
        if isinstance(kind, ExtensionKind):
            pass
        elif isinstance(kind, str) and kind in ExtensionKind._value2member_map_:
            pass
        else:
            allowed = sorted(ExtensionKind._value2member_map_.keys())
            raise ValueError(
                f"Field 'kind' must be one of {allowed}",
            )

        version = data.get("version")
        if version is not None and not isinstance(version, str):
            raise ValueError("Field 'version' must be a string")

        description = data.get("description")
        if description is not None and not isinstance(description, str):
            raise ValueError("Field 'description' must be a string")

        entrypoint = data.get("entrypoint")
        if entrypoint is not None:
            if not isinstance(entrypoint, str) or not cls._is_dotted_path(entrypoint):
                raise ValueError(
                    "Field 'entrypoint' must be a dotted path like 'pkg.mod.setup'",
                )

        dependencies = data.get("dependencies", [])
        if not isinstance(dependencies, list) or not all(
            isinstance(dep, str) and dep.strip() for dep in dependencies
        ):
            raise ValueError(
                "Field 'dependencies' must be a list of non-empty strings",
            )

        optional = data.get("optional")
        if optional is not None and not isinstance(optional, bool):
            raise ValueError("Field 'optional' must be a bool")

        api_prefix = data.get("api_prefix")
        if api_prefix is not None:
            if not isinstance(api_prefix, str) or not api_prefix.startswith("/"):
                raise ValueError("Field 'api_prefix' must be an absolute path")

        route_registrar = data.get("route_registrar")
        if route_registrar is not None:
            if (
                not isinstance(route_registrar, str)
                or not cls._is_dotted_path(route_registrar)
            ):
                raise ValueError(
                    "Field 'route_registrar' must be a dotted path like 'pkg.mod.register_routes'",
                )

        if data["id"] in set(dependencies):
            raise ValueError("Manifest cannot depend on itself")

    @classmethod
    def from_dict(cls, data: dict) -> ExtensionManifest:
        """Construct from a raw dict (JSON/YAML manifest)."""
        cls.validate_dict(data)
        kind_raw = data["kind"]
        kind = kind_raw if isinstance(kind_raw, ExtensionKind) else ExtensionKind(kind_raw)
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