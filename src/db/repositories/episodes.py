"""Episode repository abstraction."""

from __future__ import annotations

from dataclasses import dataclass
from typing import List

import duckdb

from src.db.queries import get_pending_episodes, update_episode_status
from src.logging_config import get_logger

logger = get_logger(__name__)


@dataclass(frozen=True, slots=True)
class EpisodeRecord:
    """Typed representation of an episode row."""

    guid: str
    title: str
    feed_url: str
    publish_date: str
    audio_url: str | None
    author: str | None


class EpisodeRepository:
    """Repository for episode queries and updates."""

    def __init__(self, connection: duckdb.DuckDBPyConnection):
        self._connection = connection

    def get_pending(self, limit: int | None = None) -> list[EpisodeRecord]:
        """Return pending episodes as typed records."""
        rows = get_pending_episodes(self._connection, limit)
        episodes: List[EpisodeRecord] = []
        for row in rows:
            episodes.append(
                EpisodeRecord(
                    guid=row["guid"],
                    title=row["title"],
                    feed_url=row["feed_url"],
                    publish_date=row["publish_date"],
                    audio_url=row.get("audio_url"),
                    author=row.get("author"),
                )
            )
        logger.debug("Loaded %d pending episodes", len(episodes))
        return episodes

    def mark_in_progress(self, guid: str) -> None:
        """Mark an episode as in progress."""
        update_episode_status(self._connection, guid, "in_progress")

    def mark_completed(self, guid: str) -> None:
        """Mark an episode as completed."""
        update_episode_status(self._connection, guid, "completed")

    def mark_failed(self, guid: str, reason: str) -> None:
        """Mark an episode as failed with an error reason."""
        update_episode_status(self._connection, guid, "failed", reason)
