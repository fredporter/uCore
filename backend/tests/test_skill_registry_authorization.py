from app.skills import registry
from app.skills.base import BaseSkill, SkillMeta


class _DestructiveSkill(BaseSkill):
    meta = SkillMeta(
        id="test-destructive",
        name="Test destructive",
        category="destructive",
    )

    async def run(self, **kwargs) -> dict:
        return {"success": True}


async def test_core_registry_blocks_unauthorized_destructive_execution(monkeypatch):
    monkeypatch.setattr(registry, "get_skill", lambda _skill_id: _DestructiveSkill())

    result = await registry.run_skill_by_id("test-destructive")

    assert result["success"] is False
    assert result["requires_confirmation"] is True


async def test_core_registry_runs_destructive_skill_after_authorization(monkeypatch):
    monkeypatch.setattr(registry, "get_skill", lambda _skill_id: _DestructiveSkill())

    result = await registry.run_skill_by_id(
        "test-destructive",
        execution_authorized=True,
    )

    assert result == {"success": True}
