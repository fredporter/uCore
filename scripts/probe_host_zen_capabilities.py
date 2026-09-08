#!/usr/bin/env python3
"""Probe host-native and ecosystem capabilities aligned with the Zen Ecosystem Contract.

Sprint 4 Scopes 8-9 & Zen Contract:
- Reuse before construction: Host OS -> Ecosystem -> Vendor -> custom code.
- Discover macOS (Safari, Notes, Reminders, Mail, Messages, say, notifications)
  or Linux (Firefox/Zen Browser, notify-send, Secret Service).
- Output machine-readable JSON inventory of discovered capabilities and status.
"""

from __future__ import annotations

import argparse
import json
import os
import platform
import shutil
import subprocess
import sys
from typing import Any, Dict


def probe_macos_apps() -> Dict[str, Dict[str, Any]]:
    apps = {
        "safari": "Safari",
        "notes": "Notes",
        "reminders": "Reminders",
        "mail": "Mail",
        "messages": "Messages",
    }
    results = {}
    for key, app_name in apps.items():
        try:
            res = subprocess.run(
                ["osascript", "-e", f'id of application "{app_name}"'],
                capture_output=True,
                text=True,
                timeout=2.0,
            )
            if res.returncode == 0:
                bundle_id = res.stdout.strip()
                results[key] = {
                    "available": True,
                    "bundle_id": bundle_id,
                    "adapter": f"macos_osascript_{key}",
                    "automation": "supported",
                }
            else:
                results[key] = {
                    "available": False,
                    "error": res.stderr.strip(),
                    "adapter": None,
                    "automation": "unavailable",
                }
        except Exception as exc:
            results[key] = {
                "available": False,
                "error": str(exc),
                "adapter": None,
                "automation": "error",
            }
    return results


def probe_host_capabilities() -> Dict[str, Any]:
    os_name = platform.system().lower()
    report: Dict[str, Any] = {
        "os": os_name,
        "platform": platform.platform(),
        "reuse_hierarchy": [
            "1. Host OS Native Capability",
            "2. Ecosystem Service (uCore/uFlow/uKnowledge)",
            "3. Reviewed Vendor Component",
            "4. Minimal Custom Integration Code",
        ],
        "host_native": {},
        "vendor_extensions": {},
    }

    if os_name == "darwin":
        macos_apps = probe_macos_apps()
        report["host_native"]["browser"] = {
            "preferred": "Safari",
            "detected": macos_apps.get("safari", {}).get("available", False),
            "bundle_id": macos_apps.get("safari", {}).get("bundle_id"),
            "strategy": "native_apple_events",
        }
        report["host_native"]["pim_exchange"] = {
            "notes": macos_apps.get("notes"),
            "reminders": macos_apps.get("reminders"),
            "mail": macos_apps.get("mail"),
            "messages": macos_apps.get("messages"),
        }
        report["host_native"]["speech"] = {
            "say_cli": shutil.which("say") is not None,
            "path": shutil.which("say"),
            "strategy": "host_tts",
        }
        report["host_native"]["notifications"] = {
            "available": True,
            "strategy": "osascript_display_notification",
        }
    else:
        # Linux fallback detection
        has_firefox = shutil.which("firefox") is not None
        has_zen = shutil.which("zen-browser") is not None or shutil.which("zen") is not None
        report["host_native"]["browser"] = {
            "preferred": "Zen Browser / Managed Firefox",
            "firefox_detected": has_firefox,
            "zen_detected": has_zen,
            "strategy": "managed_profile" if (has_zen or has_firefox) else "missing",
        }
        report["host_native"]["notifications"] = {
            "available": shutil.which("notify-send") is not None,
            "strategy": "notify-send" if shutil.which("notify-send") else "missing",
        }
        report["host_native"]["speech"] = {
            "spd_say": shutil.which("spd-say") is not None,
            "strategy": "speech-dispatcher" if shutil.which("spd-say") else "missing",
        }

    # Google / Frontier Extensions
    key = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
    report["vendor_extensions"]["google_ai_studio"] = {
        "frontier_tier": "gemini-2.0-flash / imagen-3.0-generate-002",
        "key_configured": bool(key),
        "grounded_search": True,
        "nano_banana_image_gen": True,
    }

    return report


def main() -> int:
    parser = argparse.ArgumentParser(description="Probe Zen Host and Ecosystem Capabilities")
    parser.add_argument("--json", action="store_true", help="Output JSON (the default; retained for CLI compatibility)")
    parser.parse_args()

    data = probe_host_capabilities()
    print(json.dumps(data, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
