#!/usr/bin/env python3
"""Backfill script to process historical episodes back to START_DATE.

This script discovers, processes, summarizes, and exports episodes
from the configured START_DATE to now using the normal pipeline.

Usage:
    python scripts/backfill_historical.py [--dry-run] [--limit N]
"""

import argparse
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.config import config
from src.logging_config import setup_logging, get_logger

# Import CLI functions
from cli import (
    cmd_discover,
    cmd_process_audio,
    cmd_process_newsletters,
    cmd_summarize,
    cmd_export,
)

setup_logging()
logger = get_logger(__name__)


def main():
    """Run backfill pipeline."""
    parser = argparse.ArgumentParser(description="Backfill historical content")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be done without making changes"
    )
    parser.add_argument(
        "--limit",
        type=int,
        help="Limit number of items to process at each stage"
    )
    parser.add_argument(
        "--no-push",
        action="store_true",
        help="Skip Git push after export"
    )
    args = parser.parse_args()

    logger.info("=" * 60)
    logger.info("BACKFILL PIPELINE STARTING")
    logger.info(f"Start date: {config.start_date}")
    logger.info(f"Dry run: {args.dry_run}")
    logger.info(f"Limit: {args.limit or 'No limit'}")
    logger.info("=" * 60)

    if args.dry_run:
        logger.info("DRY RUN: Would execute the following pipeline:")
        logger.info("1. Discover episodes and newsletters since START_DATE")
        logger.info("2. Process audio (download + transcribe)")
        logger.info("3. Process newsletters (parse)")
        logger.info("4. Summarize content")
        logger.info("5. Export to Obsidian")
        logger.info("=" * 60)
        return

    # Create namespace objects for CLI commands
    class Args:
        pass

    # Step 1: Discover
    logger.info("\n" + "=" * 60)
    logger.info("STEP 1: DISCOVER")
    logger.info("=" * 60)
    discover_args = Args()
    discover_args.since = config.start_date
    cmd_discover(discover_args)

    # Step 2: Process audio
    logger.info("\n" + "=" * 60)
    logger.info("STEP 2: PROCESS AUDIO")
    logger.info("=" * 60)
    audio_args = Args()
    audio_args.limit = args.limit
    cmd_process_audio(audio_args)

    # Step 3: Process newsletters
    logger.info("\n" + "=" * 60)
    logger.info("STEP 3: PROCESS NEWSLETTERS")
    logger.info("=" * 60)
    newsletter_args = Args()
    newsletter_args.limit = args.limit
    cmd_process_newsletters(newsletter_args)

    # Step 4: Summarize
    logger.info("\n" + "=" * 60)
    logger.info("STEP 4: SUMMARIZE")
    logger.info("=" * 60)
    summarize_args = Args()
    summarize_args.limit = args.limit
    cmd_summarize(summarize_args)

    # Step 5: Export
    logger.info("\n" + "=" * 60)
    logger.info("STEP 5: EXPORT")
    logger.info("=" * 60)
    export_args = Args()
    export_args.push = None if not args.no_push else False
    cmd_export(export_args)

    logger.info("\n" + "=" * 60)
    logger.info("BACKFILL PIPELINE COMPLETE")
    logger.info("=" * 60)


if __name__ == "__main__":
    main()
