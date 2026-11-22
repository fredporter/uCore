#!/usr/bin/env python3
"""Select reviewed Engineering commands or active-profile uFlow workflows."""

from __future__ import annotations

import argparse
import json
import os
import shlex
import subprocess
import sys
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import quote
from urllib.request import Request, urlopen

REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_MANIFEST = REPO_ROOT / "config" / "engineering-commands.json"
DEFAULT_BASE_URL = "http://127.0.0.1:8484"


def load_engineering_commands(path: Path = DEFAULT_MANIFEST) -> list[dict[str, Any]]:
    """Load and validate the committed, non-shell command catalogue."""
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, list):
        raise TypeError("Engineering command catalogue must be a list")
    commands: list[dict[str, Any]] = []
    seen: set[str] = set()
    for item in data:
        if not isinstance(item, dict):
            raise TypeError("Each Engineering command must be an object")
        ident = item.get("id")
        argv = item.get("argv")
        if (
            not isinstance(ident, str)
            or not ident.strip()
            or ident in seen
            or any(char in ident for char in "\r\n\t")
            or not isinstance(argv, list)
            or not argv
            or not all(isinstance(part, str) and part for part in argv)
            or not isinstance(item.get("name"), str)
            or not isinstance(item.get("description"), str)
        ):
            raise ValueError(f"Invalid Engineering command: {ident!r}")
        seen.add(ident)
        commands.append(item)
    return commands


def api_json(base_url: str, path: str, *, method: str = "GET", timeout: float = 300) -> dict[str, Any]:
    """Call uCore without persisting profiles, credentials, or workflow copies."""
    request = Request(
        f"{base_url.rstrip('/')}{path}",
        method=method,
        headers={"Accept": "application/json", "Content-Type": "application/json"},
        data=b"{}" if method == "POST" else None,
    )
    try:
        with urlopen(request, timeout=timeout) as response:
            payload = json.load(response)
    except HTTPError as exc:
        try:
            detail = json.loads(exc.read().decode("utf-8")).get("error", str(exc))
        except (ValueError, UnicodeDecodeError, AttributeError):
            detail = str(exc)
        raise RuntimeError(f"uCore returned HTTP {exc.code}: {detail}") from exc
    except (URLError, TimeoutError, json.JSONDecodeError) as exc:
        raise RuntimeError(f"uCore is unavailable at {base_url}: {exc}") from exc
    if not isinstance(payload, dict):
        raise TypeError("uCore returned an unexpected response")
    return payload


def list_user_workflows(base_url: str, timeout: float) -> list[dict[str, Any]]:
    payload = api_json(base_url, "/api/workflows", timeout=timeout)
    workflows = payload.get("workflows")
    if not isinstance(workflows, list):
        raise TypeError("uCore returned an invalid workflow catalogue")
    valid: list[dict[str, Any]] = []
    for workflow in workflows:
        if not isinstance(workflow, dict) or not isinstance(workflow.get("id"), str):
            continue
        if not workflow["id"] or any(char in workflow["id"] for char in "\r\n\t"):
            continue
        valid.append(workflow)
    return valid


def display_rows(commands: list[dict[str, Any]]) -> list[str]:
    return [
        f"{item['id']}\t{item.get('name', item['id'])} — {item.get('description', '')}"
        for item in commands
    ]


def choose(commands: list[dict[str, Any]], prompt: str, selected: str | None) -> dict[str, Any] | None:
    if selected is not None:
        return next((item for item in commands if item["id"] == selected), None)
    if not commands:
        return None
    result = subprocess.run(
        ["fzf", "--height=40%", f"--prompt={prompt} > ", "--delimiter=\t", "--with-nth=2.."],
        input="\n".join(display_rows(commands)),
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0 or not result.stdout:
        return None
    ident = result.stdout.strip().split("\t", 1)[0]
    return next((item for item in commands if item["id"] == ident), None)



def run_engineering(command: dict[str, Any]) -> int:
    print("Running:", shlex.join(command["argv"]), flush=True)
    return subprocess.run(command["argv"], cwd=REPO_ROOT, check=False).returncode


def run_user_workflow(base_url: str, workflow_id: str, timeout: float) -> int:
    result = api_json(
        base_url,
        f"/api/workflows/{quote(workflow_id, safe='')}/run",
        method="POST",
        timeout=timeout,
    )
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0 if result.get("status") == "completed" else 1


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--mode", choices=("dev", "user"), help="Skip the mode selector")
    parser.add_argument("--select", metavar="ID", help="Run a known command/workflow without fzf")
    parser.add_argument("--list", action="store_true", help="List entries without executing")
    parser.add_argument("--yes", action="store_true", help="Confirm a User workflow run")
    parser.add_argument("--base-url", default=os.environ.get("UCORE_URL", DEFAULT_BASE_URL))
    parser.add_argument("--timeout", type=float, default=300, help="HTTP timeout in seconds")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.timeout <= 0:
        print("Timeout must be positive", file=sys.stderr)
        return 2
    mode = args.mode
    if mode is None:
        modes = [
            {"id": "dev", "name": "Engineering", "description": "Build and maintain uDOS"},
            {"id": "user", "name": "User", "description": "Run active-profile uFlow workflows"},
        ]
        picked = choose(modes, "uDOS mode", None)
        if picked is None:
            print("Cancelled")
            return 0
        mode = picked["id"]
    try:
        commands = (
            load_engineering_commands()
            if mode == "dev"
            else list_user_workflows(args.base_url, args.timeout)
        )
        if args.list:
            print("\n".join(display_rows(commands)))
            return 0
        command = choose(commands, "Engineering" if mode == "dev" else "User workflows", args.select)
        if command is None:
            if args.select is not None and any(item["id"] == args.select for item in commands):
                print("Cancelled")
            else:
                print("No matching command or workflow", file=sys.stderr)
            return 0 if args.select is None else 1
        if mode == "dev":
            return run_engineering(command)
        print(f"Run {command.get('name', command['id'])} in the active uCore profile?")
        if not args.yes and input("Type 'run' to confirm: ").strip() != "run":
            print("Cancelled")
            return 0
        return run_user_workflow(args.base_url, command["id"], args.timeout)
    except (OSError, TypeError, ValueError, RuntimeError, json.JSONDecodeError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1
    except (KeyboardInterrupt, EOFError):
        print("\nCancelled")
        return 130


if __name__ == "__main__":
    raise SystemExit(main())
