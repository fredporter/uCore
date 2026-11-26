"""Pin integrity between vendor/lock.yaml and the reviewed NanoCoder installer."""

from __future__ import annotations

import json
import re
from pathlib import Path

import yaml

REPO_ROOT = Path(__file__).resolve().parents[2]
INSTALLER = REPO_ROOT / "scripts" / "install_nanocoder.sh"
LOCK = REPO_ROOT / "vendor" / "lock.yaml"
PATCH_DIR = REPO_ROOT / "vendor" / "patches"


def _installer_pin() -> tuple[str, str]:
    text = INSTALLER.read_text(encoding="utf-8")
    version = re.search(r'^VERSION="([^"]+)"', text, re.MULTILINE)
    digest = re.search(r'^EXPECTED_SHA256="([0-9a-f]{64})"', text, re.MULTILINE)
    assert version is not None, "VERSION pin missing from install_nanocoder.sh"
    assert digest is not None, "EXPECTED_SHA256 pin missing from install_nanocoder.sh"
    return version.group(1), digest.group(1)


def test_installer_pin_matches_vendor_lock():
    lock = yaml.safe_load(LOCK.read_text(encoding="utf-8"))
    module = lock["modules"]["nanocoder"]
    version, digest = _installer_pin()

    assert version == module["resolved_ref"]
    assert digest == module["sha256"]


def test_installer_applies_every_reviewed_patch():
    text = INSTALLER.read_text(encoding="utf-8")
    patches = sorted(p.name for p in PATCH_DIR.glob("nanocoder-*.patch"))

    assert patches, "no reviewed NanoCoder patches found"
    for name in patches:
        assert name in text, f"{name} is not applied by scripts/install_nanocoder.sh"


def test_installer_uses_the_retained_artifact_as_input():
    text = INSTALLER.read_text(encoding="utf-8")

    assert 'npm install "$PACKAGE"' not in text, "installing by registry name defeats offline installs"
    assert 'set -- "$ARCHIVE"' in text


def test_bundle_digest_is_pinned_in_reviewed_source():
    text = INSTALLER.read_text(encoding="utf-8")

    assert "EXPECTED_DEPS_SHA256" in text
    assert "EXPECTED_DEPS_BYTES" in text
    assert "catalogue_bundle_digest" in text, "the Layer 0 catalogue must confirm the pin"
    # A sidecar may only confirm the pin, never define it.
    assert 'sidecar_digest" != "$EXPECTED_DEPS_SHA256"' in text


def test_dependency_lock_is_versioned_and_complete():
    lock_path = REPO_ROOT / "vendor" / "nanocoder-1.30.0-deps-lock.json"

    assert lock_path.is_file(), "the dependency lock must be committed"
    lock = json.loads(lock_path.read_text(encoding="utf-8"))
    assert lock["lockfileVersion"] >= 3
    assert len(lock["packages"]) >= 350


def test_installer_uses_the_versioned_lock():
    text = INSTALLER.read_text(encoding="utf-8")

    assert 'DEPS_LOCK="$UCORE_ROOT/vendor/' in text
    assert "npm ci" in text


def test_bundle_digest_is_verified_before_extraction():
    text = INSTALLER.read_text(encoding="utf-8")

    assert "verify_deps_bundle" in text
    assert text.count(".sha256") >= 2
    assert text.index('verify_deps_bundle "$cache_source"') < text.index('tar -xzf "$cache_source"')


def test_bundle_rebuild_is_locked():
    text = INSTALLER.read_text(encoding="utf-8")

    assert "DEPS_LOCK" in text
    assert "package-lock.json" in text
    assert "npm ci" in text
    assert "--rebuild-deps" in text


def test_offline_install_requires_a_pinned_dependency_bundle():
    text = INSTALLER.read_text(encoding="utf-8")

    assert "--build-deps" in text
    assert "DEPS_BUNDLE" in text
    assert "--offline" in text
