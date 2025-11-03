"""Shared helpers for CLI commands."""

from __future__ import annotations

import os
from datetime import date
from pathlib import Path

from src.export.obsidian import sanitize_filename

PODCAST_DIR = Path("unread") / "Podcasts"
NEWSLETTER_DIR = Path("unread") / "Newsletters"
DAILY_DIR = Path("unread") / "Daily summary"
WEEKLY_DIR = Path("unread") / "Weekly summary"
READ_STATUSES = ("unread", "read")


def slugify_component(text: str) -> str:
    sanitized = sanitize_filename(text or "")
    if not sanitized:
        sanitized = "untitled"
    return sanitized.replace(" ", "_")


def ensure_export_dirs(root: Path) -> None:
    categories = [PODCAST_DIR.name, NEWSLETTER_DIR.name, DAILY_DIR.name, WEEKLY_DIR.name]
    for status in READ_STATUSES:
        for category in categories:
            (root / status / category).mkdir(parents=True, exist_ok=True)


def podcast_relative_path(publish_date: str | None, author: str | None, title: str) -> Path:
    date_prefix = (publish_date or "unknown-date")[:10]
    show = author or "Unknown podcast"
    filename = f"{date_prefix}_{slugify_component(show)}_{slugify_component(title)}.md"
    return PODCAST_DIR / filename


def newsletter_relative_path(date_str: str | None, sender: str | None, subject: str) -> Path:
    date_prefix = (date_str or "unknown-date")[:10]
    sender_name = sender or "Unknown sender"
    filename = f"{date_prefix}_{slugify_component(sender_name)}_{slugify_component(subject)}.md"
    return NEWSLETTER_DIR / filename


def daily_digest_relative_path(digest_date: date) -> Path:
    return DAILY_DIR / f"{digest_date.isoformat()} daily.md"


def weekly_digest_relative_path(week_end: date) -> Path:
    return WEEKLY_DIR / f"{week_end.isoformat()} weekly.md"


def relative_link(from_path: Path, to_path: Path) -> str:
    rel = os.path.relpath(os.fspath(to_path), start=os.fspath(from_path))
    return rel.replace("\\", "/")
