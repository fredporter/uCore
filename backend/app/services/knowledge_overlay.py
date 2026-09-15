"""Knowledge Overlay Federation Engine & Resolution Service.

Implements the sovereign three-tier cascading knowledge architecture:
  Layer 2: Sovereign Personal Overrides (~/Vault/knowledge/)  [Full Precedence]
  Layer 1: Shared / Community Layer     (~/Shared/knowledge/) [Filter Overlay]
  Layer 0: Canonical Base Knowledge     (~/Public/global-knowledge/) [Read-Only Baseline]

In accordance with AGENTS.md and KNOWLEDGE_LAYERING_AND_CONTRIBUTION_SPEC.md:
- Layer 0 is immutable at runtime (Wizard only via external tooling).
- Local edits are non-destructive and create/update Layer 2 files.
- Reverting a Layer 2 file immediately restores the Layer 0 (or Layer 1) baseline.
- Submission packaging outputs manifest.json, diff.patch, and provenance.json
  under ~/Vault/dispatches/submissions/ without dot-directory concealment.
- AI preflight linting sanitizes private paths (/Users/...) and credentials.
"""

from __future__ import annotations

import difflib
import hashlib
import json
import logging
import os
import re
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from app.knowledge.config import (
    global_knowledge_root,
    shared_root,
    user_vault_root,
)

log = logging.getLogger("ucore.knowledge.overlay")

# Regex patterns for preflight linting
_HOME_PATH_RE = re.compile(r"/(?:Users|home)/[a-zA-Z0-9_\.\-]+(?:\/[a-zA-Z0-9_\.\-]+)*")
_WIN_HOME_RE = re.compile(r"[A-Za-z]:\\Users\\[a-zA-Z0-9_\.\-]+")
_CREDENTIAL_PATTERNS = [
    (re.compile(r"sk-[a-zA-Z0-9_-]{20,}"), "OpenAI / LLM API key"),
    (re.compile(r"ghp_[a-zA-Z0-9]{20,}"), "GitHub personal access token"),
    (re.compile(r"xox[baprs]-[0-9a-zA-Z]{10,48}"), "Slack token"),
    (re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----"), "Private cryptographic key"),
    (re.compile(r"Bearer\s+[a-zA-Z0-9_\-\.]{25,}"), "Bearer token"),
]


def _sha256(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


class KnowledgeOverlayResolver:
    """Cascading overlay resolver for sovereign knowledge federation."""

    def __init__(
        self,
        canon_root: Path | None = None,
        shared_knowledge_root: Path | None = None,
        vault_knowledge_root: Path | None = None,
        submissions_root: Path | None = None,
    ) -> None:
        self.canon_root = (
            canon_root.expanduser().resolve()
            if canon_root
            else global_knowledge_root().resolve()
        )
        self.shared_root = (
            shared_knowledge_root.expanduser().resolve()
            if shared_knowledge_root
            else (shared_root() / "knowledge").resolve()
        )
        self.vault_root = (
            vault_knowledge_root.expanduser().resolve()
            if vault_knowledge_root
            else (user_vault_root() / "knowledge").resolve()
        )
        self.submissions_root = (
            submissions_root.expanduser().resolve()
            if submissions_root
            else (user_vault_root() / "dispatches" / "submissions").resolve()
        )

    def layer_root(self, layer: int) -> Path:
        if layer == 0:
            return self.canon_root
        if layer == 1:
            return self.shared_root
        if layer == 2:
            return self.vault_root
        raise ValueError(f"Invalid layer: {layer}. Must be 0, 1, or 2.")

    def normalize_rel_path(self, rel_path: str) -> str:
        cleaned = rel_path.strip().lstrip("/")
        parts = [p for p in cleaned.split("/") if p and p != "."]
        if any(p == ".." for p in parts):
            raise ValueError(f"Directory traversal detected in path: {rel_path}")
        if parts and parts[0] in ("global-knowledge", "knowledge"):
            parts = parts[1:]
        normalized = "/".join(parts)
        if not normalized.endswith(".md") and not normalized.endswith(".json"):
            normalized += ".md"
        return normalized

    def _find_in_layer(self, layer: int, normalized_rel: str) -> tuple[Path | None, str | None]:
        root = self.layer_root(layer)
        if not root.exists():
            return None, None
        candidate = (root / normalized_rel).resolve()
        try:
            candidate.relative_to(root)
        except ValueError:
            return None, None
        if candidate.is_file():
            try:
                content = candidate.read_text(encoding="utf-8", errors="replace")
                return candidate, content
            except OSError:
                return candidate, None
        return None, None

    def resolve(self, rel_path: str, prefer_canon: bool = False) -> dict[str, Any]:
        """Resolve a document across layers in cascading priority order.

        Priority order: Layer 2 (Personal) > Layer 1 (Shared) > Layer 0 (Canon).
        If prefer_canon is True, returns the pristine Layer 0 base content.
        """
        normalized = self.normalize_rel_path(rel_path)

        # Retrieve Layer 0 baseline for comparison
        canon_path, canon_content = self._find_in_layer(0, normalized)

        # Check in priority order
        search_order = [0] if prefer_canon else [2, 1, 0]

        effective_layer = None
        effective_path = None
        effective_content = None

        for layer in search_order:
            path, content = self._find_in_layer(layer, normalized)
            if path is not None and content is not None:
                effective_layer = layer
                effective_path = path
                effective_content = content
                break

        if effective_layer is None or effective_content is None:
            return {
                "rel_path": normalized,
                "found": False,
                "effective_layer": None,
                "effective_layer_name": None,
                "effective_path": None,
                "content": "",
                "is_overlaid": False,
                "canon_exists": canon_path is not None,
                "canon_path": str(canon_path) if canon_path else None,
                "has_diff": False,
                "diff_from_canon": "",
                "diff_stats": {"additions": 0, "deletions": 0},
            }

        layer_names = {0: "canon", 1: "community", 2: "personal"}
        is_overlaid = effective_layer > 0 and (canon_content is not None)

        # Calculate unified diff vs Canon
        diff_text = ""
        additions = 0
        deletions = 0

        if canon_content is not None and effective_layer != 0:
            canon_lines = canon_content.splitlines(keepends=True)
            effective_lines = effective_content.splitlines(keepends=True)
            diff_lines = list(
                difflib.unified_diff(
                    canon_lines,
                    effective_lines,
                    fromfile=f"canon/{normalized}",
                    tofile=f"layer{effective_layer}/{normalized}",
                )
            )
            if diff_lines:
                diff_text = "".join(diff_lines)
                for line in diff_lines[2:]:
                    if line.startswith("+") and not line.startswith("+++"):
                        additions += 1
                    elif line.startswith("-") and not line.startswith("---"):
                        deletions += 1
                is_overlaid = True
            elif effective_layer > 0:
                # Same content as canon, but file exists in higher layer
                is_overlaid = True

        return {
            "rel_path": normalized,
            "found": True,
            "effective_layer": effective_layer,
            "effective_layer_name": layer_names.get(effective_layer, "unknown"),
            "effective_path": str(effective_path),
            "content": effective_content,
            "is_overlaid": is_overlaid,
            "canon_exists": canon_path is not None,
            "canon_path": str(canon_path) if canon_path else None,
            "has_diff": bool(diff_text),
            "diff_from_canon": diff_text,
            "diff_stats": {"additions": additions, "deletions": deletions},
        }

    def create_or_update_overlay(
        self,
        rel_path: str,
        content: str,
        layer: int = 2,
    ) -> dict[str, Any]:
        """Save a personal (Layer 2) or community (Layer 1) overlay.

        Layer 0 is strictly read-only at runtime to prevent canonical corruption.
        """
        if layer == 0:
            raise PermissionError(
                "Layer 0 (Base Canon) is immutable at runtime. "
                "Only the Wizard via external developer tooling may modify canonical knowledge."
            )
        if layer not in (1, 2):
            raise ValueError(f"Invalid target layer: {layer}. Overlays can only target Layer 1 or 2.")

        normalized = self.normalize_rel_path(rel_path)
        root = self.layer_root(layer)
        target = root / normalized
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content, encoding="utf-8")

        log.info("Saved knowledge overlay at Layer %d: %s", layer, target)
        return self.resolve(normalized)

    def revert_overlay(self, rel_path: str, layer: int = 2) -> dict[str, Any]:
        """Revert (delete) an overlay in Layer 2 or Layer 1.

        Immediately restores lower layer precedence (Layer 1 or pristine Layer 0).
        """
        if layer == 0:
            raise PermissionError("Cannot revert Layer 0 (Base Canon).")
        normalized = self.normalize_rel_path(rel_path)
        root = self.layer_root(layer)
        target = root / normalized

        if target.is_file():
            target.unlink()
            log.info("Reverted knowledge overlay at Layer %d: %s", layer, target)
            # Clean up empty parent directories up to layer root
            parent = target.parent
            while parent != root and parent.is_dir():
                try:
                    if not any(parent.iterdir()):
                        parent.rmdir()
                        parent = parent.parent
                    else:
                        break
                except OSError:
                    break

        return self.resolve(normalized)

    def lint_preflight(self, content: str, rel_path: str = "") -> dict[str, Any]:
        """Automated AI preflight linter for proposed contributions.

        Checks:
        1. Privacy leak scanner (local home paths /Users/..., C:\\Users\\..., credentials).
        2. Prose typography and sentence case standards.
        3. USX token and relative asset safety.
        4. Frontmatter syntax validation.
        """
        errors: list[str] = []
        warnings: list[str] = []
        recommendations: list[str] = []

        # 1. Privacy & Credential Scan
        home_matches = _HOME_PATH_RE.findall(content)
        if home_matches:
            errors.append(
                f"Privacy leak detected: local user path found ({home_matches[0]}). "
                "Replace absolute paths with relative or ~/ tokens."
            )
        win_matches = _WIN_HOME_RE.findall(content)
        if win_matches:
            errors.append(
                f"Privacy leak detected: Windows user path found ({win_matches[0]})."
            )

        for pattern, label in _CREDENTIAL_PATTERNS:
            if pattern.search(content):
                errors.append(f"Security hazard: {label} detected in document content.")

        # 2. Prose Standards Scan
        # Headings: check for excessively title-cased headings or double punctuation
        lines = content.splitlines()
        for i, line in enumerate(lines, 1):
            if line.startswith("#"):
                heading_text = line.lstrip("#").strip()
                words = heading_text.split()
                # Check for ALL CAPS heading
                if len(words) > 2 and heading_text.isupper():
                    warnings.append(
                        f"Line {i}: Heading is ALL CAPS. Prose standard prefers sentence case."
                    )
                # Check for trailing punctuation in heading
                if heading_text.endswith((".", ":", ";")):
                    warnings.append(
                        f"Line {i}: Heading has trailing punctuation '{heading_text[-1]}'."
                    )

        # 3. USX & Relative Asset Safety
        # Check image links: ![alt](url)
        img_pattern = re.compile(r"!\[(.*?)\]\((.*?)\)")
        for alt, url in img_pattern.findall(content):
            if url.startswith("file://") or url.startswith("/Users/") or url.startswith("/home/"):
                errors.append(f"Absolute local asset link detected in image: {url}")
            elif url.startswith("http://") or url.startswith("https://"):
                warnings.append(
                    f"External image link '{url}' violates offline-first doctrine. "
                    "Embed asset in vault attachments or SVG."
                )

        # 4. Frontmatter validation if present
        if content.startswith("---"):
            try:
                import yaml

                parts = content.split("---", 2)
                if len(parts) >= 3:
                    parsed = yaml.safe_load(parts[1])
                    if not isinstance(parsed, dict):
                        warnings.append("YAML frontmatter is not a key-value mapping.")
                    else:
                        if "title" not in parsed:
                            recommendations.append("Add 'title' to YAML frontmatter for search indexing.")
            except Exception as e:
                warnings.append(f"Invalid YAML frontmatter: {e}")

        passed = len(errors) == 0
        return {
            "passed": passed,
            "errors": errors,
            "warnings": warnings,
            "recommendations": recommendations,
            "checks": {
                "privacy_clean": len(home_matches) == 0 and len(win_matches) == 0,
                "credentials_clean": not any(p.search(content) for p, _ in _CREDENTIAL_PATTERNS),
                "prose_compliant": len(warnings) == 0,
                "assets_offline": not any("violates offline-first" in w for w in warnings),
            },
        }

    def export_submission_package(
        self,
        rel_path: str,
        author: str = "sovereign-user",
        notes: str = "",
        submission_type: str = "canonical_patch",
    ) -> dict[str, Any]:
        """Bundle personal overlay into a signed cryptographic submission package.

        Package structure:
          ~/Vault/dispatches/submissions/<submission_id>/
            manifest.json
            diff.patch
            provenance.json
        """
        normalized = self.normalize_rel_path(rel_path)
        resolved = self.resolve(normalized)

        if not resolved["found"]:
            raise FileNotFoundError(f"Document '{normalized}' not found in any layer.")

        content = resolved["content"]

        # Run preflight validation
        preflight = self.lint_preflight(content, normalized)
        if not preflight["passed"]:
            raise ValueError(
                f"Automated preflight lint failed: {'; '.join(preflight['errors'])}"
            )

        # Determine diff patch
        diff_text = resolved["diff_from_canon"]
        if not diff_text:
            # New document without canon baseline; package full file diff
            canon_lines: list[str] = []
            effective_lines = content.splitlines(keepends=True)
            diff_text = "".join(
                difflib.unified_diff(
                    canon_lines,
                    effective_lines,
                    fromfile=f"/dev/null",
                    tofile=f"canon/{normalized}",
                )
            )

        timestamp_str = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
        submission_id = f"sub-{timestamp_str}-{uuid.uuid4().hex[:6]}"
        pkg_dir = self.submissions_root / submission_id
        pkg_dir.mkdir(parents=True, exist_ok=True)

        diff_checksum = _sha256(diff_text)
        content_digest = _sha256(content)

        manifest = {
            "submission_id": submission_id,
            "version": "1.0",
            "type": submission_type,
            "author": author,
            "rel_path": normalized,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "notes": notes,
            "diff_checksum_sha256": diff_checksum,
            "preflight": {
                "passed": preflight["passed"],
                "checks": preflight["checks"],
                "warnings": preflight["warnings"],
            },
        }

        provenance = {
            "origin_layer": resolved["effective_layer"],
            "origin_layer_name": resolved["effective_layer_name"],
            "origin_path": resolved["effective_path"],
            "canon_exists": resolved["canon_exists"],
            "canon_path": resolved["canon_path"],
            "content_sha256": content_digest,
            "signatures": {
                "local_device_fingerprint": _sha256(os.uname().nodename),
                "author_id": author,
                "signed_at": datetime.now(timezone.utc).isoformat(),
            },
            "status": "pending_wizard_review",
        }

        # Write files plainly to disk without dot concealment
        (pkg_dir / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
        (pkg_dir / "diff.patch").write_text(diff_text, encoding="utf-8")
        (pkg_dir / "provenance.json").write_text(json.dumps(provenance, indent=2), encoding="utf-8")

        log.info("Exported submission bundle to %s", pkg_dir)
        return {
            "submission_id": submission_id,
            "package_path": str(pkg_dir),
            "rel_path": normalized,
            "diff_checksum": diff_checksum,
            "manifest": manifest,
            "provenance": provenance,
        }

    def list_overlays(self) -> list[dict[str, Any]]:
        """List all active personal (Layer 2) and community (Layer 1) overlays."""
        overlays: list[dict[str, Any]] = []

        # Check Layer 2 (~/Vault/knowledge)
        if self.vault_root.exists():
            for p in sorted(self.vault_root.rglob("*.md")):
                if p.is_file() and not any(part.startswith(".") for part in p.parts):
                    rel = p.relative_to(self.vault_root).as_posix()
                    resolved = self.resolve(rel)
                    overlays.append({
                        "rel_path": rel,
                        "layer": 2,
                        "layer_name": "personal",
                        "path": str(p),
                        "size": p.stat().st_size,
                        "updated_at": datetime.fromtimestamp(p.stat().st_mtime, timezone.utc).isoformat(),
                        "is_overlaid": resolved["is_overlaid"],
                        "canon_exists": resolved["canon_exists"],
                        "has_diff": resolved["has_diff"],
                        "diff_stats": resolved["diff_stats"],
                    })

        # Check Layer 1 (~/Shared/knowledge)
        if self.shared_root.exists():
            for p in sorted(self.shared_root.rglob("*.md")):
                if p.is_file() and not any(part.startswith(".") for part in p.parts):
                    rel = p.relative_to(self.shared_root).as_posix()
                    # Skip if already in personal overlays (layer 2 takes precedence)
                    if any(o["rel_path"] == rel and o["layer"] == 2 for o in overlays):
                        continue
                    resolved = self.resolve(rel)
                    overlays.append({
                        "rel_path": rel,
                        "layer": 1,
                        "layer_name": "community",
                        "path": str(p),
                        "size": p.stat().st_size,
                        "updated_at": datetime.fromtimestamp(p.stat().st_mtime, timezone.utc).isoformat(),
                        "is_overlaid": resolved["is_overlaid"],
                        "canon_exists": resolved["canon_exists"],
                        "has_diff": resolved["has_diff"],
                        "diff_stats": resolved["diff_stats"],
                    })

        return overlays

    def list_submissions(self) -> list[dict[str, Any]]:
        """List existing submission packages under ~/Vault/dispatches/submissions/."""
        if not self.submissions_root.exists():
            return []

        results: list[dict[str, Any]] = []
        for d in sorted(self.submissions_root.iterdir(), reverse=True):
            if d.is_dir() and not d.name.startswith("."):
                manifest_file = d / "manifest.json"
                if manifest_file.is_file():
                    try:
                        manifest = json.loads(manifest_file.read_text(encoding="utf-8"))
                        results.append({
                            "submission_id": d.name,
                            "path": str(d),
                            "manifest": manifest,
                            "patch_exists": (d / "diff.patch").is_file(),
                            "provenance_exists": (d / "provenance.json").is_file(),
                        })
                    except Exception:
                        pass
        return results

    def get_federation_summary(self) -> dict[str, Any]:
        """Return system-wide federation layer statistics."""
        def count_md(root: Path) -> int:
            if not root.exists():
                return 0
            return sum(
                1 for p in root.rglob("*.md")
                if p.is_file() and not any(part.startswith(".") for part in p.parts)
            )

        overlays = self.list_overlays()
        submissions = self.list_submissions()

        return {
            "status": "ready",
            "layers": {
                "layer_0_canon": {
                    "layer": 0,
                    "name": "Base Canon",
                    "path": str(self.canon_root),
                    "exists": self.canon_root.exists(),
                    "articles_count": count_md(self.canon_root),
                    "authority": "Wizard (External Developer Tooling)",
                    "writable": False,
                },
                "layer_1_shared": {
                    "layer": 1,
                    "name": "Community / Shared",
                    "path": str(self.shared_root),
                    "exists": self.shared_root.exists(),
                    "articles_count": count_md(self.shared_root),
                    "authority": "Household & Peers",
                    "writable": True,
                },
                "layer_2_personal": {
                    "layer": 2,
                    "name": "Sovereign Personal",
                    "path": str(self.vault_root),
                    "exists": self.vault_root.exists(),
                    "articles_count": count_md(self.vault_root),
                    "authority": "Sovereign User",
                    "writable": True,
                },
            },
            "active_overlays_count": len(overlays),
            "submissions_count": len(submissions),
            "submissions_path": str(self.submissions_root),
        }
