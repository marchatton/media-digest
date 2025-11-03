"""Tests for configuration loading."""

import pytest
from src.config import Config


def test_config_loads_defaults():
    """Test that config loads with defaults."""
    config = Config()

    assert config.timezone == "UTC"
    assert config.start_date == "2025-10-01"
    assert config.asr_model == "small"
    assert config.llm_default_model == "claude-sonnet-4-5-20250929"


def test_config_loads_from_yaml():
    """Test that config loads from yaml file."""
    config = Config("config.yaml")

    assert config.asr_model in ["tiny", "base", "small", "medium", "large"]
    assert config.max_tags_per_doc == 5
