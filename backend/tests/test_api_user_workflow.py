"""API tests for user workflow endpoints and vault status."""
from __future__ import annotations

from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

from aiohttp import web
from aiohttp.test_utils import AioHTTPTestCase

import app.api.user_workflow as mod


class UserWorkflowApiTest(AioHTTPTestCase):
    async def get_application(self):
        app = web.Application()
        app.router.add_get(
            "/api/user/workflow/status",
            mod.handle_user_workflow_status,
        )
        app.router.add_post(
            "/api/user/workflow/archive",
            mod.handle_user_workflow_archive,
        )
        app.router.add_post(
            "/api/user/workflow/reset",
            mod.handle_user_workflow_reset,
        )
        app.router.add_post(
            "/api/user/workflow/import-markdown",
            mod.handle_user_workflow_import_markdown,
        )
        return app

    async def test_status_reports_vault_layers_and_no_appflowy(self):
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            tasker_dir = root / ".tasker"
            tasker_dir.mkdir(parents=True, exist_ok=True)

            with patch.object(
                mod,
                "default_tasker_dir",
                return_value=tasker_dir,
            ):
                resp = await self.client.get("/api/user/workflow/status")

            assert resp.status == 200
            payload = await resp.json()
            assert payload["source_of_truth"] == "markdown"
            assert "appflowy" not in payload
            assert payload["vault"]["layers"]

    async def test_archive_snapshots_tasker_without_appflowy(self):
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            logs_dir = root / "logs"
            data_dir = root / "data"
            tasker_dir = root / ".tasker"
            board_dir = tasker_dir / "inbox"
            board_dir.mkdir(parents=True, exist_ok=True)
            logs_dir.mkdir(parents=True, exist_ok=True)
            data_dir.mkdir(parents=True, exist_ok=True)
            (board_dir / "todo-sample.md").write_text(
                "# Sample\n\n- status: todo\n",
                encoding="utf-8",
            )

            with (
                patch.object(mod.settings, "logs_dir", logs_dir),
                patch.object(mod.settings, "data_dir", data_dir),
                patch.object(
                    mod,
                    "default_tasker_dir",
                    return_value=tasker_dir,
                ),
            ):
                resp = await self.client.post(
                    "/api/user/workflow/archive",
                    json={"reason": "test"},
                )

            assert resp.status == 200
            payload = await resp.json()
            archive = payload["archive"]
            assert archive["tasker"]["copied_files"] >= 1
            assert "appflowy_sidecar" not in archive

    async def test_reset_succeeds_and_seeds_without_appflowy(self):
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            logs_dir = root / "logs"
            data_dir = root / "data"
            tasker_dir = root / ".tasker"
            logs_dir.mkdir(parents=True, exist_ok=True)
            data_dir.mkdir(parents=True, exist_ok=True)

            class _StubManager:
                def create_workflow(self, **kwargs):
                    return {
                        "id": kwargs["workflow_id"],
                        "name": kwargs["name"],
                    }

            with (
                patch.object(mod.settings, "logs_dir", logs_dir),
                patch.object(mod.settings, "data_dir", data_dir),
                patch.object(
                    mod,
                    "default_tasker_dir",
                    return_value=tasker_dir,
                ),
                patch(
                    "app.services.workflow_manager.WorkflowManager",
                    return_value=_StubManager(),
                ),
            ):
                resp = await self.client.post(
                    "/api/user/workflow/reset",
                    json={"reason": "test-reset"},
                )

            assert resp.status == 200
            payload = await resp.json()
            assert payload["seed"]["tasks"]["created_count"] == 4
            assert payload["seed"]["workflows"]["created_count"] == 1
            assert "appflowy_sidecar" not in payload["cleared"]

            seeded_files = payload["seed"]["tasks"]["created"]
            assert len(seeded_files) == 4
            for path_str in seeded_files:
                text = Path(path_str).read_text(encoding="utf-8")
                assert "status:" in text
                assert "priority:" in text
                assert "mission:" in text
                assert "task:" in text
                assert "binder:" in text
                assert "tags:" in text

    async def test_import_markdown_writes_to_binder_docs(self):
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            user_vault = root / "Vault"

            with patch.object(
                mod,
                "VAULT_LAYERS",
                [
                    {
                        "id": "user",
                        "path": str(user_vault),
                        "permissions": "read_write",
                    },
                ],
            ):
                resp = await self.client.post(
                    "/api/user/workflow/import-markdown",
                    json={
                        "content": "hello from import",
                        "source_format": "text",
                        "title": "Hello Import",
                        "binder": "Sandbox",
                    },
                )

            assert resp.status == 200
            payload = await resp.json()
            file_path = Path(payload["path"])
            assert file_path.exists()
            text = file_path.read_text(encoding="utf-8")
            assert "import_plugin: builtin.text_passthrough" in text
            assert "hello from import" in text

    async def test_import_existing_binder_round_trip_and_missing_identity(self):
        from app.flow import binder_engine
        with TemporaryDirectory() as tmp:
            root = Path(tmp) / "Vault"
            with (
                patch.object(mod, "VAULT_LAYERS", [{"id": "user", "path": str(root), "permissions": "read_write"}]),
                patch.object(binder_engine, "VAULT_ROOT", root),
                patch.object(binder_engine, "BINDERS_ROOT", root / "Binders"),
            ):
                binder_engine.create_binder("garden", "Garden", "Plan spring planting")
                response = await self.client.post("/api/user/workflow/import-markdown", json={
                    "content": "Plant beans in spring. Source: https://example.com/seeds",
                    "title": "Seeds", "filename": "seeds.md", "binder": "garden",
                    "require_existing_binder": True,
                })
                assert response.status == 200
                imported = await response.json()
                assert imported["workspace_path"] == "/Binders/garden/docs/seeds.md"
                assert Path(imported["path"]).parent == (root / "Binders/garden/docs").resolve()
                reloaded = binder_engine.get_binder("garden")
                assert reloaded["documents"] == [{"filename": "seeds.md", "path": imported["workspace_path"]}]
                assert reloaded["sources"] == []  # generated notes are not evidence
                assert "https://example.com/seeds" in Path(imported["path"]).read_text()
                assert not (root / "binders" / "active").exists()
                response = await self.client.post("/api/user/workflow/import-markdown", json={
                    "content": "Do not orphan this note", "binder": "missing",
                    "require_existing_binder": True,
                })
                assert response.status == 404
                assert not (root / "binders" / "active").exists()

    async def test_import_markdown_rejects_read_only_layer(self):
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            public_vault = root / "Public"

            with patch.object(
                mod,
                "VAULT_LAYERS",
                [
                    {
                        "id": "public",
                        "path": str(public_vault),
                        "permissions": "read_only",
                    },
                ],
            ):
                resp = await self.client.post(
                    "/api/user/workflow/import-markdown",
                    json={
                        "content": "# doc",
                        "source_format": "markdown",
                        "title": "Public import",
                        "vault_layer": "public",
                    },
                )

            assert resp.status == 403
            payload = await resp.json()
            assert "read-only" in payload["error"]

    async def test_import_markdown_auto_detects_json(self):
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            user_vault = root / "Vault"

            with patch.object(
                mod,
                "VAULT_LAYERS",
                [
                    {
                        "id": "user",
                        "path": str(user_vault),
                        "permissions": "read_write",
                    },
                ],
            ):
                resp = await self.client.post(
                    "/api/user/workflow/import-markdown",
                    json={
                        "content": '{"alpha":1,"beta":2}',
                        "title": "JSON Import",
                    },
                )

            assert resp.status == 200
            payload = await resp.json()
            assert payload["detected_source_format"] == "json"
            assert payload["import_plugin"] == "builtin.json_fenced"
