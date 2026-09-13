"""Intake Service — Cryptographic original preservation and markdown normalisation.

Complies with UDOS_PRODUCT_REFACTOR_PLAN_2026-09-12 Section 7:
Receive -> preserve/checksum original -> extract -> normalise -> review.
Originals are preserved untouched in ~/Vault/Originals/<doc_id>/ and never directly published.
"""

from __future__ import annotations

import hashlib
import json
import logging
import re
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Optional

from app.services.markdown_import_pipeline import convert_content_to_markdown

log = logging.getLogger("ucore.intake_service")

VAULT_ROOT = Path.home() / "Vault"
ORIGINALS_ROOT = VAULT_ROOT / "Originals"
DOCUMENTS_ROOT = VAULT_ROOT / "Documents"


def _safe_filename(name: str) -> str:
    cleaned = re.sub(r"[^\w\.\-\s]", "_", name).strip()
    return cleaned or "document.bin"


def get_originals_dir() -> Path:
    ORIGINALS_ROOT.mkdir(parents=True, exist_ok=True)
    return ORIGINALS_ROOT


def get_documents_dir() -> Path:
    DOCUMENTS_ROOT.mkdir(parents=True, exist_ok=True)
    return DOCUMENTS_ROOT


def intake_file(
    file_name: str,
    content_bytes: bytes,
    source_uri: str = "",
    author: str = "",
    doc_id: Optional[str] = None,
) -> dict[str, Any]:
    """Preserve an incoming original document and generate a normalized Markdown representation."""
    source_hash = hashlib.sha256(content_bytes).hexdigest()
    safe_name = _safe_filename(file_name)

    if not doc_id:
        doc_id = f"doc_{source_hash[:12]}"

    orig_dir = get_originals_dir() / doc_id
    orig_dir.mkdir(parents=True, exist_ok=True)
    orig_file = orig_dir / safe_name
    orig_file.write_bytes(content_bytes)

    # Decode text for conversion
    try:
        raw_text = content_bytes.decode("utf-8")
    except UnicodeDecodeError:
        raw_text = content_bytes.decode("latin-1", errors="replace")

    suffix = Path(safe_name).suffix.lstrip(".").lower()
    conversion = convert_content_to_markdown(raw_text, source_format=suffix or "auto")

    # Frontmatter added to normalized document for provenance
    frontmatter = (
        f"---\n"
        f"doc_id: \"{doc_id}\"\n"
        f"source_file: \"{safe_name}\"\n"
        f"source_sha256: \"{source_hash}\"\n"
        f"acquired_at: \"{datetime.now(UTC).isoformat()}\"\n"
        f"converter: \"{conversion.plugin_id}\"\n"
        f"privacy: \"private\"\n"
        f"---\n\n"
    )
    normalized_md = frontmatter + conversion.markdown
    output_hash = hashlib.sha256(normalized_md.encode("utf-8")).hexdigest()

    doc_dir = get_documents_dir()
    md_file = doc_dir / f"{doc_id}.md"
    md_file.write_text(normalized_md, encoding="utf-8")

    receipt = {
        "doc_id": doc_id,
        "file_name": safe_name,
        "source_uri": source_uri or f"file://{orig_file}",
        "author": author or "Unknown",
        "acquired_at": datetime.now(UTC).isoformat(),
        "source_sha256": source_hash,
        "output_sha256": output_hash,
        "original_path": str(orig_file),
        "markdown_path": str(md_file),
        "converter_plugin_id": conversion.plugin_id,
        "source_format": conversion.source_format,
        "privacy": "private",
        "size_bytes": len(content_bytes),
    }

    receipt_file = orig_dir / "intake_receipt.json"
    receipt_file.write_text(json.dumps(receipt, indent=2), encoding="utf-8")
    log.info("Ingested document %s (%s, sha256: %s)", doc_id, safe_name, source_hash[:8])
    return receipt


def get_intake_receipt(doc_id: str) -> Optional[dict[str, Any]]:
    receipt_path = ORIGINALS_ROOT / doc_id / "intake_receipt.json"
    if receipt_path.is_file():
        try:
            return json.loads(receipt_path.read_text(encoding="utf-8"))
        except Exception:
            pass
    return None


def intake_binder_source(
    binder_dir: Path,
    file_name: str,
    content_bytes: bytes,
    source_uri: str = "",
    author: str = "",
    doc_id: Optional[str] = None,
) -> dict[str, Any]:
    """Intake an original source document directly into a binder's sources folder.

    Co-locates the raw untouched original file with its normalized Markdown representation:
      ~/Vault/Binders/<binder_id>/sources/<doc_id>/<safe_name>
      ~/Vault/Binders/<binder_id>/sources/<doc_id>/document.md
      ~/Vault/Binders/<binder_id>/sources/<doc_id>/meta.json
    Visible in system file pickers, filtered in uDos file manager and Obsidian.
    """
    source_hash = hashlib.sha256(content_bytes).hexdigest()
    safe_name = _safe_filename(file_name)

    if not doc_id:
        doc_id = f"src_{source_hash[:12]}"

    sources_dir = binder_dir / "sources" / doc_id
    sources_dir.mkdir(parents=True, exist_ok=True)

    orig_file = sources_dir / safe_name
    orig_file.write_bytes(content_bytes)

    # Decode text for conversion
    try:
        raw_text = content_bytes.decode("utf-8")
    except UnicodeDecodeError:
        raw_text = content_bytes.decode("latin-1", errors="replace")

    suffix = Path(safe_name).suffix.lstrip(".").lower()
    conversion = convert_content_to_markdown(raw_text, source_format=suffix or "auto")

    frontmatter = (
        f"---\n"
        f"doc_id: \"{doc_id}\"\n"
        f"source_file: \"{safe_name}\"\n"
        f"source_sha256: \"{source_hash}\"\n"
        f"acquired_at: \"{datetime.now(UTC).isoformat()}\"\n"
        f"converter: \"{conversion.plugin_id}\"\n"
        f"privacy: \"private\"\n"
        f"---\n\n"
    )
    normalized_md = frontmatter + conversion.markdown
    output_hash = hashlib.sha256(normalized_md.encode("utf-8")).hexdigest()

    md_file = sources_dir / "document.md"
    md_file.write_text(normalized_md, encoding="utf-8")

    meta = {
        "doc_id": doc_id,
        "file_name": safe_name,
        "source_uri": source_uri or f"file://{orig_file}",
        "author": author or "Unknown",
        "acquired_at": datetime.now(UTC).isoformat(),
        "source_sha256": source_hash,
        "output_sha256": output_hash,
        "original_path": str(orig_file),
        "markdown_path": str(md_file),
        "converter_plugin_id": conversion.plugin_id,
        "source_format": conversion.source_format,
        "privacy": "private",
        "size_bytes": len(content_bytes),
    }

    meta_file = sources_dir / "meta.json"
    meta_file.write_text(json.dumps(meta, indent=2), encoding="utf-8")
    log.info("Ingested binder source %s (%s, sha256: %s)", doc_id, safe_name, source_hash[:8])
    return meta
