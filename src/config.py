"""Configuration management for Media Digest."""

import os
from pathlib import Path
from typing import Any

import yaml
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


class Config:
    """Application configuration loaded from .env and config.yaml."""

    def __init__(self, config_path: str = "config.yaml"):
        self.config_path = Path(config_path)
        self._config_data: dict[str, Any] = {}

        if self.config_path.exists():
            with open(self.config_path) as f:
                self._config_data = yaml.safe_load(f) or {}

    # Environment variables
    @property
    def start_date(self) -> str:
        return os.getenv("START_DATE", "2025-10-01")

    @property
    def gmail_address(self) -> str:
        addr = os.getenv("GMAIL_ADDRESS", "")
        if not addr:
            raise ValueError("GMAIL_ADDRESS not set in .env")
        return addr

    @property
    def gmail_token_path(self) -> Path:
        path_str = os.getenv("GMAIL_OAUTH_TOKEN_PATH", "")
        if not path_str:
            raise ValueError("GMAIL_OAUTH_TOKEN_PATH not set in .env")
        return Path(path_str)

    @property
    def vault_root(self) -> Path:
        path_str = os.getenv("VAULT_ROOT", "")
        if not path_str:
            raise ValueError("VAULT_ROOT not set in .env")
        return Path(path_str)

    @property
    def tag_dataview_path(self) -> str:
        return os.getenv("TAG_DATAVIEW_PATH", "w_Dashboards/List of tags.md")

    @property
    def output_repo_path(self) -> Path:
        path_str = os.getenv("OUTPUT_REPO_PATH", "")
        if not path_str:
            raise ValueError("OUTPUT_REPO_PATH not set in .env")
        return Path(path_str)

    @property
    def timezone(self) -> str:
        return os.getenv("TIMEZONE", "UTC")

    @property
    def anthropic_api_key(self) -> str:
        key = os.getenv("ANTHROPIC_API_KEY", "")
        if not key:
            raise ValueError("ANTHROPIC_API_KEY not set in .env")
        return key

    # Config.yaml properties
    @property
    def podcasts_opml(self) -> Path:
        path = self._config_data.get("ingest", {}).get("podcasts_opml", "data/podcasts.opml")
        return Path(path)

    @property
    def gmail_labels(self) -> list[str]:
        return self._config_data.get("ingest", {}).get("email", {}).get("labels", ["INBOX"])

    @property
    def asr_model(self) -> str:
        return self._config_data.get("processing", {}).get("asr", {}).get("model", "medium")

    @property
    def asr_compute_type(self) -> str:
        return self._config_data.get("processing", {}).get("asr", {}).get("compute_type", "int8")

    @property
    def max_tags_per_doc(self) -> int:
        return self._config_data.get("processing", {}).get("tagging", {}).get("max_tags_per_doc", 5)

    @property
    def llm_default_model(self) -> str:
        return self._config_data.get("llm", {}).get("default_model", "claude-sonnet-4-5-20250929")

    @property
    def llm_cleaning_model(self) -> str:
        models = self._config_data.get("llm", {}).get("models", {})
        return models.get("cleaning", self.llm_default_model)

    @property
    def llm_summarization_model(self) -> str:
        models = self._config_data.get("llm", {}).get("models", {})
        return models.get("summarization", self.llm_default_model)

    @property
    def llm_rating_model(self) -> str:
        models = self._config_data.get("llm", {}).get("models", {})
        return models.get("rating", self.llm_default_model)

    @property
    def export_output_path(self) -> str:
        return self._config_data.get("export", {}).get("output_path", "5-Resources/0-Media digester")

    @property
    def export_git_push(self) -> bool:
        return self._config_data.get("export", {}).get("git_push", True)

    @property
    def daily_time(self) -> str:
        return self._config_data.get("export", {}).get("daily_time", "05:00")

    @property
    def weekly_day(self) -> str:
        return self._config_data.get("export", {}).get("weekly_day", "FRI")

    @property
    def weekly_time(self) -> str:
        return self._config_data.get("export", {}).get("weekly_time", "06:00")

    @property
    def max_retries_audio(self) -> int:
        return self._config_data.get("retry", {}).get("max_retries_audio", 3)

    @property
    def max_retries_newsletters(self) -> int:
        return self._config_data.get("retry", {}).get("max_retries_newsletters", 2)

    @property
    def backoff_base(self) -> int:
        return self._config_data.get("retry", {}).get("backoff_base", 60)


# Global config instance
config = Config()
