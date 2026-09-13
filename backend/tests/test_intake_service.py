"""Tests for Intake Service (Milestone P4).

Verifies:
1. Cryptographic original preservation (byte-for-byte).
2. SHA-256 hash calculation.
3. Markdown extraction and frontmatter provenance.
4. Intake receipt generation and retrieval.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest

from app.services import intake_service


@pytest.fixture
def temp_vault(tmp_path, monkeypatch):
    vault = tmp_path / "Vault"
    vault.mkdir(parents=True, exist_ok=True)
    orig = vault / "Originals"
    docs = vault / "Documents"

    monkeypatch.setattr(intake_service, "VAULT_ROOT", vault)
    monkeypatch.setattr(intake_service, "ORIGINALS_ROOT", orig)
    monkeypatch.setattr(intake_service, "DOCUMENTS_ROOT", docs)
    return vault


def test_intake_preserves_original_bytes_and_checksum(temp_vault):
    sample_content = b"# Specification Document\n\nThis is raw unedited content from an external source."
    expected_hash = hashlib.sha256(sample_content).hexdigest()

    receipt = intake_service.intake_file(
        file_name="spec_v1.md",
        content_bytes=sample_content,
        source_uri="https://example.com/spec_v1.md",
        author="Architect",
    )

    assert receipt["source_sha256"] == expected_hash
    assert receipt["file_name"] == "spec_v1.md"
    assert receipt["author"] == "Architect"
    assert receipt["privacy"] == "private"

    doc_id = receipt["doc_id"]
    orig_file = temp_vault / "Originals" / doc_id / "spec_v1.md"
    assert orig_file.exists()
    assert orig_file.read_bytes() == sample_content

    # Normalized markdown file check
    md_file = temp_vault / "Documents" / f"{doc_id}.md"
    assert md_file.exists()
    md_text = md_file.read_text(encoding="utf-8")
    assert f"source_sha256: \"{expected_hash}\"" in md_text
    assert "This is raw unedited content" in md_text

    # Receipt retrieval
    loaded_receipt = intake_service.get_intake_receipt(doc_id)
    assert loaded_receipt is not None
    assert loaded_receipt["source_sha256"] == expected_hash
    assert loaded_receipt["size_bytes"] == len(sample_content)


def test_intake_binary_preservation(temp_vault):
    # Binary bytes that are not valid utf-8
    sample_binary = b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\xff\xfe\xfd"
    expected_hash = hashlib.sha256(sample_binary).hexdigest()

    receipt = intake_service.intake_file(
        file_name="diagram.png",
        content_bytes=sample_binary,
    )

    assert receipt["source_sha256"] == expected_hash
    doc_id = receipt["doc_id"]
    saved_binary = (temp_vault / "Originals" / doc_id / "diagram.png").read_bytes()
    assert saved_binary == sample_binary
