"""Typed configuration loading for Media Digest."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping

import yaml
from dotenv import load_dotenv


def _load_yaml(config_path: Path) -> dict[str, Any]:
    if not config_path.exists():
        return {}
    with config_path.open() as handle:
        data = yaml.safe_load(handle) or {}
    if not isinstance(data, dict):  # pragma: no cover - defensive guard
        raise ValueError("config.yaml must contain a mapping at the root")
    return data


def _require_env(env: Mapping[str, str], name: str) -> str:
    value = env.get(name, "").strip()
    if not value:
        raise ValueError(f"{name} not set in environment")
    return value


def _optional_path(value: str | None) -> Path | None:
    if not value:
        return None
    return Path(value).expanduser()


@dataclass(frozen=True, slots=True)
class Config:
    """Typed application configuration sourced from .env and config.yaml."""

    start_date: str
    gmail_address: str
    gmail_token_path: Path
    vault_root: Path
    tag_dataview_path: str
    output_repo_path: Path
    timezone: str
    anthropic_api_key: str
    podcasts_opml: Path
    gmail_labels: list[str]
    asr_model: str
    asr_compute_type: str
    yt_dlp_binary: Path | None
    max_tags_per_doc: int
    llm_default_model: str
    llm_cleaning_model: str
    llm_summarization_model: str
    llm_rating_model: str
    export_output_path: Path
    export_git_push: bool
    daily_time: str
    weekly_day: str
    weekly_time: str
    max_retries_audio: int
    max_retries_newsletters: int
    backoff_base: int
    var_root: Path
    blobs_root: Path
    audio_blob_dir: Path
    transcript_blob_dir: Path
    newsletter_blob_dir: Path
    logs_dir: Path
    db_path: Path

    @classmethod
    def load(cls, config_path: str | Path = "config.yaml") -> "Config":
        """Load configuration from environment variables and YAML settings."""

        load_dotenv()
        env = os.environ
        config_file = Path(config_path)
        config_data = _load_yaml(config_file)

        ingest_cfg = config_data.get("ingest", {}) if isinstance(config_data, dict) else {}
        processing_cfg = config_data.get("processing", {}) if isinstance(config_data, dict) else {}
        llm_cfg = config_data.get("llm", {}) if isinstance(config_data, dict) else {}
        export_cfg = config_data.get("export", {}) if isinstance(config_data, dict) else {}
        retry_cfg = config_data.get("retry", {}) if isinstance(config_data, dict) else {}

        start_date = env.get("START_DATE", "2025-10-01")
        gmail_address = _require_env(env, "GMAIL_ADDRESS")
        gmail_token_path = Path(_require_env(env, "GMAIL_OAUTH_TOKEN_PATH")).expanduser()
        vault_root = Path(_require_env(env, "VAULT_ROOT")).expanduser()
        tag_dataview_path = env.get("TAG_DATAVIEW_PATH", "w_Dashboards/List of tags.md")
        output_repo_path = Path(_require_env(env, "OUTPUT_REPO_PATH")).expanduser()
        timezone = env.get("TIMEZONE", "UTC")
        anthropic_api_key = _require_env(env, "ANTHROPIC_API_KEY")

        podcasts_opml = Path(ingest_cfg.get("podcasts_opml", "data/podcasts.opml")).expanduser()
        email_cfg = ingest_cfg.get("email", {}) if isinstance(ingest_cfg, dict) else {}
        raw_labels = email_cfg.get("labels", ["INBOX"])
        gmail_labels = [str(label) for label in raw_labels]

        asr_cfg = processing_cfg.get("asr", {}) if isinstance(processing_cfg, dict) else {}
        audio_cfg = processing_cfg.get("audio", {}) if isinstance(processing_cfg, dict) else {}
        tagging_cfg = processing_cfg.get("tagging", {}) if isinstance(processing_cfg, dict) else {}

        asr_model = str(asr_cfg.get("model", "small"))
        asr_compute_type = str(asr_cfg.get("compute_type", "int8"))
        yt_dlp_binary = _optional_path(audio_cfg.get("yt_dlp_binary"))
        max_tags_per_doc = int(tagging_cfg.get("max_tags_per_doc", 5))

        llm_default_model = str(llm_cfg.get("default_model", "claude-sonnet-4-5-20250929"))
        models_cfg = llm_cfg.get("models", {}) if isinstance(llm_cfg, dict) else {}
        llm_cleaning_model = str(models_cfg.get("cleaning", llm_default_model))
        llm_summarization_model = str(models_cfg.get("summarization", llm_default_model))
        llm_rating_model = str(models_cfg.get("rating", llm_default_model))

        export_output_path = Path(export_cfg.get("output_path", "5-Resources/0-Media digester"))
        export_git_push = bool(export_cfg.get("git_push", True))
        daily_time = str(export_cfg.get("daily_time", "05:00"))
        weekly_day = str(export_cfg.get("weekly_day", "FRI"))
        weekly_time = str(export_cfg.get("weekly_time", "06:00"))

        max_retries_audio = int(retry_cfg.get("max_retries_audio", 3))
        max_retries_newsletters = int(retry_cfg.get("max_retries_newsletters", 2))
        backoff_base = int(retry_cfg.get("backoff_base", 60))

        var_root = Path(env.get("VAR_ROOT", "var")).expanduser()
        blobs_root = var_root / "blobs"
        audio_blob_dir = blobs_root / "audio"
        transcript_blob_dir = blobs_root / "transcripts"
        newsletter_blob_dir = blobs_root / "newsletters"
        logs_dir = var_root / "logs"
        db_filename = env.get("DUCKDB_FILENAME", "digestor.duckdb")
        db_path = var_root / db_filename

        return cls(
            start_date=start_date,
            gmail_address=gmail_address,
            gmail_token_path=gmail_token_path,
            vault_root=vault_root,
            tag_dataview_path=tag_dataview_path,
            output_repo_path=output_repo_path,
            timezone=timezone,
            anthropic_api_key=anthropic_api_key,
            podcasts_opml=podcasts_opml,
            gmail_labels=gmail_labels,
            asr_model=asr_model,
            asr_compute_type=asr_compute_type,
            yt_dlp_binary=yt_dlp_binary,
            max_tags_per_doc=max_tags_per_doc,
            llm_default_model=llm_default_model,
            llm_cleaning_model=llm_cleaning_model,
            llm_summarization_model=llm_summarization_model,
            llm_rating_model=llm_rating_model,
            export_output_path=export_output_path,
            export_git_push=export_git_push,
            daily_time=daily_time,
            weekly_day=weekly_day,
            weekly_time=weekly_time,
            max_retries_audio=max_retries_audio,
            max_retries_newsletters=max_retries_newsletters,
            backoff_base=backoff_base,
            var_root=var_root,
            blobs_root=blobs_root,
            audio_blob_dir=audio_blob_dir,
            transcript_blob_dir=transcript_blob_dir,
            newsletter_blob_dir=newsletter_blob_dir,
            logs_dir=logs_dir,
            db_path=db_path,
        )


# Global config instance with validated values
config = Config.load()
