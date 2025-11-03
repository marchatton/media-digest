# Development Guidelines for Claude - Media Digest

## Core Philosophy

**SHIP FAST, ITERATE BASED ON REAL USE.** This is a personal tool. Perfect is the enemy of done. Build the MVP, use it, learn, improve.

**TEST CORE BUSINESS LOGIC.** Not everything needs tests, but test the logic that matters: tagging, rating distribution, idempotency, LLM prompt construction. Write tests first for these.

**COST-CONSCIOUS DEVELOPMENT.** Target: $15/month. Use local Whisper (free), optimize LLM calls, cache aggressively.

## Quick Reference

### Key Principles
- **TDD for core logic**: Test first for tagging, rating, idempotency, LLM prompts
- **SOLID**: Single responsibility, open/closed, dependency inversion
- **DRY**: Don't repeat knowledge (business rules have one source of truth)
- **KISS**: Simplest solution first (subprocess over libraries, DuckDB over Postgres)
- **YAGNI**: Skip features until proven necessary (no diarization, no embeddings in MVP)
- **Functional programming**: Immutable data, pure functions, early returns
- **Type hints everywhere**: Python 3.11+ with Protocol for abstractions
- **Idempotent operations**: Safe to re-run, respects manual edits

### Tech Stack
- **Language**: Python 3.11+
- **Database**: DuckDB (embedded, single file)
- **Transcription**: Whisper medium (local via faster-whisper)
- **Summarization**: Anthropic Claude API (Haiku for cost, Sonnet for quality)
- **Scheduling**: Cron + flock
- **Sync**: Git (Hetzner → GitHub → Mac)

## Project Context

### What This Tool Does
Automatically processes 20 podcasts/week and 30 newsletters/day into structured Obsidian notes with:
- 2-3 sentence summaries
- Key topics, companies, tools
- Noteworthy quotes with timestamps
- LLM-based ratings (1-5 scale)
- Auto-tags from existing Obsidian taxonomy

### What This Tool Is NOT
- Not a web app (CLI only)
- Not multi-user (single user, personal vault)
- Not real-time (batch processing via cron)
- Not feature-complete on day 1 (ship MVP, iterate)

## Core Principles

### SOLID (Adapted for Python)
- **Single Responsibility**: One module per concern (ingest, process, summarize, export)
- **Open/Closed**: Extend via new modules, not by modifying existing ones
- **Liskov Substitution**: ASR/LLM providers are swappable via interfaces
- **Interface Segregation**: Small, focused protocols (Transcriber, Summarizer, Exporter)
- **Dependency Inversion**: Depend on abstractions (Protocol), not concrete classes

### DRY = Don't Repeat Knowledge
Not about code duplication, but about business rules having a single source of truth.

```python
# Good: Single source of truth
MAX_TAGS_PER_ITEM = 5

def select_tags(candidates: list[str]) -> list[str]:
    return candidates[:MAX_TAGS_PER_ITEM]

# Bad: Magic numbers scattered
tags = candidates[:5]  # Why 5?
```

### KISS & YAGNI
- Use `subprocess.run()` for Git, not GitPython library
- Use DuckDB, not Postgres (simpler, zero-ops)
- No speaker diarization in MVP (add later if needed)
- No FAISS/embeddings in MVP (DuckDB FTS is enough)

## Code Style

### Type Hints Everywhere
```python
from typing import Protocol
from datetime import datetime

class Transcriber(Protocol):
    def transcribe(self, audio_path: str) -> str: ...

def process_episode(
    episode_id: str,
    transcriber: Transcriber,
    *,
    retries: int = 3
) -> dict[str, str | datetime]:
    """Process a podcast episode."""
    # Implementation
```

### Functional Programming
```python
# Good: Immutable updates
def add_tag(item: dict, tag: str) -> dict:
    return {**item, "tags": [*item.get("tags", []), tag]}

# Bad: Mutation
def add_tag(item: dict, tag: str) -> None:
    item.setdefault("tags", []).append(tag)
```

### Error Handling
```python
from dataclasses import dataclass

@dataclass
class Success:
    value: dict

@dataclass
class Failure:
    error: str

Result = Success | Failure

def download_audio(url: str) -> Result:
    try:
        # Download logic
        return Success(value={"path": "/tmp/audio.mp3"})
    except Exception as e:
        return Failure(error=f"Download failed: {e}")
```

## Testing Strategy

### TDD Process (For Core Logic Only)
1. **Red**: Write failing test for desired behavior
2. **Green**: Write minimal code to pass
3. **Refactor**: Improve if needed, keep tests green

**Note:** Not everything needs TDD. Use it for business logic that's complex or error-prone. Skip it for glue code, CLI commands, and API wrappers.

### What to Test (TDD)
✅ **Core business logic:**
- Tag selection from whitelist (max 5, intersect with candidates)
- LLM rating distribution (ensure 5s are rare)
- Idempotency (re-export doesn't duplicate)
- YouTube timestamp link generation

✅ **Integration points:**
- DuckDB schema and queries
- Jinja2 template rendering
- OPML parsing
- Gmail OAuth token refresh

❌ **Don't test:**
- Third-party libraries (feedparser, faster-whisper, anthropic)
- Cron schedules (test the functions, not cron)
- Git operations (subprocess calls)
- CLI argument parsing (test the underlying functions)

### Test Organization
```
tests/
├── test_tagging.py        # Tag whitelist intersection, max 5
├── test_summarization.py  # LLM prompt construction, rating logic
├── test_export.py         # Obsidian note generation, idempotency
├── test_ingest.py         # OPML parsing, RSS feed discovery
└── fixtures/
    ├── sample_opml.xml
    ├── sample_tags.txt
    └── sample_transcript.txt
```

## Cost Optimization

### Target: $15/month

**Current estimate: $16.50/month**
- Transcription: $0 (local Whisper)
- Summarization: ~$10/month (980 items × $0.01)
- Hetzner VM: ~$6.50/month

**Optimization strategies:**
1. **Use Claude Haiku for cheap tasks:**
   - Transcript cleaning: Haiku
   - Tagging: Haiku
   - Rating: Sonnet (quality matters here)

2. **Cache system prompts:**
   - Anthropic offers prompt caching
   - System prompts are ~500 tokens each
   - Cache hits save 90% of cost

3. **Batch LLM calls:**
   - Process multiple items in one API call where possible
   - Reduce per-request overhead

4. **Optimize Whisper:**
   - Use `medium` model (not `large`)
   - Use `int8` compute type (faster, uses less RAM)
   - If still too slow, drop to `small` model

## Idempotency Rules

### Safe to Re-run
All operations must be idempotent (running twice = running once):

```python
def export_note(episode: Episode, output_path: str) -> None:
    """Export episode note to Obsidian vault."""
    note_path = output_path / f"{episode.date}_{episode.slug}.md"

    # Check if user has manually edited (rating field filled)
    if note_path.exists():
        content = note_path.read_text()
        if "rating: " in content and not content.startswith("rating:\n"):
            logger.info(f"Skipping {note_path} - user has edited")
            return

    # Safe to overwrite
    note_path.write_text(render_template(episode))
```

### Database Operations
```python
# Use INSERT OR REPLACE / UPSERT patterns
db.execute("""
    INSERT INTO episodes (guid, title, status)
    VALUES (?, ?, ?)
    ON CONFLICT (guid) DO UPDATE SET
        title = excluded.title,
        updated_at = CURRENT_TIMESTAMP
""", (episode.guid, episode.title, "completed"))
```

## Media Digest Specifics

### Privacy First
- Main Obsidian vault contains personal journals → **not in Git**
- Only `5-Resources/0-Media digester/` is version controlled
- Tag file manually copied to Hetzner (no vault access needed)

### Data Flow
```
┌─────────────────────────────────────────────────────┐
│ 1. INGEST (Daily 1:10 AM UTC)                      │
│    RSS feeds → DuckDB (new episodes)                │
│    Gmail → DuckDB (new newsletters)                 │
└─────────────────────────────────────────────────────┘
              ↓
┌─────────────────────────────────────────────────────┐
│ 2. PROCESS (Daily 1:20 AM UTC)                     │
│    Audio download → Whisper → Cleaned transcript    │
│    Newsletter fetch → HTML parse → Plain text       │
└─────────────────────────────────────────────────────┘
              ↓
┌─────────────────────────────────────────────────────┐
│ 3. SUMMARIZE (Async, as items complete)            │
│    Transcript → Claude → Summary + Topics + Rating  │
│    Newsletter → Claude → Summary + Topics + Rating  │
│    Tag whitelist → Claude → Auto-tags (max 5)       │
└─────────────────────────────────────────────────────┘
              ↓
┌─────────────────────────────────────────────────────┐
│ 4. EXPORT (Daily 5:00 AM UTC)                      │
│    DuckDB → Jinja2 → Markdown notes                 │
│    Git commit → Git push → GitHub                   │
└─────────────────────────────────────────────────────┘
              ↓
┌─────────────────────────────────────────────────────┐
│ 5. SYNC (Mac pulls every 30 min)                   │
│    GitHub → Mac → Obsidian Sync → Other devices     │
└─────────────────────────────────────────────────────┘
```

### Failure Handling
- All failures logged to DuckDB with `status=failed` and `error_reason`
- Daily/weekly digests include explicit "Failures" section
- Auto-retry once, then require manual `cli.py retry --item-id [ID]`

### YouTube Timestamp Links
```python
def format_timestamp_link(quote: Quote, episode: Episode) -> str:
    """Generate timestamp link for quotes."""
    if "youtube.com" in episode.link or "youtu.be" in episode.link:
        video_id = extract_youtube_id(episode.link)
        seconds = timestamp_to_seconds(quote.timestamp)
        return f"https://youtube.com/watch?v={video_id}&t={seconds}s"
    else:
        # Plain timestamp for non-YouTube (Pocket Casts, etc.)
        return f"[{quote.timestamp}]"
```

## Working with Claude

### Expectations
1. **Ship MVP first** - Don't over-engineer
2. **Ask clarifying questions** - Especially about cost/performance tradeoffs
3. **Suggest simpler alternatives** - If you see complexity creep
4. **Update this file** - Add learnings as you discover them
5. **Create PRs frequently** - Small, focused PRs are better than large ones

### Pull Request Guidelines
**CREATE SMALL, FREQUENT PRS.** Don't wait until a feature is "done" to create a PR. Create PRs at logical checkpoints:

✅ **Good PR cadence:**
- Add database schema → PR
- Implement RSS feed parser → PR
- Add LLM summarization → PR
- Wire up CLI commands → PR

❌ **Bad PR cadence:**
- Implement entire podcast processing pipeline → One giant PR

**PR Size Guidelines:**
- Target: 100-300 lines changed per PR
- Maximum: 500 lines (beyond this, split into multiple PRs)
- Each PR should have a single, clear purpose
- Tests should be included in the same PR as the code they test

**When to Create a PR:**
1. After completing a discrete unit of work (one module, one feature)
2. Before starting work that depends on review feedback
3. When you've made progress worth preserving (even if incomplete)
4. End of each work session if you have working code

**PR Description Template:**
```markdown
## What
Brief description of what this PR does (1-2 sentences)

## Why
Why this change is needed

## Testing
- [ ] Unit tests added/updated
- [ ] Manually tested with [specific scenario]

## Notes
Any context, tradeoffs, or follow-up work needed
```

### Anti-Patterns to Avoid
```python
# Never
item["tags"].append(tag)                    # Mutation
if x: if y: if z: ...                      # Deep nesting (use early returns)
tags = llm_response.split(",")[:5]         # Fragile parsing (use structured output)
subprocess.run("rm -rf /", shell=True)     # Shell injection risk
```

### Prefer
```python
# Always
new_item = {**item, "tags": [*item["tags"], tag]}  # Immutable
if not valid: return error                          # Early returns
tags = TagResponse.parse_raw(llm_response).tags[:5] # Structured parsing
subprocess.run(["git", "push"], cwd=repo_path)      # Safe subprocess
```

## Configuration Management

### Environment Variables (.env)
```bash
# Secrets only
START_DATE=2025-10-01
GMAIL_ADDRESS=decafvibes@gmail.com
GMAIL_OAUTH_TOKEN_PATH=/opt/digestor/secure/gmail_token.json
VAULT_ROOT=/Users/marc/Documents/Obsidian notes/Marc new3/Marc main
OUTPUT_REPO_PATH=/opt/digestor/output
ANTHROPIC_API_KEY=sk-ant-...
```

### Config File (config.yaml)
```yaml
# Non-secrets, version controlled
ingest:
  podcasts_opml: data/podcasts.opml
  email:
    labels: ["newsletters", "INBOX"]

processing:
  asr:
    model: medium
    compute_type: int8

  tagging:
    max_tags_per_doc: 5
```

## Deployment Checklist

### Hetzner VM Setup
- [ ] Python 3.11+ installed
- [ ] faster-whisper + Whisper medium model downloaded
- [ ] SSH key generated and added to GitHub as deploy key
- [ ] Cron jobs configured with flock locks
- [ ] Gmail OAuth token generated and uploaded
- [ ] Tag whitelist copied to `/opt/digestor/data/tags.md`
- [ ] DuckDB file initialized with schema

### Mac Setup
- [ ] Git repo cloned to `~/Documents/Obsidian notes/Marc new3/Marc main/5-Resources/0-Media digester`
- [ ] Cron job or LaunchAgent pulling every 30 min
- [ ] Obsidian Sync enabled

## Updates Log
Add discoveries that would have been helpful earlier:

- Whisper `medium` takes ~4x real-time on 2 vCPU Hetzner (60 min → 15 min)
- DuckDB requires explicit `COMMIT` for transactions
- Anthropic API has rate limits (60 req/min on Sonnet)
- Gmail OAuth token expires after 7 days of inactivity (auto-refresh handles this)
- Jinja2 templates must escape user content to avoid XSS in Obsidian

## Summary
Build the simplest thing that works. Use it daily. Fix annoyances. Optimize when cost/performance becomes a real problem, not a theoretical one. This is a personal tool—perfect is the enemy of shipped.
