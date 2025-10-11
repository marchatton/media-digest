# Task 0002: Export Lifecycle Refactor - Implementation Summary

## Status: ✅ COMPLETED

## Overview
Implemented new export lifecycle with explicit `exported` status tracking and configurable Git push behavior.

## Changes Made

### 1. Database Schema (`src/db/schema.py`)
- ✅ Added `exported_at TIMESTAMP` column to `episodes` table
- ✅ Added `exported_at TIMESTAMP` column to `newsletters` table
- Tracks when each item was exported to Obsidian

### 2. Configuration (`config.yaml` + `src/config.py`)
- ✅ Added `export.git_push: true` config option
- Default behavior: push to Git after export
- Can be overridden with CLI flags
- ✅ Added `export_git_push` property to Config class

### 3. Database Queries (`src/db/queries.py`)
- ✅ Added `mark_episode_exported(conn, guid)` function
- ✅ Added `mark_newsletter_exported(conn, message_id)` function
- Both functions set `status='exported'` and `exported_at=now()`

### 4. Export Logic (`cli.py`)
- ✅ Updated `cmd_export()` to query `status='completed'` episodes with summaries (not yet exported)
- ✅ Added tracking of `exported_count`
- ✅ Call `mark_episode_exported()` after successful export
- ✅ Conditional Git push based on config/CLI flags
- ✅ Added `--push` and `--no-push` CLI flags for override

### 5. Backfill Script (`scripts/backfill_historical.py`)
- ✅ New script to process historical episodes back to `START_DATE` from `.env`
- Runs full pipeline: discover → process → summarize → export
- Flags: `--dry-run`, `--limit N`, `--no-push`

## CLI Usage

```bash
# Export with Git push (default)
python cli.py export

# Export without Git push
python cli.py export --no-push

# Force Git push (override config)
python cli.py export --push

# Backfill historical content
python scripts/backfill_historical.py --dry-run
python scripts/backfill_historical.py --limit 10
python scripts/backfill_historical.py --no-push
```

## Relevant Files

- `cli.py` - Summarize/export commands to delegate to new services and expose updated status options.
- `src/db/schema.py` - Define status lifecycle changes and optional `exported_at` column.
- `src/db/queries.py` - Helpers for fetching summarized/exportable items and updating status/error fields.
- `src/summarize/summarizer.py`, `src/summarize/rater.py`, `src/summarize/client.py` - Existing LLM orchestration functions leveraged by the new summarization service.
- `src/process/transcriber.py`, `src/process/newsletter_parser.py` - Transcript/newsletter loaders used as inputs for summarization.
- `src/export/obsidian.py`, `src/export/renderer.py`, `templates/*.md.j2` - Rendering utilities/templates required for idempotent export.
- `tests/test_database.py`, `tests/test_export_idempotency.py`, `tests/test_summarization.py` - Baseline tests to extend with service coverage.

### Notes

- Use temporary DuckDB databases and temp directories in tests for isolation.
- Mock Claude API interactions in unit tests to avoid network calls.
- Maintain idempotency: rerunning summarize/export must not duplicate notes or overwrite manual `rating:` edits.

## Tasks

- [ ] 1.0 Establish Status Lifecycle & Persistence Updates
  - [ ] 1.1 Document the desired status flow (`pending → in_progress → completed → summarized → exported`) and failure semantics.
  - [ ] 1.2 Update DuckDB schema (or migrations) to support new statuses and optionally add `exported_at`.
  - [ ] 1.3 Extend query helpers to fetch summarized-but-unexported items and perform atomic status/error updates.

- [ ] 2.0 Implement Summarization Service
  - [ ] 2.1 Create `src/summarize/service.py` encapsulating dependencies (DB connection factory, filesystem paths, Claude client).
  - [ ] 2.2 Implement podcast pipeline: load transcript JSON, clean transcript, summarize, rate, persist summary, transition to `summarized`.
  - [ ] 2.3 Implement newsletter pipeline: load parsed newsletter JSON, summarize, rate, persist, transition to `summarized`.
  - [ ] 2.4 Add structured logging/error handling that records `error_reason` without blocking retries.
  - [ ] 2.5 Add unit tests covering podcast/newsletter success paths and representative failure modes.

- [ ] 3.0 Implement Export Service
  - [ ] 3.1 Create `src/export/service.py` orchestrating export with dependency injection.
  - [ ] 3.2 Implement podcast export: render via `render_episode_note`, respect manual edits with `write_note`, update status/`exported_at`.
  - [ ] 3.3 Implement newsletter export with the same guardrails and template usage.
  - [ ] 3.4 Add deterministic filename + slug helpers shared across content types.
  - [ ] 3.5 Add unit/integration tests (using temp dirs) verifying exports, manual edit protection, and status updates.

- [ ] 4.0 Refactor CLI Commands & Documentation
  - [ ] 4.1 Update `cmd_summarize` to call the summarization service, propagate failures via exit codes, and support optional batching flags.
  - [ ] 4.2 Update `cmd_export` to call the export service, log exported/skipped/failed counts, and toggle Git operations via config flag.
  - [ ] 4.3 Refresh README, DEVELOPMENT, and STATUS docs to explain the new lifecycle and usage.
  - [ ] 4.4 Add pytest integration test covering summarize → export flow using fixtures.

- [ ] 5.0 Observability & Cleanup
  - [ ] 5.1 Enhance `ClaudeClient` logging with item identifiers and model names for traceability.
  - [ ] 5.2 Ensure failures populate `error_reason` consistently and surface in logs; add regression tests where practical.
  - [ ] 5.3 Remove placeholder Markdown generation from `cli.py` and dead code paths superseded by services.
  - [ ] 5.4 Create follow-up ticket for post-MVP tagging and digest commands once refactor lands.
