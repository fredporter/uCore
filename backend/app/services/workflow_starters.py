"""Small, opt-in personal workflows written through uFlow's task contract."""
from __future__ import annotations

import hashlib

from app.flow.task_store import default_tasker_dir, write_task_markdown

STARTERS = {
    "daily": {"title": "A calmer day", "description": "Make room for what matters, with a short opening and closing routine.", "tasks": [
        ("Check in with yourself", "Take a minute to notice your energy. Write one sentence about what would make today feel manageable."),
        ("Choose one thing that matters", "Pick a realistic priority. Break it into a first step that takes about 15 minutes."),
        ("Make room for a break", "Choose a comfortable pause: step outside, stretch, drink water, or rest your eyes."),
        ("Close the day gently", "Note one thing you finished or learned. Move unfinished work to a suitable day without adding pressure.")]},
    "focus": {"title": "A focused session", "description": "Turn an intention into a small, finishable block of work.", "tasks": [
        ("Define a small finish line", "Write what done looks like for this session. Keep the scope small enough for your available time."),
        ("Clear a little space", "Gather what you need and pause avoidable distractions. Choose a session length that suits your energy."),
        ("Do the first useful step", "Work on the smallest action that moves your priority forward. Capture interruptions as notes."),
        ("Save progress and choose what follows", "Record your result, save useful notes, and decide whether to continue or take a break.")]},
    "learning": {"title": "Learn something useful", "description": "Explore a question, practise, and keep the useful parts in your own library.", "tasks": [
        ("Choose a question", "What would you like to understand or be able to do? Write one clear question."),
        ("Find one useful source", "Start in your local Knowledge library or collect a source in your binder. Note where it came from."),
        ("Try it for yourself", "Make a small example, practise a skill, or explain the idea in your own words."),
        ("Keep what you learned", "Save a short note in your Vault. Include one example and a question to explore next.")]},
}


def install_starter(owner: str, starter: str) -> int:
    """Retry safely without replacing tasks the user has edited or moved."""
    if starter not in STARTERS:
        raise ValueError("Choose an available starter workflow")
    from app.api.tasker_api import _parse_markdown_task

    base = default_tasker_dir()
    existing = {_parse_markdown_task(path).get("id") for path in base.rglob("*.md")}
    prefix = hashlib.sha256(f"{owner}:{starter}".encode()).hexdigest()[:16]
    created = 0
    for index, (title, body) in enumerate(STARTERS[starter]["tasks"]):
        ident = f"starter-{prefix}-{index}"
        if ident in existing:
            continue
        write_task_markdown(title=title, body=body, board=f"{starter}-{prefix[:6]}", source="user", source_id=ident,
                            metadata={"id": ident, "profile": owner, "group": STARTERS[starter]["title"], "tags": ["personal", "starter"]})
        created += 1
    return created
