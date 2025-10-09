"""Content rating logic."""

from src.config import config
from src.logging_config import get_logger
from src.summarize.client import get_client
from src.summarize.models import RatingResponse
from src.summarize.prompts import RATING_SYSTEM_PROMPT, rating_user_prompt

logger = get_logger(__name__)


def rate_content(
    content_type: str,
    title: str,
    summary: str,
    key_topics: list[str],
) -> RatingResponse:
    """Rate content using LLM.

    Args:
        content_type: "podcast" or "newsletter"
        title: Content title
        summary: Content summary
        key_topics: List of key topics

    Returns:
        Rating response
    """
    logger.info(f"Rating {content_type}: {title}")

    client = get_client()

    user_prompt = rating_user_prompt(
        content_type=content_type,
        title=title,
        summary=summary,
        key_topics=key_topics,
    )

    response_json = client.generate_json(
        system_prompt=RATING_SYSTEM_PROMPT,
        user_prompt=user_prompt,
        model=config.llm_rating_model,
        temperature=0.5,  # Lower temperature for more consistent ratings
    )

    # Parse into Pydantic model
    rating = RatingResponse(**response_json)

    logger.info(f"Rated {content_type}: {rating.rating}/5 - {rating.rationale}")

    return rating
