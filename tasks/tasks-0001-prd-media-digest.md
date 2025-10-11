# Task List: Media Digest Implementation

Based on PRD: `0001-prd-media-digest.md`

## Current State Assessment

**Codebase:** Greenfield (no existing Python code)

**Key Constraints:**
- Prioritize accuracy over cost (use Sonnet 4.5 for quality)
- Privacy-first: Only digest subfolder synced via Git
- Idempotent: Safe to re-run all operations
- Volume: 20 podcasts/week (30 min avg), 30 newsletters/day
- Package manager: pnpm (not npm)

**Architecture Pattern:**
- CLI-driven batch processing
- DuckDB for state management
- Pluggable providers via Protocol (Transcriber, Summarizer, Exporter)
- Functional style with immutable data structures

---

## Relevant Files

### Core Application
- `cli.py` - Main CLI entry point with all commands (discover, process-audio, process-newsletters, build-daily, build-weekly, export-obsidian, retry)
- `requirements.txt` - Python dependencies
- `.env.example` - Example environment variables template
- `config.yaml` - Application configuration (committed)

### Source Code Structure
- `src/__init__.py` - Package initialization
- `src/config.py` - Configuration loading from .env and config.yaml
- `src/logging_config.py` - Logging setup

### Database Layer
- `src/db/schema.py` - DuckDB schema definitions and migrations
- `src/db/queries.py` - Database query functions
- `src/db/connection.py` - Database connection management

### Ingestion
- `src/ingest/podcasts.py` - OPML parsing and RSS feed discovery
- `src/ingest/newsletters.py` - Gmail OAuth and email fetching
- `src/ingest/models.py` - Data models for episodes and newsletters

### Processing
- `src/process/audio.py` - Audio download using yt-dlp
- `src/process/transcriber.py` - Whisper transcription (Protocol + implementation)
- `src/process/newsletter_parser.py` - HTML to plain text parsing

### Summarization
- `src/summarize/client.py` - Anthropic Claude API client with prompt caching and configurable model
- `src/summarize/prompts.py` - All LLM prompts (cleaning, summarization, rating; tagging added in Task 8.0)
- `src/summarize/summarizer.py` - Summarization orchestration
- `src/summarize/tagger.py` - Tag selection from whitelist (Task 8.0 - Post-MVP)
- `src/summarize/rater.py` - Content rating logic
- `src/summarize/models.py` - Structured output models (SummaryResponse, RatingResponse; TagResponse added in Task 8.0)

### Export
- `src/export/renderer.py` - Jinja2 template rendering
- `src/export/obsidian.py` - Obsidian note generation and Git operations
- `src/export/digest.py` - Daily and weekly digest generation
- `src/export/models.py` - Export data models

### Utilities
- `src/utils/youtube.py` - YouTube URL parsing and timestamp link generation
- `src/utils/retry.py` - Exponential backoff retry decorator
- `src/utils/tags.py` - Tag whitelist parser for Dataview file (Task 8.0 - Post-MVP)

### Templates
- `templates/episode.md.j2` - Per-episode note template
- `templates/newsletter.md.j2` - Per-newsletter note template
- `templates/daily.md.j2` - Daily digest template
- `templates/weekly.md.j2` - Weekly digest template

### Tests
- `tests/test_tagging.py` - Tag selection logic (Task 8.0 - max 5, whitelist intersection)
- `tests/test_rating.py` - Rating distribution validation
- `tests/test_export.py` - Idempotency and note rendering
- `tests/test_youtube.py` - YouTube timestamp link generation
- `tests/test_config.py` - Configuration loading
- `tests/fixtures/sample_opml.xml` - Test OPML file
- `tests/fixtures/sample_tags.txt` - Test tag whitelist (Task 8.0)
- `tests/fixtures/sample_transcript.txt` - Test transcript

### Data & Configuration (gitignored)
- `data/podcasts.opml` - User's podcast subscriptions (currently 6 AI/tech podcasts - needs expansion)
- `data/tags.md` - Cached tag whitelist from Obsidian
- `blobs/audio/` - Downloaded audio files
- `blobs/transcripts/` - Transcription outputs
- `logs/digest.log` - Application logs
- `secure/gmail_token.json` - Gmail OAuth token
- `digestor.duckdb` - Database file

**NOTE:** The OPML file currently only contains 6 AI/tech podcasts from the initial setup (Latent Space, Dwarkesh, High Agency, Practical AI, My First Million, Lenny's Podcast). This list should be expanded with additional podcast subscriptions. Refer to `docs/ai-podcasts-directory.md` for more podcast options to add.

### Notes
- Tests use `pytest` (not Jest - this is Python)
- Run tests: `pytest tests/` or `pytest tests/test_tagging.py` for specific file
- Use `pytest --cov=src` for coverage report
- All modules should have type hints (Python 3.11+)
- Use Protocol for abstractions (Transcriber, Summarizer interfaces)
- Package manager: pnpm (not npm) - though this is a Python project, note for any JS tooling

---

## Tasks

- [ ] 1.0 **Project Setup & Infrastructure**
  - [ ] 1.1 Initialize Python project with pyproject.toml (Poetry) or requirements.txt
  - [ ] 1.2 Create directory structure (src/, tests/, templates/, data/, blobs/, logs/, secure/)
  - [ ] 1.3 Set up .gitignore (data/, blobs/, logs/, secure/, *.duckdb, *.env, .DS_Store)
  - [ ] 1.4 Create .env.example with all required environment variables
  - [ ] 1.5 Implement src/config.py to load .env and config.yaml
  - [ ] 1.6 Implement src/logging_config.py with file and console handlers
  - [ ] 1.7 Define DuckDB schema in src/db/schema.py (episodes, newsletters, processing_status, errors tables)
  - [ ] 1.8 Implement src/db/connection.py with connection pooling and migration support
  - [ ] 1.9 Write tests for config loading (tests/test_config.py)
  - [ ] 1.10 Create initial config.yaml with sensible defaults

- [ ] 2.0 **Content Ingestion (Podcasts & Newsletters)**
  - [ ] 2.1 Define data models in src/ingest/models.py (Episode, Newsletter with Pydantic or dataclasses)
  - [ ] 2.2 Implement OPML parser in src/ingest/podcasts.py (parse file, extract feed URLs)
  - [ ] 2.3 Implement RSS feed discovery (fetch feed, parse episodes, extract metadata: GUID, title, date, audio URL, video URL)
  - [ ] 2.4 Implement Gmail OAuth flow in src/ingest/newsletters.py (initial token generation script)
  - [ ] 2.5 Implement Gmail fetching (search by labels and date, extract subject, sender, date, message ID, body)
  - [ ] 2.6 Write database insertion functions in src/db/queries.py (upsert episodes, upsert newsletters)
  - [ ] 2.7 Implement discover command logic (since date filter, check for new items, insert to DB with status=pending)
  - [ ] 2.8 Write tests for OPML parsing (tests/test_ingest.py)
  - [ ] 2.9 Handle edge cases (missing audio URL, redirected feeds, invalid OPML)

- [ ] 3.0 **Audio Processing & Transcription**
  - [ ] 3.1 Define Transcriber Protocol in src/process/transcriber.py
  - [ ] 3.2 Implement audio download in src/process/audio.py using yt-dlp (audio-only extraction)
  - [ ] 3.3 Implement WhisperTranscriber using faster-whisper library (medium model, int8 compute)
  - [ ] 3.4 Add timestamp preservation in transcription output
  - [ ] 3.5 Implement retry logic with exponential backoff (src/utils/retry.py decorator)
  - [ ] 3.6 Save transcripts to blobs/transcripts/ as JSON (with timestamps)
  - [ ] 3.7 Update episode status in DB (in_progress → completed or failed with error_reason)
  - [ ] 3.8 Implement process-audio command (fetch pending episodes, download, transcribe, update DB)
  - [ ] 3.9 Handle long episodes (>2 hours) with progress logging
  - [ ] 3.10 Write integration test for Whisper transcription (use short test audio file)

- [ ] 4.0 **Newsletter Processing & Parsing**
  - [ ] 4.1 Implement HTML to plain text parser in src/process/newsletter_parser.py (BeautifulSoup4)
  - [ ] 4.2 Handle various newsletter formats (strip images, preserve links, clean formatting)
  - [ ] 4.3 Extract newsletter link (web version URL if available, else Gmail link)
  - [ ] 4.4 Save parsed text to blobs/newsletters/ as JSON
  - [ ] 4.5 Update newsletter status in DB (in_progress → completed or failed with error_reason)
  - [ ] 4.6 Implement process-newsletters command (fetch pending, parse, update DB)
  - [ ] 4.7 Handle edge cases (empty body, paywall detection, attachment handling)
  - [ ] 4.8 Write tests for HTML parsing (tests/test_newsletter_parser.py)

- [ ] 5.0 **Summarization & Analysis Pipeline**
  - [ ] 5.1 Set up Anthropic Claude API client in src/summarize/client.py with prompt caching and configurable model
  - [ ] 5.2 Add model configuration to config.yaml (default: claude-sonnet-4-5-20250929, allow override per task type)
  - [ ] 5.3 Define LLM prompts in src/summarize/prompts.py (cleaning, summarization, rating - from PRD Appendix, excluding tagging for now)
  - [ ] 5.4 Define structured output models in src/summarize/models.py (Pydantic: SummaryResponse, RatingResponse)
  - [ ] 5.5 Implement transcript cleaning (remove filler words, segment by topic) in src/summarize/summarizer.py using Sonnet 4.5
  - [ ] 5.6 Implement summarization (2-3 sentences, key topics, companies, tools, quotes) using Claude API
  - [ ] 5.7 Implement rating logic in src/summarize/rater.py (LLM proposes rating, store raw + final)
  - [ ] 5.8 Test rating distribution (tests/test_rating.py - ensure 5s are rare)
  - [ ] 5.9 Handle API rate limits and retry with backoff
  - [ ] 5.10 Save summaries and ratings to database

- [ ] 6.0 **Export & Sync to Obsidian**
  - [ ] 6.1 Create Jinja2 templates (templates/episode.md.j2, newsletter.md.j2, daily.md.j2, weekly.md.j2)
  - [ ] 6.2 Implement template renderer in src/export/renderer.py
  - [ ] 6.3 Implement YouTube timestamp link generation in src/utils/youtube.py (detect YouTube, format with &t=)
  - [ ] 6.4 Implement note generation in src/export/obsidian.py (render template, check for manual edits, write to output path)
  - [ ] 6.5 Implement idempotency (skip if user filled rating field, detect via regex)
  - [ ] 6.6 Implement daily digest generation in src/export/digest.py (list items, failures section, top themes, actionables)
  - [ ] 6.7 Implement weekly digest generation (top 3-4 takeaways per item, sorted by rating)
  - [ ] 6.8 Implement Git operations (git add, commit with date, push to origin main)
  - [ ] 6.9 Implement export-obsidian command (render notes, commit, push)
  - [ ] 6.10 Test idempotency (tests/test_export.py - re-export doesn't duplicate, respects manual edits)
  - [ ] 6.11 Test YouTube link generation (tests/test_youtube.py - correct format, handle non-YouTube)

- [ ] 7.0 **CLI & Orchestration**
  - [ ] 7.1 Implement CLI argument parsing in cli.py (using argparse or click)
  - [ ] 7.2 Implement discover command (calls ingest logic, logs results)
  - [ ] 7.3 Implement process-audio command (calls audio processing pipeline)
  - [ ] 7.4 Implement process-newsletters command (calls newsletter processing pipeline)
  - [ ] 7.5 Implement build-daily command (generates daily digest for specified date)
  - [ ] 7.6 Implement build-weekly command (generates weekly digest for specified date range)
  - [ ] 7.7 Implement export-obsidian command (exports notes and pushes to Git)
  - [ ] 7.8 Implement retry command (re-process failed items by ID)
  - [ ] 7.9 Implement skip command (mark item as skipped permanently)
  - [ ] 7.10 Add logging and error handling to all commands
  - [ ] 7.11 Create cron configuration file with flock examples (docs/cron-setup.md)
  - [ ] 7.12 Write end-to-end test (tests/test_e2e.py - discover → process → summarize → export)

- [ ] 8.0 **Auto-Tagging (Post-MVP Enhancement)**
  - [ ] 8.1 Implement tag parser in src/utils/tags.py (parse Dataview file, filter malformed entries)
  - [ ] 8.2 Add tagging prompt to src/summarize/prompts.py (from PRD Appendix)
  - [ ] 8.3 Define TagResponse model in src/summarize/models.py (Pydantic)
  - [ ] 8.4 Implement tag selection in src/summarize/tagger.py (intersect with whitelist, max 5 tags)
  - [ ] 8.5 Test tag selection (tests/test_tagging.py - ensure max 5, whitelist enforcement)
  - [ ] 8.6 Integrate tagging into summarization pipeline
  - [ ] 8.7 Update templates to include tags in frontmatter
  - [ ] 8.8 Add tag refresh command to CLI (optional: update tag whitelist from Obsidian)

---

## Implementation Order Recommendation

**Phase 1: Foundation (Task 1.0)**
Set up project structure, config, logging, and database schema.

**Phase 2: Ingestion (Task 2.0)**
Implement podcast RSS and newsletter Gmail discovery. Test with 2-3 feeds.

**Phase 3: Audio Processing (Task 3.0)**
Download and transcribe podcasts using local Whisper.

**Phase 4: Newsletter Processing (Task 4.0)**
Fetch and parse newsletters from Gmail.

**Phase 5: Summarization (Task 5.0)**
Integrate Claude Sonnet 4.5 for cleaning, summarization, and rating. Skip tagging for now.

**Phase 6: Export (Task 6.0)**
Build templates and Git sync. Test with a separate test repo first.

**Phase 7: CLI & Orchestration (Task 7.0)**
Wire up all commands, add error handling, test cron locally.

**Phase 8: Auto-Tagging (Task 8.0 - Post-MVP)**
Add auto-tagging feature after the core pipeline is working end-to-end.

---

## Development Tips

1. **Start with one podcast and one newsletter** - Don't test with 20 feeds on day 1
2. **Use Sonnet 4.5 for quality** - Prioritize accuracy over cost initially
3. **Make model configurable** - Allow easy switching between Claude models in config.yaml
4. **Mock LLM responses in tests** - Don't hit API in unit tests
5. **Test Git push to a separate test repo** - Before pushing to your actual vault repo
6. **Use pytest fixtures for common test data** - Episode, Newsletter, Summary objects
7. **Log everything** - You'll need it when debugging cron jobs on Hetzner
8. **Implement dry-run mode** - Add `--dry-run` flag to test without side effects
9. **Skip tagging initially** - Get the core pipeline working first (Tasks 1-7), add tagging later (Task 8)

---

## Ready to Start!

All tasks are now broken down into actionable sub-tasks. Each task includes specific implementation details from the PRD.

**Suggested first steps:**
1. Task 1.1-1.6 (project setup, config with model selection)
2. Task 1.7-1.8 (database schema)
3. Task 2.1-2.3 (OPML parsing and RSS discovery)
4. Test with 2-3 podcasts before proceeding
5. Complete Tasks 3-7 for end-to-end pipeline
6. Add tagging (Task 8) after core pipeline works

**Model Configuration:**
In `config.yaml`, add:
```yaml
llm:
  provider: anthropic
  default_model: claude-sonnet-4-5-20250929
  models:
    cleaning: claude-sonnet-4-5-20250929
    summarization: claude-sonnet-4-5-20250929
    rating: claude-sonnet-4-5-20250929
    tagging: claude-sonnet-4-5-20250929  # Task 8.0
```

Good luck! 🚀
