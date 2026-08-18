"""brain_sync — Synthesize recent project memory into private wisdom.

Builds a lightweight local "Brain" layer by reviewing recent project files,
spool logs, and vault activity, then refreshing private wisdom with durable
lessons, recent change summaries, and spool activity analysis.

Usage:
  POST /api/skills/brain_sync/run
    Body: {
        "action": "summarize" | "purge",
        "hours": 24,
        "limit": 12,
        "include_spool": true,
        "include_vault_activity": true,
        "include_test_failures": true,
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
DEFAULT_SCAN_DIRS = ("backend", "docs", "frontend", "scripts")
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
            "vault changes into private wisdom."
        ),
        category="assist",
        timeout=30,
        params=[
            SkillParam(
                name="action",
                type="string",
                required=False,
                default="summarize",
                description="Action: summarize or purge",
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
                name="include_vault_activity",
                type="boolean",
                required=False,
                default=True,
                description=(
                    "Include vault activity summary in private wisdom"
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

        if action == "purge":
            return self._purge_legacy_docs(**kwargs)

        # Default: summarize (original brain_sync behavior)
        return await self._summarize(**kwargs)

    async def _summarize(self, **kwargs) -> dict:
        """Original brain_sync: synthesize project memory into private wisdom."""
        hours = max(1, int(kwargs.get("hours", 24)))
        limit = max(1, int(kwargs.get("limit", 12)))
        include_spool = bool(kwargs.get("include_spool", True))
        include_vault_activity = bool(kwargs.get("include_vault_activity", True))
        include_test_failures = bool(kwargs.get("include_test_failures", True))
        include_episodic = bool(kwargs.get("include_episodic", True))
        cutoff = datetime.now(UTC) - timedelta(hours=hours)

        recent_files = self._collect_recent_files(cutoff=cutoff, limit=limit)
        existing_sections = self._load_existing_sections()
        spool_summary = summarize_spool(hours=hours) if include_spool else None
        vault_activity_summary = (
            self._get_vault_activity(hours=hours)
            if include_vault_activity
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
            vault_activity_summary=vault_activity_summary,
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
            "include_vault_activity": include_vault_activity,
            "include_test_failures": include_test_failures,
            "wisdom_path": str(wisdom_path),
            "recent_files": [
                str(path.relative_to(PROJECT_ROOT))
                for path in recent_files
            ],
            "count": len(recent_files),
            "spool_included": spool_summary is not None,
            "vault_activity_included": vault_activity_summary is not None,
            "test_failures_included": bool(test_failures),
            "test_failure_count": len(test_failures),
            "episodic_included": episodic_summary is not None,
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

    def _get_vault_activity(self, *, hours: int) -> str | None:
        """Summarize recently modified files across the vault layers."""
        cutoff = datetime.now(UTC) - timedelta(hours=hours)
        cutoff_ts = cutoff.timestamp()
        roots = [Path.home() / "Vault", Path.home() / "Shared", Path.home() / "Public"]
        recent: list[str] = []
        for root in roots:
            if not root.exists():
                continue
            for md in root.rglob("*.md"):
                if len(recent) >= 10:
                    break
                try:
                    if md.stat().st_mtime >= cutoff_ts:
                        recent.append(str(md))
                except Exception:
                    continue
        if not recent:
            return f"No vault changes in the last {hours}h."
        return "\n".join(f"- {p}" for p in recent)

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
        vault_activity_summary: str | None = None,
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
            "- Long-term: vault and canonical docs.",
            "- Episodic: private wisdom, spool logs, and recent change "
            "summaries.",
            "",
            "## Synthesis Inputs",
            f"- Window: last {hours}h",
            "- Spool summary: "
            f"{'included' if spool_summary else 'not included'}",
            "- Vault activity: "
            f"{'included' if vault_activity_summary else 'not included'}",
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

        if vault_activity_summary:
            parts.extend([
                "",
                f"## Vault Activity (last {hours}h)",
                "",
                vault_activity_summary,
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
