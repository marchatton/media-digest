"""skip command implementation."""

from argparse import _SubParsersAction

from src.db.connection import get_connection
from src.logging_config import get_logger

logger = get_logger(__name__)


def handle(args) -> None:
    conn = get_connection()
    item_id = args.item_id

    updated = conn.execute(
        "UPDATE episodes SET status = 'skipped', updated_at = now() WHERE guid = ?",
        (item_id,),
    ).rowcount
    if updated:
        conn.commit()
        logger.info("Episode %s marked as skipped", item_id)
        return

    updated = conn.execute(
        "UPDATE newsletters SET status = 'skipped', updated_at = now() WHERE message_id = ?",
        (item_id,),
    ).rowcount
    if updated:
        conn.commit()
        logger.info("Newsletter %s marked as skipped", item_id)
        return

    logger.error("Item not found: %s", item_id)


def register(subparsers: _SubParsersAction) -> None:
    parser = subparsers.add_parser("skip", help="Skip an item permanently by ID")
    parser.add_argument("--item-id", required=True, help="Item ID to skip")
    parser.set_defaults(func=handle)
