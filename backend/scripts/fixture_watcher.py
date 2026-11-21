"""Fixture watcher – triggers library rebuild on fixture change.

Runs as a background process (can be started via `/schedule` or manually).
It monitors the shared fixture JSON file and calls the library index build
function when the file is modified.
"""

import time
from pathlib import Path

# Import the build function directly to avoid HTTP round‑trip.
from app.services.library_index import build_index

FIXTURE_PATH = Path("/Users/fredbook/Shared/fixtures/fixture.json").expanduser().resolve()

def main(poll_interval: float = 2.0) -> None:
    """Poll the fixture file's modification time and rebuild index on change."""
    if not FIXTURE_PATH.is_file():
        print(f"[watcher] Fixture not found at {FIXTURE_PATH}")
        return
    last_mtime = FIXTURE_PATH.stat().st_mtime
    print(f"[watcher] Monitoring {FIXTURE_PATH} (interval {poll_interval}s)")
    try:
        while True:
            time.sleep(poll_interval)
            try:
                mtime = FIXTURE_PATH.stat().st_mtime
            except FileNotFoundError:
                continue
            if mtime != last_mtime:
                print("[watcher] Detected change, rebuilding library index…")
                result = build_index()
                print(f"[watcher] build_index result: {result}")
                last_mtime = mtime
    except KeyboardInterrupt:
        print("[watcher] Stopped")

if __name__ == "__main__":
    main()
