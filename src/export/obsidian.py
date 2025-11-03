"""Obsidian note generation and Git operations."""

import re
import subprocess
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any

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

        for line in content.splitlines():
            if not line.lower().startswith("rating:"):
                continue

            rating_value = line.partition(":")[2].strip()
            if rating_value:
                logger.info(f"Note has manual edit (rating filled): {note_path.name}")
                return True
            break

    except Exception as e:
        logger.warning(f"Failed to check manual edit: {e}")

    return False


@dataclass(frozen=True)
class NoteContext:
    """Structured data required to render a note."""

    title: str
    date: str
    authors: list[str]
    link: str
    version: str
    rating_llm: int
    summary: str
    key_topics: list[dict]
    companies: list[dict]
    tools: list[dict]
    insights: list[dict]
    takeaways: list[dict] = field(default_factory=list)
    memorable_moments: list[dict] = field(default_factory=list)
    overview: dict | None = None
    wildcard: str | None = None
    guests: list[str] | None = None


def _payload_from_context(context: NoteContext) -> dict[str, Any]:
    """Build the shared context fragment from a note context."""
    return {
        "title": context.title,
        "date": context.date,
        "authors": list(context.authors),
        "version": context.version,
        "rating_llm": context.rating_llm,
        "summary": context.summary,
        "key_topics": list(context.key_topics),
        "companies": list(context.companies),
        "tools": list(context.tools),
        "insights": list(context.insights),
        "takeaways": list(context.takeaways),
        "memorable_moments": list(context.memorable_moments),
        "overview": dict(context.overview) if context.overview else None,
        "wildcard": context.wildcard,
    }


def _render_note(
    template_name: str,
    *,
    note_type: str,
    link: str,
    payload: dict[str, Any],
    insights: list[dict],
    extra_context: dict[str, Any] | None = None,
    transform_insights: bool = False,
) -> str:
    """Render a note template with shared structure."""
    renderer = get_renderer()

    formatted_insights: list[dict] = []
    if transform_insights:
        for insight in insights:
            timestamp = insight.get("timestamp", "")
            idea = insight.get("idea", "")
            timestamp_link = format_timestamp_link(link, timestamp)
            formatted_insights.append({**insight, "timestamp_link": timestamp_link, "idea": idea})
    else:
        formatted_insights = [dict(i) for i in insights]

    context: dict[str, Any] = {
        **payload,
        "link": link,
        "type": note_type,
        "insights": formatted_insights,
    }

    if extra_context:
        context.update(extra_context)

    return renderer.render(template_name, context)


def render_note(
    context: NoteContext,
    *,
    template_name: str,
    note_type: str,
    transform_quotes: bool = False,
) -> str:
    """Render a note for the provided context."""
    payload = _payload_from_context(context)

    extra_context: dict[str, Any] | None = None
    if context.guests:
        extra_context = {"guests": list(context.guests)}

    return _render_note(
        template_name,
        note_type=note_type,
        link=context.link,
        payload=payload,
        insights=context.insights,
        extra_context=extra_context,
        transform_insights=transform_quotes,
    )


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
        # Git add any new or modified files under the repo path
        subprocess.run(
            ["git", "add", "."],
            cwd=repo_path,
            check=True,
            capture_output=True,
        )

        # Check if anything ended up staged; skip commit/push if clean
        status = subprocess.run(
            ["git", "status", "--porcelain"],
            cwd=repo_path,
            check=True,
            capture_output=True,
            text=True,
        )
        if not status.stdout.strip():
            logger.info("No changes to commit")
            return

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
