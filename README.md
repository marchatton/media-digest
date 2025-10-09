# Media Digest

**Automated podcast and newsletter summarization tool**

Stop drowning in 20+ podcasts and 30+ newsletters per day. This tool automatically transcribes, summarizes, and rates content, then outputs structured notes to your Obsidian vault.

## What It Does

- **Ingests** podcasts (via OPML) and newsletters (via Gmail)
- **Transcribes** audio locally using Whisper (free, runs on Hetzner VM)
- **Summarizes** content using Claude API (key topics, companies, tools, quotes)
- **Auto-tags** notes using your existing Obsidian taxonomy (max 5 tags)
- **Rates** content 1-5 (conservative distribution, 5s are rare)
- **Exports** daily and weekly digests to Obsidian

**Result:** Reduce content consumption time by 80% while staying informed.

## Architecture

```
Hetzner VM (cron) → Local Whisper → Claude API → Git → Your Mac → Obsidian Sync
```

- **Hetzner VM**: Runs daily at 1 AM UTC, processes content, writes notes
- **GitHub**: Private repo syncs digest notes only (not your full vault)
- **Your Mac**: Pulls updates every 30 min, Obsidian Sync handles the rest

## Cost

**~$16.50/month**
- Transcription: $0 (local Whisper)
- Summarization: ~$10/month (Claude API)
- Hetzner VM: ~$6.50/month

## Tech Stack

- **Python 3.11+** (type hints everywhere)
- **DuckDB** (embedded database, single file, zero-ops)
- **faster-whisper** (Whisper medium model, runs on CPU)
- **Anthropic Claude API** (Haiku for cost, Sonnet for quality)
- **Cron + flock** (scheduling, no race conditions)

## Key Features

### Privacy-First
- Only digest notes are synced via Git (not your journal/personal notes)
- Main Obsidian vault stays private
- Tag whitelist manually copied to Hetzner (no vault access needed)

### Idempotent
- Safe to re-run exports (won't duplicate content)
- Respects manual edits (detects if you filled in the `rating:` field)
- Retries failed items automatically (once, then manual retry required)

### Failure Tracking
- All failures logged with explicit error messages
- Daily/weekly digests include "Failures" section
- Easy retry via CLI: `cli.py retry --item-id [ID]`

### Smart Timestamps
- YouTube links: `https://youtube.com/watch?v=ID&t=123s` (clickable)
- Other podcasts: `[12:34]` (manual navigation in Pocket Casts, etc.)

## Output Structure

### Per-Episode Note
```markdown
---
title: Episode Title
date: 2025-10-09
tags: [skill/growth, ai/agents]
author: [Host Name]
guests: [Guest 1, Guest 2]
link: https://youtube.com/...
rating:                    # You fill this manually
rating_llm: 4              # LLM's rating
---

# Episode Title

> **Summary:** 2-3 sentence overview

## Key topics
- Topic 1
- Topic 2

## Companies
- **Company Name** — Brief context

## Tools
- **Tool Name** — Brief context

## Noteworthy quotes
> "Quote text"
— [12:34](https://youtube.com/watch?v=ID&t=754s)

## Original content
[View original](https://youtube.com/...)
```

### Daily Digest
- List of all processed items with one-line summaries
- **Failures** section (explicit error messages)
- **Top themes** (recurring topics across items)
- **Actionables** (tools to try, concepts to research)

### Weekly Digest (Fridays)
- Top 3-4 takeaways per item
- Sorted by LLM rating (best first)
- **Failures** section for the week

## Project Status

**Current:** PRD complete, ready for implementation

**Next:** Task breakdown and development

## Documentation

- **[PRD](tasks/0001-prd-media-digest.md)** - Full product requirements (1,100+ lines)
- **[claude.md](claude.md)** - Development guidelines for Claude Code
- **[Brainstorming Spec](docs/brainstorming-spec.md)** - Original design decisions

## Setup (High-Level)

1. **Hetzner VM**: Deploy Python app, install Whisper, configure cron
2. **GitHub**: Create private repo for digest notes
3. **Mac**: Clone repo to `~/Documents/Obsidian notes/.../5-Resources/0-Media digester`
4. **Obsidian**: Enable Sync, notes propagate to all devices

Full setup instructions in [PRD Appendix: Git Setup](tasks/0001-prd-media-digest.md#appendix-git-setup-instructions).

## CLI Commands

```bash
# Discover new episodes/newsletters
cli.py discover --since 2025-10-01

# Process audio (download + transcribe)
cli.py process-audio --retries 3

# Process newsletters (fetch + parse)
cli.py process-newsletters --retries 2

# Generate daily digest
cli.py build-daily --date today

# Generate weekly digest (Fridays)
cli.py build-weekly --ending today

# Export to Obsidian and push to Git
cli.py export-obsidian --date today

# Retry a failed item
cli.py retry --item-id [ID]
```

## Contributing

This is a personal tool. If you're building something similar, feel free to use the PRD as a reference.

## License

MIT
