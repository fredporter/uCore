from app.skills.builtin.skill_cline_invoke import ClineInvokeSkill


async def test_cline_is_disabled_by_default(monkeypatch):
    monkeypatch.delenv("UCORE_ENABLE_CLINE", raising=False)

    result = await ClineInvokeSkill().run(task="Review this repository", mode="plan")

    assert result["success"] is False
    assert result["allowed_mode"] == "plan"


async def test_cline_rejects_yolo_even_when_enabled(monkeypatch):
    monkeypatch.setenv("UCORE_ENABLE_CLINE", "true")

    result = await ClineInvokeSkill().run(task="Change everything", mode="yolo")

    assert result["success"] is False
    assert "yolo" in result["error"]


async def test_cline_rejects_auto_approval_even_when_enabled(monkeypatch):
    monkeypatch.setenv("UCORE_ENABLE_CLINE", "true")

    result = await ClineInvokeSkill().run(
        task="Review this repository",
        mode="plan",
        auto_approve="true",
    )

    assert result["success"] is False
    assert "auto-approval" in result["error"]
