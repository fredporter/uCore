"""Maintained integration recommendations, tied to actual host capabilities."""

import platform


def catalog():
    host = {"Darwin": "macos", "Linux": "linux", "Windows": "windows"}.get(
        platform.system(), "other"
    )
    apps = [
        {
            "id": "macos-apps",
            "name": "macOS local apps",
            "platforms": ["macos"],
            "points": ["Contacts", "Calendar", "Mail", "Reminders", "Notes"],
            "mode": "native-bridge",
            "available": True,
            "description": "Use Internet Accounts for Apple and Google accounts. macOS owns account authentication and cloud sync.",
            "url": "https://support.apple.com/guide/mac-help/mh35705/mac",
        },
        {
            "id": "evolution",
            "name": "Evolution + GNOME Online Accounts",
            "platforms": ["linux"],
            "points": ["Contacts", "Calendar", "Tasks", "Mail"],
            "mode": "app-managed-sync",
            "available": False,
            "description": "Recommended Linux account hub. The app handles Google/CalDAV/CardDAV sync. A live Evolution Data Server bridge is not implemented in uDOS yet.",
            "url": "https://apps.gnome.org/Evolution/",
        },
        {
            "id": "thunderbird",
            "name": "Thunderbird",
            "platforms": ["linux", "windows", "macos"],
            "points": ["Mail", "Contacts", "Calendar"],
            "mode": "app-managed-sync",
            "available": False,
            "description": "Alternative local mail and calendar app. uDOS does not yet have a live Thunderbird bridge.",
            "url": "https://www.thunderbird.net/",
        },
        {
            "id": "safari",
            "name": "Safari",
            "platforms": ["macos"],
            "points": ["Bookmarks", "Favourites", "Reading List"],
            "mode": "html-import-export",
            "available": True,
            "description": "Import an exported Bookmarks.html, including Reading List. Export local links for manual browser import. Safari manages iCloud sync.",
            "url": "https://support.apple.com/guide/safari/ibrwebf10132/mac",
        },
        {
            "id": "firefox",
            "name": "Firefox",
            "platforms": ["linux", "windows", "macos"],
            "points": ["Bookmarks"],
            "mode": "html-import-export",
            "available": True,
            "description": "Use a bookmark HTML export. Firefox manages its own account sync.",
            "url": "https://www.mozilla.org/firefox/new/",
        },
        {
            "id": "chrome",
            "name": "Chrome",
            "platforms": ["linux", "windows", "macos"],
            "points": ["Bookmarks"],
            "mode": "html-import-export",
            "available": True,
            "description": "Use a bookmark HTML export. Chrome manages its own Google account sync; Reading List export coverage differs.",
            "url": "https://www.google.com/chrome/",
        },
        {
            "id": "drive",
            "name": "Google Drive for desktop",
            "platforms": ["macos", "windows"],
            "points": ["Files"],
            "mode": "folder-workflow",
            "available": False,
            "description": "Optional app-managed file mirroring. Choose files available offline; .gdoc/.gsheet shortcuts are not full document content. A dedicated folder connector is not implemented yet.",
            "url": "https://www.google.com/drive/download/",
        },
    ]
    return {
        "platform": host,
        "reviewed": "2026-11-09",
        "coordinator": "snackbar",
        "apps": [a for a in apps if host in a["platforms"]],
    }
