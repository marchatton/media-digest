"""Light tests for newsletter parsing (MIME recursion and link extraction)."""

from src.ingest.newsletters import _extract_payload_text


def test_extract_payload_text_recursive_html_and_text():
    payload = {
        "mimeType": "multipart/alternative",
        "parts": [
            {
                "mimeType": "text/plain",
                "body": {"data": "VGhpcyBpcyBwbGFpbiB0ZXh0"},  # base64 of 'This is plain text'
            },
            {
                "mimeType": "text/html",
                "body": {"data": "PGRpdj52aWV3IGluIGJyb3dzZXI8L2Rpdj4="},  # base64 of '<div>view in browser</div>'
            },
        ],
    }

    html, text = _extract_payload_text(payload)
    assert text.startswith("This is plain text")
    assert "view in browser" in (html or "")
