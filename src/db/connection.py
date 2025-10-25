"""Database connection management for Media Digest."""

import duckdb
from pathlib import Path

from src.db.schema import init_schema
from src.logging_config import get_logger

logger = get_logger(__name__)

_connection = None


def get_connection(db_path: str = "digestor.duckdb") -> duckdb.DuckDBPyConnection:
    """Get or create database connection.

    Args:
        db_path: Path to DuckDB database file

    Returns:
        DuckDB connection
    """
    global _connection

    if _connection is None:
        logger.info(f"Connecting to database: {db_path}")
        db_file = Path(db_path)

        # Create database file if it doesn't exist
        is_new = not db_file.exists()

        _connection = duckdb.connect(str(db_file))

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
