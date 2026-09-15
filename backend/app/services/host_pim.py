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
from pathlib import Path
import platform
import re
import shutil
import subprocess
from datetime import datetime, timezone
from typing import Any, Callable, Dict, List, Optional

log = logging.getLogger("ucore.services.host_pim")


def _default_runner(cmd: list[str], timeout: float = 10.0, input_data: Optional[str] = None) -> str:
    """Default command runner executing osascript or host CLI binaries."""
    proc = subprocess.run(
        cmd,
        input=input_data,
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

            has_shortcuts = shutil.which("shortcuts") is not None
            app_status["shortcuts"] = {
                "available": has_shortcuts,
                "automation": "cli" if has_shortcuts else "none",
            }
            report["host_native"] = app_status
            report["capabilities"] = {
                "browser_intake": app_status.get("safari", {}).get("available", False),
                "notes_export": app_status.get("notes", {}).get("available", False),
                "notes_intake": app_status.get("notes", {}).get("available", False),
                "reminders_export": app_status.get("reminders", {}).get("available", False),
                "reminders_intake": app_status.get("reminders", {}).get("available", False),
                "mail_bridge": app_status.get("mail", {}).get("available", False),
                "shortcuts": has_shortcuts,
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
                "notes_intake": False,
                "reminders_export": False,
                "reminders_intake": False,
                "mail_bridge": False,
                "shortcuts": False,
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
            safe_list = list_name.replace("\\", "\\\\").replace('"', '\\"')
            target_clause = f'list "{safe_list}"'
            ensure_list_clause = f"""if not (exists list "{safe_list}") then
                make new list with properties {{name:"{safe_list}"}}
            end if"""
        else:
            target_clause = "default list"
            ensure_list_clause = ""

        due_clause = f', due date:date "{due_date}"' if due_date else ""

        script = f"""
        tell application "Reminders"
            {ensure_list_clause}
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

    def intake_apple_reminders(
        self,
        list_name: Optional[str] = None,
        limit: int = 25,
        completed: bool = False,
    ) -> Dict[str, Any]:
        """Query tasks/reminders from Apple Reminders via JXA."""
        if not self.is_macos():
            return {
                "ok": False,
                "error": "Apple Reminders intake is only supported on macOS",
                "items": [],
            }

        safe_list = (list_name or "").replace("\\", "\\\\").replace('"', '\\"')
        completed_val = "true" if completed else "false"
        safe_limit = max(1, min(int(limit), 100))

        script = f"""
        (() => {{
            try {{
                const app = Application("Reminders");
                let targetList;
                if ("{safe_list}") {{
                    const matches = app.lists.whose({{ name: "{safe_list}" }})();
                    if (!matches || matches.length === 0) {{
                        return JSON.stringify({{ ok: false, error: 'List not found: {safe_list}', items: [] }});
                    }}
                    targetList = matches[0];
                }} else {{
                    targetList = app.defaultList();
                }}
                const rems = targetList.reminders.whose({{ completed: {completed_val} }})();
                const limit = {safe_limit};
                const items = [];
                for (let i = 0; i < Math.min(rems.length, limit); i++) {{
                    const r = rems[i];
                    let dueDateStr = null;
                    try {{
                        const d = r.dueDate();
                        if (d) dueDateStr = d.toISOString();
                    }} catch (e) {{}}
                    items.push({{
                        id: r.id(),
                        title: r.name() || "",
                        notes: r.body() || "",
                        due_date: dueDateStr,
                        completed: r.completed(),
                        list: targetList.name()
                    }});
                }}
                return JSON.stringify({{ ok: true, items: items }});
            }} catch (err) {{
                return JSON.stringify({{ ok: false, error: String(err), items: [] }});
            }}
        }})()
        """
        try:
            raw = self.runner(["osascript", "-l", "JavaScript", "-e", script])
            data = json.loads(raw or "{}")
            return data
        except Exception as exc:
            log.warning("Apple Reminders intake failed: %s", exc)
            return {
                "ok": False,
                "error": str(exc),
                "items": [],
            }

    def intake_apple_notes(
        self,
        folder: Optional[str] = None,
        limit: int = 15,
        search: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Query notes from Apple Notes via JXA."""
        if not self.is_macos():
            return {
                "ok": False,
                "error": "Apple Notes intake is only supported on macOS",
                "items": [],
            }

        safe_folder = (folder or "").replace("\\", "\\\\").replace('"', '\\"')
        safe_search = (search or "").replace("\\", "\\\\").replace('"', '\\"').lower()
        safe_limit = max(1, min(int(limit), 50))

        script = f"""
        (() => {{
            try {{
                const app = Application("Notes");
                let noteList = [];
                let folderName = "{safe_folder}";
                if (folderName) {{
                    const fMatches = app.folders.whose({{ name: folderName }})();
                    if (!fMatches || fMatches.length === 0) {{
                        return JSON.stringify({{ ok: false, error: 'Folder not found: ' + folderName, items: [] }});
                    }}
                    noteList = fMatches[0].notes();
                }} else {{
                    const acc = app.defaultAccount();
                    noteList = acc.notes();
                    folderName = "Default";
                }}
                const searchTerm = "{safe_search}";
                const limit = {safe_limit};
                const items = [];
                for (let i = 0; i < noteList.length && items.length < limit; i++) {{
                    const n = noteList[i];
                    const name = n.name() || "Untitled Note";
                    let plain = "";
                    try {{
                        plain = n.plaintext() || "";
                    }} catch (e) {{}}
                    if (searchTerm) {{
                        if (!name.toLowerCase().includes(searchTerm) && !plain.toLowerCase().includes(searchTerm)) {{
                            continue;
                        }}
                    }}
                    let modDate = null;
                    try {{
                        const md = n.modificationDate();
                        if (md) modDate = md.toISOString();
                    }} catch (e) {{}}
                    items.push({{
                        id: n.id(),
                        title: name,
                        body: plain.slice(0, 1000),
                        modification_date: modDate,
                        folder: folderName
                    }});
                }}
                return JSON.stringify({{ ok: true, items: items }});
            }} catch (err) {{
                return JSON.stringify({{ ok: false, error: String(err), items: [] }});
            }}
        }})()
        """
        try:
            raw = self.runner(["osascript", "-l", "JavaScript", "-e", script])
            data = json.loads(raw or "{}")
            return data
        except Exception as exc:
            log.warning("Apple Notes intake failed: %s", exc)
            return {
                "ok": False,
                "error": str(exc),
                "items": [],
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

    def list_shortcuts(self) -> list[str]:
        """List available shortcuts on macOS non-invasively."""
        if not self.is_macos() or not shutil.which("shortcuts"):
            return []
        try:
            raw = self.runner(["shortcuts", "list"])
            return [line.strip() for line in raw.splitlines() if line.strip()]
        except Exception as exc:
            log.debug("Could not list shortcuts: %s", exc)
            return []

    def run_shortcut(self, name: str, input_text: str = "") -> Dict[str, Any]:
        """Execute a macOS shortcut with optional input text."""
        if not self.is_macos() or not shutil.which("shortcuts"):
            return {
                "ok": False,
                "error": "macOS Shortcuts CLI not available",
            }
        cmd = ["shortcuts", "run", name]
        try:
            try:
                out = self.runner(cmd, input_data=input_text)
            except TypeError:
                out = self.runner(cmd)
            return {
                "ok": True,
                "shortcut": name,
                "output": out,
            }
        except Exception as exc:
            log.warning("Running shortcut '%s' failed: %s", name, exc)
            return {
                "ok": False,
                "shortcut": name,
                "error": str(exc),
            }

    def archive_apple_mail(self, message_id: str) -> Dict[str, Any]:
        """Mark an email as read and move to archive in Apple Mail."""
        if not self.is_macos():
            return {"ok": False, "error": "Apple Mail is only supported on macOS"}
        safe_id = message_id.replace("\\", "\\\\").replace('"', '\\"')
        script = f"""
        (() => {{
            try {{
                const app = Application("Mail");
                const matches = app.inbox.messages.whose({{messageId: "{safe_id}"}})();
                if (matches.length > 0) {{
                    for (const m of matches) {{
                        m.readStatus = true;
                        try {{
                            const acc = m.mailbox().account();
                            if (acc && acc.archiveMailbox()) {{
                                m.mailbox = acc.archiveMailbox();
                            }}
                        }} catch (e) {{}}
                    }}
                    return JSON.stringify({{ ok: true, count: matches.length, archived: true }});
                }}
                return JSON.stringify({{ ok: false, error: "Message not found in inbox", archived: false }});
            }} catch (err) {{
                return JSON.stringify({{ ok: false, error: String(err), archived: false }});
            }}
        }})()
        """
        try:
            raw = self.runner(["osascript", "-l", "JavaScript", "-e", script])
            data = json.loads(raw or "{}")
            return data
        except Exception as exc:
            log.warning("Apple Mail archive failed: %s", exc)
            return {"ok": False, "error": str(exc), "archived": False}

    def flag_apple_mail(self, message_id: str, flag_index: int = 0) -> Dict[str, Any]:
        """Flag an email in Apple Mail (0=Red, 1=Orange, 2=Yellow, 3=Green, 4=Blue, 5=Purple, 6=Gray, -1=clear)."""
        if not self.is_macos():
            return {"ok": False, "error": "Apple Mail is only supported on macOS"}
        safe_id = message_id.replace("\\", "\\\\").replace('"', '\\"')
        flag_status = "true" if flag_index >= 0 else "false"
        set_flag_clause = f"m.flagIndex = {flag_index};" if flag_index >= 0 else ""
        script = f"""
        (() => {{
            try {{
                const app = Application("Mail");
                const matches = app.inbox.messages.whose({{messageId: "{safe_id}"}})();
                if (matches.length > 0) {{
                    for (const m of matches) {{
                        m.flaggedStatus = {flag_status};
                        {set_flag_clause}
                    }}
                    return JSON.stringify({{ ok: true, count: matches.length, flag_index: {flag_index} }});
                }}
                return JSON.stringify({{ ok: false, error: "Message not found in inbox" }});
            }} catch (err) {{
                return JSON.stringify({{ ok: false, error: String(err) }});
            }}
        }})()
        """
        try:
            raw = self.runner(["osascript", "-l", "JavaScript", "-e", script])
            data = json.loads(raw or "{}")
            return data
        except Exception as exc:
            log.warning("Apple Mail flag failed: %s", exc)
            return {"ok": False, "error": str(exc)}

    def intake_apple_mail(self, limit: int = 25, unread_only: bool = True) -> Dict[str, Any]:
        """Query messages from Apple Mail via JXA."""
        if not self.is_macos():
            return {
                "ok": False,
                "error": "Apple Mail is only supported on macOS",
                "items": [],
                "count": 0,
            }
        safe_limit = max(1, min(int(limit), 100))
        unread_clause = "if (!m.readStatus())" if unread_only else "if (true)"
        script = f"""
        (() => {{
            try {{
                const app = Application("Mail");
                const items = app.inbox.messages();
                const limit = {safe_limit};
                const rows = [];
                for (let i = 0; i < items.length && rows.length < limit; i++) {{
                    const m = items[i];
                    {unread_clause} {{
                        let flagged = false;
                        let flagIdx = -1;
                        try {{
                            flagged = Boolean(m.flaggedStatus());
                            flagIdx = flagged ? m.flagIndex() : -1;
                        }} catch(e) {{}}
                        let dateStr = null;
                        try {{
                            const d = m.dateReceived();
                            if (d) dateStr = d.toISOString();
                        }} catch(e) {{}}
                        let contentSnippet = "";
                        try {{
                            contentSnippet = (m.content() || "").slice(0, 500);
                        }} catch(e) {{}}
                        rows.push({{
                            id: String(m.messageId() || ""),
                            subject: String(m.subject() || "(No Subject)"),
                            sender: String(m.sender() || ""),
                            date: dateStr,
                            read: Boolean(m.readStatus()),
                            flagged: flagged,
                            flag_index: flagIdx,
                            snippet: contentSnippet
                        }});
                    }}
                }}
                return JSON.stringify({{ ok: true, items: rows, count: rows.length }});
            }} catch(err) {{
                return JSON.stringify({{ ok: false, error: String(err), items: [], count: 0 }});
            }}
        }})()
        """
        try:
            raw = self.runner(["osascript", "-l", "JavaScript", "-e", script])
            data = json.loads(raw or "{}")
            return data
        except Exception as exc:
            log.warning("Apple Mail intake failed: %s", exc)
            return {"ok": False, "error": str(exc), "items": [], "count": 0}

    def intake_imessage(self, limit: int = 25) -> Dict[str, Any]:
        """Query active chats / recent messages from Apple Messages via JXA."""
        if not self.is_macos():
            return {
                "ok": False,
                "error": "Apple Messages is only supported on macOS",
                "items": [],
                "count": 0,
            }
        safe_limit = max(1, min(int(limit), 100))
        script = f"""
        (() => {{
            try {{
                const app = Application("Messages");
                const chats = app.chats();
                const limit = {safe_limit};
                const rows = [];
                for (let i = 0; i < chats.length && rows.length < limit; i++) {{
                    const c = chats[i];
                    const name = String(c.name() || c.id() || "Chat");
                    let lastMsg = "";
                    let dateStr = null;
                    try {{
                        const msgs = c.messages();
                        if (msgs && msgs.length > 0) {{
                            const last = msgs[msgs.length - 1];
                            lastMsg = String(last.text() || "");
                            const d = last.date();
                            if (d) dateStr = d.toISOString();
                        }}
                    }} catch(e) {{}}
                    rows.push({{
                        id: String(c.id() || ""),
                        name: name,
                        last_message: lastMsg,
                        date: dateStr
                    }});
                }}
                return JSON.stringify({{ ok: true, items: rows, count: rows.length }});
            }} catch(err) {{
                return JSON.stringify({{ ok: false, error: String(err), items: [], count: 0 }});
            }}
        }})()
        """
        try:
            raw = self.runner(["osascript", "-l", "JavaScript", "-e", script])
            data = json.loads(raw or "{}")
            return data
        except Exception as exc:
            log.warning("Apple Messages intake failed: %s", exc)
            return {"ok": False, "error": str(exc), "items": [], "count": 0}

    def sync_apple_reminders_outbound(
        self,
        tasks: List[Dict[str, Any]],
        default_list: str = "uDos",
    ) -> Dict[str, Any]:
        """Export a collection of tasks / action items to Apple Reminders."""
        if not self.is_macos():
            return {
                "ok": False,
                "error": "Apple Reminders export is only supported on macOS",
                "synced_count": 0,
                "items": [],
            }

        synced: List[Dict[str, Any]] = []
        errors: List[Dict[str, Any]] = []

        for task in tasks:
            title = str(task.get("title") or task.get("name") or "").strip()
            if not title:
                continue
            notes = str(task.get("notes") or task.get("description") or "")
            list_name = str(task.get("list_name") or task.get("list") or task.get("binder") or default_list)
            due_date = task.get("due_date") or task.get("due") or task.get("deadline")
            res = self.export_to_apple_reminders(
                title=title,
                notes=notes,
                list_name=list_name,
                due_date=str(due_date) if due_date else None,
            )
            if res.get("ok"):
                synced.append({
                    "id": task.get("id"),
                    "title": title,
                    "list": list_name,
                    "due_date": due_date,
                    "status": "exported",
                })
            else:
                errors.append({
                    "id": task.get("id"),
                    "title": title,
                    "error": res.get("error", "Unknown error"),
                })

        return {
            "ok": len(errors) == 0 or len(synced) > 0,
            "synced_count": len(synced),
            "items": synced,
            "errors": errors,
        }

    def get_sync_status(self) -> Dict[str, Any]:
        """Aggregate sync status across Apple PIM, Google Drive mirror, and BitChat mesh."""
        now_iso = datetime.now(timezone.utc).isoformat()
        caps = self.probe_capabilities()
        host_native = caps.get("host_native", {})

        # Google Drive status
        vault_path = Path.home() / "Vault"
        gdrive_configured = vault_path.exists() and (
            (vault_path / ".sync").exists() or (vault_path / "GoogleDrive").exists()
        )
        gdrive_cloud_storage = Path.home() / "Library" / "CloudStorage"
        has_gdrive_mount = False
        if gdrive_cloud_storage.exists():
            try:
                has_gdrive_mount = any("GoogleDrive" in p.name for p in gdrive_cloud_storage.iterdir())
            except Exception:
                has_gdrive_mount = False

        # BitChat mesh status
        peer_count = 0
        local_peer_id = None
        try:
            from app.services.mesh_transport import get_mesh_registry
            reg = get_mesh_registry()
            local_peer_id = reg.local_peer_id
            peers = reg.get_peers()
            peer_count = len([p for p in peers if p.get("status") == "online"])
        except Exception:
            pass

        return {
            "ok": True,
            "timestamp": now_iso,
            "platform": platform.system().lower(),
            "apple_sync": {
                "reminders": {
                    "available": host_native.get("reminders", {}).get("available", False),
                    "bidirectional": True,
                },
                "notes": {
                    "available": host_native.get("notes", {}).get("available", False),
                    "bidirectional": True,
                },
                "mail": {
                    "available": host_native.get("mail", {}).get("available", False),
                    "bidirectional": True,
                },
                "messages": {
                    "available": host_native.get("messages", {}).get("available", False),
                    "bidirectional": False,
                },
            },
            "google_drive": {
                "configured": gdrive_configured or has_gdrive_mount,
                "vault_path": str(vault_path),
                "vault_exists": vault_path.exists(),
                "cloud_storage_detected": has_gdrive_mount,
            },
            "bitchat_mesh": {
                "active": True,
                "local_peer_id": local_peer_id,
                "online_peers": peer_count,
            },
        }

