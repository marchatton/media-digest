"""Anthropic Claude API client with prompt caching."""

import json
from typing import Any

from anthropic import Anthropic
import time
from typing import Callable

from src.config import config
from src.logging_config import get_logger

logger = get_logger(__name__)


class ClaudeClient:
    """Anthropic Claude API client."""

    def __init__(self, api_key: str | None = None, default_model: str | None = None):
        """Initialize Claude client.

        Args:
            api_key: Anthropic API key (defaults to config)
            default_model: Default model to use (defaults to config)
        """
        self.api_key = api_key or config.anthropic_api_key
        self.default_model = default_model or config.llm_default_model
        self.client = Anthropic(api_key=self.api_key)

    def _with_retries(self, fn: Callable[[], str], *, max_retries: int = 3, backoff_base: int = 2) -> str:
        """Execute a function with simple retry/backoff for transient errors."""
        for attempt in range(max_retries + 1):
            try:
                return fn()
            except Exception as e:
                if attempt == max_retries:
                    logger.error(f"LLM call failed after {max_retries} retries: {e}")
                    raise
                wait = backoff_base * (2**attempt)
                logger.warning(f"LLM call failed (attempt {attempt+1}/{max_retries}): {e}; retrying in {wait}s")
                time.sleep(wait)

        # Unreachable
        raise RuntimeError("Retries exhausted")

    def generate(
        self,
        system_prompt: str,
        user_prompt: str,
        model: str | None = None,
        temperature: float = 0.7,
        max_tokens: int = 4096,
    ) -> str:
        """Generate completion from Claude.

        Args:
            system_prompt: System prompt (cacheable)
            user_prompt: User prompt
            model: Model to use (defaults to configured model)
            temperature: Sampling temperature
            max_tokens: Maximum tokens to generate

        Returns:
            Generated text
        """
        model = model or self.default_model

        logger.debug(f"Generating with {model}")

        def run_call() -> str:
            response = self.client.messages.create(
                    model=model,
                    max_tokens=max_tokens,
                    temperature=temperature,
                    system=[
                        {
                            "type": "text",
                            "text": system_prompt,
                            "cache_control": {"type": "ephemeral"},  # Enable prompt caching
                        }
                    ],
                    messages=[{"role": "user", "content": user_prompt}],
                )
            # Extract text from response
            text = response.content[0].text

            # Log usage if present
            if hasattr(response, "usage"):
                usage = response.usage
                logger.debug(
                    f"Tokens - Input: {usage.input_tokens}, "
                    f"Output: {usage.output_tokens}, "
                    f"Cache read: {getattr(usage, 'cache_read_input_tokens', 0)}, "
                    f"Cache creation: {getattr(usage, 'cache_creation_input_tokens', 0)}"
                )
            return text

        return self._with_retries(run_call)

    def generate_json(
        self,
        system_prompt: str,
        user_prompt: str,
        model: str | None = None,
        temperature: float = 0.7,
        max_tokens: int = 4096,
    ) -> dict[str, Any]:
        """Generate JSON completion from Claude.

        Args:
            system_prompt: System prompt (cacheable)
            user_prompt: User prompt
            model: Model to use
            temperature: Sampling temperature
            max_tokens: Maximum tokens to generate

        Returns:
            Parsed JSON object

        Raises:
            ValueError if response is not valid JSON
        """
        text = self.generate(system_prompt, user_prompt, model, temperature, max_tokens)

        # Try to extract JSON from response
        try:
            # First try direct parsing
            return json.loads(text)
        except json.JSONDecodeError:
            # Try to find JSON in markdown code block
            import re

            match = re.search(r"```(?:json)?\s*(\{[\s\S]*?\})\s*```", text)
            if match:
                return json.loads(match.group(1))

            # Try to find raw JSON object
            # Fallback: greedy outermost braces
            match = re.search(r"(\{[\s\S]*\})", text)
            if match:
                return json.loads(match.group(1))

            raise ValueError(f"Could not parse JSON from response: {text}")


# Global client instance
_client: ClaudeClient | None = None


def get_client() -> ClaudeClient:
    """Get global Claude client instance.

    Returns:
        Claude client
    """
    global _client
    if _client is None:
        _client = ClaudeClient()
    return _client
