"""process-audio command implementation."""

from argparse import _SubParsersAction

from src.config import config
from src.db.connection import get_connection
from src.db.repositories import EpisodeRepository, TranscriptRepository
from src.logging_config import get_logger
from src.process.transcriber import WhisperTranscriber
from src.services.podcast_processor import PodcastProcessor

logger = get_logger(__name__)


def handle(args) -> None:
    logger.info("Processing audio...")
    conn = get_connection()

    processor = PodcastProcessor(
        episodes=EpisodeRepository(conn),
        transcripts=TranscriptRepository(conn),
        transcriber=WhisperTranscriber(
            model_size=config.asr_model,
            compute_type=config.asr_compute_type,
            device="cpu",
        ),
        audio_dir=config.audio_blob_dir,
        transcript_dir=config.transcript_blob_dir,
    )

    processor.process_pending(limit=args.limit)


def register(subparsers: _SubParsersAction) -> None:
    parser = subparsers.add_parser("process-audio", help="Process audio (download + transcribe)")
    parser.add_argument("--limit", type=int, help="Limit number of episodes to process")
    parser.set_defaults(func=handle)
