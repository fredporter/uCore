"""Layer 0 canon must be read-only for runtime code."""
from __future__ import annotations

import json
import sys
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest
from aiohttp.test_utils import make_mocked_request

from app.core.canon_guard import (
    CanonWriteDenied,
    assert_writable,
    find_element_asset,
    generated_elements_dir,
    is_canon_path,
)
from app.core.settings import settings


def test_canon_path_detection(tmp_path, monkeypatch):
    canon = tmp_path / "canon"
    canon.mkdir()
    monkeypatch.setenv("UDOS_CANON_ROOT", str(canon))

    assert is_canon_path(canon)
    assert is_canon_path(canon / "elements" / "x.gif")
    assert not is_canon_path(tmp_path / "other")


def test_assert_writable_denies_canon(tmp_path, monkeypatch):
    canon = tmp_path / "canon"
    canon.mkdir()
    monkeypatch.setenv("UDOS_CANON_ROOT", str(canon))

    with pytest.raises(CanonWriteDenied):
        assert_writable(canon / "elements" / "new.gif")

    outside = tmp_path / "udos" / "assets" / "x.gif"
    assert assert_writable(outside) == outside.resolve()


def test_generated_assets_live_under_udos_home(tmp_path, monkeypatch):
    monkeypatch.setattr(settings, "udos_home", tmp_path / "udos")

    directory = generated_elements_dir()

    assert str(directory).startswith(str((tmp_path / "udos").resolve()))
    assert not is_canon_path(directory)


def test_generated_asset_is_found_before_canon(tmp_path, monkeypatch):
    canon = tmp_path / "canon"
    (canon / "elements").mkdir(parents=True)
    (canon / "elements" / "shared.gif").write_bytes(b"canon")
    generated = tmp_path / "udos" / "assets" / "elements"
    generated.mkdir(parents=True)
    (generated / "shared.gif").write_bytes(b"generated")

    monkeypatch.setenv("UDOS_CANON_ROOT", str(canon))
    monkeypatch.setattr(settings, "udos_home", tmp_path / "udos")

    found = find_element_asset("shared.gif")

    assert found is not None
    assert found.read_bytes() == b"generated"


@pytest.mark.asyncio
async def test_bob_generation_writes_outside_canon(tmp_path, monkeypatch):
    from app.api import dispatch_api

    canon = tmp_path / "canon"
    (canon / "elements").mkdir(parents=True)
    monkeypatch.setenv("UDOS_CANON_ROOT", str(canon))
    monkeypatch.setattr(settings, "udos_home", tmp_path / "udos")

    fake = SimpleNamespace(
        generate_vector_motif=lambda *_args, **_kwargs: [{"svg": "x"}],
        compile_svgs_to_gif=lambda *_args, **_kwargs: b"GIF89a",
        compile_svg_to_bob=lambda *_args, **_kwargs: {"id": "bob_zen_envelope"},
    )
    sys.modules["app.services.uvector_bob"] = fake
    try:
        request = make_mocked_request("POST", "/api/dispatch/generate-bob")
        request.json = AsyncMock(
            return_value={"motif": "zen_envelope", "palette_id": "teletext_ceefax"}
        )
        response = await dispatch_api.handle_generate_bob(request)
    finally:
        sys.modules.pop("app.services.uvector_bob", None)

    payload = json.loads(response.text)

    assert response.status == 200
    assert (tmp_path / "udos" / "assets" / "elements" / payload["asset_name"]).is_file()
    assert list((canon / "elements").iterdir()) == []
