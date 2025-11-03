"""CLI command registration."""

from argparse import _SubParsersAction

from src.cli import discover, process_audio, process_newsletters, summarize, export, digests, retry, skip


def register_commands(subparsers: _SubParsersAction) -> None:
    """Register all CLI subcommands."""
    discover.register(subparsers)
    process_audio.register(subparsers)
    process_newsletters.register(subparsers)
    summarize.register(subparsers)
    export.register(subparsers)
    digests.register(subparsers)
    retry.register(subparsers)
    skip.register(subparsers)
