"""summarize command implementation."""

from argparse import _SubParsersAction

from src.db.connection import get_connection
from src.db.repositories import SummaryRepository, TranscriptRepository
from src.logging_config import get_logger
from src.services.summarization import SummarizationService
from src.summarize.rater import rate_content
from src.summarize.summarizer import summarize_content

logger = get_logger(__name__)


def handle(args) -> None:
    logger.info("Summarizing content...")

    conn = get_connection()
    service = SummarizationService(
        summaries=SummaryRepository(conn),
        transcripts=TranscriptRepository(conn),
        summarizer=summarize_content,
        rater=rate_content,
    )

    service.summarize_pending(limit=args.limit)


def register(subparsers: _SubParsersAction) -> None:
    parser = subparsers.add_parser("summarize", help="Summarize completed content")
    parser.add_argument("--limit", type=int, help="Limit number of items to summarize")
    parser.set_defaults(func=handle)
