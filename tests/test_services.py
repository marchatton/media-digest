"""Service layer tests."""

from __future__ import annotations

import tempfile
from pathlib import Path

import duckdb
import pytest

from src.db.queries import (
    get_transcript_text,
    save_transcript,
    update_episode_status,
    upsert_episode,
)
from src.db.repositories import EpisodeRepository, SummaryRepository, TranscriptRepository
from src.db.schema import init_schema
from src.services.podcast_processor import PodcastProcessor
from src.services.summarization import SummarizationService
from src.summarize.models import (
    EpisodeOverview,
    KeyTopic,
    NotableInsight,
    RatingResponse,
    SummaryResponse,
)


@pytest.fixture()
def service_db():
    """Provide an isolated DuckDB connection for service tests."""
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "service.duckdb"
        conn = duckdb.connect(str(db_path))
        init_schema(conn)
        yield conn
        conn.close()


class StubTranscriber:
    """Simple transcriber that returns a fixed transcript."""

    def __init__(self, transcript_text: str):
        self.transcript_text = transcript_text

    def transcribe(self, audio_path: Path):
        return {
            "text": self.transcript_text,
            "segments": [],
            "language": "en",
            "duration": 1.0,
        }


class StubRating:
    """Callable stub for rating."""

    def __init__(self, rating: int = 4):
        self.rating = rating

    def __call__(self, content_type: str, title: str, summary: str, key_topics: list[str]):
        return RatingResponse(rating=self.rating, rationale="stub")


def make_summary_response(title: str = "Episode") -> SummaryResponse:
    """Helper to construct a minimal summary response."""
    return SummaryResponse(
        episode_overview=EpisodeOverview(theme="Theme", hook="Hook"),
        key_topics=[KeyTopic(topic="Topic", summary="Summary", timestamp=None)],
        notable_insights=[NotableInsight(idea="Idea", attribution=None, timestamp=None)],
        summary_one_sentence=f"{title} summary",
    )


def test_podcast_processor_saves_transcripts(service_db, tmp_path):
    """PodcastProcessor should persist transcripts and update status."""
    upsert_episode(
        service_db,
        guid="ep-1",
        feed_url="https://feed",
        title="Episode 1",
        publish_date="2025-10-09",
        audio_url="https://audio",
    )

    processor = PodcastProcessor(
        episodes=EpisodeRepository(service_db),
        transcripts=TranscriptRepository(service_db),
        transcriber=StubTranscriber("Transcript text"),
        audio_dir=tmp_path / "audio",
        transcript_dir=tmp_path / "transcripts",
        audio_downloader=lambda url, output_dir, guid: output_dir / f"{guid}.mp3",
    )

    processor.process_pending()

    # Transcript should be saved to DB
    assert get_transcript_text(service_db, "ep-1") == "Transcript text"

    status, = service_db.execute(
        "SELECT status FROM episodes WHERE guid = ?", ("ep-1",)
    ).fetchone()
    assert status == "completed"


def test_podcast_processor_marks_missing_audio_failed(service_db, tmp_path):
    """Episodes without audio URLs are marked as failed."""
    upsert_episode(
        service_db,
        guid="ep-missing-audio",
        feed_url="https://feed",
        title="No Audio",
        publish_date="2025-10-09",
        audio_url=None,
    )

    processor = PodcastProcessor(
        episodes=EpisodeRepository(service_db),
        transcripts=TranscriptRepository(service_db),
        transcriber=StubTranscriber("Transcript"),
        audio_dir=tmp_path / "audio",
        transcript_dir=tmp_path / "transcripts",
        audio_downloader=lambda url, output_dir, guid: output_dir / f"{guid}.mp3",
    )

    processor.process_pending()

    status, error = service_db.execute(
        "SELECT status, error_reason FROM episodes WHERE guid = ?",
        ("ep-missing-audio",),
    ).fetchone()
    assert status == "failed"
    assert error == "No audio URL"


def test_summarization_service_persists_summary(service_db):
    """SummarizationService should store summaries and ratings."""
    upsert_episode(
        service_db,
        guid="ep-sum",
        feed_url="https://feed",
        title="Episode",
        publish_date="2025-10-09",
        audio_url="https://audio",
    )

    update_episode_status(service_db, "ep-sum", "completed")

    save_transcript(
        service_db,
        episode_guid="ep-sum",
        transcript_text="Transcript",
        transcript_path="/tmp/ep-sum.json",
    )

    summaries = SummaryRepository(service_db)
    transcripts = TranscriptRepository(service_db)

    service = SummarizationService(
        summaries=summaries,
        transcripts=transcripts,
        summarizer=lambda *args: make_summary_response(),
        rater=StubRating(5),
    )

    service.summarize_pending()

    row = service_db.execute(
        "SELECT summary, raw_rating, final_rating FROM summaries WHERE item_id = ?",
        ("ep-sum",),
    ).fetchone()
    assert row is not None
    summary_text, raw_rating, final_rating = row
    assert summary_text == "Episode summary"
    assert raw_rating == 5
    assert final_rating == 5


def test_summarization_service_skips_without_transcript(service_db):
    """SummarizationService should skip items missing transcripts."""
    upsert_episode(
        service_db,
        guid="ep-no-transcript",
        feed_url="https://feed",
        title="Episode",
        publish_date="2025-10-09",
        audio_url="https://audio",
    )

    update_episode_status(service_db, "ep-no-transcript", "completed")

    summaries = SummaryRepository(service_db)
    transcripts = TranscriptRepository(service_db)

    called = {"count": 0}

    def raising_summarizer(*args):
        called["count"] += 1
        raise AssertionError("Summarizer should not be invoked")

    service = SummarizationService(
        summaries=summaries,
        transcripts=transcripts,
        summarizer=raising_summarizer,
        rater=StubRating(),
    )

    service.summarize_pending()

    # Ensure summarizer was never called and no rows were inserted
    assert called["count"] == 0
    count, = service_db.execute(
        "SELECT COUNT(*) FROM summaries WHERE item_id = ?",
        ("ep-no-transcript",),
    ).fetchone()
    assert count == 0
