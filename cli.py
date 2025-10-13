#!/usr/bin/env python3
"""Media Digest CLI - Main entry point."""

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path

from src.config import config
from src.db.connection import get_connection, close_connection
from src.db.queries import (
    upsert_episode,
    upsert_newsletter,
    update_episode_status,
    update_newsletter_status,
    get_pending_episodes,
    get_pending_newsletters,
    save_transcript,
    save_summary,
    get_items_needing_summary,
)
from src.export.digest import generate_daily_digest, write_digest
from src.export.obsidian import (
    render_episode_note,
    render_newsletter_note,
    write_note,
    git_commit_and_push,
)
from src.ingest.podcasts import discover_all_episodes
from src.ingest.newsletters import discover_all_newsletters
from src.logging_config import setup_logging, get_logger
from src.process.audio import download_audio
from src.process.newsletter_parser import parse_newsletter, save_parsed_newsletter
from src.process.transcriber import WhisperTranscriber, save_transcript as save_transcript_file
from src.summarize.summarizer import clean_transcript, summarize_content
from src.summarize.rater import rate_content

# Set up logging
setup_logging()
logger = get_logger(__name__)


def cmd_discover(args):
    """Discover new episodes and newsletters."""
    logger.info(f"Discovering content since {args.since}")

    conn = get_connection()

    # Discover podcasts
    if config.podcasts_opml.exists():
        logger.info(f"Discovering podcasts from {config.podcasts_opml}")
        episodes = discover_all_episodes(config.podcasts_opml, since_date=args.since)

        for episode in episodes:
            try:
                upsert_episode(
                    conn,
                    guid=episode.guid,
                    feed_url=episode.feed_url,
                    title=episode.title,
                    publish_date=episode.publish_date,
                    author=episode.author,
                    audio_url=episode.audio_url,
                    video_url=episode.video_url,
                )
            except Exception as e:
                logger.error(f"Failed to insert episode {episode.title}: {e}")

        logger.info(f"Discovered {len(episodes)} podcast episodes")
    else:
        logger.warning(f"OPML file not found: {config.podcasts_opml}")

    # Discover newsletters
    try:
        logger.info(f"Discovering newsletters from Gmail")
        newsletters = discover_all_newsletters(
            token_path=config.gmail_token_path,
            labels=config.gmail_labels,
            since_date=args.since,
        )

        for newsletter in newsletters:
            try:
                upsert_newsletter(
                    conn,
                    message_id=newsletter.message_id,
                    subject=newsletter.subject,
                    sender=newsletter.sender,
                    date=newsletter.date,
                    body_html=newsletter.body_html,
                    body_text=newsletter.body_text,
                    link=newsletter.link,
                )
            except Exception as e:
                logger.error(f"Failed to insert newsletter {newsletter.subject}: {e}")

        logger.info(f"Discovered {len(newsletters)} newsletters")
    except Exception as e:
        logger.error(f"Failed to discover newsletters: {e}")

    logger.info("Discovery complete")


def cmd_process_audio(args):
    """Process pending audio (download + transcribe)."""
    logger.info("Processing audio...")

    conn = get_connection()
    pending = get_pending_episodes(conn, limit=args.limit)

    logger.info(f"Found {len(pending)} pending episodes")

    # Initialize Whisper
    transcriber = WhisperTranscriber(
        model_size=config.asr_model,
        compute_type=config.asr_compute_type,
        device="cpu",
    )

    audio_dir = Path("blobs/audio")
    transcript_dir = Path("blobs/transcripts")

    for episode in pending:
        guid = episode["guid"]
        title = episode["title"]
        audio_url = episode["audio_url"]

        if not audio_url:
            logger.warning(f"No audio URL for episode: {title}")
            update_episode_status(conn, guid, "failed", "No audio URL")
            continue

        try:
            logger.info(f"Processing: {title}")
            update_episode_status(conn, guid, "in_progress")

            # Download audio
            audio_file = download_audio(audio_url, audio_dir, guid)

            # Transcribe
            transcript = transcriber.transcribe(audio_file)

            # Save transcript
            transcript_path = transcript_dir / f"{guid}.json"
            save_transcript_file(transcript, transcript_path)

            # Save to database
            save_transcript(conn, guid, transcript["text"], str(transcript_path))

            # Update status
            update_episode_status(conn, guid, "completed")

            logger.info(f"Completed: {title}")

        except Exception as e:
            logger.error(f"Failed to process {title}: {e}")
            update_episode_status(conn, guid, "failed", str(e))

    logger.info("Audio processing complete")


def cmd_process_newsletters(args):
    """Process pending newsletters (parse)."""
    logger.info("Processing newsletters...")

    conn = get_connection()
    pending = get_pending_newsletters(conn, limit=args.limit)

    logger.info(f"Found {len(pending)} pending newsletters")

    newsletter_dir = Path("blobs/newsletters")

    for newsletter in pending:
        message_id = newsletter["message_id"]
        subject = newsletter["subject"]
        body_html = newsletter["body_html"]
        body_text = newsletter["body_text"]

        try:
            logger.info(f"Processing: {subject}")
            update_newsletter_status(conn, message_id, "in_progress")

            # Parse newsletter
            parsed_text = parse_newsletter(body_html, body_text)

            # Extract/get link
            link = newsletter.get("link")

            # Save parsed text
            save_parsed_newsletter(message_id, parsed_text, link, newsletter_dir)

            # Update status
            update_newsletter_status(conn, message_id, "completed")

            logger.info(f"Completed: {subject}")

        except Exception as e:
            logger.error(f"Failed to process {subject}: {e}")
            update_newsletter_status(conn, message_id, "failed", str(e))

    logger.info("Newsletter processing complete")


def cmd_summarize(args):
    """Summarize completed items."""
    logger.info("Summarizing content...")

    conn = get_connection()
    items = get_items_needing_summary(conn, limit=args.limit)

    logger.info(f"Found {len(items)} items to summarize")

    for item in items:
        item_type = item["item_type"]
        item_id = item["id"]
        title = item["title"]
        author = item.get("author", "")
        date = item.get("date", "")
        link = item.get("link", "")

        try:
            logger.info(f"Summarizing {item_type}: {title}")
            # Load content text
            if item_type == "podcast":
                row = conn.execute("SELECT transcript_text FROM transcripts WHERE episode_guid = ?", (item_id,)).fetchone()
                if not row:
                    logger.warning(f"No transcript for {item_id}, skipping")
                    continue
                content_text = row[0]
            else:
                row = conn.execute("SELECT body_text FROM newsletters WHERE message_id = ?", (item_id,)).fetchone()
                content_text = row[0] if row and row[0] else ""

            if not content_text:
                logger.warning(f"Empty content for {item_id}, skipping")
                continue

            summary_resp = summarize_content(
                content_type=item_type,
                title=title,
                author=author,
                date=date,
                content_text=content_text,
            )

            rating_resp = rate_content(
                content_type=item_type,
                title=title,
                summary=summary_resp.summary,
                key_topics=summary_resp.key_topics,
            )

            import json as _json
            save_summary(
                conn,
                item_id=item_id,
                item_type=item_type,
                summary=summary_resp.summary,
                key_topics=_json.dumps(summary_resp.key_topics),
                companies=_json.dumps([c.dict() for c in summary_resp.companies]),
                tools=_json.dumps([t.dict() for t in summary_resp.tools]),
                quotes=_json.dumps([q.dict() for q in summary_resp.quotes]),
                raw_rating=rating_resp.rating,
                final_rating=rating_resp.rating,
            )

            logger.info(f"Saved summary for {item_type} {item_id}")

        except Exception as e:
            logger.error(f"Failed to summarize {item_type} {item_id}: {e}")


def cmd_export(args):
    """Export notes to Obsidian and push to Git."""
    logger.info("Exporting to Obsidian...")

    # TODO: Implement full export logic
    # For now, this is a placeholder
    logger.warning("Export not yet fully implemented")


def cmd_build_daily(args):
    """Generate daily digest for a date."""
    logger.info(f"Building daily digest for {args.date}")
    # Placeholder: integrate with DB once summaries exist
    content = generate_daily_digest(datetime.now(), items=[], failures=[], themes=[], actionables=[])
    output_dir = config.output_repo_path / config.export_output_path
    output_path = output_dir / f"daily-{datetime.now().strftime('%Y-%m-%d')}.md"
    write_digest(output_path, content)
    logger.info("Daily digest generated (placeholder)")


def cmd_build_weekly(args):
    """Generate weekly digest ending at a date."""
    logger.info(f"Building weekly digest ending {args.ending}")
    # Placeholder: integrate with DB once summaries exist
    content = generate_daily_digest(datetime.now(), items=[], failures=[], themes=[], actionables=[])
    output_dir = config.output_repo_path / config.export_output_path
    output_path = output_dir / f"weekly-{datetime.now().strftime('%Y-%m-%d')}.md"
    write_digest(output_path, content)
    logger.info("Weekly digest generated (placeholder)")


def cmd_retry(args):
    """Retry a failed item by ID (placeholder)."""
    logger.info(f"Retry requested for item: {args.item_id}")
    logger.warning("Retry not yet implemented")


def cmd_skip(args):
    """Skip an item permanently by ID (placeholder)."""
    logger.info(f"Skip requested for item: {args.item_id}")
    logger.warning("Skip not yet implemented")


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(description="Media Digest CLI")
    subparsers = parser.add_subparsers(dest="command", required=True)

    # Discover command
    discover_parser = subparsers.add_parser("discover", help="Discover new content")
    discover_parser.add_argument("--since", default=config.start_date, help="Discover since date (YYYY-MM-DD)")
    discover_parser.set_defaults(func=cmd_discover)

    # Process audio command
    audio_parser = subparsers.add_parser("process-audio", help="Process audio (download + transcribe)")
    audio_parser.add_argument("--limit", type=int, help="Limit number of episodes to process")
    audio_parser.set_defaults(func=cmd_process_audio)

    # Process newsletters command
    newsletter_parser = subparsers.add_parser("process-newsletters", help="Process newsletters")
    newsletter_parser.add_argument("--limit", type=int, help="Limit number of newsletters to process")
    newsletter_parser.set_defaults(func=cmd_process_newsletters)

    # Summarize command
    summarize_parser = subparsers.add_parser("summarize", help="Summarize completed content")
    summarize_parser.add_argument("--limit", type=int, help="Limit number of items to summarize")
    summarize_parser.set_defaults(func=cmd_summarize)

    # Export command
    export_parser = subparsers.add_parser("export", help="Export to Obsidian")
    export_parser.set_defaults(func=cmd_export)

    # Build daily command
    daily_parser = subparsers.add_parser("build-daily", help="Generate daily digest")
    daily_parser.add_argument("--date", default="today", help="Date for digest (YYYY-MM-DD or 'today')")
    daily_parser.set_defaults(func=cmd_build_daily)

    # Build weekly command
    weekly_parser = subparsers.add_parser("build-weekly", help="Generate weekly digest")
    weekly_parser.add_argument("--ending", default="today", help="Week ending date (YYYY-MM-DD or 'today')")
    weekly_parser.set_defaults(func=cmd_build_weekly)

    # Retry command
    retry_parser = subparsers.add_parser("retry", help="Retry a failed item by ID")
    retry_parser.add_argument("--item-id", required=True, help="Item ID to retry")
    retry_parser.set_defaults(func=cmd_retry)

    # Skip command
    skip_parser = subparsers.add_parser("skip", help="Skip an item permanently by ID")
    skip_parser.add_argument("--item-id", required=True, help="Item ID to skip")
    skip_parser.set_defaults(func=cmd_skip)

    # Parse args
    args = parser.parse_args()

    try:
        # Execute command
        args.func(args)
    except Exception as e:
        logger.error(f"Command failed: {e}", exc_info=True)
        sys.exit(1)
    finally:
        close_connection()


if __name__ == "__main__":
    main()
