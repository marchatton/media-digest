"""Tests for Media Digest."""

from __future__ import annotations

import os
from pathlib import Path


def _ensure_env(name: str, value: str) -> None:
    os.environ.setdefault(name, value)


tmp_root = Path(os.getenv("PYTEST_TMPDIR", "/tmp"))

_ensure_env("GMAIL_ADDRESS", "test@example.com")
_ensure_env("GMAIL_OAUTH_TOKEN_PATH", str(tmp_root / "gmail-token.json"))
_ensure_env("VAULT_ROOT", str(tmp_root / "vault"))
_ensure_env("OUTPUT_REPO_PATH", str(tmp_root / "output"))
_ensure_env("ANTHROPIC_API_KEY", "test-key")
_ensure_env("START_DATE", "2025-10-01")
_ensure_env("TIMEZONE", "UTC")
_ensure_env("VAR_ROOT", str(tmp_root / "var"))
