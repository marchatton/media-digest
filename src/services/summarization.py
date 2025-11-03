"""Summarization service."""

from __future__ import annotations

import json
from typing import Callable

from src.db.repositories import SummaryRepository, TranscriptRepository
from src.logging_config import get_logger
from src.summarize.models import RatingResponse, SummaryResponse

logger = get_logger(__name__)


class SummarizationService:
    """Coordinates summarization and rating workflows."""

    def __init__(
        self,
        *,
        summaries: SummaryRepository,
        transcripts: TranscriptRepository,
        summarizer: Callable[[str, str, str, str, str], SummaryResponse],
        rater: Callable[[str, str, str, list[str]], RatingResponse],
    ):
        self._summaries = summaries
        self._transcripts = transcripts
        self._summarizer = summarizer
        self._rater = rater

    def summarize_pending(self, limit: int | None = None) -> None:
        """Summarize pending items."""
        candidates = self._summaries.get_pending(limit)
        logger.info("Found %d items to summarize", len(candidates))

        for candidate in candidates:
            if candidate.item_type != "podcast":
                logger.info("Skipping summarization for %s: %s", candidate.item_type, candidate.title)
                continue

            transcript_text = self._transcripts.get_text(candidate.item_id)
            if not transcript_text:
                logger.warning("No transcript for %s, skipping", candidate.item_id)
                continue

            summary = self._summarizer(
                candidate.item_type,
                candidate.title,
                candidate.author,
                candidate.date,
                transcript_text,
            )

            rating = self._rater(
                candidate.item_type,
                candidate.title,
                summary.summary_one_sentence,
                [topic.topic for topic in summary.key_topics],
            )

            self._summaries.save_summary(
                item_id=candidate.item_id,
                item_type=candidate.item_type,
                summary=summary.summary_one_sentence,
                key_topics=json.dumps([topic.model_dump() for topic in summary.key_topics]),
                companies=json.dumps([company.model_dump() for company in summary.companies]),
                tools=json.dumps([tool.model_dump() for tool in summary.tools]),
                quotes=json.dumps([insight.model_dump() for insight in summary.notable_insights]),
                raw_rating=rating.rating,
                final_rating=rating.rating,
                structured_summary=json.dumps(summary.model_dump()),
            )

            logger.info("Saved summary for %s", candidate.item_id)
