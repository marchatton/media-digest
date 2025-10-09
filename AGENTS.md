# Agent Guidelines for Media Digest

## Overview

This document provides instructions for AI coding agents (Claude Code, Cursor, etc.) working on the Media Digest project. Follow these guidelines to ensure consistent, high-quality contributions.

## Core Philosophy

**SHIP FAST, ITERATE BASED ON REAL USE.** This is a personal tool. Perfect is the enemy of done. Build the MVP, use it, learn, improve.

**TEST CORE BUSINESS LOGIC.** Not everything needs tests, but test the logic that matters: tagging, rating distribution, idempotency, LLM prompt construction. Write tests first for these.

**COST-CONSCIOUS DEVELOPMENT.** Target: $15/month. Use local Whisper (free), optimize LLM calls, cache aggressively.

**CREATE SMALL, FREQUENT PRS.** Don't accumulate large changesets. Ship incremental progress often.

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
- **Small PRs**: 100-300 lines per PR, single clear purpose

### Tech Stack
- **Language**: Python 3.11+
- **Database**: DuckDB (embedded, single file)
- **Transcription**: Whisper medium (local via faster-whisper)
- **Summarization**: Anthropic Claude API (Haiku for cost, Sonnet for quality)
- **Scheduling**: Cron + flock
- **Sync**: Git (Hetzner → GitHub → Mac)

## Agent Workflow

### 1. Before Starting Work

**Understand the context:**
- Read CLAUDE.md for full project guidelines
- Review existing code structure
- Check open issues/PRs for related work
- Ask clarifying questions about requirements

**Plan your approach:**
- Break large tasks into small, incremental steps
- Identify what can be shipped in <500 line PRs
- Plan test coverage for core logic
- Consider cost implications of LLM usage

### 2. During Development

**Write code that follows project standards:**
- Use type hints everywhere
- Prefer immutable data structures
- Use Protocol for abstractions
- Write tests first for core business logic
- Keep functions pure and small
- Use early returns over deep nesting

**Keep commits atomic:**
- One logical change per commit
- Write clear commit messages
- Reference issue numbers where applicable
- Don't mix refactoring with feature work

**Test as you go:**
- Run tests frequently (`pytest`)
- Test edge cases and error conditions
- Ensure idempotency of operations
- Verify cost implications of LLM calls

### 3. Creating Pull Requests

**PR Frequency:**
- Create PR after completing discrete unit of work
- Don't wait for "perfect" - ship working increments
- Target 100-300 lines changed per PR
- Maximum 500 lines (split larger changes)

**PR Content:**
- Single, clear purpose
- Tests included with code
- Updated documentation if needed
- No unrelated changes mixed in

**PR Description Template:**
```markdown
## What
Brief description of what this PR does (1-2 sentences)

## Why
Why this change is needed

## Testing
- [ ] Unit tests added/updated
- [ ] Manually tested with [specific scenario]

## Cost Impact
- Estimated monthly cost impact (if applicable)

## Notes
Any context, tradeoffs, or follow-up work needed
```

### 4. PR Examples

✅ **Good PR cadence:**
- Add database schema for episodes table → PR
- Implement RSS feed parser → PR
- Add transcript cleaning function → PR
- Wire up CLI command for ingestion → PR
- Add LLM summarization with caching → PR

❌ **Bad PR cadence:**
- Implement entire podcast processing pipeline → One giant PR
- Add feature + refactor existing code + update docs → Mixed concerns

## Code Style Guidelines

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

## Testing Strategy

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

### TDD Process (For Core Logic Only)
1. **Red**: Write failing test for desired behavior
2. **Green**: Write minimal code to pass
3. **Refactor**: Improve if needed, keep tests green

**Note:** Not everything needs TDD. Use it for business logic that's complex or error-prone. Skip it for glue code, CLI commands, and API wrappers.

## Cost Optimization

### Target: $15/month

**Always consider cost when:**
- Adding new LLM calls
- Choosing between Claude models (Haiku vs Sonnet)
- Implementing caching strategies
- Batching operations

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

## Idempotency Rules

### All Operations Must Be Idempotent
Running the same operation twice should produce the same result as running it once.

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

## Common Tasks

### Adding a New Feature

1. **Plan the work** (break into <500 line PRs)
2. **Create a branch** with descriptive name
3. **Write tests first** (if core logic)
4. **Implement minimal solution** (KISS)
5. **Verify idempotency** (safe to re-run)
6. **Check cost impact** (estimate monthly cost)
7. **Create PR** with clear description
8. **Iterate based on feedback**

### Fixing a Bug

1. **Write a failing test** that reproduces the bug
2. **Fix the bug** with minimal changes
3. **Verify the test passes**
4. **Check for similar bugs** in related code
5. **Create PR** with bug description and fix

### Refactoring

1. **Ensure tests exist** for code being refactored
2. **Make small, incremental changes**
3. **Run tests after each change**
4. **Keep refactoring separate** from feature work
5. **Create focused PR** explaining improvements

## Agent-Specific Tips

### For Claude Code / Cursor / Copilot

**Do:**
- Read CLAUDE.md and AGENTS.md before starting
- Ask questions when requirements are unclear
- Suggest simpler alternatives to complex solutions
- Point out when a change should be split into multiple PRs
- Consider cost implications of LLM-heavy features
- Update documentation as you learn new things

**Don't:**
- Implement features not explicitly requested (YAGNI)
- Mix unrelated changes in one PR
- Skip tests for core business logic
- Use mutation when immutable updates are possible
- Ignore idempotency requirements
- Create PRs larger than 500 lines without asking

### Communication

**Be proactive about:**
- Asking clarifying questions upfront
- Suggesting cost/performance tradeoffs
- Pointing out potential issues early
- Recommending simpler alternatives
- Breaking large tasks into smaller PRs

**Update this file when you:**
- Discover patterns that should be followed
- Find anti-patterns that should be avoided
- Learn cost optimization techniques
- Identify common pitfalls

## Privacy & Security

### Privacy First
- Main Obsidian vault contains personal journals → **not in Git**
- Only `5-Resources/0-Media digester/` is version controlled
- Tag file manually copied to Hetzner (no vault access needed)
- Never log or store personal information

### Security Considerations
- Use subprocess.run() with list args (no shell=True)
- Validate all user inputs
- Use OAuth for Gmail (no passwords)
- Store API keys in .env (never commit)
- Use prepared statements for database queries

## Resources

### Key Files
- `CLAUDE.md` - Full development guidelines
- `AGENTS.md` - This file (agent-specific workflow)
- `README.md` - Project overview and setup
- `config.yaml` - Configuration (non-secrets)
- `.env` - Secrets (not in Git)

### Documentation
- DuckDB: https://duckdb.org/docs/
- faster-whisper: https://github.com/guillaumekln/faster-whisper
- Anthropic API: https://docs.anthropic.com/
- Jinja2: https://jinja.palletsprojects.com/

## Summary

Build the simplest thing that works. Use it daily. Fix annoyances. Optimize when cost/performance becomes a real problem, not a theoretical one.

**Ship small, ship often.** Create PRs at logical checkpoints, not when everything is "done". This is a personal tool—perfect is the enemy of shipped.

When in doubt: **ask questions, suggest simpler alternatives, and create smaller PRs.**
