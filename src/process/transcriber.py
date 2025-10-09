"""Whisper transcription using faster-whisper."""

import json
from pathlib import Path
from typing import Protocol

from faster_whisper import WhisperModel

from src.logging_config import get_logger

logger = get_logger(__name__)


class Transcriber(Protocol):
    """Protocol for transcription services."""

    def transcribe(self, audio_path: Path) -> dict[str, any]:
        """Transcribe audio file.

        Args:
            audio_path: Path to audio file

        Returns:
            Dictionary with 'text' and 'segments' (with timestamps)
        """
        ...


class WhisperTranscriber:
    """Whisper transcription implementation."""

    def __init__(self, model_size: str = "medium", compute_type: str = "int8", device: str = "cpu"):
        """Initialize Whisper model.

        Args:
            model_size: Model size (tiny, base, small, medium, large)
            compute_type: Computation type (int8, float16)
            device: Device to run on (cpu, cuda)
        """
        self.model_size = model_size
        self.compute_type = compute_type
        self.device = device

        logger.info(f"Loading Whisper model: {model_size} ({compute_type} on {device})")
        self.model = WhisperModel(model_size, device=device, compute_type=compute_type)

    def transcribe(self, audio_path: Path) -> dict[str, any]:
        """Transcribe audio file using Whisper.

        Args:
            audio_path: Path to audio file

        Returns:
            Dictionary with:
                - text: Full transcript text
                - segments: List of segments with timestamps and text
        """
        logger.info(f"Transcribing: {audio_path}")

        try:
            segments, info = self.model.transcribe(
                str(audio_path),
                beam_size=5,
                word_timestamps=True,
            )

            # Collect segments
            all_segments = []
            full_text = []

            for segment in segments:
                segment_data = {
                    "start": segment.start,
                    "end": segment.end,
                    "text": segment.text.strip(),
                }
                all_segments.append(segment_data)
                full_text.append(segment.text.strip())

            result = {
                "text": " ".join(full_text),
                "segments": all_segments,
                "language": info.language,
                "duration": info.duration,
            }

            logger.info(
                f"Transcription complete: {len(all_segments)} segments, "
                f"{info.duration:.1f}s, language: {info.language}"
            )

            return result

        except Exception as e:
            logger.error(f"Transcription failed: {e}")
            raise


def save_transcript(transcript: dict[str, any], output_path: Path) -> None:
    """Save transcript to JSON file.

    Args:
        transcript: Transcript dictionary
        output_path: Path to save JSON file
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, "w") as f:
        json.dump(transcript, f, indent=2)

    logger.info(f"Saved transcript to: {output_path}")


def load_transcript(transcript_path: Path) -> dict[str, any]:
    """Load transcript from JSON file.

    Args:
        transcript_path: Path to transcript JSON file

    Returns:
        Transcript dictionary
    """
    with open(transcript_path) as f:
        return json.load(f)
