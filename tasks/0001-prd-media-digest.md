# PRD: Media Digest - Automated Podcast & Newsletter Summarization

## Introduction/Overview

Media Digest is an internal tool designed to solve the problem of information overload from subscriptions to 20+ podcasts and 30+ daily newsletters. Instead of spending hours listening to full episodes or reading lengthy newsletters, this tool automatically downloads, transcribes, and summarizes content, allowing the user to quickly scan summaries and only deep-dive into high-value content.

The tool outputs structured notes to an Obsidian vault (specifically the `5-Resources/0-Media digester` folder) with daily and weekly digests, making it easy to stay informed without consuming dozens of hours of media.

**Goal:** Enable the user to extract actionable insights from 20+ podcasts/week and 30+ newsletters/day without manual listening/reading, reducing content consumption time by 80% while maintaining awareness of key topics, tools, companies, and ideas.

## Goals

1. **Automate content ingestion** from podcast RSS feeds (via OPML) and newsletters (via Gmail)
2. **Generate structured summaries** for each episode/newsletter with key topics, companies, tools, and quotes
3. **Provide daily and weekly digest notes** that surface the most relevant content with LLM-based ratings
4. **Track processing status** for all content (pending, in-progress, completed, failed)
5. **Auto-tag content** using existing Obsidian vault tags (max 5 per item) read from a Dataview file
6. **Surface failures explicitly** in daily/weekly digests so broken feeds or processing errors are visible
7. **Enable deep-dive navigation** by providing timestamps and links to original content

## User Stories

1. **As a user, I want to import my podcast subscriptions via OPML** so that all my podcasts are automatically tracked without manual entry.

2. **As a user, I want to see which podcasts/newsletters have been processed (fully, partially, or failed)** so I can understand what content is available and troubleshoot issues.

3. **As a user, I want to read a daily summary note each morning** so I can quickly scan all new content from the previous day.

4. **As a user, I want to read a weekly summary note (Fridays)** so I can review the week's top 3-4 insights per item and prioritize what to explore.

5. **As a user, I want to read detailed per-episode/newsletter notes** with summaries, key topics, companies, tools, and quotes so I can decide if the full content is worth my time.

6. **As a user, I want to use timestamps to jump to interesting sections in YouTube videos** so I can quickly verify or explore content that caught my attention.

7. **As a user, I want content auto-tagged with my existing Obsidian tags (max 5)** so new notes integrate seamlessly into my existing knowledge base without tag proliferation.

8. **As a user, I want to see explicit error messages in daily/weekly digests** (e.g., "Failed: Episode Title — reason: download timeout") so I can fix broken feeds or retry failed items.

9. **As a user, I want the system to run automatically via cron** so I don't have to manually trigger processing.

10. **As a user, I want all outputs written directly to my Obsidian vault folder `5-Resources/0-Media digester`** so notes are immediately available across all my devices.

## Functional Requirements

### Ingestion

**FR1:** The system MUST accept a podcast subscription list via OPML file (located at `data/podcasts.opml`) and parse all RSS feed URLs.

**FR2:** The system MUST discover new episodes from tracked podcast RSS feeds daily.

**FR3:** The system MUST connect to Gmail via OAuth and fetch newsletters from configured Gmail labels (e.g., "newsletters", "INBOX") since a configurable start date (default: 2025-10-01).

**FR4:** The system MUST discover new newsletters daily from configured Gmail labels.

**FR5:** The system MUST store episode metadata (title, publish date, author, audio URL, video URL if available, GUID) and newsletter metadata (subject, sender, date, message ID, link) in a database.

**FR6:** The system MUST track processing status for each item: `pending`, `in_progress`, `completed`, `failed`.

### Processing - Podcasts

**FR7:** The system MUST download audio files for new podcast episodes (audio-only, even if video is available).

**FR8:** The system MUST transcribe audio using Whisper (medium model) running locally on the Hetzner VM via the `faster-whisper` library.

**FR9:** The system MUST handle transcription failures gracefully and log the error reason.

**FR10:** The system MUST clean and structure transcripts (remove filler words, segment by topic) using an LLM.

**FR11:** The system MUST support a retry mechanism (max 3 retries with exponential backoff) for failed downloads or transcriptions.

### Processing - Newsletters

**FR12:** The system MUST extract plain text content from HTML newsletters.

**FR13:** The system MUST handle various newsletter formats (plain text, HTML-heavy, embedded images).

**FR14:** The system MUST support a retry mechanism (max 2 retries) for failed fetches or parsing.

**FR15:** The system MUST ignore attachments completely.

### Summarization & Analysis

**FR16:** The system MUST generate a 2-3 sentence overall summary for each episode/newsletter using an LLM (Anthropic Claude API).

**FR17:** The system MUST extract and list key topics (3-5 topics per item).

**FR18:** The system MUST identify and list companies mentioned with brief context.

**FR19:** The system MUST identify and list tools/products mentioned with brief context.

**FR20:** The system MUST extract 2-4 noteworthy quotes with timestamps (for podcasts) or section references (for newsletters).

**FR21:** The system MUST generate an LLM-based rating (1-5 scale) with a conservative distribution (5s are rare, 3s are common) using a structured prompt.

**FR22:** The system MUST store both raw LLM rating and final rating.

### Tagging

**FR23:** The system MUST read existing tags from the Obsidian Dataview file located at `w_Dashboards/List of tags.md` in the vault.

**FR24:** The system MUST propose up to 5 tags per item by analyzing content against the tag list using an LLM.

**FR25:** The system MUST NOT create new tags unless explicitly configured to do so.

**FR26:** The system MUST place tags only in YAML frontmatter (no inline `#tag` usage).

**FR27:** The system MAY allow manual tag list updates (weekly refresh is nice-to-have, not required).

### Export to Obsidian

**FR28:** The system MUST generate one Markdown note per episode/newsletter with the following structure:
- YAML frontmatter: title, date, tags (list), author (list), guests (list), link, rating (empty for manual entry), type, version, LLM rating
- Overall summary
- Key topics (bulleted list)
- Companies (bulleted list with context)
- Tools (bulleted list with context)
- Noteworthy quotes (with timestamps for podcasts, section references for newsletters)
- **NO full text** - only links to original content

**FR29:** The system MUST write notes to the Obsidian vault path: `<VAULT_ROOT>/5-Resources/0-Media digester/` where `<VAULT_ROOT>` points to the "Marc main" vault.

**FR30:** The system MUST generate a daily digest note (generated at 5:00 AM UTC) that includes:
- List of all processed episodes/newsletters with one-line summaries
- Explicit "Failures" section listing failed items with error reasons
- "Top themes" section
- "Actionables" section

**FR31:** The system MUST generate a weekly digest note (generated Fridays at 6:00 AM UTC) that includes:
- Top 3-4 takeaways per item from the week (Sat 00:00 → Fri 23:59 UTC)
- Items sorted by LLM rating (desc) then recency
- Explicit "Failures" section for the week

**FR32:** The system MUST be idempotent (re-running export does not duplicate content).

**FR33:** The system MUST NOT overwrite notes where the user has manually filled in the `Rating:` field.

### Timestamp Links

**FR34:** For podcasts with YouTube links (domain contains `youtube.com` or `youtu.be`), the system MUST format timestamps as clickable YouTube links: `https://youtube.com/watch?v=ID&t=123s`.

**FR35:** For podcasts without YouTube links, the system MUST format timestamps as plain text `[MM:SS]` for manual navigation in the user's podcast app (Pocket Casts, etc.).

### Orchestration & Scheduling

**FR36:** The system MUST provide a CLI with the following commands (for manual runs, debugging, or if cron fails):
- `discover --since [DATE]` - discover new episodes/newsletters
- `process-audio --retries [N]` - download and transcribe podcasts
- `process-newsletters --retries [N]` - fetch and parse newsletters
- `build-daily --date [DATE]` - generate daily digest
- `build-weekly --ending [DATE]` - generate weekly digest
- `export-obsidian --date [DATE] | --weekly [DATE]` - export notes to vault

**FR37:** The system MUST run scheduled tasks via cron (all times in UTC):
- 1:10 AM - discover new items
- 1:20 AM - process audio (7-hour timeout)
- 3:30 AM - process newsletters
- 5:00 AM - build daily digest + export
- 6:00 AM (Fridays) - build weekly digest + export

**FR38:** The system MUST use flock-based locking to prevent concurrent runs of the same task.

### Configuration & Secrets

**FR39:** The system MUST load secrets from a `.env` file (gitignored) including:
- `START_DATE=2025-10-01`
- `GMAIL_ADDRESS=decafvibes@gmail.com`
- `GMAIL_OAUTH_TOKEN_PATH=/opt/digestor/secure/gmail_token.json`
- `VAULT_ROOT=/Users/marc/Documents/Obsidian notes/Marc new3/Marc main` (the root of the Obsidian vault, used for reading tags only)
- `TAG_DATAVIEW_PATH=w_Dashboards/List of tags.md` (relative to vault root)
- `OUTPUT_REPO_PATH=/opt/digestor/output` (Git repo on Hetzner that syncs to vault subfolder)
- `TIMEZONE=UTC`
- `ANTHROPIC_API_KEY=<user's own key from console.anthropic.com>`

**FR40:** The system MUST load configuration from a committed `config.yaml` including:
- OPML path: `data/podcasts.opml`
- Gmail labels to monitor (e.g., `["newsletters", "INBOX"]`)
- Whisper model settings (medium)
- Tagging settings (max tags: 5)
- Export settings (daily/weekly times)
- Output path: `5-Resources/0-Media digester`

### Error Handling & Observability

**FR41:** The system MUST log all operations to a log file with timestamps and severity levels.

**FR42:** The system MUST store error reasons in the database for failed items.

**FR43:** The system MUST include failed items in daily/weekly digests with clear error messages.

**FR44:** The system MUST support manual retry of individual failed items via CLI.

### Data Storage

**FR45:** The system MUST use DuckDB as the embedded database for storing:
- Episode/newsletter metadata
- Processing status and timestamps
- Error logs
- Transcripts and summaries
- Tags and ratings

**FR46:** The system MUST store downloaded audio files and transcripts in a `blobs/` directory.

## Non-Goals (Out of Scope)

1. **No web UI or dashboard** - This is a CLI tool with Obsidian as the UI.

2. **No real-time processing** - Batch processing via cron is sufficient.

3. **No speaker diarization initially** - Speaker labels are a future enhancement.

4. **No semantic search (FAISS/embeddings)** - DuckDB full-text search is sufficient for MVP.

5. **No custom GPU infrastructure** - Use local CPU-based Whisper on Hetzner.

6. **No multi-user support** - This is a single-user personal tool.

7. **No automatic feed discovery** - User must provide OPML or manually add feeds.

8. **No podcast hosting or playback** - Use existing podcast apps; this tool generates summaries only.

9. **No paywalled newsletter handling** - Only process content accessible via Gmail (add auth support later if needed).

10. **No video processing** - Audio-only extraction for podcasts, even if video is available.

11. **No attachment processing** - Completely ignore attachments in newsletters.

12. **No incremental processing** - Full download before processing (no streaming/chunking).

13. **No newsletter sender list maintenance** - Process all emails in configured Gmail labels.

## Design Considerations

### Obsidian Note Templates

Notes should use Jinja2 templates with the following structure:

**Per-Episode/Newsletter Note:**
```markdown
---
title: {{title}}
date: {{published_iso}}
tags:
  - {{tag1}}
  - {{tag2}}
author:
  - {{author1}}
  - {{author2}}
guests:
  - {{guest1}}
  - {{guest2}}
link: {{primary_link}}
rating:
type: {{podcast|newsletter}}
version: {{episode_or_message_id}}
rating_llm: {{llm_rating}}
---

# {{title}}

> **Summary:** {{overall_summary}}

## Key topics
- {{topic1}}
- {{topic2}}

## Companies
- **{{company_name}}** — {{context}}

## Tools
- **{{tool_name}}** — {{context}}

## Noteworthy quotes
> {{quote_text}}
— [{{timestamp}}]({{youtube_link_with_timestamp}})

## Original content
[View original]({{primary_link}})
```

**Daily Digest Note:**
- Date header
- List all items with one-line summaries and links
- "Failures" section with error reasons
- "Top themes" section (3-5 themes from LLM analysis)
- "Actionables" section (action items extracted from content)

**Weekly Digest Note:**
- Week range header (Sat → Fri)
- Top 3-4 takeaways per item
- Sorted by LLM rating (desc), then recency
- "Failures" section for the week

### Vault Sync Strategy

**Note:** The Obsidian vault "Marc main" (`/Users/marc/Documents/Obsidian notes/Marc new3/Marc main`) contains many personal folders including journals. For privacy, **only the subfolder** `5-Resources/0-Media digester/` will be version controlled and synced via Git.

**Architecture:**
1. **Hetzner VM** writes notes to local Git repo at `/opt/digestor/output`
2. After each export, Hetzner commits and pushes to **private GitHub repo**
3. **User's Mac** pulls from GitHub repo every 30 minutes via cron
4. Mac's local copy is at `~/Documents/Obsidian notes/Marc new3/Marc main/5-Resources/0-Media digester/`
5. **Obsidian Sync** detects file changes and propagates to user's other devices

**Why this approach:**
- ✅ Main vault stays private (no Git for personal notes/journals)
- ✅ Only digest notes are version controlled
- ✅ Works seamlessly with existing Obsidian Sync
- ✅ Hetzner only has access to digest notes, not personal vault
- ✅ Version history for digest notes

**Tag reading:**
- System will **read** from `w_Dashboards/List of tags.md` in the main vault (not in Git)
- Access method: User will manually copy tag file to Hetzner, or mount vault read-only via secure method (to be determined during implementation)

## Technical Considerations

### Stack

- **Runtime:** Python 3.11
- **Database:** DuckDB (embedded, single-file, zero-ops)
- **ASR:** Whisper (medium model) via `faster-whisper` library (runs on CPU)
- **LLM:** Anthropic Claude API (for summarization, cleaning, tagging, rating)
- **Scheduling:** Cron + flock
- **Dependencies:**
  - `faster-whisper` (ASR)
  - `feedparser` (RSS parsing)
  - `python-dotenv` (env vars)
  - `pyyaml` (config)
  - `duckdb` (database)
  - `requests` (HTTP)
  - `jinja2` (templates)
  - `google-auth` + `google-auth-oauthlib` + `google-auth-httplib2` (Gmail OAuth)
  - `beautifulsoup4` (HTML parsing)
  - `anthropic` (Claude API client)
  - `yt-dlp` (audio download from YouTube and other sources)

### Gmail OAuth Setup

1. Go to [Google Cloud Console](https://console.cloud.google.com)
2. Create a new project (e.g., "Media Digest")
3. Enable **Gmail API**
4. Configure OAuth consent screen (Internal or External)
5. Create OAuth 2.0 credentials (type: Desktop app)
6. Download `credentials.json`
7. Run initial OAuth flow script (will open browser, user grants access)
8. Script saves token to `GMAIL_OAUTH_TOKEN_PATH`
9. System auto-refreshes token when expired (handled by Google client library)

**Required OAuth scope:** `https://www.googleapis.com/auth/gmail.readonly`

### Whisper Model Selection

Using **Whisper medium** model:
- **Size:** ~1.5 GB
- **Speed:** ~4x real-time on 2 vCPU Hetzner VM (60 min audio → 15 min transcription)
- **Accuracy:** Excellent for English podcasts (95%+ WER)
- **Cost:** $0 (runs locally)

**Alternative:** Whisper `small` model if `medium` is too slow (3x faster, 90%+ WER).

**Why not `large`?** Large-v3 is ~3 GB and only marginally better for English podcasts. Not worth the speed tradeoff.

### Cost Estimation

**Assumptions:**
- 20 podcasts/week (avg 30 min each) = ~80 episodes/month
- 30 newsletters/day = ~900 newsletters/month
- Total: ~980 items/month to summarize

**Monthly Costs:**
- **Transcription (Whisper local):** **$0** (runs on Hetzner CPU)
- **Summarization (Claude API):**
  - 980 items × $0.01/item (estimated cost per summary) = **~$10/month**
  - Note: Actual cost depends on token usage; may be lower with Haiku model
- **Hetzner VM (CX21 - 2 vCPU, 4 GB RAM):** **€5.83/month (~$6.50/month)**

**Total: ~$16.50/month** (within $15 target if using Claude Haiku for some tasks)

**Cost optimization:**
- Use Claude Haiku for cleaning/tagging (cheaper)
- Use Claude Sonnet only for final summaries and ratings (better quality)
- Cache system prompts (Anthropic offers prompt caching)

### Retry & Failure Handling

- **Max retries:** 3 for audio processing, 2 for newsletters
- **Backoff:** Exponential (1 min, 2 min, 4 min)
- **Failure storage:** Store `error_reason` in DuckDB with timestamp
- **Manual retry:** `cli.py retry --item-id [ID]`
- **Permanent skip:** `cli.py skip --item-id [ID]` (marks as `skipped` status)

### Idempotency

- Use episode GUID (podcasts) and message ID (newsletters) as unique keys in database
- Check database before downloading/processing (skip if already `completed`)
- Allow re-export to Obsidian (overwrite existing notes by title **unless** user has filled in `rating:` field)
- Detect manual edits by checking if `rating:` field is non-empty

### Transcript Cleaning

LLM cleaning prompt will:
- Remove filler words: "um", "uh", "like", "you know"
- Remove repetitions (Whisper sometimes hallucinates repeated phrases)
- Segment by topic with paragraph breaks
- Fix obvious transcription errors (e.g., "open AI" → "OpenAI")
- Keep timestamps aligned to original audio

### Handling Long Podcasts

- Average: 30 min
- Max expected: 3 hours (e.g., deep-dive interviews)
- Whisper handles up to 4 hours without issues
- If episode > 4 hours, flag as `long-form` and process in full (rare case)

### YouTube Timestamp Links

Logic:
```python
if 'youtube.com' in link or 'youtu.be' in link:
    # Extract video ID
    video_id = extract_youtube_id(link)
    # Convert timestamp to seconds
    timestamp_seconds = timestamp_to_seconds(timestamp)  # e.g., "12:34" → 754
    # Format link
    return f"https://youtube.com/watch?v={video_id}&t={timestamp_seconds}s"
else:
    # Plain timestamp
    return f"[{timestamp}]"  # e.g., "[12:34]"
```

## Success Metrics

1. **Processing success rate ≥ 95%** (items successfully processed vs total discovered)
2. **Daily digest generated before 6:00 AM UTC** (99% of days)
3. **Weekly digest generated before 7:00 AM UTC on Fridays** (99% of weeks)
4. **Tag accuracy ≥ 90%** (tags match user's existing vault taxonomy from Dataview file)
5. **User time savings:** Reduce content consumption from ~10 hours/week to ~2 hours/week (80% reduction)
6. **User satisfaction:** User rates 80% of LLM ratings as accurate (±1 point)
7. **Cost:** Stay under $17/month (preferably $15/month)

## Open Questions

1. ✅ **RESOLVED: Can Anthropic Claude API transcribe audio?**
   - Answer: No, using local Whisper on Hetzner instead.

2. ✅ **RESOLVED: What is the average podcast episode length?**
   - Answer: 30 minutes (user confirmed)

3. ✅ **RESOLVED: How should the system handle video podcasts (YouTube)?**
   - Answer: Extract audio-only for MVP

4. **What is the desired behavior for 4+ hour episodes (rare edge case)?**
   - **Recommendation:** Process in full, flag as `long-form` type

5. ✅ **RESOLVED: How should conflicts be handled if the user edits a note in Obsidian while the system tries to update it?**
   - Answer: Never overwrite if user changed `rating:` field (indicates manual edit)

6. ✅ **RESOLVED: Should the system support private/authenticated podcast feeds (e.g., Patreon)?**
   - Answer: No for MVP, add later if needed

7. **What is the exact format of the Dataview file `w_Dashboards/List of tags.md`?**
   - Need to see sample to write parser
   - Assume it's a simple list or table of tags

8. ✅ **RESOLVED: Should the system support newsletter attachments (PDFs, etc.)?**
   - Answer: Ignore completely for MVP

9. ✅ **RESOLVED: What is the desired format for "jump to timestamp" links?**
   - Answer: YouTube links with embedded timestamps for YouTube content; plain `[MM:SS]` for other sources

10. ✅ **RESOLVED: Should the system support incremental processing?**
    - Answer: No for MVP

11. ✅ **RESOLVED: How should the system authenticate to push to the user's vault Git repo?**
    - Answer: SSH key on Hetzner VM with GitHub deploy key (write access)

12. ✅ **RESOLVED: Tag file format**
    - Answer: Simple list with `#` prefix, one tag per line (e.g., `#skill/growth`)
    - Parser will filter out malformed entries like `#[object` or non-tag lines

13. **Should failed items be auto-retried on next run, or require manual retry?**
    - **Recommendation:** Auto-retry once, then require manual retry to avoid infinite loops

14. **How should the tag Dataview file be accessed on Hetzner?**
    - Option A: User manually copies/uploads when tags change
    - Option B: Mount vault read-only via secure method (VPN, Tailscale, etc.)
    - **Recommendation:** Option A for MVP (manual copy), Option B for v2

## Appendix: LLM Prompts

All prompts use Anthropic Claude API. System prompts should be cached for cost optimization.

### A.1 Transcript Cleaning Prompt

**System Prompt (cacheable):**
```
You are a transcript editor. Your job is to clean and structure podcast transcripts for readability.

Rules:
1. Remove filler words: "um", "uh", "like" (when used as filler), "you know"
2. Remove repetitions and obvious Whisper hallucinations
3. Fix obvious transcription errors (e.g., "open AI" → "OpenAI", "GPT three" → "GPT-3")
4. Segment by topic with paragraph breaks (every 3-5 sentences or topic shift)
5. Preserve timestamps in format [HH:MM:SS] or [MM:SS]
6. Do NOT summarize or remove content - only clean
7. Keep speaker labels if present (e.g., "Speaker 1:", "Host:")

Output the cleaned transcript with timestamps preserved.
```

**User Prompt (per episode):**
```
Clean this podcast transcript:

Title: {{title}}
Duration: {{duration}}

Raw transcript:
{{raw_transcript}}
```

---

### A.2 Summarization Prompt

**System Prompt (cacheable):**
```
You are a content analyst. Your job is to summarize podcasts and newsletters for busy professionals.

For each piece of content, extract:
1. **Summary** (2-3 sentences): What is this about? Why does it matter?
2. **Key topics** (3-5 topics): Main themes or subjects discussed
3. **Companies** (0-5): Companies mentioned, with 1-sentence context
4. **Tools** (0-5): Tools, products, or technologies mentioned, with 1-sentence context
5. **Quotes** (2-4): Most interesting or insightful quotes (with timestamps for podcasts)

Be concise. Focus on actionable insights.
```

**User Prompt (per episode/newsletter):**
```
Analyze this content:

Type: {{podcast|newsletter}}
Title: {{title}}
Author: {{author}}
Date: {{date}}

Content:
{{cleaned_transcript_or_newsletter_text}}

Output JSON:
{
  "summary": "2-3 sentence summary",
  "key_topics": ["topic1", "topic2", ...],
  "companies": [{"name": "Company", "context": "Brief context"}, ...],
  "tools": [{"name": "Tool", "context": "Brief context"}, ...],
  "quotes": [{"text": "Quote text", "timestamp": "12:34" or "section name"}, ...]
}
```

---

### A.3 Tagging Prompt

**System Prompt (cacheable):**
```
You are a tagging assistant. Your job is to assign relevant tags from a whitelist to content.

Rules:
1. Only use tags from the provided whitelist
2. Maximum 5 tags per item
3. Tags should be relevant and specific
4. Prefer more specific tags over generic ones
5. If no tags match well, return fewer tags (minimum 0)
6. Never invent new tags

Output JSON: {"tags": ["tag1", "tag2", ...]}
```

**User Prompt (per episode/newsletter):**
```
Assign tags to this content:

Title: {{title}}
Summary: {{summary}}
Key topics: {{key_topics}}

Available tags (whitelist):
{{tag_whitelist}}

Output JSON:
{"tags": ["tag1", "tag2", ...]}
```

---

### A.4 Rating Prompt

**System Prompt (cacheable):**
```
You are a content quality rater. Your job is to rate podcasts and newsletters on a 1-5 scale based on their value to a busy professional interested in technology, business, and personal growth.

Rating scale:
- 5: Exceptional - Must-read/listen, highly actionable or insightful
- 4: Very good - Worth deep dive, clear takeaways
- 3: Good - Interesting but not urgent
- 2: Mediocre - Low signal, mostly filler
- 1: Poor - Not worth time, skip

**Be conservative with ratings:**
- 5s should be rare (top 5% of content)
- 4s should be uncommon (top 20%)
- Most content should be rated 3
- 2s and 1s for low-quality or off-topic content

Output JSON:
{
  "rating": 3,
  "rationale": "One sentence explaining the rating"
}
```

**User Prompt (per episode/newsletter):**
```
Rate this content:

Type: {{podcast|newsletter}}
Title: {{title}}
Summary: {{summary}}
Key topics: {{key_topics}}
Companies: {{companies}}
Tools: {{tools}}

Output JSON:
{
  "rating": 3,
  "rationale": "One sentence explaining the rating"
}
```

---

### A.5 Daily Digest Themes & Actionables Prompt

**System Prompt (cacheable):**
```
You are a content synthesizer. Your job is to identify top themes and actionable items from a day's worth of podcasts and newsletters.

From the list of summaries:
1. Identify 3-5 **top themes** (recurring topics across multiple items)
2. Extract 3-5 **actionables** (specific actions, tools to try, concepts to research)

Be concise and specific.
```

**User Prompt (daily):**
```
Analyze today's content:

Date: {{date}}

Summaries:
{{list_of_summaries}}

Output JSON:
{
  "themes": ["Theme 1", "Theme 2", ...],
  "actionables": ["Action 1", "Action 2", ...]
}
```

---

### A.6 Weekly Digest Top Takeaways Prompt

**System Prompt (cacheable):**
```
You are a content curator. Your job is to extract the top 3-4 takeaways from a piece of content for a weekly digest.

Focus on:
- Most valuable insights
- Actionable information
- Surprising or contrarian ideas
- Practical tips or strategies

Each takeaway should be 1-2 sentences with a timestamp/section reference.
```

**User Prompt (per item, for weekly digest):**
```
Extract top takeaways:

Title: {{title}}
Summary: {{summary}}
Key topics: {{key_topics}}
Quotes: {{quotes}}
Rating: {{llm_rating}}

Output JSON:
{
  "takeaways": [
    {"text": "Takeaway 1", "reference": "12:34 or section name"},
    {"text": "Takeaway 2", "reference": "..."},
    ...
  ]
}
```

---

## Appendix: Git Setup Instructions

### Overview

The `5-Resources/0-Media digester/` subfolder will be a separate Git repository that syncs between Hetzner and your Mac.

### Step 1: Create GitHub Repository (On GitHub.com)

1. Go to https://github.com/new
2. Repository name: `media-digest-notes` (or any name you prefer)
3. Description: "Automated podcast and newsletter digests"
4. **Visibility: Private** (important - keeps your notes private)
5. Do NOT initialize with README, .gitignore, or license
6. Click "Create repository"
7. Copy the SSH URL (e.g., `git@github.com:yourusername/media-digest-notes.git`)

### Step 2: Initialize Git Repo on Your Mac

```bash
# Navigate to the digest folder
cd '/Users/marc/Documents/Obsidian notes/Marc new3/Marc main/5-Resources/0-Media digester'

# Initialize Git
git init

# Add remote (replace with your repo URL)
git remote add origin git@github.com:yourusername/media-digest-notes.git

# Create initial README
echo "# Media Digest Notes" > README.md
echo "Automated digests from podcasts and newsletters" >> README.md

# Initial commit
git add .
git commit -m "Initial setup"

# Push to GitHub
git branch -M main
git push -u origin main
```

### Step 3: Generate SSH Key on Hetzner VM

```bash
# SSH into your Hetzner VM
ssh root@your-hetzner-ip

# Generate SSH key
ssh-keygen -t ed25519 -C "media-digest-hetzner" -f ~/.ssh/media_digest

# Display public key (copy this)
cat ~/.ssh/media_digest.pub
```

### Step 4: Add Deploy Key to GitHub Repository

1. Go to your GitHub repo → Settings → Deploy keys
2. Click "Add deploy key"
3. Title: `Hetzner VM - Media Digest`
4. Key: Paste the public key from Step 3
5. ✅ Check "Allow write access" (important!)
6. Click "Add key"

### Step 5: Configure Git on Hetzner VM

```bash
# Still on Hetzner VM

# Add SSH config for GitHub
mkdir -p ~/.ssh
cat >> ~/.ssh/config <<'EOF'
Host github.com
  IdentityFile ~/.ssh/media_digest
  IdentitiesOnly yes
EOF

# Set correct permissions
chmod 600 ~/.ssh/media_digest
chmod 600 ~/.ssh/config

# Test SSH connection
ssh -T git@github.com
# You should see: "Hi username! You've successfully authenticated..."

# Clone the repo
git clone git@github.com:yourusername/media-digest-notes.git /opt/digestor/output

# Configure Git user
cd /opt/digestor/output
git config user.email "media-digest-bot@yourdomain.com"
git config user.name "Media Digest Bot"
```

### Step 6: Set Up Auto-Pull on Your Mac

```bash
# On your Mac, add to crontab
crontab -e

# Add this line (pulls every 30 minutes)
*/30 * * * * cd '/Users/marc/Documents/Obsidian notes/Marc new3/Marc main/5-Resources/0-Media digester' && /usr/bin/git pull origin main --quiet >> /tmp/media-digest-pull.log 2>&1
```

**Alternative:** Use a LaunchAgent for better reliability (optional):

```bash
# Create LaunchAgent
cat > ~/Library/LaunchAgents/com.mediadigest.gitpull.plist <<'EOF'
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.mediadigest.gitpull</string>
    <key>ProgramArguments</key>
    <array>
        <string>/bin/sh</string>
        <string>-c</string>
        <string>cd '/Users/marc/Documents/Obsidian notes/Marc new3/Marc main/5-Resources/0-Media digester' && /usr/bin/git pull origin main --quiet</string>
    </array>
    <key>StartInterval</key>
    <integer>1800</integer>
    <key>StandardOutPath</key>
    <string>/tmp/media-digest-pull.log</string>
    <key>StandardErrorPath</key>
    <string>/tmp/media-digest-pull-error.log</string>
</dict>
</plist>
EOF

# Load the agent
launchctl load ~/Library/LaunchAgents/com.mediadigest.gitpull.plist
```

### Step 7: Test the Flow

**On Hetzner VM:**
```bash
cd /opt/digestor/output
echo "Test note from Hetzner" > test.md
git add test.md
git commit -m "Test commit"
git push origin main
```

**On Your Mac (wait up to 30 minutes or manually pull):**
```bash
cd '/Users/marc/Documents/Obsidian notes/Marc new3/Marc main/5-Resources/0-Media digester'
git pull origin main
# Check if test.md appeared
ls -la test.md
```

**In Obsidian:**
- Open your vault
- Navigate to `5-Resources/0-Media digester`
- You should see `test.md`
- Obsidian Sync will propagate this to your other devices

### Step 8: Hetzner Export Script (Integrated into CLI)

The CLI's export function will include:

```python
def export_and_push():
    """Export notes and push to Git."""
    output_path = os.getenv('OUTPUT_REPO_PATH')

    # Write notes to output_path
    write_notes(output_path)

    # Git operations
    subprocess.run(['git', 'add', '.'], cwd=output_path)

    # Commit with date
    commit_msg = f"Daily digest {datetime.now().strftime('%Y-%m-%d')}"
    subprocess.run(['git', 'commit', '-m', commit_msg], cwd=output_path)

    # Push to remote
    subprocess.run(['git', 'push', 'origin', 'main'], cwd=output_path)
```

### Tag File Access

**For MVP:** Manually copy tag file to Hetzner when tags change:

```bash
# On your Mac (run when tags change)
scp '/Users/marc/Documents/Obsidian notes/Marc new3/Marc main/w_Dashboards/List of tags.md' root@your-hetzner-ip:/opt/digestor/data/tags.md
```

**For v2:** Consider secure mount or Tailscale VPN for read-only access to vault.

---

## Appendix: Configuration Files

### `.env` (gitignored)

```bash
START_DATE=2025-10-01
GMAIL_ADDRESS=decafvibes@gmail.com
GMAIL_OAUTH_TOKEN_PATH=/opt/digestor/secure/gmail_token.json
VAULT_ROOT=/Users/marc/Documents/Obsidian notes/Marc new3/Marc main
TAG_DATAVIEW_PATH=w_Dashboards/List of tags.md
OUTPUT_REPO_PATH=/opt/digestor/output
TIMEZONE=UTC
ANTHROPIC_API_KEY=sk-ant-...
```

### `config.yaml` (committed)

```yaml
ingest:
  podcasts_opml: data/podcasts.opml
  email:
    since: ${START_DATE}
    labels: ["newsletters", "INBOX"]

processing:
  asr:
    model: medium  # whisper model: tiny, base, small, medium, large
    device: cpu
    compute_type: int8  # int8 or float16

  cleaner:
    enabled: true

  tagging:
    max_tags_per_doc: 5
    allow_new_tags: false

export:
  vault_root: ${VAULT_ROOT}
  output_path: 5-Resources/0-Media digester
  daily_time: "05:00"  # UTC
  weekly_day: "FRI"
  weekly_time: "06:00"  # UTC

retry:
  max_retries_audio: 3
  max_retries_newsletters: 2
  backoff_base: 60  # seconds
```

---

## Appendix: Directory Structure

```
media-digest/
├── .env                      # Secrets (gitignored)
├── .gitignore
├── config.yaml               # Configuration (committed)
├── cli.py                    # Main CLI entry point
├── requirements.txt
├── data/
│   ├── podcasts.opml         # Podcast subscriptions
│   └── tag_whitelist.txt     # Cached tag list (optional)
├── blobs/                    # Audio files, transcripts (gitignored)
│   ├── audio/
│   └── transcripts/
├── logs/                     # Log files (gitignored)
│   └── digest.log
├── secure/                   # OAuth tokens (gitignored)
│   └── gmail_token.json
├── digestor.duckdb           # Database (gitignored)
├── templates/                # Jinja2 templates
│   ├── episode.md.j2
│   ├── newsletter.md.j2
│   ├── daily.md.j2
│   └── weekly.md.j2
└── src/
    ├── __init__.py
    ├── ingest/
    │   ├── podcasts.py
    │   └── newsletters.py
    ├── process/
    │   ├── asr.py
    │   ├── cleaner.py
    │   └── parser.py
    ├── summarize/
    │   ├── summarizer.py
    │   ├── tagger.py
    │   └── rater.py
    ├── export/
    │   ├── obsidian.py
    │   └── templates.py
    ├── db/
    │   ├── schema.py
    │   └── queries.py
    └── utils/
        ├── config.py
        ├── logging.py
        └── youtube.py
```

---

## Appendix: Tag Parser Implementation

### Tag File Format

The Dataview file `w_Dashboards/List of tags.md` contains 162 tags in the following format:

```
Tag162
#[object
#ai-model/claude
#ai-model/gemini
#ai-model/gpt-4
#skill/growth
#skill/gtm
#type/article
...
```

### Parser Implementation

```python
def parse_tags_from_dataview(file_path: str) -> list[str]:
    """
    Parse tags from Obsidian Dataview file.

    Args:
        file_path: Path to the Dataview tag list file

    Returns:
        List of clean tags (without # prefix)

    Example:
        >>> tags = parse_tags_from_dataview('/opt/digestor/data/tags.md')
        >>> print(tags[:3])
        ['ai-model/claude', 'ai-model/gemini', 'ai-model/gpt-4']
    """
    tags = []

    with open(file_path, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()

            # Skip empty lines
            if not line:
                continue

            # Skip lines that don't start with #
            if not line.startswith('#'):
                continue

            # Skip malformed entries
            if '[' in line or ']' in line:
                continue

            # Remove leading # and add to list
            tag = line[1:]  # Remove the #

            # Skip if tag is empty after removing #
            if not tag:
                continue

            tags.append(tag)

    return tags
```

### Expected Output

Running the parser on the user's tag file should yield approximately 162 valid tags:

```python
[
    'ai-model/claude',
    'ai-model/gemini',
    'ai-model/gpt-4',
    'ai-model/llama',
    'ai/agents',
    'ai/embeddings',
    'dev-framework/nextjs',
    'dev-framework/react',
    'domain/engineering',
    'domain/marketing',
    'domain/product',
    'skill/growth',
    'skill/gtm',
    'skill/leadership',
    'tool/cursor',
    'tool/figma',
    'type/article',
    'type/guide',
    'type/prd',
    # ... ~143 more tags
]
```

---

## Notes

- User's Anthropic API key must be obtained from [console.anthropic.com](https://console.anthropic.com) (cannot reuse Claude Code key)
- Obsidian vault "Marc main" is on user's local desktop at `/Users/marc/Documents/Obsidian notes/Marc new3/Marc main`
- Only the subfolder `5-Resources/0-Media digester` will be written to (as a separate Git repo)
- Tag whitelist is read from `w_Dashboards/List of tags.md` (parser provided above)
- Tag file will be manually copied to Hetzner for MVP (via `scp`)
- Podcasts: ~20/week, avg 30 min each
- Newsletters: ~30/day via Gmail
- Target cost: $15/month (estimated $16.50/month with Claude Haiku optimization)
- Git sync: Hetzner → GitHub → Mac → Obsidian Sync → Other devices
