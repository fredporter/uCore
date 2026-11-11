"""Objectives persist independently of Binders in the existing uFlow database."""
import json
from unittest.mock import AsyncMock

import pytest
from aiohttp.test_utils import make_mocked_request

from app.core.settings import settings
from app.services.workflow_manager import WorkflowManager


def test_mission_persistence_profile_isolation_and_archive(tmp_path, monkeypatch):
    monkeypatch.setattr(settings, 'data_dir', tmp_path)
    manager = WorkflowManager()
    mission = manager.create_mission('alice', 'Prepare a garden plan')
    assert list(tmp_path.glob('*.db')) == [tmp_path / 'workflows.db']
    reloaded = WorkflowManager().list_missions('alice')[0]
    assert reloaded['id'] == mission['id']
    assert reloaded['binder'] == ''
    assert WorkflowManager().list_missions('bob') == []
    with pytest.raises(KeyError):
        manager.update_mission('bob', mission['id'], {'status': 'completed'})
    changed = manager.update_mission('alice', mission['id'], {'binder': 'garden', 'status': 'completed'})
    assert changed['id'] == mission['id']
    assert changed['status'] == 'completed'
    assert manager.update_mission('alice', mission['id'], {'status': 'archived'})['status'] == 'archived'
    with pytest.raises(ValueError):
        manager.create_mission('alice', ' ')


@pytest.mark.asyncio
async def test_mission_api_uses_active_profile_and_reports_invalid_link(tmp_path, monkeypatch):
    from app.flow import binder_engine
    from app.flow.workflow_api import handle_user_missions
    from app.services import identity
    monkeypatch.setattr(settings, 'data_dir', tmp_path)
    monkeypatch.setattr(identity, 'get_full_identity', lambda: {'active_profile_id': 'alice'})
    monkeypatch.setattr(binder_engine, 'BINDERS_ROOT', tmp_path / 'Binders')
    request = make_mocked_request('POST', '/api/workflow/missions')
    request.json = AsyncMock(return_value={'title': 'Read about local history', 'profile': 'bob'})
    response = await handle_user_missions(request)
    assert response.status == 201
    mission = json.loads(response.text)['mission']
    assert mission['profile'] == 'alice'
    request.json = AsyncMock(return_value={'title': 'A mission', 'binder': 'missing'})
    assert (await handle_user_missions(request)).status == 404
    request.json = AsyncMock(return_value={'title': 'A mission', 'binder': True})
    assert (await handle_user_missions(request)).status == 400
