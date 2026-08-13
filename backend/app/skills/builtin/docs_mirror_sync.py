"""docs_mirror_sync — pull uDos component docs into the readable mirror."""
from __future__ import annotations

from app.skills.base import BaseSkill, SkillMeta


class DocsMirrorSync(BaseSkill):
    meta = SkillMeta(
        id="docs_mirror_sync",
        name="Docs Mirror Sync",
        description=(
            "Pull uDos component docs from in-repo docs/ directories "
            "into the readable docs mirror."
        ),
        category="maintenance",
        timeout=180,
    )

    async def run(self, **kwargs) -> dict:
        from app.services.docs_mirror import sync_from_repos

        return sync_from_repos()
