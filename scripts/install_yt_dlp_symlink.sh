#!/bin/bash
set -euo pipefail

TARGET="/opt/digestor/venv/bin/yt-dlp"
TARGET_DIR="$(dirname "$TARGET")"

SOURCE=""
if [ -x /opt/digestor/venv/bin/yt-dlp ]; then
  SOURCE="/opt/digestor/venv/bin/yt-dlp"
elif command -v yt-dlp >/dev/null 2>&1; then
  SOURCE="$(command -v yt-dlp)"
fi

if [ -z "$SOURCE" ]; then
  echo "yt-dlp not found. Install it (e.g. via pip install yt-dlp) before running this script." >&2
  exit 1
fi

if [ ! -d "$TARGET_DIR" ]; then
  if ! mkdir -p "$TARGET_DIR" 2>/tmp/install_yt_dlp_symlink.err; then
    echo "Failed to create $TARGET_DIR (try running with sudo)." >&2
    cat /tmp/install_yt_dlp_symlink.err >&2 || true
    rm -f /tmp/install_yt_dlp_symlink.err
    exit 1
  fi
  rm -f /tmp/install_yt_dlp_symlink.err
fi

if [ -e "$TARGET" ] && [ ! -L "$TARGET" ]; then
  echo "$TARGET already exists; nothing to do."
  exit 0
fi

ln -sf "$SOURCE" "$TARGET"
echo "Symlinked $TARGET -> $SOURCE"
