# Development Guide

## Setup

1. **Install Python 3.11+**

2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Install system dependencies:**
   ```bash
   # yt-dlp for audio downloads
   pip install yt-dlp

   # For newsletter parsing (optional, already in requirements.txt)
   # lxml is needed for BeautifulSoup
   ```

4. **Configure environment:**
   ```bash
   # Copy example and edit with your values
   cp .env.example .env
   # Add your ANTHROPIC_API_KEY
   ```

5. **Create sample OPML file:**
   ```bash
   # Export from your podcast app and save to:
   # data/podcasts.opml
   ```

## Running Commands

### Discovery
```bash
python cli.py discover --since 2025-10-01
```

### Process Audio
```bash
# Process all pending episodes
python cli.py process-audio

# Process with limit
python cli.py process-audio --limit 2
```

### Process Newsletters
```bash
python cli.py process-newsletters
```

## Testing

```bash
# Run all tests
pytest

# Run specific test file
pytest tests/test_youtube.py

# Run with coverage
pytest --cov=src
```

## Project Structure

```
media-digest/
├── cli.py                  # Main CLI entry point
├── config.yaml             # Configuration
├── .env                    # Secrets (gitignored)
├── src/
│   ├── config.py           # Config loading
│   ├── logging_config.py   # Logging setup
│   ├── db/                 # Database layer
│   ├── ingest/             # Content ingestion
│   ├── process/            # Audio/newsletter processing
│   ├── summarize/          # LLM summarization
│   ├── export/             # Obsidian export
│   └── utils/              # Utilities
├── templates/              # Jinja2 templates
├── tests/                  # Tests
├── data/                   # User data (gitignored)
├── blobs/                  # Downloaded content (gitignored)
├── logs/                   # Logs (gitignored)
└── secure/                 # Secrets (gitignored)
```

## Development Workflow

1. **Phase 1: Test Discovery**
   - Create a small OPML with 2-3 podcasts
   - Run `discover` command
   - Check database: `duckdb digestor.duckdb "SELECT * FROM episodes"`

2. **Phase 2: Test Audio Processing**
   - Run `process-audio --limit 1`
   - Check `blobs/audio/` and `blobs/transcripts/`
   - Verify transcription quality

3. **Phase 3: Test Summarization**
   - Implement summarization integration in CLI
   - Test with one transcript
   - Verify summary quality

4. **Phase 4: Test Export**
   - Implement export integration in CLI
   - Test note generation
   - Check output in `output/` directory

## Next Steps

The following commands are partially implemented and need completion:

- [ ] `cli.py summarize` - Integrate summarization pipeline
- [ ] `cli.py export` - Integrate export + Git push
- [ ] `cli.py build-daily` - Generate daily digest
- [ ] `cli.py build-weekly` - Generate weekly digest
- [ ] `cli.py retry --item-id [ID]` - Retry failed items

See `tasks/tasks-0001-prd-media-digest.md` for full task breakdown.
