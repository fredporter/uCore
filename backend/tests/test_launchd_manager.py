import plistlib

from app.menu.launchd_manager import get_plist_content


def test_menu_restarts_crashes_but_respects_clean_quit():
    plist = plistlib.loads(get_plist_content().encode())

    assert plist["RunAtLoad"] is True
    assert plist["KeepAlive"] == {"SuccessfulExit": False}
