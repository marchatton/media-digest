"""Database schema definitions for Media Digest."""

from __future__ import annotations

SCHEMA_VERSION = 3

CREATE_EPISODES_TABLE = """
CREATE TABLE IF NOT EXISTS episodes (
    guid TEXT PRIMARY KEY,
    feed_url TEXT NOT NULL,
    title TEXT NOT NULL,
    publish_date TEXT NOT NULL,
    author TEXT,
    audio_url TEXT,
    video_url TEXT,
    status TEXT NOT NULL DEFAULT 'pending',
    error_reason TEXT,
    created_at TIMESTAMP DEFAULT (now()),
    updated_at TIMESTAMP DEFAULT (now())
)
"""

CREATE_NEWSLETTERS_TABLE = """
CREATE TABLE IF NOT EXISTS newsletters (
    message_id TEXT PRIMARY KEY,
    subject TEXT NOT NULL,
    sender TEXT NOT NULL,
    date TEXT NOT NULL,
    body_html TEXT,
    body_text TEXT,
    link TEXT,
    status TEXT NOT NULL DEFAULT 'pending',
    error_reason TEXT,
    created_at TIMESTAMP DEFAULT (now()),
    updated_at TIMESTAMP DEFAULT (now())
)
"""

CREATE_TRANSCRIPTS_TABLE = """
CREATE TABLE IF NOT EXISTS transcripts (
    episode_guid TEXT PRIMARY KEY,
    transcript_text TEXT NOT NULL,
    transcript_path TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT (now())
)
"""

CREATE_SUMMARIES_TABLE = """
CREATE TABLE IF NOT EXISTS summaries (
    item_id TEXT PRIMARY KEY,
    item_type TEXT NOT NULL,
    summary TEXT NOT NULL,
    key_topics TEXT,
    companies TEXT,
    tools TEXT,
    quotes TEXT,
    raw_rating INTEGER,
    final_rating INTEGER,
    structured_summary TEXT,
    created_at TIMESTAMP DEFAULT (now())
)
"""

CREATE_SCHEMA_VERSION_TABLE = """
CREATE TABLE IF NOT EXISTS schema_version (
    version INTEGER PRIMARY KEY,
    applied_at TIMESTAMP DEFAULT (now())
)
"""

ALL_TABLES = [
    CREATE_SCHEMA_VERSION_TABLE,
    CREATE_EPISODES_TABLE,
    CREATE_NEWSLETTERS_TABLE,
    CREATE_TRANSCRIPTS_TABLE,
    CREATE_SUMMARIES_TABLE,
]

# Helpful indexes for query performance
CREATE_INDEXES = [
    # Speed up status/date lookups
    "CREATE INDEX IF NOT EXISTS idx_episodes_status_date ON episodes(status, publish_date)",
    "CREATE INDEX IF NOT EXISTS idx_newsletters_status_date ON newsletters(status, date)",
    # Summaries lookup by type/id
    "CREATE INDEX IF NOT EXISTS idx_summaries_item ON summaries(item_type, item_id)",
]


def init_schema(conn) -> None:
    """Initialize database schema (idempotent) and run migrations."""

    for table_sql in ALL_TABLES:
        conn.execute(table_sql)

    for index_sql in CREATE_INDEXES:
        conn.execute(index_sql)

    row = conn.execute("SELECT MAX(version) FROM schema_version").fetchone()
    current_version = row[0] if row and row[0] is not None else None

    if current_version is None:
        conn.execute("INSERT INTO schema_version (version) VALUES (?)", (SCHEMA_VERSION,))
        conn.commit()
        return

    if current_version < SCHEMA_VERSION:
        apply_migrations(conn, current_version)
        conn.execute("INSERT INTO schema_version (version) VALUES (?)", (SCHEMA_VERSION,))
        conn.commit()


def apply_migrations(conn, current_version: int) -> None:
    """Run incremental migrations up to the latest schema version."""

    if current_version < 2:
        migrate_transcripts_table(conn)
        current_version = 2

    if current_version < 3:
        migrate_summaries_table(conn)


def migrate_transcripts_table(conn) -> None:
    """Recreate transcripts table without foreign key constraints."""

    table_exists = conn.execute(
        "SELECT COUNT(*) FROM information_schema.tables WHERE lower(table_name) = 'transcripts'"
    ).fetchone()[0]

    if not table_exists:
        return

    conn.execute("DROP TABLE IF EXISTS transcripts__tmp")
    conn.execute(
        """
        CREATE TABLE transcripts__tmp (
            episode_guid TEXT PRIMARY KEY,
            transcript_text TEXT NOT NULL,
            transcript_path TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT (now())
        )
        """
    )

    conn.execute(
        """
        INSERT INTO transcripts__tmp (episode_guid, transcript_text, transcript_path, created_at)
        SELECT episode_guid, transcript_text, transcript_path, created_at
        FROM transcripts
        """
    )

    conn.execute("DROP TABLE transcripts")
    conn.execute("ALTER TABLE transcripts__tmp RENAME TO transcripts")


def migrate_summaries_table(conn) -> None:
    """Add structured summary column for richer podcast notes."""

    existing = conn.execute(
        """
        SELECT COUNT(*)
        FROM information_schema.columns
        WHERE lower(table_name) = 'summaries' AND lower(column_name) = 'structured_summary'
        """
    ).fetchone()[0]

    if existing:
        return

    conn.execute("ALTER TABLE summaries ADD COLUMN structured_summary TEXT")
