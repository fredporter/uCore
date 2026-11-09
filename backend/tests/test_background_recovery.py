"""Recovery and resource bounds for existing uCore background services."""

import asyncio
from datetime import datetime, timedelta

import pytest

from app.services import maintenance_scheduler as maintenance
from app.services.research_queue import ResearchQueue


@pytest.mark.asyncio
async def test_research_serializes_manual_and_background_work(tmp_path, monkeypatch):
    queue = ResearchQueue(tmp_path / "queue.db")
    first = await queue.enqueue("https://example.com/one")
    second = await queue.enqueue("https://example.com/two")
    active = peak = 0

    async def process(job_id):
        nonlocal active, peak
        active += 1
        peak = max(peak, active)
        await asyncio.sleep(0)
        await queue.update_state(job_id, "completed", 100)
        active -= 1
        return queue._refetch(job_id)

    monkeypatch.setattr(queue, "_process_job", process)
    await asyncio.gather(queue.process_job(first), queue.process_job(second))
    assert peak == 1
    await queue.stop()


@pytest.mark.asyncio
async def test_research_worker_resumes_without_client(tmp_path, monkeypatch):
    path = tmp_path / "queue.db"
    queue = ResearchQueue(path)
    job_id = await queue.enqueue("https://example.com")
    await queue.update_state(job_id, "summarising", 40)
    await queue.stop()
    queue = ResearchQueue(path)
    finished = asyncio.Event()

    async def process(job_id):
        await queue.update_state(job_id, "completed", 100)
        finished.set()
        return queue._refetch(job_id)

    monkeypatch.setattr(queue, "_process_job", process)
    await queue.start()
    await asyncio.wait_for(finished.wait(), timeout=1)
    assert (await queue.status(job_id))["state"] == "completed"
    await queue.stop()


@pytest.mark.asyncio
async def test_research_retry_bound_and_destination(tmp_path):
    queue = ResearchQueue(tmp_path / "queue.db")
    with pytest.raises(ValueError):
        await queue.enqueue("https://example.com", binder="../Shared")
    job = await queue.enqueue("https://example.com")
    queue._conn.execute("UPDATE jobs SET attempts=1 WHERE id=?", (job,))
    await queue._retry_or_fail(job, "temporary", retryable=True)
    assert (await queue.status(job))["retry_at"]
    queue._conn.execute("UPDATE jobs SET attempts=3 WHERE id=?", (job,))
    await queue._retry_or_fail(job, "temporary", retryable=True)
    assert (await queue.status(job))["state"] == "failed"
    await queue.stop()


@pytest.mark.asyncio
async def test_maintenance_failure_does_not_block_later_jobs(tmp_path, monkeypatch):
    calls = []

    async def run(skill_id, **kwargs):
        calls.append(skill_id)
        if skill_id == "fails":
            raise RuntimeError("temporary")
        return {"success": True}

    monkeypatch.setattr(maintenance, "run_skill_by_id", run)
    scheduler = maintenance.MaintenanceScheduler(
        state_path=tmp_path / "state.json",
        jobs=(
            maintenance.MaintenanceJob("fails", "00:00", {}, retry_safe=True),
            maintenance.MaintenanceJob("works", "00:00", {}),
        ),
    )
    now = datetime(2026, 11, 8, 10)
    await scheduler.run_due(now)
    assert calls == ["fails", "works"]
    await scheduler.run_due(now)
    assert calls == ["fails", "works"]
    await scheduler.run_due(now + timedelta(minutes=1))
    await scheduler.run_due(now + timedelta(minutes=3))
    await scheduler.run_due(now + timedelta(minutes=9))
    assert calls.count("fails") == 3
    assert scheduler.status()["jobs"][0]["last_result"]["state"] == "failed"


@pytest.mark.asyncio
async def test_maintenance_timeout_and_approval_are_actionable(tmp_path, monkeypatch):
    async def run(skill_id, **kwargs):
        if skill_id == "hangs":
            await asyncio.Event().wait()
        return {"success": False, "requires_confirmation": True, "error": "Review required"}

    monkeypatch.setattr(maintenance, "run_skill_by_id", run)
    scheduler = maintenance.MaintenanceScheduler(
        state_path=tmp_path / "state.json",
        jobs=(
            maintenance.MaintenanceJob("hangs", "00:00", {}, timeout_seconds=0.01),
            maintenance.MaintenanceJob("approval", "00:00", {}, retry_safe=True),
        ),
    )
    await scheduler.run_due(datetime(2026, 11, 8, 10))
    jobs = scheduler.status()["jobs"]
    assert jobs[0]["last_result"]["state"] == "failed"
    assert jobs[1]["last_result"]["state"] == "needs_approval"
    assert not jobs[1]["last_result"]["next_retry"]


@pytest.mark.asyncio
async def test_research_claim_is_not_repeated(tmp_path, monkeypatch):
    queue = ResearchQueue(tmp_path / "queue.db")
    job_id = await queue.enqueue("https://example.com")
    # Terminal jobs cannot be claimed or executed again.
    await queue.update_state(job_id, "completed", 100)
    result = await queue.process_job(job_id)
    assert result["state"] == "completed"
    assert result["attempts"] == 0
    await queue.stop()


def test_research_recovered_save_preserves_document_and_citation(tmp_path, monkeypatch):
    from pathlib import Path
    from types import SimpleNamespace

    monkeypatch.setattr(Path, "home", lambda: tmp_path)
    job = SimpleNamespace(id="stable-id", binder="research", url="https://example.com", tags=[])
    result = ResearchQueue._save_document(job, "A title", "", "First summary")
    document = Path(result["file"])
    document.write_text("Personal edits", encoding="utf-8")
    ResearchQueue._save_document(job, "A title", "", "Repeated summary")
    assert document.read_text() == "Personal edits"
    assert (document.parent / "CITATIONS.md").read_text().count("job stable-id") == 1


@pytest.mark.asyncio
async def test_cancel_active_job_does_not_stop_worker(tmp_path, monkeypatch):
    queue = ResearchQueue(tmp_path / "queue.db")
    job_id = await queue.enqueue("https://example.com")
    started = asyncio.Event()

    async def process(job_id):
        await queue.update_state(job_id, "scraping", 10)
        started.set()
        await asyncio.Event().wait()

    monkeypatch.setattr(queue, "_process_job", process)
    await queue.start()
    await asyncio.wait_for(started.wait(), timeout=1)
    await queue.cancel(job_id)
    await asyncio.sleep(0)
    assert (await queue.status(job_id))["state"] == "cancelled"
    assert queue.summary()["running"]
    await queue.stop()


@pytest.mark.asyncio
async def test_task_body_save_and_clear_survive_reload(tmp_path):
    from pathlib import Path

    from app.api.tasker_api import _parse_markdown_task, _update_task_file
    from app.services.tasker_ops import write_task_markdown

    created = write_task_markdown(
        title="Editor save",
        board="inbox",
        status="todo",
        body="Original",
        tasker_dir=str(tmp_path),
        source="manual",
        source_id="save-test",
    )
    task = _parse_markdown_task(Path(created["path"]))
    updated = _update_task_file(base=tmp_path, task_id=task["id"], patch={"body": "Updated body"})
    assert _parse_markdown_task(Path(updated["path"]))["body"] == "Updated body"
    cleared = _update_task_file(base=tmp_path, task_id=updated["updated"]["id"], patch={"body": ""})
    assert _parse_markdown_task(Path(cleared["path"]))["body"] == ""


@pytest.mark.asyncio
async def test_manual_retry_reuses_identity_and_clears_terminal_state(tmp_path):
    queue = ResearchQueue(tmp_path / "queue.db")
    job = await queue.enqueue("https://example.com")
    await queue.update_state(job, "failed", error="Unavailable")
    result = await queue.retry(job)
    assert result["id"] == job
    assert result["state"] == "pending"
    assert result["completed"] is None
    assert result["error"] is None
    with pytest.raises(ValueError):
        await queue.retry(job)
    await queue.stop()


@pytest.mark.asyncio
async def test_filesystem_sync_keeps_event_loop_responsive_and_single_flight(monkeypatch):
    import threading

    from app.services import docs_mirror
    from app.skills.builtin import docs_mirror_sync as skill

    release = threading.Event()
    calls = []

    def sync():
        calls.append(1)
        release.wait(timeout=2)
        return {"success": True}

    monkeypatch.setattr(skill, "_mirror_work", None)
    monkeypatch.setattr(docs_mirror, "sync_from_repos", sync)
    first = asyncio.create_task(skill.DocsMirrorSync().run())
    second = asyncio.create_task(skill.DocsMirrorSync().run())
    try:
        # This runs while the filesystem operation is still waiting in its thread.
        await asyncio.sleep(0.01)
        assert not first.done()
        assert len(calls) == 1
    finally:
        release.set()
        await asyncio.gather(first, second)


@pytest.mark.asyncio
async def test_research_gaps_exclude_runtime_and_unconfigured_folders(tmp_path, monkeypatch):
    import json
    from pathlib import Path

    from aiohttp.test_utils import make_mocked_request

    from app.api.research_api import handle_vault_scan

    monkeypatch.setattr(Path, "home", lambda: tmp_path)
    vault = tmp_path / "Vault"
    for name in (".obsidian", "attachments", "research"):
        (vault / name).mkdir(parents=True)
    (vault / "research" / "binder.json").write_text(json.dumps({"score": 1}))
    response = await handle_vault_scan(make_mocked_request("GET", "/api/research/vault-scan"))
    assert [gap["topic"] for gap in json.loads(response.text)["gaps"]] == ["research"]
