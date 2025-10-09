"""YouTube URL parsing and timestamp link generation."""

import re
from urllib.parse import parse_qs, urlparse

from src.logging_config import get_logger

logger = get_logger(__name__)


def extract_youtube_id(url: str) -> str | None:
    """Extract YouTube video ID from URL.

    Args:
        url: YouTube URL

    Returns:
        Video ID or None
    """
    # Handle different YouTube URL formats
    patterns = [
        r"(?:youtube\.com/watch\?v=|youtu\.be/|youtube\.com/embed/)([a-zA-Z0-9_-]{11})",
        r"youtube\.com/watch\?.*v=([a-zA-Z0-9_-]{11})",
    ]

    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            return match.group(1)

    return None


def is_youtube_url(url: str) -> bool:
    """Check if URL is a YouTube URL.

    Args:
        url: URL to check

    Returns:
        True if YouTube URL
    """
    return "youtube.com" in url.lower() or "youtu.be" in url.lower()


def timestamp_to_seconds(timestamp: str) -> int:
    """Convert timestamp to seconds.

    Args:
        timestamp: Timestamp in format "MM:SS" or "HH:MM:SS"

    Returns:
        Total seconds
    """
    parts = timestamp.split(":")
    parts = [int(p) for p in parts]

    if len(parts) == 2:
        # MM:SS
        return parts[0] * 60 + parts[1]
    elif len(parts) == 3:
        # HH:MM:SS
        return parts[0] * 3600 + parts[1] * 60 + parts[2]
    else:
        logger.warning(f"Invalid timestamp format: {timestamp}")
        return 0


def format_youtube_timestamp_link(url: str, timestamp: str) -> str:
    """Format YouTube URL with timestamp.

    Args:
        url: YouTube video URL
        timestamp: Timestamp in format "MM:SS" or "HH:MM:SS"

    Returns:
        YouTube URL with timestamp parameter
    """
    video_id = extract_youtube_id(url)
    if not video_id:
        return url

    seconds = timestamp_to_seconds(timestamp)
    return f"https://youtube.com/watch?v={video_id}&t={seconds}s"


def format_timestamp_link(url: str, timestamp: str) -> str:
    """Format timestamp link based on URL type.

    Args:
        url: Content URL
        timestamp: Timestamp string

    Returns:
        Formatted link (YouTube with &t= or plain [MM:SS])
    """
    if is_youtube_url(url):
        youtube_link = format_youtube_timestamp_link(url, timestamp)
        return f"[{timestamp}]({youtube_link})"
    else:
        # Plain timestamp for non-YouTube
        return f"[{timestamp}]"
