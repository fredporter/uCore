"""Activity Markdown View Generator with Anti-Drift User Annotation Protection.

Complies with UDOS_PRODUCT_REFACTOR_PLAN_2026-09-12 Section 10:
- Formats ~/Vault/Activity/Daily_Activity.md from ~/Vault/Activity/events.jsonl.
- Preserves user notes in the <!-- BEGIN USER ANNOTATIONS --> block across refreshes.
"""
from __future__ import annotations

import json
import logging
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

log = logging.getLogger("ucore.activity_markdown")

VAULT_ROOT = Path.home() / "Vault"
ACTIVITY_DIR = VAULT_ROOT / "Activity"
EVENTS_FILE = ACTIVITY_DIR / "events.jsonl"
DAILY_ACTIVITY_FILE = ACTIVITY_DIR / "Daily_Activity.md"


def get_activity_dir() -> Path:
    ACTIVITY_DIR.mkdir(parents=True, exist_ok=True)
    return ACTIVITY_DIR


def append_activity_events(
    events: List[Dict[str, Any]],
    activity_dir: Optional[Path] = None,
) -> int:
    """Append new activity events to events.jsonl with deduplication against existing external_ids."""
    act_dir = activity_dir or get_activity_dir()
    events_file = act_dir / "events.jsonl"

    existing_ids = set()
    if events_file.is_file():
        try:
            for line in events_file.read_text(encoding="utf-8").splitlines():
                if line.strip():
                    item = json.loads(line)
                    if "external_id" in item:
                        existing_ids.add(item["external_id"])
        except Exception as exc:
            log.warning("Failed reading existing events: %s", exc)

    new_events = []
    now_iso = datetime.now(UTC).isoformat()
    for ev in events:
        ext_id = ev.get("external_id")
        if ext_id and ext_id not in existing_ids:
            if "captured_at" not in ev:
                ev["captured_at"] = now_iso
            if "privacy" not in ev:
                ev["privacy"] = "private"
            new_events.append(ev)
            existing_ids.add(ext_id)

    if new_events:
        with open(events_file, "a", encoding="utf-8") as f:
            for ev in new_events:
                f.write(json.dumps(ev) + "\n")

    return len(new_events)


def update_daily_activity_markdown(
    activity_dir: Optional[Path] = None,
) -> str:
    """Render Daily_Activity.md preserving user annotations."""
    act_dir = activity_dir or get_activity_dir()
    events_file = act_dir / "events.jsonl"
    md_file = act_dir / "Daily_Activity.md"

    user_annotations = ""
    if md_file.is_file():
        try:
            content = md_file.read_text(encoding="utf-8")
            if "<!-- BEGIN USER ANNOTATIONS -->" in content and "<!-- END USER ANNOTATIONS -->" in content:
                parts = content.split("<!-- BEGIN USER ANNOTATIONS -->")
                if len(parts) > 1:
                    subparts = parts[1].split("<!-- END USER ANNOTATIONS -->")
                    user_annotations = subparts[0].strip()
        except Exception:
            pass

    if not user_annotations:
        user_annotations = "- Add custom priorities, reflections, and follow-ups here.\n- This block is preserved across all automatic activity refreshes."

    # Read events
    events: List[Dict[str, Any]] = []
    if events_file.is_file():
        try:
            for line in events_file.read_text(encoding="utf-8").splitlines():
                if line.strip():
                    events.append(json.loads(line))
        except Exception:
            pass

    events.sort(key=lambda x: x.get("timestamp", ""), reverse=True)
    recent_events = events[:50]

    generated_lines = [
        f"> *Last synchronized: {datetime.now(UTC).strftime('%Y-%m-%d %H:%M:%S UTC')}* · *Total records: {len(events)}*\n",
    ]

    by_source: Dict[str, List[Dict[str, Any]]] = {}
    for ev in recent_events:
        src = ev.get("source", "other")
        by_source.setdefault(src, []).append(ev)

    sections = [
        ("Calendar Events", "calendar"),
        ("Reminders & Tasks", "reminders"),
        ("Unread Mail", "mail"),
        ("Recent Notes", "notes"),
    ]

    for title, key in sections:
        items = by_source.get(key, [])
        generated_lines.append(f"### {title} ({len(items)})")
        if not items:
            generated_lines.append("_No items recorded._\n")
        else:
            for it in items:
                t = it.get("timestamp", "")[:16].replace("T", " ")
                generated_lines.append(f"- **{it.get('title')}** ({t})")
                snippet = it.get("content", "").strip().split("\n")[0]
                if snippet:
                    generated_lines.append(f"  > {snippet[:120]}")
            generated_lines.append("")

    generated_body = "\n".join(generated_lines)

    document = f"""# Daily Activity & Host PIM Feed

<!-- BEGIN GENERATED ACTIVITY -->
{generated_body}
<!-- END GENERATED ACTIVITY -->

## Personal Annotations & Review Notes
<!-- BEGIN USER ANNOTATIONS -->
{user_annotations}
<!-- END USER ANNOTATIONS -->
"""
    md_file.write_text(document, encoding="utf-8")
    return document
