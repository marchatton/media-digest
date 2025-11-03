"""Discover command implementation."""

from argparse import _SubParsersAction

from src.config import config
from src.db.connection import get_connection
from src.db.queries import upsert_episode, upsert_newsletter
from src.ingest.newsletters import discover_all_newsletters
from src.ingest.podcasts import discover_all_episodes
from src.logging_config import get_logger

logger = get_logger(__name__)


def handle(args) -> None:
    logger.info("Discovering content since %s", args.since)

    conn = get_connection()

    if config.podcasts_opml.exists():
        logger.info("Discovering podcasts from %s", config.podcasts_opml)
        episodes = discover_all_episodes(config.podcasts_opml, since_date=args.since)

        for episode in episodes:
            try:
                upsert_episode(
                    conn,
                    guid=episode.guid,
                    feed_url=episode.feed_url,
                    title=episode.title,
                    publish_date=episode.publish_date,
                    author=episode.author,
                    audio_url=episode.audio_url,
                    video_url=episode.video_url,
                )
            except Exception as exc:  # pragma: no cover - defensive logging
                logger.error("Failed to insert episode %s: %s", episode.title, exc)
        logger.info("Discovered %d podcast episodes", len(episodes))
    else:
        logger.warning("OPML file not found: %s", config.podcasts_opml)

    try:
        logger.info("Discovering newsletters from Gmail")
        newsletters = discover_all_newsletters(
            token_path=config.gmail_token_path,
            labels=config.gmail_labels,
            since_date=args.since,
        )

        for newsletter in newsletters:
            try:
                upsert_newsletter(
                    conn,
                    message_id=newsletter.message_id,
                    subject=newsletter.subject,
                    sender=newsletter.sender,
                    date=newsletter.date,
                    body_html=newsletter.body_html,
                    body_text=newsletter.body_text,
                    link=newsletter.link,
                )
            except Exception as exc:  # pragma: no cover - defensive logging
                logger.error("Failed to insert newsletter %s: %s", newsletter.subject, exc)
        logger.info("Discovered %d newsletters", len(newsletters))
    except Exception as exc:  # pragma: no cover - external dependency failure
        logger.error("Failed to discover newsletters: %s", exc)

    logger.info("Discovery complete")


def register(subparsers: _SubParsersAction) -> None:
    parser = subparsers.add_parser("discover", help="Discover new content")
    parser.add_argument("--since", default=config.start_date, help="Discover since date (YYYY-MM-DD)")
    parser.set_defaults(func=handle)
