"""Light tests for JSON extraction in LLM client helper."""

import json
import pytest
from src.summarize.client import ClaudeClient


class DummyClient(ClaudeClient):
    def __init__(self):
        # Avoid requiring API key for tests
        self.api_key = "test"
        self.default_model = "test-model"
        self.client = None  # Not used

    def generate(self, *args, **kwargs) -> str:
        # Return JSON wrapped in code fences
        return """
```json
{"rating": 3, "rationale": "ok"}
```
"""


def test_generate_json_from_code_fence(monkeypatch):
    c = DummyClient()
    data = c.generate_json(system_prompt="s", user_prompt="u")
    assert data["rating"] == 3
    assert "rationale" in data
