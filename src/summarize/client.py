"""Anthropic Claude API client with prompt caching."""

import json
from typing import Any

from anthropic import Anthropic

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

        try:
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

            # Log cache usage
            if hasattr(response, "usage"):
                usage = response.usage
                logger.debug(
                    f"Tokens - Input: {usage.input_tokens}, "
                    f"Output: {usage.output_tokens}, "
                    f"Cache read: {getattr(usage, 'cache_read_input_tokens', 0)}, "
                    f"Cache creation: {getattr(usage, 'cache_creation_input_tokens', 0)}"
                )

            return text

        except Exception as e:
            logger.error(f"Claude API call failed: {e}")
            raise

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

            match = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", text, re.DOTALL)
            if match:
                return json.loads(match.group(1))

            # Try to find raw JSON object
            match = re.search(r"(\{.*\})", text, re.DOTALL)
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
