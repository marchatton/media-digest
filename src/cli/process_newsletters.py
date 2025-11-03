"""process-newsletters command implementation."""

from argparse import _SubParsersAction

from src.config import config
from src.db.connection import get_connection
from src.db.queries import (
    get_pending_newsletters,
    update_newsletter_status,
    upsert_newsletter_digest_entry,
)
from src.logging_config import get_logger
from src.process.newsletter_parser import build_preview, parse_newsletter, save_parsed_newsletter

logger = get_logger(__name__)


def handle(args) -> None:
    logger.info("Processing newsletters...")

    conn = get_connection()
    pending = get_pending_newsletters(conn, limit=args.limit)

    logger.info("Found %d pending newsletters", len(pending))

    newsletter_dir = config.newsletter_blob_dir

    for newsletter in pending:
        message_id = newsletter["message_id"]
        subject = newsletter["subject"]
        body_html = newsletter["body_html"]
        body_text = newsletter["body_text"]

        try:
            logger.info("Processing: %s", subject)
            update_newsletter_status(conn, message_id, "in_progress")

            parsed_text = parse_newsletter(body_html, body_text)
            link = newsletter.get("link")
            save_parsed_newsletter(message_id, parsed_text, link, newsletter_dir)
            preview = build_preview(parsed_text)
            upsert_newsletter_digest_entry(
                conn,
                message_id=message_id,
                subject=subject,
                preview=preview,
                source_link=link,
            )
            update_newsletter_status(conn, message_id, "completed")

            logger.info("Completed: %s", subject)

        except Exception as exc:  # pragma: no cover - defensive logging
            logger.error("Failed to process %s: %s", subject, exc)
            update_newsletter_status(conn, message_id, "failed", str(exc))

    logger.info("Newsletter processing complete")


def register(subparsers: _SubParsersAction) -> None:
    parser = subparsers.add_parser("process-newsletters", help="Process newsletters")
    parser.add_argument("--limit", type=int, help="Limit number of newsletters to process")
    parser.set_defaults(func=handle)
