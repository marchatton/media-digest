"""Retry decorator with exponential backoff."""

import time
from functools import wraps
from typing import Callable, TypeVar

from src.logging_config import get_logger

logger = get_logger(__name__)

T = TypeVar("T")


def retry_with_backoff(max_retries: int = 3, backoff_base: int = 60):
    """Retry decorator with exponential backoff.

    Args:
        max_retries: Maximum number of retry attempts
        backoff_base: Base backoff time in seconds

    Returns:
        Decorated function
    """

    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @wraps(func)
        def wrapper(*args, **kwargs) -> T:
            for attempt in range(max_retries + 1):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    if attempt == max_retries:
                        logger.error(f"{func.__name__} failed after {max_retries} retries: {e}")
                        raise

                    wait_time = backoff_base * (2**attempt)
                    logger.warning(
                        f"{func.__name__} failed (attempt {attempt + 1}/{max_retries}): {e}. "
                        f"Retrying in {wait_time}s..."
                    )
                    time.sleep(wait_time)

            # Should never reach here
            raise RuntimeError(f"{func.__name__} exhausted retries")

        return wrapper

    return decorator
