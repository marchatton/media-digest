# Refactor Progress – CLI Modularization & Cleanup

_Last updated: 2025-11-03T00:47:44Z_

## Completed Changes

- **Streamlined repository structure**
  - Moved contributor guides under `docs/guides/` (`AGENTS.md`, `DEVELOPMENT.md`, `claude.md`).
  - Moved status/test reports under `docs/status/` (`STATUS.md`, `END_TO_END_TEST_RESULTS.md`, `OVERNIGHT_TEST_STATUS.md`).
  - Consolidated root-level scripts into `scripts/` (`cron_jobs.txt`, `run_full_test.sh`, `generate_gmail_token.py`, helper installers).
  - Updated cross-references in `README.md` and status docs to point to the new paths.

- **CLI modularization (commit 3717dd6)**
  - Replaced monolithic `cli.py` command implementations with modules in `src/cli/` (`discover`, `process_audio`, `process_newsletters`, `summarize`, `export`, `digests`, `retry`, `skip`).
  - Shared filesystem/path utilities extracted to `src/cli/common.py`.
  - `cli.py` now handles parser creation and delegates to `src.cli.register_commands`.
  - Added per-command logging and reduced inline SQL duplication.
- **Service abstractions for processing and summarization**
  - Introduced `PodcastProcessor` and `SummarizationService` to keep CLI commands thin.
  - Repository classes (`EpisodeRepository`, `TranscriptRepository`, `SummaryRepository`) centralize DuckDB access with typed records.
  - CLI commands now depend on services, eliminating ad-hoc SQL and improving testability.

- **YAML front matter hardening**
  - Episode note template (`templates/episode.md.j2`) now JSON-encodes title/date/link/etc. to avoid Dataview "Invalid properties" errors.

- **Configuration and runtime layout typing**
  - `Config.load` now returns a frozen dataclass with validated environment variables and YAML settings.
  - Runtime artifacts (`blobs/`, `logs/`, DuckDB) are rooted under a configurable `VAR_ROOT` directory with derived sub-paths.

- **Newsletter digest pipeline cleanup**
  - Processing writes lightweight previews to `newsletter_digest_entries` for digest rendering instead of inlining body text.
  - CLI commands query the dedicated table and share preview helpers across workflows.

- **Digest highlight restoration**
  - Daily and weekly digests include aggregated top themes and actionables sourced from structured podcast summaries.
  - Added unit coverage for highlight extraction to guard against malformed JSON and duplication.

- **Testing**
  - `pytest` suite passing after each change (no regressions detected).

## Outstanding Refactor Opportunities

1. **Backfill newsletter previews**
   - Write a one-off migration/command to populate `newsletter_digest_entries` for legacy completed newsletters.

2. **Digest UX polish**
   - Consider surfacing notable quotes or ratings distributions alongside the restored themes/actionables.

## Next Steps for Async Execution

1. Pull latest `main` on Hetzner (`cd /opt/digestor && git pull --ff-only`).
2. Run smoke commands to verify modular CLI (`cli.py --help`, `cli.py discover --since <date>`).
3. Plan service/repository refactors as incremental PRs (start with `process_audio` and `summarize`).
4. Evaluate configuration typing and newsletter storage in separate follow-up tasks.

---

Add notes here as further refactors land.
