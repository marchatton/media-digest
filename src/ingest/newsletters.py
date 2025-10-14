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


def _extract_payload_text(payload: dict) -> tuple[str | None, str | None]:
    """Extract text/html and text/plain recursively from a Gmail message payload.

    Returns (body_html, body_text).
    """
    body_html: str | None = None
    body_text: str | None = None

    def walk(part: dict):
        nonlocal body_html, body_text
        if not part:
            return
        mime_type = part.get("mimeType", "")
        body = part.get("body", {})
        data = body.get("data")
        parts = part.get("parts")

        if data and isinstance(data, str):
            import base64
            decoded = base64.urlsafe_b64decode(data).decode("utf-8", errors="ignore")
            if mime_type == "text/html" and not body_html:
                body_html = decoded
            elif mime_type == "text/plain" and not body_text:
                body_text = decoded
        if parts and isinstance(parts, list):
            for child in parts:
                walk(child)

    walk(payload)
    return body_html, body_text


def _build_query(labels: list[str], since_date: str | None) -> str:
    query_parts: list[str] = []
    if labels:
        label_query = " OR ".join([f"label:{label}" for label in labels])
        query_parts.append(f"({label_query})")
    if since_date:
        query_parts.append(f"after:{since_date.replace('-', '/')}")
    return " ".join(query_parts)


def discover_newsletters(
    service,
    labels: list[str],
    since_date: str | None = None,
):
    """Discover newsletters from Gmail with pagination and robust MIME parsing."""
    query = _build_query(labels, since_date)
    logger.info(f"Gmail query: {query}")

    try:
        messages: list[dict] = []
        request = service.users().messages().list(userId="me", q=query, maxResults=500)
        while request is not None:
            results = request.execute()
            msgs = results.get("messages", [])
            messages.extend(msgs)
            request = service.users().messages().list_next(previous_request=request, previous_response=results)

        logger.info(f"Found {len(messages)} newsletters")

        for msg in messages:
            msg_id = msg["id"]
            message = service.users().messages().get(userId="me", id=msg_id, format="full").execute()

            headers = {h["name"]: h["value"] for h in message.get("payload", {}).get("headers", [])}
            subject = headers.get("Subject", "No Subject")
            sender = headers.get("From", "Unknown")
            date_str = headers.get("Date", "")
            message_id = headers.get("Message-ID", msg_id)

            # Parse date
            from datetime import datetime
            try:
                date_obj = datetime.strptime(date_str.split(" (")[0].strip(), "%a, %d %b %Y %H:%M:%S %z")
                date_iso = date_obj.isoformat()
            except Exception:
                date_iso = date_str

            body_html, body_text = _extract_payload_text(message.get("payload", {}))

            # Try to find web version link (fallback heuristic)
            link = None
            if body_html and "http" in body_html:
                import re
                match = re.search(r'href="(https?://[^"]+(?:view|browser|web)[^"]*)"', body_html, re.IGNORECASE)
                if match:
                    link = match.group(1)

            yield Newsletter(
                message_id=message_id,
                subject=subject,
                sender=sender,
                date=date_iso,
                body_html=body_html,
                body_text=body_text,
                link=link,
            )

    except Exception as e:
        logger.error(f"Failed to discover newsletters: {e}")
        return


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
