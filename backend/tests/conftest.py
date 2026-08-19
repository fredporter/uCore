"""uCore test configuration."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

# Ensure backend/ is on sys.path so `from app import ...` works
BACKEND_DIR = Path(__file__).resolve().parent.parent
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))


@pytest.fixture(scope="session", autouse=True)
def register_test_hello_world_skill():
    """Provide the documented hello-world API fixture without shipping it."""
    from app.skills import registry
    from app.skills.base import BaseSkill, SkillMeta, SkillParam

    class HelloWorldTestSkill(BaseSkill):
        meta = SkillMeta(
            id="hello-world",
            name="Hello World test fixture",
            category="general",
            params=[SkillParam(name="name", required=False, default="World")],
        )

        async def run(self, **kwargs) -> dict:
            return {
                "success": True,
                "message": f"Hello, {kwargs.get('name', 'World')}!",
            }

    previous_registry = registry._registry
    previous_loaded = registry._loaded
    registry._registry = registry._discover()
    registry._registry["hello-world"] = HelloWorldTestSkill()
    registry._loaded = True
    yield
    registry._registry = previous_registry
    registry._loaded = previous_loaded
