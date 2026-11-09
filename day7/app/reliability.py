
import random
import time
import logging
from collections.abc import Callable
from typing import Any

import httpx

logger = logging.getLogger(__name__)


def _is_retryable(exc: Exception) -> bool:
    error_code = getattr(exc, "code", None)
    error_message = str(exc).lower()

    # Daily quota exhaustion will not recover through short retries.
    if error_code == 429 and (
        "per day" in error_message
        or "daily" in error_message
        or "quota exceeded" in error_message
    ):
        return False

    return (
        error_code in (429, 500, 502, 503, 504)
        or isinstance(exc, (TimeoutError, httpx.TimeoutException))
    )


def generate_with_retry(
    client: Any,
    model: str,
    contents: list[Any],
    config: Any,
    max_retries: int = 4,
    before_attempt: Callable[[], None] | None = None,
    deadline: float | None = None,
) -> Any:
    if max_retries < 0:
        raise ValueError("max_retries cannot be negative.")

    for attempt in range(max_retries + 1):
        if deadline is not None and time.monotonic() >= deadline:
            raise TimeoutError("Agent execution deadline exceeded.")

        if before_attempt is not None:
            before_attempt()

        if deadline is not None and time.monotonic() >= deadline:
            raise TimeoutError("Agent execution deadline exceeded.")

        try:
            return client.models.generate_content(
                model=model,
                contents=contents,
                config=config,
            )

        except Exception as exc:
            if not _is_retryable(exc) or attempt == max_retries:
                logger.error(
                    "Gemini request failed (error_type=%s, code=%s).",
                    type(exc).__name__,
                    getattr(exc, "code", None),
                )
                raise

            delay = min(30, 2 ** attempt)
            wait_time = delay + random.uniform(0, 0.5)

            if deadline is not None:
                remaining = deadline - time.monotonic()
                if remaining <= wait_time:
                    raise TimeoutError(
                        "Agent execution deadline exceeded while retrying."
                    ) from exc

            logger.warning(
                "Retry %s/%s after %.2f seconds "
                "(error_type=%s, code=%s).",
                attempt + 1,
                max_retries,
                wait_time,
                type(exc).__name__,
                getattr(exc, "code", None),
            )
            time.sleep(wait_time)

    raise RuntimeError("Gemini request failed after retries.")
