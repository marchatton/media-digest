"""process-audio command implementation."""

from argparse import _SubParsersAction
from pathlib import Path

from src.config import config
from src.db.connection import get_connection
from src.db.queries import get_pending_episodes, save_transcript, update_episode_status
from src.logging_config import get_logger
from src.process.audio import download_audio
from src.process.transcriber import WhisperTranscriber, save_transcript as save_transcript_file

logger = get_logger(__name__)


def handle(args) -> None:
    logger.info("Processing audio...")
    conn = get_connection()
    pending = get_pending_episodes(conn, limit=args.limit)

    logger.info("Found %d pending episodes", len(pending))

    transcriber = WhisperTranscriber(
        model_size=config.asr_model,
        compute_type=config.asr_compute_type,
        device="cpu",
    )

    audio_dir = Path("blobs/audio")
    transcript_dir = Path("blobs/transcripts")

    for episode in pending:
        guid = episode["guid"]
        title = episode["title"]
        audio_url = episode["audio_url"]

        if not audio_url:
            logger.warning("No audio URL for episode: %s", title)
            update_episode_status(conn, guid, "failed", "No audio URL")
            continue

        try:
            logger.info("Processing: %s", title)
            update_episode_status(conn, guid, "in_progress")

            audio_file = download_audio(audio_url, audio_dir, guid)
            transcript = transcriber.transcribe(audio_file)

            transcript_path = transcript_dir / f"{guid}.json"
            save_transcript_file(transcript, transcript_path)
            save_transcript(conn, guid, transcript["text"], str(transcript_path))
            update_episode_status(conn, guid, "completed")

            logger.info("Completed: %s", title)

        except Exception as exc:  # pragma: no cover - defensive logging
            logger.error("Failed to process %s: %s", title, exc)
            update_episode_status(conn, guid, "failed", str(exc))

    logger.info("Audio processing complete")


def register(subparsers: _SubParsersAction) -> None:
    parser = subparsers.add_parser("process-audio", help="Process audio (download + transcribe)")
    parser.add_argument("--limit", type=int, help="Limit number of episodes to process")
    parser.set_defaults(func=handle)
