"""docs_mirror_sync — pull uDos component docs into the readable mirror."""

from __future__ import annotations

import asyncio

from app.skills.base import BaseSkill, SkillMeta

_mirror_work: asyncio.Task | None = None


class DocsMirrorSync(BaseSkill):
    meta = SkillMeta(
        id="docs_mirror_sync",
        name="Docs Mirror Sync",
        description=(
            "Pull uDos component docs from in-repo docs/ directories into the readable docs mirror."
        ),
        category="maintenance",
        timeout=180,
    )

    async def run(self, **kwargs) -> dict:
        from app.services.docs_mirror import sync_from_repos

        global _mirror_work
        if _mirror_work is None or _mirror_work.done():
            _mirror_work = asyncio.create_task(asyncio.to_thread(sync_from_repos))
        # A timed-out caller does not spawn a second copy of the filesystem job.
        return await asyncio.shield(_mirror_work)
