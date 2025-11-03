"""Summary repository abstraction."""

from __future__ import annotations

from dataclasses import dataclass
from typing import List

import duckdb

from src.db.queries import get_items_needing_summary, save_summary
from src.logging_config import get_logger

logger = get_logger(__name__)


@dataclass(frozen=True, slots=True)
class SummaryCandidate:
    """Item that needs a summary."""

    item_id: str
    item_type: str
    title: str
    author: str
    date: str
    link: str


class SummaryRepository:
    """Repository for summary data access."""

    def __init__(self, connection: duckdb.DuckDBPyConnection):
        self._connection = connection

    def get_pending(self, limit: int | None = None) -> list[SummaryCandidate]:
        """Return pending items that require summarization."""
        rows = get_items_needing_summary(self._connection, limit)
        candidates: List[SummaryCandidate] = []
        for row in rows:
            candidates.append(
                SummaryCandidate(
                    item_id=row["id"],
                    item_type=row["item_type"],
                    title=row["title"],
                    author=row.get("author", ""),
                    date=row.get("date", ""),
                    link=row.get("link", ""),
                )
            )
        logger.debug("Loaded %d summary candidates", len(candidates))
        return candidates

    def save_summary(
        self,
        *,
        item_id: str,
        item_type: str,
        summary: str,
        key_topics: str,
        companies: str,
        tools: str,
        quotes: str,
        raw_rating: int,
        final_rating: int,
        structured_summary: str,
    ) -> None:
        """Persist a generated summary."""
        save_summary(
            self._connection,
            item_id=item_id,
            item_type=item_type,
            summary=summary,
            key_topics=key_topics,
            companies=companies,
            tools=tools,
            quotes=quotes,
            raw_rating=raw_rating,
            final_rating=final_rating,
            structured_summary=structured_summary,
        )
