"""Summarization orchestration."""

import json

from src.config import config
from src.logging_config import get_logger
from src.summarize.client import get_client
from src.summarize.models import SummaryResponse
from src.summarize.prompts import (
    CLEANING_SYSTEM_PROMPT,
    SUMMARIZATION_SYSTEM_PROMPT,
    cleaning_user_prompt,
    summarization_user_prompt,
)

logger = get_logger(__name__)


def clean_transcript(title: str, duration: str, raw_transcript: str) -> str:
    """Clean transcript using LLM.

    Args:
        title: Episode title
        duration: Duration string
        raw_transcript: Raw transcript text

    Returns:
        Cleaned transcript
    """
    logger.info(f"Cleaning transcript for: {title}")

    client = get_client()

    user_prompt = cleaning_user_prompt(title, duration, raw_transcript)

    cleaned = client.generate(
        system_prompt=CLEANING_SYSTEM_PROMPT,
        user_prompt=user_prompt,
        model=config.llm_cleaning_model,
        temperature=0.3,  # Lower temperature for cleaning
    )

    logger.info(f"Cleaned transcript ({len(cleaned)} chars)")
    return cleaned


def summarize_content(
    content_type: str,
    title: str,
    author: str,
    date: str,
    content_text: str,
) -> SummaryResponse:
    """Summarize content using LLM.

    Args:
        content_type: "podcast" or "newsletter"
        title: Content title
        author: Author/host name
        date: Publication date
        content_text: Cleaned content text

    Returns:
        Summary response
    """
    logger.info(f"Summarizing {content_type}: {title}")

    client = get_client()

    user_prompt = summarization_user_prompt(
        content_type=content_type,
        title=title,
        author=author,
        date=date,
        content_text=content_text,
    )

    response_json = client.generate_json(
        system_prompt=SUMMARIZATION_SYSTEM_PROMPT,
        user_prompt=user_prompt,
        model=config.llm_summarization_model,
        temperature=0.7,
    )

    # Parse into Pydantic model
    summary = SummaryResponse(**response_json)

    logger.info(
        f"Summarized {content_type}: {len(summary.key_topics)} topics, "
        f"{len(summary.companies)} companies, {len(summary.tools)} tools, "
        f"{len(summary.quotes)} quotes"
    )

    return summary
