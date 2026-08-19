#!/usr/bin/env python3
# path-policy: allow-literals
"""Reject newly added hard-coded uDOS state paths beneath the user home."""

from __future__ import annotations

import argparse
import re
import subprocess
import sys
from pathlib import Path


FORBIDDEN = re.compile(
    r"(?:~|\$\{?HOME\}?|Path\.home\(\)|os\.path\.expanduser\([^)]*~)"
    r"[^\n]*(?:\.ucore|\.udos|\.snackbar|\.snacks|\.uds|\.uCode1|\.uhomenest)"
)
ALLOW_MARKER = "path-policy: allow-literals"
CANONICAL_HOME = re.compile(
    r"(?:~|\$\{?HOME\}?|Path\.home\(\))[^\n]*(?:/|\"|')Code(?:/|\"|')[^\n]*\.udos"
)


def staged_diff() -> str:
    return subprocess.run(
        ["git", "diff", "--cached", "--unified=0", "--no-color"],
        check=True,
        capture_output=True,
        text=True,
    ).stdout


def file_allows_literals(path: str) -> bool:
    candidate = Path(path)
    if not candidate.is_file():
        return False
    try:
        return ALLOW_MARKER in "\n".join(candidate.read_text(errors="replace").splitlines()[:10])
    except OSError:
        return False


def violations(diff: str) -> list[str]:
    current_file = ""
    allowed = False
    found: list[str] = []
    for line in diff.splitlines():
        if line.startswith("+++ b/"):
            current_file = line[6:]
            allowed = file_allows_literals(current_file)
            continue
        if allowed or not line.startswith("+") or line.startswith("+++"):
            continue
        addition = line[1:]
        if (
            "path-policy: allow" not in addition
            and not CANONICAL_HOME.search(addition)
            and FORBIDDEN.search(addition)
        ):
            found.append(f"{current_file}: {addition.strip()}")
    return found


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--diff-stdin", action="store_true", help="read a unified diff from stdin")
    args = parser.parse_args()
    diff = sys.stdin.read() if args.diff_stdin else staged_diff()
    found = violations(diff)
    if not found:
        print("Home path policy: OK")
        return 0
    print("New hard-coded home state paths are forbidden; use UDOS_HOME:")
    for item in found:
        print(f"  {item}")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
