"""Task lists/groups/binder membership use the same durable uFlow record."""
import json
from pathlib import Path
from unittest.mock import AsyncMock, Mock

import pytest
from aiohttp.test_utils import make_mocked_request

from app.api import tasker_api as api


def test_move_group_and_unlink_preserve_identity_and_content(tmp_path):
    created = api._create_workflow_task(tmp_path, {'title': 'Organize work', 'board': 'inbox', 'body': 'Keep this text'})['updated']
    updated = api._update_task_file(base=tmp_path, task_id=created['id'], patch={'board': 'week', 'binder': 'project', 'group': 'Next'})
    persisted = api._parse_markdown_task(Path(updated['path']))
    assert persisted['id'] == created['id']
    assert persisted['board'] == 'week'
    assert persisted['binder'] == 'project'
    assert persisted['group'] == 'Next'
    assert persisted['body'] == 'Keep this text'
    assert len(list(tmp_path.rglob('*.md'))) == 1
    updated = api._update_task_file(base=tmp_path, task_id=created['id'], patch={'binder': '', 'group': ''})
    assert not updated['updated'].get('binder')
    assert not updated['updated'].get('group')


@pytest.mark.asyncio
async def test_copy_is_independent_and_does_not_copy_execution_authority(tmp_path, monkeypatch):
    monkeypatch.setattr(api, 'default_tasker_dir', lambda: tmp_path)
    original = api._create_workflow_task(tmp_path, {'title': 'Task', 'board': 'inbox', 'body': 'Notes', 'binder': 'project'})['updated']
    api._update_task_file(base=tmp_path, task_id=original['id'], patch={'status': 'completed', 'action_type': 'shell', 'approval_status': 'executed'})
    request = make_mocked_request('POST', f"/api/workflow/tasks/{original['id']}/duplicate", match_info={'task_id': original['id']})
    request.json = AsyncMock(return_value={'board': 'later', 'group': 'Ideas'})
    # make_mocked_request has no body transport; provide an explicit JSON body.
    request._payload = Mock()
    request._payload.at_eof.return_value = False
    response = await api.handle_duplicate_workflow_task(request)
    assert response.status == 201
    copy = json.loads(response.text)['updated']
    assert copy['id'] != original['id']
    assert copy['status'] == 'todo'
    assert copy['board'] == 'later'
    assert copy['group'] == 'Ideas'
    assert copy['body'] == 'Notes'
    assert not copy.get('action_type')
    assert not copy.get('approval_status')
    assert len(list(tmp_path.rglob('*.md'))) == 2


def test_create_rejects_invalid_list_paths(tmp_path):
    with pytest.raises(ValueError):
        api._create_workflow_task(tmp_path, {'title': 'Unsafe', 'board': '../elsewhere'})


@pytest.mark.asyncio
async def test_empty_list_is_durable_and_path_bounded(tmp_path, monkeypatch):
    monkeypatch.setattr(api, 'default_tasker_dir', lambda: tmp_path)
    request = make_mocked_request('POST', '/api/workflow/lists')
    request.json = AsyncMock(return_value={'name': 'Ideas'})
    response = await api.handle_create_workflow_list(request)
    assert response.status == 201
    assert (tmp_path / 'Ideas').is_dir()
    assert json.loads((tmp_path / 'Ideas' / 'list.json').read_text())['scope'] == 'user'
    assert (await api.handle_create_workflow_list(request)).status == 409
    request.json = AsyncMock(return_value={'name': '../escape'})
    assert (await api.handle_create_workflow_list(request)).status == 400


@pytest.mark.asyncio
async def test_existing_yaml_dates_do_not_break_task_list_response(tmp_path, monkeypatch):
    monkeypatch.setattr(api, 'default_tasker_dir', lambda: tmp_path)
    folder = tmp_path / 'inbox'
    folder.mkdir()
    (folder / 'todo.md').write_text('---\nid: dated-task\nsource: user\ncreated: 2026-11-09T01:00:00Z\ndue: 2026-11-10\n---\n# Existing task\n\nNotes\n')
    response = await api.handle_workflow_tasks(make_mocked_request('GET', '/api/workflow/tasks?scope=user'))
    assert response.status == 200
    task = json.loads(response.text)['tasks'][0]
    assert task['created'] == '2026-11-09T01:00:00+00:00'
    assert task['due'] == '2026-11-10'


@pytest.mark.asyncio
async def test_user_lists_hide_developer_lanes_but_keep_explicit_empty_lists(tmp_path, monkeypatch):
    monkeypatch.setattr(api, 'default_tasker_dir', lambda: tmp_path)
    for name in ('archive', 'review', 'inbox'):
        (tmp_path / name).mkdir()
    (tmp_path / 'review' / 'list.json').write_text('{"scope":"user"}')
    response = await api.handle_workflow_lists(make_mocked_request('GET', '/api/workflow/lists'))
    assert {board['name'] for board in json.loads(response.text)['boards']} == {'review', 'inbox'}


@pytest.mark.asyncio
async def test_workflow_patch_and_confirmation_pass_cors_preflight(monkeypatch):
    from app.core import snackbar
    monkeypatch.setattr(snackbar.settings, 'enable_cors', True)
    request = make_mocked_request('OPTIONS', '/api/workflow/tasks/task')
    response = await snackbar.cors_middleware(request, AsyncMock())
    assert 'PATCH' in response.headers['Access-Control-Allow-Methods']
    assert 'x-ucore-confirm' in response.headers['Access-Control-Allow-Headers']


def test_binder_only_move_keeps_imported_storage_provenance_and_markdown(tmp_path):
    folder = tmp_path / 'apple-family'
    folder.mkdir()
    path = folder / 'todo-plan.md'
    body = '\n# Plan\n\n## Sources\n\n- [Original](https://example.com)\n- Keep list formatting\n\n```basic\nPRINT 90\n```\n'
    path.write_text('---\nid: stable-task\nsource: user-connection\nsource_id: remote-42\ncollection_id: local-42\nprofile: default\ncreated: 2026-11-09T01:00:00Z\nprovider_metadata:\n  list: Family\n  etag: revision-7\nbinder: old-project\n---\n' + body)
    changed = api._update_task_file(base=tmp_path, task_id='stable-task', patch={'binder': 'garden'})
    reloaded = api._parse_markdown_task(Path(changed['path']))
    assert Path(changed['path']).parent == folder
    assert reloaded['id'] == 'stable-task'
    assert reloaded['binder'] == 'garden'
    assert reloaded['board'] == 'apple-family'
    assert reloaded['source_id'] == 'remote-42'
    assert reloaded['collection_id'] == 'local-42'
    assert reloaded['provider_metadata'] == {'list': 'Family', 'etag': 'revision-7'}
    assert '2026-11-09' in str(reloaded['created'])
    _, saved_body = api._parse_frontmatter(Path(changed['path']).read_text())
    assert saved_body.strip() == body.strip()
    assert len(list(tmp_path.rglob('*.md'))) == 1


def test_unlink_clears_legacy_notebook_membership_without_erasing_the_note(tmp_path):
    folder = tmp_path / 'inbox'
    folder.mkdir()
    path = folder / 'legacy.md'
    path.write_text('---\nid: legacy\nsource: user\nnotebook: garden\n---\n\n# Legacy\n\n- Keep this list\n')
    changed = api._update_task_file(base=tmp_path, task_id='legacy', patch={'binder': ''})
    reloaded = api._parse_markdown_task(Path(changed['path']))
    assert not reloaded.get('binder')
    assert '- Keep this list' in Path(changed['path']).read_text()
