"""Audio download using yt-dlp."""

import subprocess
import sys
from pathlib import Path

from src.config import config
from src.logging_config import get_logger
from src.utils.retry import retry_with_backoff

logger = get_logger(__name__)


@retry_with_backoff(max_retries=lambda: config.max_retries_audio, backoff_base=lambda: config.backoff_base)
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

    base_args = [
        "-x",
        "--audio-format",
        "mp3",
        "--audio-quality",
        "0",
        "-o",
        output_template,
        "--no-playlist",
        "--quiet",
        "--progress",
        url,
    ]

    try:
        try:
            # Prefer running via the python module so we respect the active interpreter
            command = [sys.executable, "-m", "yt_dlp", *base_args]
            subprocess.run(
                command,
                capture_output=True,
                text=True,
                check=True,
            )

        except subprocess.CalledProcessError as e:
            stderr = e.stderr or ""

            if "No module named" in stderr or "ModuleNotFoundError" in stderr:
                logger.warning("yt-dlp Python module missing; attempting fallback binary")

                fallback_candidates: list[str] = []
                if config.yt_dlp_binary:
                    fallback_candidates.append(str(config.yt_dlp_binary))
                fallback_candidates.append("yt-dlp")

                last_missing: FileNotFoundError | None = None

                for candidate in fallback_candidates:
                    fallback_command = [candidate, *base_args]
                    try:
                        subprocess.run(
                            fallback_command,
                            capture_output=True,
                            text=True,
                            check=True,
                        )
                        break
                    except FileNotFoundError as missing:
                        last_missing = missing
                        logger.warning(f"yt-dlp binary not found: {candidate}")
                    except subprocess.CalledProcessError as fallback_error:
                        logger.error(f"yt-dlp fallback failed: {fallback_error.stderr}")
                        raise Exception(f"Failed to download audio: {fallback_error.stderr}") from fallback_error
                else:
                    hint = "yt-dlp binary not found"
                    if config.yt_dlp_binary:
                        hint += f" (tried {config.yt_dlp_binary} and system PATH)"
                    logger.error(hint)
                    raise Exception(f"Failed to download audio: {hint}") from last_missing
            else:
                logger.error(f"yt-dlp failed: {stderr}")
                raise Exception(f"Failed to download audio: {stderr}") from e

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

    except Exception as e:
        logger.error(f"Audio download failed: {e}")
        raise
