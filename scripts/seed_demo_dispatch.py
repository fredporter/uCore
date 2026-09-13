#!/usr/bin/env python3
"""Seed a reference interactive dispatch showcase for Project Odyssey in uCore."""
import json
import sys
from pathlib import Path

# Add backend to sys.path
backend_dir = Path(__file__).resolve().parent.parent / "backend"
sys.path.insert(0, str(backend_dir))

from app.core.settings import settings
from app.services.dispatch_store import dispatch_store

DEMO_BINDER_ID = "project-odyssey"
DEMO_TITLE = "Project Odyssey: Sovereign Demonstration & Invitation"
DEMO_LEAD = "A calm, zero-surveillance invitation powered by uDos Prose and GridCore."

DEMO_MARKDOWN = """# Welcome to Project Odyssey
A universal, calm operating system designed for human agency. No surveillance tracking pixels, no cookie banners, and zero third-party telemetry.

---

## 1. The Tri-Mode Zen Experience
Experience information without distraction:
- **Card Mode**: Focus on one thought at a time in a calibrated viewport.
- **Deck Mode**: 10-foot TV lean-back slide presentation.
- **Prose Mode**: Distraction-free continuous reading clamped strictly to a 72ch golden measure.

? [ ] I prefer focused card steps
? [ ] I prefer 10-foot slide decks
? [ ] I prefer long-form continuous prose

---

## 2. Universal Hardware Revival
Older Intel machines, CRT monitors, and POS kiosks revive into sovereign nodes via Sonic Screwdriver bootable flash drives.

? [ ] Attending in person at Sovereign Hub
? [ ] Attending remotely via Teletext Mode 7 portal
? [ ] Sending blessings from afar

---

## 3. Confirm Your Sovereign Attendance
Please leave your name and sovereign handle for the binder ledger:

? (Your Name / Handle): [text]
? (Preferred Hardware): [text]

Thank you for participating in the quiet computing revival.
"""


def main():
    print(f"[*] Ensuring demo binder '{DEMO_BINDER_ID}' exists...")
    binder_dir = settings.vault_root / "binders" / DEMO_BINDER_ID
    binder_dir.mkdir(parents=True, exist_ok=True)
    (binder_dir / "draft.md").write_text(DEMO_MARKDOWN, encoding="utf-8")
    manifest = {
        "id": DEMO_BINDER_ID,
        "title": "Project Odyssey",
        "outcome": "Demonstrate universal sovereign publishing, probing, and blitting across devices.",
        "audience": "Community Architects & Sovereign Users",
    }
    (binder_dir / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")

    print("[*] Staging interactive story dispatch...")
    dispatch = dispatch_store.create_dispatch(
        title=DEMO_TITLE,
        story_markdown=DEMO_MARKDOWN,
        lead_text=DEMO_LEAD,
        hero_gif_name="bob-teletext-pulse.gif",
        expires_in_seconds=7 * 86400,  # 7 days
        burn_after_read=False,
        mode_default="card",
        binder_id=DEMO_BINDER_ID,
    )

    token = dispatch["token"]
    dispatch_id = dispatch["id"]
    story_url = f"/p/{token}"
    email_url = f"/api/dispatch/preview-email/{dispatch_id}"

    print(f"[+] Dispatch created: {dispatch_id}")
    print(f"[+] Guest Story Token URL: {story_url}")
    print(f"[+] Prose HTML Email Preview URL: {email_url}")

    # Submit a sample RSVP response to demonstrate live ledger
    print("[*] Submitting sample RSVP response...")
    sample_rsvp = {
        "name": "Ada Lovelace",
        "email": "ada@analytical-engine.sovereign",
        "answers": {
            "I prefer focused card steps": True,
            "Attending in person at Sovereign Hub": True,
            "Your Name / Handle": "Ada Lovelace (@ada)",
            "Preferred Hardware": "Apple Silicon Mac M3 & Recycled POS Kiosk",
        },
        "notes": "Delighted to join the calm computing revival!",
    }
    res = dispatch_store.submit_rsvp(token, sample_rsvp)
    print(f"[+] RSVP Recorded: {res['status']}")

    responses = dispatch_store.get_responses(dispatch_id)
    print(f"[+] Current RSVP Ledger count: {len(responses)} submissions")
    print("\n[✓] Project Odyssey Interactive Showcase successfully seeded.")


if __name__ == "__main__":
    main()
