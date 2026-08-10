"""brain_sync — Synthesize recent project memory into private wisdom.

Builds a lightweight local "Brain" layer by reviewing recent project files,
spool logs, and AppFlowy activity, then refreshing private wisdom with durable
lessons, recent change summaries, and spool activity analysis.

Also provides tasker/devlog bridge actions (sync, read, write, archive, purge)
merged from the former tasker_devlog_bridge skill.

Usage:
  POST /api/skills/brain_sync/run
    Body: {
        "action": "sync" | "read" | "write" | "archive" | "purge" | "summarize",
        "hours": 24,
        "limit": 12,
        "include_spool": true,
        "include_appflowy": true,
        "include_test_failures": true,
        "tasker_dir": ".tasker",
        "devlog_file": "devlog.mcp.yaml",
        "content": "",
        "max_age_days": 7,
        "dry_run": false
    }
"""
from __future__ import annotations

import json
import re
from datetime import UTC, datetime, timedelta
from pathlib import Path
from xml.etree import ElementTree

from app.services.episodic_store import summarize_entries as summarize_episodic
from app.services.spool_reader import read_spool, summarize_spool
from app.services.wisdom_paths import (
    PROJECT_ROOT,
    readable_wisdom_path,
    writable_wisdom_path,
)
from app.skills.base import BaseSkill, SkillMeta, SkillParam

WISDOM_PATH = writable_wisdom_path()
DEFAULT_SCAN_DIRS = ("backend", "docs", "frontend", "scripts", ".tasker")
DEFAULT_TASKER_DIR = PROJECT_ROOT / ".tasker"
DEFAULT_DEVLOG_FILE = PROJECT_ROOT / "devlog.mcp.yaml"
TEST_REPORT_PATTERNS = (
    "**/junit*.xml",
    "**/pytest*.xml",
    "**/test-results*.xml",
)
PYTEST_CACHE_FILES: tuple[Path, ...] = (
    PROJECT_ROOT / ".pytest_cache" / "v" / "cache" / "lastfailed",
    PROJECT_ROOT / "backend" / ".pytest_cache" / "v" / "cache" / "lastfailed",
)


class BrainSync(BaseSkill):
    meta = SkillMeta(
        id="brain_sync",
        name="Brain Sync",
        description=(
            "Synthesize recent project changes, spool activity, and "
            "AppFlowy events into private wisdom. Also provides "
            "tasker/devlog bridge actions (sync, read, write, archive, purge)."
        ),
        category="assist",
        timeout=30,
        params=[
            SkillParam(
                name="action",
                type="string",
                required=False,
                default="summarize",
                description="Action: summarize, sync, read, write, archive, purge",
            ),
            SkillParam(
                name="hours",
                type="integer",
                required=False,
                default=24,
                description="How many recent hours to scan for changes",
            ),
            SkillParam(
                name="limit",
                type="integer",
                required=False,
                default=12,
                description="Maximum number of recent files to summarize",
            ),
            SkillParam(
                name="include_spool",
                type="boolean",
                required=False,
                default=True,
                description="Include spool activity summary in private wisdom",
            ),
            SkillParam(
                name="include_appflowy",
                type="boolean",
                required=False,
                default=True,
                description=(
                    "Include AppFlowy activity summary in private wisdom"
                ),
            ),
            SkillParam(
                name="include_test_failures",
                type="boolean",
                required=False,
                default=True,
                description=(
                    "Include recent test failure signals in private wisdom"
                ),
            ),
            SkillParam(
                name="include_episodic",
                type="boolean",
                required=False,
                default=True,
                description=(
                    "Include recent episodic log entries in private wisdom"
                ),
            ),
            SkillParam(
                name="tasker_dir",
                type="string",
                required=False,
                default=str(DEFAULT_TASKER_DIR),
                description="Path to .tasker directory (for sync/read/write/archive)",
            ),
            SkillParam(
                name="devlog_file",
                type="string",
                required=False,
                default=str(DEFAULT_DEVLOG_FILE),
                description="Path to devlog.mcp.yaml (for sync/read/write)",
            ),
            SkillParam(
                name="content",
                type="string",
                required=False,
                default="",
                description="Content to write to devlog (for write action)",
            ),
            SkillParam(
                name="max_age_days",
                type="integer",
                required=False,
                default=7,
                description="Days before archiving old tasks (for archive action)",
            ),
            SkillParam(
                name="dry_run",
                type="boolean",
                required=False,
                default=False,
                description="Preview without writing changes",
            ),
        ],
        requires_confirmation=True,
    )

    async def run(self, **kwargs) -> dict:
        action = str(kwargs.get("action", "summarize")).strip().lower()

        if action == "sync":
            return await self._sync_tasker_devlog(**kwargs)
        elif action == "read":
            return self._read_tasker_devlog(**kwargs)
        elif action == "write":
            return self._write_devlog(**kwargs)
        elif action == "archive":
            return self._archive_old_tasks(**kwargs)
        elif action == "purge":
            return self._purge_legacy_docs(**kwargs)

        # Default: summarize (original brain_sync behavior)
        return await self._summarize(**kwargs)

    async def _summarize(self, **kwargs) -> dict:
        """Original brain_sync: synthesize project memory into private wisdom."""
        hours = max(1, int(kwargs.get("hours", 24)))
        limit = max(1, int(kwargs.get("limit", 12)))
        include_spool = bool(kwargs.get("include_spool", True))
        include_appflowy = bool(kwargs.get("include_appflowy", True))
        include_test_failures = bool(kwargs.get("include_test_failures", True))
        include_episodic = bool(kwargs.get("include_episodic", True))
        cutoff = datetime.now(UTC) - timedelta(hours=hours)

        recent_files = self._collect_recent_files(cutoff=cutoff, limit=limit)
        existing_sections = self._load_existing_sections()
        spool_summary = summarize_spool(hours=hours) if include_spool else None
        appflowy_summary = (
            self._get_appflowy_activity(hours=hours)
            if include_appflowy
            else None
        )
        test_failures = (
            self._collect_test_failures(cutoff=cutoff, limit=10)
            if include_test_failures
            else []
        )
        episodic_summary = (
            summarize_episodic(hours=hours)
            if include_episodic
            else None
        )

        refreshed = self._render_wisdom(
            recent_files=recent_files,
            existing_sections=existing_sections,
            spool_summary=spool_summary,
            appflowy_summary=appflowy_summary,
            test_failures=test_failures,
            episodic_summary=episodic_summary,
            hours=hours,
        )
        wisdom_path = WISDOM_PATH
        wisdom_path.parent.mkdir(parents=True, exist_ok=True)
        wisdom_path.write_text(refreshed, encoding="utf-8")

        return {
            "success": True,
            "action": "summarize",
            "hours": hours,
            "limit": limit,
            "include_spool": include_spool,
            "include_appflowy": include_appflowy,
            "include_test_failures": include_test_failures,
            "wisdom_path": str(wisdom_path),
            "recent_files": [
                str(path.relative_to(PROJECT_ROOT))
                for path in recent_files
            ],
            "count": len(recent_files),
            "spool_included": spool_summary is not None,
            "appflowy_included": appflowy_summary is not None,
            "test_failures_included": bool(test_failures),
            "test_failure_count": len(test_failures),
            "episodic_included": episodic_summary is not None,
        }

    # ─── Tasker/Devlog Bridge Actions (merged from tasker_devlog_bridge) ──

    async def _sync_tasker_devlog(self, **kwargs) -> dict:
        """Sync .tasker with devlog.mcp.yaml and spool activity."""
        tasker_dir = Path(kwargs.get("tasker_dir", DEFAULT_TASKER_DIR)).expanduser()
        devlog_file = Path(kwargs.get("devlog_file", DEFAULT_DEVLOG_FILE)).expanduser()
        hours = int(kwargs.get("hours", 24))
        dry_run = bool(kwargs.get("dry_run", False))

        completed_tasks = self._collect_completed_tasks(tasker_dir)
        cutoff = (datetime.now(UTC) - timedelta(hours=hours)).isoformat()
        spool_entries = read_spool(since=cutoff)

        devlog_content = self._render_devlog(
            completed_tasks=completed_tasks,
            spool_entries=spool_entries,
            hours=hours,
        )

        if not dry_run:
            devlog_file.parent.mkdir(parents=True, exist_ok=True)
            devlog_file.write_text(devlog_content, encoding="utf-8")

        return {
            "success": True,
            "action": "sync",
            "devlog_path": str(devlog_file),
            "completed_tasks": len(completed_tasks),
            "spool_entries": len(spool_entries),
            "hours": hours,
            "dry_run": dry_run,
        }

    def _read_tasker_devlog(self, **kwargs) -> dict:
        """Read current state of tasker and devlog."""
        tasker_dir = Path(kwargs.get("tasker_dir", DEFAULT_TASKER_DIR)).expanduser()
        devlog_file = Path(kwargs.get("devlog_file", DEFAULT_DEVLOG_FILE)).expanduser()

        tasks = []
        if tasker_dir.exists():
            for task_file in tasker_dir.rglob("*.md"):
                if task_file.name == "README.md":
                    continue
                try:
                    content = task_file.read_text(encoding="utf-8")
                    tasks.append({
                        "path": str(task_file.relative_to(tasker_dir.parent)),
                        "content": content[:500],
                    })
                except Exception:
                    continue

        devlog_content = ""
        if devlog_file.exists():
            devlog_content = devlog_file.read_text(encoding="utf-8")

        return {
            "success": True,
            "action": "read",
            "tasks": tasks,
            "devlog_preview": devlog_content[:1000] if devlog_content else None,
        }

    def _write_devlog(self, **kwargs) -> dict:
        """Write content to devlog.mcp.yaml."""
        devlog_file = Path(kwargs.get("devlog_file", DEFAULT_DEVLOG_FILE)).expanduser()
        content = kwargs.get("content", "")
        dry_run = bool(kwargs.get("dry_run", False))

        if not dry_run:
            devlog_file.parent.mkdir(parents=True, exist_ok=True)
            devlog_file.write_text(content, encoding="utf-8")

        return {
            "success": True,
            "action": "write",
            "devlog_path": str(devlog_file),
            "dry_run": dry_run,
        }

    def _archive_old_tasks(self, **kwargs) -> dict:
        """Archive completed tasks older than max_age_days."""
        tasker_dir = Path(kwargs.get("tasker_dir", DEFAULT_TASKER_DIR)).expanduser()
        max_age_days = int(kwargs.get("max_age_days", 7))
        dry_run = bool(kwargs.get("dry_run", False))

        archived_dir = tasker_dir.parent / ".tasker.archived"
        archived_count = 0

        if not tasker_dir.exists():
            return {"success": True, "action": "archive", "archived": 0, "dry_run": dry_run}

        cutoff = datetime.now(UTC) - timedelta(days=max_age_days)

        for task_file in tasker_dir.rglob("*.md"):
            if task_file.name == "README.md":
                continue
            try:
                content = task_file.read_text(encoding="utf-8")
                if "status: done" in content or "status: completed" in content:
                    mtime = datetime.fromtimestamp(task_file.stat().st_mtime, tz=UTC)
                    if mtime < cutoff:
                        relative = task_file.relative_to(tasker_dir)
                        dest = archived_dir / relative
                        if not dry_run:
                            dest.parent.mkdir(parents=True, exist_ok=True)
                            dest.write_text(content, encoding="utf-8")
                            task_file.unlink(missing_ok=True)
                        archived_count += 1
            except Exception:
                continue

        return {
            "success": True,
            "action": "archive",
            "archived": archived_count,
            "dry_run": dry_run,
        }

    def _purge_legacy_docs(self, **kwargs) -> dict:
        """Purge legacy completed documentation reports."""
        docs_dir = Path(kwargs.get("docs_dir", PROJECT_ROOT / "docs"))
        dry_run = bool(kwargs.get("dry_run", False))

        purged = []
        legacy_patterns = [
            r"COMPLETE.*\.md$",
            r"DONE.*\.md$",
            r"REPORT_.*\.md$",
            r"CHECKLIST.*\.md$",
        ]

        if not docs_dir.exists():
            return {"success": True, "action": "purge", "purged": [], "dry_run": dry_run}

        for doc_file in docs_dir.rglob("*.md"):
            for pattern in legacy_patterns:
                if re.search(pattern, doc_file.name, re.IGNORECASE):
                    if not dry_run:
                        doc_file.unlink(missing_ok=True)
                    purged.append(str(doc_file.relative_to(docs_dir.parent)))
                    break

        return {
            "success": True,
            "action": "purge",
            "purged": purged,
            "dry_run": dry_run,
        }

    def _collect_completed_tasks(self, tasker_dir: Path) -> list[dict[str, Any]]:
        """Collect completed tasks from .tasker directory."""
        tasks = []
        if not tasker_dir.exists():
            return tasks

        for task_file in tasker_dir.rglob("*.md"):
            if task_file.name == "README.md":
                continue
            try:
                content = task_file.read_text(encoding="utf-8")
                if "status: done" in content or "status: completed" in content:
                    task_info = self._parse_task_file(task_file, content)
                    tasks.append(task_info)
            except Exception:
                continue

        return tasks

    def _parse_task_file(self, path: Path, content: str) -> dict[str, Any]:
        """Parse task file to extract metadata."""
        lines = content.split("\n")
        title = lines[0].replace("#", "").strip() if lines else path.stem

        status = "done"
        for line in lines[:20]:
            if line.startswith("- status:"):
                status = line.split(":", 1)[1].strip()
                break

        return {
            "file": str(path.relative_to(path.parent.parent)),
            "archived": True,
            "title": title,
            "status": status,
        }

    def _render_devlog(
        self,
        completed_tasks: list[dict[str, Any]],
        spool_entries: list[dict[str, Any]],
        hours: int,
    ) -> str:
        """Render MCP-formatted devlog."""
        lines = [
            f"# Devlog MCP — Generated: {datetime.now(UTC).isoformat()}",
            "",
            'version: "1.0.0"',
            'generated_by: "brain_sync"',
            f"hours: {hours}",
            f"completed_tasks: {len(completed_tasks)}",
            f"spool_entries: {len(spool_entries)}",
            "",
            "## Completed Tasks",
        ]

        for task in completed_tasks:
            lines.append(f"- file: {task['file']}")
            lines.append(f"  archived: {task['archived']}")
            lines.append("")

        lines.append("## Spool Activity")
        for entry in spool_entries[-50:]:
            lines.append(f"- timestamp: {entry.get('timestamp', 'unknown')}")
            lines.append(f"  level: {entry.get('level', 'INFO')}")
            lines.append(f"  module: {entry.get('module', 'unknown')}")
            lines.append(f"  message: {entry.get('message', '')}")
            lines.append("")

        return "\n".join(lines)

    def _collect_recent_files(
        self,
        cutoff: datetime,
        limit: int,
    ) -> list[Path]:
        matches: list[tuple[float, Path]] = []
        for name in DEFAULT_SCAN_DIRS:
            base = PROJECT_ROOT / name
            if not base.exists():
                continue
            for path in base.rglob("*"):
                if not path.is_file():
                    continue
                if path.name.startswith("."):
                    continue
                if "/__pycache__/" in str(path):
                    continue
                if path.suffix in {".pyc", ".log"}:
                    continue
                modified = datetime.fromtimestamp(
                    path.stat().st_mtime,
                    tz=UTC,
                )
                if modified >= cutoff:
                    matches.append((path.stat().st_mtime, path))
        matches.sort(key=lambda item: item[0], reverse=True)
        return [path for _, path in matches[:limit]]

    def _load_existing_sections(self) -> list[str]:
        wisdom_path = (
            WISDOM_PATH if WISDOM_PATH.exists() else readable_wisdom_path()
        )
        if not wisdom_path.exists():
            return []
        lines = wisdom_path.read_text(encoding="utf-8").splitlines()
        durable: list[str] = []
        in_durable = False
        for line in lines:
            if line.strip() == "## Durable Lessons":
                in_durable = True
                continue
            if line.startswith("## ") and line.strip() != "## Durable Lessons":
                in_durable = False
            if in_durable and line.strip().startswith("- "):
                durable.append(line.strip())
        return durable

    def _get_appflowy_activity(self, *, hours: int) -> str | None:
        """Check AppFlowy local DB for recent activity."""
        try:
            from app.knowledge.local_first import discover_databases, run_query

            dbs = discover_databases()
            db_path = dbs.get("database")
            if not db_path:
                return None

            result = run_query(
                db_path=db_path,
                sql="SELECT name, COUNT(*) as updates FROM row_table "
                    "WHERE updated_at >= datetime('now', ?) "
                    "GROUP BY name ORDER BY updates DESC LIMIT 10",
                params=[f"-{hours} hours"],
                write=False,
            )
            rows = result.get("rows", [])
            if not rows:
                return f"No AppFlowy activity in the last {hours}h."
            lines = [
                f"- {row.get('name', 'unknown')}: "
                f"{row.get('updates', 0)} updates"
                for row in rows
            ]
            return "\n".join(lines)
        except Exception:
            return None

    def _collect_test_failures(
        self,
        *,
        cutoff: datetime,
        limit: int,
    ) -> list[str]:
        items: list[str] = []
        seen: set[str] = set()

        def _push(prefix: str, detail: str) -> None:
            normalized = f"{prefix}: {detail.strip()}"
            if not detail.strip() or normalized in seen:
                return
            seen.add(normalized)
            items.append(normalized)

        for cache_path in PYTEST_CACHE_FILES:
            if not cache_path.exists():
                continue
            try:
                payload = json.loads(cache_path.read_text(encoding="utf-8"))
            except Exception:
                continue
            if not isinstance(payload, dict):
                continue
            for node_id, failed in payload.items():
                if bool(failed):
                    _push("pytest-cache", str(node_id))

        for pattern in TEST_REPORT_PATTERNS:
            for report in PROJECT_ROOT.glob(pattern):
                if not report.is_file():
                    continue
                modified = datetime.fromtimestamp(
                    report.stat().st_mtime,
                    tz=UTC,
                )
                if modified < cutoff:
                    continue
                try:
                    root = ElementTree.parse(report).getroot()
                except Exception:
                    continue
                for case in root.iter("testcase"):
                    failure = case.find("failure")
                    error = case.find("error")
                    node = failure or error
                    if node is None:
                        continue
                    class_name = case.attrib.get("classname", "").strip()
                    case_name = case.attrib.get("name", "unknown").strip()
                    test_id = (
                        f"{class_name}::{case_name}"
                        if class_name
                        else case_name
                    )
                    message = (
                        (node.attrib.get("message") or (node.text or ""))
                        .strip()
                        .replace("\n", " ")
                    )
                    if message:
                        detail = f"{test_id} - {message[:140]}"
                    else:
                        detail = test_id
                    _push(f"junit:{report.name}", detail)

        spool_since = cutoff.isoformat()
        spool_entries = read_spool(
            max_entries=500,
            since=spool_since,
            search="pytest",
        )
        for entry in spool_entries:
            msg = entry.message.strip().lower()
            if (
                entry.is_error
                or "failed" in msg
                or "traceback" in msg
                or "assert" in msg
            ):
                _push(f"spool:{entry.module}", entry.message[:180])

        return items[:limit]

    def _render_wisdom(
        self,
        *,
        recent_files: list[Path],
        existing_sections: list[str],
        spool_summary: str | None = None,
        appflowy_summary: str | None = None,
        test_failures: list[str] | None = None,
        episodic_summary: str | None = None,
        hours: int = 24,
    ) -> str:
        now = datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")
        recent_lines = [
            f"- {path.relative_to(PROJECT_ROOT)}" for path in recent_files
        ] or ["- No files changed in the selected window."]
        durable = existing_sections or [
            "- Keep one canonical implementation path per subsystem.",
            "- Favor local-first operation and explicit documented "
            "orchestration.",
        ]

        parts = [
            "# uCore Wisdom",
            "",
            f"Date: {now}",
            "Status: Refreshed by brain_sync",
            "",
            "## Durable Lessons",
            *durable,
            "",
            "## Recent Change Scan",
            *recent_lines,
            "",
            "## Memory Architecture",
            "- Short-term: active AI/chat session context.",
            "- Long-term: AppFlowy, vault, and canonical docs.",
            "- Episodic: private wisdom, spool logs, and recent change "
            "summaries.",
            "",
            "## Synthesis Inputs",
            f"- Window: last {hours}h",
            "- Spool summary: "
            f"{'included' if spool_summary else 'not included'}",
            "- AppFlowy activity: "
            f"{'included' if appflowy_summary else 'not included'}",
            f"- Test failures: {len(test_failures or [])} signals",
            "- Episodic log: "
            f"{'included' if episodic_summary else 'not included'}",
            "",
            "## Next Synthesis Targets",
            "- Migration checklist status and canonical doc destinations.",
            "- Snackbar/system orchestration refinements and tray workflows.",
            "- UI view wiring across frontend surfaces and system pages.",
            "- DocLang-style structured export for AI-efficient "
            "document context.",
        ]

        if spool_summary:
            parts.extend(["", spool_summary])

        if appflowy_summary:
            parts.extend([
                "",
                f"## AppFlowy Activity (last {hours}h)",
                "",
                appflowy_summary,
            ])

        if test_failures:
            parts.extend([
                "",
                f"## Test Failure Signals (last {hours}h)",
                "",
            ])
            parts.extend([f"- {item}" for item in test_failures])

        if episodic_summary:
            parts.extend(["", episodic_summary])

        parts.append("")
        return "\n".join(parts)
