"""retry command implementation."""

from argparse import _SubParsersAction

from src.db.connection import get_connection
from src.logging_config import get_logger

logger = get_logger(__name__)


def handle(args) -> None:
    conn = get_connection()
    item_id = args.item_id

    episode = conn.execute("SELECT guid FROM episodes WHERE guid = ?", (item_id,)).fetchone()
    if episode:
        conn.execute(
            "UPDATE episodes SET status = 'pending', error_reason = NULL, updated_at = now() WHERE guid = ?",
            (item_id,),
        )
        conn.commit()
        logger.info("Episode %s reset to pending", item_id)
        return

    newsletter = conn.execute("SELECT message_id FROM newsletters WHERE message_id = ?", (item_id,)).fetchone()
    if newsletter:
        conn.execute(
            "UPDATE newsletters SET status = 'pending', error_reason = NULL, updated_at = now() WHERE message_id = ?",
            (item_id,),
        )
        conn.commit()
        logger.info("Newsletter %s reset to pending", item_id)
        return

    logger.error("Item not found: %s", item_id)


def register(subparsers: _SubParsersAction) -> None:
    parser = subparsers.add_parser("retry", help="Retry a failed item by ID")
    parser.add_argument("--item-id", required=True, help="Item ID to retry")
    parser.set_defaults(func=handle)
