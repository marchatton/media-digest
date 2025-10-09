Perfect—here’s a crisp plan with your exact choices baked in (start date, Obsidian tags, weekly digest, Hetzner, minimal ops).

# Decisions up-front (so you can build now)

* **Start date:** **2025-10-01** (hard-coded).
* **Email:** `decafvibes@gmail.com` → kept in **.env** (gitignored).
* **ASR choice:** **Whisper** on cloud (robust, fast, widely supported). Keep a pluggable interface so you *could* swap in Parakeet later.

  * Orchestrator + storage on **Hetzner** (CPU VM).
  * ASR runs on a **GPU endpoint** (serverless or a small on-demand GPU box).
  * Cleaner & summariser via your preferred cloud LLM.
* **Tags:** reuse **existing Obsidian tags** only, max **5 per episode** (strict). We’ll scan the vault to build a whitelist and only assign from that set.
* **Outputs:** one **note per episode/newsletter**, a **daily** digest, and a **weekly** digest (Fridays) with top 3–4 items per doc.
* **Observability:** logs + healthchecks only. No heavy dashboards.

---

# Minimal, production-ready stack

**Runtime:** Python 3.11 • DuckDB (embedded DB) • ffmpeg • faster-whisper client • CRON

**Why DuckDB (vs SQLite/Postgres)?**

* Zero-ops like SQLite, **but columnar** → blazing fast analytics (daily/weekly rollups, entity counts).
* Single file, easy backups; no server to manage (fits your “internal tool, minimal observability” goal).
* If you ever outgrow it, you can export/ingest to Postgres later.

---

# Cloud layout (Option A: Hetzner + GPU ASR)

* **hetzner-vm (CPU)**

  * runs cron, main pipeline, DuckDB, writing directly into your **Obsidian vault folder** (mounted or Git-pushed).
* **gpu-asr (serverless or on-demand)**

  * exposes a simple HTTPS `/transcribe` (auth via token), runs Whisper large-v3 (or medium if cost-sensitive).
  * If ASR endpoint fails, fall back to CPU Whisper-small on Hetzner and flag `asr_degraded=true`.

This keeps your 8 GB M1 cool and still simple.

---

# Config you can paste

**`.env` (gitignored)**

```
START_DATE=2025-10-01
GMAIL_ADDRESS=decafvibes@gmail.com
GMAIL_OAUTH_TOKEN_PATH=/opt/digestor/secure/gmail_token.json
VAULT_PATH=/vault      # mount your Obsidian vault here or clone a repo into it
TIMEZONE=Europe/London
ASR_ENDPOINT=https://gpu-asr.example.com/transcribe
ASR_TOKEN=...
LLM_PROVIDER=openai
OPENAI_API_KEY=...
```

**`config.yaml` (committed)**

```yaml
ingest:
  podcasts_opml: data/podcasts.opml
  feeds: []               # extra RSS feeds if you want
  email:
    since: ${START_DATE}
    folders: ["INBOX"]    # your inbox is newsletters/events
processing:
  asr:
    provider: remote      # remote|local
    model: whisper-large-v3
    max_concurrency: 2
  cleaner:
    enforce_length_band_pct: 10
  tagging:
    max_tags_per_doc: 5
    whitelist_source: scan_vault   # scan_vault|file
    whitelist_file: data/tag_whitelist.txt
export:
  vault_path: ${VAULT_PATH}
  daily_time: "05:00"
  weekly_day: "FRI"
  weekly_time: "06:00"
```

---

# CRON (London time on Hetzner)

```
# discover new items daily
10 1 * * *  digestor  flock -n /tmp/discover.lock bash -lc "cd /opt/digestor && venv/bin/python cli.py discover --since ${START_DATE}"

# podcasts: download -> asr (remote) -> clean
20 1 * * *  digestor  flock -n /tmp/asr.lock timeout 7h bash -lc "cd /opt/digestor && venv/bin/python cli.py process-audio --retries 3"

# newsletters: gmail + feeds
30 3 * * *  digestor  flock -n /tmp/news.lock bash -lc "cd /opt/digestor && venv/bin/python cli.py process-newsletters --retries 2"

# build daily digest + export notes
0 5 * * *   digestor  flock -n /tmp/daily.lock bash -lc "cd /opt/digestor && venv/bin/python cli.py build-daily --date today && venv/bin/python cli.py export-obsidian --date today"

# weekly digest (Fridays)
0 6 * * 5   digestor  flock -n /tmp/weekly.lock bash -lc "cd /opt/digestor && venv/bin/python cli.py build-weekly --ending today && venv/bin/python cli.py export-obsidian --weekly today"
```

*(Add healthchecks.io pings if you want, but you said minimal is fine.)*

---

# Obsidian note templates (exactly your fields)

### Per-episode (or newsletter) note

```markdown
---
title: {{title}}
date: {{published_iso}}
tags:
{{#each tags}}  - {{this}}
{{/each}}
Author: {{author_or_host}}
guests: {{guests_csv}}
Link: {{primary_link}}   # video > audio > webpage, in that order
Rating:                  # (you fill in manually later)
type: {{podcast|newsletter}}
version: {{episode_or_message_id}}
Rating (LLM): {{llm_rating}}    # 1-5, conservative distribution
---

# {{title}}

> **Summary:** {{overall_summary}}

## Key topics
{{#each key_topics}}- {{this}}{{/each}}

## Companies
{{#each companies}}- **{{name}}** — {{context}}{{/each}}

## Tools
{{#each tools}}- **{{name}}** — {{context}}{{/each}}

## Noteworthy quotes
{{#each quotes}}
> {{text}}
— {{timestamp_or_section}}  {{jump_link_if_audio}}
{{/each}}

## Full text
{{cleaned_excerpt_or_sectioned_text}}
```

### Daily digest note

* Lists each episode/newsletter (with one-line summary), and **explicitly lists failures**:

  * `⚠️ Failed: <Episode Title> — reason: timeout while downloading`
  * `⚠️ Failed: <Newsletter Title> — reason: IMAP fetch error`
* Includes a “Top themes” & “Actionables” section.

### Weekly digest (Fridays)

* For each doc from the week, include **top 3–4 takeaways** max, with timestamp/section pointer.

---

# Tagging: reuse your Obsidian tags (max 5)

**How it works**

1. **Whitelist build (on first run + weekly):**

   * Scan your vault for YAML `tags:` and inline `#tags`.
   * Normalise (case, dashes, spaces).
   * Save to `data/tag_whitelist.txt`. *(If you prefer, maintain this file manually.)*

2. **Per-doc tag selection:**

   * Extract candidate tags (NER + keyphrases + a tiny LLM adjudicator).
   * Intersect with **whitelist**, score by frequency & salience.
   * Take **top 5** max (strict).
   * If nothing matches, apply **0–2 generic** fallbacks you already use (e.g., `skill/growth`, `skill/gtm`) *only if warranted*.
   * Never invent new tags unless you opt-in.

3. **Placement:** tags only in YAML frontmatter (no inline `#tag` spam).

---

# ASR: Whisper (cloud) vs Parakeet — quick trade-offs

* **Whisper (recommended):**

  * Pros: state-of-the-art English accuracy, timestamps, resilient to noise; huge ecosystem (faster-whisper, serverless images).
  * Cons: large-v3 can be pricey on GPU (use batching and medium where possible).

* **Parakeet:**

  * Pros: competitive research model, interesting diarization pipelines depending on distro.
  * Cons: less turnkey infra + tooling; fewer serverless providers; slower to iterate.

**Plan:** Use **remote Whisper** now. Keep a provider interface:

```
asr/
  base.py      # Transcriber interface
  whisper.py   # Remote + local
  parakeet.py  # (optional later)
```

---

# “Failed to download” items

* Any episode/newsletter that fails (download, auth, parse, ASR) is entered with `status` + `error_reason`.
* **Daily & weekly** digests always include a **Failures** section with titles and reasons, so you can retry or fix feeds.
* Retries happen automatically next run (idempotent by episode GUID / newsletter Message-ID).

---

# Areas we can simplify (and what you lose)

1. **Skip diarization initially.**

   * ✅ Simpler, faster.
   * ❌ Speaker labels less precise (we’ll still mark changes).

2. **Skip FAISS/embeddings at MVP.**

   * ✅ Less infra.
   * ❌ No semantic search yet (DuckDB FTS still gives good lexical search).

3. **One LLM for both cleaning & summarising.**

   * ✅ Fewer keys/providers.
   * ❌ Slightly less control vs best-of-breed per step.

4. **Cron + logs only (no Prefect).**

   * ✅ Zero dashboard.
   * ❌ No fancy retry UI—still fine for personal tool.

5. **Remote ASR only; no local fallback.**

   * ✅ Less code on Hetzner.
   * ❌ If ASR endpoint is down, you’ll only get failures listed (you *asked* to surface them).

*(You can add each “nice-to-have” later without redesign.)*

---

# Obsidian sync trade-offs (pick one)

* **Git + Obsidian Git plugin (free, private)**

  * ✅ Version history, easy backup, works offline.
  * ⚠️ Occasional merge conflicts if you edit on multiple devices simultaneously.
  * Setup: Hetzner pushes to remote; devices pull on open/interval.

* **Obsidian Sync (paid, very simple)**

  * ✅ E2E encrypted, conflict handling is good, fastest multi-device.
  * ⚠️ No commit history; monthly cost; server writes directly into the live vault (be cautious with heavy writes).

* **Cloud drive (iCloud/Dropbox/Drive)**

  * ✅ Already have it; no extra setup.
  * ⚠️ Can be flaky with many small files/rapid writes; conflict artifacts; slower indexing on mobile.

**Recommendation:** Git if you’re comfortable; otherwise Obsidian Sync.

---

# LLM rating (1–5) with sane distribution

* **LLM proposes** a score + 1-line rationale.
* We **calibrate** weekly so 5s are rare:

  * Compute per-week mean & std of candidate scores, convert to **z-scores**, then map:

    * `z >= 1.2 → 5`, `0.5–1.2 → 4`, `-0.5–0.5 → 3`, `-1.2––0.5 → 2`, `< -1.2 → 1`.
  * Store both `raw_llm_rating` and final `Rating (LLM)`.

---

# Weekly digest logic (Fridays)

* Window: **Sat 00:00 → Fri 23:59** (Europe/London).
* For each doc, compute **top 3–4 takeaways** using the map-phase summaries (no re-ASR).
* Sort within the week by **Rating (LLM)** desc, then recency.

---

# Sample `.gitignore` (add this verbatim)

```
# env & secrets
.env
*.env
/secure/
/config/local.yaml
*.key
*.pem

# data & cache
/data/
/blobs/
/vault/.obsidian/workspace.json
*.duckdb
*.duckdb.wal
/logs/
/__pycache__/

# tokens
*.json
token_*
gmail_token.json

# OS/editor
.DS_Store
.idea/
.vscode/
```

---

# Final glue you’ll want in the repo scaffold

* `cli.py` with:

  * `discover --since ${START_DATE}`
  * `process-audio --retries 3`
  * `process-newsletters --retries 2`
  * `build-daily --date`
  * `build-weekly --ending`
  * `export-obsidian --date|--weekly`
* **Vault tag scanner**: `tools/scan_vault_tags.py` → writes `data/tag_whitelist.txt`.
* **Templates**: `templates/episode.md.j2`, `newsletter.md.j2`, `daily.md.j2`, `weekly.md.j2`.
* **Schema validators** for summaries + rating calibration step.

If you want, I can spit out the exact Jinja templates + a tiny tag-scanner script next.
