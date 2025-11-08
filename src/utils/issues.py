"""Helpers for recording operational issues for surfacing in digests.

Writes to logs/discovery_issues.json to align with existing daily digest loader.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ISSUES_PATH = Path("logs/discovery_issues.json")


def _read_issues_payload() -> dict[str, Any]:
    if not ISSUES_PATH.exists():
        return {"timestamp": datetime.now(timezone.utc).isoformat(), "issues": []}
    try:
        data = json.loads(ISSUES_PATH.read_text())
        if not isinstance(data, dict):
            return {"timestamp": datetime.now(timezone.utc).isoformat(), "issues": []}
        if "issues" not in data or not isinstance(data.get("issues"), list):
            data["issues"] = []
        return data
    except Exception:
        # If file is corrupt, start fresh
        return {"timestamp": datetime.now(timezone.utc).isoformat(), "issues": []}


def _write_issues_payload(payload: dict[str, Any]) -> None:
    ISSUES_PATH.parent.mkdir(parents=True, exist_ok=True)
    ISSUES_PATH.write_text(json.dumps(payload, indent=2))


def record_llm_credit_exhaustion(message: str) -> None:
    """Append an Anthropic credit exhaustion issue to the discovery issues log.

    The daily digest already surfaces entries from this file under
    "Discovery Issues", so we piggyback on the same mechanism.
    """
    payload = _read_issues_payload()
    issues: list[dict[str, Any]] = payload.get("issues", [])

    entry = {
        "feed_url": "anthropic",
        "error": f"Credits/Payment issue: {message}",
    }

    # Simple de-duplication: avoid appending identical consecutive entries
    if not issues or issues[-1] != entry:
        issues.append(entry)

    payload["timestamp"] = datetime.now(timezone.utc).isoformat()
    payload["issues"] = issues
    _write_issues_payload(payload)

