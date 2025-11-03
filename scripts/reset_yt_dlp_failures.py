#!/usr/bin/env python3
"""Reset episodes failed due to missing yt-dlp binary."""

from __future__ import annotations

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.append(str(PROJECT_ROOT))

from src.db.connection import get_connection, close_connection


RESET_PATTERN = "No such file or directory: 'yt-dlp'"


def reset_missing_yt_dlp_failures() -> int:
    conn = get_connection()
    try:
        count_sql = (
            "SELECT COUNT(*) FROM episodes WHERE error_reason LIKE ?"
        )
        (pending_reset,) = conn.execute(count_sql, (f"%{RESET_PATTERN}%",)).fetchone()

        if pending_reset:
            reset_sql = (
                """
                UPDATE episodes
                SET status = 'pending',
                    error_reason = NULL,
                    updated_at = now()
                WHERE error_reason LIKE ?
                """
            )
            conn.execute(reset_sql, (f"%{RESET_PATTERN}%",))
            conn.commit()

        return int(pending_reset)
    finally:
        close_connection()


def main() -> None:
    updated = reset_missing_yt_dlp_failures()
    print(f"Reset {updated} episode(s) with missing yt-dlp failures")


if __name__ == "__main__":
    main()
