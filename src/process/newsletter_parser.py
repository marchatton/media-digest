"""Newsletter HTML to plain text parsing."""

import json
import re
from pathlib import Path

from bs4 import BeautifulSoup

from src.logging_config import get_logger

logger = get_logger(__name__)


def parse_newsletter(body_html: str | None, body_text: str | None) -> str:
    """Parse newsletter body to plain text.

    Args:
        body_html: HTML body
        body_text: Plain text body

    Returns:
        Cleaned plain text
    """
    # Prefer plain text if available
    if body_text and body_text.strip():
        return clean_text(body_text)

    # Otherwise parse HTML
    if body_html and body_html.strip():
        return html_to_text(body_html)

    logger.warning("Newsletter has no body content")
    return ""


def html_to_text(html: str) -> str:
    """Convert HTML to plain text.

    Args:
        html: HTML string

    Returns:
        Plain text
    """
    try:
        soup = BeautifulSoup(html, "lxml")

        # Remove script and style elements
        for element in soup(["script", "style", "head", "title", "meta"]):
            element.decompose()

        # Get text
        text = soup.get_text(separator="\n")

        # Clean up text
        return clean_text(text)

    except Exception as e:
        logger.error(f"Failed to parse HTML: {e}")
        return ""


def clean_text(text: str) -> str:
    """Clean and normalize text.

    Args:
        text: Raw text

    Returns:
        Cleaned text
    """
    # Remove excessive whitespace
    text = re.sub(r"\n\s*\n", "\n\n", text)
    text = re.sub(r" +", " ", text)

    # Remove leading/trailing whitespace from lines
    lines = [line.strip() for line in text.split("\n")]
    text = "\n".join(lines)

    # Remove excessive blank lines
    text = re.sub(r"\n{3,}", "\n\n", text)

    return text.strip()


def extract_link(body_html: str | None) -> str | None:
    """Extract web version link from newsletter HTML.

    Args:
        body_html: HTML body

    Returns:
        Web version URL or None
    """
    if not body_html:
        return None

    try:
        soup = BeautifulSoup(body_html, "lxml")

        # Look for links with "view" or "browser" text
        for link in soup.find_all("a"):
            text = link.get_text().lower()
            href = link.get("href", "")

            if any(keyword in text for keyword in ["view in browser", "view online", "web version", "read online"]):
                if href.startswith("http"):
                    return href

        # Fallback: look for any link with "view" or "browser" in URL
        for link in soup.find_all("a"):
            href = link.get("href", "")
            if any(keyword in href.lower() for keyword in ["view", "browser", "web", "online"]):
                if href.startswith("http"):
                    return href

    except Exception as e:
        logger.warning(f"Failed to extract link: {e}")

    return None


def save_parsed_newsletter(
    message_id: str,
    parsed_text: str,
    link: str | None,
    output_dir: Path,
) -> Path:
    """Save parsed newsletter to JSON file.

    Args:
        message_id: Newsletter message ID
        parsed_text: Parsed plain text
        link: Web version link
        output_dir: Directory to save file

    Returns:
        Path to saved file
    """
    output_dir.mkdir(parents=True, exist_ok=True)

    # Sanitize filename
    safe_id = "".join(c if c.isalnum() or c in "-_" else "_" for c in message_id)
    output_path = output_dir / f"{safe_id}.json"

    data = {
        "message_id": message_id,
        "text": parsed_text,
        "link": link,
    }

    with open(output_path, "w") as f:
        json.dump(data, f, indent=2)

    logger.info(f"Saved parsed newsletter to: {output_path}")
    return output_path


def load_parsed_newsletter(file_path: Path) -> dict[str, any]:
    """Load parsed newsletter from JSON file.

    Args:
        file_path: Path to JSON file

    Returns:
        Parsed newsletter data
    """
    with open(file_path) as f:
        return json.load(f)
