"""Audio download using yt-dlp."""

import subprocess
from pathlib import Path

from src.logging_config import get_logger
from src.utils.retry import retry_with_backoff

logger = get_logger(__name__)


@retry_with_backoff(max_retries=3, backoff_base=60)
def download_audio(url: str, output_dir: Path, episode_guid: str) -> Path:
    """Download audio from URL using yt-dlp.

    Args:
        url: Audio or video URL
        output_dir: Directory to save audio file
        episode_guid: Episode GUID (for filename)

    Returns:
        Path to downloaded audio file

    Raises:
        Exception if download fails
    """
    output_dir.mkdir(parents=True, exist_ok=True)

    # Sanitize filename
    safe_guid = "".join(c if c.isalnum() or c in "-_" else "_" for c in episode_guid)
    output_template = str(output_dir / f"{safe_guid}.%(ext)s")

    logger.info(f"Downloading audio: {url}")

    try:
        # Run yt-dlp
        result = subprocess.run(
            [
                "yt-dlp",
                "-x",  # Extract audio
                "--audio-format", "mp3",
                "--audio-quality", "0",  # Best quality
                "-o", output_template,
                "--no-playlist",  # Don't download playlists
                "--quiet",
                "--progress",
                url,
            ],
            capture_output=True,
            text=True,
            check=True,
        )

        # Find the downloaded file
        audio_file = output_dir / f"{safe_guid}.mp3"

        if not audio_file.exists():
            # Try to find any file matching the GUID
            matches = list(output_dir.glob(f"{safe_guid}.*"))
            if matches:
                audio_file = matches[0]
            else:
                raise FileNotFoundError(f"Downloaded audio file not found: {audio_file}")

        logger.info(f"Downloaded audio to: {audio_file}")
        return audio_file

    except subprocess.CalledProcessError as e:
        logger.error(f"yt-dlp failed: {e.stderr}")
        raise Exception(f"Failed to download audio: {e.stderr}")
    except Exception as e:
        logger.error(f"Audio download failed: {e}")
        raise
