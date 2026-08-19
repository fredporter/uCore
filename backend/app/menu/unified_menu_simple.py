"""Unified uCore Menu Bar App — Simplified version.

CONSOLIDATED MENU: Only essential actions appear here.
Full snack management is available in the SnackMachine surface.

This is the streamlined menu that focuses on:
- UI Hub status and access
- Quick access to SnackMachine surface
- Clipboard buffer (essential)
- Backend status
- Start at login toggle
"""
from __future__ import annotations

import logging
import os
import threading
import time
from pathlib import Path

import objc
from AppKit import (
    NSAlert,
    NSApp,
    NSApplication,
    NSMenu,
    NSMenuItem,
)
from Foundation import NSObject

try:
    from AppKit import NSEvent, NSEventMaskKeyDown
except Exception:
    NSEvent = NSEventMaskKeyDown = None
from PyObjCTools import AppHelper

from app.clipboard.clipboard_buffer import (
    add_clipboard_item,
    copy_text_to_clipboard,
)

# Import modular components
from app.menu.api_helpers import (
    api_get_sync,
    api_post_sync,
    is_dev_alive,
    is_ucore_alive,
    is_uihub_alive,
    open_url,
)

# Import snack registry and plugins
from app.menu.backend_manager import ensure_backend_running
from app.menu.launchd_integration import (
    install_launchd,
    is_launchd_installed,
    uninstall_launchd,
)
from app.menu.lockfile import acquire_lock, release_lock
from app.menu.snacks.clipboard_snack import register as register_clipboard
from app.menu.status_icon import _make_status_icon, update_status_icon
from snackmachine.registry import get_registry

# ─── Config ───────────────────────────────────────────────────────────
UCORE_URL = "http://127.0.0.1:8484"
UI_HUB_URL = "http://localhost:5175"
REFRESH_INTERVAL = 30.0  # seconds

UCORE_LABEL = "com.udos.ucore-menu"
UCORE_PLIST = os.path.expanduser(f"~/Library/LaunchAgents/{UCORE_LABEL}.plist")
UDOS_HOME = Path(os.environ.get("UDOS_HOME", Path.home() / "Code" / ".udos")).expanduser()
UCORE_LOCKFILE = str(UDOS_HOME / "ucore-menu.pid")
UCORE_BACKEND_DIR = os.environ.get("UCORE_BACKEND_DIR", str(Path.home() / "Code" / "uCore" / "backend"))
SNACKMACHINE_REPO_DIR = Path(
    os.environ.get(
        "SNACKMACHINE_REPO_DIR",
        str(Path.home() / "Code" / "SnackMachine"),
    )
)

CORE_EXTENSION_IDS = {
    "ucore-core",
    "ucore-skills",
    "ucore-surfaces",
    "ucore-secrets",
    "ucore-tools",
    "uflow",
    "uknowledge",
}

EXTENSION_LINKS = {
    "snackmachine-extension": "http://localhost:5175/snackbar?tab=snacks",
}

log_dir = UDOS_HOME / "logs"
log_dir.mkdir(parents=True, exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] ucore-menu: %(message)s",
    handlers=[
        logging.FileHandler(log_dir / "ucore-menu.log"),
        logging.StreamHandler(),
    ],
)
log = logging.getLogger("ucore-menu")


# ─── Frontend helpers ─────────────────────────────────────────────────


def _ensure_frontend_running() -> bool:
    """Ensure both backend and frontend are running.

    Returns True if frontend is reachable after this call.
    Extracted from duplicated blocks in openUIHub_, openSnackMachine_,
    and showClipboardPopover_.
    """
    if is_uihub_alive():
        return True

    if not is_ucore_alive():
        ensure_backend_running()
        time.sleep(2)

    log.info("Starting frontend via launchd...")
    try:
        from app.menu.launchd_manager import (
            install_frontend,
            is_frontend_installed,
        )
        if not is_frontend_installed():
            install_frontend()
        for _ in range(20):
            time.sleep(0.5)
            if is_uihub_alive():
                log.info("Frontend started successfully")
                return True
    except Exception as e:
        log.error(f"Failed to start frontend: {e}")

    return is_uihub_alive()


def _is_snackmachine_installed() -> bool:
    """Check whether SnackMachine extension appears locally installed."""
    return (SNACKMACHINE_REPO_DIR / "pyproject.toml").exists()


def _clipboard_preview_label(item: dict, max_len: int = 60) -> str:
    """Build a short, single-line preview label for a clipboard item."""
    text = str(item.get("content") or "")
    text = " ".join(text.split())
    if not text:
        text = "(empty)"
    if len(text) > max_len:
        text = f"{text[:max_len - 3]}..."
    return text


def _installed_extensions() -> list[dict[str, str]]:
    """List detected installed extras for menu links."""
    extensions: list[dict[str, str]] = []

    if _is_snackmachine_installed():
        extensions.append(
            {
                "id": "snackmachine-extension",
                "name": "SnackMachine",
                "url": EXTENSION_LINKS["snackmachine-extension"],
            }
        )

    status = api_get_sync("/api/extensions/status") or {}
    for ext in status.get("extensions", []):
        ext_id = str(ext.get("id", "")).strip()
        if not ext_id or ext_id in CORE_EXTENSION_IDS:
            continue
        if not ext.get("loaded", False):
            continue

        if any(e["id"] == ext_id for e in extensions):
            continue

        extensions.append(
            {
                "id": ext_id,
                "name": str(ext.get("name", ext_id)),
                "url": EXTENSION_LINKS.get(
                    ext_id,
                    "http://localhost:5175/system",
                ),
            }
        )

    return extensions


# ─── App Delegate ─────────────────────────────────────────────────────

class UnifiedMenuDelegate(NSObject):
    """Main delegate for the unified uCore menu bar app."""

    def init(self):
        self = objc.super(UnifiedMenuDelegate, self).init()
        if self is None:
            return None

        self._connected = False
        self._uihub_connected = False
        self._dev_connected = False
        self._start_at_login = False
        self._services = []
        self._status_item = None
        self._menu = None
        self._refresh_timer = None
        self._clipboard_panel = None
        self._clipboard_search_field = None
        self._clipboard_table = None
        self._clipboard_panel_items = []
        self._global_shortcut_monitor = None

        self._registry = get_registry()
        self._clipboard_snack = register_clipboard(self)

        return self

    def setupStatusBar(self):
        """Create the status bar item."""
        # Create status item with emoji title directly
        self._status_item = _make_status_icon(False)
        self._status_item.retain()

        self._menu = NSMenu.alloc().init()
        self._menu.setAutoenablesItems_(False)
        self._status_item.setMenu_(self._menu)

        self._start_at_login = is_launchd_installed()
        self._rebuild_menu()
        self._register_global_shortcut()
        self._start_refresh()

    def _register_global_shortcut(self):
        """Register global shortcut for clipboard panel (Ctrl+Cmd+V)."""
        try:
            from AppKit import NSEvent, NSEventMaskKeyDown

            from app.menu.shortcut_utils import MOD_ALL, MOD_COMMAND, MOD_CONTROL

            wanted_mods = MOD_CONTROL | MOD_COMMAND
            wanted_key = 9  # 'v' key code

            def _handler(event):
                try:
                    actual = int(event.modifierFlags()) & MOD_ALL
                    if actual == wanted_mods and int(event.keyCode()) == wanted_key:
                        self.performSelectorOnMainThread_withObject_waitUntilDone_(
                            "showClipboardPopover:", None, False,
                        )
                except Exception as exc:
                    log.debug("Global shortcut handler error: %s", exc)

            self._global_shortcut_monitor = (
                NSEvent.addGlobalMonitorForEventsMatchingMask_handler_(
                    NSEventMaskKeyDown, _handler
                )
            )
            log.info("Global clipboard shortcut registered: Ctrl+Cmd+V")
        except Exception as exc:
            log.warning("Failed to register global shortcut: %s", exc)

    def _rebuild_menu(self):
        """Rebuild the menu - CONSOLIDATED to essential items only."""
        # Create a fresh NSMenu each rebuild — reusing self._menu with
        # NSMenuItem.separatorItem() singletons causes "already in another menu".
        new_menu = NSMenu.alloc().init()
        self._status_item.setMenu_(new_menu)
        self._menu = new_menu

        # ── Header ──────────────────────────────────────────────
        item = NSMenuItem.alloc().initWithTitle_action_keyEquivalent_(
            "🍿 Snackbar", None, "h",
        )
        item.setEnabled_(False)
        item.setTarget_(self)
        self._menu.addItem_(item)

        self._menu.addItem_(NSMenuItem.separatorItem())

        # ── UI Hub Section ──────────────────────────────────────
        uihub_status = "😊" if self._uihub_connected else "😢"
        item = NSMenuItem.alloc().initWithTitle_action_keyEquivalent_(
            f"{uihub_status} Frontend", None, "",
        )
        item.setEnabled_(False)
        self._menu.addItem_(item)

        item = NSMenuItem.alloc().initWithTitle_action_keyEquivalent_(
            "🍒 Open UI Hub", "openUIHub:", "o",
        )
        item.setTarget_(self)
        self._menu.addItem_(item)

        # ── Services Health ─────────────────────────────────────
        down = [s for s in self._services if s.get("status") != "up"]
        srv_icon = "😞" if down else "😊"
        item = NSMenuItem.alloc().initWithTitle_action_keyEquivalent_(
            f"{srv_icon} Services Health", None, "",
        )
        srv_submenu = NSMenu.alloc().init()

        if not self._services:
            none_item = NSMenuItem.alloc().initWithTitle_action_keyEquivalent_(
                "Backend unreachable", None, "",
            )
            none_item.setEnabled_(False)
            srv_submenu.addItem_(none_item)
        else:
            title_item = NSMenuItem.alloc().initWithTitle_action_keyEquivalent_(
                f"{len(self._services)} services · {len(down)} down",
                None,
                "",
            )
            title_item.setEnabled_(False)
            srv_submenu.addItem_(title_item)
            srv_submenu.addItem_(NSMenuItem.separatorItem())

            for svc in self._services[:12]:
                name = svc.get("name", "?")
                status = svc.get("status", "unknown")
                port = svc.get("port", "")
                dot = {
                    "up": "�",
                    "degraded": "😐",
                    "down": "😞",
                }.get(status, "⚪")
                label = f"{dot} {name}"
                if port:
                    label += f"  :{port}"
                svc_item = NSMenuItem.alloc().initWithTitle_action_keyEquivalent_(
                    label, None, "",
                )
                svc_item.setEnabled_(False)
                srv_submenu.addItem_(svc_item)

            srv_submenu.addItem_(NSMenuItem.separatorItem())
            if down:
                crash_item = NSMenuItem.alloc().initWithTitle_action_keyEquivalent_(
                    "🚨 Open Crash Recovery (S500)",
                    "openServicesCrash:",
                    "",
                )
                crash_item.setTarget_(self)
                srv_submenu.addItem_(crash_item)
            services_item = NSMenuItem.alloc().initWithTitle_action_keyEquivalent_(
                "Open All Services", "openServicesPanel:", "",
            )
            services_item.setTarget_(self)
            srv_submenu.addItem_(services_item)

        item.setSubmenu_(srv_submenu)
        self._menu.addItem_(item)

        self._menu.addItem_(NSMenuItem.separatorItem())

        # ── Quick Actions ────────────────────────────────────────
        if _is_snackmachine_installed():
            item = NSMenuItem.alloc().initWithTitle_action_keyEquivalent_(
                "🍟 SnackMachine", None, "s",
            )
            submenu = NSMenu.alloc().init()

            open_item = NSMenuItem.alloc().initWithTitle_action_keyEquivalent_(
                "Open Snacks Workspace", "openSnackMachine:", "",
            )
            open_item.setTarget_(self)
            submenu.addItem_(open_item)
            submenu.addItem_(NSMenuItem.separatorItem())

            snacks = self._registry.get_all(enabled_only=False)
            if snacks:
                status_title = NSMenuItem.alloc().initWithTitle_action_keyEquivalent_(
                    "Installed Snacks",
                    None,
                    "",
                )
                status_title.setEnabled_(False)
                submenu.addItem_(status_title)

                max_items = 12
                for snack in snacks[:max_items]:
                    spec = snack.spec
                    available = bool(spec.enabled and snack.is_available())
                    state = "on" if available else "off"
                    snack_item = NSMenuItem.alloc().initWithTitle_action_keyEquivalent_(
                        f"{spec.icon} {spec.name} ({state})",
                        None,
                        "",
                    )
                    snack_item.setEnabled_(False)
                    submenu.addItem_(snack_item)

                if len(snacks) > max_items:
                    more = len(snacks) - max_items
                    more_item = NSMenuItem.alloc().initWithTitle_action_keyEquivalent_(
                        f"... +{more} more",
                        None,
                        "",
                    )
                    more_item.setEnabled_(False)
                    submenu.addItem_(more_item)
            else:
                none_item = NSMenuItem.alloc().initWithTitle_action_keyEquivalent_(
                    "No snacks registered",
                    None,
                    "",
                )
                none_item.setEnabled_(False)
                submenu.addItem_(none_item)

            item.setSubmenu_(submenu)
            self._menu.addItem_(item)
        else:
            item = NSMenuItem.alloc().initWithTitle_action_keyEquivalent_(
                "🍟 Install SnackMachine", "installSnackMachine:", "s",
            )
            item.setTarget_(self)
            self._menu.addItem_(item)

        item = NSMenuItem.alloc().initWithTitle_action_keyEquivalent_(
            "🏝️ Clipboard", None, "v",
        )
        item.setTarget_(self)
        clipboard_submenu = NSMenu.alloc().init()

        recent: list[dict] = []
        if self._clipboard_snack:
            recent, _saved = self._clipboard_snack.get_items()

        if recent:
            title_item = NSMenuItem.alloc().initWithTitle_action_keyEquivalent_(
                "Recent Copies",
                None,
                "",
            )
            title_item.setEnabled_(False)
            clipboard_submenu.addItem_(title_item)

            for clip_item in recent[:10]:
                clip_id = str(clip_item.get("id") or "")
                if not clip_id:
                    continue
                label = _clipboard_preview_label(clip_item)
                menu_item = NSMenuItem.alloc().initWithTitle_action_keyEquivalent_(
                    label,
                    "selectClipboardItem:",
                    "",
                )
                menu_item.setTarget_(self)
                menu_item.setRepresentedObject_(clip_id)
                clipboard_submenu.addItem_(menu_item)
        else:
            empty_item = NSMenuItem.alloc().initWithTitle_action_keyEquivalent_(
                "No clipboard history yet",
                None,
                "",
            )
            empty_item.setEnabled_(False)
            clipboard_submenu.addItem_(empty_item)

        clipboard_submenu.addItem_(NSMenuItem.separatorItem())
        open_item = NSMenuItem.alloc().initWithTitle_action_keyEquivalent_(
            "Open Full Clipboard History",
            "showClipboardPopover:",
            "",
        )
        open_item.setTarget_(self)
        clipboard_submenu.addItem_(open_item)

        item.setSubmenu_(clipboard_submenu)
        self._menu.addItem_(item)

        # ── Vue Server ──────────────────────────────────────────
        frontend_dot = "💎" if self._uihub_connected else "😢"
        frontend_label = (
            f"{frontend_dot} Vue Server: Running"
            if self._uihub_connected
            else f"{frontend_dot} Vue Server: Stopped"
        )
        item = NSMenuItem.alloc().initWithTitle_action_keyEquivalent_(
            frontend_label, None, "",
        )
        item.setEnabled_(False)
        self._menu.addItem_(item)

        extensions = _installed_extensions()
        if extensions:
            self._menu.addItem_(NSMenuItem.separatorItem())
            ext_header = NSMenuItem.alloc().initWithTitle_action_keyEquivalent_(
                "Extensions",
                None,
                "",
            )
            ext_header.setEnabled_(False)
            self._menu.addItem_(ext_header)

            for ext in extensions:
                if ext["id"] == "snackmachine-extension":
                    continue
                ext_item = NSMenuItem.alloc().initWithTitle_action_keyEquivalent_(
                    f"🧩 {ext['name']}",
                    "openExtensionLink:",
                    "",
                )
                ext_item.setTarget_(self)
                ext_item.setRepresentedObject_(ext["url"])
                self._menu.addItem_(ext_item)

        self._menu.addItem_(NSMenuItem.separatorItem())

        # ── Status ───────────────────────────────────────────────
        backend_status = "😊" if self._connected else "😢"
        item = NSMenuItem.alloc().initWithTitle_action_keyEquivalent_(
            f"{backend_status} Backend", None, "",
        )
        item.setEnabled_(False)
        self._menu.addItem_(item)

        state = "✓" if self._start_at_login else "  "
        item = NSMenuItem.alloc().initWithTitle_action_keyEquivalent_(
            f"{state} Start at Login", "toggleStartAtLogin:", "",
        )
        item.setTarget_(self)
        self._menu.addItem_(item)

        item = NSMenuItem.alloc().initWithTitle_action_keyEquivalent_(
            "↻ Restart Backend", "restartBackend:", "b",
        )
        item.setTarget_(self)
        self._menu.addItem_(item)

        item = NSMenuItem.alloc().initWithTitle_action_keyEquivalent_(
            "↻ Restart Vue", "restartFrontend:", "v",
        )
        item.setTarget_(self)
        self._menu.addItem_(item)

        self._menu.addItem_(NSMenuItem.separatorItem())

        # ── Quit ───────────────────────────────────────────────
        item = NSMenuItem.alloc().initWithTitle_action_keyEquivalent_(
            "🔥 Quit", "quitApp:", "q",
        )
        item.setTarget_(self)
        self._menu.addItem_(item)

    def _start_refresh(self):
        """Start the periodic refresh timer."""
        self._refresh()

    def _refresh(self):
        """Refresh all status and rebuild menu."""
        try:
            self._connected = is_ucore_alive()
            self._uihub_connected = is_uihub_alive()
            self._dev_connected = is_dev_alive()
            self._start_at_login = is_launchd_installed()

            if self._connected:
                clip_data = api_get_sync("/api/snacks/clipboard?limit=24")
                if clip_data:
                    clip_items = clip_data.get("items", [])
                    recent = [c for c in clip_items if not c.get("pinned")]
                    saved = [c for c in clip_items if c.get("pinned")]
                    if self._clipboard_snack:
                        self._clipboard_snack.update_items(recent, saved)

                services = api_get_sync("/api/server/services")
                self._services = (
                    (services or {}).get("services", [])
                    if services
                    else []
                )
            else:
                self._services = []
        except Exception as e:
            log.warning(f"Refresh error: {e}")
            self._connected = False

        if self._refresh_timer:
            self._refresh_timer.cancel()
        self._refresh_timer = threading.Timer(REFRESH_INTERVAL, self._refresh)
        self._refresh_timer.daemon = True
        self._refresh_timer.start()

        self.performSelectorOnMainThread_withObject_waitUntilDone_(
            "updateUI:", None, False,
        )

    def updateUI_(self, sender):
        """Called on main thread to update icon and menu."""
        update_status_icon(self._status_item, self._connected)
        self._rebuild_menu()

    # ─── Actions ───────────────────────────────────────────────────

    def openUIHub_(self, _sender):
        """Open UI Hub in browser with auto-start."""
        log.info("Opening UI Hub")
        if _ensure_frontend_running():
            open_url(UI_HUB_URL)
        else:
            alert = NSAlert.alloc().init()
            alert.setMessageText_("UIHub not reachable")
            alert.setInformativeText_(
                "Backend is running but UI Hub is still down."
            )
            alert.runModal()

    def openSnackMachine_(self, _sender):
        """Open snacks workspace (and extension if installed)."""
        log.info("Opening SnackMachine/workspace")
        _ensure_frontend_running()
        open_url("http://localhost:5175/server?tab=snacks")

    def openServicesCrash_(self, _sender):
        """Open the S500 crash recovery page."""
        log.info("Opening S500 crash recovery")
        _ensure_frontend_running()
        open_url("http://localhost:5175/system/s500")

    def openServicesPanel_(self, _sender):
        """Open the Snackbar services panel."""
        log.info("Opening Snackbar services panel")
        _ensure_frontend_running()
        open_url("http://localhost:5175/snackbar?tab=services")

    def installSnackMachine_(self, _sender):
        """Open the SnackMachine repository for installation instructions."""
        log.info("Opening SnackMachine install page")
        open_url("https://github.com/fredporter/SnackMachine")

    def openExtensionLink_(self, sender):
        """Open an installed extension link from represented object."""
        try:
            url = str(sender.representedObject() or "").strip()
            if not url:
                return
            open_url(url)
        except Exception as exc:
            log.warning("Failed to open extension link: %s", exc)

    def showClipboardPopover_(self, _sender):
        """Show the clipboard popover panel."""
        _ensure_frontend_running()
        # Open the canonical clipboard full-history surface page
        open_url("http://localhost:5175/system/s310")

    def selectClipboardItem_(self, sender):
        """Promote selected history item back into active system clipboard."""
        item_id = str(sender.representedObject() or "").strip()
        if not item_id:
            return

        recent: list[dict] = []
        if self._clipboard_snack:
            recent, _saved = self._clipboard_snack.get_items()

        selected = next(
            (item for item in recent if str(item.get("id") or "") == item_id),
            None,
        )
        if not selected:
            log.warning("Clipboard item not found in cached list: %s", item_id)
            return

        content = str(selected.get("content") or "")
        try:
            copy_text_to_clipboard(content)
            add_clipboard_item(
                source="menu-select",
                type=str(selected.get("type") or "text"),
                content=content,
                metadata={"selected_item_id": item_id},
            )
            log.info("Clipboard item promoted: %s", item_id)
        except Exception as exc:
            log.warning(
                "Failed to promote clipboard item %s: %s",
                item_id,
                exc,
            )

    def toggleStartAtLogin_(self, _sender):
        """Toggle start at login."""
        if self._start_at_login:
            uninstall_launchd()
        else:
            install_launchd()
        self._start_at_login = is_launchd_installed()
        self.performSelectorOnMainThread_withObject_waitUntilDone_(
            "updateUI:", None, False,
        )

    def restartBackend_(self, _sender):
        """Restart backend via popcorn lifecycle manager."""
        from app.services.popcorn_manager import perform_action

        result = perform_action("restart-backend")
        log.info("Restart backend: %s", result.get("message", result))
        self._connected = is_ucore_alive()
        self.performSelectorOnMainThread_withObject_waitUntilDone_(
            "updateUI:", None, False,
        )

    def restartFrontend_(self, _sender):
        """Restart frontend via popcorn lifecycle manager."""
        from app.services.popcorn_manager import perform_action

        result = perform_action("restart-frontend")
        log.info("Restart frontend: %s", result.get("message", result))
        self._uihub_connected = is_uihub_alive()
        self.performSelectorOnMainThread_withObject_waitUntilDone_(
            "updateUI:", None, False,
        )

    def restartMenu_(self, _sender):
        """Restart menu via popcorn lifecycle manager."""
        from app.services.popcorn_manager import perform_action

        result = perform_action("restart-menu")
        log.info("Restart menu: %s", result.get("message", result))

    def startDevMode_(self, _sender):
        """Enable uCore's built-in Developer surface."""
        log.info("Enabling built-in Developer surface")
        try:
            if is_ucore_alive():
                result = api_post_sync(
                    "/api/developer/start", timeout=8.0
                ) or {}
                if not result.get("success"):
                    log.warning(
                        "Backend dev start returned failure: %s", result
                    )
            else:
                log.warning("Backend unavailable; Developer surface cannot be enabled")
            time.sleep(1.5)
        except Exception as exc:
            log.error("Failed to start dev server: %s", exc)
        self._dev_connected = is_dev_alive()
        self.performSelectorOnMainThread_withObject_waitUntilDone_(
            "updateUI:", None, False,
        )

    def stopDevMode_(self, _sender):
        """Disable uCore's built-in Developer mode."""
        log.info("Disabling built-in Developer mode")
        try:
            if is_ucore_alive():
                api_post_sync("/api/developer/stop", timeout=5.0)
        except Exception as exc:
            log.error("Failed to stop dev server: %s", exc)
        self._dev_connected = is_dev_alive()
        self.performSelectorOnMainThread_withObject_waitUntilDone_(
            "updateUI:", None, False,
        )

    def toggleDevMode_(self, _sender):
        """Toggle uCore's built-in Developer mode.

        Single menu item shows the live status; clicking starts the
        server when stopped and stops it when running.
        """
        if is_dev_alive():
            self.stopDevMode_(None)
        else:
            self.startDevMode_(None)

    def quitApp_(self, _sender):
        """Quit cleanly; launchd restarts crashes, not successful exits."""
        log.info("Quitting uCore Menu")
        if self._refresh_timer:
            self._refresh_timer.cancel()
        if self._global_shortcut_monitor:
            from AppKit import NSEvent
            NSEvent.removeMonitor_(self._global_shortcut_monitor)
        release_lock()
        NSApplication.sharedApplication().terminate_(self)


# ─── Main ─────────────────────────────────────────────────────────────

def main():
    """Main entry point."""
    if not acquire_lock():
        print("Failed to acquire lock")
        return

    # Auto-start backend if not running
    if not is_ucore_alive():
        log.info("Backend not running, attempting auto-start...")
        ensure_backend_running()

    app = NSApplication.sharedApplication()

    # Hide from Dock — this is a menu bar app only
    app.setActivationPolicy_(1)  # NSApplicationActivationPolicyAccessory
    app.activateIgnoringOtherApps_(True)

    # Set the process name for Activity Monitor
    from Foundation import NSProcessInfo
    NSProcessInfo.processInfo().setProcessName_("uCore Menu")

    delegate = UnifiedMenuDelegate.alloc().init()
    delegate.setupStatusBar()

    NSApp().setDelegate_(delegate)
    AppHelper.runEventLoop()


if __name__ == "__main__":
    main()
