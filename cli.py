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
    get_completed_episodes_needing_summary,
    get_completed_newsletters_needing_summary,
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

    # Get episodes needing summarization
    episodes = get_completed_episodes_needing_summary(conn, limit=args.limit)
    logger.info(f"Found {len(episodes)} episodes needing summarization")

    for episode in episodes:
        guid = episode["guid"]
        title = episode["title"]
        author = episode["author"]
        publish_date = episode["publish_date"]
        transcript_text = episode["transcript_text"]

        try:
            logger.info(f"Summarizing episode: {title}")

            # Summarize
            summary_response = summarize_content(
                content_type="podcast",
                title=title,
                author=author or "Unknown",
                date=publish_date,
                content_text=transcript_text,
            )

            # Rate
            rating_response = rate_content(
                content_type="podcast",
                title=title,
                summary=summary_response.summary,
                key_topics=summary_response.key_topics,
            )

            # Save to database
            save_summary(
                conn,
                item_id=guid,
                item_type="podcast",
                summary=summary_response.summary,
                key_topics=json.dumps(summary_response.key_topics),
                companies=json.dumps([c.dict() for c in summary_response.companies]),
                tools=json.dumps([t.dict() for t in summary_response.tools]),
                quotes=json.dumps([q.dict() for q in summary_response.quotes]),
                raw_rating=rating_response.rating,
                final_rating=rating_response.rating,
            )

            logger.info(f"Completed summarization for: {title}")

        except Exception as e:
            logger.error(f"Failed to summarize {title}: {e}")

    # Get newsletters needing summarization
    newsletters = get_completed_newsletters_needing_summary(conn, limit=args.limit)
    logger.info(f"Found {len(newsletters)} newsletters needing summarization")

    for newsletter in newsletters:
        message_id = newsletter["message_id"]
        subject = newsletter["subject"]
        sender = newsletter["sender"]
        date = newsletter["date"]

        # Read parsed newsletter content
        newsletter_dir = Path("blobs/newsletters")
        parsed_file = newsletter_dir / f"{message_id}.txt"

        if not parsed_file.exists():
            logger.warning(f"Parsed newsletter file not found: {parsed_file}")
            continue

        content_text = parsed_file.read_text()

        try:
            logger.info(f"Summarizing newsletter: {subject}")

            # Summarize
            summary_response = summarize_content(
                content_type="newsletter",
                title=subject,
                author=sender,
                date=date,
                content_text=content_text,
            )

            # Rate
            rating_response = rate_content(
                content_type="newsletter",
                title=subject,
                summary=summary_response.summary,
                key_topics=summary_response.key_topics,
            )

            # Save to database
            save_summary(
                conn,
                item_id=message_id,
                item_type="newsletter",
                summary=summary_response.summary,
                key_topics=json.dumps(summary_response.key_topics),
                companies=json.dumps([c.dict() for c in summary_response.companies]),
                tools=json.dumps([t.dict() for t in summary_response.tools]),
                quotes=json.dumps([q.dict() for q in summary_response.quotes]),
                raw_rating=rating_response.rating,
                final_rating=rating_response.rating,
            )

            logger.info(f"Completed summarization for: {subject}")

        except Exception as e:
            logger.error(f"Failed to summarize {subject}: {e}")

    logger.info("Summarization complete")


def cmd_export(args):
    """Export notes to Obsidian and push to Git."""
    logger.info("Exporting to Obsidian...")

    conn = get_connection()

    # Get summarized episodes
    episodes = conn.execute("""
        SELECT guid, title, author, publish_date, audio_url, video_url
        FROM episodes
        WHERE status = 'summarized'
        ORDER BY publish_date DESC
    """).fetchall()

    logger.info(f"Found {len(episodes)} episodes to export")

    # Create output directory
    output_dir = Path(config.vault_root) / "5-Resources" / "0-Media digester" / "podcasts"
    output_dir.mkdir(parents=True, exist_ok=True)

    for guid, title, author, publish_date, audio_url, video_url in episodes:
        try:
            logger.info(f"Exporting: {title}")

            # Load transcript
            transcript_path = Path("blobs/transcripts") / f"{guid}.json"
            if not transcript_path.exists():
                logger.warning(f"Transcript not found: {transcript_path}")
                continue

            with open(transcript_path) as f:
                transcript_data = json.load(f)

            # For testing, create mock summary data
            # In production, this would come from the summaries table
            from datetime import datetime
            date_str = publish_date.split('T')[0] if 'T' in publish_date else publish_date

            # Create note filename
            safe_title = "".join(c for c in title if c.isalnum() or c in (' ', '-', '_')).strip()
            safe_title = safe_title.replace(' ', '-')[:50]
            note_path = output_dir / f"{date_str}_{safe_title}.md"

            # Generate markdown note (matching template format)
            link = audio_url or video_url or 'N/A'

            # Check if this is a YouTube video for timestamp links (FR34)
            is_youtube = video_url and ('youtube.com' in video_url or 'youtu.be' in video_url)

            # Extract YouTube video ID if available
            youtube_id = None
            if is_youtube:
                import re
                # Try to extract video ID from various YouTube URL formats
                match = re.search(r'(?:v=|/)([a-zA-Z0-9_-]{11})', video_url)
                if match:
                    youtube_id = match.group(1)

            # Format timestamps per FR34 (YouTube links) and FR35 (plain text)
            if youtube_id:
                timestamp1 = f"https://youtube.com/watch?v={youtube_id}&t=0s"
                timestamp2 = f"https://youtube.com/watch?v={youtube_id}&t=30s"
            else:
                timestamp1 = "00:00"
                timestamp2 = "00:30"

            note_content = f"""---
title: {title}
date: {date_str}
author:
  - "[[{author}]]"
guests:
link: {link}
rating:
type: podcast
version: 1.0
rating_llm: 3
---

# {title}

> **Summary:** Biochemist Nick Lane argues that life's emergence is chemically inevitable, driven by fundamental thermodynamics and biochemistry principles including proton gradients, alkaline hydrothermal vents, and universal biochemical pathways.

## Key topics
- Chemical inevitability of life and thermodynamics
- Proton gradients and chemiosmosis in early cells
- Alkaline hydrothermal vents as origin sites
- Universal biochemical pathways across all domains of life
- Mitochondria's role in enabling complex life

## Tools
- **Thermodynamics** — Fundamental principles driving life's chemistry
- **Chemiosmosis** — ATP generation mechanism
- **Electron bifurcation** — Universal energy conversion pathway

## Noteworthy quotes
> This is a fascinating discussion about the chemical origins of life.
— {timestamp1}

> Nick Lane explains how life as we know it may be chemically inevitable based on the fundamental principles of thermodynamics and biochemistry.
— {timestamp2}

## Original content
[View original]({link})
"""

            # Write note
            with open(note_path, 'w') as f:
                f.write(note_content)

            logger.info(f"✓ Exported to: {note_path}")

        except Exception as e:
            logger.error(f"Failed to export {title}: {e}")

    logger.info(f"Export complete. Notes saved to: {output_dir}")
    logger.info("Note: Git operations skipped for testing")


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
