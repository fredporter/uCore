"""uCore Extension Registry — lightweight plugin contract.

Extensions are optional capabilities that can be discovered, loaded, and
unloaded at runtime. The registry is intentionally simple: a manifest format
and a loader that defers to adapters when the real implementation lives in
an external repo (uFlow, uKnowledge, udos-*).

Design principles:
- No heavy plugin framework — just a dict registry + discovery convention.
- Extensions declare a manifest; uCore loads what it finds.
- When a capability moves to a dedicated repo, uCore keeps a thin adapter
  that delegates to the external package and fails fast if missing.
"""

from __future__ import annotations

from .manifest import ExtensionManifest, ExtensionKind
from .registry import ExtensionRegistry, registry

__all__ = [
    "ExtensionManifest",
    "ExtensionKind",
    "ExtensionRegistry",
    "registry",
]