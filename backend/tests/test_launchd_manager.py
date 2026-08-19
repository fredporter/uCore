import plistlib
from pathlib import Path

from app.menu.launchd_manager import UDOS_HOME, get_frontend_plist_content, get_plist_content


def test_menu_restarts_crashes_but_respects_clean_quit():
    plist = plistlib.loads(get_plist_content().encode())

    assert plist["RunAtLoad"] is True
    assert plist["KeepAlive"] == {"SuccessfulExit": False}
    assert plist["EnvironmentVariables"]["UDOS_HOME"] == str(UDOS_HOME)
    assert Path(plist["StandardOutPath"]).is_relative_to(UDOS_HOME)


def test_frontend_uses_canonical_runtime_home():
    plist = plistlib.loads(get_frontend_plist_content().encode())

    assert plist["EnvironmentVariables"]["UDOS_HOME"] == str(UDOS_HOME)
    assert Path(plist["StandardOutPath"]).is_relative_to(UDOS_HOME)
