#!/usr/bin/env python3
"""Media Digest CLI entrypoint."""

from __future__ import annotations

import argparse
import sys

from src.cli import register_commands
from src.db.connection import close_connection
from src.logging_config import get_logger, setup_logging

setup_logging()
logger = get_logger(__name__)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Media Digest CLI")
    subparsers = parser.add_subparsers(dest="command", required=True)
    register_commands(subparsers)
    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    try:
        args.func(args)
    except Exception as exc:  # pragma: no cover - defensive logging
        logger.error("Command failed: %s", exc, exc_info=True)
        sys.exit(1)
    finally:
        close_connection()


if __name__ == "__main__":
    main()
