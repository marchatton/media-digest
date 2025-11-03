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

- **YAML front matter hardening**
  - Episode note template (`templates/episode.md.j2`) now JSON-encodes title/date/link/etc. to avoid Dataview "Invalid properties" errors.

- **Testing**
  - `pytest` suite passing after each change (no regressions detected).

## Outstanding Refactor Opportunities

1. **Service abstraction for core workflows**
   - Introduce `PodcastProcessor`, `SummarizationService`, etc., to separate business logic from CLI glue.
   - Encapsulate retry/error handling so commands remain thin orchestrators.

2. **Repository layer for DuckDB access**
   - Replace raw SQL in CLI modules with typed repositories or query objects.
   - Clarify return types (episodes/newsletters) to reduce manual dict handling.

3. **Typed configuration model**
   - Wrap `src/config.py` values in a Pydantic model or `dataclass` for early validation.

4. **Newsletter pipeline review**
   - Since newsletters are no longer summarized, remove dead code paths and consider storing lightweight metadata for digests in a dedicated table.

5. **Digest summarizer enhancements**
   - Reintroduce "top themes"/"actionables" when summaries become structured again.
   - Expand tests around digest rendering and CLI commands.

6. **Runtime artifact layout**
   - Optionally move `blobs/`, `logs/`, `digestor.duckdb` under a `var/` directory with configurable paths.

## Next Steps for Async Execution

1. Pull latest `main` on Hetzner (`cd /opt/digestor && git pull --ff-only`).
2. Run smoke commands to verify modular CLI (`cli.py --help`, `cli.py discover --since <date>`).
3. Plan service/repository refactors as incremental PRs (start with `process_audio` and `summarize`).
4. Evaluate configuration typing and newsletter storage in separate follow-up tasks.

---

Add notes here as further refactors land.
