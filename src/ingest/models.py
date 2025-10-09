"""Data models for episodes and newsletters."""

from dataclasses import dataclass
from datetime import datetime


@dataclass
class Episode:
    """Podcast episode metadata."""

    guid: str
    feed_url: str
    title: str
    publish_date: str
    author: str | None = None
    audio_url: str | None = None
    video_url: str | None = None
    description: str | None = None


@dataclass
class Newsletter:
    """Newsletter metadata."""

    message_id: str
    subject: str
    sender: str
    date: str
    body_html: str | None = None
    body_text: str | None = None
    link: str | None = None
