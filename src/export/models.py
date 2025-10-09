"""Export data models."""

from dataclasses import dataclass


@dataclass
class NoteData:
    """Data for rendering a note."""

    title: str
    date: str
    author: list[str]
    guests: list[str]
    link: str
    type: str  # "podcast" or "newsletter"
    version: str  # episode_guid or message_id
    rating_llm: int
    summary: str
    key_topics: list[str]
    companies: list[dict[str, str]]
    tools: list[dict[str, str]]
    quotes: list[dict[str, str]]
