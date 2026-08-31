from pathlib import Path

from app.services.feed_rules import evaluate_feed_rules, load_feed_rules


def test_rules_match_source_content_and_importance(tmp_path: Path):
    config = tmp_path / "rules.yaml"
    config.write_text(
        """auto_execute: false
rules:
  - id: follow-up
    enabled: true
    match:
      sources: [mail]
      contains: [follow up]
      min_importance: 0.5
    action:
      type: propose-task
      board: inbox
      priority: high
""",
        encoding="utf-8",
    )
    rules, metadata = load_feed_rules(config)
    proposals = evaluate_feed_rules(
        [
            {"id": 1, "source": "mail", "title": "Please follow up", "content": "", "importance": 0.8},
            {"id": 2, "source": "mail", "title": "Newsletter", "content": "", "importance": 0.8},
        ],
        rules,
    )

    assert metadata["auto_execute"] is False
    assert [proposal["activity_id"] for proposal in proposals] == [1]
    assert proposals[0]["priority"] == "high"


def test_example_rules_are_discoverable():
    rules, metadata = load_feed_rules()

    assert rules
    assert metadata["auto_execute"] is False
