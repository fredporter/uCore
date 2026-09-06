from __future__ import annotations

import json
from unittest.mock import AsyncMock, MagicMock

import pytest
from aiohttp import web

from app.api.host_api import (
    get_host_pim_service,
    handle_host_capabilities,
    handle_host_notify,
    handle_host_say,
    handle_notes_export,
    handle_reminders_export,
    handle_safari_active,
    handle_safari_intake,
    set_host_pim_service,
)
from app.services.host_pim import HostPIMService, markdown_to_html


def test_markdown_to_html():
    md = "# Title\n\n## Subtitle\n\n- item 1\n- **bold item**\n\n```python\nprint('hello')\n```\n\nA regular paragraph with `code`."
    rendered = markdown_to_html(md)

    assert "<h1>Title</h1>" in rendered
    assert "<h2>Subtitle</h2>" in rendered
    assert "<li>item 1</li>" in rendered
    assert "<li><strong>bold item</strong></li>" in rendered
    assert "<pre><code>print(&#x27;hello&#x27;)</code></pre>" in rendered
    assert "<p>A regular paragraph with <code>code</code>.</p>" in rendered


def test_probe_capabilities_macos(monkeypatch):
    commands_run = []

    def mock_runner(cmd: list[str], timeout: float = 10.0) -> str:
        commands_run.append(cmd)
        if "Safari" in cmd[-1]:
            return "com.apple.Safari"
        if "Notes" in cmd[-1]:
            return "com.apple.Notes"
        if "Reminders" in cmd[-1]:
            return "com.apple.reminders"
        if "Mail" in cmd[-1]:
            return "com.apple.mail"
        if "Messages" in cmd[-1]:
            return "com.apple.MobileSMS"
        return ""

    svc = HostPIMService(runner=mock_runner)
    monkeypatch.setattr(svc, "is_macos", lambda: True)
    monkeypatch.setattr("platform.system", lambda: "Darwin")
    monkeypatch.setattr("shutil.which", lambda prog: f"/usr/bin/{prog}")

    caps = svc.probe_capabilities()

    assert caps["os"] == "darwin"
    assert caps["host_native"]["safari"]["available"] is True
    assert caps["host_native"]["safari"]["bundle_id"] == "com.apple.Safari"
    assert caps["host_native"]["notes"]["available"] is True
    assert caps["capabilities"]["browser_intake"] is True
    assert caps["capabilities"]["notes_export"] is True
    assert caps["capabilities"]["reminders_export"] is True
    assert caps["capabilities"]["notifications"] is True
    assert caps["capabilities"]["speech_tts"] is True


def test_safari_active_tab():
    def mock_runner(cmd: list[str], timeout: float = 10.0) -> str:
        return json.dumps({
            "ok": True,
            "running": True,
            "url": "https://developer.apple.com/documentation",
            "title": "Apple Developer Documentation",
        })

    svc = HostPIMService(runner=mock_runner)
    tab = svc.get_active_safari_tab()

    assert tab["ok"] is True
    assert tab["running"] is True
    assert tab["url"] == "https://developer.apple.com/documentation"
    assert tab["title"] == "Apple Developer Documentation"


def test_safari_intake_to_research():
    def mock_runner(cmd: list[str], timeout: float = 10.0) -> str:
        return json.dumps({
            "ok": True,
            "running": True,
            "url": "https://news.ycombinator.com",
            "title": "Hacker News",
        })

    svc = HostPIMService(runner=mock_runner)
    res = svc.intake_safari_to_research(notes="Interesting read")

    assert res["ok"] is True
    assert res["url"] == "https://news.ycombinator.com"
    assert res["title"] == "Hacker News"
    assert "card" in res
    assert res["card"]["source"] == "safari"
    assert res["card"]["notes"] == "Interesting read"


def test_export_to_apple_notes():
    executed_scripts = []

    def mock_runner(cmd: list[str], timeout: float = 10.0) -> str:
        executed_scripts.append(cmd)
        return "note id 123"

    svc = HostPIMService(runner=mock_runner)
    res = svc.export_to_apple_notes(
        title="Sprint 4 Brief",
        body_markdown="# Architecture\n\n- Task 1\n- Task 2",
        folder="Work",
    )

    assert res["ok"] is True
    assert res["title"] == "Sprint 4 Brief"
    assert res["folder"] == "Work"
    assert len(executed_scripts) == 1
    assert 'tell application "Notes"' in executed_scripts[0][-1]
    assert 'folder "Work"' in executed_scripts[0][-1]


def test_export_to_apple_reminders():
    executed_scripts = []

    def mock_runner(cmd: list[str], timeout: float = 10.0) -> str:
        executed_scripts.append(cmd)
        return "reminder id 456"

    svc = HostPIMService(runner=mock_runner)
    res = svc.export_to_apple_reminders(
        title="Review Zen Ecosystem Contract",
        notes="Check reuse hierarchy and storage boundary",
        list_name="Tasks",
    )

    assert res["ok"] is True
    assert res["title"] == "Review Zen Ecosystem Contract"
    assert res["list"] == "Tasks"
    assert len(executed_scripts) == 1
    assert 'tell application "Reminders"' in executed_scripts[0][-1]
    assert 'list "Tasks"' in executed_scripts[0][-1]


def test_notify_and_say(monkeypatch):
    executed = []

    def mock_runner(cmd: list[str], timeout: float = 10.0) -> str:
        executed.append(cmd)
        return ""

    svc = HostPIMService(runner=mock_runner)
    monkeypatch.setattr(svc, "is_macos", lambda: True)
    monkeypatch.setattr("shutil.which", lambda _: "/usr/bin/say")

    notif_res = svc.notify(title="Build Passed", message="Frontend 61 tests OK", subtitle="uDOS")
    assert notif_res["ok"] is True

    say_res = svc.say("All systems nominal", voice="Samantha")
    assert say_res["ok"] is True
    assert say_res["voice"] == "Samantha"

    assert len(executed) == 2
    assert "display notification" in executed[0][-1]
    assert executed[1] == ["say", "-v", "Samantha", "All systems nominal"]


@pytest.mark.asyncio
async def test_api_handlers():
    def mock_runner(cmd: list[str], timeout: float = 10.0) -> str:
        if "Safari" in str(cmd):
            return json.dumps({"ok": True, "running": True, "url": "https://example.com", "title": "Example"})
        return "ok"

    svc = HostPIMService(runner=mock_runner)
    set_host_pim_service(svc)

    # 1. capabilities
    req_caps = MagicMock(spec=web.Request)
    resp_caps = await handle_host_capabilities(req_caps)
    assert resp_caps.status == 200

    # 2. safari active
    req_safari = MagicMock(spec=web.Request)
    resp_safari = await handle_safari_active(req_safari)
    assert resp_safari.status == 200
    safari_data = json.loads(resp_safari.text)
    assert safari_data["url"] == "https://example.com"

    # 3. notes export
    req_notes = MagicMock(spec=web.Request)
    req_notes.json = AsyncMock(return_value={"title": "Test Note", "body": "Hello world"})
    resp_notes = await handle_notes_export(req_notes)
    assert resp_notes.status == 200
    notes_data = json.loads(resp_notes.text)
    assert notes_data["ok"] is True

    # 4. reminders export
    req_rem = MagicMock(spec=web.Request)
    req_rem.json = AsyncMock(return_value={"title": "Test Reminder", "notes": "Do something"})
    resp_rem = await handle_reminders_export(req_rem)
    assert resp_rem.status == 200
    rem_data = json.loads(resp_rem.text)
    assert rem_data["ok"] is True

    # 5. notify
    req_notif = MagicMock(spec=web.Request)
    req_notif.json = AsyncMock(return_value={"title": "Alert", "message": "Notice"})
    resp_notif = await handle_host_notify(req_notif)
    assert resp_notif.status == 200

    # 6. say
    req_say = MagicMock(spec=web.Request)
    req_say.json = AsyncMock(return_value={"text": "Speaking"})
    resp_say = await handle_host_say(req_say)
    assert resp_say.status == 200
