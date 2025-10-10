"""Utility to fetch YouTube channel IDs from handles."""

import re
from urllib.parse import quote

def get_youtube_rss_from_channel_id(channel_id: str) -> str:
    """Convert YouTube channel ID to RSS feed URL.

    Args:
        channel_id: YouTube channel ID (e.g., UCqZSBSRcc_EzDYISssxmGHw)

    Returns:
        RSS feed URL
    """
    return f"https://www.youtube.com/feeds/videos.xml?channel_id={channel_id}"


def get_youtube_rss_from_handle(handle: str) -> str:
    """Convert YouTube handle to RSS feed URL format.

    Note: This returns a placeholder that needs manual conversion.
    YouTube handles (@username) need to be resolved to channel IDs first.

    Args:
        handle: YouTube handle (e.g., @HowIAI or HowIAI)

    Returns:
        Placeholder RSS feed URL with handle
    """
    # Remove @ if present
    clean_handle = handle.lstrip('@')

    # Return a comment format for manual resolution
    return f"<!-- TODO: Resolve @{clean_handle} to channel ID -->"


def extract_channel_id_from_url(url: str) -> str | None:
    """Extract channel ID from YouTube URL.

    Supports formats:
    - https://www.youtube.com/channel/UC...
    - https://www.youtube.com/feeds/videos.xml?channel_id=UC...

    Args:
        url: YouTube URL

    Returns:
        Channel ID or None if not found
    """
    # Pattern for channel ID (always starts with UC and is 24 chars)
    pattern = r'UC[\w-]{22}'
    match = re.search(pattern, url)
    return match.group(0) if match else None


# Manual mapping for channels we've discovered
KNOWN_CHANNEL_IDS = {
    "@latentspacepod": "UCgUP8wMCPGZ9Dt7k5bqUKlw",  # Needs verification
    "@practicalai": None,  # Has podcast RSS, no YouTube
    "@HowIAI": "UCqZSBSRcc_EzDYISssxmGHw",  # HowtoAI (uncertain)
    "@EverydayAI": None,  # Needs manual lookup
    "@AIForHumansShow": "UCghJTNTO9kcDeUFXMuSDGLQ",
    "@creatoreconomy": None,  # Actually @peteryangyt
    "@peteryangyt": None,  # Needs manual lookup
    "@danshipper": None,  # Needs manual lookup
    "@AakashGupta": None,  # Actually @growproduct
    "@growproduct": None,  # Needs manual lookup
    "@MyFirstMillionPod": None,  # Has podcast RSS
    "@LennysPodcast": None,  # Has podcast RSS
    "@DwarkeshPatel": None,  # Has podcast RSS
}
