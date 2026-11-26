"""Keep the Cline Kanban board available and refresh the workspace export.

Owner: uCore Engineering tooling.
Lifecycle: one-shot ``--ensure`` from a launcher or a launchd ``StartInterval``
agent. This script is not a resident service and does not own the board data.
Writes: a log under ``UDOS_HOME/logs`` and the generated ``kanban.json`` export.
Removal: unload ``com.udos.kanban-supervisor``, delete this script and its
``engineering-commands.json`` entry. Board data in ``~/.cline/kanban`` stays.

Usage:
    python3 scripts/kanban_supervisor.py --ensure   # heal, refresh, exit
    python3 scripts/kanban_supervisor.py --status   # report, change nothing
    python3 scripts/kanban_supervisor.py --open     # heal, then open the board
"""
from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
import time
from datetime import UTC, datetime
from pathlib import Path
from urllib.error import URLError
from urllib.request import urlopen

HERE = Path(__file__).resolve().parent
WORKSPACE = HERE.parents[1]
BOARD_URL = "http://127.0.0.1:3484/ucore"
BOARD_ARGS = [
    "kanban",
    "--host",
    "127.0.0.1",
    "--port",
    "3484",
    "--no-open",
    "--skip-shutdown-cleanup",
]


def udos_home() -> Path:
    explicit = os.environ.get("UDOS_HOME")
    if explicit:
        return Path(explicit).expanduser()
    return Path(os.environ.get("UDOS_ROOT", str(Path.home() / "Code"))).expanduser() / ".udos"


def log_path() -> Path:
    directory = udos_home() / "logs"
    directory.mkdir(parents=True, exist_ok=True)
    return directory / "kanban-supervisor.log"


def log(message: str) -> None:
    stamp = datetime.now(tz=UTC).astimezone().strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{stamp}] {message}\n"
    try:
        with log_path().open("a", encoding="utf-8") as handle:
            handle.write(line)
    except OSError:
        pass


def board_is_running(timeout: float = 1.5) -> bool:
    try:
        with urlopen(BOARD_URL, timeout=timeout) as response:
            return response.status == 200 and b"kanban" in response.read().lower()
    except (URLError, TimeoutError, OSError):
        return False


def export_boards() -> bool:
    """Refresh kanban.json using the existing exporter; never fail the heal."""
    sys.path.insert(0, str(HERE))
    try:
        from dev_kanban import export_boards as exporter
    except ImportError as exc:  # pragma: no cover - exporter import is local
        log(f"export unavailable: {exc}")
        return False
    try:
        exporter()
        return True
    except (OSError, KeyError, ValueError) as exc:  # pragma: no cover
        log(f"export failed: {exc}")
        return False


def find_binary() -> str | None:
    """Locate `kanban`, including nvm installs that launchd's PATH omits."""
    found = shutil.which("kanban")
    if found:
        return found
    candidates = sorted(
        (Path.home() / ".nvm" / "versions" / "node").glob("*/bin/kanban"),
        reverse=True,
    )
    for candidate in candidates:
        if candidate.is_file() and os.access(candidate, os.X_OK):
            return str(candidate)
    for prefix in (Path("/opt/homebrew/bin"), Path("/usr/local/bin")):
        candidate = prefix / "kanban"
        if candidate.is_file() and os.access(candidate, os.X_OK):
            return str(candidate)
    return None


def start_board() -> subprocess.Popen | None:
    binary = find_binary()
    if binary is None:
        log("kanban binary not found on PATH; cannot heal")
        return None
    argv = [binary] + BOARD_ARGS[1:]
    handle = log_path().open("a", encoding="utf-8")
    log(f"starting board: {' '.join(argv)}")
    try:
        return subprocess.Popen(
            argv,
            cwd=WORKSPACE / "uCore",
            stdout=handle,
            stderr=subprocess.STDOUT,
            stdin=subprocess.DEVNULL,
            start_new_session=True,
        )
    except OSError as exc:
        log(f"failed to start board: {exc}")
        return None


def wait_for_board(process: subprocess.Popen | None, timeout: float) -> bool:
    deadline = time.time() + timeout
    while time.time() < deadline:
        if board_is_running():
            return True
        if process is not None and process.poll() is not None:
            log(f"board exited early with status {process.returncode}")
            return False
        time.sleep(0.5)
    return board_is_running()


def ensure(timeout: float = 30.0) -> int:
    if board_is_running():
        log("board already running")
        export_boards()
        return 0
    process = start_board()
    if process is None:
        return 2
    if not wait_for_board(process, timeout):
        log(f"board did not become ready within {timeout:.0f}s")
        return 1
    log(f"board ready at {BOARD_URL}")
    export_boards()
    return 0


def status() -> int:
    running = board_is_running()
    export = WORKSPACE / "kanban.json"
    print(
        json.dumps(
            {
                "running": running,
                "url": BOARD_URL,
                "export": str(export),
                "export_exists": export.exists(),
                "export_modified": (
                    datetime.fromtimestamp(
                        export.stat().st_mtime, tz=UTC
                    ).astimezone().isoformat()
                    if export.exists()
                    else None
                ),
            },
            indent=2,
        )
    )
    return 0 if running else 1


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--ensure", action="store_true", help="Heal the board and refresh the export (default).")
    parser.add_argument("--status", action="store_true", help="Report board state without changing anything.")
    parser.add_argument("--open", action="store_true", help="Heal the board, then open it in the browser.")
    parser.add_argument("--timeout", type=float, default=30.0, help="Seconds to wait for readiness.")
    args = parser.parse_args()

    if args.status:
        return status()
    result = ensure(args.timeout)
    if result == 0 and args.open:
        subprocess.run(["open", BOARD_URL], check=False)
    return result


if __name__ == "__main__":
    raise SystemExit(main())
