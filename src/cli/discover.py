"""Discover command implementation."""

from argparse import _SubParsersAction
import json
from datetime import datetime, timezone
from pathlib import Path

from src.config import config
from src.db.connection import get_connection
from src.db.queries import upsert_episode, upsert_newsletter
from src.ingest.newsletters import discover_all_newsletters
from src.ingest.podcasts import discover_all_episodes
from src.logging_config import get_logger

logger = get_logger(__name__)

DISCOVERY_ISSUES_PATH = Path("logs/discovery_issues.json")


def _write_discovery_issues(issues: list[dict[str, str]]) -> None:
    if not issues:
        if DISCOVERY_ISSUES_PATH.exists():
            DISCOVERY_ISSUES_PATH.unlink()
        return

    payload = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "issues": issues,
    }
    DISCOVERY_ISSUES_PATH.parent.mkdir(parents=True, exist_ok=True)
    DISCOVERY_ISSUES_PATH.write_text(json.dumps(payload, indent=2))


def handle(args) -> None:
    logger.info("Discovering content since %s", args.since)

    conn = get_connection()
    discovery_issues: list[dict[str, str]] = []

    if config.podcasts_opml.exists():
        logger.info("Discovering podcasts from %s", config.podcasts_opml)
        episodes, issues = discover_all_episodes(config.podcasts_opml, since_date=args.since)

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
        discovery_issues.extend(issues)
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
        discovery_issues.append(
            {
                "feed_url": "gmail",
                "error": str(exc),
            }
        )

    logger.info("Discovery complete")
    _write_discovery_issues(discovery_issues)


def register(subparsers: _SubParsersAction) -> None:
    parser = subparsers.add_parser("discover", help="Discover new content")
    parser.add_argument("--since", default=config.start_date, help="Discover since date (YYYY-MM-DD)")
    parser.set_defaults(func=handle)
