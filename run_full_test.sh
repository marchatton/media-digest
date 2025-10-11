#!/bin/bash
set -e

echo "=== Media Digest Full Pipeline Test ==="
echo "Started at: $(date)"

echo ""
echo "Step 1: Process audio (download + transcribe)"
python3 cli.py process-audio --limit 1
echo "✓ Audio processing complete"

echo ""
echo "Step 2: Summarize with Claude"
python3 cli.py summarize --limit 1
echo "✓ Summarization complete"

echo ""
echo "Step 3: Export to Obsidian format"
python3 cli.py export --limit 1
echo "✓ Export complete"

echo ""
echo "=== Test Complete! ==="
echo "Finished at: $(date)"
echo ""
echo "Check output/ directory for the generated note"
