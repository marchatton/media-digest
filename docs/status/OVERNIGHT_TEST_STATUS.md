# Overnight Test Status

## What's Running

I've started a background process to test the full Media Digest pipeline with a short TED talk episode (~10-15 minutes).

### Process ID: 194705
**Command**: `python3 cli.py process-audio --limit 1`

**Episode being processed**: "The hidden cost of buying gold | Claudia Vega" (TED Talk from Oct 10, 2025)

## Timeline (Estimated)

1. **Model Download** (5-10 min) - Downloading Whisper medium model (~1.5GB)
2. **Audio Download** (1-2 min) - Downloading the TED talk audio
3. **Transcription** (10-20 min) - Whisper transcription on CPU for ~10-15 min audio
4. **Next Steps** (manual): Run summarization and export

**Total estimated time**: 15-30 minutes

## What to Do in the Morning

### Check if the process completed:

```bash
cd /Users/marc/Code/personal-projects/media-digest/media-digest/.conductor/harrisburg
tail -50 logs/process.log
```

### If successful, run the full pipeline:

```bash
# This will run: process → summarize → export
./scripts/run_full_test.sh
```

### Or run steps manually:

```bash
# Step 1: Check what's been processed
python3 -c "import duckdb; conn = duckdb.connect('digestor.duckdb'); print(conn.execute('SELECT title, status FROM episodes LIMIT 5').fetchall())"

# Step 2: Summarize (uses Claude API with your key)
python3 cli.py summarize --limit 1

# Step 3: Export to Obsidian format
python3 cli.py export --limit 1

# Step 4: Check the output
ls -lh output/
cat output/*.md
```

## Hetzner Setup - Next Steps

Once you complete verification tomorrow morning:

### 1. Create Server
- **Type**: CX22 (2 vCPU, 4GB RAM) - €5.83/month
- **OS**: Ubuntu 22.04
- **Location**: Choose closest (US East/West or Europe)
- **SSH Key**: Generate one with:
  ```bash
  ssh-keygen -t ed25519 -C "media-digest-hetzner" -f ~/.ssh/hetzner_media_digest
  cat ~/.ssh/hetzner_media_digest.pub  # Copy this to Hetzner
  ```

### 2. SSH In
```bash
ssh -i ~/.ssh/hetzner_media_digest root@YOUR_SERVER_IP
```

### 3. Install Dependencies
```bash
# Update system
apt update && apt upgrade -y

# Install Python 3.11+
apt install -y python3.11 python3.11-pip python3.11-venv git

# Install system dependencies for audio processing
apt install -y ffmpeg

# Verify
python3.11 --version
```

### 4. Clone Repo
```bash
mkdir -p /opt/digestor
cd /opt/digestor
git clone https://github.com/marchatton/media-digest.git .
```

### 5. Set Up Environment
```bash
# Install Python dependencies
pip3.11 install -r requirements.txt

# Copy .env file (you'll need to edit it)
cp .env.example .env
nano .env  # Add your ANTHROPIC_API_KEY

# Create directories
mkdir -p data blobs/audio blobs/transcripts logs secure output
```

### 6. Test Discovery
```bash
# Copy your OPML file
# (You'll need to scp it from your Mac or create it on the server)

# Run discovery
python3.11 cli.py discover --since 2025-10-01
```

## Current Progress

✅ Project setup complete
✅ All Python modules implemented
✅ CLI commands integrated (discover, process-audio, summarize, export)
✅ Database schema created
✅ Sample OPML with shorter podcasts (TED, NPR)
✅ .env configured with your API key
✅ Dependencies installed locally

⏳ Running: Audio processing for 1 TED talk
⏳ Waiting: Hetzner verification (tomorrow AM)

## Files Created

- `scripts/run_full_test.sh` - Script to run full pipeline automatically
- `logs/process.log` - Log file for the background process
- `digestor.duckdb` - DuckDB database with 22 discovered episodes
- `data/podcasts.opml` - OPML with TED Talks and NPR Up First
- `.env` - Environment variables (with your Anthropic API key)

## Known Status

- **Whisper model**: Downloading/loaded (first run takes longer)
- **Database**: Initialized with schema
- **Discovered episodes**: 22 (from TED and NPR feeds since Oct 1)
- **Pending processing**: 1 episode selected for test

## Questions or Issues?

If something fails, check:
1. `logs/process.log` - Full output from audio processing
2. `logs/digest.log` - Application logs
3. DuckDB status: `python3 -c "import duckdb; conn = duckdb.connect('digestor.duckdb'); print(conn.execute('SELECT * FROM episodes WHERE status = \"failed\"').fetchall())"`

---

**Last Updated**: 2025-10-10 23:15 UTC
**Status**: Audio processing in progress (background)
