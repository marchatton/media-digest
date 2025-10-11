"""Database schema definitions for Media Digest."""

SCHEMA_VERSION = 2

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
    updated_at TIMESTAMP DEFAULT (now()),
    exported_at TIMESTAMP
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
    updated_at TIMESTAMP DEFAULT (now()),
    exported_at TIMESTAMP
)
"""

CREATE_TRANSCRIPTS_TABLE = """
CREATE SEQUENCE IF NOT EXISTS transcripts_seq START 1;
CREATE TABLE IF NOT EXISTS transcripts (
    id INTEGER PRIMARY KEY DEFAULT nextval('transcripts_seq'),
    episode_guid TEXT UNIQUE NOT NULL,
    transcript_text TEXT NOT NULL,
    transcript_path TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT (now()),
    FOREIGN KEY (episode_guid) REFERENCES episodes(guid)
)
"""

CREATE_SUMMARIES_TABLE = """
CREATE SEQUENCE IF NOT EXISTS summaries_seq START 1;
CREATE TABLE IF NOT EXISTS summaries (
    id INTEGER PRIMARY KEY DEFAULT nextval('summaries_seq'),
    item_id TEXT UNIQUE NOT NULL,
    item_type TEXT NOT NULL,
    summary TEXT NOT NULL,
    key_topics TEXT,
    companies TEXT,
    tools TEXT,
    quotes TEXT,
    raw_rating INTEGER,
    final_rating INTEGER,
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


def get_current_schema_version(conn) -> int:
    """Get current schema version from database.

    Args:
        conn: DuckDB connection

    Returns:
        Current schema version (0 if no version table exists)
    """
    try:
        result = conn.execute("SELECT MAX(version) FROM schema_version").fetchone()
        return result[0] if result and result[0] is not None else 0
    except Exception:
        # Table doesn't exist yet
        return 0


def migrate_v1_to_v2(conn) -> None:
    """Migration from v1 to v2: Add exported_at columns.

    Args:
        conn: DuckDB connection
    """
    # Check if columns already exist
    episodes_cols = conn.execute("DESCRIBE episodes").fetchall()
    episodes_col_names = [col[0] for col in episodes_cols]

    if "exported_at" not in episodes_col_names:
        conn.execute("ALTER TABLE episodes ADD COLUMN exported_at TIMESTAMP")

    newsletters_cols = conn.execute("DESCRIBE newsletters").fetchall()
    newsletters_col_names = [col[0] for col in newsletters_cols]

    if "exported_at" not in newsletters_col_names:
        conn.execute("ALTER TABLE newsletters ADD COLUMN exported_at TIMESTAMP")

    conn.commit()


def run_migrations(conn) -> None:
    """Run all pending migrations.

    Args:
        conn: DuckDB connection
    """
    current_version = get_current_schema_version(conn)

    # Apply migrations in order
    if current_version < 2:
        migrate_v1_to_v2(conn)
        conn.execute("INSERT INTO schema_version (version) VALUES (2)")
        conn.commit()


def init_schema(conn) -> None:
    """Initialize database schema and run migrations.

    Args:
        conn: DuckDB connection
    """
    # Create tables
    for table_sql in ALL_TABLES:
        conn.execute(table_sql)

    # Insert initial schema version if not exists
    current_version = get_current_schema_version(conn)
    if current_version == 0:
        conn.execute("INSERT INTO schema_version (version) VALUES (1)")
        conn.commit()

    # Run any pending migrations
    run_migrations(conn)

    conn.commit()
