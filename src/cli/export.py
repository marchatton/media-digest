"""export command implementation."""

from argparse import _SubParsersAction
import json
from datetime import datetime
from pathlib import Path

from src.cli import common
from src.config import config
from src.db.connection import get_connection
from src.export.obsidian import NoteContext, git_commit_and_push, render_note, write_note
from src.logging_config import get_logger

logger = get_logger(__name__)


def handle(args) -> None:
    logger.info("Exporting to Obsidian...")

    conn = get_connection()
    output_root = config.output_repo_path / config.export_output_path
    output_root.mkdir(parents=True, exist_ok=True)
    common.ensure_export_dirs(output_root)

    episodes = conn.execute(
        """
        SELECT e.guid, e.title, e.publish_date, coalesce(e.author,'') AS author,
               coalesce(e.video_url, e.audio_url, '') AS link,
               s.summary, s.key_topics, s.companies, s.tools, s.quotes, s.final_rating, s.structured_summary
        FROM episodes e JOIN summaries s ON s.item_id = e.guid AND s.item_type = 'podcast'
        """
    ).fetchall()
    cols = [d[0] for d in conn.description]

    for row in episodes:
        rec = dict(zip(cols, row))

        key_topics = json.loads(rec["key_topics"]) if rec["key_topics"] else []
        companies = json.loads(rec["companies"]) if rec["companies"] else []
        tools = json.loads(rec["tools"]) if rec["tools"] else []
        insights = json.loads(rec["quotes"]) if rec["quotes"] else []
        structured = json.loads(rec.get("structured_summary") or "{}")

        note_context = NoteContext(
            title=rec["title"],
            date=rec["publish_date"],
            authors=[rec["author"]] if rec["author"] else [],
            link=rec["link"],
            version=rec["guid"],
            rating_llm=rec["final_rating"] or 0,
            summary=rec["summary"],
            key_topics=key_topics,
            companies=companies,
            tools=tools,
            insights=insights,
            takeaways=structured.get("takeaways") or [],
            memorable_moments=structured.get("memorable_moments") or [],
            overview=structured.get("episode_overview"),
            wildcard=structured.get("wildcard"),
            guests=[],
        )

        note = render_note(
            note_context,
            template_name="episode.md.j2",
            note_type="podcast",
            transform_quotes=True,
        )

        rel_note_path = common.podcast_relative_path(
            rec.get("publish_date"),
            rec.get("author"),
            rec["title"],
        )
        note_path = output_root / rel_note_path
        write_note(note_path, note, check_edit=True)

    if getattr(args, "dry_run", False):
        logger.info("Dry-run enabled: skipping git commit/push")
    else:
        commit_msg = f"Digest export {datetime.now().strftime('%Y-%m-%d')}"
        git_commit_and_push(config.output_repo_path, commit_msg)


def register(subparsers: _SubParsersAction) -> None:
    parser = subparsers.add_parser("export", help="Export to Obsidian")
    parser.add_argument("--dry-run", action="store_true", help="Do not write files; preview only")
    parser.set_defaults(func=handle)

    export_alias = subparsers.add_parser("export-obsidian", help="Export to Obsidian (alias)")
    export_alias.add_argument("--dry-run", action="store_true", help="Do not write files; preview only")
    export_alias.set_defaults(func=handle)
