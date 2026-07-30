#!/usr/bin/env python3
"""Verify external uKnowledge route contract for uCore knowledge surface.

This script imports `uknowledge.routes.register_routes` and confirms the
registered method/path pairs match the currently expected knowledge API surface.
"""

from __future__ import annotations

from collections.abc import Iterable

from aiohttp import web


EXPECTED: set[tuple[str, str]] = {
	("GET", "/api/knowledge/workspaces"),
	("POST", "/api/knowledge/workspaces"),
	("GET", "/api/knowledge/workspaces/{workspace_id}/views"),
	("GET", "/api/knowledge/documents"),
	("GET", "/api/knowledge/documents/{object_id}"),
	("GET", "/api/knowledge/documents/{object_id}/content"),
	("GET", "/api/knowledge/views/{view_id}"),
	("POST", "/api/knowledge/views"),
	("GET", "/api/knowledge/search"),
	("GET", "/api/knowledge/adapter/mission-task-binder"),
	("GET", "/api/knowledge/local/databases"),
	("GET", "/api/knowledge/local/tables"),
	("POST", "/api/knowledge/local/query"),
	("POST", "/api/knowledge/local/export"),
	("POST", "/api/knowledge/import"),
	("POST", "/api/knowledge/sync"),
	("GET", "/api/knowledge/status"),
	("GET", "/api/knowledge/index/status"),
	("GET", "/api/knowledge/import/status"),
	("GET", "/api/knowledge/index/coverage"),
}


def _iter_routes(app: web.Application) -> Iterable[tuple[str, str]]:
	for route in app.router.routes():
		info = route.get_info()
		path = info.get("path")
		if not path:
			resource = getattr(route, "resource", None)
			canonical = getattr(resource, "canonical", None)
			path = canonical if canonical else ""
		method = str(getattr(route, "method", "")).upper()
		if method == "HEAD":
			continue
		yield method, str(path)


def main() -> int:
	try:
		from uknowledge.routes import register_routes
	except Exception as exc:
		print(f"[FAIL] Unable to import uknowledge.routes.register_routes: {exc}")
		return 1

	app = web.Application()
	register_routes(app)

	actual = set(_iter_routes(app))
	missing = sorted(EXPECTED - actual)
	extra = sorted(actual - EXPECTED)

	print(f"Expected routes: {len(EXPECTED)}")
	print(f"Actual routes:   {len(actual)}")

	if not missing and not extra:
		print("Knowledge route contract check passed.")
		return 0

	if missing:
		print("[FAIL] Missing routes:")
		for method, path in missing:
			print(f"- {method} {path}")

	if extra:
		print("[FAIL] Unexpected extra routes:")
		for method, path in extra:
			print(f"- {method} {path}")

	return 1


if __name__ == "__main__":
	raise SystemExit(main())
