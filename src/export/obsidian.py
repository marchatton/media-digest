"""Obsidian note generation and Git operations."""

import re
import subprocess
from datetime import datetime
from pathlib import Path

from src.export.renderer import get_renderer
from src.logging_config import get_logger
from src.utils.youtube import format_timestamp_link

logger = get_logger(__name__)


def check_manual_edit(note_path: Path) -> bool:
    """Check if note has been manually edited by user.

    Detects manual edit if rating field is filled in.

    Args:
        note_path: Path to note file

    Returns:
        True if manually edited
    """
    if not note_path.exists():
        return False

    try:
        content = note_path.read_text()

        # Check if rating field is filled (not empty and not just whitespace)
        # Use [^\n] to match only characters on the same line
        match = re.search(r"^rating:\s*([^\n]+)$", content, re.MULTILINE | re.IGNORECASE)
        if match:
            rating_value = match.group(1).strip()
            if rating_value:  # Not empty
                logger.info(f"Note has manual edit (rating filled): {note_path.name}")
                return True

    except Exception as e:
        logger.warning(f"Failed to check manual edit: {e}")

    return False


def render_episode_note(
    title: str,
    date: str,
    authors: list[str],
    guests: list[str],
    link: str,
    version: str,
    rating_llm: int,
    summary: str,
    key_topics: list[str],
    companies: list[dict],
    tools: list[dict],
    quotes: list[dict],
) -> str:
    """Render episode note from template.

    Args:
        title: Episode title
        date: Publication date
        authors: List of authors/hosts
        guests: List of guests
        link: Episode URL
        version: Episode GUID
        rating_llm: LLM rating
        summary: Summary text
        key_topics: List of key topics
        companies: List of company dicts
        tools: List of tool dicts
        quotes: List of quote dicts with timestamp and text

    Returns:
        Rendered note content
    """
    renderer = get_renderer()

    # Format quotes with timestamp links
    formatted_quotes = []
    for quote in quotes:
        timestamp = quote.get("timestamp", "")
        text = quote.get("text", "")

        # Generate timestamp link
        timestamp_link = format_timestamp_link(link, timestamp)

        formatted_quotes.append({"text": text, "timestamp_link": timestamp_link})

    context = {
        "title": title,
        "date": date,
        "authors": authors,
        "guests": guests,
        "link": link,
        "type": "podcast",
        "version": version,
        "rating_llm": rating_llm,
        "summary": summary,
        "key_topics": key_topics,
        "companies": companies,
        "tools": tools,
        "quotes": formatted_quotes,
    }

    return renderer.render("episode.md.j2", context)


def render_newsletter_note(
    title: str,
    date: str,
    authors: list[str],
    link: str,
    version: str,
    rating_llm: int,
    summary: str,
    key_topics: list[str],
    companies: list[dict],
    tools: list[dict],
    quotes: list[dict],
) -> str:
    """Render newsletter note from template.

    Args:
        title: Newsletter subject
        date: Publication date
        authors: List of authors (senders)
        link: Web version link or Gmail link
        version: Message ID
        rating_llm: LLM rating
        summary: Summary text
        key_topics: List of key topics
        companies: List of company dicts
        tools: List of tool dicts
        quotes: List of quote dicts

    Returns:
        Rendered note content
    """
    renderer = get_renderer()

    context = {
        "title": title,
        "date": date,
        "authors": authors,
        "link": link,
        "type": "newsletter",
        "version": version,
        "rating_llm": rating_llm,
        "summary": summary,
        "key_topics": key_topics,
        "companies": companies,
        "tools": tools,
        "quotes": quotes,
    }

    return renderer.render("newsletter.md.j2", context)


def write_note(output_path: Path, content: str, check_edit: bool = True) -> bool:
    """Write note to file.

    Args:
        output_path: Path to write note
        content: Note content
        check_edit: Check for manual edits before overwriting

    Returns:
        True if note was written, False if skipped
    """
    # Check for manual edit
    if check_edit and check_manual_edit(output_path):
        logger.info(f"Skipping note (manually edited): {output_path.name}")
        return False

    # Create parent directory
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Write note
    output_path.write_text(content)
    logger.info(f"Wrote note: {output_path.name}")
    return True


def sanitize_filename(name: str) -> str:
    """Sanitize a string for safe filesystem filenames.

    Replaces disallowed characters and collapses whitespace.
    """
    import re
    # Replace path separators and illegal characters
    sanitized = re.sub(r"[\\/\0\t\n\r:*?\"<>|]", "_", name)
    # Collapse whitespace
    sanitized = re.sub(r"\s+", " ", sanitized).strip()
    # Truncate overly long filenames
    return sanitized[:180]


def git_commit_and_push(repo_path: Path, commit_message: str) -> None:
    """Commit and push changes to Git.

    Args:
        repo_path: Path to Git repository
        commit_message: Commit message
    """
    try:
        # Git add
        subprocess.run(
            ["git", "add", "."],
            cwd=repo_path,
            check=True,
            capture_output=True,
        )

        # Git commit
        subprocess.run(
            ["git", "commit", "-m", commit_message],
            cwd=repo_path,
            check=True,
            capture_output=True,
        )

        # Git push
        subprocess.run(
            ["git", "push", "origin", "main"],
            cwd=repo_path,
            check=True,
            capture_output=True,
        )

        logger.info(f"Git push successful: {commit_message}")

    except subprocess.CalledProcessError as e:
        if "nothing to commit" in e.stdout.decode() or "nothing to commit" in e.stderr.decode():
            logger.info("No changes to commit")
        else:
            logger.error(f"Git operation failed: {e.stderr.decode()}")
            raise
