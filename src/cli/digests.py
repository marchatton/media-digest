"""Daily and weekly digest commands."""

from argparse import _SubParsersAction
from datetime import date as date_cls, timedelta

from src.cli import common
from src.config import config
from src.db.connection import get_connection
from src.export.digest import generate_daily_digest, generate_weekly_digest, write_digest
from src.logging_config import get_logger

logger = get_logger(__name__)


def _newsletter_preview(text: str | None) -> str:
    snippet = (text or "").strip()
    snippet = " ".join(snippet.split())
    if not snippet:
        return "Preview unavailable."
    return snippet[:200] + ("…" if len(snippet) > 200 else "")


def handle_daily(args) -> None:
    target_date = date_cls.today() if args.date == "today" else date_cls.fromisoformat(args.date)
    logger.info("Building daily digest for %s", target_date)

    conn = get_connection()
    podcasts: list[dict] = []
    newsletters: list[dict] = []

    output_root = config.output_repo_path / config.export_output_path
    common.ensure_export_dirs(output_root)
    daily_rel_path = common.daily_digest_relative_path(target_date)
    daily_full_path = output_root / daily_rel_path

    ep_rows = conn.execute(
        """
        SELECT e.title, e.publish_date, coalesce(e.author, '') AS author, s.final_rating, s.summary
        FROM episodes e
        JOIN summaries s ON s.item_id = e.guid AND s.item_type = 'podcast'
        WHERE CAST(s.created_at AS DATE) = ?
        ORDER BY s.created_at DESC
        """,
        (str(target_date),),
    ).fetchall()

    for title, publish_date, author, rating, summary in ep_rows:
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

    nl_rows = conn.execute(
        """
        SELECT subject, coalesce(link, '') AS link, body_text
        FROM newsletters
        WHERE status = 'completed' AND CAST(updated_at AS DATE) = ?
        ORDER BY updated_at DESC
        """,
        (str(target_date),),
    ).fetchall()

    for subject, link, body_text in nl_rows:
        newsletters.append(
            {
                "title": subject,
                "description": _newsletter_preview(body_text),
                "source_link": link or "#",
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

    content = generate_daily_digest(
        date=target_date,
        podcasts=podcasts,
        newsletters=newsletters,
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

    output_root = config.output_repo_path / config.export_output_path
    common.ensure_export_dirs(output_root)
    weekly_rel_path = common.weekly_digest_relative_path(week_end)
    weekly_full_path = output_root / weekly_rel_path

    podcast_rows = conn.execute(
        """
        SELECT e.title, e.publish_date, coalesce(e.author, '') AS author,
               s.final_rating, s.summary
        FROM episodes e JOIN summaries s ON s.item_id = e.guid AND s.item_type = 'podcast'
        WHERE CAST(s.created_at AS DATE) BETWEEN ? AND ?
        ORDER BY s.final_rating DESC NULLS LAST, s.created_at DESC
        """,
        (str(week_start), str(week_end)),
    ).fetchall()

    for title, date_str, author, rating, summary in podcast_rows:
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

    newsletter_rows = conn.execute(
        """
        SELECT subject, coalesce(link, '') AS link, body_text
        FROM newsletters
        WHERE status = 'completed' AND CAST(updated_at AS DATE) BETWEEN ? AND ?
        ORDER BY updated_at DESC
        """,
        (str(week_start), str(week_end)),
    ).fetchall()

    for subject, link, body_text in newsletter_rows:
        newsletters.append(
            {
                "title": subject,
                "description": _newsletter_preview(body_text),
                "source_link": link or "#",
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

    content = generate_weekly_digest(
        week_start=week_start,
        week_end=week_end,
        podcasts=podcasts,
        newsletters=newsletters,
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
