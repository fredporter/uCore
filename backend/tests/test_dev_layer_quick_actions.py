from app.api.dev_layer_api import _QUICK_ACTIONS


def test_dev_hud_only_exposes_read_only_working_quick_actions():
    assert _QUICK_ACTIONS == [
        {
            "id": "system-health",
            "label": "System Health Check",
            "icon": "favorite",
            "method": "GET",
            "path": "/api/health/full",
        },
    ]
