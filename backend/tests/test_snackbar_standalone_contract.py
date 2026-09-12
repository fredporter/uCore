"""Tests for Snackbar Standalone Contract & Apple Activity (Milestone P6).

Verifies:
1. Launcher discovery filters absent products by default.
2. Activity events appending and deduplication against external IDs.
3. Daily activity markdown rendering preserves user annotations between <!-- BEGIN/END USER ANNOTATIONS -->.
4. Snackbar launchers API endpoint returns present launchers.
"""
from __future__ import annotations

import json
from pathlib import Path
from aiohttp import web
from aiohttp.test_utils import AioHTTPTestCase
import pytest

from app.services.activity_markdown import (
    append_activity_events,
    update_daily_activity_markdown,
)
from app.snackbar.modules.launchers import (
    get_active_launchers,
    handle_get_activity,
    handle_list_launchers,
    handle_sync_activity,
)


def test_launcher_discovery_hides_absent(tmp_path):
    launchers = get_active_launchers(include_absent=False)
    # Every item returned must be installed
    for item in launchers:
        assert item["installed"] is True
        assert item["id"] in ("obsidian", "ucore", "ucode", "ucode2", "udos-publishing",
                              "homenest", "uvector", "groovebox", "sonicscrewdriver",
                              "snackmachine", "apple-notes", "apple-reminders", "apple-calendar", "apple-mail")

    all_items = get_active_launchers(include_absent=True)
    assert len(all_items) >= len(launchers)


def test_activity_markdown_preserves_annotations(tmp_path):
    act_dir = tmp_path / "Activity"
    act_dir.mkdir(parents=True, exist_ok=True)

    events = [
        {
            "external_id": "cal-100",
            "source": "calendar",
            "title": "Release Milestone P6",
            "content": "Verify clean launcher contract",
            "timestamp": "2026-09-13T10:00:00Z",
        },
        {
            "external_id": "rem-200",
            "source": "reminders",
            "title": "Clean up dead repos",
            "content": "Confirm satellites merged",
            "timestamp": "2026-09-13T11:00:00Z",
        }
    ]

    count = append_activity_events(events, activity_dir=act_dir)
    assert count == 2

    # Duplicate appending is ignored
    dup_count = append_activity_events(events, activity_dir=act_dir)
    assert dup_count == 0

    # Render initial markdown view
    md_text = update_daily_activity_markdown(activity_dir=act_dir)
    assert "Release Milestone P6" in md_text
    assert "<!-- BEGIN USER ANNOTATIONS -->" in md_text

    # User adds custom notes
    user_notes = "- Prioritize offline local bundle verification.\n- Schedule sync for Monday morning."
    custom_md = md_text.replace(
        "- Add custom priorities, reflections, and follow-ups here.\n- This block is preserved across all automatic activity refreshes.",
        user_notes
    )
    (act_dir / "Daily_Activity.md").write_text(custom_md, encoding="utf-8")

    # Add a 3rd event and refresh markdown
    append_activity_events([{
        "external_id": "mail-300",
        "source": "mail",
        "title": "Build Confirmation",
        "content": "CI pipeline succeeded",
        "timestamp": "2026-09-13T12:00:00Z",
    }], activity_dir=act_dir)

    refreshed_md = update_daily_activity_markdown(activity_dir=act_dir)
    assert "Build Confirmation" in refreshed_md
    assert user_notes in refreshed_md, "User annotations must be preserved across refreshes"


class SnackbarLauncherAPITest(AioHTTPTestCase):
    async def get_application(self):
        app = web.Application()
        app.router.add_get("/api/snackbar/launchers", handle_list_launchers)
        app.router.add_get("/api/snackbar/activity", handle_get_activity)
        return app

    async def test_get_launchers_endpoint(self):
        resp = await self.client.get("/api/snackbar/launchers")
        assert resp.status == 200
        data = await resp.json()
        assert "launchers" in data
        assert data["absent_hidden"] is True
        for item in data["launchers"]:
            assert item["installed"] is True
