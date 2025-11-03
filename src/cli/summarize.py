"""summarize command implementation."""

from argparse import _SubParsersAction
import json

from src.db.connection import get_connection
from src.db.queries import get_items_needing_summary, save_summary
from src.logging_config import get_logger
from src.summarize.rater import rate_content
from src.summarize.summarizer import summarize_content

logger = get_logger(__name__)


def handle(args) -> None:
    logger.info("Summarizing content...")

    conn = get_connection()
    items = get_items_needing_summary(conn, limit=args.limit)

    logger.info("Found %d items to summarize", len(items))

    for item in items:
        item_type = item["item_type"]
        if item_type != "podcast":
            logger.info("Skipping summarization for %s: %s", item_type, item["title"])
            continue

        item_id = item["id"]
        title = item["title"]
        author = item.get("author", "")
        date = item.get("date", "")

        try:
            row = conn.execute(
                "SELECT transcript_text FROM transcripts WHERE episode_guid = ?",
                (item_id,),
            ).fetchone()
            if not row:
                logger.warning("No transcript for %s, skipping", item_id)
                continue

            content_text = row[0]
            if not content_text:
                logger.warning("Empty transcript for %s, skipping", item_id)
                continue

            summary_resp = summarize_content(
                content_type=item_type,
                title=title,
                author=author,
                date=date,
                content_text=content_text,
            )

            rating_resp = rate_content(
                content_type=item_type,
                title=title,
                summary=summary_resp.summary_one_sentence,
                key_topics=[topic.topic for topic in summary_resp.key_topics],
            )

            save_summary(
                conn,
                item_id=item_id,
                item_type=item_type,
                summary=summary_resp.summary_one_sentence,
                key_topics=json.dumps([topic.dict() for topic in summary_resp.key_topics]),
                companies=json.dumps([company.dict() for company in summary_resp.companies]),
                tools=json.dumps([tool.dict() for tool in summary_resp.tools]),
                quotes=json.dumps([insight.dict() for insight in summary_resp.notable_insights]),
                raw_rating=rating_resp.rating,
                final_rating=rating_resp.rating,
                structured_summary=json.dumps(summary_resp.model_dump()),
            )

            logger.info("Saved summary for %s", item_id)

        except Exception as exc:  # pragma: no cover - defensive logging
            logger.error("Failed to summarize %s %s: %s", item_type, item_id, exc)


def register(subparsers: _SubParsersAction) -> None:
    parser = subparsers.add_parser("summarize", help="Summarize completed content")
    parser.add_argument("--limit", type=int, help="Limit number of items to summarize")
    parser.set_defaults(func=handle)
