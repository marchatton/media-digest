"""Daily and weekly digest commands."""

from __future__ import annotations

from argparse import _SubParsersAction

import json
from datetime import date as date_cls, timedelta
from typing import Iterable

from src.cli import common
from src.config import config
from src.db.connection import get_connection
from src.db.queries import get_newsletter_digest_entries
from src.export.digest import generate_daily_digest, generate_weekly_digest, write_digest
from src.logging_config import get_logger

logger = get_logger(__name__)


def _extract_highlights(structured_summary: str | None) -> tuple[list[tuple[str, str]], list[str]]:
    """Return topics and actionables from a structured summary JSON payload."""

    if not structured_summary:
        return [], []

    try:
        data = json.loads(structured_summary)
    except json.JSONDecodeError:
        logger.warning("Skipping malformed structured summary in digest aggregation")
        return [], []

    topics_raw = data.get("key_topics", []) or []
    takeaways_raw = data.get("takeaways", []) or []

    topics: list[tuple[str, str]] = []
    for topic in topics_raw:
        if not isinstance(topic, dict):
            continue
        title = str(topic.get("topic", "")).strip()
        summary = str(topic.get("summary", "")).strip()
        if title and summary:
            topics.append((title, summary))

    actionables: list[str] = []
    for item in takeaways_raw:
        text = ""
        if isinstance(item, dict):
            text = str(item.get("text", ""))
        else:
            text = str(item)
        text = text.strip()
        if text:
            actionables.append(text)

    return topics, actionables


def _collect_highlights(structured_summaries: Iterable[str | None], limit: int = 5) -> tuple[list[dict[str, str]], list[str]]:
    """Aggregate top themes and actionables across structured summaries."""

    themes: list[dict[str, str]] = []
    actionables: list[str] = []
    seen_topics: set[str] = set()
    seen_actionables: set[str] = set()

    for structured_summary in structured_summaries:
        topic_items, actionable_items = _extract_highlights(structured_summary)

        for title, summary in topic_items:
            if len(themes) >= limit:
                break
            cleaned_title = title.strip()
            cleaned_summary = summary.strip()
            if not cleaned_title or not cleaned_summary:
                continue
            key = cleaned_title.lower()
            if key in seen_topics:
                continue
            seen_topics.add(key)
            themes.append({"title": cleaned_title, "summary": cleaned_summary})

        for item in actionable_items:
            if len(actionables) >= limit:
                break
            cleaned_item = item.strip()
            if not cleaned_item:
                continue
            key = cleaned_item.lower()
            if key in seen_actionables:
                continue
            seen_actionables.add(key)
            actionables.append(cleaned_item)

        if len(themes) >= limit and len(actionables) >= limit:
            break

    return themes, actionables


def handle_daily(args) -> None:
    target_date = date_cls.today() if args.date == "today" else date_cls.fromisoformat(args.date)
    logger.info("Building daily digest for %s", target_date)

    conn = get_connection()
    podcasts: list[dict] = []
    newsletters: list[dict] = []
    structured_summaries: list[str | None] = []

    output_root = config.output_repo_path / config.export_output_path
    common.ensure_export_dirs(output_root)
    daily_rel_path = common.daily_digest_relative_path(target_date)
    daily_full_path = output_root / daily_rel_path

    ep_rows = conn.execute(
        """
        SELECT e.title, e.publish_date, coalesce(e.author, '') AS author,
               s.final_rating, s.summary, s.structured_summary
        FROM episodes e
        JOIN summaries s ON s.item_id = e.guid AND s.item_type = 'podcast'
        WHERE CAST(s.created_at AS DATE) = ?
        ORDER BY s.created_at DESC
        """,
        (str(target_date),),
    ).fetchall()

    for title, publish_date, author, rating, summary, structured_summary in ep_rows:
        rel_note_path = common.podcast_relative_path(publish_date, author, title)
        link = common.relative_link(daily_full_path.parent, output_root / rel_note_path)
        podcasts.append(
            {
                "title": title,
                "rating_llm": rating or 0,
                "description": summary,
                "note_link": link,
            }
        )
        structured_summaries.append(structured_summary)

    digest_rows = get_newsletter_digest_entries(
        conn,
        start_date=str(target_date),
    )

    for row in digest_rows:
        newsletters.append(
            {
                "title": row["subject"],
                "description": row["preview"],
                "source_link": row.get("source_link") or "#",
            }
        )

    failures: list[dict] = []
    for table, title_col, date_col, type_name in [
        ("episodes", "title", "updated_at", "podcast"),
        ("newsletters", "subject", "updated_at", "newsletter"),
    ]:
        rows = conn.execute(
            f"SELECT {title_col}, error_reason FROM {table} WHERE status = 'failed' AND CAST({date_col} AS DATE) = ?",
            (str(target_date),),
        ).fetchall()
        for title, error_reason in rows:
            failures.append(
                {
                    "title": title,
                    "type": type_name,
                    "error_reason": error_reason or "",
                }
            )

    top_themes, actionables = _collect_highlights(structured_summaries)

    content = generate_daily_digest(
        date=target_date,
        podcasts=podcasts,
        newsletters=newsletters,
        top_themes=top_themes,
        actionables=actionables,
        failures=failures,
    )

    write_digest(daily_full_path, content)
    logger.info("Daily digest generated")


def handle_weekly(args) -> None:
    week_end = date_cls.today() if args.ending == "today" else date_cls.fromisoformat(args.ending)
    week_start = week_end - timedelta(days=6)
    logger.info("Building weekly digest ending %s", week_end)

    conn = get_connection()
    podcasts: list[dict] = []
    newsletters: list[dict] = []
    structured_summaries: list[str | None] = []

    output_root = config.output_repo_path / config.export_output_path
    common.ensure_export_dirs(output_root)
    weekly_rel_path = common.weekly_digest_relative_path(week_end)
    weekly_full_path = output_root / weekly_rel_path

    podcast_rows = conn.execute(
        """
        SELECT e.title, e.publish_date, coalesce(e.author, '') AS author,
               s.final_rating, s.summary, s.structured_summary
        FROM episodes e JOIN summaries s ON s.item_id = e.guid AND s.item_type = 'podcast'
        WHERE CAST(s.created_at AS DATE) BETWEEN ? AND ?
        ORDER BY s.final_rating DESC NULLS LAST, s.created_at DESC
        """,
        (str(week_start), str(week_end)),
    ).fetchall()

    for title, date_str, author, rating, summary, structured_summary in podcast_rows:
        rel_note_path = common.podcast_relative_path(date_str, author, title)
        link = common.relative_link(weekly_full_path.parent, output_root / rel_note_path)
        podcasts.append(
            {
                "title": title,
                "rating_llm": rating or 0,
                "description": summary,
                "note_link": link,
            }
        )
        structured_summaries.append(structured_summary)

    newsletter_rows = get_newsletter_digest_entries(
        conn,
        start_date=str(week_start),
        end_date=str(week_end),
    )

    for row in newsletter_rows:
        newsletters.append(
            {
                "title": row["subject"],
                "description": row["preview"],
                "source_link": row.get("source_link") or "#",
            }
        )

    failures: list[dict] = []
    for table, title_col, date_col, type_name in [
        ("episodes", "title", "updated_at", "podcast"),
        ("newsletters", "subject", "updated_at", "newsletter"),
    ]:
        rows = conn.execute(
            f"SELECT {title_col}, error_reason FROM {table} WHERE status = 'failed' AND CAST({date_col} AS DATE) BETWEEN ? AND ?",
            (str(week_start), str(week_end)),
        ).fetchall()
        for title, error_reason in rows:
            failures.append(
                {
                    "title": title,
                    "type": type_name,
                    "error_reason": error_reason or "",
                }
            )

    top_themes, actionables = _collect_highlights(structured_summaries)

    content = generate_weekly_digest(
        week_start=week_start,
        week_end=week_end,
        podcasts=podcasts,
        newsletters=newsletters,
        top_themes=top_themes,
        actionables=actionables,
        failures=failures,
    )

    write_digest(weekly_full_path, content)
    logger.info("Weekly digest generated")


def register(subparsers: _SubParsersAction) -> None:
    daily_parser = subparsers.add_parser("build-daily", help="Generate daily digest")
    daily_parser.add_argument("--date", default="today", help="Date for digest (YYYY-MM-DD or 'today')")
    daily_parser.set_defaults(func=handle_daily)

    weekly_parser = subparsers.add_parser("build-weekly", help="Generate weekly digest")
    weekly_parser.add_argument("--ending", default="today", help="Week ending date (YYYY-MM-DD or 'today')")
    weekly_parser.set_defaults(func=handle_weekly)
