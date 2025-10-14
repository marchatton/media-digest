"""Podcast RSS feed ingestion."""

import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Generator

import feedparser

from src.ingest.models import Episode
from datetime import datetime, timezone
from src.logging_config import get_logger

logger = get_logger(__name__)


def parse_opml(opml_path: Path) -> list[str]:
    """Parse OPML file and extract RSS feed URLs.

    Args:
        opml_path: Path to OPML file

    Returns:
        List of RSS feed URLs
    """
    if not opml_path.exists():
        logger.warning(f"OPML file not found: {opml_path}")
        return []

    try:
        tree = ET.parse(opml_path)
        root = tree.getroot()

        feed_urls = []
        for outline in root.findall(".//outline[@type='rss']"):
            xml_url = outline.get("xmlUrl")
            if xml_url:
                feed_urls.append(xml_url)

        logger.info(f"Parsed {len(feed_urls)} feeds from OPML")
        return feed_urls

    except ET.ParseError as e:
        logger.error(f"Failed to parse OPML file: {e}")
        return []


def discover_episodes(feed_url: str, since_date: str | None = None) -> Generator[Episode, None, None]:
    """Discover episodes from RSS feed.

    Args:
        feed_url: RSS feed URL
        since_date: Only return episodes published after this date (ISO format)

    Yields:
        Episode objects
    """
    logger.info(f"Discovering episodes from {feed_url}")

    try:
        feed = feedparser.parse(feed_url)

        if feed.bozo:
            logger.warning(f"Feed has errors: {feed_url}")

        for entry in feed.entries:
            # Extract episode metadata
            guid = entry.get("id") or entry.get("link")
            if not guid:
                logger.warning(f"Episode missing GUID, skipping: {entry.get('title', 'Unknown')}")
                continue

            title = entry.get("title", "Untitled")

            # Parse publish date (normalize to ISO 8601 UTC)
            publish_date_iso = None
            if hasattr(entry, "published_parsed") and entry.published_parsed:
                from time import mktime
                publish_dt = datetime.fromtimestamp(mktime(entry.published_parsed), tz=timezone.utc)
                publish_date_iso = publish_dt.isoformat()
            elif hasattr(entry, "published") and entry.published:
                # Best-effort parse string to datetime
                try:
                    publish_dt = datetime.fromisoformat(entry.published)
                    if publish_dt.tzinfo is None:
                        publish_dt = publish_dt.replace(tzinfo=timezone.utc)
                    publish_date_iso = publish_dt.isoformat()
                except Exception:
                    # Fallback: keep raw string but skip date filtering for safety
                    publish_date_iso = entry.published

            if not publish_date_iso:
                logger.warning(f"Episode missing publish date, skipping: {title}")
                continue

            # Filter by date if specified
            if since_date:
                try:
                    since_dt = datetime.fromisoformat(since_date)
                    if since_dt.tzinfo is None:
                        since_dt = since_dt.replace(tzinfo=timezone.utc)
                    # Only filter if our publish_date_iso parsed to a datetime
                    pub_dt = None
                    try:
                        pub_dt = datetime.fromisoformat(publish_date_iso)
                    except Exception:
                        pub_dt = None
                    if pub_dt and pub_dt < since_dt:
                        continue
                except Exception:
                    # If since_date is malformed, do not filter
                    pass

            # Extract audio/video URLs
            audio_url = None
            video_url = None

            # Check enclosures
            for enclosure in entry.get("enclosures", []):
                url = enclosure.get("href") or enclosure.get("url")
                mime_type = enclosure.get("type", "")

                if "audio" in mime_type:
                    audio_url = url
                elif "video" in mime_type:
                    video_url = url

            # Check links if no enclosures
            if not audio_url and not video_url:
                for link in entry.get("links", []):
                    url = link.get("href")
                    mime_type = link.get("type", "")

                    if "audio" in mime_type:
                        audio_url = url
                    elif "video" in mime_type:
                        video_url = url

            # Get author
            author = None
            if hasattr(entry, "author"):
                author = entry.author
            elif hasattr(feed.feed, "author"):
                author = feed.feed.author
            elif hasattr(feed.feed, "title"):
                author = feed.feed.title

            # Get description
            description = entry.get("summary", "")

            episode = Episode(
                guid=guid,
                feed_url=feed_url,
                title=title,
                publish_date=publish_date_iso,
                author=author,
                audio_url=audio_url,
                video_url=video_url,
                description=description,
            )

            yield episode

    except Exception as e:
        logger.error(f"Failed to discover episodes from {feed_url}: {e}")


def discover_all_episodes(opml_path: Path, since_date: str | None = None) -> list[Episode]:
    """Discover all episodes from feeds in OPML file.

    Args:
        opml_path: Path to OPML file
        since_date: Only return episodes published after this date

    Returns:
        List of episodes
    """
    feed_urls = parse_opml(opml_path)
    all_episodes = []

    for feed_url in feed_urls:
        episodes = list(discover_episodes(feed_url, since_date))
        all_episodes.extend(episodes)
        logger.info(f"Discovered {len(episodes)} episodes from {feed_url}")

    logger.info(f"Total episodes discovered: {len(all_episodes)}")
    return all_episodes
