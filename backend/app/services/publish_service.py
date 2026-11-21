"""Publishing Service — Local First Library Delivery.

Reads binder section from ~/Shared/fixtures/fixture.json, validates fixture existence,
strips private front-matter, and invokes uCore publishing compiler to generate offline Tomb bundles.
"""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any, Dict, Optional

from app.core.settings import settings

log = logging.getLogger("ucore.publish_service")

FIXTURE_PATH = settings.shared_vault_root / "fixtures" / "fixture.json"
DEFAULT_TOMB_OUTPUT = settings.udos_home / "tombs" / "library"


def load_fixture_binder() -> Dict[str, Any]:
    """Load and verify fixture file at ~/Shared/fixtures/fixture.json, returning binder dict."""
    if not FIXTURE_PATH.exists():
        raise FileNotFoundError(f"Required fixture not found at {FIXTURE_PATH}")

    try:
        data = json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))
    except Exception as e:
        raise ValueError(f"Failed to parse JSON fixture at {FIXTURE_PATH}: {e}")

    binder = data.get("binder")
    if not binder or not isinstance(binder, dict):
        raise ValueError(f"Invalid or missing 'binder' section in fixture at {FIXTURE_PATH}")

    return binder


def compile_binder_to_tomb(output_dir: Optional[Path] = None) -> Dict[str, Any]:
    """Read binder from fixture, compile documents stripping private front-matter, and generate Tomb bundle."""
    binder = load_fixture_binder()

    target_dir = Path(output_dir) if output_dir else DEFAULT_TOMB_OUTPUT
    target_dir.mkdir(parents=True, exist_ok=True)

    title = binder.get("title", "Oakhaven Sanctuary Field Guide")
    edition_num = binder.get("edition_num", 1)
    documents = binder.get("documents", [])

    if not documents:
        raise ValueError("Binder contains no documents to publish")

    # Combine document contents or compile primary document
    # Using the compiler from udos_publishing
    import sys
    publishing_path = settings.udos_root / "uCorePub"
    if str(publishing_path) not in sys.path:
        sys.path.append(str(publishing_path))

    from udos_publishing.src.compiler import compile_edition_to_static

    # Compile the first document or concatenated documents using compile_edition_to_static
    combined_md_parts = []
    for doc in documents:
        doc_content = doc.get("content", "")
        # Validate private front-matter stripping (frontmatter is handled by compiler, but we verify here too)
        combined_md_parts.append(doc_content)

    full_markdown = "\n\n---\n\n".join(combined_md_parts)

    receipt = compile_edition_to_static(
        edition_markdown=full_markdown,
        title=title,
        edition_num=edition_num,
        output_dir=target_dir,
    )

    # Verify private author keys or sensitive front-matter are stripped in generated clean md
    md_file_path = receipt.get("markdown_path")
    if md_file_path:
        md_text = Path(md_file_path).read_text(encoding="utf-8")
        if "private_author_key" in md_text:
            log.warning("private_author_key detected in compiled markdown; forcing removal")
            clean_lines = [line for line in md_text.splitlines() if "private_author_key" not in line]
            Path(md_file_path).write_text("\n".join(clean_lines), encoding="utf-8")

    return {
        "type": "publish_result",
        "binder_id": binder.get("binder_id"),
        "title": title,
        "tomb_path": str(target_dir),
        "receipt": receipt,
    }
