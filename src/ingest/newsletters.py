"""Newsletter ingestion from Gmail."""

import base64
import os
from datetime import datetime
from pathlib import Path
from typing import Generator

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

from src.ingest.models import Newsletter
from src.logging_config import get_logger

logger = get_logger(__name__)

# Gmail API scopes
SCOPES = ["https://www.googleapis.com/auth/gmail.readonly"]


def get_gmail_service(token_path: Path, credentials_path: Path | None = None):
    """Get authenticated Gmail API service.

    Args:
        token_path: Path to token.json file
        credentials_path: Path to credentials.json file (for initial OAuth flow)

    Returns:
        Gmail API service
    """
    creds = None

    # Load existing token
    if token_path.exists():
        creds = Credentials.from_authorized_user_file(str(token_path), SCOPES)

    # Refresh or get new token
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            logger.info("Refreshing Gmail OAuth token")
            creds.refresh(Request())
        else:
            if not credentials_path or not credentials_path.exists():
                raise FileNotFoundError(
                    f"Gmail credentials file not found. "
                    f"Please download from Google Cloud Console and save to {credentials_path}"
                )

            logger.info("Starting OAuth flow")
            flow = InstalledAppFlow.from_client_secrets_file(str(credentials_path), SCOPES)
            creds = flow.run_local_server(port=0)

        # Save token
        token_path.parent.mkdir(parents=True, exist_ok=True)
        with open(token_path, "w") as token:
            token.write(creds.to_json())
        logger.info(f"Saved OAuth token to {token_path}")

    return build("gmail", "v1", credentials=creds)


def discover_newsletters(
    service,
    labels: list[str],
    since_date: str | None = None,
) -> Generator[Newsletter, None, None]:
    """Discover newsletters from Gmail.

    Args:
        service: Gmail API service
        labels: Gmail labels to search
        since_date: Only return emails after this date (YYYY-MM-DD)

    Yields:
        Newsletter objects
    """
    # Build query
    query_parts = []

    if labels:
        label_query = " OR ".join([f"label:{label}" for label in labels])
        query_parts.append(f"({label_query})")

    if since_date:
        query_parts.append(f"after:{since_date.replace('-', '/')}")

    query = " ".join(query_parts)
    logger.info(f"Gmail query: {query}")

    try:
        # Get message IDs
        results = service.users().messages().list(userId="me", q=query, maxResults=500).execute()
        messages = results.get("messages", [])

        logger.info(f"Found {len(messages)} newsletters")

        for msg in messages:
            msg_id = msg["id"]

            # Get full message
            message = service.users().messages().get(userId="me", id=msg_id, format="full").execute()

            # Extract headers
            headers = {h["name"]: h["value"] for h in message["payload"]["headers"]}

            subject = headers.get("Subject", "No Subject")
            sender = headers.get("From", "Unknown")
            date_str = headers.get("Date", "")
            message_id = headers.get("Message-ID", msg_id)

            # Parse date
            try:
                date_obj = datetime.strptime(date_str.split(" (")[0].strip(), "%a, %d %b %Y %H:%M:%S %z")
                date = date_obj.isoformat()
            except Exception:
                date = date_str

            # Extract body
            body_html = None
            body_text = None

            if "parts" in message["payload"]:
                for part in message["payload"]["parts"]:
                    mime_type = part.get("mimeType", "")
                    if "data" in part["body"]:
                        data = part["body"]["data"]
                        decoded = base64.urlsafe_b64decode(data).decode("utf-8", errors="ignore")

                        if mime_type == "text/html":
                            body_html = decoded
                        elif mime_type == "text/plain":
                            body_text = decoded
            elif "body" in message["payload"] and "data" in message["payload"]["body"]:
                data = message["payload"]["body"]["data"]
                decoded = base64.urlsafe_b64decode(data).decode("utf-8", errors="ignore")
                body_text = decoded

            # Try to find web version link
            link = None
            if body_html and "http" in body_html:
                # Simple heuristic: look for "view in browser" or similar links
                import re
                match = re.search(r'href="(https?://[^"]+(?:view|browser|web)[^"]*)"', body_html, re.IGNORECASE)
                if match:
                    link = match.group(1)

            newsletter = Newsletter(
                message_id=message_id,
                subject=subject,
                sender=sender,
                date=date,
                body_html=body_html,
                body_text=body_text,
                link=link,
            )

            yield newsletter

    except Exception as e:
        logger.error(f"Failed to discover newsletters: {e}")


def discover_all_newsletters(
    token_path: Path,
    labels: list[str],
    since_date: str | None = None,
    credentials_path: Path | None = None,
) -> list[Newsletter]:
    """Discover all newsletters from Gmail.

    Args:
        token_path: Path to OAuth token
        labels: Gmail labels to search
        since_date: Only return emails after this date
        credentials_path: Path to credentials.json (for initial OAuth)

    Returns:
        List of newsletters
    """
    service = get_gmail_service(token_path, credentials_path)
    newsletters = list(discover_newsletters(service, labels, since_date))
    logger.info(f"Total newsletters discovered: {len(newsletters)}")
    return newsletters
