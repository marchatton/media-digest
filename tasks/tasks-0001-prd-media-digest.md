# Task List: Media Digest Implementation

Based on PRD: `0001-prd-media-digest.md`

## 📊 Quick Status Overview

**Overall Progress:** ~80% Complete (MVP almost ready!)

- ✅ **Tasks 1.0-4.0**: COMPLETE (Infrastructure, ingestion, processing)
- ⚠️ **Task 5.0**: MOSTLY DONE (needs CLI integration)
- ⚠️ **Task 6.0**: MOSTLY DONE (needs CLI integration)
- ⚠️ **Task 7.0**: PARTIAL (core commands work, missing some CLI commands)
- ❌ **Task 8.0**: NOT STARTED (post-MVP)

**What's Working:**
- ✅ Podcast discovery from OPML (17 feeds configured)
- ✅ Newsletter discovery from Gmail
- ✅ Audio download + Whisper transcription
- ✅ Newsletter HTML parsing
- ✅ Claude Sonnet 4.5 summarization logic
- ✅ Export templates and Git sync

**What's Missing for MVP:**
- ⏳ CLI integration for summarize command
- ⏳ CLI integration for export command
- ⏳ build-daily, build-weekly, retry, skip commands
- ⏳ End-to-end testing

---

## Current State Assessment

**Codebase:** ~3,000 lines of Python code across 33 modules (as of Jan 2025)
- All core infrastructure in place
- 6 test files covering critical business logic
- 4 Jinja2 templates ready
- OPML file with 17 podcast feeds

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

- [x] 1.0 **Project Setup & Infrastructure** ✅ COMPLETE
  - [x] 1.1 Initialize Python project with pyproject.toml (Poetry) or requirements.txt
  - [x] 1.2 Create directory structure (src/, tests/, templates/, data/, blobs/, logs/, secure/)
  - [x] 1.3 Set up .gitignore (data/, blobs/, logs/, secure/, *.duckdb, *.env, .DS_Store)
  - [x] 1.4 Create .env.example with all required environment variables
  - [x] 1.5 Implement src/config.py to load .env and config.yaml
  - [x] 1.6 Implement src/logging_config.py with file and console handlers
  - [x] 1.7 Define DuckDB schema in src/db/schema.py (episodes, newsletters, processing_status, errors tables)
  - [x] 1.8 Implement src/db/connection.py with connection pooling and migration support
  - [x] 1.9 Write tests for config loading (tests/test_config.py)
  - [x] 1.10 Create initial config.yaml with sensible defaults

- [x] 2.0 **Content Ingestion (Podcasts & Newsletters)** ✅ COMPLETE
  - [x] 2.1 Define data models in src/ingest/models.py (Episode, Newsletter with Pydantic or dataclasses)
  - [x] 2.2 Implement OPML parser in src/ingest/podcasts.py (parse file, extract feed URLs)
  - [x] 2.3 Implement RSS feed discovery (fetch feed, parse episodes, extract metadata: GUID, title, date, audio URL, video URL)
  - [x] 2.4 Implement Gmail OAuth flow in src/ingest/newsletters.py (initial token generation script)
  - [x] 2.5 Implement Gmail fetching (search by labels and date, extract subject, sender, date, message ID, body)
  - [x] 2.6 Write database insertion functions in src/db/queries.py (upsert episodes, upsert newsletters)
  - [x] 2.7 Implement discover command logic (since date filter, check for new items, insert to DB with status=pending)
  - [x] 2.8 Write tests for OPML parsing (tests/test_opml_parsing.py)
  - [x] 2.9 Handle edge cases (missing audio URL, redirected feeds, invalid OPML)

- [x] 3.0 **Audio Processing & Transcription** ✅ COMPLETE
  - [x] 3.1 Define Transcriber Protocol in src/process/transcriber.py
  - [x] 3.2 Implement audio download in src/process/audio.py using yt-dlp (audio-only extraction)
  - [x] 3.3 Implement WhisperTranscriber using faster-whisper library (medium model, int8 compute)
  - [x] 3.4 Add timestamp preservation in transcription output
  - [x] 3.5 Implement retry logic with exponential backoff (src/utils/retry.py decorator)
  - [x] 3.6 Save transcripts to blobs/transcripts/ as JSON (with timestamps)
  - [x] 3.7 Update episode status in DB (in_progress → completed or failed with error_reason)
  - [x] 3.8 Implement process-audio command (fetch pending episodes, download, transcribe, update DB)
  - [x] 3.9 Handle long episodes (>2 hours) with progress logging
  - [ ] 3.10 Write integration test for Whisper transcription (use short test audio file) - OPTIONAL

- [x] 4.0 **Newsletter Processing & Parsing** ✅ COMPLETE
  - [x] 4.1 Implement HTML to plain text parser in src/process/newsletter_parser.py (BeautifulSoup4)
  - [x] 4.2 Handle various newsletter formats (strip images, preserve links, clean formatting)
  - [x] 4.3 Extract newsletter link (web version URL if available, else Gmail link)
  - [x] 4.4 Save parsed text to blobs/newsletters/ as JSON
  - [x] 4.5 Update newsletter status in DB (in_progress → completed or failed with error_reason)
  - [x] 4.6 Implement process-newsletters command (fetch pending, parse, update DB)
  - [x] 4.7 Handle edge cases (empty body, paywall detection, attachment handling)
  - [ ] 4.8 Write tests for HTML parsing (tests/test_newsletter_parser.py) - OPTIONAL

- [x] 5.0 **Summarization & Analysis Pipeline** ⚠️ MOSTLY DONE (needs CLI integration)
  - [x] 5.1 Set up Anthropic Claude API client in src/summarize/client.py with prompt caching and configurable model
  - [x] 5.2 Add model configuration to config.yaml (default: claude-sonnet-4-5-20250929, allow override per task type)
  - [x] 5.3 Define LLM prompts in src/summarize/prompts.py (cleaning, summarization, rating - from PRD Appendix, excluding tagging for now)
  - [x] 5.4 Define structured output models in src/summarize/models.py (Pydantic: SummaryResponse, RatingResponse)
  - [x] 5.5 Implement transcript cleaning (remove filler words, segment by topic) in src/summarize/summarizer.py using Sonnet 4.5
  - [x] 5.6 Implement summarization (2-3 sentences, key topics, companies, tools, quotes) using Claude API
  - [x] 5.7 Implement rating logic in src/summarize/rater.py (LLM proposes rating, store raw + final)
  - [x] 5.8 Test rating distribution (tests/test_summarization.py - ensure 5s are rare)
  - [x] 5.9 Handle API rate limits and retry with backoff
  - [ ] 5.10 Save summaries and ratings to database - NEEDS CLI INTEGRATION in cmd_summarize

- [x] 6.0 **Export & Sync to Obsidian** ⚠️ MOSTLY DONE (needs CLI integration)
  - [x] 6.1 Create Jinja2 templates (templates/episode.md.j2, newsletter.md.j2, daily.md.j2, weekly.md.j2)
  - [x] 6.2 Implement template renderer in src/export/renderer.py
  - [x] 6.3 Implement YouTube timestamp link generation in src/utils/youtube.py (detect YouTube, format with &t=)
  - [x] 6.4 Implement note generation in src/export/obsidian.py (render template, check for manual edits, write to output path)
  - [x] 6.5 Implement idempotency (skip if user filled rating field, detect via regex)
  - [x] 6.6 Implement daily digest generation in src/export/digest.py (list items, failures section, top themes, actionables)
  - [x] 6.7 Implement weekly digest generation (top 3-4 takeaways per item, sorted by rating)
  - [x] 6.8 Implement Git operations (git add, commit with date, push to origin main)
  - [ ] 6.9 Implement export-obsidian command - NEEDS CLI INTEGRATION in cmd_export
  - [x] 6.10 Test idempotency (tests/test_export_idempotency.py - re-export doesn't duplicate, respects manual edits)
  - [x] 6.11 Test YouTube link generation (tests/test_youtube.py - correct format, handle non-YouTube)

- [ ] 7.0 **CLI & Orchestration** ⚠️ PARTIAL (core commands work, missing some commands)
  - [x] 7.1 Implement CLI argument parsing in cli.py (using argparse)
  - [x] 7.2 Implement discover command (calls ingest logic, logs results)
  - [x] 7.3 Implement process-audio command (calls audio processing pipeline)
  - [x] 7.4 Implement process-newsletters command (calls newsletter processing pipeline)
  - [ ] 7.5 Implement build-daily command (generates daily digest for specified date) - NOT YET ADDED
  - [ ] 7.6 Implement build-weekly command (generates weekly digest for specified date range) - NOT YET ADDED
  - [ ] 7.7 Implement summarize command - PLACEHOLDER EXISTS, needs full integration with 5.10
  - [ ] 7.8 Implement export command - PLACEHOLDER EXISTS, needs full integration with 6.9
  - [ ] 7.9 Implement retry command (re-process failed items by ID) - NOT YET ADDED
  - [ ] 7.10 Implement skip command (mark item as skipped permanently) - NOT YET ADDED
  - [x] 7.11 Add logging and error handling to all commands
  - [ ] 7.12 Create cron configuration file with flock examples (docs/cron-setup.md) - NOT YET DONE
  - [ ] 7.13 Write end-to-end test (tests/test_e2e.py - discover → process → summarize → export) - NOT YET DONE

- [ ] 8.0 **Auto-Tagging (Post-MVP Enhancement)** ❌ NOT STARTED
  - [ ] 8.1 Implement tag parser in src/utils/tags.py (parse Dataview file, filter malformed entries)
  - [ ] 8.2 Add tagging prompt to src/summarize/prompts.py (from PRD Appendix)
  - [ ] 8.3 Define TagResponse model in src/summarize/models.py (Pydantic)
  - [ ] 8.4 Implement tag selection in src/summarize/tagger.py (intersect with whitelist, max 5 tags)
  - [ ] 8.5 Test tag selection (tests/test_tagging.py - ensure max 5, whitelist enforcement)
  - [ ] 8.6 Integrate tagging into summarization pipeline
  - [ ] 8.7 Update templates to include tags in frontmatter
  - [ ] 8.8 Add tag refresh command to CLI (optional: update tag whitelist from Obsidian)

---

## Implementation Status Summary

**✅ Phase 1: Foundation (Task 1.0)** - COMPLETE
All infrastructure is ready: project structure, config, logging, database schema.

**✅ Phase 2: Ingestion (Task 2.0)** - COMPLETE
Podcast RSS and newsletter Gmail discovery fully working. OPML with 17 feeds created.

**✅ Phase 3: Audio Processing (Task 3.0)** - COMPLETE
Audio download and Whisper transcription fully working.

**✅ Phase 4: Newsletter Processing (Task 4.0)** - COMPLETE
Newsletter HTML parsing fully working.

**⚠️ Phase 5: Summarization (Task 5.0)** - MOSTLY DONE
Claude Sonnet 4.5 integration, prompts, models, and logic complete. **NEEDS: CLI integration (cmd_summarize)**.

**⚠️ Phase 6: Export (Task 6.0)** - MOSTLY DONE
Templates, renderer, Git sync all implemented. **NEEDS: CLI integration (cmd_export)**.

**⚠️ Phase 7: CLI & Orchestration (Task 7.0)** - PARTIAL
Core commands work (discover, process-audio, process-newsletters). **NEEDS: build-daily, build-weekly, retry, skip commands + full summarize/export integration**.

**❌ Phase 8: Auto-Tagging (Task 8.0 - Post-MVP)** - NOT STARTED
Skip for MVP. Implement after end-to-end pipeline works.

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

## Manual TODOs

### YouTube Channel IDs - PENDING USER ACTION

**Status:** Need to manually look up 10 YouTube channel IDs to complete OPML file

**Instructions:**
For each channel below:
1. Visit the YouTube channel URL
2. Right-click → View Page Source (or press Ctrl+U / Cmd+Option+U)
3. Search for `"channelId"` (Ctrl+F / Cmd+F)
4. Copy the UC... string (24 characters total, starts with "UC")
5. Add to `data/podcasts.opml` in format:
   ```xml
   <outline text="Channel Name" type="rss" xmlUrl="https://www.youtube.com/feeds/videos.xml?channel_id=CHANNEL_ID" />
   ```

**Channels to look up:**
- [ ] @builtwithhumanloop - https://www.youtube.com/@builtwithhumanloop (High Agency)
- [ ] @Tessl_io - https://www.youtube.com/@Tessl_io (The AI Native Dev)
- [ ] @PracticalAIbyRamsri - https://www.youtube.com/@PracticalAIbyRamsri (Practical AI)
- [ ] @CognitiveRevolutionPodcast - https://www.youtube.com/@CognitiveRevolutionPodcast (The Cognitive Revolution)
- [ ] @Squirro_AI - https://www.youtube.com/@Squirro_AI (Redefining AI)
- [ ] @latentspacepod - https://www.youtube.com/@latentspacepod (Latent Space)
- [ ] @TheAIBreakdown - https://www.youtube.com/@TheAIBreakdown (The AI Daily Brief)
- [ ] @DwarkeshPatel - https://www.youtube.com/@DwarkeshPatel (Dwarkesh Podcast)
- [ ] @MyFirstMillionPod - https://www.youtube.com/@MyFirstMillionPod (My First Million)
- [ ] @LennysPodcast - https://www.youtube.com/@LennysPodcast (Lenny's Podcast)

**Note:** The AI in Business podcast doesn't appear to have a YouTube channel.

**Current OPML Status:**
- ✅ 11 standard podcast RSS feeds configured
- ✅ 6 YouTube channels configured (How I AI, AI For Humans, Everyday AI, Behind the Craft, Every Inc, Product Growth)
- ⏳ 10 YouTube channels pending (above list)
- **Total when complete: 27 podcast sources**

---

## 🎯 Priority: What's Left for MVP

The core building blocks are done. Here's what's needed to complete the MVP:

### High Priority (Blocking MVP)
1. **Complete CLI Integration**
   - [ ] Task 7.7: Wire up `cmd_summarize` to actually call summarization functions and save to DB
   - [ ] Task 7.8: Wire up `cmd_export` to render notes, write files, and git commit/push
   - [ ] Task 7.5: Add `build-daily` command to generate daily digests
   - [ ] Task 7.6: Add `build-weekly` command to generate weekly digests

2. **Essential Commands**
   - [ ] Task 7.9: Add `retry` command to re-process failed items
   - [ ] Task 7.10: Add `skip` command to permanently skip items

### Medium Priority (Helpful but not blocking)
3. **End-to-End Testing**
   - [ ] Task 7.13: Write e2e test: discover → process → summarize → export
   - [ ] Manual testing with real podcasts and newsletters

4. **Deployment Prep**
   - [ ] Task 7.12: Create cron configuration documentation
   - [ ] Set up Gmail OAuth token
   - [ ] Configure `.env` with actual credentials

### Low Priority (Post-MVP)
5. **Auto-Tagging (Task 8.0)** - Skip for now, add later
6. **Optional Tests** - Task 3.10, 4.8 (Whisper integration, newsletter parser)

---

## 🚀 Next Steps to Complete MVP

**Current Status:** ~80% complete. Core building blocks are done, need final CLI integration.

**Immediate Next Steps:**
1. ✅ ~~Tasks 1-4~~ (Complete - Infrastructure, ingestion, processing all working)
2. ⚠️ **Task 5.10**: Implement `cmd_summarize` - wire up summarization pipeline to CLI
3. ⚠️ **Task 6.9**: Implement `cmd_export` - wire up export pipeline to CLI
4. ⏳ **Task 7.5-7.6**: Add `build-daily` and `build-weekly` commands
5. ⏳ **Task 7.9-7.10**: Add `retry` and `skip` commands
6. ⏳ **Task 7.13**: Write end-to-end test
7. ⏳ Test full pipeline: discover → process → summarize → export
8. ⏳ Deploy to Hetzner with cron jobs
9. ⏳ Add tagging (Task 8) after MVP works end-to-end

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
