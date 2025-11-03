"""Daily and weekly digest generation."""

from datetime import datetime, timedelta
from pathlib import Path

from src.export.renderer import get_renderer
from src.logging_config import get_logger

logger = get_logger(__name__)


def generate_daily_digest(
    date: datetime,
    podcasts: list[dict],
    newsletters: list[dict],
    failures: list[dict],
) -> str:
    """Generate daily digest.

    Args:
        date: Digest date
        items: List of processed items
        failures: List of failed items
        themes: Top themes
        actionables: Actionable items

    Returns:
        Rendered digest content
    """
    renderer = get_renderer()

    context = {
        "date": date.strftime("%Y-%m-%d"),
        "podcasts": podcasts,
        "newsletters": newsletters,
        "failures": failures,
    }

    return renderer.render("daily.md.j2", context)


def generate_weekly_digest(
    week_start: datetime,
    week_end: datetime,
    podcasts: list[dict],
    newsletters: list[dict],
    failures: list[dict],
) -> str:
    """Generate weekly digest.

    Args:
        week_start: Start of week
        week_end: End of week
        items: List of items with takeaways
        failures: List of failed items

    Returns:
        Rendered digest content
    """
    renderer = get_renderer()

    context = {
        "week_start": week_start.strftime("%Y-%m-%d"),
        "week_end": week_end.strftime("%Y-%m-%d"),
        "podcasts": podcasts,
        "newsletters": newsletters,
        "failures": failures,
    }

    return renderer.render("weekly.md.j2", context)


def write_digest(output_path: Path, content: str) -> None:
    """Write digest to file.

    Args:
        output_path: Path to write digest
        content: Digest content
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(content)
    logger.info(f"Wrote digest: {output_path.name}")
