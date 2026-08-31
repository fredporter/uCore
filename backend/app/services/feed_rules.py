"""Small, auditable rules engine for turning Feed signals into workflow proposals."""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

from app.core.settings import settings

DEFAULT_RULES_PATH = Path(__file__).resolve().parents[3] / "config" / "feed-rules.example.yaml"
USER_RULES_PATH = settings.udos_home / "config" / "feed-rules.yaml"


@dataclass(frozen=True)
class FeedRule:
    id: str
    enabled: bool
    sources: tuple[str, ...]
    contains: tuple[str, ...]
    min_importance: float
    action: str
    board: str
    priority: str
    binder: str

    def matches(self, activity: dict[str, Any]) -> bool:
        source = str(activity.get("source") or "").lower()
        if self.sources and source not in self.sources:
            return False
        if float(activity.get("importance") or 0) < self.min_importance:
            return False
        haystack = " ".join(
            str(activity.get(key) or "") for key in ("title", "content", "type")
        ).lower()
        return not self.contains or any(term in haystack for term in self.contains)


def load_feed_rules(path: Path | None = None) -> tuple[list[FeedRule], dict[str, Any]]:
    selected = path or (USER_RULES_PATH if USER_RULES_PATH.exists() else DEFAULT_RULES_PATH)
    if not selected.exists():
        return [], {"path": str(selected), "auto_execute": False}
    raw = yaml.safe_load(selected.read_text(encoding="utf-8")) or {}
    rules = []
    for item in raw.get("rules") or []:
        match = item.get("match") or {}
        action = item.get("action") or {}
        rules.append(
            FeedRule(
                id=str(item.get("id") or "unnamed-rule"),
                enabled=bool(item.get("enabled", False)),
                sources=tuple(str(value).lower() for value in match.get("sources") or []),
                contains=tuple(str(value).lower() for value in match.get("contains") or []),
                min_importance=float(match.get("min_importance", 0)),
                action=str(action.get("type") or "propose-task"),
                board=str(action.get("board") or "inbox"),
                priority=str(action.get("priority") or "medium"),
                binder=str(action.get("binder") or "Sandbox"),
            )
        )
    return rules, {
        "path": str(selected),
        "auto_execute": bool(raw.get("auto_execute", False)),
    }


def evaluate_feed_rules(
    activities: list[dict[str, Any]], rules: list[FeedRule]
) -> list[dict[str, Any]]:
    proposals: list[dict[str, Any]] = []
    for activity in activities:
        for rule in rules:
            if not rule.enabled or not rule.matches(activity):
                continue
            proposals.append(
                {
                    "rule_id": rule.id,
                    "activity_id": int(activity["id"]),
                    "action": rule.action,
                    "board": rule.board,
                    "priority": rule.priority,
                    "binder": rule.binder,
                    "title": str(activity.get("title") or activity.get("type") or "Feed item"),
                }
            )
    return proposals
