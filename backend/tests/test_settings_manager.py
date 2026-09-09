from pathlib import Path
from app.services.settings_manager import SettingsManager


def test_settings_manager_defaults(tmp_path: Path):
    target = tmp_path / "system_settings.json"
    mgr = SettingsManager(target)
    all_data = mgr.get_all()
    assert all_data["global"]["theme"] == "dark"
    assert all_data["user"]["displayName"] == "uDos Developer"
    assert target.exists()


def test_settings_manager_update_scope(tmp_path: Path):
    target = tmp_path / "system_settings.json"
    mgr = SettingsManager(target)
    updated = mgr.update_scope("global", {"theme": "light", "fontSize": 18})
    assert updated["global"]["theme"] == "light"
    assert updated["global"]["fontSize"] == 18

    # Reload from disk
    mgr2 = SettingsManager(target)
    assert mgr2.get_scope("global")["theme"] == "light"


def test_settings_manager_profile_isolation(tmp_path: Path):
    target = tmp_path / "system_settings.json"
    mgr = SettingsManager(target)

    # Set preferences for default profile
    mgr.update_user_preferences({"themeMode": "dark", "fontSize": 14}, profile_id="default")
    
    # Set preferences for Alice profile
    mgr.update_user_preferences({"themeMode": "light", "fontSize": 20}, profile_id="alice")

    default_prefs = mgr.get_user_preferences(profile_id="default")
    alice_prefs = mgr.get_user_preferences(profile_id="alice")

    assert default_prefs["themeMode"] == "dark"
    assert default_prefs["fontSize"] == 14
    assert alice_prefs["themeMode"] == "light"
    assert alice_prefs["fontSize"] == 20

    # User settings scope also reflects profile
    mgr.update_scope("user", {"displayName": "Alice Smith"}, profile_id="alice")
    alice_user = mgr.get_scope("user", profile_id="alice")
    default_user = mgr.get_scope("user", profile_id="default")

    assert alice_user["displayName"] == "Alice Smith"
    assert default_user["displayName"] == "uDos Developer"
