"""Host-native Personal Information Management (PIM) and OS automation service.

Adheres to the Zen Ecosystem Contract reuse hierarchy:
1. Host OS Native (macOS Apple Events / osascript; Linux Zen/Firefox / notify-send)
2. Ecosystem Service (uCore Feed / Spool / Binders)
3. Vendor Components
4. Custom Code

Policy: Probing capabilities is non-invasive and never auto-launches applications
or triggers macOS Automation authorization prompts. Actions are only dispatched
on explicit user invocation.
"""

from __future__ import annotations

import html
import json
import logging
import platform
import re
import shutil
import subprocess
from typing import Any, Callable, Dict, Optional

log = logging.getLogger("ucore.services.host_pim")


def _default_runner(cmd: list[str], timeout: float = 10.0) -> str:
    """Default command runner executing osascript or host CLI binaries."""
    proc = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        timeout=timeout,
        check=False,
    )
    if proc.returncode != 0:
        err = proc.stderr.strip() or f"Command exited with code {proc.returncode}"
        raise RuntimeError(err)
    return proc.stdout.strip()


def markdown_to_html(markdown_text: str) -> str:
    """Convert standard markdown text to clean HTML suitable for Apple Notes / email."""
    lines = markdown_text.splitlines()
    html_lines = []
    in_code_block = False
    code_buffer: list[str] = []

    for line in lines:
        if line.startswith("```"):
            if in_code_block:
                escaped_code = html.escape("\n".join(code_buffer))
                html_lines.append(f"<pre><code>{escaped_code}</code></pre>")
                code_buffer = []
                in_code_block = False
            else:
                in_code_block = True
                code_buffer = []
            continue

        if in_code_block:
            code_buffer.append(line)
            continue

        stripped = line.strip()
        if not stripped:
            continue

        # Headings
        if stripped.startswith("### "):
            html_lines.append(f"<h3>{html.escape(stripped[4:])}</h3>")
        elif stripped.startswith("## "):
            html_lines.append(f"<h2>{html.escape(stripped[3:])}</h2>")
        elif stripped.startswith("# "):
            html_lines.append(f"<h1>{html.escape(stripped[2:])}</h1>")
        # Unordered list items
        elif stripped.startswith(("- ", "* ")):
            item_text = html.escape(stripped[2:])
            item_text = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", item_text)
            item_text = re.sub(r"`(.+?)`", r"<code>\1</code>", item_text)
            html_lines.append(f"<li>{item_text}</li>")
        else:
            # Paragraph
            para = html.escape(stripped)
            para = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", para)
            para = re.sub(r"`(.+?)`", r"<code>\1</code>", para)
            html_lines.append(f"<p>{para}</p>")

    if in_code_block and code_buffer:
        escaped_code = html.escape("\n".join(code_buffer))
        html_lines.append(f"<pre><code>{escaped_code}</code></pre>")

    return "".join(html_lines)


class HostPIMService:
    """Host PIM and automation service bridging uCore to host OS capabilities."""

    def __init__(self, runner: Optional[Callable[[list[str]], str]] = None) -> None:
        self.runner = runner or _default_runner

    def is_macos(self) -> bool:
        return platform.system().lower() == "darwin"

    def probe_capabilities(self) -> Dict[str, Any]:
        """Non-invasively inspect availability of host-native applications."""
        os_name = platform.system().lower()
        report: Dict[str, Any] = {
            "os": os_name,
            "platform": platform.platform(),
            "host_native": {},
            "capabilities": {},
        }

        if os_name == "darwin":
            has_osascript = shutil.which("osascript") is not None
            apps = {
                "safari": ("com.apple.Safari", "Safari"),
                "notes": ("com.apple.Notes", "Notes"),
                "reminders": ("com.apple.reminders", "Reminders"),
                "mail": ("com.apple.mail", "Mail"),
                "messages": ("com.apple.MobileSMS", "Messages"),
            }
            app_status = {}
            for key, (bundle_id, app_name) in apps.items():
                if has_osascript:
                    try:
                        # Inspect bundle identifier without launching app
                        res = self.runner(["osascript", "-e", f'id of application "{app_name}"'])
                        app_status[key] = {
                            "available": bool(res and bundle_id in res),
                            "bundle_id": res or bundle_id,
                            "automation": "supported",
                        }
                    except Exception as exc:
                        app_status[key] = {
                            "available": False,
                            "error": str(exc),
                            "automation": "unavailable",
                        }
                else:
                    app_status[key] = {
                        "available": False,
                        "automation": "no_osascript",
                    }

            report["host_native"] = app_status
            report["capabilities"] = {
                "browser_intake": app_status.get("safari", {}).get("available", False),
                "notes_export": app_status.get("notes", {}).get("available", False),
                "reminders_export": app_status.get("reminders", {}).get("available", False),
                "mail_bridge": app_status.get("mail", {}).get("available", False),
                "notifications": has_osascript,
                "speech_tts": shutil.which("say") is not None,
            }
        else:
            # Linux / other fallback
            has_zen = shutil.which("zen-browser") is not None or shutil.which("zen") is not None
            has_firefox = shutil.which("firefox") is not None
            report["host_native"] = {
                "browser": "zen" if has_zen else ("firefox" if has_firefox else "none"),
                "notifications": shutil.which("notify-send") is not None,
                "speech": shutil.which("spd-say") is not None,
            }
            report["capabilities"] = {
                "browser_intake": False,
                "notes_export": False,
                "reminders_export": False,
                "mail_bridge": False,
                "notifications": shutil.which("notify-send") is not None,
                "speech_tts": shutil.which("spd-say") is not None,
            }

        return report

    def get_active_safari_tab(self) -> Dict[str, Any]:
        """Safely retrieve the URL and title of Safari's active/frontmost tab.

        Returns {ok: bool, running: bool, url: str, title: str, error?: str}.
        Never launches Safari if it is not already running.
        """
        if not self.is_macos():
            return {
                "ok": False,
                "running": False,
                "error": "Safari tab intake is only supported on macOS",
                "url": "",
                "title": "",
            }

        script = """
        (() => {
            try {
                const app = Application("Safari");
                if (!app.running()) {
                    return JSON.stringify({ ok: false, running: false, error: "Safari is not currently running", url: "", title: "" });
                }
                if (app.windows.length === 0) {
                    return JSON.stringify({ ok: false, running: true, error: "Safari has no open windows", url: "", title: "" });
                }
                const win = app.windows[0];
                const tab = win.currentTab();
                return JSON.stringify({
                    ok: true,
                    running: true,
                    url: tab.url() || "",
                    title: tab.name() || "Untitled"
                });
            } catch (err) {
                return JSON.stringify({ ok: false, running: false, error: String(err), url: "", title: "" });
            }
        })()
        """
        try:
            raw = self.runner(["osascript", "-l", "JavaScript", "-e", script])
            data = json.loads(raw or "{}")
            return data
        except Exception as exc:
            return {
                "ok": False,
                "running": False,
                "error": str(exc),
                "url": "",
                "title": "",
            }

    def intake_safari_to_research(self, notes: str = "") -> Dict[str, Any]:
        """Capture the active Safari tab and structure it as a Research Card payload."""
        tab_info = self.get_active_safari_tab()
        if not tab_info.get("ok"):
            return {
                "ok": False,
                "error": tab_info.get("error", "Failed to get active Safari tab"),
            }

        url = tab_info.get("url", "")
        title = tab_info.get("title", "") or "Web Page"

        card = {
            "id": f"card_safari_{hash(url) & 0xFFFFFFFF:08x}",
            "title": title,
            "url": url,
            "notes": notes,
            "source": "safari",
            "type": "web",
            "tags": ["safari", "intake"],
            "summary": f"Captured from active Safari tab: {title}",
        }

        return {
            "ok": True,
            "card": card,
            "url": url,
            "title": title,
        }

    def export_to_apple_notes(
        self,
        title: str,
        body_markdown: str,
        folder: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Export a Markdown document or research synthesis to Apple Notes."""
        if not self.is_macos():
            return {
                "ok": False,
                "error": "Apple Notes export is only supported on macOS",
            }

        body_html = markdown_to_html(body_markdown)
        # Escape for AppleScript string literals
        safe_title = title.replace("\\", "\\\\").replace('"', '\\"')
        safe_body = body_html.replace("\\", "\\\\").replace('"', '\\"')

        folder_clause = f'at folder "{folder.replace("\"", "\\\"")}"' if folder else ""

        script = f"""
        tell application "Notes"
            tell default account
                make new note {folder_clause} with properties {{name:"{safe_title}", body:"{safe_body}"}}
            end tell
        end tell
        """

        try:
            self.runner(["osascript", "-e", script])
            return {
                "ok": True,
                "title": title,
                "folder": folder or "Default",
                "app": "com.apple.Notes",
            }
        except Exception as exc:
            log.warning("Apple Notes export failed: %s", exc)
            return {
                "ok": False,
                "error": str(exc),
                "title": title,
            }

    def export_to_apple_reminders(
        self,
        title: str,
        notes: str = "",
        list_name: Optional[str] = None,
        due_date: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Export a task or snack to Apple Reminders."""
        if not self.is_macos():
            return {
                "ok": False,
                "error": "Apple Reminders export is only supported on macOS",
            }

        safe_title = title.replace("\\", "\\\\").replace('"', '\\"')
        safe_notes = notes.replace("\\", "\\\\").replace('"', '\\"')

        if list_name:
            target_clause = f'list "{list_name.replace("\"", "\\\"")}"'
        else:
            target_clause = "default list"

        due_clause = f', due date:date "{due_date}"' if due_date else ""

        script = f"""
        tell application "Reminders"
            set targetList to {target_clause}
            make new reminder at targetList with properties {{name:"{safe_title}", body:"{safe_notes}"{due_clause}}}
        end tell
        """

        try:
            self.runner(["osascript", "-e", script])
            return {
                "ok": True,
                "title": title,
                "list": list_name or "Default",
                "app": "com.apple.reminders",
            }
        except Exception as exc:
            log.warning("Apple Reminders export failed: %s", exc)
            return {
                "ok": False,
                "error": str(exc),
                "title": title,
            }

    def notify(self, title: str, message: str, subtitle: str = "") -> Dict[str, Any]:
        """Display a native desktop notification."""
        if self.is_macos():
            safe_msg = message.replace("\\", "\\\\").replace('"', '\\"')
            safe_title = title.replace("\\", "\\\\").replace('"', '\\"')
            safe_sub = subtitle.replace("\\", "\\\\").replace('"', '\\"')
            sub_clause = f' subtitle "{safe_sub}"' if subtitle else ""
            script = f'display notification "{safe_msg}" with title "{safe_title}"{sub_clause}'
            try:
                self.runner(["osascript", "-e", script])
                return {"ok": True, "title": title, "message": message}
            except Exception as exc:
                return {"ok": False, "error": str(exc)}
        else:
            # Linux notify-send
            if shutil.which("notify-send"):
                try:
                    self.runner(["notify-send", title, message])
                    return {"ok": True, "title": title, "message": message}
                except Exception as exc:
                    return {"ok": False, "error": str(exc)}
            return {"ok": False, "error": "Desktop notifications not supported on this platform"}

    def say(self, text: str, voice: Optional[str] = None) -> Dict[str, Any]:
        """Synthesize speech on the host OS."""
        if self.is_macos() and shutil.which("say"):
            cmd = ["say"]
            if voice:
                cmd.extend(["-v", voice])
            cmd.append(text)
            try:
                self.runner(cmd)
                return {"ok": True, "text": text, "voice": voice or "default"}
            except Exception as exc:
                return {"ok": False, "error": str(exc)}
        elif shutil.which("spd-say"):
            try:
                self.runner(["spd-say", text])
                return {"ok": True, "text": text}
            except Exception as exc:
                return {"ok": False, "error": str(exc)}
        return {"ok": False, "error": "Speech synthesizer not available"}
