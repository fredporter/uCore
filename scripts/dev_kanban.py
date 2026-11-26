"""Launch Cline Kanban and export its development boards."""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import tempfile
import time
from pathlib import Path
from urllib.error import URLError
from urllib.request import urlopen

WORKSPACE = Path(__file__).resolve().parents[2]
BOARDS = Path.home() / ".cline" / "kanban" / "workspaces"
EXPORT = WORKSPACE / "kanban.json"
BOARD_URL = "http://127.0.0.1:3484/ucore"


def export_boards() -> None:
    index = json.loads((BOARDS / "index.json").read_text())["entries"]
    boards = {}
    for name, entry in sorted(index.items()):
        repo = Path(entry["repoPath"]).resolve()
        board = BOARDS / name / "board.json"
        if repo.is_relative_to(WORKSPACE) and board.is_file():
            boards[name] = {
                "repository": str(repo.relative_to(WORKSPACE)),
                **json.loads(board.read_text()),
            }

    content = json.dumps({"version": 1, "boards": boards}, indent=2, ensure_ascii=False) + "\n"
    if EXPORT.exists() and EXPORT.read_text() == content:
        return
    with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", dir=WORKSPACE, delete=False) as output:
        output.write(content)
    try:
        os.replace(output.name, EXPORT)
    finally:
        Path(output.name).unlink(missing_ok=True)


def board_is_running() -> bool:
    try:
        with urlopen(BOARD_URL, timeout=1) as response:
            return response.status == 200 and b"kanban" in response.read().lower()
    except (URLError, TimeoutError):
        return False


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--export", action="store_true", help="Refresh kanban.json and exit.")
    parser.add_argument("--no-open", action="store_true", help="Keep the browser closed.")
    args = parser.parse_args()
    if args.export:
        export_boards()
        return 0

    server = None
    if not board_is_running():
        server = subprocess.Popen(
            ["kanban", "--host", "127.0.0.1", "--port", "3484",
             "--no-open", "--skip-shutdown-cleanup"],
            cwd=WORKSPACE / "uCore",
        )

    try:
        for _ in range(30):
            if board_is_running():
                break
            if server is not None and server.poll() is not None:
                return server.returncode
            time.sleep(0.25)
        else:
            raise RuntimeError("Cline Kanban did not become ready on port 3484")

        export_boards()
        if not args.no_open:
            subprocess.run(["open", BOARD_URL], check=True)
        print(f"Watching Cline boards at {BOARD_URL} and updating {EXPORT.name}", flush=True)
        while board_is_running():
            time.sleep(2)
            export_boards()
        if server is not None and server.poll() is not None:
            return server.returncode
        return 0
    except KeyboardInterrupt:
        return 0
    finally:
        if server is not None and server.poll() is None:
            server.terminate()
            server.wait(timeout=10)


if __name__ == "__main__":
    raise SystemExit(main())
