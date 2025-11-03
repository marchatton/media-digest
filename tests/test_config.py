"""Tests for typed configuration loading."""

from pathlib import Path

import yaml

from src.config import Config


def test_config_loads_and_validates(monkeypatch, tmp_path):
    """Config.load should coerce types and derive runtime directories."""

    config_path = tmp_path / "config.yaml"
    config_path.write_text(
        yaml.safe_dump(
            {
                "ingest": {
                    "podcasts_opml": "data/podcasts.opml",
                    "email": {"labels": ["newsletters", "inbox"]},
                },
                "processing": {
                    "asr": {"model": "medium", "compute_type": "int8"},
                    "audio": {"yt_dlp_binary": "/usr/local/bin/yt-dlp"},
                    "tagging": {"max_tags_per_doc": 7},
                },
                "llm": {
                    "default_model": "claude-sonnet",
                    "models": {"summarization": "claude-haiku"},
                },
                "export": {
                    "output_path": "vault/media",
                    "git_push": False,
                    "daily_time": "06:00",
                    "weekly_day": "SAT",
                    "weekly_time": "07:00",
                },
                "retry": {"max_retries_audio": 2, "max_retries_newsletters": 1, "backoff_base": 30},
            }
        )
    )

    var_root = tmp_path / "var"
    monkeypatch.setenv("START_DATE", "2025-11-01")
    monkeypatch.setenv("GMAIL_ADDRESS", "user@example.com")
    monkeypatch.setenv("GMAIL_OAUTH_TOKEN_PATH", str(tmp_path / "token.json"))
    monkeypatch.setenv("VAULT_ROOT", str(tmp_path / "vault"))
    monkeypatch.setenv("TAG_DATAVIEW_PATH", "tags.md")
    monkeypatch.setenv("OUTPUT_REPO_PATH", str(tmp_path / "output"))
    monkeypatch.setenv("TIMEZONE", "America/Chicago")
    monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key")
    monkeypatch.setenv("VAR_ROOT", str(var_root))
    monkeypatch.setenv("DUCKDB_FILENAME", "digest.duckdb")

    cfg = Config.load(config_path)

    assert cfg.start_date == "2025-11-01"
    assert cfg.gmail_labels == ["newsletters", "inbox"]
    assert cfg.asr_model == "medium"
    assert cfg.llm_summarization_model == "claude-haiku"
    assert cfg.export_output_path == Path("vault/media")
    assert cfg.export_git_push is False
    assert cfg.audio_blob_dir == var_root / "blobs" / "audio"
    assert cfg.newsletter_blob_dir == var_root / "blobs" / "newsletters"
    assert cfg.logs_dir == var_root / "logs"
    assert cfg.db_path == var_root / "digest.duckdb"
    assert cfg.yt_dlp_binary == Path("/usr/local/bin/yt-dlp")
