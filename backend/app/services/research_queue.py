"""Research Job Queue — SQLite-backed async pipeline for BrowserUI research.

Orchestrates: scrape URL → summarise via ChatUI → save to binder.
Jobs tracked in ``$UDOS_HOME/indices/research_queue.db``.
"""

from __future__ import annotations

import asyncio
import json
import logging
import random
import sqlite3
import uuid
from contextlib import suppress
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

from app.core.settings import settings

log = logging.getLogger("ucore.research_queue")

DB_PATH = settings.udos_home / "indices" / "research_queue.db"

SCHEMA = """
CREATE TABLE IF NOT EXISTS jobs (
    id TEXT PRIMARY KEY,
    url TEXT NOT NULL,
    binder TEXT NOT NULL,
    tags TEXT DEFAULT '[]',
    mode TEXT DEFAULT 'summarise',
    state TEXT DEFAULT 'pending',
    progress INTEGER DEFAULT 0,
    result TEXT,
    error TEXT,
    created TEXT NOT NULL,
    started TEXT,
    completed TEXT
);
CREATE INDEX IF NOT EXISTS idx_jobs_state ON jobs(state);
CREATE INDEX IF NOT EXISTS idx_jobs_binder ON jobs(binder);
"""


class ResearchJob:
    """A single research job in the queue."""

    def __init__(self, row: sqlite3.Row):
        self.id = row["id"]
        self.url = row["url"]
        self.binder = row["binder"]
        self.tags = json.loads(row["tags"])
        self.mode = row["mode"]
        self.state = row["state"]
        self.progress = row["progress"]
        self.result = row["result"]
        self.error = row["error"]
        self.created = row["created"]
        self.started = row["started"]
        self.completed = row["completed"]
        self.attempts = row["attempts"]
        self.retry_at = row["retry_at"]

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "url": self.url,
            "binder": self.binder,
            "tags": self.tags,
            "mode": self.mode,
            "state": self.state,
            "progress": self.progress,
            "result": self.result,
            "error": self.error,
            "created": self.created,
            "started": self.started,
            "completed": self.completed,
            "attempts": self.attempts,
            "retry_at": self.retry_at,
        }


class ResearchQueue:
    """Enqueue and track BrowserUI research jobs."""

    def __init__(self, db_path: Path | None = None) -> None:
        db_path = db_path or DB_PATH
        db_path.parent.mkdir(parents=True, exist_ok=True)
        self._conn = sqlite3.connect(str(db_path))
        self._conn.row_factory = sqlite3.Row
        self._conn.executescript(SCHEMA)
        columns = {row[1] for row in self._conn.execute("PRAGMA table_info(jobs)")}
        for name, definition in (("attempts", "INTEGER DEFAULT 0"), ("retry_at", "TEXT")):
            if name not in columns:
                self._conn.execute(f"ALTER TABLE jobs ADD COLUMN {name} {definition}")
        self._conn.commit()
        self._lock = asyncio.Lock()
        self._wake = asyncio.Event()
        self._worker: asyncio.Task | None = None
        self._active_job: str | None = None
        self._active_task: asyncio.Task | None = None

    async def start(self):
        if self._worker and not self._worker.done():
            return
        # A single worker belongs to the existing uCore process. Recover work
        # interrupted before a terminal result; attempts cap restart loops.
        self._conn.execute(
            "UPDATE jobs SET state=CASE WHEN attempts >= 3 THEN 'failed' ELSE 'pending' END, error='Interrupted by service restart' WHERE state IN ('scraping','summarising','saving')"
        )
        self._conn.commit()
        self._worker = asyncio.create_task(self._run(), name="research-worker")

    async def stop(self):
        if self._worker:
            self._worker.cancel()
            with suppress(asyncio.CancelledError):
                await self._worker
            self._worker = None
        self._conn.close()

    async def _run(self):
        while True:
            self._wake.clear()
            try:
                if await self.process_next() is not None:
                    continue
            except Exception:
                log.exception("Research worker cycle failed")
            try:
                await asyncio.wait_for(self._wake.wait(), timeout=30)
            except TimeoutError:
                pass

    def summary(self):
        counts = {
            row[0]: row[1]
            for row in self._conn.execute("SELECT state, count(*) FROM jobs GROUP BY state")
        }
        return {
            "running": bool(self._worker and not self._worker.done()),
            "concurrency": 1,
            "queue_limit": 100,
            "states": counts,
        }

    async def enqueue(self, url, binder="research", tags=None, mode="summarise"):
        """Enqueue a new research job. Returns job ID."""
        vault = (Path.home() / "Vault").resolve()
        destination = (vault / binder).resolve()
        if not destination.is_relative_to(vault) or destination == vault:
            raise ValueError("Choose a binder within your vault")
        count = self._conn.execute(
            "SELECT count(*) FROM jobs WHERE state NOT IN ('completed','failed','cancelled')"
        ).fetchone()[0]
        if count >= 100:
            raise ValueError("Research queue is full. Wait for existing jobs to finish.")
        job_id = str(uuid.uuid4())
        now = datetime.now(UTC).isoformat()
        self._conn.execute(
            "INSERT INTO jobs (id,url,binder,tags,mode,state,progress,created) "
            "VALUES (?,?,?,?,?,'pending',0,?)",
            (job_id, url, binder, json.dumps(tags or []), mode, now),
        )
        self._conn.commit()
        self._wake.set()
        log.info("Enqueued job %s: %s → %s", job_id, url, binder)
        return job_id

    async def status(self, job_id):
        """Get job status by ID."""
        row = self._conn.execute("SELECT * FROM jobs WHERE id = ?", (job_id,)).fetchone()
        return ResearchJob(row).to_dict() if row else None

    async def update_state(self, job_id, state, progress=0, result=None, error=None):
        """Update job state and progress."""
        now = datetime.now(UTC).isoformat()
        updates = ["state = ?", "progress = ?", "started = COALESCE(started, ?)"]
        params: list = [state, progress, now]
        if result is not None:
            updates.append("result = ?")
            params.append(result)
        if error is not None:
            updates.append("error = ?")
            params.append(error)
        if state in ("completed", "failed", "cancelled"):
            updates.append("completed = ?")
            params.append(now)
        params.append(job_id)
        self._conn.execute(f"UPDATE jobs SET {', '.join(updates)} WHERE id = ?", params)
        self._conn.commit()

    async def list_jobs(self, state=None, binder=None, limit=50):
        """List jobs, optionally filtered."""
        query = "SELECT * FROM jobs WHERE 1=1"
        params: list = []
        if state:
            query += " AND state = ?"
            params.append(state)
        if binder:
            query += " AND binder = ?"
            params.append(binder)
        query += " ORDER BY created DESC LIMIT ?"
        params.append(limit)
        return [ResearchJob(r).to_dict() for r in self._conn.execute(query, params).fetchall()]

    async def process_next(self) -> dict | None:
        """Process next pending job: scrape → summarise → save to binder."""
        row = self._conn.execute(
            "SELECT * FROM jobs WHERE state='pending' AND (retry_at IS NULL OR retry_at <= ?) ORDER BY created ASC LIMIT 1",
            (datetime.now(UTC).isoformat(),),
        ).fetchone()
        if row is None:
            return None
        return await self.process_job(row["id"])

    async def process_job(self, job_id: str) -> dict | None:
        """Serialize manual runs and the background worker through one lane."""
        async with self._lock:
            self._active_job = job_id
            self._active_task = asyncio.create_task(self._process_job(job_id))
            try:
                return await asyncio.wait_for(self._active_task, timeout=180)
            except asyncio.CancelledError:
                status = self._refetch(job_id)
                if (
                    status
                    and status["state"] == "cancelled"
                    and not asyncio.current_task().cancelling()
                ):
                    return status
                raise
            except TimeoutError:
                await self._retry_or_fail(job_id, "Research timed out", retryable=True)
                return self._refetch(job_id)
            except Exception as exc:
                log.exception("Research job failed: %s", job_id)
                await self._retry_or_fail(job_id, str(exc))
                return self._refetch(job_id)
            finally:
                self._active_job = None
                self._active_task = None

    async def cancel(self, job_id):
        status = self._refetch(job_id)
        if not status:
            raise KeyError(job_id)
        if status["state"] == "saving":
            raise ValueError("The note is already being saved. Wait for completion.")
        if status["state"] in ("completed", "failed", "cancelled"):
            return status
        await self.update_state(job_id, "cancelled", error="Cancelled")
        if self._active_job == job_id and self._active_task:
            self._active_task.cancel()
        return self._refetch(job_id)

    async def retry(self, job_id):
        status = self._refetch(job_id)
        if not status:
            raise KeyError(job_id)
        if status["state"] not in ("failed", "cancelled"):
            raise ValueError("Only failed or cancelled jobs can be retried")
        self._conn.execute(
            "UPDATE jobs SET state='pending', attempts=0, retry_at=NULL, progress=0, error=NULL, started=NULL, completed=NULL WHERE id=?",
            (job_id,),
        )
        self._conn.commit()
        self._wake.set()
        return self._refetch(job_id)

    async def _retry_or_fail(self, job_id, error, *, retryable=False):
        row = self._conn.execute("SELECT attempts FROM jobs WHERE id=?", (job_id,)).fetchone()
        if retryable and row and row[0] < 3:
            retry_at = (
                datetime.now(UTC)
                + timedelta(seconds=30 * 2 ** max(0, row[0] - 1) + random.uniform(0, 10))
            ).isoformat()
            self._conn.execute(
                "UPDATE jobs SET state='pending', error=?, retry_at=? WHERE id=?",
                (error, retry_at, job_id),
            )
            self._conn.commit()
        else:
            await self.update_state(job_id, "failed", error=error)

    async def _process_job(self, job_id):
        row = self._conn.execute(
            "SELECT * FROM jobs WHERE id=? AND state='pending' AND (retry_at IS NULL OR retry_at <= ?)",
            (job_id, datetime.now(UTC).isoformat()),
        ).fetchone()
        if row is None:
            return self._refetch(job_id)
        claimed = self._conn.execute(
            "UPDATE jobs SET state='scraping', attempts=attempts+1, error=NULL, retry_at=NULL WHERE id=? AND state='pending'",
            (job_id,),
        )
        self._conn.commit()
        if not claimed.rowcount:
            return self._refetch(job_id)
        job = ResearchJob(row)
        await self.update_state(job.id, "scraping", progress=10)

        # Phase 1: Scrape URL
        try:
            import aiohttp

            timeout = aiohttp.ClientTimeout(total=15)
            headers = {"User-Agent": "Mozilla/5.0 (compatible; uCore-Scraper/1.0)"}
            async with aiohttp.ClientSession(timeout=timeout, headers=headers) as sess:
                async with sess.get(job.url) as resp:
                    if not resp.ok:
                        await self._retry_or_fail(
                            job.id,
                            f"Source returned HTTP {resp.status}",
                            retryable=resp.status in (408, 429) or resp.status >= 500,
                        )
                        return self._refetch(job.id)
                    html = await resp.text(errors="replace")
            from app.api.chat import _html_body_text, _html_desc, _html_title

            title = _html_title(html, job.url)
            description = _html_desc(html)
            text = _html_body_text(html)
            await self.update_state(job.id, "summarising", progress=40)
        except Exception as e:
            await self._retry_or_fail(
                job.id,
                str(e),
                retryable=isinstance(e, (TimeoutError, aiohttp.ClientConnectionError)),
            )
            return self._refetch(job.id)

        # Phase 2: Summarise via ChatUI
        warning = None
        try:
            from app.api.chat import get_router

            router = get_router()
            prompt = (
                f"Summarise concisely. Include key points, main argument, "
                f"and 3-5 suggested tags with # prefix. Use markdown.\n\n"
                f"Title: {title}\n\n{text[:4000]}"
            )
            sr = await asyncio.wait_for(
                router.chat(
                    messages=[{"role": "user", "content": prompt}],
                    model="ollama/qwen2.5-coder:3b",
                    temperature=0.3,
                ),
                timeout=120,
            )
            summary = sr.get("content", description)
            await self.update_state(job.id, "saving", progress=70)
        except Exception:
            warning = "Saved the source without a summary because the local model was unavailable."
            summary = f"## {title}\n\n{description}\n\n*Source: [{job.url}]({job.url})*"

        # Phase 3: Save to vault binder
        try:
            result = await asyncio.to_thread(self._save_document, job, title, description, summary)
            if warning:
                result["warning"] = warning
            # Auto-score: token count + source quality → 0-5
            auto_score = min(5, round((len(summary) / 500) + (1 if description else 0), 1))
            result["score"] = auto_score
            result = json.dumps(result)
            await self.update_state(job.id, "completed", progress=100, result=result)
        except Exception as e:
            await self.update_state(job.id, "failed", error=f"Save error: {e}")

        return self._refetch(job.id)

    @staticmethod
    def _save_document(job, title, description, summary):
        """Keep filesystem work off the event loop; preserve existing notes."""
        vault_root = (Path.home() / "Vault").resolve()
        vault_dir = (vault_root / job.binder).resolve()
        if not vault_dir.is_relative_to(vault_root) or vault_dir == vault_root:
            raise ValueError("Binder must be within your vault")
        vault_dir.mkdir(parents=True, exist_ok=True)
        safe = "".join(c for c in title if c.isalnum() or c in " _-")[:80]
        safe = safe.strip().replace(" ", "-") or "untitled"
        fp = vault_dir / f"{safe}-{job.id}.md"
        now = datetime.now(UTC).strftime("%Y-%m-%d %H:%M")
        temporary = fp.with_suffix(".md.tmp")
        temporary.write_text(
            f"# {title}\n\n> Source: [{job.url}]({job.url})\n"
            f"> Scraped: {now}\n> Tags: {' '.join(job.tags)}\n\n{summary}\n",
            encoding="utf-8",
        )
        if not fp.exists():
            temporary.replace(fp)
        else:
            temporary.unlink(missing_ok=True)
        cp = vault_dir / "CITATIONS.md"
        cit = f"- [{title}]({job.url}) — job {job.id}\n"
        # Append rather than replacing the user's citation file. A recovered job
        # has the same ID, so it cannot add the same citation again.
        existing = cp.read_text(encoding="utf-8") if cp.exists() else ""
        if cit not in existing:
            with cp.open("a", encoding="utf-8") as stream:
                stream.write(("# Citations\n\n" if not existing else "") + cit)
        return {"file": str(fp), "title": title, "binder": job.binder}

    def _refetch(self, job_id):
        row = self._conn.execute("SELECT * FROM jobs WHERE id=?", (job_id,)).fetchone()
        return ResearchJob(row).to_dict() if row else None
