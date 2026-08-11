"""Research Job Queue — SQLite-backed async pipeline for BrowserUI research.

Orchestrates: scrape URL → summarise via ChatUI → save to binder.
Jobs tracked in ~/.ucore/indices/research_queue.db.
"""
from __future__ import annotations

import json
import logging
import sqlite3
import uuid
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

log = logging.getLogger("ucore.research_queue")

DB_PATH = Path.home() / ".ucore" / "indices" / "research_queue.db"

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

    def to_dict(self) -> dict:
        return {
            "id": self.id, "url": self.url, "binder": self.binder,
            "tags": self.tags, "mode": self.mode, "state": self.state,
            "progress": self.progress, "result": self.result,
            "error": self.error, "created": self.created,
            "started": self.started, "completed": self.completed,
        }


class ResearchQueue:
    """Enqueue and track BrowserUI research jobs."""

    def __init__(self) -> None:
        DB_PATH.parent.mkdir(parents=True, exist_ok=True)
        self._conn = sqlite3.connect(str(DB_PATH))
        self._conn.row_factory = sqlite3.Row
        self._conn.executescript(SCHEMA)
        self._conn.commit()

    async def enqueue(self, url, binder="research", tags=None, mode="summarise"):
        """Enqueue a new research job. Returns job ID."""
        job_id = str(uuid.uuid4())[:8]
        now = datetime.now(UTC).isoformat()
        self._conn.execute(
            "INSERT INTO jobs (id,url,binder,tags,mode,state,progress,created) "
            "VALUES (?,?,?,?,?,'pending',0,?)",
            (job_id, url, binder, json.dumps(tags or []), mode, now),
        )
        self._conn.commit()
        log.info("Enqueued job %s: %s → %s", job_id, url, binder)
        return job_id

    async def status(self, job_id):
        """Get job status by ID."""
        row = self._conn.execute(
            "SELECT * FROM jobs WHERE id = ?", (job_id,)
        ).fetchone()
        return ResearchJob(row).to_dict() if row else None

    async def update_state(self, job_id, state, progress=0, result=None, error=None):
        """Update job state and progress."""
        now = datetime.now(UTC).isoformat()
        updates = ["state = ?", "progress = ?", "started = COALESCE(started, ?)"]
        params: list = [state, progress, now]
        if result is not None:
            updates.append("result = ?"); params.append(result)
        if error is not None:
            updates.append("error = ?"); params.append(error)
        if state in ("completed", "failed"):
            updates.append("completed = ?"); params.append(now)
        params.append(job_id)
        self._conn.execute(
            f"UPDATE jobs SET {', '.join(updates)} WHERE id = ?", params
        )
        self._conn.commit()

    async def list_jobs(self, state=None, binder=None, limit=50):
        """List jobs, optionally filtered."""
        query = "SELECT * FROM jobs WHERE 1=1"
        params: list = []
        if state: query += " AND state = ?"; params.append(state)
        if binder: query += " AND binder = ?"; params.append(binder)
        query += " ORDER BY created DESC LIMIT ?"; params.append(limit)
        return [ResearchJob(r).to_dict() for r in
                self._conn.execute(query, params).fetchall()]

    async def process_next(self) -> dict | None:
        """Process next pending job: scrape → summarise → save to binder."""
        row = self._conn.execute(
            "SELECT * FROM jobs WHERE state='pending' ORDER BY created ASC LIMIT 1"
        ).fetchone()
        if row is None:
            return None
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
                        raise Exception(f"HTTP {resp.status}")
                    html = await resp.text(errors="replace")
            from app.api.chat import _html_body_text, _html_desc, _html_title
            title = _html_title(html, job.url)
            description = _html_desc(html)
            text = _html_body_text(html)
            await self.update_state(job.id, "summarising", progress=40)
        except Exception as e:
            await self.update_state(job.id, "failed", error=str(e))
            return self._refetch(job.id)

        # Phase 2: Summarise via ChatUI
        try:
            from app.api.chat import get_router
            router = get_router()
            prompt = (
                f"Summarise concisely. Include key points, main argument, "
                f"and 3-5 suggested tags with # prefix. Use markdown.\n\n"
                f"Title: {title}\n\n{text[:4000]}"
            )
            sr = await router.chat(
                messages=[{"role": "user", "content": prompt}],
                model="ollama/qwen2.5-coder:3b", temperature=0.3,
            )
            summary = sr.get("content", description)
            await self.update_state(job.id, "saving", progress=70)
        except Exception:
            summary = f"## {title}\n\n{description}\n\n*Source: [{job.url}]({job.url})*"

        # Phase 3: Save to vault binder
        try:
            vault_dir = Path.home() / "Vault" / job.binder
            vault_dir.mkdir(parents=True, exist_ok=True)
            safe = "".join(c for c in title if c.isalnum() or c in " _-")[:80]
            safe = safe.strip().replace(" ", "-") or "untitled"
            fp = vault_dir / f"{safe}.md"
            now = datetime.now(UTC).strftime("%Y-%m-%d %H:%M")
            fp.write_text(
                f"# {title}\n\n> Source: [{job.url}]({job.url})\n"
                f"> Scraped: {now}\n> Tags: {' '.join(job.tags)}\n\n{summary}\n",
                encoding="utf-8",
            )
            # Update CITATIONS.md
            cp = vault_dir / "CITATIONS.md"
            cit = f"- [{title}]({job.url}) — accessed {now}\n"
            if cp.exists():
                ex = cp.read_text()
                if cit not in ex:
                    cp.write_text(ex + cit)
            else:
                cp.write_text(f"# Citations\n\n{cit}")
            result = json.dumps({"file": str(fp), "title": title, "binder": job.binder})
            # Auto-score: token count + source quality → 0-5
            auto_score = min(5, round((len(summary) / 500) + (1 if description else 0), 1))
            self._conn.execute(
                "UPDATE jobs SET result=json_set(COALESCE(result,'{}'),'$.score',?) WHERE id=?",
                (auto_score, job.id),
            )
            self._conn.commit()
            await self.update_state(job.id, "completed", progress=100, result=result)
        except Exception as e:
            await self.update_state(job.id, "failed", error=f"Save error: {e}")

        return self._refetch(job.id)

    def _refetch(self, job_id):
        row = self._conn.execute("SELECT * FROM jobs WHERE id=?", (job_id,)).fetchone()
        return ResearchJob(row).to_dict() if row else None
