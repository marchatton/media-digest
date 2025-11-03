"""Transcript repository abstraction."""

from __future__ import annotations

from pathlib import Path
from typing import Optional

import duckdb

from src.db.queries import get_transcript_text, save_transcript


class TranscriptRepository:
    """Repository for transcript persistence and retrieval."""

    def __init__(self, connection: duckdb.DuckDBPyConnection):
        self._connection = connection

    def save(self, episode_guid: str, transcript_text: str, transcript_path: Path) -> None:
        """Persist transcript metadata."""
        save_transcript(self._connection, episode_guid, transcript_text, str(transcript_path))

    def get_text(self, episode_guid: str) -> Optional[str]:
        """Return transcript text for an episode if present."""
        return get_transcript_text(self._connection, episode_guid)
