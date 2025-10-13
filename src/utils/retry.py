"""Retry decorator with exponential backoff."""

import time
from functools import wraps
from typing import Callable, TypeVar, Union, cast

from src.logging_config import get_logger

logger = get_logger(__name__)

T = TypeVar("T")


def _resolve_int(value: Union[int, Callable[[], int]]) -> int:
    return value() if callable(value) else cast(int, value)


def retry_with_backoff(max_retries: Union[int, Callable[[], int]] = 3, backoff_base: Union[int, Callable[[], int]] = 60):
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
            max_retries_val = _resolve_int(max_retries)
            backoff_base_val = _resolve_int(backoff_base)
            for attempt in range(max_retries_val + 1):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    if attempt == max_retries_val:
                        logger.error(f"{func.__name__} failed after {max_retries_val} retries: {e}")
                        raise

                    wait_time = backoff_base_val * (2**attempt)
                    logger.warning(
                        f"{func.__name__} failed (attempt {attempt + 1}/{max_retries_val}): {e}. "
                        f"Retrying in {wait_time}s..."
                    )
                    time.sleep(wait_time)

            # Should never reach here
            raise RuntimeError(f"{func.__name__} exhausted retries")

        return wrapper

    return decorator
