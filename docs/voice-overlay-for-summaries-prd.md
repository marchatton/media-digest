# Voice Overlay for Summaries – PRD

## 1. Overview
Create an automated "voice overlay" so every generated summary (daily digest + per-podcast summaries) is accompanied by an audio rendition stored directly inside the Obsidian vault. Audio should be created during the Hetzner pipeline, synced via Obsidian Sync, and playable from desktop or mobile where the user can manually mark items as read. This avoids local watchers, keeps GitHub free of binaries, and leverages small, privacy-friendly TTS options where possible.

## 2. Goals
1. Automatically produce an audio file for each new/updated daily summary and podcast summary generated on Hetzner.
2. Store the audio next to its markdown note in Obsidian so playback works on desktop and mobile without extra apps.
3. Provide a lightweight way inside Obsidian (hotkey/button) to move a consumed note+audio into the "read" area.
4. Keep the Git history text-only (audio ignored) while still syncing audio to all devices via Obsidian Sync.
5. Keep runtime + storage costs low by favoring open-source/local TTS (e.g., Piper) but allowing cloud providers if desired.

## 3. User Stories
- As a daily digest consumer, I want each digest note to include an embedded audio player so I can listen hands-free on phone or desktop.
- As someone triaging podcast summaries, I want audio to appear automatically once the note is created so I never run a manual "generate" step.
- As a multitasking listener, I want playback controls directly in Obsidian and a single hotkey/button to mark the note as read once I finish.
- As the repository owner, I want large binary audio files excluded from GitHub but still synced to my devices through Obsidian Sync.
- As an operator of the Hetzner job, I want a cron-friendly script that can run unattended, report failures, and avoid re-generating unchanged audio.

## 4. Functional Requirements
1. **Audio generation trigger:** After the Hetzner pipeline finishes writing/refreshing a summary note (daily or podcast), call a TTS render step before the job completes.
2. **Text extraction:** Renderer must pull clean text (frontmatter excluded) with sensible defaults (intro summary first, optional truncation if extremely long).
3. **TTS providers:** Support at least one open-source/local option (Piper) running on Hetzner CPU and allow swapping to a cloud API (ElevenLabs, Polly, etc.) via configuration.
4. **Encoding:** Output mono MP3 (48–64 kbps) named predictably (e.g., `<note-slug>.mp3`) to keep files small for sync.
5. **Embedding:** Insert or update a `![[filename.mp3]]` block near the top of the markdown so Obsidian displays a player automatically.
6. **Caching:** Skip re-generation if the note text hash matches the last rendered version; refresh only when content changes.
7. **File placement:** Save audio beside the markdown (same folder). Ensure both move together when the user re-files notes.
8. **Git hygiene:** Add/confirm `*.mp3` (and hash cache files) live in `.gitignore` so GitHub pushes remain text-only.
9. **Sync compatibility:** Ensure resulting files work with Obsidian Sync (size under a few MB, no exotic formats); no additional storage service required.
10. **Mark-as-read helper:** Provide an Obsidian command (Templater/QuickAdd or tiny plugin) that moves the current note and its audio twin from `/unread/` to `/read/` when invoked.
11. **Observability:** Log TTS activity (success/failure, duration). On failure, leave the note untouched and record an error so it can be retried manually.
12. **Cron friendliness:** Package the render step as a CLI or script callable from cron/systemd on Hetzner, with idempotent behavior when run repeatedly.

## 5. Non-Goals
- Streaming playback outside Obsidian (no mobile/web player beyond the vault).
- Automatic detection that playback finished; user manually marks as read.
- Long-form podcast audio transcription or editing—the feature only voices summaries already produced.
- Storage/backup outside the existing Obsidian Sync + local vault setup.
- Rich playlist UX, push notifications, or scheduling playback.

## 6. Design Considerations
- Audio embed should sit immediately after the summary title so it’s obvious on mobile.
- Manual mark-as-read can be as simple as a command palette action that runs "Move current file (and matching `.mp3`) to `/read/`"; no special UI beyond what Obsidian offers.
- Consider a tiny status line in each note (e.g., `Audio rendered: 2024-06-23 05:00 UTC`) so the user can tell if a file is fresh.

## 7. Technical Considerations
- **TTS Engine:** Start with Piper (CPU) for cost-free operation on Hetzner. Models (~50–150 MB) can live in `/opt/digestor/models`. Keep provider selection configurable via `config.yaml` or env vars so switching to ElevenLabs/Polly only changes config.
- **Dependencies:** Piper output is WAV; convert to MP3 via `ffmpeg`/`lame`. Ensure these binaries are installed on Hetzner or shipped with the project.
- **Cron integration:** Add a post-processing step (script or `cli.py` subcommand) that runs after summaries are generated. Example: `cli.py render-audio --targets daily,podcasts`.
- **Hash cache:** Write `<note>.mp3.sha256` (gitignored) storing the text hash + provider info to avoid redundant renders.
- **Error handling:** Retry transient failures (network to cloud TTS) with backoff. If rendering fails, leave a TODO block in the markdown so the user knows audio is missing.
- **Storage footprint:** Estimate ~1 MB per summary; with ~4/day you add ~120 MB/month. Plan periodic cleanup or archiving (e.g., prune mp3 > 90 days old) if vault nears the 10 GB Sync quota.
- **Security:** Keep any API keys (if cloud provider chosen) in env vars or Hetzner secrets; never commit them or place inside synced vault.

## 8. Success Metrics
- 100% of newly generated daily + podcast summaries include an audio embed within five minutes of note creation.
- Audio generation failures stay below 2% per week (tracked via logs).
- Obsidian Sync latency for new audio remains under two minutes on average (spot-checked).
- User reports zero manual steps needed to produce audio (only to mark notes as read).
- Vault size growth remains <1.5 GB per quarter attributable to audio (validated via periodic checks or automated reports).

## 9. Open Questions
1. Which Obsidian automation method is preferred for the "move current note + mp3" command (Templater, QuickAdd, or custom plugin)?
2. Should old audio files be auto-pruned after a retention window, or is manual cleanup acceptable?
3. Do we need multilingual support immediately, or is English-only sufficient for the first release?
4. Is Piper quality adequate, or should the MVP include a cloud provider fallback from day one?
5. Should the render step also cover any other content types (newsletters, weekly digests) beyond daily + podcast summaries?
