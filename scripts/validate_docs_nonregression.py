#!/usr/bin/env python3
"""Guard key governance docs against policy drift.

Fails when required hard-cut / preflight statements regress in active docs.
"""

from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def _read(path: str) -> str:
    p = ROOT / path
    if not p.exists():
        raise SystemExit(f"[FAIL] Missing file: {p}")
    return p.read_text(encoding="utf-8", errors="ignore")


def _require(text: str, needle: str, label: str, failures: list[str]) -> None:
    if needle not in text:
        failures.append(f"missing: {label}")


def _forbid(text: str, needle: str, label: str, failures: list[str]) -> None:
    if needle in text:
        failures.append(f"forbidden: {label}")


def main() -> int:
    failures: list[str] = []

    ext_spec = _read("docs/EXTENSION_REGISTRY_SPEC.md")
    policy = _read("docs/RELIABILITY_SINGLE_PATH_POLICY.md")
    dev_flow = _read("docs/specs/ECOSYSTEM_EXTENDED_DEV_FLOW_2026-07-31.md")
    runbook = _read("docs/specs/AUTONOMOUS_DEV_ROUNDS_RUNBOOK.md")

    _require(
        ext_spec,
        '"id": "uflow"',
        "extension spec contains uflow manifest example",
        failures,
    )
    _require(
        ext_spec,
        '"optional": false',
        "extension spec marks required ownership as optional=false",
        failures,
    )
    _require(
        ext_spec,
        "ready=false",
        "preflight block semantics documented",
        failures,
    )
    _require(
        ext_spec,
        "HTTP 412",
        "preflight HTTP 412 documented",
        failures,
    )
    _forbid(
        ext_spec,
        "except ImportError: use uCore's built-in manager",
        "workflow fallback-to-core guidance",
        failures,
    )
    _forbid(
        ext_spec,
        "except ImportError: use uCore's built-in modules",
        "knowledge fallback-to-core guidance",
        failures,
    )

    _require(
        policy,
        "Model Role Split (Speed Without Drift)",
        "policy includes model role split section",
        failures,
    )
    _require(
        policy,
        "Documentation Non-Regression Gate",
        "policy includes documentation non-regression section",
        failures,
    )
    _require(
        dev_flow,
        "Gate 0 - Core Stability First",
        "extended flow includes stability-first gate",
        failures,
    )
    _require(
        runbook,
        "Stop-the-line bundle is required",
        "autonomous runbook enforces stop-the-line bundle",
        failures,
    )
    _require(
        runbook,
        "validate_legacy_settings_cleanup.py",
        "autonomous runbook includes legacy cleanup validation gate",
        failures,
    )

    if failures:
        print("[FAIL] Documentation non-regression checks failed:")
        for item in failures:
            print(f"- {item}")
        return 1

    print("Documentation non-regression checks passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
