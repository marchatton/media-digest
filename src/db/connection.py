"""Database connection management for Media Digest."""

from __future__ import annotations

from pathlib import Path

import duckdb

from src.config import config
from src.db.schema import init_schema
from src.logging_config import get_logger

logger = get_logger(__name__)

_connection: duckdb.DuckDBPyConnection | None = None


def get_connection(db_path: str | Path | None = None) -> duckdb.DuckDBPyConnection:
    """Get or create database connection.

    Args:
        db_path: Path to DuckDB database file

    Returns:
        DuckDB connection
    """
    global _connection

    if _connection is None:
        resolved_path = Path(db_path) if db_path is not None else config.db_path
        resolved_path.parent.mkdir(parents=True, exist_ok=True)

        logger.info(f"Connecting to database: {resolved_path}")

        # Create database file if it doesn't exist
        is_new = not resolved_path.exists()

        _connection = duckdb.connect(str(resolved_path))

        if is_new:
            logger.info("Initializing database schema")

        init_schema(_connection)

    return _connection


def close_connection() -> None:
    """Close database connection."""
    global _connection
    if _connection is not None:
        _connection.close()
        _connection = None
        logger.info("Database connection closed")
