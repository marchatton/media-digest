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
    get_episodes_for_summarization,
    get_newsletters_for_summarization,
    get_summarized_episodes,
    get_summarized_newsletters,
    save_transcript,
    save_summary,
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

    # Get items needing summarization
    episodes = get_episodes_for_summarization(conn, limit=args.limit)
    newsletters = get_newsletters_for_summarization(conn, limit=args.limit)

    logger.info(f"Found {len(episodes)} episodes and {len(newsletters)} newsletters to summarize")

    # Summarize episodes
    for episode in episodes:
        guid = episode["guid"]
        title = episode["title"]
        author = episode.get("author", "Unknown")
        publish_date = episode.get("publish_date", "")
        transcript_text = episode["transcript_text"]

        try:
            logger.info(f"Summarizing episode: {title}")

            # Clean transcript (calculate duration from transcript length as estimate)
            duration = "~30 min"  # Placeholder
            cleaned = clean_transcript(title=title, duration=duration, raw_transcript=transcript_text)

            # Summarize
            summary_result = summarize_content(
                content_type="podcast",
                title=title,
                author=author,
                date=publish_date,
                content_text=cleaned
            )

            # Rate
            rating_result = rate_content(
                content_type="podcast",
                title=title,
                summary=summary_result.summary,
                key_topics=summary_result.key_topics,
            )

            # Save to database
            save_summary(
                conn,
                item_id=guid,
                item_type="podcast",
                summary=summary_result.summary,
                key_topics=json.dumps(summary_result.key_topics),
                companies=json.dumps([c.model_dump() for c in summary_result.companies]),
                tools=json.dumps([t.model_dump() for t in summary_result.tools]),
                quotes=json.dumps([q.model_dump() for q in summary_result.quotes]),
                raw_rating=rating_result.rating,
                final_rating=rating_result.rating,  # For now, no calibration
            )

            logger.info(f"Completed summarization: {title}")

        except Exception as e:
            logger.error(f"Failed to summarize {title}: {e}")

    # Summarize newsletters
    for newsletter in newsletters:
        message_id = newsletter["message_id"]
        subject = newsletter["subject"]
        sender = newsletter.get("sender", "Unknown")
        date = newsletter.get("date", "")

        # Load parsed text from file
        newsletter_dir = Path("blobs/newsletters")
        parsed_file = newsletter_dir / f"{message_id}.json"

        if not parsed_file.exists():
            logger.warning(f"No parsed text for newsletter: {subject}")
            continue

        with open(parsed_file, "r") as f:
            parsed_data = json.load(f)
            parsed_text = parsed_data.get("text", "")

        try:
            logger.info(f"Summarizing newsletter: {subject}")

            # Summarize (no cleaning needed for newsletters)
            summary_result = summarize_content(
                content_type="newsletter",
                title=subject,
                author=sender,
                date=date,
                content_text=parsed_text
            )

            # Rate
            rating_result = rate_content(
                content_type="newsletter",
                title=subject,
                summary=summary_result.summary,
                key_topics=summary_result.key_topics,
            )

            # Save to database
            save_summary(
                conn,
                item_id=message_id,
                item_type="newsletter",
                summary=summary_result.summary,
                key_topics=json.dumps(summary_result.key_topics),
                companies=json.dumps([c.model_dump() for c in summary_result.companies]),
                tools=json.dumps([t.model_dump() for t in summary_result.tools]),
                quotes=json.dumps([q.model_dump() for q in summary_result.quotes]),
                raw_rating=rating_result.rating,
                final_rating=rating_result.rating,  # For now, no calibration
            )

            logger.info(f"Completed summarization: {subject}")

        except Exception as e:
            logger.error(f"Failed to summarize {subject}: {e}")

    logger.info("Summarization complete")


def cmd_export(args):
    """Export notes to Obsidian and push to Git."""
    logger.info("Exporting to Obsidian...")

    conn = get_connection()
    output_dir = Path(config.output_repo_path)

    # Get items with summaries
    episodes = get_summarized_episodes(conn, limit=args.limit)
    newsletters = get_summarized_newsletters(conn, limit=args.limit)

    logger.info(f"Exporting {len(episodes)} episodes and {len(newsletters)} newsletters")

    # Export episodes
    for episode in episodes:
        try:
            # Parse JSON fields
            key_topics = json.loads(episode.get("key_topics", "[]"))
            companies = json.loads(episode.get("companies", "[]"))
            tools = json.loads(episode.get("tools", "[]"))
            quotes = json.loads(episode.get("quotes", "[]"))

            # Render note
            note_content = render_episode_note(
                title=episode["title"],
                date=episode["publish_date"],
                authors=[episode.get("author", "Unknown")],
                guests=[],  # No guest extraction in MVP
                link=episode.get("audio_url", ""),
                version=episode["guid"],
                rating_llm=episode.get("final_rating", 0),
                summary=episode["summary"],
                key_topics=key_topics,
                companies=companies,
                tools=tools,
                quotes=quotes,
            )

            # Write to output directory
            note_filename = f"{episode['publish_date']}_{episode['guid'][:8]}.md"
            note_path = output_dir / note_filename
            write_note(note_path, note_content)

            logger.info(f"Exported episode: {episode['title']}")

        except Exception as e:
            logger.error(f"Failed to export episode {episode['title']}: {e}")

    # Export newsletters
    for newsletter in newsletters:
        try:
            # Parse JSON fields
            newsletter["key_topics"] = json.loads(newsletter.get("key_topics", "[]"))
            newsletter["companies"] = json.loads(newsletter.get("companies", "[]"))
            newsletter["tools"] = json.loads(newsletter.get("tools", "[]"))
            newsletter["quotes"] = json.loads(newsletter.get("quotes", "[]"))

            # Render note
            note_content = render_newsletter_note(newsletter)

            # Write to output directory
            note_filename = f"{newsletter['date']}_{newsletter['message_id'][:8]}.md"
            note_path = output_dir / note_filename
            write_note(note_path, note_content)

            logger.info(f"Exported newsletter: {newsletter['subject']}")

        except Exception as e:
            logger.error(f"Failed to export newsletter {newsletter['subject']}: {e}")

    # Git commit and push
    if args.push:
        try:
            git_commit_and_push(output_dir, f"Export notes - {datetime.now().strftime('%Y-%m-%d')}")
            logger.info("Pushed to Git")
        except Exception as e:
            logger.error(f"Failed to push to Git: {e}")

    logger.info("Export complete")


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
    export_parser.add_argument("--limit", type=int, help="Limit number of items to export")
    export_parser.add_argument("--push", action="store_true", help="Push to Git after export")
    export_parser.set_defaults(func=cmd_export)

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
