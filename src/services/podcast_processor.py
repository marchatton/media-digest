"""Podcast processing service."""

from __future__ import annotations

from pathlib import Path
from typing import Callable

from src.db.repositories import EpisodeRepository, TranscriptRepository
from src.logging_config import get_logger
from src.process.audio import download_audio
from src.process.transcriber import Transcriber, save_transcript as save_transcript_file

logger = get_logger(__name__)


class PodcastProcessor:
    """Co-ordinates audio download, transcription, and persistence."""

    def __init__(
        self,
        *,
        episodes: EpisodeRepository,
        transcripts: TranscriptRepository,
        transcriber: Transcriber,
        audio_dir: Path,
        transcript_dir: Path,
        audio_downloader: Callable[[str, Path, str], Path] = download_audio,
    ):
        self._episodes = episodes
        self._transcripts = transcripts
        self._transcriber = transcriber
        self._audio_dir = audio_dir
        self._transcript_dir = transcript_dir
        self._audio_downloader = audio_downloader

    def process_pending(self, limit: int | None = None) -> None:
        """Process pending podcast episodes."""
        episodes = self._episodes.get_pending(limit)
        logger.info("Found %d pending episodes", len(episodes))

        for episode in episodes:
            if not episode.audio_url:
                logger.warning("No audio URL for episode: %s", episode.title)
                self._episodes.mark_failed(episode.guid, "No audio URL")
                continue

            try:
                logger.info("Processing: %s", episode.title)
                self._episodes.mark_in_progress(episode.guid)

                audio_path = self._audio_downloader(episode.audio_url, self._audio_dir, episode.guid)
                transcript = self._transcriber.transcribe(audio_path)

                transcript_path = self._transcript_dir / f"{episode.guid}.json"
                save_transcript_file(transcript, transcript_path)
                self._transcripts.save(episode.guid, transcript["text"], transcript_path)

                self._episodes.mark_completed(episode.guid)
                logger.info("Completed: %s", episode.title)
            except Exception as exc:  # pragma: no cover - defensive logging
                logger.error("Failed to process %s: %s", episode.title, exc)
                self._episodes.mark_failed(episode.guid, str(exc))

        logger.info("Audio processing complete")
