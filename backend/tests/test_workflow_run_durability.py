"""Gate A step 3 (first milestone): durable admission and restart recovery."""


def _manager(tmp_path, monkeypatch):
    from app.core.settings import settings
    from app.services.workflow_manager import WorkflowManager

    monkeypatch.setattr(settings, "data_dir", tmp_path)
    manager = WorkflowManager()
    # Pin the store to this test's directory; other modules may have changed the
    # process-wide data_dir before this test runs.
    manager._db_path = tmp_path / "workflows.db"
    manager._init_db()
    return manager


def test_admitted_run_is_durable_before_completion(tmp_path, monkeypatch):
    manager = _manager(tmp_path, monkeypatch)
    manager.start_run(
        run_id="run-1",
        workflow_id="wf-1",
        workflow_name="Workflow",
        started_at="t0",
        owner="alice",
    )

    rows = manager.get_all_runs(owner="alice")

    assert [row["run_id"] for row in rows] == ["run-1"]
    assert rows[0]["status"] == "running"
    assert rows[0]["finished_at"] == ""


def test_completion_updates_the_admitted_row(tmp_path, monkeypatch):
    manager = _manager(tmp_path, monkeypatch)
    manager.start_run(
        run_id="run-1",
        workflow_id="wf-1",
        workflow_name="Workflow",
        started_at="t0",
        owner="alice",
    )
    manager.save_run(
        run_id="run-1",
        workflow_id="wf-1",
        workflow_name="Workflow",
        started_at="t0",
        finished_at="t1",
        status="completed",
        steps=[{"index": 1}],
        owner="alice",
    )

    rows = manager.get_all_runs(owner="alice")

    assert len(rows) == 1
    assert rows[0]["status"] == "completed"
    assert rows[0]["finished_at"] == "t1"
    assert rows[0]["steps"] == [{"index": 1}]


def test_recovery_marks_only_running_runs(tmp_path, monkeypatch):
    manager = _manager(tmp_path, monkeypatch)
    manager.start_run(
        run_id="run-live",
        workflow_id="wf-1",
        workflow_name="Workflow",
        started_at="t0",
        owner="alice",
    )
    manager.save_run(
        run_id="run-done",
        workflow_id="wf-1",
        workflow_name="Workflow",
        started_at="t0",
        finished_at="t1",
        status="completed",
        steps=[],
        owner="alice",
    )

    assert manager.recover_interrupted_runs(now="t2") == 1

    statuses = {row["run_id"]: row["status"] for row in manager.get_all_runs()}
    assert statuses == {"run-live": "interrupted", "run-done": "completed"}


def test_recovery_is_idempotent(tmp_path, monkeypatch):
    manager = _manager(tmp_path, monkeypatch)
    manager.start_run(
        run_id="run-live",
        workflow_id="wf-1",
        workflow_name="Workflow",
        started_at="t0",
        owner="alice",
    )

    assert manager.recover_interrupted_runs(now="t2") == 1
    assert manager.recover_interrupted_runs(now="t3") == 0
