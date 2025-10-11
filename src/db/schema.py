"""Database schema definitions for Media Digest."""

SCHEMA_VERSION = 1

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
    created_at TIMESTAMP DEFAULT (now()),
    FOREIGN KEY (episode_guid) REFERENCES episodes(guid)
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
    created_at TIMESTAMP DEFAULT (now()),
    FOREIGN KEY (item_id) REFERENCES episodes(guid)
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


def init_schema(conn) -> None:
    """Initialize database schema.

    Args:
        conn: DuckDB connection
    """
    for table_sql in ALL_TABLES:
        conn.execute(table_sql)

    # Insert schema version if not exists
    result = conn.execute("SELECT version FROM schema_version WHERE version = ?", (SCHEMA_VERSION,)).fetchone()
    if not result:
        conn.execute("INSERT INTO schema_version (version) VALUES (?)", (SCHEMA_VERSION,))

    conn.commit()
