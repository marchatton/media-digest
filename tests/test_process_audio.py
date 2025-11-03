"""Tests for audio processing helpers."""

from __future__ import annotations

import subprocess
import sys
from dataclasses import replace

from src.config import config
from src.process.audio import download_audio


def test_download_audio_uses_configured_fallback(tmp_path, monkeypatch):
    """Ensure configured yt-dlp binary is tried when module is missing."""

    audio_dir = tmp_path / "audio"
    guid = "test-guid"

    fake_binary = tmp_path / "bin" / "yt-dlp"
    fake_binary.parent.mkdir()

    calls: list[list[str]] = []

    def fake_run(command: list[str], *, capture_output: bool, text: bool, check: bool):
        calls.append(command)

        if command[0] == sys.executable:
            raise subprocess.CalledProcessError(
                returncode=1,
                cmd=command,
                stderr="ModuleNotFoundError: No module named 'yt_dlp'",
            )

        assert command[0] == str(fake_binary)
        (audio_dir / f"{guid}.mp3").write_bytes(b"audio")
        return subprocess.CompletedProcess(command, 0)

    monkeypatch.setattr("src.process.audio.subprocess.run", fake_run)

    patched_config = replace(config, yt_dlp_binary=fake_binary)
    monkeypatch.setattr("src.config.config", patched_config)
    monkeypatch.setattr("src.process.audio.config", patched_config)

    result = download_audio("https://example.com/audio.mp3", audio_dir, guid)

    assert result == audio_dir / f"{guid}.mp3"
    assert result.exists()
    assert calls[0][0] == sys.executable
    assert calls[1][0] == str(fake_binary)
